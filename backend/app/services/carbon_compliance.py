"""
Aviation Carbon Compliance & Cost Optimizer
============================================
AI system for carbon footprint calculation, compliance reporting, and
cost optimization for airline operations.

Solves:
1. EU ETS (Emissions Trading Scheme) compliance reporting
2. CORSIA carbon offset calculations
3. Fuel burn optimization recommendations
4. Route carbon footprint comparison
5. Compliance cost estimation

Based on ICAO CORSIA framework and EU ETS requirements.
"""

import json
import math
from datetime import datetime
from typing import Dict, List, Optional

# ─────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────

# ICAO CORSIA carbon calculation coefficients
# Based on ICAO Carbon Emissions Calculator methodology
AIRCRAFT_FUEL_FACTORS = {
    "A320": {"fuel_consumption": 2.5, "co2_per_kg_fuel": 3.15},  # L/100km, kg CO2/kg fuel
    "A321": {"fuel_consumption": 2.7, "co2_per_kg_fuel": 3.15},
    "B737": {"fuel_consumption": 2.6, "co2_per_kg_fuel": 3.15},
    "B738": {"fuel_consumption": 2.8, "co2_per_kg_fuel": 3.15},
    "A330": {"fuel_consumption": 4.0, "co2_per_kg_fuel": 3.15},
    "B777": {"fuel_consumption": 5.2, "co2_per_kg_fuel": 3.15},
    "B787": {"fuel_consumption": 3.8, "co2_per_kg_fuel": 3.15},
    "A350": {"fuel_consumption": 3.5, "co2_per_kg_fuel": 3.15},
    "A380": {"fuel_consumption": 6.0, "co2_per_kg_fuel": 3.15},
    "E190": {"fuel_consumption": 2.2, "co2_per_kg_fuel": 3.15},
    "ATR72": {"fuel_consumption": 1.8, "co2_per_kg_fuel": 3.15},
}

# Default factors for unknown aircraft
DEFAULT_FUEL_FACTOR = 2.8  # L/100km
DEFAULT_CO2_PER_KG = 3.15   # kg CO2/kg fuel

# Jet fuel density (kg/L)
FUEL_DENSITY = 0.804  # kg/L

# EU ETS carbon price (EUR/ton CO2) - varies by year
EU_ETS_CARBON_PRICE = {
    2024: 85,  # EUR/ton
    2025: 95,
    2026: 105,
    2027: 115,
}

# CORSIA benchmark CO2 emissions (t per passenger) for different routes
# Based on ICAO CORSIA Phase I benchmarks
CORSIA_BENCHMARKS = {
    "IST_JFK": 0.65,     # Istanbul to JFK (long-haul international)
    "IST_LHR": 0.18,     # Istanbul to London (short-haul international)
    "IST_DXB": 0.28,     # Istanbul to Dubai
    "IST_BAH": 0.19,     # Istanbul to Bahrain
    "JFK_LHR": 0.62,     # JFK to London
}

# Route distances (NM)
ROUTE_DISTANCES = {
    ("IST", "JFK"): 4400,
    ("IST", "LHR"): 1700,
    ("IST", "DXB"): 1800,
    ("IST", "BAH"): 1300,
    ("IST", "SAW"): 50,
    ("JFK", "LHR"): 3440,
    ("LHR", "DXB"): 3400,
}

# Passenger load factor assumptions
LOAD_FACTORS = {
    "high_season": 0.85,
    "normal": 0.78,
    "low_season": 0.65,
}

