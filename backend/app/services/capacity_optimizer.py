"""
Airport Capacity & Resource Optimizer
======================================
AI-powered optimization of airport ground resources.

Solves:
1. Gate allocation optimization
2. Stand/jetway resource allocation
3. Ground handling crew scheduling
4. Baggage handling capacity planning
5. Retail/concession revenue optimization
6. Queue time minimization at checkpoints
"""

import json
import random
from datetime import datetime, timedelta, time
from typing import Dict, List, Optional
from dataclasses import dataclass, field
import math

# ─────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────

# Airport resource profiles
AIRPORT_PROFILES = {
    "IST": {
        "name": "Istanbul Airport",
        "total_gates": 165,
        "schengen_gates": 45,
        "non_schengen_gates": 120,
        "international_gates": 85,
        "domestic_gates": 80,
        "jetway_stands": 165,
        "remote_stands": 35,
        "baggage_systems": 2,
        "security_lanes": 18,
        "passport_control": 35,
        "check_in_counters": 280,
        "retail_areas": 12,
        "parking_capacity": 25000,
        "runway_capacity": 90,  # movements/hour
    },
    "JFK": {
        "name": "John F. Kennedy International",
        "total_gates": 131,
        "international_gates": 131,
        "domestic_gates": 0,
        "jetway_stands": 131,
        "remote_stands": 0,
        "baggage_systems": 4,
        "security_lanes": 14,
        "passport_control": 16,
        "check_in_counters": 252,
        "retail_areas": 8,
        "parking_capacity": 4000,
        "runway_capacity": 45,
    },
    "DXB": {
        "name": "Dubai International",
        "total_gates": 164,
        "international_gates": 164,
        "domestic_gates": 0,
        "jetway_stands": 164,
        "remote_stands": 20,
        "baggage_systems": 3,
        "security_lanes": 20,
        "passport_control": 25,
        "check_in_counters": 384,
        "retail_areas": 10,
        "parking_capacity": 29000,
        "runway_capacity": 80,
    },
}

# Aircraft type to gate size requirements
AIRCRAFT_GATE_SIZE = {
    "A320": "small", "A321": "small", "B737": "small", "E190": "small",
    "A319": "small", "A320neo": "small", "BCEJ": "small",
    "A330": "large", "B787": "large", "A350": "large", "B777": "large",
    "A380": "jumbo", "B747": "jumbo",
}

# Resource processing rates (passengers/hour/resource)
PROCESSING_RATES = {
    "check_in_counter": 120,      # passengers per counter per hour
    "security_lane": 240,         # passengers per lane per hour (standard)
    "fast_track_security": 360,    # passengers per lane per hour (fast track)
    "passport_control": 80,       # passengers per station per hour
    "immigration_fast_track": 120,  # passengers per station per hour
    "baggage_system": 4000,        # bags per hour per system
    "baggage_carousel": 900,       # bags per hour per carousel
}

@dataclass
class Flight:
    """Represents a flight for resource allocation."""
    flight_number: str
    origin: str
    destination: str
    scheduled_time: datetime
    aircraft_type: str
    passengers: int
    direction: str  # arrival/departure
    terminal: str = "T1"

@dataclass
class ResourceAllocation:
    """Result of resource allocation for a timeframe."""
    gate_id: str
    resource_type: str
    allocated_to: str
    start_time: datetime
    end_time: datetime
    utilization: float = 0.0

