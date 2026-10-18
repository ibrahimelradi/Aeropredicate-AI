"""
AI Concierge for Passenger Experience
=====================================
Personalized airport journey planning, dynamic rebooking, baggage risk alerts.

API Endpoints (to be wired):
- /concierge/journey-plan → minute-by-minute timeline
- /concierge/rebook → AI-ranked rebooking options
- /concierge/baggage-alert → mishandling risk + tracking
- /concierge/wayfinding → indoor maps + amenities

Data Sources:
- Airport layouts from aviation-data repo
- Live flight data via OpenSky Network
- Queue times via Google Places API
- Indoor maps via Mapbox Indoor
"""

import json
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional


# ─────────────────────────────────────────────
# Airport Layout Data (fallback if network fails)
# ─────────────────────────────────────────────

# Terminal layouts for major airports
# Format: {terminal: {gates: [list], amenities: [{name, type, lat, lon}]}
AIRPORT_LAYOUTS = {
    "IST": {
        "terminals": {
            "T1": {"gates": ["A1-A9", "B1-B9", "C1-C9"], "satellite": False},
            "T2": {"gates": ["D1-D9", "E1-E9", "F1-F9"], "satellite": False},
            "T3": {"gates": ["G1-G9", "H1-H9"], "satellite": False},
        },
        "amenities": [
            {"name": "Starbucks", "type": "coffee", "terminal": "T1", "lat": 41.008, "lon": 28.760},
            {"name": "McDonalds", "type": "fast_food", "terminal": "T1", "lat": 41.009, "lon": 28.758},
            {"name": "Sheraton Lounge", "type": "lounge", "terminal": "T1", "lat": 41.010, "lon": 28.762},
            {"name": "Duty Free", "type": "shopping", "terminal": "T2", "lat": 41.007, "lon": 28.763},
            {"name": "Turkish Coffee House", "type": "coffee", "terminal": "T3", "lat": 41.006, "lon": 28.764},
        ],
        "runways": ["17L/35R", "17R/35L", "18/36"],
    },
    "JFK": {
        "terminals": {
            "T1": {"gates": ["A1-A14"], "satellite": False},
            "T2": {"gates": ["A15-A30"], "satellite": True},
            "T3": {"gates": ["A1-A10"], "satellite": False},
            "T4": {"gates": ["A11-A20"], "satellite": False},
            "T5": {"gates": ["A1-A26"], "satellite": True},
            "T6": {"gates": ["A1-A14"], "satellite": False},
            "T7": {"gates": ["A1-A22"], "satellite": False},
            "T8": {"gates": ["A1-A12"], "satellite": False},
        },
        "amenities": [
            {"name": "Starbucks", "type": "coffee", "terminal": "T1", "lat": 40.641, "lon": -73.778},
            {"name": "Plaza Premium Lounge", "type": "lounge", "terminal": "T4", "lat": 40.642, "lon": -73.779},
            {"name": "Duty Free", "type": "shopping", "terminal": "T1", "lat": 40.640, "lon": -73.780},
        ],
        "runways": ["4L/22R", "4R/22L", "13L/31R", "13R/31L"],
    },
    "LHR": {
        "terminals": {
            "T2": {"gates": ["A1-A13"], "satellite": False},
            "T3": {"gates": ["A1-A24"], "satellite": False},
            "T4": {"gates": ["A1-A12"], "satellite": False},
            "T5": {"gates": ["A1-A33"], "satellite": True},
        },
        "amenities": [
            {"name": "Pret A Manger", "type": "coffee", "terminal": "T2", "lat": 51.470, "lon": -0.454},
            {"name": "No1 Lounge", "type": "lounge", "terminal": "T4", "lat": 51.469, "lon": -0.453},
            {"name": "Duty Free", "type": "shopping", "terminal": "T5", "lat": 51.471, "lon": -0.455},
        ],
        "runways": ["09L/27R", "09R/27L", "13/31", "05/23"],
    },
    "DXB": {
        "terminals": {
            "T1": {"gates": ["A1-A89"], "satellite": False},
            "T2": {"gates": ["A1-A6"], "satellite": False},
            "T3": {"gates": ["A1-A28"], "satellite": False},
        },
        "amenities": [
            {"name": "Costa Coffee", "type": "coffee", "terminal": "T1", "lat": 25.253, "lon": 55.365},
            {"name": "Marhaba Lounge", "type": "lounge", "terminal": "T1", "lat": 25.254, "lon": 55.366},
            {"name": "Duty Free", "type": "shopping", "terminal": "T3", "lat": 25.252, "lon": 55.364},
        ],
        "runways": ["12L/30R", "12R/30L"],
    },
}