class CarbonCalculator:
    """
    Calculate carbon emissions and compliance costs for aviation operations.
    Uses ICAO CORSIA and EU ETS methodologies.
    """
    
    def __init__(self):
        self.fuel_factors = AIRCRAFT_FUEL_FACTORS
        self.co2_per_kg = DEFAULT_CO2_PER_KG
        self.fuel_density = FUEL_DENSITY
    
    def calculate_co2_emissions(self, flight_number: str,
                                 dep_airport: str,
                                 arr_airport: str,
                                 aircraft_type: str = "A320",
                                 passengers: int = 150,
                                 load_factor: float = None,
                                 date_str: str = None) -> Dict:
        """
        Calculate CO2 emissions for a flight leg.
        
        Args:
            flight_number: Flight identifier
            dep_airport: Departure airport (IATA)
            arr_airport: Arrival airport (IATA)
            aircraft_type: Aircraft model (A320, B737, etc.)
            passengers: Passenger count
            load_factor: Aircraft occupancy (auto-calculated if None)
            date_str: Date for seasonal load factor
        """
        # Get route distance
        dep_upper = dep_airport.upper()
        arr_upper = arr_airport.upper()
        
        route_key = (dep_upper, arr_upper)
        distance_nm = ROUTE_DISTANCES.get(route_key, 1000)  # Default 1000 NM
        
        # Get aircraft fuel factor
        aircraft_key = aircraft_type.upper()
        if aircraft_key in self.fuel_factors:
            fuel_factor = self.fuel_factors[aircraft_key]["fuel_consumption"]
        else:
            fuel_factor = DEFAULT_FUEL_FACTOR
        
        # Estimate fuel consumption
        distance_km = distance_nm * 1.852  # NM to km
        base_fuel_liters = (fuel_factor * distance_km) / 100
        
        # Apply aircraft capacity and load factor
        if load_factor is None:
            # Determine seasonal load factor
            if date_str:
                try:
                    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                    month = date_obj.month
                    # Summer (Jun-Aug) = high season, Winter (Dec-Feb) = low season
                    if 6 <= month <= 8:
                        load_factor = LOAD_FACTORS["high_season"]
                    elif month in [12, 1, 2]:
                        load_factor = LOAD_FACTORS["low_season"]
                    else:
                        load_factor = LOAD_FACTORS["normal"]
                except:
                    load_factor = LOAD_FACTORS["normal"]
            else:
                load_factor = LOAD_FACTORS["normal"]
        
        # Adjust fuel based on actual passenger count vs capacity
        # Typical capacities
        capacities = {"A320": 180, "A321": 210, "B737": 160, "B738": 180,
                      "A330": 300, "B777": 360, "B787": 300, "A350": 320,
                      "A380": 525, "E190": 100, "ATR72": 70}
        
        capacity = capacities.get(aircraft_key, 150)
        actual_passengers = min(passengers, capacity)
        
        # Scale fuel by actual load vs capacity
        fuel_scale = 0.7 + (0.3 * load_factor)  # 70% base, 30% variable
        fuel_liters = base_fuel_liters * fuel_scale
        fuel_kg = fuel_liters * self.fuel_density
        
        # Calculate CO2
        co2_kg = fuel_kg * self.co2_per_kg
        co2_tonnes = co2_kg / 1000
        
        # Per-passenger emissions
        co2_per_passenger = co2_kg / actual_passengers if actual_passengers > 0 else 0
        
        # RHI (Radiative Forcing) - ICAO adds 2x multiplier for non-CO2 effects
        rhi_adjusted = co2_tonnes * 2.0
        
        return {
            "flight_number": flight_number.upper(),
            "route": f"{dep_upper} → {arr_upper}",
            "distance_nm": distance_nm,
            "aircraft_type": aircraft_type,
            "passengers": actual_passengers,
            "capacity": capacity,
            "load_factor": round(load_factor * 100, 1),
            "fuel_consumption_liters": round(fuel_liters, 1),
            "fuel_consumption_kg": round(fuel_kg, 1),
            "co2_emissions_kg": round(co2_kg, 1),
            "co2_emissions_tonnes": round(co2_tonnes, 3),
            "co2_per_passenger_kg": round(co2_per_passenger, 1),
            "rhi_adjusted_emissions_tonnes": round(rhi_adjusted, 3),
        }
    
    def calculate_corsia_costs(self, flight_number: str,
                                dep_airport: str,
                                arr_airport: str,
                                date_str: str = None,
                                aircraft_type: str = "A320",
                                passengers: int = 150) -> Dict:
        """
        Calculate CORSIA compliance costs and requirements.
        
        CORSIA is ICAO's global scheme for carbon-neutral growth in international aviation.
        """
        if not date_str:
            date_str = datetime.now().strftime("%Y-%m-%d")
        
        # Calculate base emissions
        emissions = self.calculate_co2_emissions(
            flight_number=flight_number,
            dep_airport=dep_airport,
            arr_airport=arr_airport,
            aircraft_type=aircraft_type,
            passengers=passengers,
            date_str=date_str
        )
        
        # Get CORSIA benchmark
        route_key = f"{dep_airport.upper()}_{arr_airport.upper()}"
        benchmark = CORSIA_BENCHMARKS.get(route_key, 0.40)  # Default 0.40 t/passenger
        
        # CORSIA phase-based compliance
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        year = date_obj.year
        
        if year <= 2023:
            corsia_phase = "Phase I (2019-2023) - 2019 baseline"
            compliance_required = True
        elif year <= 2026:
            corsia_phase = "Phase II (2024-2026) - Baseline grow"
            compliance_required = True
        else:
            corsia_phase = "Phase III (2027+) - Global aspirational"
            compliance_required = True
        
        # Calculate CORSIA obligation
        # Formula: (Actual emissions - benchmark) × passengers × eligible aircraft
        # For simplicity, assume all aircraft are eligible
        benchmark_emissions = benchmark * passengers
        actual_emissions = emissions["co2_emissions_tonnes"]
        
        if actual_emissions > benchmark_emissions:
            excess_emissions = actual_emissions - benchmark_emissions
            # Offsetting required
            offset_price = 5.0  # USD/ton CO2 (approximate market price)
            offset_cost = excess_emissions * offset_price * 1.5  # Include admin costs
            
            corsia_action = "offset_required"
        else:
            excess_emissions = 0
            offset_cost = 0
            corsia_action = "compliant_no_offset_needed"
        
        # EU ETS applicability
        # EU ETS applies to flights to/from/within EEA
        # IST is in EEA for aviation purposes
        eea_countries = ["IST", "LHR", "FRA", "CDG", "MUC", "FCO", "MAD", "BCN", "FCO", "ARN", "OSL", "HEL"]
        in_eea = (dep_airport.upper() in eea_countries or arr_airport.upper() in eea_countries)
        
        if in_eea:
            eu_ets_applicable = True
            carbon_price = EU_ETS_CARBON_PRICE.get(year, EU_ETS_CARBON_PRICE[2026])
            eu_allowance_cost = actual_emissions * carbon_price * 1.1  # Include compliance cost
            eu_ets_status = f"Apply for EU ETS at €{carbon_price}/ton CO2"
        else:
            eu_ets_applicable = False
            eu_allowance_cost = 0
            eu_ets_status = "Not applicable (non-EEA route)"
        
        return {
            "flight_number": flight_number.upper(),
            "corsia_phase": corsia_phase,
            "route": f"{dep_airport.upper()} → {arr_airport.upper()}",
            "emissions_tonnes": emissions["co2_emissions_tonnes"],
            "benchmark_tonnes_per_passenger": benchmark,
            "benchmark_total_tonnes": round(benchmark_emissions, 3),
            "excess_emissions_tonnes": round(excess_emissions, 3),
            "compliance_status": "COMPLIANT" if excess_emissions == 0 else "OFFSET REQUIRED",
            "offset_cost_usd": round(offset_cost, 2),
            "corsia_action": corsia_action,
            "eu_ets_applicable": eu_ets_applicable,
            "eu_ets_status": eu_ets_status,
            "eu_allowance_cost_usd": round(eu_allowance_cost, 2),
            "total_compliance_cost_usd": round(offset_cost + eu_allowance_cost, 2),
            "recommendations": self._generate_carbon_recommendations(emissions, excess_emissions, in_eea),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    def _generate_carbon_recommendations(self, emissions: Dict, 
                                          excess: float, 
                                          in_eea: bool) -> List[str]:
        """Generate carbon optimization recommendations."""
        recs = []
        
        # Fuel efficiency recommendations
        aircraft = emissions.get("aircraft_type", "")
        if aircraft in ["A330", "B777", "B787", "A350", "A380"]:
            recs.append(f"Consider newer-generation {aircraft} for better fuel efficiency")
        
        # Load factor optimization
        load_factor = emissions.get("load_factor", 0) / 100
        if load_factor < 0.75:
            recs.append(f"Increase load factor from {emissions.get('load_factor', 0)}% to 80%+ for better unit emissions")
        
        # Offset recommendations
        if excess > 0:
            recs.append(f"Purchase CORSIA-compliant carbon offsets for {excess:.2f} tonnes CO2")
            recs.append("Consider SAF (Sustainable Aviation Fuel) for offset compliance")
        
        # EU ETS specific
        if in_eea:
            recs.append("Register for EU ETS Monitoring & Reporting (MRG) system")
            recs.append("Submit annual tonne-km report to relevant authority")
        
        # Route optimization
        if emissions.get("co2_per_passenger_kg", 0) > 100:
            recs.append("Investigate route optimization for fuel savings")
        
        if not recs:
            recs.append("Operations are currently efficient - continue monitoring")
        
        return recs

# ─────────────────────────────────────────────
# API Convenience Functions
# ─────────────────────────────────────────────
_calculator = None

def get_calculator():
    global _calculator
    if _calculator is None:
        _calculator = CarbonCalculator()
    return _calculator

def calculate_carbon_footprint(flight_number: str,
                                dep_airport: str,
                                arr_airport: str,
                                aircraft_type: str = "A320",
                                passengers: int = 150,
                                date_str: str = None) -> Dict:
    """Calculate carbon footprint for a flight."""
    calc = get_calculator()
    return calc.calculate_co2_emissions(
        flight_number=flight_number,
        dep_airport=dep_airport,
        arr_airport=arr_airport,
        aircraft_type=aircraft_type,
        passengers=passengers,
        date_str=date_str
    )

def calculate_corsia_compliance(flight_number: str,
                                 dep_airport: str,
                                 arr_airport: str,
                                 date_str: str = None,
                                 aircraft_type: str = "A320",
                                 passengers: int = 150) -> Dict:
    """Calculate CORSIA compliance costs and requirements."""
    calc = get_calculator()
    return calc.calculate_corsia_costs(
        flight_number=flight_number,
        dep_airport=dep_airport,
        arr_airport=arr_airport,
        date_str=date_str,
        aircraft_type=aircraft_type,
        passengers=passengers
    )

if __name__ == "__main__":
    # Test with sample flight
    result = calculate_corsia_compliance(
        flight_number="TK1988",
        dep_airport="IST",
        arr_airport="JFK",
        date_str="2026-10-20",
        aircraft_type="A350",
        passengers=300
    )
    print(json.dumps(result, indent=2))