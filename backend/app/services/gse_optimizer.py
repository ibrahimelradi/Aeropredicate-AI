"""
Ground Support Equipment (GSE) Optimization System
===================================================
Real-time tracking and optimization for airport ground equipment.
Addresses the $600K-$1.2M annual waste per major airport from idle GSE.

Key Features:
- Real-time location tracking simulation
- Utilization analytics and idle time alerts
- Predictive maintenance scheduling
- Cost optimization recommendations
"""

import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, field, asdict

# ─────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────
GSE_TYPES = {
    "belt_loader": {"name": "Belt Loader", "hourly_cost": 120, "maintenance_interval": 72},
    "baggage_cart": {"name": "Baggage Cart", "hourly_cost": 35, "maintenance_interval": 168},
    "fuel_truck": {"name": "Fuel Truck", "hourly_cost": 180, "maintenance_interval": 48},
    "catering_truck": {"name": "Catering Truck", "hourly_cost": 140, "maintenance_interval": 96},
    "pushback_tractor": {"name": "Pushback Tractor", "hourly_cost": 200, "maintenance_interval": 60},
    "water_truck": {"name": "Water Truck", "hourly_cost": 90, "maintenance_interval": 120},
    "lavatory_truck": {"name": "Lavatory Truck", "hourly_cost": 100, "maintenance_interval": 84},
    "air_start_unit": {"name": "Air Start Unit", "hourly_cost": 150, "maintenance_interval": 56},
    "ground_power_unit": {"name": "Ground Power Unit", "hourly_cost": 95, "maintenance_interval": 100},
}

@dataclass
class GSERecord:
    """Represents a single GSE asset."""
    id: str
    type: str
    name: str
    location: str
    status: str  # available, in_use, maintenance, idle
    last_maintenance: datetime
    hours_operated: float = 0.0
    hours_idle: float = 0.0
    utilization_rate: float = 0.0
    cost_per_hour: float = 0.0
    maintenance_hours: float = 0.0
    fuel_consumed: float = 0.0  # liters
    last_checkout: Optional[datetime] = None
    next_maintenance: Optional[datetime] = None

