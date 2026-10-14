"""
Client library for Malaysia Department of Environment (DOE) MyEQMS / APIMS Air Quality API.
Reverse-engineered from https://eqms.doe.gov.my/APIMS/main
"""

import math
import urllib.request
import urllib.parse
import ssl
import json
from typing import List, Dict, Optional, Any

BASE_URL = "https://eqms.doe.gov.my/api3"
USER_AGENT = "HomeAssistant-MyEQMS/1.0"


def _get_ssl_context() -> ssl.SSLContext:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def fetch_all_stations() -> List[Dict[str, Any]]:
    """Fetch all 68 active CAQM air quality stations across Malaysia."""
    url = f"{BASE_URL}/publicportalapims/mapcaqm"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(req, context=_get_ssl_context(), timeout=20) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        return data.get("data", [])


def fetch_nearest_station(lat: float, lon: float) -> Optional[str]:
    """Find the nearest station ID using coordinates."""
    params = urllib.parse.urlencode({"latitude": lat, "longitude": lon})
    url = f"{BASE_URL}/publicportalapims/getstationidbylonglat?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(req, context=_get_ssl_context(), timeout=20) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        items = data.get("data", [])
        if items and "STATION_ID" in items[0]:
            return items[0]["STATION_ID"]
    return None


def fetch_station_reading(station_id: str) -> Optional[Dict[str, Any]]:
    """Fetch the latest air quality reading and metadata for a specific station ID."""
    params = urllib.parse.urlencode({"stationid": station_id})
    url = f"{BASE_URL}/publicportalapims/currentapicurrentlocation?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(req, context=_get_ssl_context(), timeout=20) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        items = data.get("data", [])
        if items:
            return items[0]
    return None


if __name__ == "__main__":
    print("Testing MyEQMS API Client...")
    print("\n1. Fetching all stations:")
    stations = fetch_all_stations()
    print(f"Total stations found: {len(stations)}")
    for s in stations[:3]:
        print(f"  - [{s.get('STATION_ID')}] {s.get('STATION_LOCATION')} (API: {s.get('API')}, Class: {s.get('CLASS')})")

    print("\n2. Finding nearest station to Kuala Lumpur (3.1390, 101.6869):")
    nearest_id = fetch_nearest_station(3.1390, 101.6869)
    print(f"Nearest Station ID: {nearest_id}")

    if nearest_id:
        print(f"\n3. Fetching reading for {nearest_id}:")
        reading = fetch_station_reading(nearest_id)
        print(json.dumps(reading, indent=2))
