"""Cover platform for Smart Coop."""

from __future__ import annotations

from typing import Any

from homeassistant.components.cover import (
    ATTR_POSITION,
    CoverDeviceClass,
    CoverEntity,
    CoverEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
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
    """Set up Smart Coop covers."""
    coordinator: SmartCoopCoordinator = hass.data[DOMAIN][entry.entry_id][
        DATA_COORDINATOR
    ]
    async_add_entities(
        SmartCoopDoor(coordinator, mac) for mac in coordinator.data
    )


class SmartCoopDoor(SmartCoopEntity, CoverEntity):
    """A Smart Coop chicken door."""

    _attr_name = None
    _attr_device_class = CoverDeviceClass.DOOR
    _attr_supported_features = CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE

    def __init__(self, coordinator: SmartCoopCoordinator, mac: str) -> None:
        super().__init__(coordinator, mac)
        self._attr_unique_id = f"{self.mac}_door"

    @property
    def is_closed(self) -> bool | None:
        """Return true when the cloud explicitly reports door_status 0."""
        status = self.device_data.get("door_status")
        if status == 0:
            return True
        if status in (1, 3):
            return False
        return None

    @property
    def current_cover_position(self) -> int | None:
        """Return a binary 0/100 position where the state is known."""
        closed = self.is_closed
        if closed is True:
            return 0
        if closed is False:
            return 100
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose raw cloud status for diagnosis while we learn all status codes."""
        return {
            "mac": self.mac,
            "raw_door_status": self.device_data.get("door_status"),
        }

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Open the coop door."""
        await self.coordinator.api.async_open(self.mac)
        await self.coordinator.async_request_refresh()

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Close the coop door."""
        await self.coordinator.api.async_close(self.mac)
        await self.coordinator.async_request_refresh()
