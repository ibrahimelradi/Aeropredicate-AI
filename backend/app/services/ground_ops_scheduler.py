"""
Ground Operations Scheduling System
====================================
AI-powered optimization of ground handling operations.

Solves:
1. Ground crew shift scheduling
2. Equipment (GPU, ASU, belt loader) allocation
3. Turnaround resource optimization
4. Ramp agent assignment
5. Fueling truck dispatch optimization
6. Ground power unit (GPU) scheduling
"""

import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, field
import math

# ─────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────

# Ground support equipment (GSE) types and availability
GSE_TYPES = {
    "GPU": {  # Ground Power Unit
        "count": 20,
        "power_kw": 120,
        "usage_rate": 0.7,
        "hourly_cost": 85,
    },
    "ASU": {  # Air Start Unit
        "count": 15,
        "usage_rate": 0.6,
        "hourly_cost": 120,
    },
    "BELT_LOADER": {
        "count": 30,
        "usage_rate": 0.8,
        "hourly_cost": 75,
    },
    "FUEL_TRUCK": {
        "count": 12,
        "capacity_liters": 15000,
        "usage_rate": 0.65,
        "hourly_cost": 95,
    },
    "BAGGAGE_TUG": {
        "count": 25,
        "usage_rate": 0.75,
        "hourly_cost": 65,
    },
    "CATERING_TRUCK": {
        "count": 8,
        "usage_rate": 0.5,
        "hourly_cost": 110,
    },
    "STAIRCASE_TRUCK": {
        "count": 10,
        "usage_rate": 0.4,
        "hourly_cost": 80,
    },
    "WATER_TRUCK": {
        "count": 6,
        "usage_rate": 0.3,
        "hourly_cost": 70,
    },
}

# Ground crew positions
CREW_POSITIONS = {
    " ramp_agent": {"count": 40, "hourly_wage": 22},
    "gate_agent": {"count": 35, "hourly_wage": 20},
    "baggage_handler": {"count": 50, "hourly_wage": 24},
    "fuel_technician": {"count": 15, "hourly_wage": 28},
    "gse_operator": {"count": 30, "hourly_wage": 26},
}

# Shift patterns
SHIFT_PATTERNS = {
    "morning": {"start": "06:00", "end": "14:00", "count": 0.4},   # 40% of crew
    "afternoon": {"start": "14:00", "end": "22:00", "count": 0.35}, # 35% of crew
    "night": {"start": "22:00", "end": "06:00", "count": 0.25},    # 25% of crew
}

# Turnaround task types and durations (minutes)
TURNAROUND_TASKS = {
    "GPU_connection": {"duration": 5, "crew": 1, "equipment": None},
    "ASU_connection": {"duration": 10, "crew": 1, "equipment": "ASU"},
    "catering": {"duration": 25, "crew": 3, "equipment": "CATERING_TRUCK"},
    "baggage_loading": {"duration": 40, "crew": 4, "equipment": "BELT_LOADER"},
    "baggage_unloading": {"duration": 35, "crew": 4, "equipment": "BELT_LOADER"},
    "fueling": {"duration": 30, "crew": 2, "equipment": "FUEL_TRUCK"},
    "water_refill": {"duration": 15, "crew": 2, "equipment": "WATER_TRUCK"},
    "lavatory_service": {"duration": 12, "crew": 2, "equipment": "BAGGAGE_TUG"},
    "boarding_stairs": {"duration": 8, "crew": 2, "equipment": "STAIRCASE_TRUCK"},
    "deboarding_stairs": {"duration": 8, "crew": 2, "equipment": "STAIRCASE_TRUCK"},
}

@dataclass
class GroundCrew:
    """Represents a ground crew member."""
    crew_id: str
    position: str
    shift_start: datetime
    shift_end: datetime
    hourly_wage: float
    assigned_tasks: List[str] = field(default_factory=list)

@dataclass
class GSE:
    """Represents ground support equipment."""
    equipment_id: str
    type: str
    available: bool = True
    current_task: str = None
    next_available: datetime = None

