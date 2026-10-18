"""
Airline Route Optimizer
=======================
AI-powered route optimization system for airlines.

Solves:
1. Weather-based route adjustment
2. Fuel cost minimization with wind optimization
3. Delay propagation modeling
4. Network-wide delay impact analysis

Uses OpenSky Network data + NOAA weather for real-time optimization.
"""

import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, field

# Import aviation data
try:
    from .aviation_data_service import (
        get_airport_weather_severity,
        get_icao_code,
        get_live_traffic,
    )
except ImportError:
    pass

# ─────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────

# Wind altitude data (feet) and corresponding jet stream impact
WIND_IMPACT_LEVELS = {
    0: -0.05,    # Surface - minimal wind impact
    10000: 0.0,  # Low altitude - neutral
    24000: 0.15, # Cruise - moderate tailwind/wind impact
    30000: 0.25, # Optimal - significant tailwind
    40000: 0.35, # High cruise - maximum wind benefit
}

# Aircraft fuel burn rates (kg/hour)
FUEL_BURN_RATES = {
    "narrow_body": {"rate": 2400, "capacity": 20000, "optimal_altitude": 35000},
    "wide_body": {"rate": 9500, "capacity": 80000, "optimal_altitude": 38000},
    "regional": {"rate": 850, "capacity": 3500},
    "super_jumbo": {"rate": 12000, "capacity": 120000, "optimal_altitude": 35000},
}

# Route cost constants (per minute of delay)
DELAY_COST_PER_MINUTE = {
    "wide_body": 3500,   # $3,500/min for A350/B777
    "narrow_body": 850,   # $850/min for A320/B737
    "regional": 350,      # $350/min for E-Jet/ATR
}

@dataclass
class RouteSegment:
    """Represents a single flight route segment."""
    origin: str
    destination: str
    distance_nm: float  # Nautical miles
    optimal_altitude: int  # Feet
    base_flight_time: float  # Minutes
    fuel_required: float  # kg

@dataclass
class DelayPropagation:
    """Models how delays propagate through a flight network."""
    flight_number: str
    departure_delay: float  # Minutes
    arrival_delay: float     # Minutes
    downstream_flights: List[str] = field(default_factory=list)
    recovery_actions: List[str] = field(default_factory=list)

