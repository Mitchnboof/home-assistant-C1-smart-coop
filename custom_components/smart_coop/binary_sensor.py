"""Binary sensor platform for Smart Coop."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DATA_COORDINATOR, DOMAIN
from .coordinator import SmartCoopCoordinator
from .entity import SmartCoopEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Smart Coop binary sensors."""
    coordinator: SmartCoopCoordinator = hass.data[DOMAIN][entry.entry_id][
        DATA_COORDINATOR
    ]
    entities = []
    for mac in coordinator.data:
        entities.extend(
            (
                SmartCoopOnlineSensor(coordinator, mac),
                SmartCoopChargingSensor(coordinator, mac),
            )
        )
    async_add_entities(entities)


class SmartCoopOnlineSensor(SmartCoopEntity, BinarySensorEntity):
    """Cloud-reported device connectivity."""

    _attr_translation_key = "online"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: SmartCoopCoordinator, mac: str) -> None:
        super().__init__(coordinator, mac)
        self._attr_unique_id = f"{self.mac}_online"

    @property
    def is_on(self) -> bool | None:
        value = self.device_data.get("online_status")
        return bool(value) if value is not None else None

    @property
    def available(self) -> bool:
        # This entity must remain available to report that the physical device is offline.
        return bool(self.coordinator.last_update_success and self.device_data)


class SmartCoopChargingSensor(SmartCoopEntity, BinarySensorEntity):
    """Cloud-reported charging state."""

    _attr_translation_key = "charging"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:battery-charging"

    def __init__(self, coordinator: SmartCoopCoordinator, mac: str) -> None:
        super().__init__(coordinator, mac)
        self._attr_unique_id = f"{self.mac}_charging"

    @property
    def is_on(self) -> bool | None:
        value = self.device_data.get("charging")
        return bool(value) if value is not None else None