class GSOptimizer:
    """
    Optimizes ground support equipment fleet management.
    """
    
    def __init__(self, fleet_size: int = 50):
        self.fleet_size = fleet_size
        self.gse_fleet: List[GSERecord] = self._initialize_fleet()
    
    def _initialize_fleet(self) -> List[GSERecord]:
        """Initialize a simulated GSE fleet."""
        fleet = []
        gse_types = list(GSE_TYPES.keys())
        
        for i in range(self.fleet_size):
            gse_type = random.choice(gse_types)
            type_info = GSE_TYPES[gse_type]
            
            locations = ["Gate A", "Gate B", "Gate C", "Apron 1", "Apron 2", 
                        "Maintenance Bay", "Hangar", "Parking Area"]
            
            record = GSERecord(
                id=f"GSE-{i+1:04d}",
                type=gse_type,
                name=type_info["name"],
                location=random.choice(locations),
                status=random.choice(["available", "idle", "in_use", "maintenance"]),
                last_maintenance=datetime.now() - timedelta(days=random.randint(1, 30)),
                hours_operated=random.uniform(100, 500),
                hours_idle=random.uniform(50, 200),
                utilization_rate=round(random.uniform(0.45, 0.85), 2),
                cost_per_hour=type_info["hourly_cost"],
                maintenance_hours=random.uniform(5, 50),
                fuel_consumed=round(random.uniform(100, 1500), 1),
            )
            
            # Calculate next maintenance
            hours_until_maintenance = type_info["maintenance_interval"] - record.hours_operated % type_info["maintenance_interval"]
            record.next_maintenance = datetime.now() + timedelta(hours=hours_until_maintenance)
            
            fleet.append(record)
        
        return fleet
    
    def get_fleet_status(self) -> Dict:
        """Return current fleet status overview."""
        total = len(self.gse_fleet)
        status_counts = {"available": 0, "in_use": 0, "maintenance": 0, "idle": 0}
        
        for gse in self.gse_fleet:
            if gse.status in status_counts:
                status_counts[gse.status] += 1
        
        total_utilization = sum(g.utilization_rate for g in self.gse_fleet) / total
        total_cost = sum(g.cost_per_hour * g.hours_operated for g in self.gse_fleet)
        idle_cost = sum(g.cost_per_hour * g.hours_idle for g in self.gse_fleet)
        
        return {
            "fleet_size": total,
            "status_breakdown": status_counts,
            "overall_utilization_rate": round(total_utilization * 100, 1),
            "total_operational_cost": round(total_cost, 2),
            "idle_cost_loss": round(idle_cost, 2),
            "idle_cost_percentage": round((idle_cost / total_cost * 100) if total_cost > 0 else 0, 1),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    def identify_idle_equipment(self, threshold_minutes: int = 60) -> List[Dict]:
        """Find equipment that has been idle beyond threshold."""
        idle_equipment = []
        threshold = datetime.now() - timedelta(minutes=threshold_minutes)
        
        for gse in self.gse_fleet:
            if (gse.status == "idle" and 
                (gse.last_checkout is None or gse.last_checkout < threshold)):
                idle_equipment.append({
                    "id": gse.id,
                    "type": gse.type,
                    "name": gse.name,
                    "location": gse.location,
                    "idle_since": gse.last_checkout.isoformat() if gse.last_checkout else "unknown",
                    "hourly_cost": gse.cost_per_hour,
                    "estimated_loss": round(gse.cost_per_hour * (threshold_minutes / 60), 2)
                })
        
        return sorted(idle_equipment, key=lambda x: x["estimated_loss"], reverse=True)
    
    def predict_maintenance_needs(self) -> List[Dict]:
        """Predict upcoming maintenance needs using equipment data."""
        maintenance_alerts = []
        
        for gse in self.gse_fleet:
            type_info = GSE_TYPES[gse.type]
            hours_since_maintenance = type_info["maintenance_interval"] - (
                type_info["maintenance_interval"] - gse.hours_operated % type_info["maintenance_interval"]
            )
            
            # Alert if within 20% of maintenance interval
            if hours_since_maintenance > type_info["maintenance_interval"] * 0.8:
                risk_level = "high" if hours_since_maintenance >= type_info["maintenance_interval"] else "medium"
                maintenance_alerts.append({
                    "id": gse.id,
                    "type": gse.type,
                    "name": gse.name,
                    "location": gse.location,
                    "hours_operated": round(gse.hours_operated, 1),
                    "maintenance_interval": type_info["maintenance_interval"],
                    "hours_remaining": round(type_info["maintenance_interval"] - hours_since_maintenance, 1),
                    "risk_level": risk_level,
                    "recommended_action": "Schedule maintenance immediately" if risk_level == "high" else "Plan maintenance within 48 hours",
                    "estimated_downtime_cost": round(gse.cost_per_hour * 4, 2)
                })
        
        return sorted(maintenance_alerts, key=lambda x: x["hours_remaining"])
    
    def optimize_allocation(self, flight_schedule: List[Dict]) -> Dict:
        """
        Optimize GSE allocation based on upcoming flight schedule.
        
        Args:
            flight_schedule: List of flights with required equipment types
        
        Returns:
            Optimized allocation plan
        """
        allocation_plan = {
            "total_flights": len(flight_schedule),
            "allocated_equipment": {},
            "unavailable_equipment": [],
            "recommendations": [],
            "cost_savings_potential": 0.0,
        }
        
        # Group GSE by type
        gse_by_type: Dict[str, List[GSERecord]] = {}
        for gse in self.gse_fleet:
            if gse.type not in gse_by_type:
                gse_by_type[gse.type] = []
            gse_by_type[gse.type].append(gse)
        
        # Assign equipment to flights
        for flight in flight_schedule:
            required_equipment = flight.get("equipment", [])
            flight_id = flight.get("flight_id", "unknown")
            
            flight_allocation = []
            for eq_type in required_equipment:
                if eq_type in gse_by_type:
                    available = [g for g in gse_by_type[eq_type] if g.status == "available"]
                    idle_units = [g for g in gse_by_type[eq_type] if g.status == "idle"]
                    
                    if available:
                        selected = available[0]
                        flight_allocation.append({
                            "equipment_id": selected.id,
                            "type": eq_type,
                            "name": selected.name,
                            "location": selected.location,
                            "status": "assigned"
                        })
                        selected.status = "in_use"
                        selected.last_checkout = datetime.now()
                    elif idle_units:
                        # Reactivate idle equipment
                        selected = idle_units[0]
                        flight_allocation.append({
                            "equipment_id": selected.id,
                            "type": eq_type,
                            "name": selected.name,
                            "location": selected.location,
                            "status": "reactivated"
                        })
                        selected.status = "in_use"
                        selected.last_checkout = datetime.now()
                        allocation_plan["recommendations"].append(
                            f"Reactivate idle {selected.name} (ID: {selected.id}) for Flight {flight_id}"
                        )
                    else:
                        allocation_plan["unavailable_equipment"].append({
                            "flight_id": flight_id,
                            "equipment_type": eq_type,
                            "reason": "All units assigned or in maintenance"
                        })
                        allocation_plan["recommendations"].append(
                            f"No available {eq_type} for Flight {flight_id} - consider rental or schedule adjustment"
                        )
                else:
                    allocation_plan["unavailable_equipment"].append({
                        "flight_id": flight_id,
                        "equipment_type": eq_type,
                        "reason": "Equipment type not in fleet"
                    })
            
            allocation_plan["allocated_equipment"][flight_id] = flight_allocation
        
        # Calculate idle cost savings potential
        idle_equipment = self.identify_idle_equipment(threshold_minutes=30)
        cost_savings = sum(e["estimated_loss"] for e in idle_equipment)
        allocation_plan["cost_savings_potential"] = round(cost_savings * 0.7, 2)  # Estimated recovery
        
        return allocation_plan
    
    def generate_utilization_report(self) -> Dict:
        """Generate detailed utilization report for the fleet."""
        report = {
            "by_type": {},
            "location_analysis": {},
            "efficiency_metrics": {},
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        # By type analysis
        for gse_type, type_info in GSE_TYPES.items():
            type_gse = [g for g in self.gse_fleet if g.type == gse_type]
            if type_gse:
                avg_util = sum(g.utilization_rate for g in type_gse) / len(type_gse)
                total_hours = sum(g.hours_operated for g in type_gse)
                idle_hours = sum(g.hours_idle for g in type_gse)
                cost = sum(g.cost_per_hour * g.hours_operated for g in type_gse)
                
                report["by_type"][gse_type] = {
                    "name": type_info["name"],
                    "count": len(type_gse),
                    "avg_utilization": round(avg_util * 100, 1),
                    "total_operational_hours": round(total_hours, 1),
                    "total_idle_hours": round(idle_hours, 1),
                    "total_cost": round(cost, 2),
                    "cost_per_utilized_hour": round(cost / total_hours * (1/avg_util) if avg_util > 0 else 0, 2)
                }
        
        # Location analysis
        locations = set(g.location for g in self.gse_fleet)
        for loc in locations:
            loc_gse = [g for g in self.gse_fleet if g.location == loc]
            status_dist = {"available": 0, "in_use": 0, "maintenance": 0, "idle": 0}
            for g in loc_gse:
                if g.status in status_dist:
                    status_dist[g.status] += 1
            
            report["location_analysis"][loc] = {
                "total_equipment": len(loc_gse),
                "status_distribution": status_dist,
                "avg_utilization": round(sum(g.utilization_rate for g in loc_gse) / len(loc_gse) * 100, 1)
            }
        
        # Overall efficiency
        total_hours_op = sum(g.hours_operated for g in self.gse_fleet)
        total_hours_idle = sum(g.hours_idle for g in self.gse_fleet)
        total_cost = sum(g.cost_per_hour * g.hours_operated for g in self.gse_fleet)
        
        report["efficiency_metrics"] = {
            "total_operational_hours": round(total_hours_op, 1),
            "total_idle_hours": round(total_hours_idle, 1),
            "overall_efficiency_ratio": round(total_hours_op / (total_hours_op + total_hours_idle) * 100, 1) if (total_hours_op + total_hours_idle) > 0 else 0,
            "total_operational_cost": round(total_cost, 2),
            "estimated_waste_from_idle": round(sum(g.cost_per_hour * g.hours_idle for g in self.gse_fleet), 2)
        }
        
        return report

# Convenience functions for API use
def get_fleet_status() -> Dict:
    optimizer = GSOptimizer()
    return optimizer.get_fleet_status()

def get_idle_equipment(threshold_minutes: int = 60) -> Dict:
    optimizer = GSOptimizer()
    return {
        "idle_equipment": optimizer.identify_idle_equipment(threshold_minutes),
        "count": len(optimizer.identify_idle_equipment(threshold_minutes)),
        "potential_savings": round(sum(
            e["estimated_loss"] for e in optimizer.identify_idle_equipment(threshold_minutes)
        ), 2)
    }

def get_maintenance_alerts() -> Dict:
    optimizer = GSOptimizer()
    alerts = optimizer.predict_maintenance_needs()
    return {
        "alerts": alerts,
        "count": len(alerts),
        "high_risk_count": len([a for a in alerts if a["risk_level"] == "high"])
    }

def optimize_gse_allocation(flight_schedule: List[Dict]) -> Dict:
    optimizer = GSOptimizer()
    return optimizer.optimize_allocation(flight_schedule)

def get_utilization_report() -> Dict:
    optimizer = GSOptimizer()
    return optimizer.generate_utilization_report()

if __name__ == "__main__":
    # Demo
    print("=== GSE Fleet Status ===")
    print(json.dumps(get_fleet_status(), indent=2))
    
    print("\n=== Idle Equipment ===")
    print(json.dumps(get_idle_equipment(), indent=2))
    
    print("\n=== Maintenance Alerts ===")
    print(json.dumps(get_maintenance_alerts(), indent=2))
    
    print("\n=== Utilization Report ===")
    print(json.dumps(get_utilization_report(), indent=2))
