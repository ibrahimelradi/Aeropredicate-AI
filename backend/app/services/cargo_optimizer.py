"""
Cargo Handling & Optimization System
=====================================
AI system for optimizing cargo handling operations at airports.

Solves:
1. Cargo terminal capacity planning
2. Freighter aircraft scheduling
3. Cargo-ground handling resource allocation
4. Revenue optimization for cargo operations
5. Turnaround time minimization for cargo flights

Target: Airport cargo terminals, freighter operators
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass

# ─────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────

# Cargo aircraft types and their characteristics
CARGO_AIRCRAFT = {
    "B747F": {"capacity_tonne": 100, "volume_cbm": 640, "handling_time_hr": 4.0, "hourly_rate": 12000},
    "B777F": {"capacity_tonne": 102, "volume_cbm": 658, "handling_time_hr": 4.0, "hourly_rate": 13000},
    "B767": {"capacity_tonne": 58, "volume_cbm": 480, "handling_time_hr": 3.0, "hourly_rate": 8000},
    "B757F": {"capacity_tonne": 36, "volume_cbm": 320, "handling_time_hr": 2.5, "hourly_rate": 6500},
    "A330F": {"capacity_tonne": 68, "volume_cbm": 440, "handling_time_hr": 3.5, "hourly_rate": 9500},
    "A300F": {"capacity_tonne": 53, "volume_cbm": 380, "handling_time_hr": 3.0, "hourly_rate": 7500},
    "B737F": {"capacity_tonne": 23, "volume_cbm": 140, "handling_time_hr": 2.0, "hourly_rate": 4500},
    "B747P": {"capacity_tonne": 40, "volume_cbm": 500, "handling_time_hr": 3.5, "hourly_rate": 9000},  # Passenger to freighter
}

# Ground handling equipment for cargo
CARGO_EQUIPMENT = {
    " forklifts": {"hourly_cost": 150, "handling_rate": 4},  # tonnes/hour
    "high_loader": {"hourly_cost": 200, "handling_rate": 6},
    "belt_loader": {"hourly_cost": 180, "handling_rate": 5},
    "container_truck": {"hourly_cost": 120, "handling_rate": 3},
    "reach_stacker": {"hourly_cost": 250, "handling_rate": 8},
}

# Cargo terminal capacity (tonnes per hour)
TERMINAL_CAPACITY = {
    "small": 100,
    "medium": 300,
    "large": 600,
    "mega": 1200,
}

# Cargo type revenue rates (USD/tonne)
CARGO_REVENUE_RATES = {
    "belly": 3.5,      # Belly cargo on passenger flights
    "freighter": 2.5,  # Pure freighter
    "priority": 6.0,   # Express/priority
    "general": 2.0,    # General freight
    "pharma": 8.0,     # Pharmaceuticals
    "livestock": 5.0,  # Live animals
}

@dataclass
class CargoShipment:
    """Represents a cargo shipment."""
    shipment_id: str
    origin: str
    destination: str
    weight_tonnes: float
    volume_cbm: float
    cargo_type: str
    priority: str
    aircraft_type: Optional[str] = None
    handling_requirements: List[str] = None

@dataclass
class CargoFlight:
    """Represents a cargo flight operation."""
    flight_number: str
    aircraft_type: str
    origin: str
    destination: str
    departure: datetime
    arrival: datetime
    cargo_shipment: CargoShipment

class CargoOptimizer:
    """
    Optimizes cargo handling operations and flight scheduling.
    """
    
    def __init__(self):
        self.aircraft_specs = CARGO_AIRCRAFT
        self.terminal_capacity = TERMINAL_CAPACITY
    
    def optimize_cargo_flight(self, shipment: CargoShipment,
                               origin: str, destination: str,
                               departure: str, aircraft_type: str = None) -> Dict:
        """
        Optimize cargo flight planning for a shipment.
        
        Determines optimal aircraft, handling time, and costs.
        """
        # Determine optimal aircraft based on shipment
        if not aircraft_type:
            aircraft_type = self._select_optimal_aircraft(shipment)
        
        aircraft = self.aircraft_specs.get(aircraft_type, {})
        if not aircraft:
            return {"error": f"Unknown aircraft type: {aircraft_type}"}
        
        # Calculate handling time
        base_handling_time = aircraft["handling_time_hr"]
        
        # Adjust for cargo type
        cargo_multipliers = {
            "priority": 1.5,    # More checks
            "pharma": 1.3,      # Temperature control
            "livestock": 2.0,   # Special handling
            "general": 1.0,
            "belly": 0.8,       # Less complex
        }
        handling_time = base_handling_time * cargo_multipliers.get(shipment.cargo_type, 1.0)
        
        # Calculate costs
        handling_cost = handling_time * aircraft["hourly_rate"]
        
        # Equipment costs
        equipment_cost = sum(
            CARGO_EQUIPMENT.get(eq, {}).get("hourly_cost", 150) * handling_time
            for eq in (shipment.handling_requirements or [])
        )
        
        # Revenue estimate
        revenue_rate = CARGO_REVENUE_RATES.get(shipment.cargo_type, 3.0)
        revenue = shipment.weight_tonnes * revenue_rate
        
        # Profit margin
        profit = revenue - handling_cost - equipment_cost
        
        # Utilization check
        capacity_util = min(shipment.weight_tonnes / aircraft["capacity_tonne"], 1.0)
        volume_util = min(shipment.volume_cbm / aircraft["volume_cbm"], 1.0)
        
        return {
            "flight_number": f"/CARGO-{shipment.shipment_id}",
            "aircraft_type": aircraft_type,
            "route": f"{origin} → {destination}",
            "shipment": {
                "id": shipment.shipment_id,
                "weight_tonnes": shipment.weight_tonnes,
                "volume_cbm": shipment.volume_cbm,
                "cargo_type": shipment.cargo_type,
                "priority": shipment.priority
            },
            "handling": {
                "base_time_hours": base_handling_time,
                "adjusted_time_hours": round(handling_time, 2),
                "equipment_needed": shipment.handling_requirements or []
            },
            "costs": {
                "handling_cost_usd": round(handling_cost, 2),
                "equipment_cost_usd": round(equipment_cost, 2),
                "total_cost_usd": round(handling_cost + equipment_cost, 2)
            },
            "revenue": {
                "estimated_revenue_usd": round(revenue, 2),
                "profit_usd": round(profit, 2),
                "margin_percent": round((profit / revenue * 100) if revenue > 0 else 0, 1)
            },
            "utilization": {
                "weight_capacity": f"{capacity_util:.1%}",
                "volume_capacity": f"{volume_util:.1%}",
                "efficient": capacity_util >= 0.7 and volume_util >= 0.7
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    def _select_optimal_aircraft(self, shipment: CargoShipment) -> str:
        """Select the most appropriate aircraft for a shipment."""
        # Find minimum aircraft that can handle the shipment
        candidates = []
        
        for aircraft_type, specs in self.aircraft_specs.items():
            if (specs["capacity_tonne"] >= shipment.weight_tonnes and
                specs["volume_cbm"] >= shipment.volume_cbm):
                # Calculate efficiency (utilization vs cost)
                weight_util = shipment.weight_tonnes / specs["capacity_tonne"]
                volume_util = shipment.volume_cbm / specs["volume_cbm"]
                avg_util = (weight_util + volume_util) / 2
                
                candidates.append({
                    "type": aircraft_type,
                    "utilization": avg_util,
                    "hourly_rate": specs["hourly_rate"],
                    "handling_time": specs["handling_time_hr"]
                })
        
        if not candidates:
            # No single aircraft - need multiple or largest
            return max(self.aircraft_specs.keys(), 
                      key=lambda x: self.aircraft_specs[x]["capacity_tonne"])
        
        # Select most efficient (highest utilization, lowest rate)
        return sorted(candidates, 
                     key=lambda x: x["utilization"] / x["hourly_rate"],
                     reverse=True)[0]["type"]
    
    def forecast_terminal_capacity(self, terminal_type: str = "large",
                                    flights: List[CargoFlight] = None) -> Dict:
        """
        Forecast cargo terminal capacity utilization.
        
        Args:
            terminal_type: small/medium/large/mega
            flights: List of cargo flights to process
        """
        capacity = self.terminal_capacity.get(terminal_type, 300)
        
        # Simulate hourly forecasts
        hourly_forecast = {}
        
        if flights:
            for flight in flights:
                hour = flight.departure.hour
                weight = 0
                for s in [flight.cargo_shipment]:
                    weight += s.weight_tonnes if s else 0
                
                if hour not in hourly_forecast:
                    hourly_forecast[hour] = {"weight_tonnes": 0, "flights": 0}
                
                hourly_forecast[hour]["weight_tonnes"] += weight
                hourly_forecast[hour]["flights"] += 1
        else:
            # Generate sample forecast
            import random
            for hour in range(24):
                base = capacity * 0.3
                if 6 <= hour <= 10:
                    multiplier = 1.8
                elif 16 <= hour <= 20:
                    multiplier = 2.0
                else:
                    multiplier = 0.4
                
                hourly_forecast[hour] = {
                    "weight_tonnes": round(base * multiplier * random.uniform(0.8, 1.2), 1),
                    "flights": int(random.uniform(2, 10) * multiplier),
                }
        
        # Calculate forecast metrics
        for hour, data in hourly_forecast.items():
            utiliz_rate = min(data["weight_tonnes"] / capacity, 2.0)  # Can exceed 100%
            data["utilization_pct"] = round(utiliz_rate * 100, 1)
            data["capacity_status"] = (
                "overloaded" if utiliz_rate > 1.0
                else "high" if utiliz_rate > 0.8
                else "normal" if utiliz_rate > 0.5
                else "low"
            )
            data["expected_wait_min"] = round(utiliz_rate * 30, 0) if utiliz_rate > 0.5 else 0
        
        # Find bottleneck hours
        bottleneck_hours = [
            h for h, d in hourly_forecast.items()
            if d["capacity_status"] in ["overloaded", "high"]
        ]
        
        return {
            "terminal_type": terminal_type,
            "capacity_tonnes_per_hour": capacity,
            "hourly_forecast": hourly_forecast,
            "bottleneck_hours": bottleneck_hours,
            "peak_hour": max(hourly_forecast.items(), key=lambda x: x[1]["weight_tonnes"])[0] if hourly_forecast else None,
            "total_daily_tonnes": round(sum(d["weight_tonnes"] for d in hourly_forecast.values()), 1),
            "avg_utilization": round(sum(d["utilization_pct"] for d in hourly_forecast.values()) / 24, 1),
            "recommendations": self._generate_terminal_recommendations(hourly_forecast, capacity),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    def _generate_terminal_recommendations(self, hourly: Dict, capacity: float) -> List[str]:
        """Generate terminal capacity recommendations."""
        recs = []
        
        for hour, data in hourly.items():
            if data["capacity_status"] == "overloaded":
                recs.append(f"CRITICAL: Hour {hour:02d}:00 overloaded ({data['utilization_pct']:.0f}%) - redirect flights or add resources")
            elif data["capacity_status"] == "high":
                recs.append(f"Warning: Hour {hour:02d}:00 high utilization ({data['utilization_pct']:.0f}%) - monitor closely")
        
        if not recs:
            recs.append("Terminal capacity is adequate - no immediate concerns")
        
        # General recommendations
        if len(recs) > 2:
            recs.append("Consider expanding terminal capacity or shift cargo operations to off-peak hours")
        
        return recs
    
    def generate_revenue_optimization_report(self, routes: List[Dict]) -> Dict:
        """
        Generate revenue optimization report for cargo routes.
        
        Args:
            routes: List of route data with cargo volumes
        """
        route_analysis = []
        total_revenue = 0
        total_volume = 0
        
        for route in routes:
            origin = route.get("origin", "IST")
            dest = route.get("destination", "JFK")
            volume_tpm = route.get("monthly_tonnes", 100)
            cargo_type = route.get("cargo_type", "general")
            
            rate = CARGO_REVENUE_RATES.get(cargo_type, 2.5)
            revenue = volume_tpm * rate * 30  # Monthly estimate
            
            # Find optimal aircraft
            sample_shipment = CargoShipment(
                shipment_id="RPT001",
                origin=origin,
                destination=dest,
                weight_tonnes=20,
                volume_cbm=150,
                cargo_type=cargo_type,
                priority=route.get("priority", "normal"),
                handling_requirements=["forklifts", "container_truck"]
            )
            
            aircraft = self._select_optimal_aircraft(sample_shipment)
            handling_time = self.aircraft_specs[aircraft]["handling_time_hr"]
            
            route_analysis.append({
                "route": f"{origin} → {dest}",
                "cargo_type": cargo_type,
                "monthly_volume_tonnes": volume_tpm,
                "estimated_monthly_revenue": round(revenue, 2),
                "optimal_aircraft": aircraft,
                "handling_time_hours": handling_time,
                "priority": route.get("priority", "normal")
            })
            
            total_revenue += revenue
            total_volume += volume_tpm
        
        # Sort by revenue for top routes
        top_routes = sorted(route_analysis, key=lambda x: x["estimated_monthly_revenue"], reverse=True)[:5]
        
        return {
            "routes_analyzed": len(routes),
            "total_monthly_revenue": round(total_revenue, 2),
            "total_monthly_volume": total_volume,
            "avg_revenue_per_tonne": round(total_revenue / max(total_volume, 1), 2),
            "top_routes": top_routes,
            "recommendations": [
                f"Focus on {top_routes[0]['route']} - highest revenue potential",
                f"Promote {top_routes[0]['cargo_type']} cargo with premium rates",
                f"Optimize handling for {top_routes[0]['optimal_aircraft']} to reduce turnaround time"
            ],
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

# ─────────────────────────────────────────────
# API Convenience Functions
# ─────────────────────────────────────────────
_optimizer = None

def get_optimizer():
    global _optimizer
    if _optimizer is None:
        _optimizer = CargoOptimizer()
    return _optimizer

def optimize_cargo_flight(shipment_id: str = "SHP001",
                          origin: str = "IST",
                          destination: str = "JFK",
                          weight_tonnes: float = 25.0,
                          volume_cbm: float = 150.0,
                          cargo_type: str = "general",
                          priority: str = "normal") -> Dict:
    """Optimize a cargo flight for a shipment."""
    optimizer = get_optimizer()
    
    shipment = CargoShipment(
        shipment_id=shipment_id,
        origin=origin,
        destination=destination,
        weight_tonnes=weight_tonnes,
        volume_cbm=volume_cbm,
        cargo_type=cargo_type,
        priority=priority,
        handling_requirements=["forklifts", "container_truck"]
    )
    
    return optimizer.optimize_cargo_flight(shipment, origin, destination, "", None)

def forecast_cargo_terminal(terminal_type: str = "large") -> Dict:
    """Generate cargo terminal capacity forecast."""
    optimizer = get_optimizer()
    return optimizer.forecast_terminal_capacity(terminal_type)

def generate_cargo_revenue_report(routes: List[Dict] = None) -> Dict:
    """Generate cargo revenue optimization report."""
    optimizer = get_optimizer()
    
    if routes is None:
        routes = [
            {"origin": "IST", "destination": "JFK", "monthly_tonnes": 500, "cargo_type": "general"},
            {"origin": "IST", "destination": "LHR", "monthly_tonnes": 300, "cargo_type": "priority"},
            {"origin": "IST", "destination": "DXB", "monthly_tonnes": 250, "cargo_type": "general"},
            {"origin": "IST", "destination": "BAH", "monthly_tonnes": 150, "cargo_type": "pharma"},
            {"origin": "IST", "destination": "FRA", "monthly_tonnes": 200, "cargo_type": "general"},
        ]
    
    return optimizer.generate_revenue_optimization_report(routes)

if __name__ == "__main__":
    # Test cargo flight optimization
    print("=== Cargo Flight Optimization ===")
    result = optimize_cargo_flight("SHP001", "IST", "JFK", 25.0, 150.0, "general", "normal")
    print(json.dumps(result, indent=2))
    
    print("\n=== Terminal Forecast ===")
    forecast = forecast_cargo_terminal("large")
    print(json.dumps(forecast, indent=2))
    
    print("\n=== Revenue Report ===")
    report = generate_cargo_revenue_report()
    print(json.dumps(report, indent=2))
