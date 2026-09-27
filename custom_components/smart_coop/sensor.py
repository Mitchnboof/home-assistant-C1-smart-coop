"""Sensor platform for Smart Coop."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DATA_COORDINATOR, DOMAIN
from .coordinator import SmartCoopCoordinator
from .entity import SmartCoopEntity


@dataclass(frozen=True, kw_only=True)
class SmartCoopSensorDescription(SensorEntityDescription):
    """Describe a Smart Coop sensor."""

    value_fn: Callable[[dict[str, Any]], Any]


def _mode(data: dict[str, Any]) -> str | None:
    value = data.get("open_mode")
    return {0: "manual", 1: "timer", 2: "light"}.get(value, str(value) if value is not None else None)


def _time_value(key: str) -> Callable[[dict[str, Any]], str | None]:
    def value(data: dict[str, Any]) -> str | None:
        raw = data.get(key)
        if not isinstance(raw, dict):
            return None
        try:
            return f"{int(raw.get('hour', 0)):02d}:{int(raw.get('min', 0)):02d}"
        except (TypeError, ValueError):
            return None

    return value


SENSORS: tuple[SmartCoopSensorDescription, ...] = (
    SmartCoopSensorDescription(
        key="battery",
        translation_key="battery",
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: min(100, max(0, int(data.get("power", 0)) * 20))
        if data.get("power") is not None
        else None,
    ),
    SmartCoopSensorDescription(
        key="brightness",
        translation_key="brightness",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.get("brightness"),
    ),
    SmartCoopSensorDescription(
        key="open_mode",
        translation_key="open_mode",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_mode,
    ),
    SmartCoopSensorDescription(
        key="opening_time",
        translation_key="opening_time",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_time_value("time_open"),
    ),
    SmartCoopSensorDescription(
        key="closing_time",
        translation_key="closing_time",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_time_value("time_close"),
    ),
    SmartCoopSensorDescription(
        key="light_open_threshold",
        translation_key="light_open_threshold",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.get("brightness_open"),
    ),
    SmartCoopSensorDescription(
        key="close_strength",
        translation_key="close_strength",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.get("close_strength"),
    ),
    SmartCoopSensorDescription(
        key="raw_door_status",
        translation_key="raw_door_status",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda data: data.get("door_status"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Smart Coop sensors."""
    coordinator: SmartCoopCoordinator = hass.data[DOMAIN][entry.entry_id][
        DATA_COORDINATOR
    ]
    async_add_entities(
        SmartCoopSensor(coordinator, mac, description)
        for mac in coordinator.data
        for description in SENSORS
    )


class SmartCoopSensor(SmartCoopEntity, SensorEntity):
    """A Smart Coop sensor."""

    entity_description: SmartCoopSensorDescription

    def __init__(
        self,
        coordinator: SmartCoopCoordinator,
        mac: str,
        description: SmartCoopSensorDescription,
    ) -> None:
        super().__init__(coordinator, mac)
        self.entity_description = description
        self._attr_unique_id = f"{self.mac}_{description.key}"

    @property
    def native_value(self) -> Any:
        """Return current sensor value."""
        return self.entity_description.value_fn(self.device_data)
