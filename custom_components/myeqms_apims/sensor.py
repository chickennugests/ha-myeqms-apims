"""Sensor platform for Malaysia APIMS (DOE MyEQMS)."""

from __future__ import annotations

from datetime import datetime
import logging
from typing import Any, Dict, Optional

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, CONF_STATION_ID, CONF_STATION_NAME, DOMAIN
from .coordinator import MyEQMSDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up MyEQMS sensors based on a config entry."""
    coordinator: MyEQMSDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        MyEQMSIndexSensor(coordinator, entry),
        MyEQMSClassSensor(coordinator, entry),
        MyEQMSPollutantSensor(coordinator, entry),
        MyEQMSLastUpdateSensor(coordinator, entry),
    ]

    async_add_entities(entities)


class MyEQMSBaseSensor(CoordinatorEntity[MyEQMSDataUpdateCoordinator], SensorEntity):
    """Base class for MyEQMS sensors."""

    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION

    def __init__(
        self,
        coordinator: MyEQMSDataUpdateCoordinator,
        entry: ConfigEntry,
        key: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entry = entry
        self.station_id = entry.data[CONF_STATION_ID]
        self.station_name = entry.data.get(CONF_STATION_NAME, self.station_id)
        self._attr_unique_id = f"{self.station_id}_{key}"

    @property
    def device_info(self) -> DeviceInfo:
        """Return information about the station device."""
        data = self.coordinator.data or {}
        location = data.get("STATION_LOCATION") or self.station_name
        state = data.get("STATE_NAME", "")
        place = data.get("PLACE")

        model_desc = f"{place} ({state})" if place and state else (place or state or "CAQM Station")

        return DeviceInfo(
            identifiers={(DOMAIN, self.station_id)},
            name=f"APIMS {location}",
            manufacturer="Department of Environment Malaysia (JAS)",
            model=model_desc,
            entry_type=DeviceEntryType.SERVICE,
            configuration_url="https://eqms.doe.gov.my/APIMS/main",
        )


class MyEQMSIndexSensor(MyEQMSBaseSensor):
    """Air Pollutant Index (API / IPU) numerical sensor."""

    _attr_device_class = SensorDeviceClass.AQI
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:air-filter"

    def __init__(self, coordinator: MyEQMSDataUpdateCoordinator, entry: ConfigEntry) -> None:
        """Initialize index sensor."""
        super().__init__(coordinator, entry, "api_index")
        self._attr_name = "Air Pollutant Index"
        self._attr_native_unit_of_measurement = "API"

    @property
    def native_value(self) -> Optional[int]:
        """Return current API reading."""
        data = self.coordinator.data or {}
        val = data.get("API")
        if val is not None:
            try:
                return int(val)
            except (ValueError, TypeError):
                return None
        return None

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return diagnostic attributes."""
        data = self.coordinator.data or {}
        return {
            "classification": data.get("CLASS"),
            "parameter_symbol": data.get("PARAM_SYMBOL"),
            "dominant_pollutant": data.get("PARAM_SELECTED"),
            "station_id": data.get("STATION_ID"),
            "station_location": data.get("STATION_LOCATION"),
            "place": data.get("PLACE"),
            "state": data.get("STATE_NAME"),
            "category": data.get("STATION_CATEGORY"),
            "latitude": data.get("LATITUDE"),
            "longitude": data.get("LONGITUDE"),
            "record_time": data.get("RECORD_DT") or data.get("DATETIME"),
        }


class MyEQMSClassSensor(MyEQMSBaseSensor):
    """Categorical air quality status sensor (Good, Moderate, Unhealthy, etc.)."""

    def __init__(self, coordinator: MyEQMSDataUpdateCoordinator, entry: ConfigEntry) -> None:
        """Initialize status sensor."""
        super().__init__(coordinator, entry, "air_quality_class")
        self._attr_name = "Air Quality Status"

    @property
    def native_value(self) -> Optional[str]:
        """Return categorical air quality status."""
        data = self.coordinator.data or {}
        return data.get("CLASS")

    @property
    def icon(self) -> str:
        """Return appropriate icon depending on air quality."""
        cls = (self.native_value or "").lower()
        if "good" in cls:
            return "mdi:emoticon-happy-outline"
        if "moderate" in cls:
            return "mdi:emoticon-neutral-outline"
        if "unhealthy" in cls and "very" not in cls:
            return "mdi:emoticon-sad-outline"
        if "very unhealthy" in cls:
            return "mdi:emoticon-dead-outline"
        if "hazardous" in cls:
            return "mdi:biohazard"
        return "mdi:weather-hazy"


class MyEQMSPollutantSensor(MyEQMSBaseSensor):
    """Dominant pollutant parameter sensor (e.g., PM2.5, PM10)."""

    _attr_icon = "mdi:molecule"

    def __init__(self, coordinator: MyEQMSDataUpdateCoordinator, entry: ConfigEntry) -> None:
        """Initialize pollutant sensor."""
        super().__init__(coordinator, entry, "dominant_pollutant")
        self._attr_name = "Dominant Pollutant"

    @property
    def native_value(self) -> Optional[str]:
        """Return dominant pollutant."""
        data = self.coordinator.data or {}
        return data.get("PARAM_SELECTED") or "PM2.5"


class MyEQMSLastUpdateSensor(MyEQMSBaseSensor):
    """Last update timestamp sensor."""

    _attr_icon = "mdi:clock-check-outline"

    def __init__(self, coordinator: MyEQMSDataUpdateCoordinator, entry: ConfigEntry) -> None:
        """Initialize timestamp sensor."""
        super().__init__(coordinator, entry, "last_updated")
        self._attr_name = "Last Updated"

    @property
    def native_value(self) -> Optional[str]:
        """Return timestamp string."""
        data = self.coordinator.data or {}
        return data.get("RECORD_DT") or data.get("DATETIME")
