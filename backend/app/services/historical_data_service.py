"""
Historical Flight Data Service
==============================
Integrates free aviation data APIs for historical flight patterns.
"""

import requests
import json
from datetime import datetime, timedelta
import os

# Free APIs (no paid tier yet)
AVIATIONSTACK_KEY = os.getenv("AVIATIONSTACK_KEY", "")

def get_historical_flights(dep_airport: str, arr_airport: str, date_range_days: int = 30) -> list[dict]:
    """
    Fetch historical flight data using AviationStack API (free tier: 1,000 req/month).
    Returns list of flight records with actual delays.
    """
    if not AVIATIONSTACK_KEY:
        return _get_synthetic_historical(dep_airport, arr_airport)

    base_url = "http://api.aviationstack.com/v1/flights"
    flights = []
    current_date = datetime.now()
    
    for i in range(date_range_days):
        check_date = current_date - timedelta(days=i)
        try:
            response = requests.get(base_url, params={
                "access_key": AVIATIONSTACK_KEY,
                "dep_iata": dep_airport,
                "arr_iata": arr_airport,
                "flight_date": check_date.strftime("%Y-%m-%d"),
                "limit": 50
            }, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                flights.extend(data.get("data", []))
        except Exception:
            continue
    
    return flights

def calculate_route_performance(flights: list[dict]) -> dict:
    """
    Calculate on-time performance metrics from historical flights.
    Returns dict with OTP, average delay, and delay distribution.
    """
    if not flights:
        return {"otp": 0.75, "avg_delay_min": 15.0, "delay_distribution": {
            "on_time": 75.0, "delayed_15": 15.0, "delayed_30": 7.0, "cancelled": 3.0
        }}

    total = len(flights)
    on_time = 0
    delayed_15 = 0
    delayed_30 = 0
    cancelled = 0
    total_delay_min = 0

    for flight in flights:
        status = flight.get("flight_status", "")
        dep_delay = int(flight.get("departure", {}).get("delay", 0) or 0)

        if status == "cancelled":
            cancelled += 1
        elif dep_delay <= 0:
            on_time += 1
        elif dep_delay <= 14:
            delayed_15 += 1
        elif dep_delay <= 29:
            delayed_30 += 1

        total_delay_min += dep_delay

    return {
        "otp": round((on_time / total) * 100, 1),
        "avg_delay_min": round(total_delay_min / total, 1),
        "delay_distribution": {
            "on_time": round((on_time / total) * 100, 1),
            "delayed_15": round((delayed_15 / total) * 100, 1),
            "delayed_30": round((delayed_30 / total) * 100, 1),
            "cancelled": round((cancelled / total) * 100, 1)
        }
    }

def _get_synthetic_historical(dep_airport: str, arr_airport: str) -> list[dict]:
    """
    Fallback synthetic data if no API key provided.
    Generates realistic historical patterns.
    """
    import random
    random.seed(hash(f"{dep_airport}{arr_airport}") % 2**32)
    
    flights = []
    for i in range(30):
        delay_chance = random.random()
        if delay_chance < 0.75:
            delay = 0
        elif delay_chance < 0.90:
            delay = random.randint(5, 25)
        else:
            delay = random.randint(25, 90)
            
        flights.append({
            "flight_status": "active",
            "departure": {"delay": delay}
        })
    return flights

if __name__ == "__main__":
    # Test with a common route
    flights = get_historical_flights("IST", "JFK")
    stats = calculate_route_performance(flights)
    print(f"Route IST->JFK Historical Stats:")
    print(json.dumps(stats, indent=2))
