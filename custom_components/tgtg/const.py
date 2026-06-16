"""Constants for the Too Good To Go integration."""

DOMAIN = "tgtg"
PLATFORMS = ["sensor"]

CONF_EMAIL = "email"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_ITEM_IDS = "item_ids"

DEFAULT_SCAN_INTERVAL = 5  # minutes
MIN_SCAN_INTERVAL = 1

# Coordinator update key
COORDINATOR = "coordinator"
TGTG_CLIENT = "tgtg_client"

# Sensor attributes
ATTR_ITEM_ID = "item_id"
ATTR_STORE_NAME = "store_name"
ATTR_STORE_BRANCH = "store_branch"
ATTR_STORE_LOGO = "store_logo"
ATTR_ITEM_NAME = "item_name"
ATTR_ITEM_COVER_IMAGE = "item_cover_image"
ATTR_ITEMS_AVAILABLE = "items_available"
ATTR_ITEMS_MAX = "items_max"
ATTR_PICKUP_START = "pickup_start"
ATTR_PICKUP_END = "pickup_end"
ATTR_PRICE = "price"
ATTR_PRICE_INCLUDING_TAXES = "price_including_taxes"
ATTR_CURRENCY = "currency"
ATTR_DESCRIPTION = "description"
ATTR_FAVORITE = "favorite"
ATTR_SOLD_OUT = "sold_out"
ATTR_STORE_ADDRESS = "store_address"
ATTR_RATING = "rating"
ATTR_STORE_LATITUDE = "store_latitude"
ATTR_STORE_LONGITUDE = "store_longitude"
ATTR_DISTANCE_KM = "distance_km"
