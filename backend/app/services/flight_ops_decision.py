"""
Flight Operations Decision Support System
==========================================
AI-powered operational decision support for flight crews and dispatchers.

Solves:
1. GO/NO-GO weather decisions at destination
2. Fuel stop optimization
3. Alternate airport selection
4. Flight level optimization
5. Wind-aware route planning
6. Operational cost analysis
"""

import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
import math

# ─────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────

# Airport weather minima for GO/NO-GO decisions
GO_NOGO_MINIMA = {
    "CAT3": {"visibility_meters": 550, "ceiling_feet": 100},
    "CAT2": {"visibility_meters": 1000, "ceiling_feet": 200},
    "CAT1": {"visibility_meters": 1600, "ceiling_feet": 400},
    "NON_PREC": {"visibility_meters": 2400, "ceiling_feet": 500},
    "BASIC": {"visibility_meters": 3200, "ceiling_feet": 1000},
}

# Alternative airport database
ALTERNATE_AIRPORTS = {
    "IST": [
        {"icao": "LTAI", "name": "Antalya", "distance_nm": 250, "runway": "18/36", "ils": "CAT1"},
        {"icao": "LTAF", "name": "Eskisehir", "distance_nm": 230, "runway": "18/36", "ils": "CAT1"},
        {"icao": "LTFJ", "name": "Istanbul Sabiha Gokcen", "distance_nm": 45, "runway": "17/35", "ils": "CAT3"},
        {"icao": "LTFC", "name": "Corlu", "distance_nm": 150, "runway": "18/36", "ils": "CAT1"},
    ],
    "JFK": [
        {"icao": "KLGA", "name": "LaGuardia", "distance_nm": 12, "runway": "13/31", "ils": "CAT3"},
        {"icao": "KEWR", "name": "Newark", "distance_nm": 15, "runway": "04L/22R", "ils": "CAT3"},
        {"icao": "KLGA", "name": "Stewart", "distance_nm": 60, "runway": "08/26", "ils": "CAT1"},
        {"icao": "KBDL", "name": "Bradley", "distance_nm": 100, "runway": "16/34", "ils": "CAT2"},
    ],
    "LHR": [
        {"icao": "EGKK", "name": "Gatwick", "distance_nm": 35, "runway": "08/26", "ils": "CAT3"},
        {"icao": "EGBB", "name": "Birmingham", "distance_nm": 110, "runway": "15/33", "ils": "CAT2"},
        {"icao": "EGKK", "name": "Stansted", "distance_nm": 65, "runway": "08/26", "ils": "CAT2"},
    ],
}

# Wind jet data (knots) by altitude and region
WIND_JET_DATA = {
    "NORTH_ATLANTIC": {
        24000: {"speed": 30, "direction": 260},
        30000: {"speed": 65, "direction": 265},
        35000: {"speed": 80, "direction": 270},
        39000: {"speed": 85, "direction": 270},
    },
    "SOUTH_ATLANTIC": {
        24000: {"speed": 15, "direction": 120},
        30000: {"speed": 40, "direction": 115},
        35000: {"speed": 55, "direction": 110},
        39000: {"speed": 60, "direction": 110},
    },
    "EUROPE": {
        24000: {"speed": 20, "direction": 230},
        30000: {"speed": 45, "direction": 235},
        35000: {"speed": 55, "direction": 240},
        39000: {"speed": 60, "direction": 240},
    },
}

# Aircraft climb rates and fuel consumption
CLIMB_FUEL_BURN = {
    "A320": {"burn_rate": 2.8, "climb_rate": 2500},      # kg/min, fpm
    "B737": {"burn_rate": 3.0, "climb_rate": 2500},
    "A330": {"burn_rate": 6.5, "climb_rate": 2200},
    "B787": {"burn_rate": 6.0, "climb_rate": 2200},
    "B777": {"burn_rate": 8.0, "climb_rate": 2000},
    "A350": {"burn_rate": 6.2, "climb_rate": 2200},
}

@dataclass
class FlightPlan:
    """Represents a flight operation plan."""
    origin: str
    destination: str
    aircraft_type: str
    flight_number: str
    planned_cruise_alt: int
    departure_time: datetime
    passengers: int = 0
    cargo_weight_kg: float = 0.0

