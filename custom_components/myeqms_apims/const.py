"""Constants for the Malaysia APIMS (DOE MyEQMS) integration."""

DOMAIN = "myeqms_apims"

API_BASE_URL = "https://eqms.doe.gov.my/api3"
ENDPOINT_MAPCAQM = "/publicportalapims/mapcaqm"
ENDPOINT_CURRENT_LOCATION = "/publicportalapims/currentapicurrentlocation"
ENDPOINT_NEAREST_STATION = "/publicportalapims/getstationidbylonglat"

CONF_STATION_ID = "station_id"
CONF_STATION_NAME = "station_name"
CONF_AUTO_DETECT = "auto_detect"

DEFAULT_SCAN_INTERVAL = 1800  # 30 minutes in seconds

ATTRIBUTION = "Data provided by Department of Environment Malaysia (MyEQMS / APIMS)"
