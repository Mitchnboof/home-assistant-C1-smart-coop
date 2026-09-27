"""Config flow for Smart Coop."""

from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import SmartCoopApi, SmartCoopApiError, SmartCoopCannotConnect, SmartCoopInvalidAuth
from .const import CONF_EMAIL, DOMAIN


async def _validate_input(hass: HomeAssistant, data: dict[str, str]) -> None:
    api = SmartCoopApi(
        async_get_clientsession(hass),
        data[CONF_EMAIL],
        data[CONF_PASSWORD],
    )
    await api.async_login()
    devices = await api.async_get_devices()
    if not devices:
        raise SmartCoopApiError("No Smart Coop devices found on this account")


class SmartCoopConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Smart Coop."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, str] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            user_input[CONF_EMAIL] = user_input[CONF_EMAIL].strip()
            try:
                await _validate_input(self.hass, user_input)
            except SmartCoopInvalidAuth:
                errors["base"] = "invalid_auth"
            except SmartCoopCannotConnect:
                errors["base"] = "cannot_connect"
            except SmartCoopApiError:
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(user_input[CONF_EMAIL].lower())
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title="Smart Coop",
                    data=user_input,
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_EMAIL): str,
                vol.Required(CONF_PASSWORD): str,
            }
        )
        return self.async_show_form(
            step_id="user", data_schema=schema, errors=errors
        )

    async def async_step_reauth(self, entry_data: dict[str, str]) -> FlowResult:
        """Start reauthentication."""
        self._reauth_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, str] | None = None
    ) -> FlowResult:
        """Confirm new credentials."""
        errors: dict[str, str] = {}
        entry = self._reauth_entry
        if entry is None:
            return self.async_abort(reason="reauth_failed")

        if user_input is not None:
            new_data = {
                **entry.data,
                CONF_PASSWORD: user_input[CONF_PASSWORD],
            }
            try:
                await _validate_input(self.hass, new_data)
            except SmartCoopInvalidAuth:
                errors["base"] = "invalid_auth"
            except SmartCoopCannotConnect:
                errors["base"] = "cannot_connect"
            except SmartCoopApiError:
                errors["base"] = "unknown"
            else:
                self.hass.config_entries.async_update_entry(entry, data=new_data)
                await self.hass.config_entries.async_reload(entry.entry_id)
                return self.async_abort(reason="reauth_successful")

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_PASSWORD): str}),
            errors=errors,
        )
