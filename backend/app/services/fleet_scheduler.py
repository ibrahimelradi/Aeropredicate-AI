"""
Airline Fleet Schedule Generator
=================================
AI system for generating optimized flight schedules for small airlines
and charter operators.

Solves:
1. Schedule optimization based on demand forecasts
2. Aircraft rotation planning
3. Maintenance slot scheduling
4. Crew pairing automation
5. Cost minimization

Target: Small airlines, charter operators, cargo operators
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, field

@dataclass
class AircraftSlot:
    """Represents an aircraft availability window."""
    aircraft_id: str
    aircraft_type: str
    start_time: datetime
    end_time: datetime
    
    @property
    def duration_hours(self) -> float:
        return (self.end_time - self.start_time).total_seconds() / 3600

@dataclass
class MaintenanceWindow:
    """Represents a scheduled maintenance window."""
    aircraft_id: str
    start_time: datetime
    end_time: datetime
    maintenance_type: str  # A-check, B-check, C-check, D-check

class FleetScheduler:
    """
    Generates optimized flight schedules for airline fleets.
    """
    
    def __init__(self):
        self.aircraft_fleet: List[Dict] = []
        self.flights: List[Dict] = []
        self.maintenance_windows: List[MaintenanceWindow] = []
    
    def generate_schedule(self, fleet_data: List[Dict],
                          route_demands: List[Dict],
                          date_str: str = None) -> Dict:
        """
        Generate optimized fleet schedule from route demands.
        
        Args:
            fleet_data: List of aircraft with capabilities
            route_demands: List of route requests with demand
            date_str: Date for schedule (YYYY-MM-DD)
        """
        if not date_str:
            date_str = datetime.now().strftime("%Y-%m-%d")
        
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        
        schedule = []
        unassigned_routes = []
        
        # Sort routes by priority (demand volume)
        sorted_routes = sorted(route_demands, 
                              key=lambda x: x.get("demand", 0), reverse=True)
        
        # Sort aircraft by availability
        available_aircraft = [a for a in fleet_data if a.get("status", "active") == "active"]
        
        for route in sorted_routes:
            assigned = False
            optimal_aircraft = None
            
            for aircraft in available_aircraft:
                # Check aircraft type match
                if aircraft.get("type") != route.get("aircraft_type"):
                    continue
                
                # Check range capability
                if aircraft.get("range_nm", 0) < route.get("distance_nm", 0):
                    continue
                
                # Check availability for departure time
                aircraft_availability = self._check_availability(
                    aircraft, route["dep_time"], 
                    date_obj + timedelta(hours=route.get("flight_time", 0))
                )
                
                if aircraft_availability["available"]:
                    optimal_aircraft = aircraft
                    assigned = True
                    break
            
            if assigned:
                flight_entry = {
                    "flight_number": self._generate_flight_number(route),
                    "route": f"{route['origin']} → {route['destination']}",
                    "origin": route["origin"],
                    "destination": route["destination"],
                    "departure": route["dep_time"],
                    "arrival": route["arr_time"],
                    "aircraft_id": optimal_aircraft["id"],
                    "aircraft_type": optimal_aircraft["type"],
                    "demand": route.get("demand", 0),
                    "revenue_estimate": route.get("demand", 0) * route.get("avg_fare", 300),
                    "status": "scheduled"
                }
                schedule.append(flight_entry)
            else:
                unassigned_routes.append({
                    "route": f"{route['origin']} → {route['destination']}",
                    "reason": "No suitable aircraft available",
                    "demand": route.get("demand", 0)
                })
        
        # Generate maintenance schedule
        maintenance_schedule = self._generate_maintenance_schedule(
            fleet_data, date_obj
        )
        
        # Calculate metrics
        total_revenue = sum(f["revenue_estimate"] for f in schedule)
        total_flights = len(schedule)
        aircraft_utilization = self._calculate_utilization(
            schedule, fleet_data, date_obj
        )
        
        return {
            "date": date_str,
            "schedule": schedule,
            "unassigned_routes": unassigned_routes,
            "maintenance_schedule": maintenance_schedule,
            "metrics": {
                "total_flights": total_flights,
                "total_revenue": round(total_revenue, 2),
                "avg_revenue_per_flight": round(total_revenue / max(total_flights, 1), 2),
                "unassigned_routes": len(unassigned_routes),
                "aircraft_utilization": aircraft_utilization,
            },
            "recommendations": self._generate_recommendations(
                schedule, unassigned_routes, maintenance_schedule
            ),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    def _check_availability(self, aircraft: Dict, dep_time: str, 
                            arr_time: datetime) -> Dict:
        """Check if aircraft is available for a flight."""
        # In a real implementation, this would check against scheduled flights
        # For demo, assume simple availability based on aircraft status
        return {
            "available": aircraft.get("status", "active") == "active",
            "reason": None if aircraft.get("status", "active") == "active" else "Aircraft not active"
        }
    
    def _generate_flight_number(self, route: Dict) -> str:
        """Generate flight number based on route."""
        # Simple pattern: TC + route index
        import hashlib
        hash_val = hashlib.md5(f"{route['origin']}{route['destination']}".encode()).hexdigest()
        num = int(hash_val[:4], 16) % 9000 + 1000
        return f"TC{num}"
    
    def _generate_maintenance_schedule(self, fleet_data: List[Dict], 
                                        date_obj: datetime) -> List[Dict]:
        """Generate maintenance schedule based on flight hours."""
        schedule = []
        
        for aircraft in fleet_data:
            flight_hours = aircraft.get("flight_hours", 0)
            hours_since_maint = flight_hours % 100  # A-check every 100 hours
            
            if hours_since_maint > 85:
                maint_type = "A-check"
                duration = 6  # hours
            elif hours_since_maint > 50:
                maint_type = "Visual Inspection"
                duration = 2
            else:
                continue  # No maintenance needed
            
            schedule.append({
                "aircraft_id": aircraft["id"],
                "maintenance_type": maint_type,
                "scheduled_time": (date_obj + timedelta(hours=2)).strftime("%Y-%m-%d %H:%M"),
                "duration_hours": duration,
                "reason": f"Last {maint_type} due in {100 - hours_since_maint} hours"
            })
        
        return sorted(schedule, key=lambda x: x["scheduled_time"])
    
    def _calculate_utilization(self, schedule: List[Dict], 
                                fleet_data: List[Dict],
                                date_obj: datetime) -> Dict:
        """Calculate aircraft utilization metrics."""
        utilization = {}
        
        for aircraft in fleet_data:
            aircraft_flights = [f for f in schedule if f["aircraft_id"] == aircraft["id"]]
            
            # Calculate total block time including overnight flights
            total_block_hours = 0.0
            for f in aircraft_flights:
                dep_time = datetime.strptime(f["departure"], "%H:%M")
                arr_time = datetime.strptime(f["arrival"], "%H:%M")
                block_time = (arr_time - dep_time).total_seconds() / 3600
                # Handle overnight flights (arrival time < departure time)
                if block_time < 0:
                    block_time += 24  # Add 24h for overnight
                total_block_hours += block_time
            
            utilization[aircraft["id"]] = {
                "type": aircraft.get("type", "unknown"),
                "flights_assigned": len(aircraft_flights),
                "block_hours": round(total_block_hours, 1),
                "utilization_pct": round(min(total_block_hours / 16 * 100, 100), 1)  # 16 usable hours/day
            }
        
        return utilization
    
    def _generate_recommendations(self, schedule: List[Dict], 
                                   unassigned: List[Dict],
                                   maintenance: List[Dict]) -> List[str]:
        """Generate scheduling recommendations."""
        recs = []
        
        if unassigned:
            total_unassigned_demand = sum(r["demand"] for r in unassigned)
            total_demand = sum(f["demand"] for f in schedule) + total_unassigned_demand
            if total_demand > 0:
                capacity = (total_demand - total_unassigned_demand) / total_demand * 100
                recs.append(f"Current capacity serves {capacity:.1f}% of demand")
            
            high_demand_routes = sorted(unassigned, key=lambda x: x["demand"], reverse=True)[:3]
            for route in high_demand_routes:
                recs.append(f"High-demand route {route['route']} ({route['demand']} pax) unassigned")
        
        if maintenance:
            aircraft_needing_maint = [m["aircraft_id"] for m in maintenance]
            recs.append(f"Schedule maintenance for: {', '.join(aircraft_needing_maint[:5])}")
            if len(aircraft_needing_maint) > 2:
                recs.append("Consider overnight maintenance to minimize schedule impact")
        
        # Utilization recommendations
        recs.append("Monitor early morning departures for crew positioning")
        recs.append("Consider code-share partnerships for unassigned routes")
        
        return recs

# ─────────────────────────────────────────────
# Sample Data + API Functions
# ─────────────────────────────────────────────

def generate_sample_fleet() -> List[Dict]:
    """Generate sample fleet data."""
    return [
        {"id": "TC-001", "type": "narrow_body", "model": "B737-800", "range_nm": 2935, 
         "flight_hours": 87.5, "status": "active", "base": "IST"},
        {"id": "TC-002", "type": "narrow_body", "model": "B737-800", "range_nm": 2935,
         "flight_hours": 42.3, "status": "active", "base": "IST"},
        {"id": "TC-003", "type": "narrow_body", "model": "A320neo", "range_nm": 3400,
         "flight_hours": 95.8, "status": "active", "base": "IST"},
        {"id": "TC-004", "type": "wide_body", "model": "B777-300ER", "range_nm": 7700,
         "flight_hours": 112.4, "status": "active", "base": "IST"},
        {"id": "TC-005", "type": "wide_body", "model": "A330-300", "range_nm": 6700,
         "flight_hours": 78.9, "status": "maintenance", "base": "IST"},
    ]

def generate_sample_routes() -> List[Dict]:
    """Generate sample route demands."""
    return [
        {"origin": "IST", "destination": "JFK", "distance_nm": 4400, "flight_time": 11,
         "dep_time": "14:30", "arr_time": "18:45", "aircraft_type": "wide_body",
         "demand": 280, "avg_fare": 850},
        {"origin": "IST", "destination": "LHR", "distance_nm": 1700, "flight_time": 3.5,
         "dep_time": "09:00", "arr_time": "11:30", "aircraft_type": "narrow_body",
         "demand": 180, "avg_fare": 320},
        {"origin": "IST", "destination": "DXB", "distance_nm": 1800, "flight_time": 4.0,
         "dep_time": "03:00", "arr_time": "07:00", "aircraft_type": "narrow_body",
         "demand": 160, "avg_fare": 280},
        {"origin": "IST", "destination": "BAH", "distance_nm": 1300, "flight_time": 2.5,
         "dep_time": "11:00", "arr_time": "13:30", "aircraft_type": "narrow_body",
         "demand": 120, "avg_fare": 200},
        {"origin": "IST", "destination": "SAW", "distance_nm": 50, "flight_time": 1.0,
         "dep_time": "08:00", "arr_time": "09:00", "aircraft_type": "regional",
         "demand": 50, "avg_fare": 80},
    ]

_scheduler = None

def get_scheduler():
    global _scheduler
    if _scheduler is None:
        _scheduler = FleetScheduler()
    return _scheduler

def generate_fleet_schedule(fleet_data: List[Dict] = None,
                             route_demands: List[Dict] = None,
                             date_str: str = None) -> Dict:
    """Generate optimized fleet schedule."""
    scheduler = get_scheduler()
    
    if fleet_data is None:
        fleet_data = generate_sample_fleet()
    if route_demands is None:
        route_demands = generate_sample_routes()
    
    return scheduler.generate_schedule(fleet_data, route_demands, date_str)

if __name__ == "__main__":
    result = generate_fleet_schedule()
    print(json.dumps(result, indent=2))