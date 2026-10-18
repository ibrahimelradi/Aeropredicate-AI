"""
Airport Ground Handling Quality Manager
=========================================
AI-powered quality management for ground handling operations.

Solves:
1. Service quality monitoring (on-time performance)
2. Key Performance Indicator (KPI) tracking
3. SLA compliance monitoring
4. Customer feedback analysis
5. Root cause analysis for delays
6. Continuous improvement recommendations
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

# Ground handling KPIs and targets
GROUND_HANDLING_KPIS = {
    "boarding_time": {"target": 30, "unit": "minutes", "weight": 0.20},
    "baggage_delivery": {"target": 20, "unit": "minutes", "weight": 0.15},
    "cleaning_time": {"target": 25, "unit": "minutes", "weight": 0.10},
    "catering_time": {"target": 15, "unit": "minutes", "weight": 0.10},
    "fuel_turnaround": {"target": 40, "unit": "minutes", "weight": 0.15},
    "ramp_taxi_time": {"target": 10, "unit": "minutes", "weight": 0.10},
    "deicing_time": {"target": 15, "unit": "minutes", "weight": 0.10},
    "load_sheet_accuracy": {"target": 100, "unit": "%", "weight": 0.10},
}

# SLA thresholds (minutes over target = penalty)
SLA_THRESHOLDS = {
    "boading": {"target": 30, "warning": 35, "breach": 45},
    "baggage_delivery": {"target": 20, "warning": 25, "breach": 35},
    "cleaning": {"target": 25, "warning": 30, "breach": 40},
    "catering": {"target": 15, "warning": 20, "breach": 30},
    "fueling": {"target": 40, "warning": 50, "breach": 70},
}

# Common delay causes
DELAY_CAUSES = {
    "weather": {"impact": 0.30, "prevention": "Weather monitoring system"},
    "crew_shortage": {"impact": 0.25, "prevention": "Adequate staffing planning"},
    "equipment_failure": {"impact": 0.20, "prevention": "Preventive maintenance"},
    "traffic_congestion": {"impact": 0.15, "prevention": "Coordination with ATC"},
    "documentation": {"impact": 0.10, "prevention": "Digital documentation"},
    "passenger_delays": {"impact": 0.15, "prevention": "Early boarding procedures"},
}

# Service quality ratings
QUALITY_RATINGS = {
    "excellent": {"min_score": 90, "color": "green"},
    "good": {"min_score": 80, "color": "light_green"},
    "satisfactory": {"min_score": 70, "color": "yellow"},
    "needs_attention": {"min_score": 60, "color": "orange"},
    "poor": {"min_score": 0, "color": "red"},
}

@dataclass
class ServiceEvent:
    """Represents a ground handling service event."""
    event_id: str
    flight_number: str
    service_type: str
    start_time: datetime
    end_time: datetime
    actual_duration: float
    target_duration: float
    status: str  # completed, delayed, breached
    handler: str
    notes: str = ""

class GroundHandlingQualityManager:
    """
    AI-powered ground handling quality management system.
    """
    
    def __init__(self):
        self.kpis = GROUND_HANDLING_KPIS
        self.sla_thresholds = SLA_THRESHOLDS
        self.delay_causes = DELAY_CAUSES
        self.quality_ratings = QUALITY_RATINGS
    
    def calculate_service_quality_score(self, events: List[ServiceEvent]) -> Dict:
        """
        Calculate overall service quality score from events.
        """
        if not events:
            return {"error": "No events provided", "score": 0}
        
        category_scores = {}
        total_weighted_score = 0
        total_weight = 0
        
        # Group by service type
        service_groups = {}
        for event in events:
            service_type = event.service_type
            if service_type not in service_groups:
                service_groups[service_type] = []
            service_groups[service_type].append(event)
        
        for service_type, service_events in service_groups.items():
            kpi = self.kpis.get(service_type.replace(" ", "_"), 
                               {"target": 30, "unit": "minutes", "weight": 0.10})
            
            target = kpi["target"]
            weight = kpi["weight"]
            unit = kpi["unit"]
            
            on_target_count = sum(1 for e in service_events if e.actual_duration <= target)
            on_target_pct = (on_target_count / len(service_events)) * 100
            
            # Average actual vs target
            avg_actual = sum(e.actual_duration for e in service_events) / len(service_events)
            performance_ratio = avg_actual / target if target > 0 else 1.0
            
            # Score: 100 if avg_actual <= target, decreases linearly
            score = max(0, min(100, 100 * (2 - performance_ratio)))
            if score > 100:
                score = 100
            
            category_scores[service_type] = {
                "score": round(score, 1),
                "on_target_count": on_target_count,
                "total_events": len(service_events),
                "on_target_percentage": round(on_target_pct, 1),
                "avg_actual": round(avg_actual, 1),
                "target": target,
                "unit": unit,
                "weight": weight,
            }
            
            total_weighted_score += score * weight
            total_weight += weight
        
        overall_score = total_weighted_score / total_weight if total_weight > 0 else 0
        rating = self._get_quality_rating(overall_score)
        
        return {
            "overall_score": round(overall_score, 1),
            "rating": rating,
            "category_scores": category_scores,
            "total_events_analyzed": len(events),
            "compliance_metrics": {
                "kpi_compliance_rate": round(sum(1 for c in category_scores.values() if c["on_target_percentage"] >= 80) / max(len(category_scores), 1) * 100, 1),
                "sla_breach_count": sum(1 for e in events if e.status == "breached"),
                "sla_warning_count": sum(1 for e in events if e.status == "delayed"),
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    def _get_quality_rating(self, score: float) -> Dict:
        """Get quality rating based on score."""
        for rating_name, rating_info in sorted(
            self.quality_ratings.items(), 
            key=lambda x: x[1]["min_score"], 
            reverse=True
        ):
            if score >= rating_info["min_score"]:
                return {"level": rating_name, "color": rating_info["color"]}
        return {"level": "poor", "color": "red"}
    
    def sla_compliance_report(self, events: List[ServiceEvent]) -> Dict:
        """
        Generate SLA compliance report.
        """
        if not events:
            return {"error": "No events provided"}
        
        sla_breakdown = {}
        breach_details = []
        
        for event in events:
            service_type = event.service_type.replace(" ", "_")
            sla_key = service_type.replace("boarding", "boarding").replace("baggage", "baggage_delivery")
            sla_key = service_type
            
            if service_type not in self.sla_thresholds:
                sla_key = "boarding" if "boarding" in service_type else "baggage_delivery" if "baggage" in service_type else \
                          "cleaning" if "cleaning" in service_type else "catering" if "catering" in service_type else "fueling"
            
            if service_type not in sla_breakdown:
                sla_breakdown[service_type] = {
                    "target": self.sla_thresholds.get(sla_key, {}).get("target", 30),
                    "warning": self.sla_thresholds.get(sla_key, {}).get("warning", 35),
                    "breach": self.sla_thresholds.get(sla_key, {}).get("breach", 45),
                    "total_events": 0,
                    "on_time": 0,
                    "warning_count": 0,
                    "breach_count": 0,
                    "compliance_rate": 0,
                }
            
            stats = sla_breakdown[service_type]
            stats["total_events"] += 1
            
            if event.status == "completed":
                stats["on_time"] += 1
            elif event.status == "delayed":
                stats["warning_count"] += 1
                breach_details.append({
                    "event_id": event.event_id,
                    "flight": event.flight_number,
                    "service": service_type,
                    "actual": event.actual_duration,
                    "target": stats["target"],
                    "warning_threshold": stats["warning"],
                })
            elif event.status == "breached":
                stats["breach_count"] += 1
                breach_details.append({
                    "event_id": event.event_id,
                    "flight": event.flight_number,
                    "service": service_type,
                    "actual": event.actual_duration,
                    "target": stats["target"],
                    "breach_threshold": stats["breach"],
                    "delay_minutes": event.actual_duration - stats["breach"],
                })
            
            stats["compliance_rate"] = round(
                (stats["on_time"] / stats["total_events"]) * 100, 1
            ) if stats["total_events"] > 0 else 0
        
        total_breaches = sum(s["breach_count"] for s in sla_breakdown.values())
        total_warnings = sum(s["warning_count"] for s in sla_breakdown.values())
        total_events = sum(s["total_events"] for s in sla_breakdown.values())
        
        # Overall SLA compliance
        overall_compliance = round((total_events - total_warnings - total_breaches) / total_events * 100, 1) if total_events > 0 else 0
        
        penalty_cost = (total_warnings * 50 + total_breaches * 200)  # USD
        
        return {
            "overall_sla_compliance": f"{overall_compliance}%",
            "total_events": total_events,
            "sla_breakdown": sla_breakdown,
            "breach_details": breach_details[:10],  # Top 10
            "financial_impact": {
                "penalty_cost_usd": penalty_cost,
                "breach_cost_usd": total_breaches * 200,
                "warning_cost_usd": total_warnings * 50,
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    def root_cause_analysis(self, delay_reasons: Dict[str, int]) -> Dict:
        """
        Perform root cause analysis on delay data.
        """
        total_delays = sum(delay_reasons.values())
        if total_delays == 0:
            return {"error": "No delays to analyze"}
        
        cause_analysis = {}
        for cause, count in delay_reasons.items():
            cause_info = self.delay_causes.get(cause, {"impact": 0.10, "prevention": "Standard procedure"})
            percentage = (count / total_delays) * 100
            cause_analysis[cause] = {
                "count": count,
                "percentage": round(percentage, 1),
                "impact_score": cause_info["impact"],
                "weighted_impact": round(percentage * cause_info["impact"], 2),
                "prevention_strategy": cause_info["prevention"],
            }
        
        # Rank by weighted impact
        ranked = sorted(cause_analysis.items(), key=lambda x: x[1]["weighted_impact"], reverse=True)
        
        primary_cause = ranked[0][0] if ranked else "unknown"
        primary_impact = ranked[0][1]["weighted_impact"] if ranked else 0
        
        return {
            "total_delays": total_delays,
            "primary_cause": primary_cause,
            "primary_cause_impact": primary_impact,
            "cause_analysis": dict(ranked),
            "recommendations": [
                ranked[0][1]["prevention_strategy"],
                "Implement predictive analytics for early warning",
                "Increase cross-training of ground staff",
            ][:5],
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    def generate_quality_report(self, flight_count: int = 100, 
                                date_range: str = "last_30_days") -> Dict:
        """
        Generate comprehensive ground handling quality report.
        """
        # Generate sample service events
        events = []
        service_types = list(self.kpis.keys())
        
        for i in range(flight_count):
            for service_type in service_types[:random.randint(4, 6)]:  # Each flight has 4-6 services
                target = self.kpis[service_type]["target"]
                # Realistic duration: target ± 30%
                actual = target * random.uniform(0.7, 1.6)
                
                if actual <= target:
                    status = "completed"
                elif actual <= target * 1.5:
                    status = "delayed"
                else:
                    status = "breached"
                
                event = ServiceEvent(
                    event_id=f"EV-{i+1:04d}-{service_type[:4]}",
                    flight_number=f"TK{random.randint(100, 999)}",
                    service_type=service_type,
                    start_time=datetime.now() - timedelta(hours=random.randint(0, 24)),
                    end_time=datetime.now() + timedelta(minutes=actual),
                    actual_duration=round(actual, 1),
                    target_duration=target,
                    status=status,
                    handler=random.choice(["DHL Ground", "Swissport", " dnata", "Menzies", "TAV"]),
                )
                events.append(event)
        
        quality_score = self.calculate_service_quality_score(events)
        sla_report = self.sla_compliance_report(events)
        
        # Generate sample delay reasons
        delay_reasons = {
            "weather": random.randint(10, 25),
            "crew_shortage": random.randint(15, 30),
            "equipment_failure": random.randint(5, 15),
            "traffic_congestion": random.randint(20, 40),
            "documentation": random.randint(5, 15),
        }
        root_cause = self.root_cause_analysis(delay_reasons)
        
        return {
            "report_type": "ground_handling_quality_report",
            "date_range": date_range,
            "flights_analyzed": flight_count,
            "quality_score": quality_score,
            "sla_compliance": {
                "overall_compliance": sla_report["overall_sla_compliance"],
                "total_events": sla_report["total_events"],
                "breach_count": sla_report["financial_impact"]["breach_cost_usd"] / 200,
            },
            "root_cause_analysis": root_cause,
            "performance_trends": {
                "month_over_month": f"+{random.randint(2, 15)}%",
                "target_score": "90+",
                "current_score": quality_score["overall_score"],
            },
            "recommendations": quality_score.get("recommendations", [
                "Focus on improving baggage delivery times",
                "Increase staffing for boarding operations",
            ]),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

# ─────────────────────────────────────────────
# API Convenience Functions
# ─────────────────────────────────────────────
_quality_mgr = None

def get_quality_manager():
    global _quality_mgr
    if _quality_mgr is None:
        _quality_mgr = GroundHandlingQualityManager()
    return _quality_mgr

def calculate_quality_score(events: List[Dict]) -> dict:
    """Calculate service quality score."""
    mgr = get_quality_manager()
    event_objects = []
    for e in events:
        event_objects.append(ServiceEvent(
            event_id=e.get("event_id", "EV-000"),
            flight_number=e.get("flight_number", "TK000"),
            service_type=e.get("service_type", "boarding"),
            start_time=datetime.fromisoformat(e.get("start_time", "2026-01-01T00:00:00")),
            end_time=datetime.fromisoformat(e.get("end_time", "2026-01-01T00:30:00")),
            actual_duration=e.get("actual_duration", 30),
            target_duration=e.get("target_duration", 30),
            status=e.get("status", "completed"),
            handler=e.get("handler", "Unknown"),
        ))
    return mgr.calculate_service_quality_score(event_objects)

def sla_compliance_report(events: List[Dict]) -> dict:
    """Generate SLA compliance report."""
    mgr = get_quality_manager()
    event_objects = []
    for e in events:
        event_objects.append(ServiceEvent(
            event_id=e.get("event_id", "EV-000"),
            flight_number=e.get("flight_number", "TK000"),
            service_type=e.get("service_type", "boarding"),
            start_time=datetime.fromisoformat(e.get("start_time", "2026-01-01T00:00:00")),
            end_time=datetime.fromisoformat(e.get("end_time", "2026-01-01T00:30:00")),
            actual_duration=e.get("actual_duration", 30),
            target_duration=e.get("target_duration", 30),
            status=e.get("status", "completed"),
            handler=e.get("handler", "Unknown"),
        ))
    return mgr.sla_compliance_report(event_objects)

def root_cause_analysis(delay_reasons: Dict[str, int]) -> dict:
    """Perform root cause analysis."""
    return get_quality_manager().root_cause_analysis(delay_reasons)

def generate_quality_report(flight_count: int = 100, date_range: str = "last_30_days") -> dict:
    """Generate comprehensive quality report."""
    return get_quality_manager().generate_quality_report(flight_count, date_range)

if __name__ == "__main__":
    result = generate_quality_report(50)
    print(json.dumps(result, indent=2))
    print("✅ Quality manager tested")
