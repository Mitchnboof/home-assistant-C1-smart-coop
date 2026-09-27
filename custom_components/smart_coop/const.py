"""Constants for the Smart Coop integration."""

from __future__ import annotations

DOMAIN = "smart_coop"

CONF_EMAIL = "email"
CONF_PASSWORD = "password"

API_BASE_URL = "https://door.app198.com/index.php"
DEFAULT_SCAN_INTERVAL = 10
REQUEST_TIMEOUT = 20

# The Android app sends these fields for a normal email/password login.
# These defaults match the working Australian account/API exchange used to
# reverse-engineer this integration.
AREA_CODE = "61"
COUNTRY_CODE = "AU"
COUNTRY_NAME = "Australia"

DATA_API = "api"
DATA_COORDINATOR = "coordinator"

MANUFACTURER = "Runch Network Tech"
MODEL = "Smart Coop Wi-Fi Door"
