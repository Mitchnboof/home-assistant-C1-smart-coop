"""Base entities for Smart Coop."""

from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER, MODEL
from .coordinator import SmartCoopCoordinator


class SmartCoopEntity(CoordinatorEntity[SmartCoopCoordinator]):
    """Base Smart Coop entity."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: SmartCoopCoordinator, mac: str) -> None:
        super().__init__(coordinator)
        self.mac = mac.upper()

    @property
    def device_data(self) -> dict[str, Any]:
        """Return current device data."""
        return self.coordinator.data.get(self.mac, {})

    @property
    def device_info(self) -> DeviceInfo:
        """Return HA device-registry information."""
        name = (
            self.device_data.get("device_name")
            or self.device_data.get("deviceName")
            or self.mac
        )
        return DeviceInfo(
            identifiers={(DOMAIN, self.mac)},
            name=str(name),
            manufacturer=MANUFACTURER,
            model=MODEL,
        )

    @property
    def available(self) -> bool:
        """Entity is available when the cloud poll works and device is online."""
        return bool(
            self.coordinator.last_update_success
            and self.device_data
            and self.device_data.get("online_status") == 1
        )
