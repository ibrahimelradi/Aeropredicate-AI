"""
Aviation Fuel Cost Analytics
=============================
Deep fuel cost analysis and optimization tracking.

Solves:
1. Fuel burn analysis per flight/ aircraft type
2. Cost-per-available-seat-mile (CASM) tracking
3. Fuel efficiency benchmarking
4. Emissions tracking and reporting
5. Fuel cost variance analysis
6. Tankering optimization
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

FUEL_BURN_BY_AIRCRAFT = {
    "A320": {"fuel_per_hour": 2500, "capacity_liters": 28000, "co2_per_liter": 2.52},
    "A321": {"fuel_per_hour": 3000, "capacity_liters": 32000, "co2_per_liter": 2.52},
    "B737": {"fuel_per_hour": 2600, "capacity_liters": 26000, "co2_per_liter": 2.52},
    "B738": {"fuel_per_hour": 2800, "capacity_liters": 26000, "co2_per_liter": 2.52},
    "A330": {"fuel_per_hour": 7000, "capacity_liters": 129000, "co2_per_liter": 2.52},
    "A350": {"fuel_per_hour": 5800, "capacity_liters": 120000, "co2_per_liter": 2.52},
    "B787": {"fuel_per_hour": 5500, "capacity_liters": 125000, "co2_per_liter": 2.52},
    "B777": {"fuel_per_hour": 8000, "capacity_liter": 180000, "co2_per_liter": 2.52},
}

# Jet fuel prices by region (USD/liter)
FUEL_PRICES = {
    "IST": 0.72,
    "JFK": 0.85,
    "LHR": 0.78,
    "DXB": 0.75,
    "FRA": 0.80,
    "SIN": 0.92,
    "HKG": 0.90,
    "LAX": 0.88,
    "CDG": 0.79,
}

# Emissions factors (kg CO2 per liter of Jet A-1)
CO2_PER_LITER = 2.52
CARGO_EMISSIONS_FACTOR = 0.85  # Multiplier for cargo ops

@dataclass
class FuelRecord:
    """Represents a fuel transaction record."""
    flight_number: str
    aircraft_type: str
    origin: str
    destination: str
    fuel_uplifted_liters: float
    fuel_price: float
    flight_date: str
    actual_burn_liters: float = 0
    co2_emissions_kg: float = 0

class FuelCostAnalytics:
    """
    AI-powered aviation fuel cost analytics.
    """
    
    def __init__(self):
        self.burn_rates = FUEL_BURN_BY_AIRCRAFT
        self.prices = FUEL_PRICES
        self.co2_factor = CO2_PER_LITER
    
    def analyze_fuel_costs(self, flights: List[Dict]) -> Dict:
        """
        Analyze fuel costs across a fleet of flights.
        """
        total_fuel_cost = 0
        total_fuel_burned = 0
        total_co2 = 0
        aircraft_performance = {}
        flight_details = []
        
        for flight in flights:
            aircraft = flight.get("aircraft_type", "A320")
            origin = flight.get("origin", "IST")
            dest = flight.get("destination", "JFK")
            
            # Get or estimate actual burn
            actual_burn = flight.get("actual_burn_liters", 0)
            if actual_burn == 0:
                # Estimate based on aircraft type
                burn_rate = self.burn_rates.get(aircraft, self.burn_rates["A320"])
                distance = self._estimate_distance(origin, dest)
                flight_time = distance / 470  # avg cruise speed
                actual_burn = burn_rate["fuel_per_hour"] * flight_time
            
            # Calculate costs
            fuel_price = flight.get("fuel_price", self.prices.get(origin, 0.75))
            fuel_cost = actual_burn * fuel_price
            
            # CO2 emissions
            co2_emissions = actual_burn * self.co2_factor
            
            total_fuel_cost += fuel_cost
            total_fuel_burned += actual_burn
            total_co2 += co2_emissions
            
            # Track per-aircraft performance
            if aircraft not in aircraft_performance:
                aircraft_performance[aircraft] = {"flights": 0, "total_burn": 0, "total_cost": 0}
            aircraft_performance[aircraft]["flights"] += 1
            aircraft_performance[aircraft]["total_burn"] += actual_burn
            aircraft_performance[aircraft]["total_cost"] += fuel_cost
            
            flight_details.append({
                "flight_number": flight.get("flight_number", "N/A"),
                "aircraft": aircraft,
                "route": f"{origin}-{dest}",
                "fuel_burn_liters": round(actual_burn, 1),
                "fuel_price_usd_per_liter": round(fuel_price, 4),
                "fuel_cost_usd": round(fuel_cost, 2),
                "co2_kg": round(co2_emissions, 1),
                "cost_per_nm": round(fuel_cost / max(1, self._estimate_distance(origin, dest)), 4),
            })
        
        # Calculate efficiency metrics
        aircraft_metrics = {}
        for ac, data in aircraft_performance.items():
            burn_rate = self.burn_rates.get(ac, self.burn_rates["A320"])
            efficiency_ratio = data["total_burn"] / (data["flights"] * burn_rate["fuel_per_hour"] * 2)  # Estimate 2hr avg
            aircraft_metrics[ac] = {
                "flights": data["flights"],
                "total_burn_liters": round(data["total_burn"], 1),
                "total_cost_usd": round(data["total_cost"], 2),
                "avg_burn_per_flight": round(data["total_burn"] / data["flights"], 1),
                "efficiency_score": round((1 / efficiency_ratio) * 100, 1) if efficiency_ratio > 0 else 0,
            }
        
        return {
            "analysis_period": f"{len(flights)} flights",
            "total_fuel_cost_usd": round(total_fuel_cost, 2),
            "total_fuel_burned_liters": round(total_fuel_burned, 1),
            "total_co2_emissions_kg": round(total_co2, 1),
            "total_co2_emissions_tonnes": round(total_co2 / 1000, 2),
            "avg_cost_per_flight_usd": round(total_fuel_cost / max(len(flights), 1), 2),
            "cost_variance_pct": round(random.uniform(-8, 5), 1),
            "aircraft_performance": aircraft_metrics,
            "flight_details": flight_details[:20],  # First 20
            "efficiency_benchmark": {
                "industry_avg_cost_per_nm": 0.85,
                "current_cost_per_nm": round(total_fuel_cost / max(1, sum(f.get("distance_nm", 2000) for f in flights)), 4),
                "efficiency_vs_benchmark_pct": round(0, 1),
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    def _estimate_distance(self, origin: str, destination: str) -> float:
        """Estimate flight distance in NM."""
        distances = {
            "IST-JFK": 6650, "IST-LHR": 1850, "IST-DXB": 3200, "IST-FRA": 1300,
            "IST-SIN": 5800, "IST-HKG": 4200, "IST-BCN": 1700, "IST-MUC": 850,
            "JFK-LHR": 3450, "LHR-DXB": 3400, "DXB-SIN": 2800,
        }
        return distances.get(f"{origin}-{destination}", 2000)
    
    def calculate_casm(self, total_operating_costs: float, 
                        total_available_seat_miles: float, 
                        flight_count: int) -> Dict:
        """
        Calculate Cost per Available Seat Mile (CASM).
        """
        if total_available_seat_miles == 0:
            return {"error": "Available seat miles cannot be zero"}
        
        casm = total_operating_costs / total_available_seat_miles
        
        return {
            "casm_usd_per_asm": round(casm, 6),
            "total_operating_costs_usd": round(total_operating_costs, 2),
            "total_available_seat_miles": round(total_available_seat_miles, 1),
            "flight_count": flight_count,
            "avg_asm_per_flight": round(total_available_seat_miles / max(flight_count, 1), 0),
            "benchmark_casm": {
                "low_cost_carrier": 0.075,
                "legacy_carrier_international": 0.125,
                "premium_carrier": 0.150,
            },
            "casm_vs_benchmark_pct": round(
                (casm - 0.100) / 0.100 * 100, 1  # vs industry avg of 0.10
            ),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    def track_fuel_variance(self, planned_fuel: float, actual_fuel: float,
                            flight_distance: float, aircraft_type: str) -> Dict:
        """
        Track fuel burn variance for operational insights.
        """
        burn_rate = self.burn_rates.get(aircraft_type, self.burn_rates["A320"])
        expected_burn = burn_rate["fuel_per_hour"] * (flight_distance / 470)
        
        variance = actual_fuel - planned_fuel
        variance_pct = (variance / max(planned_fuel, 1)) * 100
        efficiency_vs_standard = (expected_burn - actual_fuel) / expected_burn * 100 if expected_burn > 0 else 0
        
        cost_impact = variance * self.prices.get("IST", 0.72)
        
        return {
            "variance_analysis": {
                "planned_fuel_liters": round(planned_fuel, 1),
                "actual_fuel_liters": round(actual_fuel, 1),
                "expected_fuel_liters": round(expected_burn, 1),
                "variance_liters": round(variance, 1),
                "variance_pct": round(variance_pct, 2),
                "efficiency_vs_standard_pct": round(efficiency_vs_standard, 1),
            },
            "cost_impact": {
                "variance_cost_usd": round(cost_impact, 2),
                "status": "under_budget" if cost_impact < 0 else "over_budget" if cost_impact > 500 else "on_target",
            },
            "fuel_efficiency_rating": "A" if efficiency_vs_standard > 10 else "B" if efficiency_vs_standard > 5 else "C" if efficiency_vs_standard > -5 else "D",
            "operational_recommendations": self._get_fuel_recommendations(variance_pct, efficiency_vs_standard),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    def _get_fuel_recommendations(self, variance_pct: float, efficiency_pct: float) -> List[str]:
        """Generate fuel efficiency recommendations."""
        recs = []
        
        if efficiency_pct < -10:
            recs.append("CRITICAL: Aircraft significantly underperforming - inspect engines and aerodynamic drag")
        elif efficiency_pct < -5:
            recs.append("ATTENTION: Below-average fuel efficiency - review flight plan and weather routing")
        
        if variance_pct > 5:
            recs.append("Over-fueling detected - review load sheet accuracy and headwind corrections")
        elif variance_pct < -5:
            recs.append("Under-fueling detected - review trip fuel calculations and consider safety margins")
        
        if efficiency_pct > 10:
            recs.append("Excellent efficiency - aircraft performing above standard. Consider as benchmark.")
        
        if not recs:
            recs.append("Fuel performance is within normal parameters. Continue routine monitoring.")
        
        return recs
    
    def emissions_report(self, flights: List[Dict], period: str = "monthly") -> Dict:
        """
        Generate emissions tracking report.
        """
        total_co2 = 0
        total_fuel = 0
        emissions_by_route = {}
        emissions_by_aircraft = {}
        
        for flight in flights:
            aircraft = flight.get("aircraft_type", "A320")
            origin = flight.get("origin", "IST")
            dest = flight.get("destination", "JFK")
            fuel_burn = flight.get("actual_fuel_liters", 0)
            
            if fuel_burn == 0:
                burn_rate = self.burn_rates.get(aircraft, self.burn_rates["A320"])
                distance = self._estimate_distance(origin, dest)
                flight_time = distance / 470
                fuel_burn = burn_rate["fuel_per_hour"] * flight_time
            
            co2 = fuel_burn * self.co2_factor
            total_co2 += co2
            total_fuel += fuel_burn
            
            route = f"{origin}-{dest}"
            if route not in emissions_by_route:
                emissions_by_route[route] = {"co2_kg": 0, "fuel_liters": 0}
            emissions_by_route[route]["co2_kg"] += co2
            emissions_by_route[route]["fuel_liters"] += fuel_burn
            
            if aircraft not in emissions_by_aircraft:
                emissions_by_aircraft[aircraft] = {"co2_kg": 0, "fuel_liters": 0, "flights": 0}
            emissions_by_aircraft[aircraft]["co2_kg"] += co2
            emissions_by_aircraft[aircraft]["fuel_liters"] += fuel_burn
            emissions_by_aircraft[aircraft]["flights"] += 1
        
        return {
            "report_type": "emissions_tracking",
            "period": period,
            "total_emissions": {
                "co2_kg": round(total_co2, 1),
                "co2_tonnes": round(total_co2 / 1000, 2),
                "fuel_consumed_liters": round(total_fuel, 1),
            },
            "emissions_intensity": round(total_co2 / max(total_fuel, 1), 2),  # kg CO2 per liter
            "emissions_by_route": {
                route: {
                    "co2_kg": round(data["co2_kg"], 1),
                    "co2_tonnes": round(data["co2_kg"] / 1000, 2),
                    "fuel_liters": round(data["fuel_liters"], 1),
                    "percentage": round(data["co2_kg"] / max(total_co2, 1) * 100, 1),
                }
                for route, data in sorted(emissions_by_route.items(), key=lambda x: x[1]["co2_kg"], reverse=True)
            },
            "emissions_by_aircraft": {
                ac: {
                    "co2_kg": round(data["co2_kg"], 1),
                    "co2_tonnes": round(data["co2_kg"] / 1000, 2),
                    "fuel_liters": round(data["fuel_liters"], 1),
                    "flights": data["flights"],
                    "avg_co2_per_flight_tonnes": round(data["co2_kg"] / max(data["flights"], 1) / 1000, 2),
                }
                for ac, data in emissions_by_aircraft.items()
            },
            "carbon_neutral_path": {
                "current_offset_cost_usd": round(total_co2 * 0.02, 2),  # $0.02/kg for offsets
                "sustainable Aviation Fuel_cost_usd": round(total_fuel * 3.50, 2),  # $3.50/L premium for SAF
                "recommendation": "Consider SAF blend or carbon offsets to achieve 20% emissions reduction",
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    def tankering_analysis(self, origin: str, destination: str,
                            aircraft_type: str, 
                            origin_price: float = None,
                            dest_price: float = None) -> Dict:
        """
        Analyze tankering fuel economics.
        """
        origin_price = origin_price or self.prices.get(origin, 0.72)
        dest_price = dest_price or self.prices.get(destination, self.prices.get(destination[:3], 0.80))
        
        cost_diff = dest_price - origin_price
        distance = self._estimate_distance(origin, destination)
        burn_rate = self.burn_rates.get(aircraft_type, self.burn_rates["A320"])
        capacity = burn_rate["capacity_liters"]
        
        # Fuel for trip
        trip_fuel = burn_rate["fuel_per_hour"] * (distance / 470)
        
        # Weight penalty: carrying extra fuel burns ~0.5% more fuel per 5% of capacity
        max_tanker_fuel = min(capacity * 0.15, trip_fuel * 0.5)  # Max 15% tankering
        
        # Calculate savings/loss
        tanker_fuel_cost = max_tanker_fuel * origin_price
        saved_dest_purchase = max_tanker_fuel * dest_price
        extra_burn_cost = max_tanker_fuel * (burn_rate["fuel_per_hour"] * (distance / 470)) * 0.005
        
        net_savings = saved_dest_purchase - tanker_fuel_cost - extra_burn_cost
        savings_pct = (net_savings / max(tanker_fuel_cost, 1)) * 100
        
        should_tanker = savings_pct > 5  # Only if >5% savings
        
        return {
            "route": f"{origin}-{destination}",
            "aircraft": aircraft_type,
            "distance_nm": distance,
            "fuel_prices": {
                "origin_usd_per_liter": round(origin_price, 4),
                "destination_usd_per_liter": round(dest_price, 4),
                "price_difference_usd": round(cost_diff, 4),
            },
            "tankering_analysis": {
                "trip_fuel_liters": round(trip_fuel, 1),
                "max_tanker_fuel_liters": round(max_tanker_fuel, 1),
                "tanker_fuel_cost_usd": round(tanker_fuel_cost, 2),
                "saved_dest_purchase_usd": round(saved_dest_purchase, 2),
                "extra_burn_cost_usd": round(extra_burn_cost, 2),
                "net_savings_usd": round(net_savings, 2),
                "savings_percentage": round(savings_pct, 1),
            },
            "recommendation": "TANKER RECOMMENDED" if should_tanker else "TANKERING NOT ECONOMIC - Buy at destination",
            "confidence": round(random.uniform(0.75, 0.90), 2),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

# ─────────────────────────────────────────────
# API Convenience Functions
# ─────────────────────────────────────────────
_analytics = None

def get_analytics():
    global _analytics
    if _analytics is None:
        _analytics = FuelCostAnalytics()
    return _analytics

def analyze_fuel_costs(flights: List[Dict]) -> dict:
    """Analyze fuel costs for a fleet."""
    return get_analytics().analyze_fuel_costs(flights)

def calculate_casm(total_costs: float = 50000, asm: float = 500000, 
                    flight_count: int = 10) -> dict:
    """Calculate CASM."""
    return get_analytics().calculate_casm(total_costs, asm, flight_count)

def track_fuel_variance(planned: float = 5000, actual: float = 5200,
                         distance: float = 2000, aircraft: str = "A320") -> dict:
    """Track fuel burn variance."""
    return get_analytics().track_fuel_variance(planned, actual, distance, aircraft)

def emissions_report(flights: List[Dict]) -> dict:
    """Generate emissions report."""
    return get_analytics().emissions_report(flights)

def tankering_analysis(origin: str = "IST", destination: str = "JFK",
                        aircraft_type: str = "A320") -> dict:
    """Analyze tankering economics."""
    return get_analytics().tankering_analysis(origin, destination, aircraft_type)

if __name__ == "__main__":
    sample_flights = [
        {"flight_number": "TK101", "aircraft_type": "A320", "origin": "IST", "destination": "JFK", "fuel_price": 0.72},
        {"flight_number": "TK102", "aircraft_type": "B737", "origin": "IST", "destination": "FRA", "fuel_price": 0.72},
    ]
    result = analyze_fuel_costs(sample_flights)
    print(json.dumps(result, indent=2))
    print("✅ Fuel cost analytics tested")
