"""Cloud API client for Runch Smart Coop."""

from __future__ import annotations

import asyncio
from typing import Any

from aiohttp import ClientError, ClientSession

from .const import (
    API_BASE_URL,
    AREA_CODE,
    COUNTRY_CODE,
    COUNTRY_NAME,
    REQUEST_TIMEOUT,
)


class SmartCoopError(Exception):
    """Base Smart Coop exception."""


class SmartCoopCannotConnect(SmartCoopError):
    """Raised when the Smart Coop cloud cannot be reached."""


class SmartCoopInvalidAuth(SmartCoopError):
    """Raised when Smart Coop authentication fails or expires."""


class SmartCoopApiError(SmartCoopError):
    """Raised when the Smart Coop API returns an application error."""


class SmartCoopApi:
    """Small async client for the API used by the Smart Coop Android app."""

    def __init__(self, session: ClientSession, email: str, password: str) -> None:
        self._session = session
        self._email = email
        self._password = password
        self._token: str | None = None

    @property
    def token(self) -> str | None:
        """Return the in-memory token for diagnostics; it is never persisted here."""
        return self._token

    async def async_login(self) -> None:
        """Authenticate and retain the returned token in memory."""
        payload = {
            "userName": self._email,
            "password": self._password,
            "areaCode": AREA_CODE,
            "countryCode": COUNTRY_CODE,
            "countryName": COUNTRY_NAME,
        }
        result = await self._async_request("/home/account/login", payload, auth=False)
        token = result.get("data", {}).get("token")
        if not token:
            raise SmartCoopInvalidAuth("Login succeeded without a token")
        self._token = str(token)

    async def async_get_devices(self) -> list[dict[str, Any]]:
        """Return all Smart Coop devices on the account."""
        result = await self._async_authenticated_request(
            "/home/system/getDeviceList", {}
        )
        devices = result.get("data") or []
        if not isinstance(devices, list):
            raise SmartCoopApiError("Unexpected device-list response")
        return devices

    async def async_get_one_device(self, mac: str) -> dict[str, Any]:
        """Return detailed state for one device."""
        result = await self._async_authenticated_request(
            "/home/System/getOneDevice", {"mac": mac}
        )
        data = result.get("data") or {}
        if not isinstance(data, dict):
            raise SmartCoopApiError("Unexpected device response")
        return data

    async def async_set_device(
        self, mac: str, exec_type: int | str, exec_content: Any
    ) -> dict[str, Any]:
        """Send one of the app's setDevice commands."""
        if isinstance(exec_content, bool):
            # Match the JavaScript app's form values exactly.
            exec_content = "true" if exec_content else "false"
        result = await self._async_authenticated_request(
            "/home/system/setDevice",
            {
                "mac": mac,
                "execType": str(exec_type),
                "execContent": str(exec_content),
            },
        )
        return result

    async def async_open(self, mac: str) -> dict[str, Any]:
        """Open the coop door (execType 1)."""
        return await self.async_set_device(mac, 1, True)

    async def async_close(self, mac: str) -> dict[str, Any]:
        """Close the coop door (execType 2)."""
        return await self.async_set_device(mac, 2, False)

    async def _async_authenticated_request(
        self, path: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        if not self._token:
            await self.async_login()

        try:
            return await self._async_request(path, payload, auth=True)
        except SmartCoopInvalidAuth:
            # The app itself treats errorCode 1002/1003 as an expired/invalid
            # session. Re-login once so HA survives normal token expiry.
            self._token = None
            await self.async_login()
            return await self._async_request(path, payload, auth=True)

    async def _async_request(
        self, path: str, payload: dict[str, Any], *, auth: bool
    ) -> dict[str, Any]:
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        if auth and self._token:
            headers["token"] = self._token

        try:
            async with asyncio.timeout(REQUEST_TIMEOUT):
                async with self._session.post(
                    f"{API_BASE_URL}{path}",
                    data=payload,
                    headers=headers,
                ) as response:
                    if response.status >= 500:
                        raise SmartCoopCannotConnect(
                            f"Smart Coop server returned HTTP {response.status}"
                        )
                    if response.status >= 400:
                        raise SmartCoopApiError(
                            f"Smart Coop server returned HTTP {response.status}"
                        )
                    try:
                        result = await response.json(content_type=None)
                    except (ValueError, TypeError) as err:
                        text = await response.text()
                        raise SmartCoopApiError(
                            f"Smart Coop returned invalid JSON: {text[:200]}"
                        ) from err
        except (TimeoutError, ClientError) as err:
            raise SmartCoopCannotConnect(str(err)) from err

        if not isinstance(result, dict):
            raise SmartCoopApiError("Unexpected Smart Coop API response")

        code = result.get("errorCode")
        if code == 0:
            return result

        message = str(result.get("message") or f"Smart Coop error {code}")

        # The Android app explicitly redirects to login for these codes.
        if code in (1002, 1003):
            raise SmartCoopInvalidAuth(message)

        # During login, any application-level rejection is an auth failure.
        if not auth:
            raise SmartCoopInvalidAuth(message)

        raise SmartCoopApiError(f"{message} (errorCode {code})")
