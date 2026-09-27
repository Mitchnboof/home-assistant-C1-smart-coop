"""Data coordinator for Smart Coop."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    SmartCoopApi,
    SmartCoopApiError,
    SmartCoopCannotConnect,
    SmartCoopInvalidAuth,
)
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class SmartCoopCoordinator(DataUpdateCoordinator[dict[str, dict[str, Any]]]):
    """Poll account devices and expose them by MAC address."""

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, api: SmartCoopApi
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            config_entry=entry,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.api = api

    async def _async_update_data(self) -> dict[str, dict[str, Any]]:
        try:
            devices = await self.api.async_get_devices()
        except SmartCoopInvalidAuth as err:
            raise ConfigEntryAuthFailed from err
        except (SmartCoopCannotConnect, SmartCoopApiError) as err:
            raise UpdateFailed(str(err)) from err

        result: dict[str, dict[str, Any]] = {}
        for device in devices:
            mac = device.get("mac")
            if mac:
                result[str(mac).upper()] = device
        return result
