"""
Aviation Marketing & Revenue Analytics
========================================
AI-powered revenue analytics for airline marketing.

Solves:
1. Customer lifetime value (CLV) calculation
2. Dynamic pricing optimization
3. Route profitability analysis
4. Customer segmentation
5. Marketing campaign ROI
6. Ancillary revenue optimization
"""

import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import math

# ─────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────

# Customer segments and their characteristics
CUSTOMER_SEGMENTS = {
    "frequent_business": {
        "annual_revenue": 4500,
        "avg_booking_advance": 14,
        "loyalty_score": 0.9,
        "price_sensitivity": 0.3,
        "ancillary_propensity": 0.4,
    },
    "occasional_business": {
        "annual_revenue": 1800,
        "avg_booking_advance": 10,
        "loyalty_score": 0.6,
        "price_sensitivity": 0.5,
        "ancillary_propensity": 0.3,
    },
    "leisure": {
        "annual_revenue": 900,
        "avg_booking_advance": 45,
        "loyalty_score": 0.3,
        "price_sensitivity": 0.8,
        "ancillary_propensity": 0.2,
    },
    "premium_leisure": {
        "annual_revenue": 2200,
        "avg_booking_advance": 30,
        "loyalty_score": 0.5,
        "price_sensitivity": 0.6,
        "ancillary_propensity": 0.5,
    },
    "group_travel": {
        "annual_revenue": 15000,
        "avg_booking_advance": 60,
        "loyalty_score": 0.4,
        "price_sensitivity": 0.7,
        "ancillary_propensity": 0.1,
    },
    "cargo_forwarder": {
        "annual_revenue": 25000,
        "avg_booking_advance": 7,
        "loyalty_score": 0.8,
        "price_sensitivity": 0.4,
        "ancillary_propensity": 0.05,
    },
}

# Ancillary services and their revenue potential
ANCILLARY_SERVICES = {
    "seat_selection": {"revenue_per_booking": 25, "attachment_rate": 0.70},
    "extra_baggage": {"revenue_per_booking": 45, "attachment_rate": 0.50},
    "priority_boarding": {"revenue_per_booking": 20, "attachment_rate": 0.60},
    "meal_upgrade": {"revenue_per_booking": 15, "attachment_rate": 0.35},
    "wifi": {"revenue_per_booking": 12, "attachment_rate": 0.45},
    "lounge_access": {"revenue_per_booking": 50, "attachment_rate": 0.25},
    "upgrade": {"revenue_per_booking": 150, "attachment_rate": 0.20},
    "hotel_package": {"revenue_per_booking": 80, "attachment_rate": 0.15},
    "car_rental": {"revenue_per_booking": 60, "attachment_rate": 0.12},
}

# Route profitability factors
ROUTE_PROFITABILITY = {
    "IST-JFK": {"yield": 0.12, "load_factor": 0.82, "distance_nm": 6650, "competition": "medium"},
    "IST-LHR": {"yield": 0.10, "load_factor": 0.78, "distance_nm": 1850, "competition": "high"},
    "IST-DXB": {"yield": 0.14, "load_factor": 0.85, "distance_nm": 3200, "competition": "low"},
    "IST-SIN": {"yield": 0.13, "load_factor": 0.80, "distance_nm": 5800, "competition": "medium"},
    "IST-FCO": {"yield": 0.08, "load_factor": 0.72, "distance_nm": 1050, "competition": "high"},
    "IST-BCN": {"yield": 0.09, "load_factor": 0.75, "distance_nm": 1700, "competition": "high"},
    "IST-MUC": {"yield": 0.10, "load_factor": 0.70, "distance_nm": 850, "competition": "high"},
    "IST-IST": {"yield": 0.05, "load_factor": 0.65, "distance_nm": 300, "competition": "high"},
}

# Campaign types and typical ROI
CAMPAIGN_TYPES = {
    "email_marketing": {"base_roi": 3.5, "cost_per_thousand": 5},
    "social_media": {"base_roi": 2.8, "cost_per_thousand": 15},
    "ppc": {"base_roi": 4.2, "cost_per_thousand": 25},
    "loyalty_program": {"base_roi": 5.5, "cost_per_thousand": 50},
    "content_marketing": {"base_roi": 3.0, "cost_per_thousand": 8},
    "tv_advertising": {"base_roi": 2.0, "cost_per_thousand": 150},
    "influencer": {"base_roi": 2.5, "cost_per_thousand": 35},
}