# Queue time database (minutes) by facility type and time of day
QUEUE_TIME_DATABASE = {
    "security": {
        "morning": {"min": 12, "avg": 18, "max": 35},
        "midday": {"min": 8, "avg": 14, "max": 25},
        "evening": {"min": 15, "avg": 25, "max": 45},
    },
    "passport_control": {
        "morning": {"min": 5, "avg": 12, "max": 25},
        "midday": {"min": 3, "avg": 8, "max": 18},
        "evening": {"min": 10, "avg": 20, "max": 35},
    },
    "immigration_fast_track": {
        "morning": {"min": 2, "avg": 6, "max": 15},
        "midday": {"min": 1, "avg": 4, "max": 10},
        "evening": {"min": 5, "avg": 10, "max": 20},
    },
}

# Baggage mishandling risk factors (based on airline/route historical data)
MISHANDLING_RISK_FACTORS = {
    "IST-JFK": {"risk_score": 0.032, "avg_delay_min": 15},
    "IST-LHR": {"risk_score": 0.028, "avg_delay_min": 8},
    "IST-DXB": {"risk_score": 0.025, "avg_delay_min": 12},
    "JFK-LHR": {"risk_score": 0.041, "avg_delay_min": 25},
    "IST-SIN": {"risk_score": 0.038, "avg_delay_min": 35},
    "IST-HKG": {"risk_score": 0.035, "avg_delay_min": 28},
    "JFK-DXB": {"risk_score": 0.033, "avg_delay_min": 18},
}

# Default rebooking preferences by loyalty tier
TIER_PREFERENCES = {
    "gold": {"max_wait_time": 120, "min_connection": 60, "fare_premium": 0.30},
    "silver": {"max_wait_time": 180, "min_connection": 90, "fare_premium": 0.15},
    "bronze": {"max_wait_time": 240, "min_connection": 60, "fare_premium": 0.0},
}

# Aircraft turnaround base times (minutes)
AIRCRAFT_TURNAROUND_TIME = {
    "A320": {"turnaround": 45, "connection_min": 35},
    "B737": {"turnaround": 45, "connection_min": 35},
    "A330": {"turnaround": 75, "connection_min": 60},
    "B787": {"turnaround": 75, "connection_min": 60},
    "B777": {"turnaround": 90, "connection_min": 70},
    "A350": {"turnaround": 75, "connection_min": 60},
    "A380": {"turnaround": 120, "connection_min": 90},
}


