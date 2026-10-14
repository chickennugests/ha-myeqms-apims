"""DataUpdateCoordinator for Malaysia APIMS (DOE MyEQMS)."""

from datetime import timedelta
import logging
from typing import Any, Dict, Optional

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    API_BASE_URL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    ENDPOINT_CURRENT_LOCATION,
    ENDPOINT_MAPCAQM,
)

_LOGGER = logging.getLogger(__name__)


class MyEQMSDataUpdateCoordinator(DataUpdateCoordinator[Dict[str, Any]]):
    """Class to manage fetching APIMS air quality data."""

    def __init__(self, hass: HomeAssistant, station_id: str, station_name: str) -> None:
        """Initialize coordinator."""
        self.station_id = station_id
        self.station_name = station_name
        self.session = async_get_clientsession(hass, verify_ssl=False)

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{station_id}",
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )

    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch data from MyEQMS API."""
        result: Dict[str, Any] = {}

        # 1. Fetch mapcaqm (contains latest readings for all stations)
        map_url = f"{API_BASE_URL}{ENDPOINT_MAPCAQM}"
        try:
            async with self.session.get(
                map_url,
                headers={"User-Agent": "HomeAssistant-MyEQMS", "Accept": "application/json"},
                timeout=aiohttp.ClientTimeout(total=20),
            ) as resp:
                if resp.status != 200:
                    raise UpdateFailed(f"Error fetching stations list: HTTP {resp.status}")
                payload = await resp.json(content_type=None)
                data_list = payload.get("data", [])
                for item in data_list:
                    if item.get("STATION_ID") == self.station_id:
                        result.update(item)
                        break
        except Exception as err:
            _LOGGER.error("Failed to fetch mapcaqm from MyEQMS: %s", err)
            raise UpdateFailed(f"Communication error with MyEQMS API: {err}") from err

        if not result:
            raise UpdateFailed(f"Station {self.station_id} not found in MyEQMS response")

        # 2. Try to fetch detailed station reading (for dominant pollutant / param_selected)
        detail_url = f"{API_BASE_URL}{ENDPOINT_CURRENT_LOCATION}?stationid={self.station_id}"
        try:
            async with self.session.get(
                detail_url,
                headers={"User-Agent": "HomeAssistant-MyEQMS", "Accept": "application/json"},
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                if resp.status == 200:
                    detail_payload = await resp.json(content_type=None)
                    detail_items = detail_payload.get("data", [])
                    if detail_items and isinstance(detail_items, list):
                        detail = detail_items[0]
                        # Augment fields if present
                        for key in ["PARAM_SELECTED", "PLACE", "STATION_CATEGORY", "REGION_NAME", "LOT_INFO"]:
                            if detail.get(key):
                                result[key] = detail[key]
        except Exception as err:
            _LOGGER.debug("Could not fetch secondary station details (non-critical): %s", err)

        return result
