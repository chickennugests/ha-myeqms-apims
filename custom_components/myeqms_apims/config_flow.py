"""Config flow for Malaysia APIMS (DOE MyEQMS) integration."""

from typing import Any, Dict, Optional
import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    API_BASE_URL,
    CONF_AUTO_DETECT,
    CONF_STATION_ID,
    CONF_STATION_NAME,
    DOMAIN,
    ENDPOINT_MAPCAQM,
    ENDPOINT_NEAREST_STATION,
)


async def _async_get_stations(hass: HomeAssistant) -> Dict[str, str]:
    """Fetch dictionary of station_id -> display_name."""
    session = async_get_clientsession(hass, verify_ssl=False)
    url = f"{API_BASE_URL}{ENDPOINT_MAPCAQM}"
    stations: Dict[str, str] = {}
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            if resp.status == 200:
                payload = await resp.json(content_type=None)
                for item in payload.get("data", []):
                    s_id = item.get("STATION_ID")
                    loc = item.get("STATION_LOCATION", s_id)
                    state = item.get("STATE_NAME", "")
                    if s_id:
                        display = f"{state} - {loc} ({s_id})" if state else f"{loc} ({s_id})"
                        stations[s_id] = display
    except Exception:
        pass
    return dict(sorted(stations.items(), key=lambda x: x[1]))


async def _async_get_nearest_station(hass: HomeAssistant, lat: float, lon: float) -> Optional[str]:
    """Find nearest station ID using coordinates."""
    session = async_get_clientsession(hass, verify_ssl=False)
    url = f"{API_BASE_URL}{ENDPOINT_NEAREST_STATION}?latitude={lat}&longitude={lon}"
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            if resp.status == 200:
                payload = await resp.json(content_type=None)
                items = payload.get("data", [])
                if items and "STATION_ID" in items[0]:
                    return items[0]["STATION_ID"]
    except Exception:
        pass
    return None


class MyEQMSConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for MyEQMS APIMS."""

    VERSION = 1

    async def async_step_user(self, user_input: Optional[Dict[str, Any]] = None) -> FlowResult:
        """Handle the initial user setup step."""
        errors: Dict[str, str] = {}
        stations = await _async_get_stations(self.hass)

        if not stations:
            errors["base"] = "cannot_connect"

        default_station = None
        has_location = bool(self.hass.config.latitude and self.hass.config.longitude)

        if has_location and not default_station:
            nearest = await _async_get_nearest_station(
                self.hass, self.hass.config.latitude, self.hass.config.longitude
            )
            if nearest and nearest in stations:
                default_station = nearest

        if not default_station and stations:
            default_station = list(stations.keys())[0]

        if user_input is not None and not errors:
            station_id = user_input.get(CONF_STATION_ID)
            station_name = stations.get(station_id, station_id)

            await self.async_set_unique_id(station_id)
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=station_name,
                data={
                    CONF_STATION_ID: station_id,
                    CONF_STATION_NAME: station_name,
                },
            )

        schema = vol.Schema(
            {
                vol.Required(CONF_STATION_ID, default=default_station): vol.In(stations),
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
