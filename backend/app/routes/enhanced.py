"""
Enhanced API routes with live aviation data and optimization modules.
"""

from flask import Blueprint, request, jsonify
import json

# Import the enhanced prediction function
from ..services.ml_engine_enhanced import predict_with_live_data, get_system_status

# NEW: Import optimization modules
from ..services.turnaround_optimizer import optimize_turnaround
from ..services.gse_optimizer import (
    get_fleet_status,
    get_idle_equipment,
    get_maintenance_alerts,
    optimize_gse_allocation,
    get_utilization_report,
)
from ..services.route_optimizer import calculate_route_optimization
from ..services.passenger_flow_forecaster import forecast_passenger_flows
from ..services.crew_scheduler import resolve_crew_conflict

enhanced_bp = Blueprint("enhanced", __name__)

@enhanced_bp.route("/predict/live", methods=["POST"])
def predict_flight_live():
    """
    Enhanced prediction endpoint with real-time weather data.
    Uses the same input format as /api/predict but adds live weather integration.
    """
    data = request.get_json(force=True)

    required = [
        "flight_number", "dep_airport", "arr_airport",
        "airline", "date", "dep_time"
    ]
    missing = [k for k in required if not data.get(k)]
    if missing:
        return jsonify({
            "error": f"Missing fields: {', '.join(missing)}"
        }), 400

    try:
        result = predict_with_live_data(
            flight_number=data["flight_number"],
            dep_airport=data["dep_airport"],
            arr_airport=data["arr_airport"],
            airline=data["airline"],
            date_str=data["date"],
            dep_time=data["dep_time"],
        )
        return jsonify({
            "success": True,
            "data": result,
            "enhanced": True,
            "data_sources": ["noaa_aviation_weather", "opensky_network"]
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "error": f"Enhanced prediction failed: {str(e)[:200]}"
        }), 500

@enhanced_bp.route("/system/status", methods=["GET"])
def system_status():
    """
    Get system status including live data source health.
    """
    try:
        status = get_system_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({
            "error": str(e),
            "model": {"trained": False}
        }), 500

# ============================================================
# NEW: Turnaround Optimization Endpoints
# ============================================================

@enhanced_bp.route("/turnaround/plan", methods=["POST"])
def turnaround_plan():
    """
    Generate optimized turnaround plan for an aircraft.
    
    Request Body:
    {
        "flight_number": "TK1988",
        "dep_airport": "IST",
        "arr_airport": "JFK",
        "airline": "TK",
        "date": "2026-10-20",
        "dep_time": "14:30",
        "aircraft_type": "narrow_body",
        "crew_count": 5
    }
    """
    data = request.get_json(force=True, silent=True) or {}
    
    try:
        result = optimize_turnaround(
            flight_number=data.get("flight_number", "TK1988"),
            dep_airport=data.get("dep_airport", "IST"),
            arr_airport=data.get("arr_airport", "JFK"),
            airline=data.get("airline", "TK"),
            date_str=data.get("date", ""),
            dep_time=data.get("dep_time", "14:30"),
            aircraft_type=data.get("aircraft_type", "narrow_body"),
            crew_count=data.get("crew_count", 5)
        )
        
        return jsonify({"success": True, "data": result})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

# ============================================================
# NEW: GSE Tracking Endpoints
# ============================================================

@enhanced_bp.route("/gse/status", methods=["GET"])
def gse_fleet_status():
    """Get current GSE fleet status and utilization metrics."""
    try:
        status = get_fleet_status()
        return jsonify({"success": True, "data": status})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@enhanced_bp.route("/gse/idle", methods=["GET"])
def gse_idle_detection():
    """Identify idle GSE equipment wasting resources."""
    try:
        threshold = int(request.args.get("threshold_minutes", 60))
        idle = get_idle_equipment(threshold_minutes=threshold)
        return jsonify({"success": True, "data": idle})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@enhanced_bp.route("/gse/maintenance", methods=["GET"])
def gse_maintenance_alerts():
    """Get predictive maintenance alerts for GSE fleet."""
    try:
        alerts = get_maintenance_alerts()
        return jsonify({"success": True, "data": alerts})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@enhanced_bp.route("/gse/optimize", methods=["POST"])
def gse_optimize_endpoint():
    """Optimize GSE allocation based on flight schedule."""
    data = request.get_json(force=True, silent=True) or {}
    
    if "flight_schedule" not in data:
        return jsonify({
            "success": False,
            "error": "Missing 'flight_schedule' in request body",
            "example": {
                "flight_schedule": [
                    {"flight_id": "TK1988", "equipment": ["belt_loader", "fuel_truck"]}
                ]
            }
        }), 400
    
    try:
        result = optimize_gse_allocation(data["flight_schedule"])
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@enhanced_bp.route("/gse/report", methods=["GET"])
def gse_utilization_report():
    """Generate comprehensive GSE utilization report."""
    try:
        report = get_utilization_report()
        return jsonify({"success": True, "data": report})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============================================================