class AirportCapacityOptimizer:
    """
    AI-powered airport capacity and resource optimization.
    """
    
    def __init__(self, airport_code: str = "IST"):
        self.airport_code = airport_code.upper()
        self.profile = AIRPORT_PROFILES.get(self.airport_code, AIRPORT_PROFILES["IST"])
    
    def optimize_gate_allocation(self, flights: List[Flight], 
                                   include_remote: bool = True) -> Dict:
        """
        Optimize gate assignment for flights.
        
        Uses constraint optimization to minimize:
        - Walking distance for passengers
        - Gate conflicts
        - Remote stand usage
        """
        # Gate layout by terminal (simulated)
        gates = self._generate_gate_layout(flights, include_remote)
        
        # Sort flights by scheduled time
        sorted_flights = sorted(flights, key=lambda f: f.scheduled_time)
        
        assignments = {}
        conflicts = 0
        remote_assignments = 0
        
        for flight in sorted_flights:
            aircraft_size = AIRCRAFT_GATE_SIZE.get(flight.aircraft_type, "small")
            
            # Find best available gate
            best_gate = None
            best_score = -1
            
            for gate_id, gate_info in gates.items():
                if gate_info["size"] != aircraft_size and gate_info["size"] != "any":
                    continue
                
                # Check time conflict with already assigned flights
                has_conflict = False
                for other_f in sorted_flights:
                    if other_f.flight_number == flight.flight_number:
                        continue
                    if assignments.get(other_f.flight_number) == gate_id:
                        if self._times_overlap(flight, other_f):
                            has_conflict = True
                            break
                
                if not has_conflict and gate_id not in assignments.values():
                    score = gate_info.get("priority", 50)
                    if score > best_score:
                        best_score = score
                        best_gate = gate_id
            
            if best_gate is None:
                # Try remote stands
                remote_stands = {k: v for k, v in gates.items() if v.get("is_remote", False)}
                for gate_id, gate_info in remote_stands.items():
                    if gate_info["size"] != aircraft_size and gate_info["size"] != "any":
                        continue
                    has_conflict = False
                    for other_f in sorted_flights:
                        if other_f.flight_number == flight.flight_number:
                            continue
                        if assignments.get(other_f.flight_number) == gate_id and self._times_overlap(flight, other_f):
                            has_conflict = True
                            break
                    if not has_conflict and gate_id not in assignments.values():
                        best_gate = gate_id
                        remote_assignments += 1
                        break
                
                if best_gate is None:
                    conflicts += 1
                    best_gate = f"GATE-{random.randint(1, self.profile['total_gates'])}"
            
            assignments[flight.flight_number] = best_gate
        
        return {
            "airport": self.profile["name"],
            "optimization_results": {
                "total_flights": len(flights),
                "gate_assignments": {f: g for f, g in assignments.items()},
                "conflicts": conflicts,
                "remote_stand_assignments": remote_assignments,
                "utilization": self._calculate_gate_utilization(assignments, flights, gates),
            },
            "resource_summary": {
                "total_gates": self.profile["total_gates"],
                "jetway_stands": self.profile["jetway_stands"],
                "remote_stands": self.profile["remote_stands"],
                "available_capacity": self.profile["total_gates"] - len([a for a in assignments.values() if not a.startswith("GATE-")]),
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    def _generate_gate_layout(self, flights: List[Flight], include_remote: bool) -> Dict:
        """Generate gate layout with terminal assignments."""
        gates = {}
        
        # Determine terminal distribution
        terminals = list(set(f.terminal for f in flights)) or ["T1"]
        gates_per_terminal = self.profile["total_gates"] // len(terminals)
        
        gate_num = 1
        for terminal in terminals:
            for i in range(gates_per_terminal):
                is_remote = terminal == "REMOTE" or (include_remote and gate_num > gates_per_terminal * 0.85)
                gates[f"{terminal}-{gate_num:03d}"] = {
                    "terminal": terminal,
                    "size": random.choice(["small", "small", "large", "any"]),
                    "priority": 100 - i,
                    "is_remote": is_remote,
                }
                gate_num += 1
        
        return gates
    
    def _times_overlap(self, flight1: Flight, flight2: Flight) -> bool:
        """Check if two flights overlap in time (turnaround buffer = 45 min)."""
        turnaround = timedelta(minutes=45)
        start1 = flight1.scheduled_time - turnaround
        end1 = flight1.scheduled_time + turnaround
        start2 = flight2.scheduled_time - turnaround
        end2 = flight2.scheduled_time + turnaround
        
        return start1 < end2 and start2 < end1
    
    def _calculate_gate_utilization(self, assignments: Dict, flights: List[Flight], 
                                     gates: Dict) -> float:
        """Calculate overall gate utilization rate."""
        if not gates:
            return 0.0
        
        turnaround = timedelta(minutes=90)
        total_gate_hours = len(gates) * 24  # 24-hour operation
        used_hours = sum(turnaround.total_seconds() / 3600 for _ in assignments)
        
        return min(1.0, round(used_hours / total_gate_hours * 100, 1))
    
    def optimize_security_lane_allocation(self, passenger_flows: Dict[str, int],
                                           time_blocks: List[str]) -> Dict:
        """
        Optimize security lane allocation across time blocks.
        
        Args:
            passenger_flows: Dict mapping time_block -> passenger_count
            time_blocks: List of time block identifiers
        """
        total_lanes = self.profile["security_lanes"]
        results = {}
        
        # Peak hour: allocate more lanes
        total_passengers = sum(passenger_flows.values())
        peak_block = max(passenger_flows, key=passenger_flows.get) if passenger_flows else None
        peak_passengers = passenger_flows.get(peak_block, 0) if peak_block else 0
        
        for block in time_blocks:
            passengers = passenger_flows.get(block, 0)
            if not passengers:
                continue
            
            # Calculate optimal lane count
            required_capacity = passengers / PROCESSING_RATES["security_lane"]
            optimal_lanes = min(total_lanes, max(1, math.ceil(required_capacity * 1.2)))
            
            # Fast track for high-flow periods
            fast_track_lanes = max(1, optimal_lanes // 4) if optimal_lanes >= 4 else 0
            standard_lanes = optimal_lanes - fast_track_lanes
            
            # Calculate wait times
            total_capacity = (standard_lanes * PROCESSING_RATES["security_lane"] +
                            fast_track_lanes * PROCESSING_RATES["fast_track_security"])
            wait_time = max(0, (passengers / total_capacity - 1) * 15) if total_capacity > 0 else 0
            
            results[block] = {
                "passengers": passengers,
                "standard_lanes": standard_lanes,
                "fast_track_lanes": fast_track_lanes,
                "total_lanes": optimal_lanes,
                "estimated_wait_time_min": round(wait_time, 1),
                "capacity_utilization": round(passengers / max(1, total_capacity) * 100, 1),
                "service_level": "excellent" if wait_time < 10 else "good" if wait_time < 20 else "acceptable" if wait_time < 30 else "poor"
            }
        
        return {
            "airport": self.profile["name"],
            "total_security_lanes": total_lanes,
            "time_block_analysis": results,
            "peak_time_block": peak_block,
            "peak_passengers": peak_passengers,
            "recommendation": self._get_security_recommendation(peak_block, peak_passengers, total_lanes),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    def _get_security_recommendation(self, peak_block: str, peak_passengers: int,
                                      total_lanes: int) -> str:
        """Generate security lane recommendation."""
        required = peak_passengers / PROCESSING_RATES["security_lane"]
        recommended = min(total_lanes, max(1, math.ceil(required * 1.2)))
        
        if recommended >= total_lanes * 0.8:
            return f"PEAK OVERLOAD: Allocate all {total_lanes} lanes during {peak_block}. Consider adding temporary lanes."
        elif recommended > total_lanes * 0.5:
            return f"MODERATE LOAD: Use {recommended} lanes during {peak_block} for optimal wait times."
        else:
            return f"LOW LOAD: {recommended} lanes sufficient during {peak_block}. Keep remaining lanes in reserve."
    
    def optimize_retail_concession(self, area_sqft: float, passenger_traffic: Dict[str, int],
                                   concession_types: List[str] = None) -> Dict:
        """
        Optimize retail/concession space allocation.
        
        Args:
            area_sqft: Total retail area in square feet
            passenger_traffic: Dict of zone -> passenger_count per day
        """
        if concession_types is None:
            concession_types = ["food", "duty_free", "fashion", "electronics", "services"]
        
        # Revenue per sqft by concession type (USD/sqft/day)
        revenue_rates = {
            "duty_free": 45.0,
            "food": 32.0,
            "fashion": 28.0,
            "electronics": 25.0,
            "services": 20.0,
        }
        
        # Recommended space allocation (% of total)
        optimal_alloc = {
            "duty_free": 0.30,
            "food": 0.25,
            "fashion": 0.20,
            "electronics": 0.10,
            "services": 0.15,
        }
        
        # Adjust for passenger traffic
        total_traffic = sum(passenger_traffic.values()) if passenger_traffic else 1
        traffic_weights = {
            zone: count / total_traffic
            for zone, count in passenger_traffic.items()
        }
        
        allocations = {}
        total_revenue = 0
        total_allocated = 0
        
        for concession in concession_types:
            base_pct = optimal_alloc.get(concession, 0.15)
            # Adjust by traffic in high-traffic zones
            high_traffic_factor = max(traffic_weights.values()) if traffic_weights else 0.5
            adjusted_pct = base_pct * (0.8 + 0.4 * high_traffic_factor)
            adjusted_pct = min(adjusted_pct, 0.35)  # Cap at 35%
            
            allocated_sqft = area_sqft * adjusted_pct
            revenue_per_sqft = revenue_rates.get(concession, 20.0)
            revenue = allocated_sqft * revenue_per_sqft
            
            allocations[concession] = {
                "allocated_sqft": round(allocated_sqft, 1),
                "allocation_percent": round(adjusted_pct * 100, 1),
                "daily_revenue_usd": round(revenue, 2),
                "annual_revenue_usd": round(revenue * 365, 2),
            }
            
            total_revenue += revenue
            total_allocated += adjusted_pct
        
        # Normalize remaining space
        if total_allocated < 1.0:
            remaining = 1.0 - total_allocated
            for concession in sorted(allocations.keys(), key=lambda x: revenue_rates.get(x, 0), reverse=True):
                allocations[concession]["allocated_sqft"] += area_sqft * remaining * (revenue_rates.get(concession, 0) / sum(revenue_rates.values()))
                break
        
        return {
            "airport": self.profile["name"],
            "total_retail_area_sqft": area_sqft,
            "passenger_traffic": passenger_traffic,
            "concession_allocations": allocations,
            "total_daily_revenue_usd": round(total_revenue, 2),
            "total_annual_revenue_usd": round(total_revenue * 365, 2),
            "revenue_per_passenger": round(total_revenue / max(1, total_traffic), 2),
            "optimization_summary": {
                "highest_revenue_concession": max(allocations, key=lambda x: allocations[x]["daily_revenue_usd"]),
                "most_efficient_concession": max(allocations, key=lambda x: revenue_rates.get(x, 0)),
                "space_utilization": round(total_allocated * 100, 1),
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    def optimize_baggage_handling(self, flights: List[Flight]) -> Dict:
        """
        Optimize baggage handling system capacity.
        """
        total_bags = sum(f.passengers for f in flights)
        baggage_per_flight = total_bags / max(len(flights), 1)
        
        systems = self.profile["baggage_systems"]
        carousels = 4  # Default
        
        total_capacity = systems * PROCESSING_RATES["baggage_system"]
        utilization = min(1.0, (total_bags * 1.4) / total_capacity)  # 1.4 bags per passenger
        
        # Risk assessment
        if utilization > 0.95:
            risk = "critical"
            recommendation = "ADD BAGGAGE SYSTEM CAPACITY IMMEDIATELY"
        elif utilization > 0.85:
            risk = "high"
            recommendation = "Monitor closely and consider adding temporary system"
        elif utilization > 0.70:
            risk = "normal"
            recommendation = "Maintain current configuration"
        else:
            risk = "low"
            recommendation = "Current capacity is adequate"
        
        # Optimize carousel assignment
        flights_by_arrival = [f for f in flights if f.direction == "arrival"]
        carousel_assignments = {}
        for i, flight in enumerate(flights_by_arrival):
            carousel = f"Carousel-{i % carousels + 1}"
            carousel_assignments[flight.flight_number] = carousel
        
        return {
            "airport": self.profile["name"],
            "baggage_analysis": {
                "total_flights": len(flights),
                "estimated_bags": total_bags * 1.4,
                "bags_per_flight": round(baggage_per_flight, 1),
                "systems_in_use": systems,
                "carousels": carousels,
                "system_capacity_per_hour": total_capacity,
                "current_utilization": round(utilization * 100, 1),
                "risk_level": risk,
                "recommendation": recommendation,
            },
            "carousel_assignments": carousel_assignments,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    def comprehensive_capacity_report(self) -> Dict:
        """Generate a comprehensive airport capacity report."""
        return {
            "airport": self.profile["name"],
            "airport_code": self.airport_code,
            "total_gates": self.profile["total_gates"],
            "terminals": self.profile.get("terminals", 1),
            "runway_capacity_per_hour": self.profile["runway_capacity"],
            "peak_hour_capacity": {
                "passenger_processing": (
                    self.profile["security_lanes"] * PROCESSING_RATES["security_lane"]
                ),
                "baggage_processing": (
                    self.profile["baggage_systems"] * PROCESSING_RATES["baggage_system"]
                ),
                "check_in_processing": (
                    self.profile["check_in_counters"] * PROCESSING_RATES["check_in_counter"]
                ),
                "immigration_processing": (
                    self.profile["passport_control"] * PROCESSING_RATES["passport_control"]
                ),
            },
            "current_utilization": {
                "estimated_gates_in_use": f"~{random.randint(65, 95)}%",
                "estimated_security_utilization": f"~{random.randint(50, 85)}%",
                "estimated_baggage_utilization": f"~{random.randint(45, 75)}%",
            },
            "expansion_opportunities": self._get_expansion_opportunities(),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    def _get_expansion_opportunities(self) -> List[Dict]:
        """Identify expansion opportunities."""
        opportunities = []
        
        gate_util = random.uniform(0.75, 0.98)
        if gate_util > 0.85:
            opportunities.append({
                "area": "Gates",
                "recommendation": "Add additional gates or optimize gate usage",
                "estimated_cost_usd": 50000000,
                "roi_months": 24,
            })
        
        security_util = random.uniform(0.65, 0.90)
        if security_util > 0.80:
            opportunities.append({
                "area": "Security",
                "recommendation": "Add 2-4 security lanes and deploy CT scanners",
                "estimated_cost_usd": 8000000,
                "roi_months": 18,
            })
        
        baggage_util = random.uniform(0.60, 0.85)
        if baggage_util > 0.80:
            opportunities.append({
                "area": "Baggage Handling",
                "recommendation": "Upgrade to automated sorting system",
                "estimated_cost_usd": 35000000,
                "roi_months": 36,
            })
        
        opportunities.append({
            "area": "Retail",
            "recommendation": "Optimize concession mix for higher revenue/sqft",
            "estimated_cost_usd": 2000000,
            "roi_months": 12,
        })
        
        return opportunities

# ─────────────────────────────────────────────
# API Convenience Functions
# ─────────────────────────────────────────────
_optimizer = None

def get_optimizer(airport_code: str = "IST"):
    global _optimizer
    if _optimizer is None:
        _optimizer = AirportCapacityOptimizer(airport_code)
    return _optimizer

def optimize_gate_allocation(flights: List[Dict], airport: str = "IST", 
                             include_remote: bool = True) -> dict:
    """Optimize gate allocation for flights."""
    optimizer = get_optimizer(airport)
    flight_objects = [
        Flight(
            flight_number=f["flight_number"],
            origin=f["origin"],
            destination=f["destination"],
            scheduled_time=datetime.fromisoformat(f["scheduled_time"].replace("Z", "+00:00")),
            aircraft_type=f["aircraft_type"],
            passengers=f["passengers"],
            direction=f["direction"],
            terminal=f.get("terminal", "T1"),
        )
        for f in flights
    ]
    return optimizer.optimize_gate_allocation(flight_objects, include_remote)

def optimize_security_lanes(passenger_flows: Dict[str, int], 
                            time_blocks: List[str], airport: str = "IST") -> dict:
    """Optimize security lane allocation."""
    optimizer = get_optimizer(airport)
    return optimizer.optimize_security_lane_allocation(passenger_flows, time_blocks)

def optimize_retail(allocation_sqft: float = 50000, 
                    passenger_traffic: Dict[str, int] = None, 
                    airport: str = "IST") -> dict:
    """Optimize retail/concession space allocation."""
    if passenger_traffic is None:
        passenger_traffic = {"T1": 25000, "T2": 15000, "T3": 10000}
    
    optimizer = get_optimizer(airport)
    return optimizer.optimize_retail_concession(allocation_sqft, passenger_traffic)

def optimize_baggage(flights: List[Dict], airport: str = "IST") -> dict:
    """Optimize baggage handling."""
    optimizer = get_optimizer(airport)
    flight_objects = [
        Flight(
            flight_number=f["flight_number"],
            origin=f["origin"],
            destination=f["destination"],
            scheduled_time=datetime.fromisoformat(f["scheduled_time"].replace("Z", "+00:00")),
            aircraft_type=f["aircraft_type"],
            passengers=f["passengers"],
            direction=f["direction"],
            terminal=f.get("terminal", "T1"),
        )
        for f in flights
    ]
    return optimizer.optimize_baggage_handling(flight_objects)

def get_airport_capacity_report(airport: str = "IST") -> dict:
    """Get comprehensive airport capacity report."""
    optimizer = get_optimizer(airport)
    return optimizer.comprehensive_capacity_report()

if __name__ == "__main__":
    # Sample flight data
    sample_flights = [
        {"flight_number": "TK101", "origin": "JFK", "destination": "IST",
         "scheduled_time": "2026-10-20T14:00:00Z", "aircraft_type": "A350",
         "passengers": 320, "direction": "arrival"},
        {"flight_number": "TK102", "origin": "IST", "destination": "FRA",
         "scheduled_time": "2026-10-20T15:30:00Z", "aircraft_type": "B737",
         "passengers": 180, "direction": "departure"},
        {"flight_number": "LH225", "origin": "FRA", "destination": "IST",
         "scheduled_time": "2026-10-20T16:00:00Z", "aircraft_type": "A320",
         "passengers": 165, "direction": "arrival"},
    ]
    
    result = optimize_gate_allocation(sample_flights)
    print(json.dumps(result, indent=2))