class RouteOptimizer:
    """
    Optimizes airline routes for fuel efficiency and delay minimization.
    """
    
    def __init__(self):
        self.aircraft_specs = FUEL_BURN_RATES
    
    def calculate_optimal_altitude(self, dep_icao: str, arr_icao: str, 
                                   date_str: str, aircraft_type: str = "narrow_body") -> Dict:
        """
        Calculate optimal cruising altitude based on weather conditions.
        
        Higher wind impact = more fuel savings at higher altitude (if weather permits).
        """
        # Get weather severity
        dep_severity = get_airport_weather_severity(dep_icao)
        arr_severity = get_airport_weather_severity(arr_icao)
        avg_severity = (dep_severity + arr_severity) / 2
        
        specs = self.aircraft_specs.get(aircraft_type, self.aircraft_specs["narrow_body"])
        optimal_alt = specs["optimal_altitude"]
        
        # Adjust based on weather
        if avg_severity > 0.7:
            # Poor weather - fly lower for safety
            optimal_alt = max(24000, optimal_alt - 5000)
            recommendation = "Fly at lower altitude due to severe weather"
        elif avg_severity > 0.4:
            optimal_alt = max(28000, optimal_alt - 3000)
            recommendation = "Moderate weather - slight altitude adjustment recommended"
        else:
            # Good weather - full altitude benefit
            recommendation = "Optimal conditions - cruise at maximum altitude"
        
        # Get live traffic density
        traffic = get_live_traffic()
        if traffic and traffic.get("total_aircraft", 0) > 8000:
            # High traffic - climb higher or descend to avoid congestion
            optimal_alt = min(42000, optimal_alt + 2000)
            recommendation += " | High traffic density - consider altitude change"
        
        return {
            "optimal_altitude_ft": optimal_alt,
            "weather_severity": round(avg_severity, 3),
            "wind_impact": WIND_IMPACT_LEVELS.get(optimal_alt, 0.25),
            "recommendation": recommendation,
            "live_traffic_count": traffic.get("total_aircraft", 0) if traffic else 0
        }
    
    def estimate_fuel_and_cost(self, route: RouteSegment, aircraft_type: str,
                                dep_weather: float = 0.25, 
                                arr_weather: float = 0.25) -> Dict:
        """Estimate fuel requirements and costs with weather adjustments."""
        specs = self.aircraft_specs.get(aircraft_type, self.aircraft_specs["narrow_body"])
        
        # Base fuel calculation
        base_fuel = (route.distance_nm / 100) * specs["rate"] * (route.base_flight_time / 60)
        
        # Weather impact on fuel consumption
        weather_factor = 1.0 + (dep_weather + arr_weather) * 0.1  # 10% increase per severity unit
        
        # Altitude optimization benefit
        wind_benefit = WIND_IMPACT_LEVELS.get(route.optimal_altitude, 0.2)
        
        # Calculate adjusted fuel
        adjusted_fuel = base_fuel * weather_factor * (1 - wind_benefit * 0.15)
        
        # Fuel cost (avg jet fuel ~$0.75/L, density ~0.8 kg/L)
        fuel_cost_per_kg = 0.95  # USD
        
        return {
            "base_fuel_kg": round(base_fuel, 1),
            "weather_adjusted_fuel_kg": round(adjusted_fuel, 1),
            "fuel_cost_usd": round(adjusted_fuel * fuel_cost_per_kg, 2),
            "co2_emissions_kg": round(adjusted_fuel * 3.15, 1),
            "weather_factor": round(weather_factor, 3),
            "wind_benefit_percent": f"{wind_benefit * 15:.1f}%"
        }
    
    def model_delay_propagation(self, flight_number: str, dep_airport: str, 
                                 arr_airport: str, date_str: str, dep_time: str,
                                 aircraft_type: str = "narrow_body") -> Dict:
        """
        Model how delays propagate through the airline network.
        
        When Flight A is delayed, it impacts:
        - Aircraft A's return flight
        - Connecting passengers
        - Downstream aircraft assignments
        """
        # Get delay prediction
        try:
            dep_icao = get_icao_code(dep_airport)
            arr_icao = get_icao_code(arr_airport)
            delay_prediction = self._get_delay_probability(dep_icao, arr_icao)
        except:
            delay_prediction = {"probability": 35.0, "expected_delay": 15}
        
        # Calculate downstream impacts
        delay_minutes = delay_prediction["expected_delay"]
        
        # Aircraft rotation impact (same aircraft returns)
        return_delay = delay_minutes + 5  # Additional crew rest time
        
        # Connecting passenger impact
        connecting_passengers_delayed = int(delay_minutes / 5) * 8  # ~8 passengers per 5 min
        
        # Downstream flight impacts (assuming 2-3 subsequent flights)
        downstream_impact = []
        recovery_actions = []
        
        for i in range(1, 4):
            downstream_delay = max(0, delay_minutes - (i * 3))  # Recovery over subsequent flights
            if downstream_delay > 5:
                downstream_impact.append({
                    "flight_sequence": i,
                    "estimated_delay_min": int(downstream_delay),
                    "impact_type": "aircraft_rotation" if i == 1 else "passenger_connection"
                })
        
        # Recovery recommendations
        recovery_cost_per_minute = DELAY_COST_PER_MINUTE.get(aircraft_type, 850)
        
        if delay_minutes > 30:
            recovery_actions.append("Rebook passengers on later flights")
            recovery_actions.append("Swap aircraft if available")
            recovery_actions.append("Prioritize boarding to minimize further delays")
        elif delay_minutes > 15:
            recovery_actions.append("Monitor connecting passengers")
            recovery_actions.append("Communicate proactively with affected passengers")
        
        total_cost = delay_minutes * recovery_cost_per_minute * (1 + len(downstream_impact) * 0.3)
        
        return {
            "flight_number": flight_number.upper(),
            "departure_airport": dep_airport,
            "arrival_airport": arr_airport,
            "date": date_str,
            "predicted_delay_minutes": delay_minutes,
            "delay_probability": delay_prediction["probability"],
            "downstream_impacts": downstream_impact,
            "connecting_passengers_affected": connecting_passengers_delayed,
            "estimated_cost_impact_usd": round(total_cost, 2),
            "recovery_actions": recovery_actions,
            "aircraft_type": aircraft_type,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    def _get_delay_probability(self, dep_icao: str, arr_icao: str) -> Dict:
        """Get quick delay probability estimate."""
        dep_severity = get_airport_weather_severity(dep_icao)
        arr_severity = get_airport_weather_severity(arr_icao)
        
        base_probability = 20.0  # Base delay probability
        
        # Weather impact
        weather_impact = (dep_severity + arr_severity) * 40  # Up to 80% from weather
        
        # Aircraft type impact (simplified)
        total_prob = min(base_probability + weather_impact, 95.0)
        
        # Expected delay scales with probability
        expected_delay = int(total_prob * 0.8)  # Rough correlation
        
        return {
            "probability": round(total_prob, 1),
            "expected_delay": expected_delay,
            "factors": {
                "weather_severity": round((dep_severity + arr_severity) / 2, 2),
                "base_probability": base_probability,
            }
        }

# Convenience API functions
_optimizer = None

def get_optimizer():
    global _optimizer
    if _optimizer is None:
        _optimizer = RouteOptimizer()
    return _optimizer

def calculate_route_optimization(flight_number: str, dep_airport: str, arr_airport: str,
                                  airline: str, date_str: str, dep_time: str,
                                  aircraft_type: str = "narrow_body") -> Dict:
    """Calculate optimal route with fuel, altitude, and delay analysis."""
    optimizer = get_optimizer()
    
    dep_icao = get_icao_code(dep_airport)
    arr_icao = get_icao_code(arr_airport)
    
    # Get weather-based altitude recommendation
    altitude_info = optimizer.calculate_optimal_altitude(dep_icao, arr_icao, date_str, aircraft_type)
    
    # Estimate distance (simplified - would use great circle in production)
    # IST to JFK is ~4400 NM, typical for narrow-body
    distance_map = {
        ("IST", "JFK"): (4400, 620),     # NM, minutes
        ("IST", "LHR"): (1700, 240),
        ("IST", "DXB"): (1800, 260),
        ("IST", "BAH"): (1300, 170),
    }
    
    key = (dep_airport.upper(), arr_airport.upper())
    if key in distance_map:
        distance_nm, base_time = distance_map[key]
    else:
        distance_nm = 2000  # Default
        base_time = 300
    
    route = RouteSegment(
        origin=dep_airport,
        destination=arr_airport,
        distance_nm=distance_nm,
        optimal_altitude=altitude_info["optimal_altitude_ft"],
        base_flight_time=base_time,
        fuel_required=0.0  # Calculated below
    )
    
    # Get weather severities
    dep_weather = get_airport_weather_severity(dep_icao)
    arr_weather = get_airport_weather_severity(arr_icao)
    
    fuel_analysis = optimizer.estimate_fuel_and_cost(route, aircraft_type, dep_weather, arr_weather)
    
    # Delay propagation analysis
    delay_impact = optimizer.model_delay_propagation(
        flight_number, dep_airport, arr_airport, date_str, dep_time, aircraft_type
    )
    
    return {
        "flight_number": flight_number.upper(),
        "route": {
            "origin": dep_airport,
            "destination": arr_airport,
            "distance_nm": distance_nm,
            "base_flight_time_min": base_time,
        },
        "altitude_optimization": altitude_info,
        "fuel_analysis": fuel_analysis,
        "delay_impact": delay_impact,
        "aircraft_type": aircraft_type,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

if __name__ == "__main__":
    # Test
    result = calculate_route_optimization(
        flight_number="TK1988",
        dep_airport="IST",
        arr_airport="JFK",
        airline="TK",
        date_str="2026-10-20",
        dep_time="14:30",
        aircraft_type="narrow_body"
    )
    print(json.dumps(result, indent=2))