# NEW: Baggage Handling Prediction
# ============================================================

@enhanced_bp.route("/baggage/risk", methods=["GET"])
def baggage_risk_prediction():
    """
    Predict baggage handling risks for a flight.
    
    Query Parameters:
    - flight_number: Flight identifier (e.g., TK1988)
    - dep_airport: Departure airport code
    - arr_airport: Arrival airport code
    """
    try:
        flight_number = request.args.get("flight_number", "TK1988")
        dep_airport = request.args.get("dep_airport", "IST")
        arr_airport = request.args.get("arr_airport", "JFK")
        
        # Import weather severity for risk calculation
        from ..services.aviation_data_service import get_airport_weather_severity
        
        risk_factors = []
        risk_score = 0
        
        # Weather impact
        dep_icao = dep_airport if len(dep_airport) == 4 else "LTBA"
        try:
            weather_severity = get_airport_weather_severity(dep_icao)
            if weather_severity > 7:
                risk_factors.append(f"Severe weather at {dep_airport}")
                risk_score += 25
            elif weather_severity > 4:
                risk_factors.append(f"Moderate weather at {dep_airport}")
                risk_score += 10
        except:
            weather_severity = 5
        
        # International flight complexity
        if len(arr_airport) == 3 and arr_airport != "IST":
            risk_factors.append("International transfer complexity")
            risk_score += 15
        
        return jsonify({
            "success": True,
            "data": {
                "flight_number": flight_number,
                "risk_score": min(risk_score, 100),
                "risk_level": "high" if risk_score > 40 else "medium" if risk_score > 20 else "low",
                "risk_factors": risk_factors,
                "estimated_delay_minutes": risk_score * 2,
                "recommendations": [
                    "Assign priority baggage handling team" if risk_score > 30 else "Standard handling sufficient",
                    "Monitor carousel assignment closely" if risk_score > 25 else "Routine carousel monitoring",
                ],
                "timestamp": json.dumps({"__type__": "datetime"})
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============================================================
# NEW: Route Optimization Endpoints
# ============================================================

@enhanced_bp.route("/route/optimize", methods=["POST"])
def route_optimization():
    """
    Calculate optimal flight route with fuel, altitude, and delay analysis.
    """
    data = request.get_json(force=True, silent=True) or {}
    
    try:
        result = calculate_route_optimization(
            flight_number=data.get("flight_number", "TK1988"),
            dep_airport=data.get("dep_airport", "IST"),
            arr_airport=data.get("arr_airport", "JFK"),
            airline=data.get("airline", "TK"),
            date_str=data.get("date", ""),
            dep_time=data.get("dep_time", "14:30"),
            aircraft_type=data.get("aircraft_type", "narrow_body")
        )
        
        return jsonify({"success": True, "data": result})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

# ============================================================
# NEW: Crew Scheduling Endpoints
# ============================================================

@enhanced_bp.route("/crew/resolve", methods=["POST"])
def crew_resolve_conflict():
    """
    Resolve crew scheduling conflict and find replacement crews.
    
    Request Body:
    {
        "flight_number": "TK1988",
        "dep_airport": "IST",
        "arr_airport": "JFK",
        "date": "2026-10-20",
        "dep_time": "14:30",
        "arr_time": "18:45",
        "aircraft_type": "narrow_body",
        "crew_requirements": {"captain": 1, "first_officer": 1, "flight_attendant": 4}
    }
    """
    data = request.get_json(force=True, silent=True) or {}
    
    try:
        crew_reqs = data.get("crew_requirements", {"captain": 1, "first_officer": 1, "flight_attendant": 4})
        
        result = resolve_crew_conflict(
            flight_number=data.get("flight_number", "TK1988"),
            dep_airport=data.get("dep_airport", "IST"),
            arr_airport=data.get("arr_airport", "JFK"),
            date_str=data.get("date", ""),
            dep_time=data.get("dep_time", "14:30"),
            arr_time=data.get("arr_time", "18:45"),
            aircraft_type=data.get("aircraft_type", "narrow_body"),
            crew_count=crew_reqs
        )
        
        return jsonify({"success": True, "data": result})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500
# ============================================================

@enhanced_bp.route("/passenger/flow", methods=["POST"])
def passenger_flow_forecast():
    """
    Forecast passenger flow through airport processes (check-in, security, baggage).
    """
    data = request.get_json(force=True, silent=True) or {}
    
    try:
        result = forecast_passenger_flows(
            airport=data.get("airport", "IST"),
            date=data.get("date", ""),
            total_passengers=data.get("total_passengers", 45000),
            check_in_lanes=data.get("check_in_lanes", 20),
            security_lanes=data.get("security_lanes", 8),
            fast_track_lanes=data.get("fast_track_lanes", 2),
            carousels=data.get("carousels", 4),
            self_service_ratio=data.get("self_service_ratio", 0.4)
        )
        
        return jsonify({"success": True, "data": result})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500