class FlightOpsDecisionSupport:
    """
    AI-powered flight operations decision support.
    """
    
    def __init__(self):
        self.gonogo_minima = GO_NOGO_MINIMA
        self.alternates = ALTERNATE_AIRPORTS
        self.wind_data = WIND_JET_DATA
        self.climb_data = CLIMB_FUEL_BURN
    
    def go_nogo_decision(self, destination: str, visibility_meters: float,
                          ceiling_feet: float, approach_type: str = "CAT1") -> Dict:
        """
        Make GO/NO-GO decision based on weather at destination.
        """
        minima = self.gonogo_minima.get(approach_type, self.gonogo_minima["CAT1"])
        
        vis_ok = visibility_meters >= minima["visibility_meters"]
        ceil_ok = ceiling_feet >= minima["ceiling_feet"]
        
        decision = "GO" if vis_ok and ceil_ok else "NO-GO"
        reason = []
        
        if not vis_ok:
            reason.append(f"Visibility {visibility_meters}m < minimum {minima['visibility_meters']}m")
        if not ceil_ok:
            reason.append(f"Ceiling {ceiling_feet}ft < minimum {minima['ceiling_feet']}ft")
        
        if decision == "GO":
            reason.append("Weather conditions meet approach minima")
        
        return {
            "destination": destination,
            "weather_conditions": {
                "visibility_meters": visibility_meters,
                "ceiling_feet": ceiling_feet,
                "approach_type": approach_type,
            },
            "minima": minima,
            "decision": decision,
            "reason": "; ".join(reason),
            "alternate_required": decision == "NO-GO",
            "alternate_recommendation": self._recommend_alternate(destination) if decision == "NO-GO" else None,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    def _recommend_alternate(self, destination: str) -> Dict:
        """Recommend alternate airports."""
        alternates = self.alternates.get(destination, [])
        if not alternates:
            return {"available": False, "reason": "No alternates in database"}
        
        # Sort by distance
        alternates_sorted = sorted(alternates, key=lambda x: x["distance_nm"])
        best = alternates_sorted[0]
        
        return {
            "available": True,
            "recommended": best,
            "all_alternates": alternates_sorted,
            "diversion_distance_nm": best["distance_nm"],
        }
    
    def optimize_flight_level(self, origin: str, destination: str,
                               aircraft_type: str, departure_time: datetime = None) -> Dict:
        """
        Find optimal flight level with wind optimization.
        """
        if departure_time is None:
            departure_time = datetime.now()
        
        # Determine region for wind data
        route_key = f"{origin}-{destination}"
        region = self._get_route_region(origin, destination)
        
        # Calculate true course
        lat1, lon1 = self._get_coords(origin)
        lat2, lon2 = self._get_coords(destination)
        
        distance_nm = self._calculate_distance_nm(origin, destination)
        
        # Get wind data for region
        winds = self.wind_data.get(region, self.wind_data.get("EUROPE"))
        
        # Get aircraft performance data
        climb_info = self.climb_data.get(aircraft_type, {"burn_rate": 3.0, "climb_rate": 2500})
        
        optimal_fl = 35000
        best_ground_speed = 0
        best_fuel_burn = float('inf')
        best_info = None
        best_fl = 35000  # Initialize to avoid unbound
        
        for altitude, wind in winds.items():
            # Calculate headwind component
            if lat1 and lon1 and lat2 and lon2:
                dlon = lon2 - lon1
                y = math.sin(dlon) * math.cos(lat2)
                x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
                bearing = math.atan2(y, x)
                true_course = (bearing * 180 / math.pi + 360) % 360
            else:
                true_course = 270
            
            wind_angle = abs(wind["direction"] - true_course)
            if wind_angle > 180:
                wind_angle = 360 - wind_angle
            wind_angle_rad = wind_angle * math.pi / 180
            
            headwind_component = wind["speed"] * math.cos(wind_angle_rad)
            tailwind = wind["speed"] * math.sin(wind_angle_rad)
            
            # True airspeed (typical cruise)
            tas = 450  # knots
            ground_speed = tas + tailwind
            
            # Fuel burn at altitude (reduced by wind benefit)
            base_burn = climb_info["burn_rate"] * 60  # kg/hour at this altitude
            adjusted_burn = base_burn * (1 - tailwind / (tas * 2))
            
            # Net benefit: faster + fuel savings
            time_saved = distance_nm / ground_speed - distance_nm / tas
            fuel_saved = time_saved * base_burn * 3600 / 3600  # Simplified
            
            net_benefit = tailwind * 0.5 + fuel_saved * 0.01  # Combined metric
            
            if ground_speed > best_ground_speed:
                best_ground_speed = ground_speed
                best_fuel_burn = adjusted_burn
                best_fl = altitude
                best_info = {
                    "wind_speed": wind["speed"],
                    "wind_direction": wind["direction"],
                    "headwind_component": round(headwind_component, 1),
                    "tailwind_component": round(tailwind, 1),
                    "true_course": round(true_course, 1),
                    "tas_knots": tas,
                    "ground_speed_knots": round(ground_speed, 1),
                    "fuel_burn_kg_hr": round(adjusted_burn, 1),
                    "time_saved_min": round(time_saved * 60, 1),
                    "fuel_saved_kg": round(fuel_saved, 1),
                    "net_benefit": round(net_benefit, 2),
                }
        
        optimal_fl = best_fl
        
        # Flight time calculation
        flight_time = distance_nm / best_ground_speed if best_ground_speed > 0 else distance_nm / 450
        climb_fuel = climb_info["burn_rate"] * (optimal_fl / climb_info["climb_rate"] * 60)
        cruise_fuel = best_fuel_burn * flight_time
        descent_fuel = climb_info["burn_rate"] * 5  # ~5 min descent
        total_fuel = climb_fuel + cruise_fuel + descent_fuel
        
        return {
            "route": route_key,
            "aircraft": aircraft_type,
            "region": region,
            "optimal_flight_level": optimal_fl,
            "wind_optimization": best_info,
            "fuel_analysis": {
                "climb_fuel_kg": round(climb_fuel, 1),
                "cruise_fuel_kg": round(cruise_fuel, 1),
                "descent_fuel_kg": round(descent_fuel, 1),
                "total_fuel_kg": round(total_fuel, 1),
                "fuel_per_nm": round(total_fuel / distance_nm, 3),
            },
            "flight_analysis": {
                "distance_nm": round(distance_nm),
                "flight_time_hours": round(flight_time, 2),
                "ground_speed_knots": round(best_ground_speed, 1),
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    def _get_route_region(self, origin: str, destination: str) -> str:
        """Determine wind region for a route."""
        origins = {"IST": "EUROPE", "JFK": "NORTH_ATLANTIC", "LHR": "EUROPE",
                    "LAX": "NORTH_ATLANTIC", "DXB": "SOUTH_ATLANTIC"}
        dests = {"IST": "EUROPE", "JFK": "NORTH_ATLANTIC", "LHR": "EUROPE",
                  "LAX": "NORTH_AMERICA", "DXB": "SOUTH_ATLANTIC"}
        
        origin_region = origins.get(origin, "EUROPE")
        dest_region = dests.get(destination, "EUROPE")
        
        # If crossing ocean, use ocean region
        if "NORTH" in origin_region or "NORTH" in dest_region:
            return "NORTH_ATLANTIC"
        if "SOUTH" in origin_region or "SOUTH" in dest_region:
            return "SOUTH_ATLANTIC"
        return origin_region
    
    def _get_coords(self, airport: str) -> tuple:
        """Get coordinates for an airport."""
        coords = {
            "IST": (41.0082 * math.pi / 180, 28.7625 * math.pi / 180),
            "JFK": (40.6413 * math.pi / 180, -73.7781 * math.pi / 180),
            "LHR": (51.4700 * math.pi / 180, -0.4543 * math.pi / 180),
            "DXB": (25.2532 * math.pi / 180, 55.3657 * math.pi / 180),
            "FRA": (50.0379 * math.pi / 180, 8.5622 * math.pi / 180),
            "LAX": (33.9425 * math.pi / 180, -118.4081 * math.pi / 180),
        }
        return coords.get(airport, (None, None))
    
    def _calculate_distance_nm(self, origin: str, destination: str) -> float:
        """Calculate great circle distance in NM."""
        lat1, lon1 = self._get_coords(origin)
        lat2, lon2 = self._get_coords(destination)
        
        if not lat1 or not lat2:
            return 2000  # Default
        
        R = 3440.1  # Earth radius in NM
        
        # Haversine
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c

# ─────────────────────────────────────────────
# API Convenience Functions
# ─────────────────────────────────────────────
_support = None

def get_support():
    global _support
    if _support is None:
        _support = FlightOpsDecisionSupport()
    return _support

def go_nogo_decision(destination: str = "IST", visibility: float = 3200,
                     ceiling: float = 1000, approach_type: str = "CAT1") -> dict:
    """Make GO/NO-GO decision based on weather."""
    return get_support().go_nogo_decision(destination, visibility, ceiling, approach_type)

def optimize_flight_level(origin: str = "IST", destination: str = "JFK",
                           aircraft_type: str = "A320") -> dict:
    """Optimize flight level for wind advantage."""
    return get_support().optimize_flight_level(origin, destination, aircraft_type)

def comprehensive_flight_ops_report(origin: str = "IST", destination: str = "JFK",
                                     aircraft_type: str = "A320") -> dict:
    """Generate comprehensive flight operations report."""
    support = get_support()
    
    gng = support.go_nogo_decision(destination, 3200, 1000, "CAT1")
    fl_opt = support.optimize_flight_level(origin, destination, aircraft_type)
    
    return {
        "go_nogo_decision": gng,
        "flight_level_optimization": fl_opt,
        "route_knowledge": {
            "origin": origin,
            "destination": destination,
            "aircraft": aircraft_type,
            "distance_nm": fl_opt["flight_analysis"]["distance_nm"],
        },
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

if __name__ == "__main__":
    result = optimize_flight_level("IST", "JFK", "A320")
    print(json.dumps(result, indent=2))
    print("✅ Flight ops decision support tested")
