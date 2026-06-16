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

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Step 1 — collect email address."""
        errors: dict[str, str] = {}

        if user_input is not None:
            email = user_input[CONF_EMAIL].strip().lower()

            await self.async_set_unique_id(email)
            self._abort_if_unique_id_configured()

            try:
                from tgtg import TgtgClient  # noqa: PLC0415

                self._client = await self.hass.async_add_executor_job(
                    lambda: TgtgClient(email=email)
                )
                self._email = email
                return await self.async_step_link()

            except ImportError:
                errors["base"] = "missing_dependency"
            except Exception as err:  # noqa: BLE001
                _LOGGER.exception("Error starting TGTG login: %s", err)
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_EMAIL): str}),
            errors=errors,
        )

    async def async_step_link(self, user_input: dict[str, Any] | None = None):
        """Step 2 — user clicks magic link, then submits here."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                self._credentials = await self.hass.async_add_executor_job(
                    self._client.get_credentials
                )
                return await self.async_step_options()
            except Exception as err:  # noqa: BLE001
                _LOGGER.error("TGTG credential fetch failed: %s", err)
                errors["base"] = "invalid_auth"

        return self.async_show_form(
            step_id="link",
            data_schema=vol.Schema({}),
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
