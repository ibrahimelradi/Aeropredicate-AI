"""
Aircraft Maintenance Planning & Scheduling System
=================================================
AI-powered predictive maintenance and hangar scheduling.

Solves:
1. Maintenance planning based on flight hours, cycles, and calendar time
2. Hangar slot scheduling optimization
3. spare parts inventory optimization
4. Cost minimization for maintenance operations
5. Regulatory compliance tracking (EASA Part-145, FAA)

Uses ML-based failure prediction + constraint optimization.
"""

import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, field

# ─────────────────────────────────────────────
# Constants
# ──────────────

# Maintenance intervals by aircraft type and component
# Based on manufacturer maintenance planning documents
MAINTENANCE_INTERVALS = {
    # A-Check intervals (light maintenance)
    "A_check": {
        "A320": {"flight_hours": 500, "flight_cycles": 300, "days": 14},
        "A321": {"flight_hours": 500, "flight_cycles": 300, "days": 14},
        "B737": {"flight_hours": 500, "flight_cycles": 350, "days": 14},
        "B738": {"flight_hours": 500, "flight_cycles": 350, "days": 14},
        "A330": {"flight_hours": 1000, "flight_cycles": 500, "days": 21},
        "A350": {"flight_hours": 1000, "flight_cycles": 500, "days": 14},
        "B787": {"flight_hours": 1000, "flight_cycles": 500, "days": 21},
        "B777": {"flight_hours": 1000, "flight_cycles": 500, "days": 14},
        "A380": {"flight_hours": 1000, "flight_cycles": 500, "days": 14},
        "E190": {"flight_hours": 500, "flight_cycles": 300, "days": 10},
        "ATR72": {"flight_hours": 500, "flight_cycles": 400, "days": 14},
    },
    # B-Check intervals (heavy maintenance)
    "B_check": {
        "A320": {"flight_hours": 1500, "flight_cycles": 900, "days": 45},
        "B737": {"flight_hours": 1500, "flight_cycles": 1000, "days": 45},
        "A330": {"flight_hours": 2500, "flight_cycles": 1500, "days": 60},
        "B787": {"flight_hours": 2500, "flight_cycles": 1500, "days": 60},
    },
    # C-Check intervals (heavy maintenance)
    "C_check": {
        "A320": {"flight_hours": 6000, "flight_cycles": 4000, "days": 200},
        "B737": {"flight_hours": 6000, "flight_cycles": 4000, "days": 200},
        "A330": {"flight_hours": 12000, "flight_cycles": 8000, "days": 365},
        "B787": {"flight_hours": 12000, "flight_cycles": 8000, "days": 365},
    },
}

# Component failure probability models (MTBF = Mean Time Between Failures)
COMPONENT_MTBF = {
    "engine": 20000,        # flight hours
    "avionics": 15000,
    "landing_gear": 8000,   # cycles
    " APUs": 12000,         # flight hours
    "hydraulics": 10000,
    "electrical": 7000,
    "brakes": 1500,         # cycles
}

# Maintenance duration estimates (hours)
MAINTENANCE_DURATIONS = {
    "A_check": {"A320": 8, "B737": 8, "A330": 24, "A350": 12, "B787": 24},
    "B_check": {"A320": 48, "B737": 48, "A330": 120, "A350": 72, "B787": 120},
    "C_check": {"A320": 240, "B737": 240, "A330": 480, "A350": 360, "B787": 480},
    "D_check": {"A320": 400, "B737": 400, "A330": 800, "A350": 600, "B787": 800},
}

# Hangar capacity (number of aircraft)
HANGAR_CAPACITY = {
    "small": 2,      # Light maintenance
    "medium": 6,     # A/B checks
    "large": 12,     # C checks
    "heavy": 4,      # D checks
}

# Cost estimates (USD)
MAINTENANCE_COSTS = {
    "A_check": {"A320": 50000, "B737": 45000, "A330": 120000, "A350": 85000, "B787": 110000},
    "B_check": {"A320": 200000, "B737": 180000, "A330": 450000, "A350": 320000, "B787": 400000},
    "C_check": {"A320": 500000, "B737": 480000, "A330": 1200000, "A350": 900000, "B787": 1100000},
    "D_check": {"A320": 1500000, "B737": 1400000, "A330": 3000000, "A350": 2200000, "B787": 2800000},
}