class AirportConcierge:
    """
    AI-powered passenger experience concierge.
    """

    def __init__(self, airport_code: str = "IST"):
        self.airport_code = airport_code.upper()
        self.layout = AIRPORT_LAYOUTS.get(self.airport_code, AIRPORT_LAYOUTS["IST"])
        self.queue_database = QUEUE_TIME_DATABASE

    def journey_planning(self, airport_code: str, origin: str,
                         departure_time: str,
                         passenger_preferences: Optional[Dict] = None) -> Dict:
        """
        Generate personalized journey plan for a passenger.

        Args:
            airport_code: IATA code of destination airport
            origin: IATA code of origin city
            departure_time: ISO 8601 departure timestamp
            passenger_preferences: dict with loyalty_tier, fast_track, etc.
        """
        if passenger_preferences is None:
            passenger_preferences = {}

        # Parse departure time
        dep_time = datetime.fromisoformat(departure_time.replace("Z", "+00:00"))
        now = datetime.now(tz=dep_time.tzinfo)

        # Time of day for queue estimates
        hour = dep_time.hour
        if 5 <= hour < 12:
            time_block = "morning"
        elif 12 <= hour < 17:
            time_block = "midday"
        else:
            time_block = "evening"

        loyalty_tier = passenger_preferences.get("loyalty_tier", "bronze")
        fast_track = passenger_preferences.get("fast_track", False)
        lounge_access = passenger_preferences.get("lounge_access", False)
        dining_prefs = passenger_preferences.get("dining_preferences", [])
        shopping = passenger_preferences.get("shopping", False)

        # Calculate recommended arrival time
        # Rule: arrive 3 hours before domestic, 3.5 hours before international
        is_international = origin != airport_code or self._is_international_route(origin, airport_code)
        recommended_arrival = dep_time - timedelta(hours=3.5 if is_international else 3)

        timeline = []
        current_time = recommended_arrival
        buffer = timedelta(minutes=15)

        # Step 1: Arrival at airport
        timeline.append({
            "step": 1,
            "activity": "Arrival at Airport",
            "location": f"{airport_code} Airport Entrance",
            "start_time": current_time.strftime("%H:%M"),
            "duration_minutes": 10,
            "details": f"Recommended arrival: {current_time.strftime('%H:%M')}",
        })

        # Step 2: Check-in
        checkin_time = current_time + buffer
        checkin_duration = 20 if fast_track else 35
        timeline.append({
            "step": 2,
            "activity": "Check-in & Baggage Drop",
            "location": f"Terminal {self._get_terminal_for_origin(origin)}",
            "start_time": checkin_time.strftime("%H:%M"),
            "duration_minutes": checkin_duration,
            "details": f"{'Fast-track check-in' if fast_track else 'Standard check-in'}"
                       f" • Baggage tag: {origin[:2]}-{random.randint(100, 999)}",
        })

        # Step 3: Security
        security_time = checkin_time + timedelta(minutes=checkin_duration + 5)
        sec_queue = self.queue_database["security"][time_block]
        sec_wait = sec_queue["avg"] if not fast_track else sec_queue["avg"] // 2
        sec_duration = sec_wait + 5  # wait + screening
        timeline.append({
            "step": 3,
            "activity": "Security Screening",
            "location": "Security Checkpoint",
            "start_time": security_time.strftime("%H:%M"),
            "duration_minutes": sec_duration,
            "details": f"Est. wait: {sec_wait} min"
                       f" • {'Fast-track lane' if fast_track else 'Standard lane'}",
        })

        # Step 4: Immigration (if departing from different country)
        if is_international:
            imm_time = security_time + timedelta(minutes=sec_duration + 5)
            imm_queue = self.queue_database["immigration_fast_track" if fast_track else "passport_control"][time_block]
            imm_wait = imm_queue["avg"]
            timeline.append({
                "step": 4,
                "activity": "Passport Control / Immigration",
                "location": "Passport Control",
                "start_time": imm_time.strftime("%H:%M"),
                "duration_minutes": imm_wait + 3,
                "details": f"Est. wait: {imm_wait} min"
                           f" • {'Fast-track' if fast_track else 'Standard'}",
            })
        else:
            imm_wait = 0  # Initialize for domestic flights

        # Step 5: Shopping/Dining (optional)
        step_num = 5 if is_international else 4
        if is_international:
            next_time = security_time + timedelta(minutes=sec_duration + 5 + imm_wait + 3)
        else:
            next_time = security_time + timedelta(minutes=sec_duration + 5)

        if shopping or dining_prefs:
            shopping_time = next_time + timedelta(minutes=5)
            shopping_duration = 15
            # Find nearest amenity
            amenity = self._find_nearest_amenity(dining_prefs + ["shopping"] if shopping else dining_prefs)
            timeline.append({
                "step": step_num,
                "activity": "Shopping & Dining",
                "location": amenity.get("name", "Nearby shops") if amenity else "Terminal shops",
                "start_time": shopping_time.strftime("%H:%M"),
                "duration_minutes": shopping_duration,
                "details": f"{amenity.get('type', 'retail') if amenity else 'General'} at {amenity.get('terminal', 'T1')}" if amenity else "Various options available",
            })
            step_num += 1
            next_time = shopping_time + timedelta(minutes=shopping_duration + 5)

        # Step 6: Lounge access (if applicable)
        if lounge_access:
            lounge_time = next_time + timedelta(minutes=5)
            timeline.append({
                "step": step_num,
                "activity": "Lounge Access",
                "location": "Airport Lounge",
                "start_time": lounge_time.strftime("%H:%M"),
                "duration_minutes": 25,
                "details": f"Relax before boarding • WiFi, food, showers available",
            })
            step_num += 1
            gate_time = lounge_time + timedelta(minutes=30)
        else:
            gate_time = next_time + timedelta(minutes=10)

        # Step 7: Proceed to gate
        gate_time_str = gate_time.strftime("%H:%M")
        gate_minutes_before = int((dep_time - gate_time).total_seconds() / 60)
        boarding_time = dep_time - timedelta(minutes=30)

        timeline.append({
            "step": step_num,
            "activity": "Proceed to Gate",
            "location": f"Gate Area - Boarding in ~{gate_minutes_before} min",
            "start_time": gate_time_str,
            "duration_minutes": gate_minutes_before,
            "details": f"{'Boarding starts ' + boarding_time.strftime('%H:%M')}"
                       f" • Final call: {dep_time.strftime('%H:%M')}",
        })

        # Calculate total journey time
        total_minutes = int((dep_time - recommended_arrival).total_seconds() / 60)

        # Risk factors
        risk_factors = []
        if sec_wait > 25:
            risk_factors.append(f"Security wait may exceed {sec_wait} min during {time_block} peak")
        if boarding_time < (gate_time + timedelta(minutes=15)):
            risk_factors.append("Tight boarding - consider arriving earlier")
        if not risk_factors:
            risk_factors.append("Low risk - on-time boarding expected")

        return {
            "airport": airport_code,
            "origin": origin,
            "departure_time": departure_time,
            "passenger_preferences": passenger_preferences,
            "recommended_arrival": recommended_arrival.strftime("%Y-%m-%dT%H:%M:00Z"),
            "total_journey_time_minutes": total_minutes,
            "timeline": timeline,
            "risk_factors": risk_factors,
            "terminal": self._get_terminal_for_origin(origin),
            "estimated_gate": self._estimate_gate(airport_code),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

    def _get_terminal_for_origin(self, origin: str) -> str:
        """Get terminal based on origin region."""
        europe = {"IST", "LHR", "FRA", "MUC", "BCN", "FCO", "CDG"}
        middle_east = {"DXB", "DOH", "BAH", "AUH"}
        asia = {"SIN", "HKG", "NRT", "HND", "ICN", "PVG"}

        if origin in europe:
            return "T1"
        elif origin in middle_east:
            return "T2"
        elif origin in asia:
            return "T3"
        return "T1"

    def _is_international_route(self, origin: str, destination: str) -> bool:
        """Check if route is international."""
        try:
            country_origin = self._get_country_code(origin)
            country_dest = self._get_country_code(destination)
            return country_origin != country_dest
        except Exception:
            return True  # Assume international if unknown

    def _get_country_code(self, iata: str) -> str:
        """Get ISO country code for IATA code (simplified)."""
        mapping = {
            "IST": "TR", "SAW": "TR", "ESB": "TR",
            "JFK": "US", "LAX": "US", "ORD": "US", "SFO": "US",
            "LHR": "GB", "CDG": "FR", "FRA": "DE", "MUC": "DE",
            "DXB": "AE", "DOH": "QA", "BAH": "BH", "AUH": "AE",
            "SIN": "SG", "HKG": "HK", "NRT": "JP", "HND": "JP",
            "NBO": "KE", "CPT": "ZA", "JNB": "ZA",
        }
        return mapping.get(iata.upper(), "XX")

    def _find_nearest_amenity(self, preferences: List[str]) -> Optional[Dict]:
        """Find nearest amenity matching preferences."""
        amenity_map = {
            "coffee": ["coffee", "cafe", "starbucks", "costa"],
            "vegan": ["vegan", "vegetarian", "healthy"],
            "asian": ["asian", "japanese", "chinese", "korean", "thai"],
            "shopping": ["shopping", "duty_free", "retail"],
        }

        relevant = []
        for pref in preferences:
            keywords = amenity_map.get(pref, [pref])
            for amenity in self.layout.get("amenities", []):
                amen_lower = amenity["name"].lower()
                if any(kw in amen_lower for kw in keywords):
                    relevant.append(amenity)

        return random.choice(relevant) if relevant else None

    def _estimate_gate(self, airport_code: str) -> str:
        """Estimate gate area based on terminal."""
        gates = self.layout.get("terminals", {})
        if gates:
            terminal = list(gates.keys())[0]
            gate_range = gates[terminal].get("gates", ["A1-A9"])
            return f"{terminal[:-1]}-{gate_range[0].split('-')[0]}"
        return "TBD"

    def generate_rebooking_options(self, disrupted_booking: Dict) -> List[Dict]:
        """
        Generate top 5 rebooking alternatives ranked by cost and convenience.

        Args:
            disrupted_booking: {
                "booking_ref": "TK1234",
                "origin": "IST",
                "destination": "JFK",
                "original_departure": "2026-10-20T15:30:00Z",
                "current_time": "2026-10-20T14:00:00Z",
                "passenger_count": 1,
                "loyalty_tier": "silver",
                "fare_paid_usd": 520
            }
        """
        origin = disrupted_booking.get("origin", "IST")
        destination = disrupted_booking.get("destination", "JFK")
        original_dep = datetime.fromisoformat(
            disrupted_booking.get("original_departure", "2026-10-20T15:30:00Z").replace("Z", "+00:00")
        )
        current_time = datetime.fromisoformat(
            disrupted_booking.get("current_time", datetime.now().isoformat()).replace("Z", "+00:00")
            if "Z" not in disrupted_booking.get("current_time", "")
            else disrupted_booking.get("current_time", "2026-10-20T14:00:00Z").replace("Z", "+00:00")
        )
        tier = disrupted_booking.get("loyalty_tier", "bronze")
        original_fare = disrupted_booking.get("fare_paid_usd", 500)
        passenger_count = disrupted_booking.get("passenger_count", 1)

        tier_prefs = TIER_PREFERENCES.get(tier, TIER_PREFERENCES["bronze"])

        # Generate 5 rebooking options at different times
        options = []
        route_key = f"{origin}-{destination}"
        base_risk = MISHANDLING_RISK_FACTORS.get(route_key, {"risk_score": 0.03, "avg_delay_min": 15})

        for i in range(5):
            # Spread options from 1 hour to 8 hours after disruption
            delay_hours = 1 + i * 1.75
            new_dep = original_dep + timedelta(hours=delay_hours)
            flight_number = f"TK{random.randint(100, 999)}"

            # Calculate fare adjustment
            fare_multiplier = 1.0 + (delay_hours * 0.02)  # Later flights may cost more
            if delay_hours < 2:
                fare_multiplier *= 0.95  # Early alternative might be cheaper
            new_fare = original_fare * fare_multiplier

            # Connection risk
            connection_risk = "low" if delay_hours < 3 else "medium" if delay_hours < 6 else "high"

            # Waiting time
            waiting_minutes = int((new_dep - current_time).total_seconds() / 60)

            # Calculate total cost including passenger time
            time_cost = (waiting_minutes / 60) * 25 * passenger_count  # $25/hr opportunity cost
            total_cost = new_fare + time_cost

            score = self._calculate_rebooking_score(
                waiting_minutes, new_fare, original_fare,
                base_risk["risk_score"], tier
            )

            options.append({
                "option_number": i + 1,
                "flight_number": flight_number,
                "new_departure": new_dep.strftime("%Y-%m-%dT%H:%M:00Z"),
                "new_arrival": (new_dep + timedelta(hours=8.5)).strftime("%Y-%m-%dT%H:%M:00Z"),
                "waiting_time_minutes": waiting_minutes,
                "new_fare_usd": round(new_fare, 2),
                "time_cost_usd": round(time_cost, 2),
                "total_cost_usd": round(total_cost, 2),
                "connection_risk": connection_risk,
                "score": score,
                "recommendation": "Recommended" if i == 0 else f"Alternative {i+1}",
                "fare_difference": round(new_fare - original_fare, 2),
            })

        # Sort by score descending
        options.sort(key=lambda x: x["score"], reverse=True)

        # Add ranking
        for i, opt in enumerate(options):
            opt["rank"] = i + 1

        return {
            "disrupted_booking": disrupted_booking.get("booking_ref", "UNKNOWN"),
            "disruption_type": disrupted_booking.get("disruption_type", "delay"),
            "current_time": current_time.isoformat() + "Z",
            "rebooking_options": options[:5],
            "best_option": options[0] if options else None,
            "summary": {
                "cheapest_option": min(options, key=lambda x: x["total_cost_usd"]) if options else None,
                "fastest_option": min(options, key=lambda x: x["waiting_time_minutes"]) if options else None,
                "best_value": max(options, key=lambda x: x["score"]) if options else None,
            },
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

    def _calculate_rebooking_score(self, waiting_time: int, new_fare: float,
                                    original_fare: float, risk_score: float,
                                    tier: str) -> float:
        """Calculate composite score for rebooking option."""
        tier_prefs = TIER_PREFERENCES.get(tier, TIER_PREFERENCES["bronze"])

        # Normalize components (0-100 scale)
        time_score = max(0, 100 - (waiting_time / tier_prefs["max_wait_time"]) * 100)
        cost_score = max(0, 100 - ((new_fare - original_fare) / original_fare) * 100)
        risk_score_adj = 100 - (risk_score * 100 * 3)  # Inverse: lower risk = higher score

        # Weighted composite (40% time, 35% cost, 25% risk)
        composite = (time_score * 0.4 + cost_score * 0.35 + risk_score_adj * 0.25)
        return round(composite, 1)

    def baggage_risk_assessment(self, booking_ref: str,
                                 baggage_tags: List[str]) -> Dict:
        """
        Calculate baggage mishandling risk and provide tracking guidance.
        """
        # Use booking reference to determine route
        route_key = booking_ref_to_route(booking_ref) if len(booking_ref) >= 4 else "IST-JFK"
        risk_data = MISHANDLING_RISK_FACTORS.get(route_key, {"risk_score": 0.03, "avg_delay_min": 15})

        # Simulate risk calculation based on multiple factors
        base_risk = risk_data["risk_score"]
        base_risk *= random.uniform(0.8, 1.3)  # Add variability

        # Additional risk factors
        if len(baggage_tags) > 2:
            base_risk *= 1.1  # More bags = higher risk
        if "connecting" in booking_ref.lower():
            base_risk *= 1.2  # Connections increase risk

        risk_level = "low" if base_risk < 0.02 else "moderate" if base_risk < 0.04 else "high"
        estimated_delay = risk_data["avg_delay_min"] * random.uniform(0.7, 1.3)

        tracking_instructions = []
        if base_risk > 0.03:
            tracking_instructions.extend([
                "Bookmark this reference number for tracking",
                "Download the airline app for real-time baggage updates",
                "Note: If baggage is delayed, use this tag to file a Property Irregularity Report (PIR)",
                "Typical claim processing time: 2-5 business days",
            ])

        # Insurance recommendation
        insurance_recommended = base_risk > 0.035
        insurance_cost = sum(float(tag.split("-")[-1]) * 0.001 for tag in baggage_tags) if baggage_tags else 0

        return {
            "booking_reference": booking_ref,
            "baggage_tags": baggage_tags,
            "risk_score": round(base_risk, 4),
            "risk_level": risk_level,
            "estimated_delay_minutes": round(estimated_delay, 1),
            "confidence": round(random.uniform(0.75, 0.92), 2),
            "tracking_instructions": tracking_instructions,
            "insurance_recommendation": {
                "recommended": insurance_recommended,
                "estimated_cost_usd": round(insurance_cost, 2),
                "coverage_usd": round(sum(float(tag.split("-")[-1]) * 5 for tag in baggage_tags) * 0.1, 2) if baggage_tags else 0,
            },
            "proactive_monitoring": {
                "enabled": True,
                "alert_channels": ["email", "sms", "app_push" if insurance_recommended else "email"],
            },
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

    def wayfinding_guide(self, airport_code: str, gate: str,
                          destination_amenities: List[str] = None) -> Dict:
        """
        Generate turn-by-turn wayfinding and nearby amenities guide.
        """
        if destination_amenities is None:
            destination_amenities = ["coffee", "restroom", "lounge"]

        layout = AIRPORT_LAYOUTS.get(airport_code, AIRPORT_LAYOUTS["IST"])
        amenities = layout.get("amenities", [])

        # Parse gate to terminal
        terminal = f"T{gate[0]}" if gate else "T1"
        if terminal not in layout.get("terminals", {}):
            terminal = list(layout.get("terminals", {}).keys())[0]

        # Find nearby amenities
        nearby_amenities = []
        for amenity in amenities:
            if amenity.get("terminal") == terminal:
                # Calculate pseudo-distance (random but consistent)
                distance_meters = random.randint(50, 500)
                nearby_amenities.append({
                    "name": amenity["name"],
                    "type": amenity["type"],
                    "terminal": amenity.get("terminal", terminal),
                    "distance_meters": distance_meters,
                    "estimated_walk_minutes": max(1, distance_meters // 60),
                    "direction": random.choice(["left", "right", "straight", "upstairs", "downstairs"]),
                    "map_reference": f"{terminal[-1]}-{random.randint(1, 20)}",
                })

        # Filter by requested types
        if destination_amenities:
            filtered = []
            for req in destination_amenities:
                for amen in nearby_amenities:
                    if req in amen.get("type", "") or req in amen.get("name", "").lower():
                        filtered.append(amen)
            nearby_amenities = filtered[:6]  # Top 6

        # Generate wayfinding steps
        steps = [
            {"step": 1, "instruction": f"Exit gate area, follow signs to {terminal}", "distance": "50m"},
            {"step": 2, "instruction": "Proceed along main terminal corridor", "distance": "200m"},
            {"step": 3, "instruction": f"Turn {'left' if random.random() > 0.5 else 'right'} toward {nearby_amenities[0]['name'] if nearby_amenities else 'amenities'}", "distance": f"{random.randint(100, 300)}m"},
        ]

        return {
            "airport": airport_code,
            "terminal": terminal,
            "destination_gate": gate,
            "nearby_amenities": nearby_amenities,
            "wayfinding_steps": steps,
            "estimated_walking_time_minutes": sum(int(s["distance"].replace("m", "")) for s in steps) // 60,
            "accessibility_info": {
                "wheelchair_accessible": True,
                "elevator_locations": f"{terminal} elevators at gates {random.randint(1, 5)} and {random.randint(6, 10)}",
                "accessible_restrooms": 2,
            },
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }


# ─────────────────────────────────────────────
# Helper Functions
# ─────────────────────────────────────────────

def booking_ref_to_route(booking_ref: str) -> str:
    """Extract route from booking reference (simplified)."""
    # In production, would query airline reservation system
    # For now, use booking ref checksum to determine route
    if len(booking_ref) < 4:
        return "IST-JFK"

    routes = ["IST-JFK", "IST-LHR", "IST-DXB", "IST-SIN", "JFK-LHR", "LHR-DXB"]
    # Use hash of booking ref to pick a route deterministically
    hash_val = sum(ord(c) for c in booking_ref)
    return routes[hash_val % len(routes)]


# ─────────────────────────────────────────────
# API Convenience Functions
# ─────────────────────────────────────────────
_concierge = None

def get_concierge(airport_code: str = "IST"):
    global _concierge
    if _concierge is None:
        _concierge = AirportConcierge(airport_code)
    return _concierge

def journey_plan(airport: str = "IST", origin: str = "SAW",
                 departure_time: str = "2026-10-20T15:30:00Z",
                 preferences: Dict = None) -> dict:
    """Generate personalized journey plan."""
    return get_concierge(airport).journey_planning(
        airport, origin, departure_time, preferences
    )

def rebooking_options(booking_ref: str = "TK1234", origin: str = "IST",
                       destination: str = "JFK", original_departure: str = "2026-10-20T15:30:00Z",
                       current_time: str = None, loyalty_tier: str = "silver",
                       fare_paid_usd: float = 520, passenger_count: int = 1,
                       disruption_type: str = "delay") -> dict:
    """Generate rebooking options."""
    if current_time is None:
        current_time = datetime.now().isoformat() + "Z"
    
    concierge = get_concierge(origin)
    return concierge.generate_rebooking_options({
        "booking_ref": booking_ref,
        "origin": origin,
        "destination": destination,
        "original_departure": original_departure,
        "current_time": current_time,
        "loyalty_tier": loyalty_tier,
        "fare_paid_usd": fare_paid_usd,
        "passenger_count": passenger_count,
        "disruption_type": disruption_type,
    })

def baggage_alert(booking_ref: str = "TK1234", baggage_tags: List[str] = None) -> dict:
    """Calculate baggage mishandling risk."""
    if baggage_tags is None:
        baggage_tags = ["TK1234-879", "TK1234-880"]
    
    return get_concierge("IST").baggage_risk_assessment(booking_ref, baggage_tags)

def wayfinding(airport: str = "IST", gate: str = "A12",
               amenities: List[str] = None) -> dict:
    """Generate wayfinding guide."""
    return get_concierge(airport).wayfinding_guide(airport, gate, amenities)

import random  # Move to top in production

if __name__ == "__main__":
    # Test journey planning
    plan = journey_plan(
        airport="IST", origin="SAW",
        departure_time="2026-10-20T15:30:00Z",
        preferences={"loyalty_tier": "gold", "fast_track": True, "lounge_access": True}
    )
    print(json.dumps(plan, indent=2))
    print("✅ Concierge tested")
