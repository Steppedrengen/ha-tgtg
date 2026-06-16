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
        self._email: str | None = None
        self._credentials: dict | None = None
        self._client: Any = None
        self._polling_id: str | None = None

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Step 1 — collect email."""
        errors: dict[str, str] = {}

        if user_input is not None:
            email = user_input[CONF_EMAIL].strip().lower()
            await self.async_set_unique_id(email)
            self._abort_if_unique_id_configured()

            try:
                from tgtg import TgtgClient  # noqa: PLC0415
                self._client = TgtgClient(email=email)
                self._email = email

                def _request_pin():
                    # Use the correct v5 endpoint via _post() so DataDome is handled
                    resp = self._client._post(
                        self._client._get_url("auth/v5/authByEmail"),
                        json={"device_type": self._client.device_type, "email": email},
                    )
                    _LOGGER.debug("authByEmail status=%s body=%s", resp.status_code, resp.text[:300])
                    if resp.status_code == 429:
                        raise Exception("too_many_requests")
                    if resp.status_code != 200:
                        raise Exception(f"api_error:{resp.status_code}")
                    data = resp.json()
                    state = data.get("state", "")
                    if state == "TERMS":
                        raise Exception("not_registered")
                    if state != "WAIT":
                        raise Exception(f"unexpected_state:{state}")
                    return data.get("polling_id")

                self._polling_id = await self.hass.async_add_executor_job(_request_pin)
                return await self.async_step_pin()

            except ImportError:
                errors["base"] = "missing_dependency"
            except Exception as err:  # noqa: BLE001
                msg = str(err)
                _LOGGER.error("TGTG login initiation failed: %s", msg)
                if "too_many_requests" in msg:
                    errors["base"] = "too_many_requests"
                elif "not_registered" in msg:
                    errors["base"] = "not_registered"
                else:
                    errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_EMAIL): str}),
            errors=errors,
        )

    async def async_step_pin(self, user_input: dict[str, Any] | None = None):
        """Step 2 — enter PIN from email."""
        errors: dict[str, str] = {}

        if user_input is not None:
            pin = user_input.get("pin", "").strip()
            if not pin:
                errors["pin"] = "pin_required"
            else:
                try:
                    def _validate_pin():
                        # _auth_by_pin sets access_token, refresh_token, cookie on client
                        self._client._auth_by_pin(self._polling_id, pin)
                        return {
                            "access_token": self._client.access_token,
                            "refresh_token": self._client.refresh_token,
                            "cookie": self._client.cookie,
                        }

                    self._credentials = await self.hass.async_add_executor_job(_validate_pin)
                    if not self._credentials.get("access_token"):
                        raise Exception("No access token received")
                    return await self.async_step_options()

                except Exception as err:  # noqa: BLE001
                    _LOGGER.error("PIN validation failed: %s", err)
                    errors["base"] = "invalid_pin"

        return self.async_show_form(
            step_id="pin",
            data_schema=vol.Schema({vol.Required("pin"): str}),
            description_placeholders={"email": self._email or ""},
            errors=errors,
        )

    async def async_step_options(self, user_input: dict[str, Any] | None = None):
        """Step 3 — polling interval."""
        if user_input is not None:
            return self.async_create_entry(
                title=f"Too Good To Go ({self._email})",
                data={
                    CONF_EMAIL: self._email,
                    "credentials": self._credentials,
                    CONF_SCAN_INTERVAL: user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                },
            )
        return self.async_show_form(
            step_id="options",
            data_schema=vol.Schema({
                vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
                    vol.Coerce(int), vol.Range(min=MIN_SCAN_INTERVAL, max=60)
                )
            }),
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return TgtgOptionsFlow()


class TgtgOptionsFlow(config_entries.OptionsFlow):
    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        current = self.config_entry.options.get(
            CONF_SCAN_INTERVAL,
            self.config_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
        )
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional(CONF_SCAN_INTERVAL, default=current): vol.All(
                    vol.Coerce(int), vol.Range(min=MIN_SCAN_INTERVAL, max=60)
                )
            }),
        )
