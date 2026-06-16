"""Config flow for Too Good To Go integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback

from .const import (
    CONF_EMAIL,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MIN_SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


class TgtgConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Too Good To Go."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize flow."""
        self._email: str | None = None
        self._credentials: dict | None = None
        self._client: Any = None
        self._polling_id: str | None = None

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Step 1 — collect email and send magic link/PIN email immediately."""
        errors: dict[str, str] = {}

        if user_input is not None:
            email = user_input[CONF_EMAIL].strip().lower()

            await self.async_set_unique_id(email)
            self._abort_if_unique_id_configured()

            try:
                from tgtg import TgtgClient  # noqa: PLC0415
                from tgtg.exceptions import TgtgPollingError  # noqa: PLC0415

                def _create_and_send(email: str):
                    client = TgtgClient(email=email)
                    # Send the auth request — this triggers the PIN/magic link email
                    response = client._post(
                        client._get_url("auth/v5/authByEmail"),
                        json={"device_type": client.device_type, "email": email},
                    )
                    if response.status_code == 200:
                        data = response.json()
                        state = data.get("state", "")
                        if state == "TERMS":
                            raise TgtgPollingError(
                                f"Email {email} is not linked to a TGTG account."
                            )
                        elif state == "WAIT":
                            return client, data.get("polling_id")
                        else:
                            raise Exception(f"Unexpected state: {state}")
                    elif response.status_code == 429:
                        raise Exception("too_many_requests")
                    else:
                        raise Exception(f"API error {response.status_code}")

                self._client, self._polling_id = await self.hass.async_add_executor_job(
                    _create_and_send, email
                )
                self._email = email
                return await self.async_step_pin()

            except ImportError:
                errors["base"] = "missing_dependency"
            except Exception as err:  # noqa: BLE001
                err_str = str(err)
                _LOGGER.exception("Error initiating TGTG login: %s", err_str)
                if "too_many_requests" in err_str:
                    errors["base"] = "too_many_requests"
                elif "not linked" in err_str:
                    errors["base"] = "not_registered"
                else:
                    errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_EMAIL): str}),
            errors=errors,
        )

    async def async_step_pin(self, user_input: dict[str, Any] | None = None):
        """Step 2 — user enters PIN from email."""
        errors: dict[str, str] = {}

        if user_input is not None:
            pin = str(user_input.get("pin", "")).strip()
            if not pin:
                errors["pin"] = "required"
            else:
                try:
                    def _validate_pin(email: str, polling_id: str, pin: str):
                        from http import HTTPStatus  # noqa: PLC0415
                        resp = self._client._post(
                            self._client._get_url("auth/v5/authByRequestPin"),
                            json={
                                "device_type": self._client.device_type,
                                "email": email,
                                "request_pin": pin,
                                "request_polling_id": polling_id,
                            },
                        )
                        if resp.status_code == HTTPStatus.OK:
                            data = resp.json()
                            return {
                                "access_token": data.get("access_token"),
                                "refresh_token": data.get("refresh_token"),
                                "cookie": resp.headers.get("Set-Cookie", ""),
                            }
                        elif resp.status_code == 403:
                            raise Exception("invalid_pin")
                        else:
                            raise Exception(f"PIN error {resp.status_code}: {resp.text[:100]}")

                    self._credentials = await self.hass.async_add_executor_job(
                        _validate_pin, self._email, self._polling_id, pin
                    )
                    return await self.async_step_options()

                except Exception as err:  # noqa: BLE001
                    err_str = str(err)
                    _LOGGER.error("TGTG PIN validation failed: %s", err_str)
                    if "invalid_pin" in err_str:
                        errors["base"] = "invalid_pin"
                    else:
                        errors["base"] = "invalid_auth"

        return self.async_show_form(
            step_id="pin",
            data_schema=vol.Schema({vol.Required("pin"): str}),
            description_placeholders={"email": self._email or ""},
            errors=errors,
        )

    async def async_step_options(self, user_input: dict[str, Any] | None = None):
        """Step 3 — pick polling interval."""
        if user_input is not None:
            return self.async_create_entry(
                title=f"Too Good To Go ({self._email})",
                data={
                    CONF_EMAIL: self._email,
                    "credentials": self._credentials,
                    CONF_SCAN_INTERVAL: user_input.get(
                        CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                    ),
                },
            )

        return self.async_show_form(
            step_id="options",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=MIN_SCAN_INTERVAL, max=60),
                    )
                }
            ),
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        """Return the options flow handler."""
        return TgtgOptionsFlow()


class TgtgOptionsFlow(config_entries.OptionsFlow):
    """Options flow — change polling interval after setup."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        """Handle options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = self.config_entry.options.get(
            CONF_SCAN_INTERVAL,
            self.config_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_SCAN_INTERVAL, default=current): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=MIN_SCAN_INTERVAL, max=60),
                    )
                }
            ),
        )
