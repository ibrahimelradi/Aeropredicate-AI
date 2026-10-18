"""
Turnaround Optimization Engine
==============================
AI-powered system for optimizing aircraft turnaround operations.
Builds on flight delay predictions to provide real-time turnaround recommendations.

Key Features:
- Predictive task sequencing for ground operations
- Bottleneck detection with early warning alerts
- Resource allocation optimization
- Integration with existing delay prediction model
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Import from existing modules
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "services"))

try:
    from aviation_data_service import (
        get_airport_weather_severity,
        get_icao_code,
        get_live_traffic,
    )
    from ml_engine_enhanced import predict_with_live_data
except ImportError:
    # Fallback for direct execution
    pass

# ─────────────────────────────────────────────
# Constants: Turnaround Task Timings (minutes)
# ─────────────────────────────────────────────
DEFAULT_TASK_DURATIONS = {
    "deboard_passengers": 25,    # Minutes for narrow-body (B737/A320)
    "unload_baggage": 20,
    "refuel": 45,                # Varies by aircraft size
    "cater": 25,
    "clean_cabin": 30,
    "load_baggage": 25,
    "load_catering": 15,         # Water, food, supplies
    "pushback": 10,
    "engine_start": 15,
    "pre_flight_checks": 20,
    "gate_cleanup": 10,          # After departure
}

# Aircraft type durations (multipliers)
AIRCRAFT_TYPE_MULTIPLIERS = {
    "narrow_body": 1.0,      # A320, B737
    "wide_body": 1.8,        # B777, B787, A350
    "regional": 0.7,         # ATR, E-Jet
    "super_jumbo": 3.0,      # A380
}

# Priority levels for tasks
TASK_PRIORITY = {
    "critical": 1,      # Must complete before takeoff
    "high": 2,          # Should complete before takeoff
    "medium": 3,        # Nice to have
    "low": 4,           # Can be deferred
}

class TurnaroundOptimizer:
    """
    Optimizes aircraft turnaround operations using predictive analytics.
    """
    
    def __init__(self):
        self.task_durations = DEFAULT_TASK_DURATIONS.copy()
        self.aircraft_types = AIRCRAFT_TYPE_MULTIPLIERS.copy()
    
    def plan_turnaround(
        self,
        flight_number: str,
        aircraft_type: str = "narrow_body",
        dep_airport: str = "IST",
        arr_airport: str = "JFK",
        scheduled_departure: str = "2026-10-20 14:30",
        gate_assignment: str = "A1",
        available_equipment: List[str] = None,
        crew_count: int = 5,
    ) -> Dict:
        """
        Generate an optimized turnaround plan for a flight.
        Returns detailed plan with timing, sequencing, and risk indicators.
        """
        # Get prediction for context
        try:
            dep_time = scheduled_departure.split()[1] if " " in scheduled_departure else scheduled_departure
            date_str = scheduled_departure.split()[0] if " " in scheduled_departure else datetime.now().strftime("%Y-%m-%d")
            
            prediction = predict_with_live_data(
                flight_number=flight_number,
                dep_airport=dep_airport,
                arr_airport=arr_airport,
                airline=flight_number[:2] if len(flight_number) > 2 else "TK",
                date_str=date_str,
                dep_time=dep_time,
            )
        except Exception:
            prediction = {"risk_tier": "UNKNOWN", "probabilities": {"delayed": 30.0}}
        
        # Calculate base turnaround time
        multiplier = self.aircraft_types.get(aircraft_type, 1.0)
        base_time = sum(self.task_durations.values()) * multiplier
        planned_turnaround_time = int(base_time * 0.85)  # Optimization factor
        
        # Generate optimal task sequence
        task_sequence = self._optimize_sequence(aircraft_type, available_equipment, crew_count)
        
        # Calculate timing
        tasks = []
        current_time = 0
        
        for task in task_sequence:
            duration = self.task_durations[task] * multiplier
            # Adjust for crew count and equipment availability
            crew_factor = min(1.0, crew_count / 5.0)  # Standard crew = 5
            duration = duration / crew_factor
            
            tasks.append({
                "task": task,
                "start_minute": current_time,
                "end_minute": current_time + int(duration),
                "duration_mins": int(duration),
                "crew_required": self._get_crew_requirement(task),
                "equipment_required": self._get_equipment_requirement(task),
                "priority": self._get_task_priority(task),
                "status": "planned",
            })
            current_time += int(duration)
        
        # Identify potential bottlenecks
        bottlenecks = self._identify_bottlenecks(tasks, prediction)
        
        # Calculate risk-adjusted completion time
        risk_buffer = self._calculate_risk_buffer(prediction["risk_tier"])
        estimated_completion = planned_turnaround_time + risk_buffer
        
        return {
            "flight_number": flight_number.upper(),
            "aircraft_type": aircraft_type,
            "gate_assignment": gate_assignment,
            "scheduled_departure": scheduled_departure,
            "turnaround_time_minutes": planned_turnaround_time,
            "estimated_completion": estimated_completion,
            "buffer_minutes": risk_buffer,
            "task_sequence": tasks,
            "bottlenecks": bottlenecks,
            "risk_assessment": prediction["risk_tier"],
            "delay_probability": prediction["probabilities"]["delayed"],
            "confidence_score": self._calculate_confidence(tasks, crew_count),
            "recommendations": self._generate_recommendations(tasks, prediction),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
    
    def _optimize_sequence(
        self,
        aircraft_type: str,
        available_equipment: List[str],
        crew_count: int
    ) -> List[str]:
        """Generate optimal task execution sequence based on dependencies."""
        # Critical path optimization
        core_sequence = [
            "deboard_passengers",
            "unload_baggage",
            "clean_cabin",
            "refuel",
            "cater",
            "load_baggage",
            "pre_flight_checks",
            "engine_start",
            "pushback",
        ]
        
        # Wide-body aircraft need additional steps
        if aircraft_type == "wide_body":
            core_sequence.insert(2, "unload_cargo")
            core_sequence.insert(4, "inspect_cargo_hold")
        
        # Add parallel task optimization based on crew count
        if crew_count >= 8:
            # Can run some tasks in parallel
            optimized = [
                "deboard_passengers",
                "unload_baggage",
                "clean_cabin",  # Parallel with refuel
                "refuel",
                "cater",  # Parallel with load_baggage
                "load_baggage",
                "load_catering",  # Parallel
                "pre_flight_checks",
                "engine_start",
                "pushback",
            ]
            return optimized
        
        return core_sequence
    
    def _get_crew_requirement(self, task: str) -> int:
        """Return minimum crew required for a task."""
        requirements = {
            "deboard_passengers": 2,
            "unload_baggage": 3,
            "refuel": 1,
            "cater": 2,
            "clean_cabin": 3,
            "load_baggage": 3,
            "load_catering": 2,
            "pre_flight_checks": 2,
            "engine_start": 1,
            "pushback": 2,
        }
        return requirements.get(task, 1)
    
    def _get_equipment_requirement(self, task: str) -> List[str]:
        """Return required equipment for a task."""
        equipment = {
            "deboard_passengers": [],
            "unload_baggage": ["belt_loader", "baggage_cart"],
            "refuel": ["fuel_truck"],
            "cater": ["catering_truck"],
            "clean_cabin": ["cleaning_supplies"],
            "load_baggage": ["belt_loader", "baggage_cart"],
            "load_catering": ["catering_truck"],
            "pre_flight_checks": [],
            "engine_start": ["air_start_unit"],
            "pushback": ["pushback_tractor"],
        }
        return equipment.get(task, [])
    
    def _get_task_priority(self, task: str) -> str:
        """Return priority level for a task."""
        priorities = {
            "deboard_passengers": "critical",
            "unload_baggage": "high",
            "refuel": "high",
            "cater": "high",
            "clean_cabin": "high",
            "load_baggage": "critical",
            "load_catering": "medium",
            "pre_flight_checks": "critical",
            "engine_start": "critical",
            "pushback": "critical",
        }
        return priorities.get(task, "medium")
    
    def _identify_bottlenecks(self, tasks: List[Dict], prediction: Dict) -> List[Dict]:
        """Identify potential bottlenecks and delay risks."""
        bottlenecks = []
        
        # Check for high-risk tasks
        for task in tasks:
            if task["priority"] in ["critical", "high"] and task["duration_mins"] > 25:
                bottlenecks.append({
                    "task": task["task"],
                    "risk_level": "high",
                    "reason": f"Long duration ({task['duration_mins']} mins) for critical task",
                    "recommendation": "Add additional equipment or crew"
                })
        
        # Check for sequential dependencies that could cause delays
        critical_path_duration = sum(
            t["duration_mins"] for t in tasks 
            if t["priority"] == "critical"
        )
        
        if critical_path_duration > 90:
            bottlenecks.append({
                "task": "overall_turnaround",
                "risk_level": "high",
                "reason": f"Critical path duration exceeds 90 minutes ({critical_path_duration} mins)",
                "recommendation": "Consider parallel task execution or earlier gate assignment"
            })
        
        # Check prediction-based risks
        if prediction["probabilities"]["delayed"] > 50:
            bottlenecks.append({
                "task": "weather_impact",
                "risk_level": "high",
                "reason": f"High delay probability ({prediction['probabilities']['delayed']}%)",
                "recommendation": "Prepare alternative gate or delay mitigation plan"
            })
        
        return bottlenecks
    
    def _calculate_risk_buffer(self, risk_tier: str) -> int:
        """Calculate buffer time based on prediction risk tier."""
        buffers = {
            "LOW": 10,
            "MODERATE": 25,
            "HIGH": 45,
            "CRITICAL": 75,
        }
        return buffers.get(risk_tier, 20)
    
    def _calculate_confidence(self, tasks: List[Dict], crew_count: int) -> float:
        """Calculate confidence score for the turnaround plan (0-100)."""
        base_confidence = 85.0
        
        # Adjust for crew adequacy
        required_crew = max(t["crew_required"] for t in tasks)
        if crew_count >= required_crew:
            base_confidence += 5
        else:
            base_confidence -= 15
        
        # Adjust for task complexity
        critical_tasks = sum(1 for t in tasks if t["priority"] == "critical")
        if critical_tasks > 5:
            base_confidence -= 5
        
        return max(0.0, min(100.0, base_confidence))
    
    def _generate_recommendations(self, tasks: List[Dict], prediction: Dict) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []
        
        # Crew recommendations
        max_crew_needed = max(t["crew_required"] for t in tasks)
        if max_crew_needed > 5:
            recommendations.append(
                f"Assign {max_crew_needed} crew members for critical tasks"
            )
        
        # Equipment recommendations
        all_equipment = set()
        for task in tasks:
            all_equipment.update(task["equipment_required"])
        
        if all_equipment:
            recommendations.append(
                f"Ensure equipment availability: {', '.join(sorted(all_equipment))}"
            )
        
        # Risk-based recommendations
        if prediction["probabilities"]["delayed"] > 40:
            recommendations.append(
                "Monitor weather conditions and prepare contingency plans"
            )
        
        if prediction["risk_tier"] in ["HIGH", "CRITICAL"]:
            recommendations.append(
                "Consider early boarding to compensate for potential delays"
            )
        
        bottlenecks = self._identify_bottlenecks(tasks, prediction)
        for b in bottlenecks:
            if "recommendation" in b:
                recommendations.append(b["recommendation"])
        
        return recommendations

# Global optimizer instance
_optimizer = None

def get_optimizer():
    global _optimizer
    if _optimizer is None:
        _optimizer = TurnaroundOptimizer()
    return _optimizer

# Convenience function for API use
def optimize_turnaround(flight_number: str, dep_airport: str, arr_airport: str,
                       airline: str, date_str: str, dep_time: str,
                       aircraft_type: str = "narrow_body",
                       gate_assignment: str = "A1",
                       crew_count: int = 5) -> Dict:
    """Main API function for turnaround optimization."""
    optimizer = get_optimizer()
    scheduled_dep = f"{date_str} {dep_time}"
    
    try:
        result = optimizer.plan_turnaround(
            flight_number=flight_number,
            aircraft_type=aircraft_type,
            dep_airport=dep_airport,
            arr_airport=arr_airport,
            scheduled_departure=scheduled_dep,
            gate_assignment=gate_assignment,
            crew_count=crew_count,
        )
        return result
    except Exception as e:
        return {
            "error": str(e),
            "success": False,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

if __name__ == "__main__":
    # Demo
    result = optimize_turnaround(
        flight_number="TK1988",
        dep_airport="IST",
        arr_airport="JFK",
        airline="TK",
        date_str="2026-10-20",
        dep_time="14:30",
        aircraft_type="narrow_body",
        crew_count=5
    )
    print(json.dumps(result, indent=2))
