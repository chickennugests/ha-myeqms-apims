# Malaysia APIMS (DOE MyEQMS) Air Quality Integration

Reverse-engineered API and Home Assistant integration for the Malaysia Department of Environment (Jabatan Alam Sekitar / JAS) **Air Pollutant Index Management System (APIMS / MyEQMS)** at [https://eqms.doe.gov.my/APIMS/main](https://eqms.doe.gov.my/APIMS/main).

---

## 🔍 Discovered Direct REST API Endpoints

The web portal is a Vue/Quasar SPA that communicates with a public REST API at `https://eqms.doe.gov.my/api3`. You do **not** need web scraping or headless browsers—all data is accessible via lightweight JSON calls:

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `https://eqms.doe.gov.my/api3/publicportalapims/mapcaqm` | `GET` | Returns **all 68 air quality monitoring stations** across Malaysia, including current API reading, status classification, coordinates, and timestamp in a single response. |
| `https://eqms.doe.gov.my/api3/publicportalapims/currentapicurrentlocation?stationid={STATION_ID}` | `GET` | Returns real-time reading and extended metadata (`PLACE`, `STATION_CATEGORY`, `PARAM_SELECTED`) for a specific station. |
| `https://eqms.doe.gov.my/api3/publicportalapims/getstationidbylonglat?latitude={LAT}&longitude={LON}` | `GET` | Returns the nearest station ID and calculated distance (km) based on GPS coordinates. |
| `https://eqms.doe.gov.my/api3/publicportalapims/apitablehourly?stateid={STATE_ID}&datetime={DATETIME}` | `GET` | Returns 24-hour historical hourly readings for all stations or filtered by state. |
| `https://eqms.doe.gov.my/api3/publicportalapims/statelist` | `GET` | Returns the list of Malaysian states and their IDs. |
| `https://eqms.doe.gov.my/api3/publicportalapims/apiranking` | `GET` | Returns top stations with the cleanest air rankings. |

---

## 🚀 Option 1: Quick Setup via `configuration.yaml` (No Custom Component Needed)

If you just want sensors without installing custom files, add this directly to your Home Assistant `configuration.yaml`.

Replace `CA17W` with your preferred station ID (e.g. `CA17W` for Putrajaya, `CA16W` for Cheras KL, `CA01R` for Kangar, etc.):

```yaml
sensor:
  - platform: rest
    name: "APIMS Air Quality"
    resource: "https://eqms.doe.gov.my/api3/publicportalapims/currentapicurrentlocation?stationid=CA17W"
    scan_interval: 1800 # 30 minutes
    value_template: "{{ value_json.data[0].API if value_json.data[0].API is not none else 'N/A' }}"
    unit_of_measurement: "API"
    device_class: aqi
    state_class: measurement
    icon: mdi:air-filter
    json_attributes_path: "$.data[0]"
    json_attributes:
      - CLASS
      - PARAM_SELECTED
      - STATION_LOCATION
      - PLACE
      - DATETIME
      - LATITUDE
      - LONGITUDE

  - platform: template
    sensors:
      apims_air_quality_status:
        friendly_name: "APIMS Air Quality Status"
        value_template: "{{ state_attr('sensor.apims_air_quality', 'CLASS') }}"
        icon_template: >
          {% set status = state_attr('sensor.apims_air_quality', 'CLASS') | lower %}
          {% if 'good' in status %} mdi:emoticon-happy-outline
          {% elif 'moderate' in status %} mdi:emoticon-neutral-outline
          {% elif 'unhealthy' in status %} mdi:emoticon-sad-outline
          {% elif 'hazardous' in status %} mdi:biohazard
          {% else %} mdi:weather-hazy
          {% endif %}

      apims_dominant_pollutant:
        friendly_name: "APIMS Dominant Pollutant"
        value_template: "{{ state_attr('sensor.apims_air_quality', 'PARAM_SELECTED') | default('PM2.5', true) }}"
        icon_template: mdi:molecule
```

---

## 📦 Option 2: Full Custom Component Integration (`custom_components/myeqms_apims`)

This repository contains a full Home Assistant custom integration featuring:
- **UI Config Flow**: Auto-detects the nearest station using your Home Assistant GPS coordinates, or lets you choose from a sorted dropdown of all 68 stations.
- **Dedicated Entities**:
  - `sensor.<station>_air_pollutant_index` (native AQI device class)
  - `sensor.<station>_air_quality_status` (Good, Moderate, Unhealthy, etc. with dynamic icons)
  - `sensor.<station>_dominant_pollutant` (PM2.5, etc.)
  - `sensor.<station>_last_updated` (timestamp)
- **Automatic 30-minute background polling** via Home Assistant's `DataUpdateCoordinator`.

### Installation Steps:
1. Copy the `custom_components/myeqms_apims` folder into your Home Assistant directory:
   ```text
   /config/custom_components/myeqms_apims/
   ├── __init__.py
   ├── config_flow.py
   ├── const.py
   ├── coordinator.py
   ├── manifest.json
   ├── sensor.py
   ├── strings.json
   └── translations/
       └── en.json
   ```
2. Restart Home Assistant.
3. In Home Assistant, navigate to **Settings** -> **Devices & Services** -> **Add Integration**.
4. Search for **Malaysia APIMS (DOE MyEQMS)**.
5. Confirm or select your desired station.

---

## 🐍 Standalone Python CLI / Helper

Run `myeqms_client.py` on any machine with Python 3:

```bash
python myeqms_client.py
```

It outputs all stations, resolves coordinates to the nearest station ID, and displays live data.
