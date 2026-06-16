"""Config flow for Too Good To Go integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv

from .const import (
    CONF_EMAIL,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MIN_SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


async def validate_credentials(hass: HomeAssistant, email: str) -> dict[str, Any]:
    """Validate credentials by initiating TGTG login."""
    from tgtg import TgtgClient

    errors: dict[str, str] = {}

    try:
        # TgtgClient with email triggers polling-based login flow
        client = await hass.async_add_executor_job(
            lambda: TgtgClient(email=email)
        )
        # Try to get credentials to verify login
        credentials = await hass.async_add_executor_job(client.get_credentials)
        return {"credentials": credentials, "errors": {}}
    except Exception as err:
        _LOGGER.error("TGTG login fejlede: %s", err)
        errors["base"] = "invalid_auth"
        return {"credentials": None, "errors": errors}


class TgtgConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Too Good To Go."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize flow."""
        self._email: str | None = None
        self._credentials: dict | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step - get email."""
        errors: dict[str, str] = {}

        if user_input is not None:
            email = user_input[CONF_EMAIL]

            # Check for duplicate entries
            await self.async_set_unique_id(email.lower())
            self._abort_if_unique_id_configured()

            self._email = email
            return await self.async_step_login()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_EMAIL): str,
                }
            ),
            description_placeholders={
                "info": "Indtast din Too Good To Go e-mail. Du vil modtage en login-email fra TGTG."
            },
            errors=errors,
        )

    async def async_step_login(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Wait for user to confirm email login."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Try to get credentials after user has clicked email link
            result = await validate_credentials(self.hass, self._email)

            if result["credentials"]:
                self._credentials = result["credentials"]
                return await self.async_step_options()
            else:
                errors = result["errors"]

        return self.async_show_form(
            step_id="login",
            data_schema=vol.Schema({}),
            description_placeholders={
                "email": self._email,
                "instructions": (
                    f"En login-email er sendt til {self._email}.\n\n"
                    "Åbn emailen fra Too Good To Go og klik på linket. "
                    "Kom derefter tilbage her og tryk 'Send'."
                ),
            },
            errors=errors,
        )

    async def async_step_options(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle options step."""
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
                        vol.Coerce(int), vol.Range(min=MIN_SCAN_INTERVAL, max=60)
                    ),
                }
            ),
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> TgtgOptionsFlow:
        """Get the options flow for this handler."""
        return TgtgOptionsFlow(config_entry)


class TgtgOptionsFlow(config_entries.OptionsFlow):
    """Handle options for Too Good To Go."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current_interval = self.config_entry.options.get(
            CONF_SCAN_INTERVAL,
            self.config_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_SCAN_INTERVAL, default=current_interval
                    ): vol.All(
                        vol.Coerce(int), vol.Range(min=MIN_SCAN_INTERVAL, max=60)
                    ),
                }
            ),
        )
