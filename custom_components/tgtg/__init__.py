"""Too Good To Go integration for Home Assistant."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_EMAIL,
    CONF_SCAN_INTERVAL,
    COORDINATOR,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    PLATFORMS,
    TGTG_CLIENT,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Too Good To Go from a config entry."""
    from tgtg import TgtgClient
    from tgtg.exceptions import TgtgAPIError, TgtgLoginError

    email = entry.data[CONF_EMAIL]
    credentials = entry.data.get("credentials", {})
    scan_interval = entry.options.get(
        CONF_SCAN_INTERVAL,
        entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
    )

    try:
        client = await hass.async_add_executor_job(
            lambda: TgtgClient(
                email=email,
                access_token=credentials.get("access_token"),
                refresh_token=credentials.get("refresh_token"),
                user_id=credentials.get("user_id"),
                cookie=credentials.get("cookie"),
            )
        )
    except TgtgLoginError as err:
        raise ConfigEntryAuthFailed(f"TGTG login fejlede: {err}") from err
    except Exception as err:
        raise ConfigEntryNotReady(f"Kunne ikke forbinde til TGTG: {err}") from err

    async def async_update_data() -> dict:
        """Fetch data from TGTG API."""
        try:
            items = await hass.async_add_executor_job(client.get_items)
            return {item["item"]["item_id"]: item for item in items}
        except TgtgAPIError as err:
            raise UpdateFailed(f"TGTG API fejl: {err}") from err
        except Exception as err:
            raise UpdateFailed(f"Ukendt fejl fra TGTG: {err}") from err

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=DOMAIN,
        update_method=async_update_data,
        update_interval=timedelta(minutes=scan_interval),
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        COORDINATOR: coordinator,
        TGTG_CLIENT: client,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)