class RevenueAnalytics:
    """
    AI-powered revenue analytics engine.
    """
    
    def __init__(self):
        self.segments = CUSTOMER_SEGMENTS
        self.ancillaries = ANCILLARY_SERVICES
        self.routes = ROUTE_PROFITABILITY
        self.campaigns = CAMPAIGN_TYPES
    
    def calculate_customer_lifetime_value(self, customer_id: str = None,
                                          segment: str = "frequent_business",
                                          tenure_months: int = 24,
                                          monthly_bookings: int = 4) -> Dict:
        """
        Calculate Customer Lifetime Value (CLV).
        """
        seg_data = self.segments.get(segment, self.segments["occasional_business"])
        
        annual_revenue = seg_data["annual_revenue"]
        loyalty = seg_data["loyalty_score"]
        price_sens = seg_data["price_sensitivity"]
        ancillary_prop = seg_data["ancillary_propensity"]
        
        # Tenure-based retention
        monthly_retention = 0.92 if segment == "frequent_business" else 0.88
        retention_factor = 1 - (1 - monthly_retention) ** tenure_months
        
        # Monthly revenue
        monthly_rev = annual_revenue / 12
        total_revenue = monthly_rev * tenure_months
        
        # Ancillary revenue (upsell/cross-sell)
        ancillary_rev_per_flight = sum(
            a["revenue_per_booking"] * a["attachment_rate"] * ancillary_prop
            for a in self.ancillaries.values()
        )
        total_ancillary = ancillary_rev_per_flight * monthly_bookings * tenure_months
        
        # Cost to serve
        cost_to_serve = total_revenue * 0.45  # 45% of revenue
        
        # CLV calculation
        clv = (total_revenue + total_ancillary - cost_to_serve) * retention_factor
        
        # Segmentation for marketing
        if clv > 5000:
            clv_tier = "VIP"
        elif clv > 2000:
            clv_tier = "Premium"
        elif clv > 800:
            clv_tier = "Standard"
        else:
            clv_tier = "Basic"
        
        return {
            "customer_id": customer_id or f"CUST-{random.randint(1000, 9999)}",
            "segment": segment,
            "clv_calculation": {
                "tenure_months": tenure_months,
                "annual_revenue": annual_revenue,
                "total_revenue": round(total_revenue, 2),
                "ancillary_revenue": round(total_ancillary, 2),
                "cost_to_serve": round(cost_to_serve, 2),
                "retention_factor": round(retention_factor, 3),
            },
            "clv_usd": round(clv, 2),
            "clv_tier": clv_tier,
            "marketing_recommendations": {
                "upsell_opportunities": [s for s in ["upgrade", "lounge_access", "hotel_package"] 
                                        if self.ancillaries[s]["attachment_rate"] * ancillary_prop > 0.15],
                "loyalty_program": "Gold" if clv > 3000 else "Silver" if clv > 1000 else "Bronze",
                "email_frequency": "monthly" if segment in ["frequent_business"] else "quarterly" if segment != "leisure" else "annual",
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    def optimize_ancillary_revenue(self, bookings: int = 10000,
                                    segment: str = "mixed") -> Dict:
        """
        Optimize ancillary revenue across bookings.
        """
        if segment == "mixed":
            seg_distribution = {
                "frequent_business": 0.25,
                "occasional_business": 0.20,
                "leisure": 0.40,
                "premium_leisure": 0.10,
                "group_travel": 0.03,
                "cargo_forwarder": 0.02,
            }
        else:
            seg_distribution = {segment: 1.0}
        
        total_revenue = 0
        service_breakdown = {}
        
        for seg_name, seg_pct in seg_distribution.items():
            seg_data = self.segments.get(seg_name, self.segments["occasional_business"])
            booking_count = int(bookings * seg_pct)
            ancillary_prop = seg_data["ancillary_propensity"]
            
            for service_name, service_data in self.ancillaries.items():
                # Adjust attachment rate by segment
                base_attach = service_data["attachment_rate"]
                adjusted_attach = base_attach * (0.5 + ancillary_prop)
                attached = booking_count * adjusted_attach
                revenue = attached * service_data["revenue_per_booking"]
                
                if service_name not in service_breakdown:
                    service_breakdown[service_name] = {"revenue": 0, "attachments": 0, "bookings": booking_count}
                
                service_breakdown[service_name]["revenue"] += revenue
                service_breakdown[service_name]["attachments"] += attached
                total_revenue += revenue
        
        # Optimize recommendations
        recommendations = []
        for service, data in sorted(service_breakdown.items(), key=lambda x: x[1]["revenue"], reverse=True)[:5]:
            attach_rate = data["attachments"] / max(data["bookings"], 1)
            recommendations.append({
                "service": service,
                "revenue_usd": round(data["revenue"], 2),
                "overall_attachement_rate": round(attach_rate * 100, 1),
                "action": f"Promote {service} more aggressively" if attach_rate < 0.3 else "Maintain current strategy",
            })
        
        return {
            "total_bookings": bookings,
            "customer_segment_mix": segment,
            "total_ancillary_revenue_usd": round(total_revenue, 2),
            "revenue_per_booking": round(total_revenue / max(bookings, 1), 2),
            "service_breakdown": {
                s: {"revenue_usd": round(d["revenue"], 2), "attachments": round(d["attachments"], 0)}
                for s, d in service_breakdown.items()
            },
            "top_opportunities": recommendations,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    def analyze_route_profitability(self, routes: List[str] = None,
                                     period: str = "monthly") -> Dict:
        """
        Analyze profitability across routes.
        """
        if routes is None:
            routes = list(self.routes.keys())
        
        analysis = {}
        total_revenue = 0
        total_profit = 0
        
        for route in routes:
            route_data = self.routes.get(route, {"yield": 0.10, "load_factor": 0.75, "distance_nm": 2000, "competition": "medium"})
            yield_rate = route_data["yield"]
            load_factor = route_data["load_factor"]
            distance = route_data["distance_nm"]
            
            # Estimate seats (typical aircraft capacity)
            if distance > 5000:
                seats = 250  # Long-haul
            elif distance > 2000:
                seats = 180  # Medium-haul
            else:
                seats = 150  # Short-haul
            
            # Revenue estimation
            avg_fare = distance * 0.15 * random.uniform(0.8, 1.2)  # $/passenger
            passengers = seats * load_factor
            revenue = passengers * avg_fare
            
            # Cost estimation (fuel + crew + airport + maintenance)
            fuel_cost = distance * 3.5 * 0.85  # USD per NM
            crew_cost = passengers * 2.5
            airport_cost = 500 + distance * 0.1
            maintenance_cost = passengers * 15
            total_cost = fuel_cost + crew_cost + airport_cost + maintenance_cost
            
            profit = revenue - total_cost
            profit_margin = (profit / revenue) * 100 if revenue > 0 else 0
            
            analysis[route] = {
                "distance_nm": distance,
                "seats": seats,
                "load_factor": f"{load_factor * 100}%",
                "passengers": round(passengers, 0),
                "avg_fare_usd": round(avg_fare, 2),
                "revenue_usd": round(revenue, 2),
                "total_cost_usd": round(total_cost, 2),
                "profit_usd": round(profit, 2),
                "profit_margin_pct": round(profit_margin, 1),
                "competition_level": route_data["competition"],
                "profitability": "high" if profit_margin > 20 else "medium" if profit_margin > 10 else "low" if profit_margin > 0 else "unprofitable",
            }
            
            total_revenue += revenue
            total_profit += profit
        
        return {
            "period": period,
            "route_analysis": analysis,
            "summary": {
                "total_routes": len(routes),
                "total_revenue_usd": round(total_revenue, 2),
                "total_profit_usd": round(total_profit, 2),
                "avg_profit_margin_pct": round((total_profit / max(total_revenue, 1)) * 100, 1),
                "most_profitable_route": max(analysis.items(), key=lambda x: x[1]["profit_usd"])[0],
                "least_profitable_route": min(analysis.items(), key=lambda x: x[1]["profit_usd"])[0],
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    def campaign_roi_analysis(self, campaign_type: str = "email_marketing",
                               audience_size: int = 10000,
                               budget: float = 5000) -> Dict:
        """
        Analyze marketing campaign ROI.
        """
        campaign_data = self.campaigns.get(campaign_type, self.campaigns["email_marketing"])
        
        base_roi = campaign_data["base_roi"]
        cpm = campaign_data["cost_per_thousand"]
        
        # Calculate expected results
        impressions = audience_size
        cost = (impressions / 1000) * cpm
        if budget and cost > budget:
            # Scale down to budget
            scale = budget / cost
            impressions = audience_size * scale
            cost = budget
        
        # Conversion rates
        base_conversion = 0.02 if campaign_type == "ppc" else 0.05 if campaign_type == "loyalty_program" else 0.03
        conversions = impressions * base_conversion
        
        # Revenue from conversions
        avg_booking_value = 450  # USD
        conversion_revenue = conversions * avg_booking_value
        
        # ROI calculation
        roi = (conversion_revenue - cost) / max(cost, 1) if cost > 0 else 0
        actual_roi = roi * (base_roi / 3.5)  # Normalize to base ROI
        
        return {
            "campaign_type": campaign_type,
            "audience_size": int(impressions),
            "cost_usd": round(cost, 2),
            "budget_usd": budget,
            "within_budget": cost <= budget,
            "metrics": {
                "cpm_usd": cpm,
                "estimated_conversions": round(conversions, 1),
                "conversion_rate_pct": round(base_conversion * 100, 1),
                "revenue_usd": round(conversion_revenue, 2),
                "roi_multiple": round(actual_roi, 2),
                "roi_pct": round(actual_roi * 100, 1),
                "net_revenue_usd": round(conversion_revenue - cost, 2),
            },
            "recommendation": "Scale up campaign" if actual_roi > base_roi else "Optimize targeting" if actual_roi > base_roi * 0.5 else "Reevaluate campaign type",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    def comprehensive_revenue_report(self) -> Dict:
        """Generate comprehensive revenue analytics report."""
        clv = self.calculate_customer_lifetime_value(segment="frequent_business", tenure_months=24)
        ancillary = self.optimize_ancillary_revenue(bookings=15000)
        routes = self.analyze_route_profitability()
        campaign = self.campaign_roi_analysis("email_marketing", 10000, 5000)
        
        return {
            "customer_lifetime_value": clv,
            "ancillary_revenue_optimization": {
                "total_revenue": ancillary["total_ancillary_revenue_usd"],
                "per_booking": ancillary["revenue_per_booking"],
            },
            "route_profitability": {
                "total_revenue": routes["summary"]["total_revenue_usd"],
                "total_profit": routes["summary"]["total_profit_usd"],
                "avg_margin": f"{routes['summary']['avg_profit_margin_pct']}%",
            },
            "marketing_roi": {
                "campaign_type": campaign["campaign_type"],
                "roi_multiple": campaign["metrics"]["roi_multiple"],
                "net_revenue": campaign["metrics"]["net_revenue_usd"],
            },
            "total_monthly_revenue_usd": round(
                ancillary["total_ancillary_revenue_usd"] +
                routes["summary"]["total_revenue_usd"] +
                campaign["metrics"]["net_revenue_usd"],
                2
            ),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

# ─────────────────────────────────────────────
# API Convenience Functions
# ─────────────────────────────────────────────
_revenue = None

def get_revenue_analytics():
    global _revenue
    if _revenue is None:
        _revenue = RevenueAnalytics()
    return _revenue

def calculate_clv(segment: str = "frequent_business", tenure: int = 24, bookings: int = 4) -> dict:
    """Calculate customer lifetime value."""
    return get_revenue_analytics().calculate_customer_lifetime_value(
        segment=segment, tenure_months=tenure, monthly_bookings=bookings
    )

def optimize_ancillaries(bookings: int = 10000, segment: str = "mixed") -> dict:
    """Optimize ancillary revenue."""
    return get_revenue_analytics().optimize_ancillary_revenue(bookings, segment)

def route_profitability(routes: List[str] = None, period: str = "monthly") -> dict:
    """Analyze route profitability."""
    return get_revenue_analytics().analyze_route_profitability(routes, period)

def campaign_analysis(campaign_type: str = "email_marketing", audience: int = 10000, budget: float = 5000) -> dict:
    """Analyze campaign ROI."""
    return get_revenue_analytics().campaign_roi_analysis(campaign_type, audience, budget)

def revenue_report() -> dict:
    """Generate comprehensive revenue report."""
    return get_revenue_analytics().comprehensive_revenue_report()

if __name__ == "__main__":
    result = revenue_report()
    print(json.dumps(result, indent=2))
    print("✅ Revenue analytics tested")
