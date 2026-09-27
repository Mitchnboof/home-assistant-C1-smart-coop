# Smart Coop (Runch) for Home Assistant

Unofficial Home Assistant custom integration for the Runch Network Tech **Smart Coop** Wi-Fi chicken-door app (`xin.yysf.wifidoor`).

This integration was reverse-engineered from **Smart Coop Android 1.2.4** and verified against real C1 hardware. Authentication, device discovery, live state, OPEN and CLOSE commands all work independently of the Smart Coop mobile app.

> **Current version:** v0.1.0 — field tested on a Smart Coop C1 door.

## Features

- Home Assistant `cover` entity for the coop door
  - Open
  - Close
  - Open/closed state from the Smart Coop cloud
- Battery percentage
- Online/offline status
- Charging state
- Current light level
- Opening mode
- Configured opening/closing times
- Light-opening threshold
- Closing strength
- Disabled-by-default raw door-status sensor for diagnostics

The original Smart Coop mobile app continues to work normally alongside Home Assistant.

## Installation

### HACS custom repository

1. In HACS, open **Integrations**.
2. Add this repository as a **Custom repository**:
   `https://github.com/Mitchnboof/home-assistant-C1-smart-coop`
3. Select category **Integration**.
4. Install **Smart Coop (Runch)**.
5. Restart Home Assistant.
6. Go to **Settings → Devices & services → Add integration**.
7. Search for **Smart Coop (Runch)** and sign in using the same email/password as the Smart Coop app.

### Manual installation

Copy `custom_components/smart_coop` into your Home Assistant `/config/custom_components/` directory, restart Home Assistant, then add **Smart Coop (Runch)** from **Settings → Devices & services**.

No YAML is required.

## Cloud dependency

The integration currently uses the same Runch cloud API as the official Smart Coop app:

`https://door.app198.com/index.php`

If the Runch service is unavailable, remote control and state updates will be unavailable. Any schedules already stored in the physical controller continue to run independently.

## Reverse-engineered API

The integration uses:

- `POST /home/account/login`
- `POST /home/system/getDeviceList`
- `POST /home/System/getOneDevice`
- `POST /home/system/setDevice`

Authentication uses the API's `token` HTTP header. The integration logs in at startup and automatically re-authenticates when the API reports an expired/invalid session. Account credentials are stored in the Home Assistant config entry; the session token is held in memory.

Door commands verified against real C1 hardware:

- `execType=1`, `execContent=true` → **OPEN**
- `execType=2`, `execContent=false` → **CLOSE**

## Known limitations

- v0.1.0 currently uses Australian login metadata (`areaCode=61`, `countryCode=AU`, `countryName=Australia`) because this is the verified account path. Support for other regions needs testing.
- Door state codes `0 = closed` and `1 = open` are verified. The official app also treats code `3` as an open/on state, so the integration treats `3` as not closed and exposes the raw status code for diagnostics.
- Timer/mode/light/close-strength settings are read-only in v0.1.0. They can still be edited in the official Smart Coop app.
- This is an unofficial reverse-engineered integration and is not affiliated with Runch Network Tech.

## Privacy and security

- Your Smart Coop password is used only to authenticate with the Runch cloud API through Home Assistant.
- The API session token is retained in memory by the integration and is not deliberately exposed as an entity or diagnostic attribute.
- Do not post Home Assistant logs containing account credentials or API tokens in public issues.

## Contributing / testing

Reports from other Smart Coop / C1 owners are very welcome, especially:

- whether non-Australian accounts can authenticate
- additional `door_status` codes
- other hardware revisions using the Smart Coop app
- behaviour when the cloud service is unavailable

Please open an issue with your Home Assistant version, integration version, door model, and sanitized logs.

## License

MIT. See [LICENSE](LICENSE).
