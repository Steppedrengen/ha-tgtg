"""Sensor platform for Too Good To Go."""
from __future__ import annotations

import logging
from math import atan2, cos, radians, sin, sqrt
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import (
    ATTR_CURRENCY,
    ATTR_DESCRIPTION,
    ATTR_DISTANCE_KM,
    ATTR_FAVORITE,
    ATTR_ITEM_COVER_IMAGE,
    ATTR_ITEM_ID,
    ATTR_ITEM_NAME,
    ATTR_ITEMS_AVAILABLE,
    ATTR_ITEMS_MAX,
    ATTR_PICKUP_END,
    ATTR_PICKUP_START,
    ATTR_PRICE,
    ATTR_PRICE_INCLUDING_TAXES,
    ATTR_RATING,
    ATTR_SOLD_OUT,
    ATTR_STORE_ADDRESS,
    ATTR_STORE_BRANCH,
    ATTR_STORE_LATITUDE,
    ATTR_STORE_LOGO,
    ATTR_STORE_LONGITUDE,
    ATTR_STORE_NAME,
    COORDINATOR,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance in km between two GPS coordinates (Haversine)."""
    R = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return round(R * 2 * atan2(sqrt(a), sqrt(1 - a)), 2)


def _format_price(price_data: dict | None) -> str | None:
    """Format price from TGTG API response."""
    if not price_data:
        return None
    minor_units = price_data.get("minor_units", 0)
    decimals = price_data.get("decimals", 2)
    return str(minor_units / (10 ** decimals))


def _format_pickup_interval(interval: dict | None) -> str | None:
    """Format pickup interval as Danish-friendly string."""
    if not interval:
        return None
    start = interval.get("start", "")
    end = interval.get("end", "")
    if start and end:
        try:
            from datetime import datetime
            s = datetime.fromisoformat(start.replace("Z", "+00:00"))
            e = datetime.fromisoformat(end.replace("Z", "+00:00"))
            return f"{s.strftime('%d/%m %H:%M')} – {e.strftime('%H:%M')}"
        except Exception:
            return f"{start} – {end}"
    return None


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up TGTG sensors from config entry."""
    coordinator: DataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][COORDINATOR]

    known_item_ids: set[str] = set()

    def _create_new_entities() -> None:
        """Create new sensor entities for newly discovered items."""
        new_entities = []
        for item_id, item_data in coordinator.data.items():
            if item_id not in known_item_ids:
                known_item_ids.add(item_id)
                new_entities.append(TgtgItemSensor(coordinator, item_id, entry.entry_id, hass))
        if new_entities:
            async_add_entities(new_entities)

    _create_new_entities()
    coordinator.async_add_listener(_create_new_entities)


class TgtgItemSensor(CoordinatorEntity, SensorEntity):
    """Sensor representing a single TGTG store/item."""

    _attr_has_entity_name = True
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        item_id: str,
        entry_id: str,
        hass: HomeAssistant,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._item_id = item_id
        self._entry_id = entry_id
        self._hass = hass
        self._attr_unique_id = f"{entry_id}_{item_id}"

    @property
    def _item_data(self) -> dict | None:
        return self.coordinator.data.get(self._item_id)

    @property
    def _store_coords(self) -> tuple[float, float] | None:
        """Extract store GPS coordinates from item data."""
        if not self._item_data:
            return None
        location = (
            self._item_data
            .get("store", {})
            .get("store_location", {})
            .get("location", {})
        )
        lat = location.get("latitude")
        lon = location.get("longitude")
        if lat is not None and lon is not None:
            return float(lat), float(lon)
        return None

    @property
    def _distance_km(self) -> float | None:
        """Calculate distance from HA home to this store in km."""
        coords = self._store_coords
        if coords is None:
            return None
        ha_lat = self._hass.config.latitude
        ha_lon = self._hass.config.longitude
        if ha_lat is None or ha_lon is None:
            return None
        return _haversine_km(ha_lat, ha_lon, coords[0], coords[1])

    @property
    def name(self) -> str:
        store = (self._item_data or {}).get("store", {})
        store_name = store.get("store_name", "Ukendt butik")
        branch = store.get("branch", "")
        if branch:
            return f"{store_name} – {branch}"
        return store_name

    @property
    def icon(self) -> str:
        if self._item_data:
            return "mdi:shopping-outline" if self._item_data.get("items_available", 0) > 0 else "mdi:shopping-remove"
        return "mdi:food-takeout-box"

    @property
    def native_value(self) -> int:
        return (self._item_data or {}).get("items_available", 0)

    @property
    def native_unit_of_measurement(self) -> str:
        return "pakker"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        if not self._item_data:
            return {}

        item = self._item_data.get("item", {})
        store = self._item_data.get("store", {})
        pickup_interval = self._item_data.get("pickup_interval", {})
        price = item.get("price_including_taxes", {})
        item_price = item.get("item_price", {})
        store_location = store.get("store_location", {})
        address = store_location.get("address", {})
        location = store_location.get("location", {})
        store_lat = location.get("latitude")
        store_lon = location.get("longitude")

        attrs: dict[str, Any] = {
            ATTR_ITEM_ID: self._item_id,
            ATTR_STORE_NAME: store.get("store_name"),
            ATTR_STORE_BRANCH: store.get("branch"),
            ATTR_STORE_LOGO: store.get("logo_picture", {}).get("current_url"),
            ATTR_ITEM_NAME: item.get("name"),
            ATTR_ITEM_COVER_IMAGE: item.get("cover_picture", {}).get("current_url"),
            ATTR_ITEMS_AVAILABLE: self._item_data.get("items_available", 0),
            ATTR_ITEMS_MAX: item.get("items_max_count"),
            ATTR_PICKUP_START: pickup_interval.get("start"),
            ATTR_PICKUP_END: pickup_interval.get("end"),
            "pickup_display": _format_pickup_interval(pickup_interval),
            ATTR_PRICE: _format_price(item_price),
            ATTR_PRICE_INCLUDING_TAXES: _format_price(price),
            ATTR_CURRENCY: price.get("code", "DKK"),
            ATTR_DESCRIPTION: item.get("description"),
            ATTR_FAVORITE: self._item_data.get("favorite", False),
            ATTR_SOLD_OUT: self._item_data.get("items_available", 0) == 0,
            ATTR_STORE_ADDRESS: address.get("address_line"),
            ATTR_RATING: store.get("average_overall_rating", {}).get("average_overall_rating"),
        }

        # GPS-koordinater på butikken
        if store_lat is not None:
            attrs[ATTR_STORE_LATITUDE] = float(store_lat)
        if store_lon is not None:
            attrs[ATTR_STORE_LONGITUDE] = float(store_lon)

        # Afstand fra HA's hjemmekoordinater
        dist = self._distance_km
        if dist is not None:
            attrs[ATTR_DISTANCE_KM] = dist

        return {k: v for k, v in attrs.items() if v is not None}

    @property
    def available(self) -> bool:
        return self.coordinator.last_update_success and self._item_data is not None