class GroundOpsScheduler:
    """
    AI-powered ground operations scheduling.
    """
    
    def __init__(self):
        self.gse_types = GSE_TYPES
        self.crew_positions = CREW_POSITIONS
        self.shift_patterns = SHIFT_PATTERNS
        self.turnaround_tasks = TURNAROUND_TASKS
    
    def optimize_turnaround(self, aircraft_type: str = "A320",
                            turnaround_time_target: int = 45) -> Dict:
        """
        Optimize turnaround operations with parallel task scheduling.
        
        Returns optimal task sequence and resource allocation.
        """
        # Get turnaround tasks based on aircraft type
        tasks = self._get_turnaround_tasks(aircraft_type)
        
        # Parallelizable groups (tasks that can run simultaneously)
        parallel_groups = self._group_parallel_tasks(tasks)
        
        # Optimize with resource constraints
        current_duration = 0
        for group in parallel_groups:
            group_duration = max(self.turnaround_tasks[task]["duration"] for task in group)
            current_duration += group_duration
        
        # Resource requirements
        total_crew_needed = max(
            sum(self.turnaround_tasks[task]["crew"] for task in group)
            for group in parallel_groups
        )
        equipment_needed = set()
        for group in parallel_groups:
            for task in group:
                eq = self.turnaround_tasks[task]["equipment"]
                if eq:
                    equipment_needed.add(eq)
        
        # Calculate costs
        labor_cost = total_crew_needed * (current_duration / 60) * 22  # avg wage
        equipment_cost = len(equipment_needed) * (current_duration / 60) * 85
        total_cost = labor_cost + equipment_cost
        
        # Bottleneck analysis
        bottlenecks = []
        for group in parallel_groups:
            group_duration = max(self.turnaround_tasks[task]["duration"] for task in group)
            longest_task = max(group, key=lambda t: self.turnaround_tasks[t]["duration"])
            if group_duration > 15:
                bottlenecks.append({
                    "tasks": group,
                    "duration": group_duration,
                    "bottleneck_task": longest_task,
                })
        
        # Recommendations
        recommendations = []
        if current_duration < turnaround_time_target:
            recommendations.append(f"Achievable: {current_duration} min < {turnaround_time_target} min target")
        else:
            gap = current_duration - turnaround_time_target
            recommendations.append(f"Need to reduce by {gap} min — consider adding belt loader or parallel baggage ops")
        
        if bottlenecks:
            recommendations.append(f"Bottleneck: {bottlenecks[0]['bottleneck_task']} takes {bottlenecks[0]['duration']} min")
        
        return {
            "aircraft_type": aircraft_type,
            "optimized_turnaround_minutes": current_duration,
            "target_turnaround_minutes": turnaround_time_target,
            "achievable": current_duration <= turnaround_time_target,
            "parallel_task_groups": [
                {
                    "group": group,
                    "duration": max(self.turnaround_tasks[task]["duration"] for task in group),
                    "crew_needed": sum(self.turnaround_tasks[task]["crew"] for task in group),
                    "equipment": list(set(
                        self.turnaround_tasks[task]["equipment"]
                        for task in group if self.turnaround_tasks[task]["equipment"]
                    )),
                }
                for group in parallel_groups
            ],
            "resource_requirements": {
                "total_crew": total_crew_needed,
                "equipment": list(equipment_needed),
            },
            "cost_analysis": {
                "labor_cost_usd": round(labor_cost, 2),
                "equipment_cost_usd": round(equipment_cost, 2),
                "total_cost_usd": round(total_cost, 2),
            },
            "bottlenecks": bottlenecks,
            "recommendations": recommendations,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    def _get_turnaround_tasks(self, aircraft_type: str) -> List[str]:
        """Get relevant turnaround tasks for aircraft type."""
        if aircraft_type in ["A320", "A321", "B737", "A319", "E190", "ATR72"]:
            return ["GPU_connection", "ASU_connection", "catering", 
                    "baggage_loading", "baggage_unloading", "fueling",
                    "water_refill", "lavatory_service", "boarding_stairs"]
        elif aircraft_type in ["A330", "A350", "B787", "B777"]:
            return ["GPU_connection", "ASU_connection", "catering",
                    "baggage_loading", "baggage_unloading", "fueling",
                    "water_refill", "lavatory_service", "boarding_stairs",
                    "lavatory_service", "boarding_stairs"]
        elif aircraft_type == "A380":
            return ["GPU_connection", "ASU_connection", "catering", "catering",
                    "baggage_loading", "baggage_unloading", "baggage_unloading",
                    "fueling", "water_refill", "water_refill",
                    "lavatory_service", "lavatory_service", "boarding_stairs",
                    "boarding_stairs", "deboarding_stairs"]
        else:
            return ["GPU_connection", "catering", "baggage_loading", 
                    "baggage_unloading", "fueling"]
    
    def _group_parallel_tasks(self, tasks: List[str]) -> List[List[str]]:
        """Group tasks that can be performed in parallel."""
        # Remove duplicates
        unique_tasks = []
        seen = set()
        for t in tasks:
            if t not in seen:
                unique_tasks.append(t)
                seen.add(t)
        
        # Define parallelization groups
        parallel_groups = []
        
        # Group 1: External services (can run in parallel)
        external = []
        for t in ["fueling", "water_refill", "lavatory_service"]:
            if t in unique_tasks:
                external.append(t)
        if external:
            parallel_groups.append(external)
        
        # Group 2: Boarding/deboarding stairs (parallel with external)
        stairs = [t for t in ["boarding_stairs", "deboarding_stairs"] if t in unique_tasks]
        if stairs:
            parallel_groups.append(stairs)
        
        # Group 3: Catering (can overlap with external services)
        catering = [t for t in unique_tasks if t == "catering"]
        if catering:
            parallel_groups.append(catering)
        
        # Group 4: Baggage (sequential, can overlap with some)
        baggage = [t for t in ["baggage_loading", "baggage_unloading"] if t in unique_tasks]
        if baggage:
            parallel_groups.append(baggage)
        
        # Group 5: GPU/ASU (can run early in parallel)
        power = [t for t in ["GPU_connection", "ASU_connection"] if t in unique_tasks]
        if power:
            parallel_groups.append(power)
        
        return parallel_groups if parallel_groups else [[t] for t in unique_tasks]
    
    def schedule_ground_crew(self, date: str = None, timezone: str = "UTC") -> Dict:
        """
        Generate optimal ground crew shift schedule.
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        base_date = datetime.strptime(date, "%Y-%m-%d")
        shifts = []
        total_crew = 0
        total_labor_cost = 0
        
        for position, info in self.crew_positions.items():
            position_count = info["count"]
            hourly_wage = info["hourly_wage"]
            total_crew += position_count
            
            for shift_name, shift_info in self.shift_patterns.items():
                shift_count = int(position_count * shift_info["count"])
                start_time = self._parse_time(base_date, shift_info["start"])
                end_time = self._parse_time(base_date, shift_info["end"])
                if end_time < start_time:
                    end_time += timedelta(days=1)
                
                shift_duration = (end_time - start_time).total_seconds() / 3600
                shift_cost = shift_count * shift_duration * hourly_wage
                total_labor_cost += shift_cost
                
                shifts.append({
                    "position": position.strip(),
                    "shift_type": shift_name,
                    "crew_count": shift_count,
                    "start_time": start_time.strftime("%Y-%m-%dT%H:%M:00Z"),
                    "end_time": end_time.strftime("%Y-%m-%dT%H:%M:00Z"),
                    "hours_per_crew": shift_duration,
                    "hourly_wage": hourly_wage,
                    "shift_cost_usd": round(shift_cost, 2),
                })
        
        return {
            "date": date,
            "timezone": timezone,
            "shift_schedule": shifts,
            "summary": {
                "total_crew_members": total_crew,
                "total_shifts": len(shifts),
                "total_labor_cost_usd": round(total_labor_cost, 2),
                "coverage_pct": 100,
            },
            "peak_shift": max(shifts, key=lambda s: s["crew_count"])["shift_type"],
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    def _parse_time(self, base_date: datetime, time_str: str) -> datetime:
        """Parse time string to datetime."""
        h, m = map(int, time_str.split(":"))
        return base_date.replace(hour=h, minute=m, second=0, microsecond=0)
    
    def allocate_gse(self, flight_count: int = 50, operating_hours: int = 16) -> Dict:
        """
        Allocate ground support equipment for a given flight schedule.
        """
        allocations = {}
        total_gse_cost = 0
        utilization_rates = {}
        
        # Each flight needs specific GSE types
        gse_per_flight = {
            "GPU": 1, "ASU": 1, "BELT_LOADER": 2,
            "FUEL_TRUCK": 1, "BAGGAGE_TUG": 1,
            "CATERING_TRUCK": 1, "STAIRCASE_TRUCK": 1,
            "WATER_TRUCK": 1,
        }
        
        for gse_type, specs in self.gse_types.items():
            available_count = specs["count"]
            needed_per_flight = gse_per_flight.get(gse_type, 1)
            total_needed = flight_count * needed_per_flight
            
            # Utilization rate
            # Each unit serves multiple flights per hour
            flights_per_unit = operating_hours * 2  # Rough estimate
            units_needed = math.ceil(total_needed / flights_per_unit) if total_needed > 0 else 1
            
            utilization = min(1.0, units_needed / available_count)
            usage_hours = units_needed * operating_hours
            
            hourly_cost = specs["hourly_cost"]
            cost = usage_hours * hourly_cost
            total_gse_cost += cost
            
            allocations[gse_type] = {
                "available_units": available_count,
                "units_utilized": units_needed,
                "utilization_rate": round(utilization * 100, 1),
                "usage_hours": usage_hours,
                "hourly_cost_usd": hourly_cost,
                "total_cost_usd": round(cost, 2),
                "shortage": max(0, units_needed - available_count),
            }
            utilization_rates[gse_type] = utilization
        
        # Risk assessment
        shortages = {k: v["shortage"] for k, v in allocations.items() if v["shortage"] > 0}
        risk_level = "critical" if shortages else "high" if any(u > 0.9 for u in utilization_rates.values()) else \
                     "moderate" if any(u > 0.75 for u in utilization_rates.values()) else "low"
        
        recommendations = []
        for gse_type, info in allocations.items():
            if info["shortage"] > 0:
                recommendations.append(f"Add {info['shortage']} more {gse_type} units")
            elif info["utilization_rate"] > 90:
                recommendations.append(f"{gse_type} utilization critical ({info['utilization_rate']}%)")
        
        return {
            "flight_count": flight_count,
            "operating_hours": operating_hours,
            "gse_allocations": allocations,
            "total_gse_cost_usd": round(total_gse_cost, 2),
            "risk_level": risk_level,
            "shortages": shortages,
            "recommendations": recommendations,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    def optimize_fuel_truck_dispatch(self, flights: List[Dict]) -> Dict:
        """
        Optimize fuel truck dispatch scheduling.
        """
        # Group flights by time windows
        time_windows = {}
        for flight in flights:
            fuel_required = flight.get("fuel_required_liters", 20000)
            scheduled_time = flight.get("scheduled_time", "12:00")
            
            # Round to nearest hour
            hour_str = scheduled_time.split(":")[0]
            if hour_str not in time_windows:
                time_windows[hour_str] = {"flights": [], "total_fuel": 0}
            time_windows[hour_str]["flights"].append(flight)
            time_windows[hour_str]["total_fuel"] += fuel_required
        
        fuel_truck_capacity = self.gse_types["FUEL_TRUCK"]["capacity_liters"]
        fuel_truck_count = self.gse_types["FUEL_TRUCK"]["count"]
        refuel_time = 30  # minutes per flight
        
        dispatch_schedule = []
        total_cost = 0
        
        for hour, data in sorted(time_windows.items()):
            flights_in_window = data["flights"]
            total_fuel = data["total_fuel"]
            
            # Calculate trips needed
            trips_needed = math.ceil(total_fuel / fuel_truck_capacity)
            trucks_needed = min(fuel_truck_count, max(1, trips_needed))
            
            # Each truck can do multiple trips
            trips_per_truck = math.ceil(trips_needed / trucks_needed)
            total_refuel_time = flights_in_window * refuel_time
            total_dispatch_time = trips_per_truck * 45  # 45 min per trip (fuel + drive)
            
            cost = trucks_needed * 95 * (total_dispatch_time / 60)  # $95/hr
            total_cost += cost
            
            dispatch_schedule.append({
                "hour": hour,
                "flights": len(flights_in_window),
                "total_fuel_liters": total_fuel,
                "trucks_dispatched": trucks_needed,
                "trips_per_truck": trips_per_truck,
                "estimated_time": round(total_dispatch_time, 1),
                "cost_usd": round(cost, 2),
            })
        
        return {
            "total_flights": len(flights),
            "fuel_truck_capacity": fuel_truck_capacity,
            "total_trucks": fuel_truck_count,
            "dispatch_schedule": dispatch_schedule,
            "total_cost_usd": round(total_cost, 2),
            "average_cost_per_flight": round(total_cost / max(len(flights), 1), 2),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

# ─────────────────────────────────────────────
# API Convenience Functions
# ─────────────────────────────────────────────
_scheduler = None

def get_scheduler():
    global _scheduler
    if _scheduler is None:
        _scheduler = GroundOpsScheduler()
    return _scheduler

def optimize_turnaround(aircraft_type: str = "A320", target_minutes: int = 45) -> dict:
    """Optimize turnaround operations for an aircraft type."""
    scheduler = get_scheduler()
    return scheduler.optimize_turnaround(aircraft_type, target_minutes)

def schedule_ground_crew(date: str = None) -> dict:
    """Generate ground crew shift schedule."""
    scheduler = get_scheduler()
    return scheduler.schedule_ground_crew(date)

def allocate_gse(flight_count: int = 50, operating_hours: int = 16) -> dict:
    """Allocate ground support equipment."""
    scheduler = get_scheduler()
    return scheduler.allocate_gse(flight_count, operating_hours)

def optimize_fuel_dispatch(flights: List[Dict]) -> dict:
    """Optimize fuel truck dispatch."""
    scheduler = get_scheduler()
    return scheduler.optimize_fuel_truck_dispatch(flights)

def comprehensive_ground_ops_report(date: str = None) -> dict:
    """Generate comprehensive ground operations report."""
    scheduler = get_scheduler()
    
    # Generate sample flights
    sample_flights = []
    base_time = datetime.now().replace(hour=6, minute=0, second=0, microsecond=0)
    for i in range(30):
        sample_flights.append({
            "flight_number": f"TK{i+100}",
            "scheduled_time": (base_time + timedelta(hours=i//3)).strftime("%H:%M"),
            "aircraft_type": random.choice(["A320", "B737", "A330", "A350"]),
            "fuel_required_liters": random.randint(15000, 35000),
        })
    
    turnaround = scheduler.optimize_turnaround("A320", 45)
    crew_schedule = scheduler.schedule_ground_crew(date)
    gse_allocation = scheduler.allocate_gse(flight_count=30)
    fuel_dispatch = scheduler.optimize_fuel_truck_dispatch(sample_flights)
    
    return {
        "turnaround_optimization": turnaround,
        "crew_schedule": crew_schedule,
        "gse_allocation": gse_allocation,
        "fuel_dispatch": fuel_dispatch,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

if __name__ == "__main__":
    result = optimize_turnaround("A320", 45)
    print(json.dumps(result, indent=2))
    print("\n✅ Turnaround optimization complete")