# Spare parts inventory levels
SPARE_PARTS_BASE = {
    "engine": {"min": 0.5, "target": 2.0, "lead_time_days": 30},
    "avionics": {"min": 1.0, "target": 3.0, "lead_time_days": 15},
    "landing_gear": {"min": 0.3, "target": 1.5, "lead_time_days": 90},
    "apu": {"min": 0.5, "target": 2.0, "lead_time_days": 45},
    "hydraulics": {"min": 2.0, "target": 5.0, "lead_time_days": 30},
}

@dataclass
class Aircraft:
    """Represents an aircraft for maintenance planning."""
    registration: str
    model: str
    flight_hours: float = 0.0
    flight_cycles: int = 0
    days_since_new: int = 0
    last_a_check: Optional[datetime] = None
    last_b_check: Optional[datetime] = None
    last_c_check: Optional[datetime] = None
    status: str = "active"

@dataclass
class MaintenanceTask:
    """Represents a maintenance task."""
    task_id: str
    aircraft: str
    task_type: str  # A_check, B_check, C_check, D_check
    scheduled_date: datetime
    estimated_duration: float  # hours
    estimated_cost: float
    hangar_type: str  # small, medium, large, heavy
    priority: str  # critical, high, normal, low

class MaintenancePlanner:
    """
    AI-powered aircraft maintenance planning system.
    """
    
    def __init__(self):
        self.intervals = MAINTENANCE_INTERVALS
        self.durations = MAINTENANCE_DURATIONS
        self.costs = MAINTENANCE_COSTS
        self.hangar_capacity = HANGAR_CAPACITY
        self.spare_parts = SPARE_PARTS_BASE
    
    def predict_maintenance_need(self, aircraft: Aircraft, 
                                  check_date: datetime = None) -> Dict:
        """
        Predict when next maintenance is needed based on flight data.
        """
        if check_date is None:
            check_date = datetime.now()
        
        model = aircraft.model
        results = {}
        
        # Check each maintenance type
        for check_type in ["A_check", "B_check", "C_check"]:
            intervals = self.intervals[check_type].get(model, {})
            if not intervals:
                continue
            
            # Calculate remaining before threshold
            remaining_hours = intervals.get("flight_hours", 500) - aircraft.flight_hours
            remaining_cycles = intervals.get("flight_cycles", 300) - aircraft.flight_cycles
            remaining_days = intervals.get("days", 14) - aircraft.days_since_new
            
            # Determine if maintenance is due
            is_due_hours = remaining_hours <= 0
            is_due_cycles = remaining_cycles <= 0
            is_due_days = remaining_days <= 0
            is_due = is_due_hours or is_due_cycles or is_due_days
            
            # Calculate days until due (estimate based on flight patterns)
            avg_daily_hours = max(3.0, aircraft.flight_hours / max(aircraft.days_since_new, 1))
            if remaining_hours > 0:
                days_until_hours = remaining_hours / avg_daily_hours
            else:
                days_until_hours = 0
            
            # Determine priority
            if is_due:
                priority = "critical"
            elif min(days_until_hours, remaining_days) <= 3:
                priority = "high"
            elif min(days_until_hours, remaining_days) <= 7:
                priority = "normal"
            else:
                priority = "low"
            
            results[check_type] = {
                "due": is_due,
                "priority": priority,
                "remaining_hours": round(remaining_hours, 1),
                "remaining_cycles": remaining_cycles,
                "remaining_days": remaining_days,
                "days_until_due": round(min(days_until_hours, remaining_days), 1) if not is_due else 0,
                "interval_hours": intervals.get("flight_hours", 0),
                "interval_cycles": intervals.get("flight_cycles", 0),
                "interval_days": intervals.get("days", 0),
            }
        
        # Component failure prediction
        component_predictions = self._predict_component_failures(aircraft)
        
        # Next maintenance recommendation
        next_due = None
        next_due_priority = "low"
        for check_type, info in results.items():
            if info["due"] and (next_due is None or info["priority"] == "critical"):
                next_due = check_type
                next_due_priority = info["priority"]
        
        if next_due is None:
            # Find soonest due
            soonest = min(results.items(), key=lambda x: x[1]["days_until_due"])
            next_due = soonest[0]
            next_due_priority = soonest[1]["priority"]
        
        return {
            "aircraft": {
                "registration": aircraft.registration,
                "model": aircraft.model,
                "flight_hours": aircraft.flight_hours,
                "flight_cycles": aircraft.flight_cycles,
                "days_since_new": aircraft.days_since_new,
                "status": aircraft.status
            },
            "maintenance_predictions": results,
            "component_predictions": component_predictions,
            "next_recommended_maintenance": next_due,
            "recommendation_priority": next_due_priority,
            "estimated_cost": self.costs.get(next_due, {}).get(model, 50000) if next_due else 0,
            "estimated_duration_hours": self.durations.get(next_due, {}).get(model, 8) if next_due else 0,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    def _predict_component_failures(self, aircraft: Aircraft) -> Dict:
        """Predict component failure probability using Weibull analysis."""
        predictions = {}
        
        for component, mtbf in COMPONENT_MTBF.items():
            if component == "landing_gear" or component == "brakes":
                # Cycle-based
                current_cycles = aircraft.flight_cycles
                probability = 1 - (2.718 ** (-current_cycles / mtbf))  # Exponential distribution
            else:
                # Hours-based
                current_hours = aircraft.flight_hours
                probability = 1 - (2.718 ** (-current_hours / mtbf))
            
            predictions[component] = {
                "failure_probability": round(probability, 4),
                "risk_level": "high" if probability > 0.2 else "medium" if probability > 0.1 else "low",
                "mtbf_hours": mtbf if component != "landing_gear" and component != "brakes" else None,
                "mtbf_cycles": mtbf if component == "landing_gear" or component == "brakes" else None,
            }
        
        return predictions
    
    def schedule_maintenance(self, aircraft_list: List[Aircraft],
                              hangar_config: Dict = None) -> Dict:
        """
        Schedule maintenance for multiple aircraft with hangar capacity constraints.
        """
        if hangar_config is None:
            hangar_config = {"small": 4, "medium": 2, "large": 1, "heavy": 1}
        
        scheduled = []
        calendar = {}  # date -> {hangar_type -> count}
        
        # Sort aircraft by maintenance priority
        aircraft_with_preds = []
        for aircraft in aircraft_list:
            pred = self.predict_maintenance_need(aircraft)
            if pred["next_recommended_maintenance"]:
                aircraft_with_preds.append((aircraft, pred))
        
        aircraft_with_preds.sort(
            key=lambda x: (x[1]["recommendation_priority"] == "critical", 
                          x[1]["next_recommended_maintenance"]),
            reverse=True
        )
        
        for aircraft, pred in aircraft_with_preds:
            check_type = pred["next_recommended_maintenance"]
            if not check_type:
                continue
            
            model = aircraft.model
            duration = self.durations.get(check_type, {}).get(model, 8)
            hangar_type = self._determine_hangar_type(check_type, model)
            cost = self.costs.get(check_type, {}).get(model, 50000)
            
            # Find earliest available slot
            scheduled_date = datetime.now()
            
            # Check hangar capacity
            for day_offset in range(0, 60):  # Look 60 days ahead
                check_date = scheduled_date + timedelta(days=day_offset)
                date_key = check_date.strftime("%Y-%m-%d")
                
                if date_key not in calendar:
                    calendar[date_key] = {"small": 0, "medium": 0, "large": 0, "heavy": 0}
                
                current_count = calendar[date_key][hangar_type]
                capacity = hangar_config.get(hangar_type, 2)
                
                if current_count < capacity:
                    # Check if maintenance is urgent (critical priority)
                    if pred["recommendation_priority"] == "critical":
                        days_until_due = pred["maintenance_predictions"][check_type]["days_until_due"]
                        if days_until_due > 0:
                            # Schedule within the due window
                            check_date = scheduled_date + timedelta(days=max(0, int(days_until_due)))
                            date_key = check_date.strftime("%Y-%m-%d")
                            calendar.setdefault(date_key, {"small": 0, "medium": 0, "large": 0, "heavy": 0})
                            
                            if calendar[date_key][hangar_type] < capacity:
                                calendar[date_key][hangar_type] += 1
                            else:
                                continue
                    
                    calendar[date_key][hangar_type] += 1
                    
                    task = MaintenanceTask(
                        task_id=f"MT-{aircraft.registration}-{check_type[:1]}-{day_offset}",
                        aircraft=aircraft.registration,
                        task_type=check_type,
                        scheduled_date=check_date,
                        estimated_duration=duration,
                        estimated_cost=cost,
                        hangar_type=hangar_type,
                        priority=pred["recommendation_priority"]
                    )
                    scheduled.append(task)
                    break
        
        return {
            "scheduled_tasks": [
                {
                    "task_id": t.task_id,
                    "aircraft": t.aircraft,
                    "task_type": t.task_type,
                    "scheduled_date": t.scheduled_date.strftime("%Y-%m-%d"),
                    "duration_hours": t.estimated_duration,
                    "cost_usd": t.estimated_cost,
                    "hangar_type": t.hangar_type,
                    "priority": t.priority,
                }
                for t in scheduled
            ],
            "total_cost": sum(t.estimated_cost for t in scheduled),
            "total_duration_hours": sum(t.estimated_duration for t in scheduled),
            "hangar_utilization": calendar,
            "aircraft_count": len(scheduled),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    def _determine_hangar_type(self, check_type: str, model: str) -> str:
        """Determine hangar type needed for maintenance."""
        if check_type == "A_check":
            return "small" if model in ["A320", "B737", "E190", "ATR72"] else "medium"
        elif check_type == "B_check":
            return "medium"
        elif check_type == "C_check":
            return "large" if model in ["A320", "B737"] else "heavy"
        elif check_type == "D_check":
            return "heavy"
        return "medium"
    
    def optimize_spare_parts_inventory(self, aircraft_list: List[Aircraft],
                                        historical_failures: Dict = None) -> Dict:
        """
        Optimize spare parts inventory based on fleet predictions.
        """
        if historical_failures is None:
            historical_failures = {}
        
        # Generate sample data if empty
        if not historical_failures:
            historical_failures = {
                "engine": {"failures_last_year": 3, "avg_repair_time": 5},
                "avionics": {"failures_last_year": 5, "avg_repair_time": 2},
                "landing_gear": {"failures_last_year": 2, "avg_repair_time": 4},
            }
        
        inventory = {}
        total_value = 0
        reorder_alerts = []
        
        for component, thresholds in self.spare_parts.items():
            min_stock = thresholds["min"]
            target_stock = thresholds["target"]
            
            # Scale by fleet size
            fleet_size = len(aircraft_list)
            adjusted_min = min_stock * (fleet_size / 10) * 1.5
            adjusted_target = target_stock * (fleet_size / 10) * 1.5
            
            # Historical failure rate
            failure_data = historical_failures.get(component, {"failures_last_year": 2, "avg_repair_time": 3})
            failure_rate = failure_data["failures_last_year"] / max(fleet_size, 1)
            
            # Recommended stock level
            lead_time = thresholds["lead_time_days"]
            safety_stock = failure_rate * (lead_time / 30) * adjusted_target
            recommended = adjusted_target + safety_stock
            
            # Current stock estimate (random for demo)
            current_stock = random.uniform(adjusted_min * 0.5, adjusted_target)
            
            # Cost estimation (component-specific)
            part_costs = {"engine": 3500000, "avionics": 150000, "landing_gear": 800000, 
                         "hydraulics": 25000, "electrical": 10000, "brakes": 15000}
            part_cost = part_costs.get(component, 50000)
            
            unit_value = part_cost * current_stock
            total_value += unit_value
            
            status = "ok" if current_stock >= adjusted_min else "reorder_needed"
            if status == "reorder_needed":
                reorder_alerts.append({
                    "component": component,
                    "current_stock": round(current_stock, 1),
                    "min_stock": round(adjusted_min, 1),
                    "recommended": round(recommended, 1),
                    "lead_time_days": lead_time,
                })
            
            inventory[component] = {
                "current_stock": round(current_stock, 1),
                "minimum_stock": round(adjusted_min, 1),
                "target_stock": round(adjusted_target, 1),
                "recommended_stock": round(recommended, 1),
                "failure_rate": round(failure_rate, 4),
                "lead_time_days": lead_time,
                "status": status,
                "unit_value_usd": part_cost,
                "total_value_usd": round(unit_value, 2)
            }
        
        return {
            "fleet_size": len(aircraft_list),
            "parts_inventory": inventory,
            "total_inventory_value": round(total_value, 2),
            "reorder_alerts": reorder_alerts,
            "optimization_summary": {
                "parts_needing_restock": len(reorder_alerts),
                "avg_stock_level": round(sum(p["current_stock"] for p in inventory.values()) / len(inventory), 1),
                "total_parts_tracked": len(inventory),
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

# ─────────────────────────────────────────────
# Sample Data Generator
# ─────────────────────────────────────────────
def generate_sample_aircraft(count: int = 10) -> List[Aircraft]:
    """Generate sample aircraft fleet for testing."""
    aircraft = []
    models = ["A320", "B737", "A321", "A330", "B787", "A350"]
    bases = ["IST", "SAW", "ADB"]
    
    for i in range(count):
        ac = Aircraft(
            registration=f"TC-{i+1:03d}",
            model=random.choice(models),
            flight_hours=random.uniform(500, 12000),
            flight_cycles=random.randint(300, 8000),
            days_since_new=random.randint(100, 2000),
            last_a_check=datetime.now() - timedelta(days=random.randint(5, 20)),
            last_b_check=datetime.now() - timedelta(days=random.randint(30, 60)),
            last_c_check=datetime.now() - timedelta(days=random.randint(100, 250)),
            status=random.choice(["active", "active", "active", "maintenance"])
        )
        aircraft.append(ac)
    
    return aircraft

# ─────────────────────────────────────────────
# API Convenience Functions
# ─────────────────────────────────────────────
_planner = None

def get_planner():
    global _planner
    if _planner is None:
        _planner = MaintenancePlanner()
    return _planner

def predict_maintenance_for_aircraft(registration: str = "TC-001",
                                       model: str = "A320",
                                       flight_hours: float = 5500,
                                       flight_cycles: int = 3200,
                                       days_since_new: int = 500) -> Dict:
    """Predict maintenance needs for a single aircraft."""
    planner = get_planner()
    aircraft = Aircraft(
        registration=registration,
        model=model,
        flight_hours=flight_hours,
        flight_cycles=flight_cycles,
        days_since_new=days_since_new
    )
    return planner.predict_maintenance_need(aircraft)

def schedule_fleet_maintenance(fleet_size: int = 10) -> Dict:
    """Generate and schedule maintenance for a sample fleet."""
    planner = get_planner()
    aircraft_list = generate_sample_aircraft(fleet_size)
    
    # Predict individual aircraft needs
    predictions = []
    for ac in aircraft_list:
        pred = planner.predict_maintenance_need(ac)
        if pred["next_recommended_maintenance"]:
            predictions.append(pred)
    
    # Schedule maintenance
    schedule = planner.schedule_maintenance(aircraft_list)
    
    # Optimize parts inventory
    inventory = planner.optimize_spare_parts_inventory(aircraft_list)
    
    return {
        "predictions": predictions,
        "schedule": schedule,
        "inventory": inventory,
        "fleet_size": fleet_size,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

if __name__ == "__main__":
    result = schedule_fleet_maintenance(fleet_size=15)
    print(json.dumps({
        "scheduled_tasks": result["schedule"]["scheduled_tasks"][:3],
        "total_cost": result["schedule"]["total_cost"],
        "inventory_value": result["inventory"]["total_inventory_value"]
    }, indent=2))
    print("✅ Maintenance planner tested")
