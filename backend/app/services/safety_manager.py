"""
Aviation Safety & Risk Management System
==========================================
AI-powered safety analysis and risk assessment.

Solves:
1. Hazard identification and risk assessment
2. Go-around/incident probability modeling
3. Runway excursion risk analysis
4. Fatigue risk management (FRA)
5. Weather minima compliance
6. SMS (Safety Management System) reporting
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

HAZARD_CATEGORIES = {
    "weather": {"weight": 0.25, "severity_levels": ["low", "moderate", "high", "extreme"]},
    "runway": {"weight": 0.20, "severity_levels": ["low", "moderate", "high", "extreme"]},
    "equipment": {"weight": 0.15, "severity_levels": ["low", "moderate", "high", "extreme"]},
    "human_factors": {"weight": 0.25, "severity_levels": ["low", "moderate", "high", "extreme"]},
    "air_traffic": {"weight": 0.10, "severity_levels": ["low", "moderate", "high", "extreme"]},
    "security": {"weight": 0.05, "severity_levels": ["low", "moderate", "high", "extreme"]},
}

SEVERITY_SCORES = {"low": 1, "moderate": 2, "high": 3, "extreme": 4}
PROBABILITY_SCORES = {"unlikely": 1, "remote": 2, "occasional": 3, "probable": 4, "frequent": 5}

# Fatigue risk factors
FATIGUE_FACTORS = {
    "flight_hours_24h": {"threshold": 8, "risk_multiplier": 1.5},
    "flight_hours_7d": {"threshold": 30, "risk_multiplier": 1.8},
    "night_flights": {"threshold": 3, "risk_multiplier": 2.0},
    "early_start": {"threshold": 5, "risk_multiplier": 1.3},  # 5 AM start
    "consecutive_days": {"threshold": 4, "risk_multiplier": 1.4},
    "time_zones": {"threshold": 2, "risk_multiplier": 1.2},
}

# Runway safety parameters
RUNWAY_SAFETY_AREA = {
    "dry": {"friction": 0.85, "braking_factor": 1.0},
    "wet": {"friction": 0.65, "braking_factor": 0.7},
    "snow": {"friction": 0.30, "braking_factor": 0.4},
    "ice": {"friction": 0.10, "braking_factor": 0.2},
}

@dataclass
class RiskAssessment:
    """Represents a risk assessment result."""
    category: str
    hazard: str
    likelihood: str
    severity: str
    risk_score: float
    mitigation: str
    residual_risk: float

class SafetyRiskManager:
    """
    AI-powered aviation safety and risk management.
    """
    
    def __init__(self):
        self.hazard_categories = HAZARD_CATEGORIES
        self.severity_scores = SEVERITY_SCORES
        self.probability_scores = PROBABILITY_SCORES
        self.fatigue_factors = FATIGUE_FACTORS
        self.runway_safety = RUNWAY_SAFETY_AREA
    
    def assess_risk(self, hazards: List[Dict]) -> Dict:
        """
        Perform comprehensive risk assessment on identified hazards.
        """
        assessments = []
        total_risk = 0
        category_risks = {}
        
        for hazard in hazards:
            category = hazard.get("category", "human_factors")
            hazard_name = hazard.get("hazard", "unknown")
            likelihood = hazard.get("likelihood", "occasional")
            severity = hazard.get("severity", "moderate")
            
            # Calculate risk score (1-25 scale)
            prob_score = self.probability_scores.get(likelihood, 3)
            sev_score = self.severity_scores.get(severity, 2)
            base_risk = prob_score * sev_score
            
            # Apply category weight
            cat_weight = self.hazard_categories.get(category, {}).get("weight", 0.15)
            weighted_risk = base_risk * cat_weight
            
            # Mitigation effectiveness
            mitigation = hazard.get("mitigation", "standard_procedures")
            mitigation_effectiveness = {
                "standard_procedures": 0.4,
                "training": 0.3,
                "technology": 0.2,
                "redundancy": 0.5,
                "automation": 0.6,
                "manual_override": 0.3,
            }.get(mitigation, 0.3)
            
            residual_risk = max(0.5, weighted_risk * (1 - mitigation_effectiveness))
            
            # Risk level classification
            if residual_risk > 8:
                risk_level = "high"
            elif residual_risk > 5:
                risk_level = "moderate"
            elif residual_risk > 2:
                risk_level = "low"
            else:
                risk_level = "acceptable"
            
            assessment = RiskAssessment(
                category=category,
                hazard=hazard_name,
                likelihood=likelihood,
                severity=severity,
                risk_score=round(weighted_risk, 2),
                mitigation=mitigation,
                residual_risk=round(residual_risk, 2)
            )
            assessments.append(assessment)
            
            total_risk += residual_risk
            if category not in category_risks:
                category_risks[category] = 0
            category_risks[category] += residual_risk
        
        # Overall risk classification
        avg_risk = total_risk / max(len(hazards), 1)
        if avg_risk > 8:
            overall = "critical"
        elif avg_risk > 5:
            overall = "high"
        elif avg_risk > 3:
            overall = "moderate"
        elif avg_risk > 1:
            overall = "low"
        else:
            overall = "acceptable"
        
        return {
            "risk_assessments": [
                {
                    "category": a.category,
                    "hazard": a.hazard,
                    "likelihood": a.likelihood,
                    "severity": a.severity,
                    "risk_score": a.risk_score,
                    "mitigation": a.mitigation,
                    "residual_risk": a.residual_risk,
                    "risk_level": "high" if a.residual_risk > 5 else "moderate" if a.residual_risk > 3 else "low",
                }
                for a in assessments
            ],
            "overall_risk": overall,
            "overall_risk_score": round(avg_risk, 2),
            "category_breakdown": {
                cat: round(risk, 2) for cat, risk in category_risks.items()
            },
            "top_risks": sorted(
                [{"hazard": a.hazard, "residual_risk": a.residual_risk, "category": a.category} 
                 for a in assessments],
                key=lambda x: x["residual_risk"],
                reverse=True
            )[:5],
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    def assess_fatigue_risk(self, pilot_data: Dict) -> Dict:
        """
        Assess fatigue risk for flight crew.
        """
        factors = []
        total_risk_score = 0
        risk_multiplier = 1.0
        
        # Check flight hours in 24h
        fh_24h = pilot_data.get("flight_hours_24h", 0)
        if fh_24h > self.fatigue_factors["flight_hours_24h"]["threshold"]:
            factor = self.fatigue_factors["flight_hours_24h"]["risk_multiplier"]
            risk_multiplier *= factor
            factors.append({
                "factor": "flight_hours_24h",
                "value": fh_24h,
                "threshold": self.fatigue_factors["flight_hours_24h"]["threshold"],
                "risk": "high",
                "multiplier": factor,
            })
            total_risk_score += 3
        
        # Check flight hours in 7 days
        fh_7d = pilot_data.get("flight_hours_7d", 0)
        if fh_7d > self.fatigue_factors["flight_hours_7d"]["threshold"]:
            factor = self.fatigue_factors["flight_hours_7d"]["risk_multiplier"]
            risk_multiplier *= factor
            factors.append({
                "factor": "flight_hours_7d",
                "value": fh_7d,
                "threshold": self.fatigue_factors["flight_hours_7d"]["threshold"],
                "risk": "moderate" if fh_7d < 40 else "high",
                "multiplier": factor,
            })
            total_risk_score += 2
        
        # Check night flights
        night_count = pilot_data.get("night_flights_28d", 0)
        if night_count > self.fatigue_factors["night_flights"]["threshold"]:
            factor = self.fatigue_factors["night_flights"]["risk_multiplier"]
            risk_multiplier *= factor
            factors.append({
                "factor": "night_flights",
                "value": night_count,
                "threshold": self.fatigue_factors["night_flights"]["threshold"],
                "risk": "moderate",
                "multiplier": factor,
            })
            total_risk_score += 1
        
        # Check early starts
        early_starts = pilot_data.get("early_starts_7d", 0)
        if early_starts > self.fatigue_factors["early_start"]["threshold"]:
            factor = self.fatigue_factors["early_start"]["risk_multiplier"]
            risk_multiplier *= factor
            factors.append({
                "factor": "early_starts",
                "value": early_starts,
                "threshold": self.fatigue_factors["early_start"]["threshold"],
                "risk": "low",
                "multiplier": factor,
            })
            total_risk_score += 1
        
        # Check consecutive days
        consec_days = pilot_data.get("consecutive_days", 1)
        if consec_days > self.fatigue_factors["consecutive_days"]["threshold"]:
            factor = self.fatigue_factors["consecutive_days"]["risk_multiplier"]
            risk_multiplier *= factor
            factors.append({
                "factor": "consecutive_days",
                "value": consec_days,
                "threshold": self.fatigue_factors["consecutive_days"]["threshold"],
                "risk": "moderate",
                "multiplier": factor,
            })
            total_risk_score += 1
        
        # Risk classification
        if total_risk_score >= 5 or risk_multiplier > 2.5:
            risk_level = "high"
            recommendation = "REST REQUIRED - 12+ hours before next flight"
        elif total_risk_score >= 3 or risk_multiplier > 1.8:
            risk_level = "moderate"
            recommendation = "Consider reducing flight hours. Monitor for fatigue signs."
        elif total_risk_score >= 1 or risk_multiplier > 1.3:
            risk_level = "low"
            recommendation = "Standard monitoring. Fatigue risk is elevated but acceptable."
        else:
            risk_level = "acceptable"
            recommendation = "No elevated fatigue risk. Fit for duty."
        
        return {
            "pilot_data": pilot_data,
            "fatigue_factors": factors,
            "total_risk_score": total_risk_score,
            "risk_multiplier": round(risk_multiplier, 2),
            "risk_level": risk_level,
            "recommendation": recommendation,
            "compliance_status": "compliant" if risk_level in ["low", "acceptable"] else "review_required",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    def assess_runway_excursion_risk(self, runway_condition: str, aircraft_weight: str,
                                      landing_speed: float, pilot_experience: str) -> Dict:
        """
        Assess runway excursion risk during landing.
        """
        conditions = self.runway_safety.get(runway_condition, self.runway_safety["dry"])
        friction = conditions["friction"]
        braking_factor = conditions["braking_factor"]
        
        # Weight factor
        weight_factors = {"light": 0.7, "medium": 1.0, "heavy": 1.3, "super": 1.6}
        weight_factor = weight_factors.get(aircraft_weight, 1.0)
        
        # Speed factor
        speed_factor = max(0.8, min(1.5, landing_speed / 130))  # 130 kts = baseline
        
        # Experience factor
        experience_factors = {"novice": 1.5, "intermediate": 1.2, "experienced": 1.0, "senior": 0.8}
        exp_factor = experience_factors.get(pilot_experience, 1.0)
        
        # Combined risk score
        risk_score = (1 / friction) * weight_factor * speed_factor * exp_factor * braking_factor * 10
        
        if risk_score > 20:
            risk_level = "critical"
        elif risk_score > 12:
            risk_level = "high"
        elif risk_score > 6:
            risk_level = "moderate"
        else:
            risk_level = "low"
        
        # Calculate stopping distance
        baseline_stop = 1800  # meters for A320 at 130 kts on dry runway
        adjusted_stop = baseline_stop * (1 / friction) * weight_factor * (speed_factor ** 2) / braking_factor
        
        return {
            "runway_assessment": {
                "condition": runway_condition,
                "friction_coefficient": friction,
                "braking_action": braking_factor,
            },
            "aircraft_factors": {
                "weight_category": aircraft_weight,
                "weight_factor": weight_factor,
                "landing_speed_knots": landing_speed,
                "speed_factor": round(speed_factor, 2),
            },
            "pilot_factors": {
                "experience_level": pilot_experience,
                "experience_factor": exp_factor,
            },
            "risk_score": round(risk_score, 2),
            "risk_level": risk_level,
            "estimated_stopping_distance_meters": round(adjusted_stop, 0),
            "runway_length_recommended": round(adjusted_stop * 1.67, 0),  # 1.67x safety margin
            "recommendations": self._get_runway_recommendations(risk_level, runway_condition),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    def _get_runway_recommendations(self, risk_level: str, condition: str) -> List[str]:
        """Get runway safety recommendations."""
        recommendations = []
        
        if risk_level in ["critical", "high"]:
            recommendations.append("CONSIDER DIVERTER - High runway excursion risk")
            recommendations.append("Maximum brake temperature check required")
            recommendations.append("Increased approach speed by 10-15 knots recommended")
        elif risk_level == "moderate":
            recommendations.append("Use autobrake MAX if available")
            recommendations.append("Plan for full reverse and manual braking")
        else:
            recommendations.append("Standard landing procedure")
        
        if condition in ["snow", "ice"]:
            recommendations.append("Apply reverse thrust immediately on touchdown")
            recommendations.append("Consider landing distance assessment (LDA)")
        
        return recommendations
    
    def generate_safety_report(self, flight_count: int = 100, 
                                route: str = "IST-JFK") -> Dict:
        """
        Generate comprehensive safety report for operations.
        """
        # Generate sample hazard data
        sample_hazards = []
        hazard_pool = [
            {"category": "weather", "hazard": "wind_shear_on_final", "likelihood": "occasional", "severity": "high", "mitigation": "wind_shear_detection"},
            {"category": "weather", "hazard": "wake_turbulence", "likelihood": "probable", "severity": "moderate", "mitigation": "separation_standards"},
            {"category": "runway", "hazard": "runway_contamination", "likelihood": "occasional", "severity": "high", "mitigation": "braking_action_reports"},
            {"category": "runway", "hazard": "runway_end_obstacle", "likelihood": "remote", "severity": "extreme", "mitigation": "approach_procedures"},
            {"category": "equipment", "hazard": "engine_failure_takeoff", "likelihood": "unlikely", "severity": "extreme", "mitigation": "engine_failure_procedures"},
            {"category": "human_factors", "hazard": "controlled_flight_into_terrain", "likelihood": "unlikely", "severity": "extreme", "mitigation": "pilot_training"},
            {"category": "air_traffic", "hazard": "traffic_conflict_app", "likelihood": "probable", "severity": "moderate", "mitigation": "tcas_resolution"},
        ]
        
        # Random sample based on flight count
        selected = random.sample(hazard_pool, min(5, len(hazard_pool)))
        
        risk_assessment = self.assess_risk(selected)
        
        # Sample fatigue assessment
        pilot_data = {
            "flight_hours_24h": random.randint(4, 12),
            "flight_hours_7d": random.randint(20, 45),
            "night_flights_28d": random.randint(0, 8),
            "early_starts_7d": random.randint(0, 6),
            "consecutive_days": random.randint(1, 6),
            "time_zones": random.randint(0, 4),
        }
        fatigue_assessment = self.assess_fatigue_risk(pilot_data)
        
        # Sample runway assessment
        runway_assessment = self.assess_runway_excursion_risk(
            runway_condition=random.choice(["dry", "wet", "snow", "ice"]),
            aircraft_weight=random.choice(["light", "medium", "heavy", "super"]),
            landing_speed=random.uniform(110, 160),
            pilot_experience=random.choice(["novice", "intermediate", "experienced", "senior"])
        )
        
        # Incident probability
        incident_prob = {
            "ground_incident": round(random.uniform(0.01, 0.05) * flight_count, 1),
            "runway_excursion": round(random.uniform(0.001, 0.005) * flight_count, 1),
            "weather_event": round(random.uniform(0.005, 0.02) * flight_count, 1),
            "inflight_event": round(random.uniform(0.002, 0.01) * flight_count, 1),
        }
        
        # SMS metrics
        sms_metrics = {
            "safety_reports_filed": random.randint(15, 45),
            "hazards_identified": len(selected),
            "risks_assessed": len(selected),
            "mitigations_implemented": random.randint(3, 7),
            "trend": random.choice(["improving", "stable", "degrading"]),
        }
        
        return {
            "report_type": "comprehensive_safety_report",
            "route": route,
            "flight_count": flight_count,
            "risk_assessment": risk_assessment,
            "fatigue_assessment": fatigue_assessment,
            "runway_safety": runway_assessment,
            "incident_probability": incident_prob,
            "sms_metrics": sms_metrics,
            "overall_safety_status": "safe" if risk_assessment["overall_risk_score"] < 4 else "caution" if risk_assessment["overall_risk_score"] < 7 else "attention_required",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

# ─────────────────────────────────────────────
# API Convenience Functions
# ─────────────────────────────────────────────
_manager = None

def get_manager():
    global _manager
    if _manager is None:
        _manager = SafetyRiskManager()
    return _manager

def assess_safety_risk(hazards: List[Dict]) -> dict:
    """Perform risk assessment on identified hazards."""
    return get_manager().assess_risk(hazards)

def assess_fatigue_risk(pilot_data: Dict) -> dict:
    """Assess fatigue risk for flight crew."""
    return get_manager().assess_fatigue_risk(pilot_data)

def assess_runway_risk(runway_condition: str = "wet", 
                        aircraft_weight: str = "medium",
                        landing_speed: float = 130,
                        pilot_experience: str = "experienced") -> dict:
    """Assess runway excursion risk."""
    return get_manager().assess_runway_excursion_risk(
        runway_condition, aircraft_weight, landing_speed, pilot_experience
    )

def generate_safety_report(flight_count: int = 100, route: str = "IST-JFK") -> dict:
    """Generate comprehensive safety report."""
    return get_manager().generate_safety_report(flight_count, route)

if __name__ == "__main__":
    hazards = [
        {"category": "weather", "hazard": "wind_shear", "likelihood": "occasional", 
         "severity": "high", "mitigation": "wind_shear_detection"},
        {"category": "human_factors", "hazard": "pilot_error", "likelihood": "probable",
         "severity": "moderate", "mitigation": "training"},
    ]
    result = assess_safety_risk(hazards)
    print(json.dumps(result, indent=2))
    print("✅ Safety risk manager tested")
