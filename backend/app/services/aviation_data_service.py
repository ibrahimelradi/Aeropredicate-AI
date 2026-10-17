"""
Aviation Data Service
======================
Integrates free aviation APIs for real-time weather and flight tracking.
"""

import requests
from datetime import datetime
from typing import Dict, Optional

# NOAA Aviation Weather API (no auth required)
NOAA_METAR_BASE = "https://aviationweather.gov/api/data/metar"
NOAA_TAF_BASE = "https://aviationweather.gov/api/data/taf"

def get_metar(icao_code: str) -> Optional[Dict]:
    """
    Fetch current METAR for an airport.
    Returns parsed weather data or None if unavailable.
    """
    try:
        # Convert common codes (e.g., IST -> LTBA if needed)
        # For demo, assume ICAO codes are used
        response = requests.get(
            NOAA_METAR_BASE,
            params={"ids": icao_code, "format": "json", "date": "now"},
            timeout=5
        )
        if response.status_code == 200 and response.text.strip():
            data = response.json()
            if data:
                return data[0] if isinstance(data, list) else data
    except Exception as e:
        print(f"METAR fetch error for {icao_code}: {str(e)[:100]}")
    return None

def get_taf(icao_code: str) -> Optional[Dict]:
    """
    Fetch Terminal Aerodrome Forecast (TAF) for weather predictions.
    """
    try:
        response = requests.get(
            NOAA_TAF_BASE,
            params={"ids": icao_code, "format": "json", "date": "now"},
            timeout=5
        )
        if response.status_code == 200 and response.text.strip():
            data = response.json()
            if data:
                return data[0] if isinstance(data, list) else data
    except Exception as e:
        print(f"TAF fetch error for {icao_code}: {str(e)[:100]}")
    return None

def parse_weather_severity(metar_data: Dict) -> float:
    """
    Convert METAR data to a weather severity score (0-1).
    Higher = worse weather conditions.
    """
    if not metar_data:
        return 0.25  # Default moderate risk

    severity = 0.0

    # Check flight category
    flt_cat = metar_data.get("fltCat", "VFR")
    cat_mapping = {"CAVU": 0.0, "VFR": 0.1, "MVFR": 0.4, "IFR": 0.7, "LIFR": 0.9}
    severity += cat_mapping.get(flt_cat, 0.25)

    # Check for precipitation
    raw_obscuration = metar_data.get("rawObscuration", "").lower()
    if any(x in raw_obscuration for x in ["rain", "snow", "storm", "fog", "ice"]):
        severity += 0.3
    if any(x in raw_obscuration for x in ["moderate", "heavy"]):
        severity += 0.4

    # Check wind speed (sustained)
    wspd = metar_data.get("wspd", 0)
    if wspd:
        try:
            wspd_val = int(wspd)
            if wspd_val > 30:
                severity += 0.3
            elif wspd_val > 20:
                severity += 0.2
            elif wspd_val > 15:
                severity += 0.1
        except (ValueError, TypeError):
            pass

    # Check visibility
    vis = metar_data.get("visib", "9999")
    try:
        vis_val = int(vis)
        if vis_val < 1:
            severity += 0.5
        elif vis_val < 3:
            severity += 0.3
        elif vis_val < 5:
            severity += 0.1
    except (ValueError, TypeError):
        pass

    return min(max(severity, 0.0), 1.0)

def get_airport_weather_severity(icao_code: str) -> float:
    """
    Get real-time weather severity score for an airport.
    """
    # Try METAR first, then TAF if METAR is missing
    metar = get_metar(icao_code)
    if metar:
        return parse_weather_severity(metar)

    # Fallback: try TAF
    taf = get_taf(icao_code)
    if taf:
        # Parse first TAF line for basic severity
        raw_text = taf.get("rawTAF", "").upper()
        if any(x in raw_text for x in ["TEMPO", "INTER", "PROB"]):
            return 0.4
        if "FEW" in raw_text or "SKC" in raw_text:
            return 0.1
        return 0.25

    return 0.25  # Default fallback

# OpenSky Network integration (requires free API key)
OPEN_SKY_BASE = "https://opensky-network.org/api/states/all"

def get_live_traffic(icao_codes: list = None) -> Dict:
    """
    Get live aircraft positions from OpenSky Network.
    Returns dict with traffic information.
    """
    import os

    username = os.getenv("OPEN_SKY_USERNAME")
    password = os.getenv("OPEN_SKY_PASSWORD")

    if not username or not password:
        # Without auth, get all aircraft (rate limited)
        url = OPEN_SKY_BASE
        auth = None
    else:
        url = OPEN_SKY_BASE
        auth = (username, password)

    try:
        response = requests.get(url, auth=auth, timeout=10)
        if response.status_code == 200:
            data = response.json()
            aircraft_count = len(data.get("states", []))
            return {
                "total_aircraft": aircraft_count,
                "timestamp": data.get("time", int(datetime.now().timestamp()))
            }
    except Exception as e:
        print(f"OpenSky fetch error: {str(e)[:100]}")

    return {"total_aircraft": 0, "timestamp": int(datetime.now().timestamp())}

# Airport ICAO code mapping (common IATA -> ICAO)
AIRPORT_ICAO_MAP = {
    "IST": "LTBA",  # Istanbul Atatürk -> Istanbul Airport
    "SAW": "LTFJ",  # Sabiha Gokcen
    "ESB": "LTAF",  # Esenboğa
    "JFK": "KJFK",
    "LHR": "EGLL",
    "LAX": "KLAX",
    "ORD": "KORD",
    "DXB": "OMDB",
    "DOH": "OTHH",
    "BAH": "OBBB",
}

def get_icao_code(airport_code: str) -> str:
    """
    Convert IATA or airport code to ICAO.
    """
    airport_code = airport_code.upper().strip()
    if airport_code in AIRPORT_ICAO_MAP:
        return AIRPORT_ICAO_MAP[airport_code]
    # Already ICAO if 4 letters and starts with K, L, O, E, etc.
    if len(airport_code) == 4 and airport_code[0] in ["K", "L", "O", "E", "T", "U"]:
        return airport_code
    return airport_code

if __name__ == "__main__":
    # Quick test
    test_airport = "LTBA"  # Istanbul
    severity = get_airport_weather_severity(test_airport)
    print(f"Weather severity for {test_airport}: {severity}")
