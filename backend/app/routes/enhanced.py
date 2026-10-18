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
from ..services.carbon_compliance import (
    calculate_carbon_footprint,
    calculate_corsia_compliance,
)
from ..services.fleet_scheduler import generate_fleet_schedule
from ..services.airport_slot_manager import allocate_airport_slots
from ..services.cargo_optimizer import (
    optimize_cargo_flight as _optimize_cargo,
    forecast_cargo_terminal as _forecast_cargo,
    generate_cargo_revenue_report as _revenue_report,
)
from ..services.maintenance_planner import (
    predict_maintenance_for_aircraft,
    schedule_fleet_maintenance,
)
from ..services.weather_analyzer import (
    get_weather_report,
    calculate_wind_optimization,
    get_live_aircraft_traffic,
)
from ..services.capacity_optimizer import (
    optimize_gate_allocation as _optimize_gates,
    optimize_security_lanes as _optimize_security,
    optimize_retail as _optimize_retail,
    optimize_baggage as _optimize_baggage,
    get_airport_capacity_report as _capacity_report,
)
from ..services.ground_ops_scheduler import (
    optimize_turnaround as _optimize_turnaround,
    schedule_ground_crew as _schedule_crew,
    allocate_gse as _allocate_gse,
    optimize_fuel_dispatch as _optimize_fuel,
    comprehensive_ground_ops_report as _ground_ops_report,
)
from ..services.cargo_revenue_manager import (
    get_dynamic_price as _dynamic_price,
    allocate_cargo_capacity as _allocate_cargo,
    forecast_cargo_demand as _forecast_demand,
    optimize_booking_classes as _optimize_booking,
)
from ..services.fuel_manager import (
    forecast_fuel_prices as _forecast_fuel,
    recommend_fuel_hedge as _hedge_recommend,
    optimize_fuel_loading as _optimize_fuel_loading,
    track_fuel_costs as _track_fuel,
)
from ..services.flight_ops_decision import (
    go_nogo_decision as _go_nogo,
    optimize_flight_level as _optimize_flight_level,
    comprehensive_flight_ops_report as _flight_ops_report,
)
from ..services.safety_manager import (
    assess_safety_risk as _assess_risk,
    assess_fatigue_risk as _assess_fatigue,
    assess_runway_risk as _assess_runway,
    generate_safety_report as _safety_report,
)
from ..services.quality_manager import (
    calculate_quality_score as _quality_score,
    sla_compliance_report as _sla_report,
    root_cause_analysis as _root_cause,
    generate_quality_report as _quality_report,
)
from ..services.revenue_analytics import (
    calculate_clv as _calc_clv,
    optimize_ancillaries as _optimize_ancillaries,
    route_profitability as _route_profit,
    campaign_analysis as _campaign_analysis,
    revenue_report as _revenue_report,
)
from ..services.fuel_cost_analytics import (
    analyze_fuel_costs as _analyze_fuel_costs,
    calculate_casm as _calculate_casm,
    track_fuel_variance as _track_variance,
    emissions_report as _emissions_report,
    tankering_analysis as _tankering_analysis,
)
from ..services.concierge import (
    journey_plan as _journey_plan,
    rebooking_options as _rebooking_options,
    baggage_alert as _baggage_alert,
    wayfinding as _wayfinding,
)
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

# ============================================================
# NEW: Carbon Compliance Endpoints
# ============================================================

@enhanced_bp.route("/carbon/footprint", methods=["GET"])
def carbon_footprint():
    """
    Calculate carbon footprint for a flight.
    
    Query Parameters:
    - flight_number: Flight identifier
    - dep_airport: Departure airport
    - arr_airport: Arrival airport
    - aircraft_type: Aircraft model (default: A320)
    - passengers: Passenger count (default: 150)
    - date: Date YYYY-MM-DD (optional)
    """
    try:
        result = calculate_carbon_footprint(
            flight_number=request.args.get("flight_number", "TK1988"),
            dep_airport=request.args.get("dep_airport", "IST"),
            arr_airport=request.args.get("arr_airport", "JFK"),
            aircraft_type=request.args.get("aircraft_type", "A320"),
            passengers=int(request.args.get("passengers", 150)),
            date_str=request.args.get("date", ""),
        )
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@enhanced_bp.route("/carbon/corsia", methods=["GET"])
def carbon_corsia():
    """
    Calculate CORSIA compliance costs and requirements.
    
    Query Parameters:
    - flight_number: Flight identifier
    - dep_airport: Departure airport
    - arr_airport: Arrival airport
    - aircraft_type: Aircraft model (default: A320)
    - passengers: Passenger count (default: 150)
    - date: Date YYYY-MM-DD (optional)
    """
    try:
        result = calculate_corsia_compliance(
            flight_number=request.args.get("flight_number", "TK1988"),
            dep_airport=request.args.get("dep_airport", "IST"),
            arr_airport=request.args.get("arr_airport", "JFK"),
            date_str=request.args.get("date", ""),
            aircraft_type=request.args.get("aircraft_type", "A320"),
            passengers=int(request.args.get("passengers", 150)),
        )
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============================================================
# NEW: Airport Slot Management Endpoints
# ============================================================

@enhanced_bp.route("/slots/allocate", methods=["POST"])
def slot_allocation():
    """
    Allocate airport slots based on airline requests.
    """
    data = request.get_json(force=True, silent=True) or {}
    
    try:
        result = allocate_airport_slots(
            airport=data.get("airport", "IST"),
            request_count=data.get("request_count", 30),
            capacity=data.get("capacity_per_hour", 40)
        )
        
        return jsonify({"success": True, "data": result})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

# ============================================================
# NEW: Cargo Handling Endpoints
# ============================================================

@enhanced_bp.route("/cargo/optimize", methods=["POST"])
def cargo_flight_optimization():
    """Optimize cargo flight for a shipment."""
    data = request.get_json(force=True, silent=True) or {}
    
    try:
        result = _optimize_cargo(
            shipment_id=data.get("shipment_id", "SHP001"),
            origin=data.get("origin", "IST"),
            destination=data.get("destination", "JFK"),
            weight_tonnes=data.get("weight_tonnes", 25.0),
            volume_cbm=data.get("volume_cbm", 150.0),
            cargo_type=data.get("cargo_type", "general"),
            priority=data.get("priority", "normal"),
        )
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@enhanced_bp.route("/cargo/terminal", methods=["GET"])
def cargo_terminal_forecast():
    """Forecast cargo terminal capacity utilization."""
    try:
        terminal_type = request.args.get("terminal_type", "large")
        result = _forecast_cargo(terminal_type)
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@enhanced_bp.route("/cargo/revenue", methods=["POST"])
def cargo_revenue_report():
    """Generate cargo revenue optimization report."""
    data = request.get_json(force=True, silent=True) or {}
    
    try:
        routes = data.get("routes", None)
        result = _revenue_report(routes if routes else None)
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============================================================
# NEW: Maintenance Planning Endpoints
# ============================================================

@enhanced_bp.route("/maintenance/predict", methods=["GET"])
def maintenance_prediction():
    """
    Predict maintenance needs for an aircraft.
    """
    try:
        result = predict_maintenance_for_aircraft(
            registration=request.args.get("registration", "TC-001"),
            model=request.args.get("model", "A320"),
            flight_hours=float(request.args.get("flight_hours", 5500)),
            flight_cycles=int(request.args.get("flight_cycles", 3200)),
            days_since_new=int(request.args.get("days_since_new", 500)),
        )
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@enhanced_bp.route("/maintenance/schedule", methods=["POST"])
def maintenance_schedule():
    """
    Schedule fleet-wide maintenance with hangar capacity constraints.
    """
    data = request.get_json(force=True, silent=True) or {}
    
    try:
        result = schedule_fleet_maintenance(
            fleet_size=data.get("fleet_size", 10)
        )
        return jsonify({"success": True, "data": result})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

# ============================================================
# NEW: Weather Analysis Endpoints
# ============================================================

@enhanced_bp.route("/weather/report", methods=["GET"])
def weather_report():
    """
    Get comprehensive weather report for an airport.
    """
    try:
        result = get_weather_report(
            airport=request.args.get("airport", "IST"),
            date_str=request.args.get("date", None)
        )
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@enhanced_bp.route("/weather/fuel-optimization", methods=["GET"])
def weather_fuel_optimization():
    """
    Calculate fuel optimization based on wind patterns.
    """
    try:
        result = calculate_wind_optimization(
            origin=request.args.get("origin", "IST"),
            destination=request.args.get("destination", "JFK"),
            date_str=request.args.get("date", None)
        )
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@enhanced_bp.route("/weather/live-traffic", methods=["GET"])
def weather_live_traffic():
    """
    Get live aircraft traffic from OpenSky Network.
    """
    try:
        limit = int(request.args.get("limit", 5))
        result = get_live_aircraft_traffic(limit=limit)
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============================================================
# NEW: Airport Capacity Optimization Endpoints
# ============================================================

@enhanced_bp.route("/capacity/gate-allocation", methods=["POST"])
def capacity_gate_allocation():
    """
    Optimize gate allocation for a set of flights.
    """
    data = request.get_json(force=True, silent=True) or {}
    try:
        result = _optimize_gates(
            data.get("flights", []),
            airport=data.get("airport", "IST"),
            include_remote=data.get("include_remote", True)
        )
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@enhanced_bp.route("/capacity/security-lanes", methods=["POST"])
def capacity_security_lanes():
    """
    Optimize security lane allocation across time blocks.
    """
    data = request.get_json(force=True, silent=True) or {}
    try:
        result = _optimize_security(
            data.get("passenger_flows", {"AM": 15000, "MID": 12000, "PM": 18000}),
            data.get("time_blocks", ["AM", "MID", "PM"]),
            airport=data.get("airport", "IST")
        )
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@enhanced_bp.route("/capacity/retail", methods=["POST"])
def capacity_retail():
    """
    Optimize retail/concession space allocation.
    """
    data = request.get_json(force=True, silent=True) or {}
    try:
        result = _optimize_retail(
            data.get("area_sqft", 50000),
            data.get("passenger_traffic", {"T1": 25000, "T2": 15000}),
            airport=data.get("airport", "IST")
        )
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@enhanced_bp.route("/capacity/baggage", methods=["POST"])
def capacity_baggage():
    """
    Optimize baggage handling for assigned flights.
    """
    data = request.get_json(force=True, silent=True) or {}
    try:
        result = _optimize_baggage(
            data.get("flights", []),
            airport=data.get("airport", "IST")
        )
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@enhanced_bp.route("/capacity/report", methods=["GET"])
def capacity_report():
    """
    Get comprehensive airport capacity report.
    """
    try:
        result = _capacity_report(
            airport=request.args.get("airport", "IST")
        )
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============================================================
# NEW: Ground Operations Endpoints
# ============================================================

@enhanced_bp.route("/ops/turnaround", methods=["GET"])
def ops_turnaround():
    """
    Optimize turnaround for an aircraft type.
    """
    try:
        result = _optimize_turnaround(
            aircraft_type=request.args.get("aircraft_type", "A320"),
            target_minutes=int(request.args.get("target_minutes", 45))
        )
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@enhanced_bp.route("/ops/crew-schedule", methods=["POST"])
def ops_crew_schedule():
    """
    Generate ground crew shift schedule.
    """
    data = request.get_json(force=True, silent=True) or {}
    try:
        result = _schedule_crew(
            date=data.get("date", None)
        )
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@enhanced_bp.route("/ops/gse", methods=["POST"])
def ops_gse():
    """
    Allocate ground support equipment.
    """
    data = request.get_json(force=True, silent=True) or {}
    try:
        result = _allocate_gse(
            flight_count=data.get("flight_count", 50),
            operating_hours=data.get("operating_hours", 16)
        )
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@enhanced_bp.route("/ops/fuel-dispatch", methods=["POST"])
def ops_fuel_dispatch():
    """
    Optimize fuel truck dispatch.
    """
    data = request.get_json(force=True, silent=True) or {}
    try:
        result = _optimize_fuel(
            data.get("flights", [])
        )
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@enhanced_bp.route("/ops/report", methods=["POST"])
def ops_report():
    """
    Generate comprehensive ground operations report.
    """
    data = request.get_json(force=True, silent=True) or {}
    try:
        result = _ground_ops_report(
            date=data.get("date", None)
        )
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============================================================
# NEW: Cargo Revenue Management Endpoints
# ============================================================

@enhanced_bp.route("/cargo/price", methods=["GET"])
def cargo_dynamic_price():
    """
    Get dynamic pricing for a cargo shipment.
    """
    try:
        result = _dynamic_price(
            route=request.args.get("route", "IST-JFK"),
            demand_level=request.args.get("demand_level", "medium"),
            days_to_departure=int(request.args.get("days_to_departure", 7)),
            booking_class=request.args.get("booking_class", "Y")
        )
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@enhanced_bp.route("/cargo/demand-forecast", methods=["GET"])
def cargo_demand_forecast():
    """
    Forecast cargo demand for a route.
    """
    try:
        result = _forecast_demand(
            route=request.args.get("route", "IST-JFK"),
            date_str=request.args.get("date", None)
        )
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@enhanced_bp.route("/cargo/booking-classes", methods=["POST"])
def cargo_booking_classes():
    """
    Optimize booking class allocation for a route.
    """
    data = request.get_json(force=True, silent=True) or {}
    try:
        result = _optimize_booking(
            route=data.get("route", "IST-JFK"),
            capacity_kg=data.get("capacity_kg", 100000)
        )
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@enhanced_bp.route("/cargo/allocate", methods=["POST"])
def cargo_allocate():
    """
    Optimize cargo capacity allocation across flights.
    """
    data = request.get_json(force=True, silent=True) or {}
    try:
        result = _allocate_cargo(
            data.get("flights", []),
            data.get("bookings", [])
        )
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============================================================
# NEW: Fuel Management Endpoints
# ============================================================

@enhanced_bp.route("/fuel/price-forecast", methods=["GET"])
def fuel_price_forecast():
    """
    Forecast jet fuel prices for an airport.
    """
    try:
        result = _forecast_fuel(
            airport=request.args.get("airport", "IST"),
            days=int(request.args.get("days", 30))
        )
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@enhanced_bp.route("/fuel/hedge", methods=["GET", "POST"])
def fuel_hedge():
    """
    Recommend fuel hedging strategy.
    """
    try:
        if request.method == "GET":
            airport = request.args.get("airport", "IST")
            volume = float(request.args.get("monthly_volume", 500000))
        else:
            data = request.get_json(force=True, silent=True) or {}
            airport = data.get("airport", "IST")
            volume = float(data.get("monthly_volume", 500000))
        
        result = _hedge_recommend(airport, volume)
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@enhanced_bp.route("/fuel/optimize-loading", methods=["GET"])
def fuel_optimize_loading():
    """
    Optimize fuel loading for a flight.
    """
    try:
        result = _optimize_fuel_loading(
            origin=request.args.get("origin", "IST"),
            destination=request.args.get("destination", "JFK"),
            aircraft_type=request.args.get("aircraft_type", "A320"),
            distance_nm=float(request.args.get("distance_nm", 0)) or None
        )
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@enhanced_bp.route("/fuel/cost-tracking", methods=["POST"])
def fuel_cost_tracking():
    """
    Track actual vs planned fuel costs.
    """
    data = request.get_json(force=True, silent=True) or {}
    try:
        result = _track_fuel(data.get("flights", []))
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============================================================
# NEW: Flight Ops Decision Support Endpoints
# ============================================================

@enhanced_bp.route("/ops/go-nogo", methods=["GET"])
def ops_go_nogo():
    """
    Make GO/NO-GO decision based on weather at destination.
    """
    try:
        result = _go_nogo(
            destination=request.args.get("destination", "IST"),
            visibility=float(request.args.get("visibility", 3200)),
            ceiling=float(request.args.get("ceiling", 1000)),
            approach_type=request.args.get("approach_type", "CAT1")
        )
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@enhanced_bp.route("/ops/flight-level", methods=["GET"])
def ops_flight_level():
    """
    Optimize flight level for wind advantage.
    """
    try:
        result = _optimize_flight_level(
            origin=request.args.get("origin", "IST"),
            destination=request.args.get("destination", "JFK"),
            aircraft_type=request.args.get("aircraft_type", "A320")
        )
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@enhanced_bp.route("/ops/flight-report", methods=["GET"])
def ops_flight_report():
    """
    Comprehensive flight operations report.
    """
    try:
        result = _flight_ops_report(
            origin=request.args.get("origin", "IST"),
            destination=request.args.get("destination", "JFK"),
            aircraft_type=request.args.get("aircraft_type", "A320")
        )
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============================================================
# NEW: Safety & Risk Management Endpoints
# ============================================================

@enhanced_bp.route("/safety/risk-assessment", methods=["GET", "POST"])
def safety_risk_assessment():
    """
    Perform risk assessment on identified hazards.
    """
    try:
        if request.method == "GET":
            hazards = [
                {"category": "weather", "hazard": "wind_shear", "likelihood": "occasional",
                 "severity": "high", "mitigation": "wind_shear_detection"},
            ]
        else:
            data = request.get_json(force=True, silent=True) or {}
            hazards = data.get("hazards", [])
        
        result = _assess_risk(hazards)
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@enhanced_bp.route("/safety/fatigue", methods=["GET", "POST"])
def safety_fatigue():
    """
    Assess fatigue risk for flight crew.
    """
    try:
        if request.method == "GET":
            pilot_data = {
                "flight_hours_24h": 8,
                "flight_hours_7d": 30,
                "night_flights_28d": 3,
                "early_starts_7d": 5,
                "consecutive_days": 4,
                "time_zones": 2,
            }
        else:
            data = request.get_json(force=True, silent=True) or {}
            pilot_data = data.get("pilot_data", {})
        
        result = _assess_fatigue(pilot_data)
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@enhanced_bp.route("/safety/runway-risk", methods=["GET"])
def safety_runway_risk():
    """
    Assess runway excursion risk during landing.
    """
    try:
        result = _assess_runway(
            runway_condition=request.args.get("runway_condition", "wet"),
            aircraft_weight=request.args.get("aircraft_weight", "medium"),
            landing_speed=float(request.args.get("landing_speed", 130)),
            pilot_experience=request.args.get("pilot_experience", "experienced")
        )
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@enhanced_bp.route("/safety/report", methods=["GET"])
def safety_report():
    """
    Generate comprehensive safety report.
    """
    try:
        result = _safety_report(
            flight_count=int(request.args.get("flight_count", 100)),
            route=request.args.get("route", "IST-JFK")
        )
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============================================================
# NEW: Ground Handling Quality Endpoints
# ============================================================

@enhanced_bp.route("/quality/score", methods=["POST"])
def quality_score():
    """
    Calculate service quality score from events.
    """
    data = request.get_json(force=True, silent=True) or {}
    try:
        result = _quality_score(data.get("events", []))
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@enhanced_bp.route("/quality/sla", methods=["POST"])
def quality_sla():
    """
    Generate SLA compliance report.
    """
    data = request.get_json(force=True, silent=True) or {}
    try:
        result = _sla_report(data.get("events", []))
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@enhanced_bp.route("/quality/root-cause", methods=["POST"])
def quality_root_cause():
    """
    Perform root cause analysis on delay reasons.
    """
    data = request.get_json(force=True, silent=True) or {}
    try:
        result = _root_cause(data.get("delay_reasons", {}))
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@enhanced_bp.route("/quality/report", methods=["GET"])
def quality_report():
    """
    Generate comprehensive quality report.
    """
    try:
        result = _quality_report(
            flight_count=int(request.args.get("flight_count", 100)),
            date_range=request.args.get("date_range", "last_30_days")
        )
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============================================================
# NEW: Revenue Analytics Endpoints
# ============================================================

@enhanced_bp.route("/revenue/clv", methods=["GET"])
def revenue_clv():
    """
    Calculate Customer Lifetime Value.
    """
    try:
        result = _calc_clv(
            segment=request.args.get("segment", "frequent_business"),
            tenure=int(request.args.get("tenure", 24)),
            bookings=int(request.args.get("bookings", 4))
        )
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@enhanced_bp.route("/revenue/ancillaries", methods=["GET", "POST"])
def revenue_ancillaries():
    """
    Optimize ancillary revenue.
    """
    try:
        if request.method == "GET":
            bookings = int(request.args.get("bookings", 10000))
            segment = request.args.get("segment", "mixed")
        else:
            data = request.get_json(force=True, silent=True) or {}
            bookings = int(data.get("bookings", 10000))
            segment = data.get("segment", "mixed")
        
        result = _optimize_ancillaries(bookings, segment)
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@enhanced_bp.route("/revenue/routes", methods=["GET"])
def revenue_routes():
    """
    Analyze route profitability.
    """
    try:
        routes = request.args.get("routes", "").split(",") if request.args.get("routes") else None
        result = _route_profit(
            routes=routes if routes and routes != [""] else None,
            period=request.args.get("period", "monthly")
        )
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@enhanced_bp.route("/revenue/campaign", methods=["GET"])
def revenue_campaign():
    """
    Analyze marketing campaign ROI.
    """
    try:
        result = _campaign_analysis(
            campaign_type=request.args.get("campaign_type", "email_marketing"),
            audience=int(request.args.get("audience", 10000)),
            budget=float(request.args.get("budget", 5000))
        )
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@enhanced_bp.route("/revenue/report", methods=["GET"])
def revenue_summary():
    """
    Generate comprehensive revenue report.
    """
    try:
        result = _revenue_report()
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============================================================
# NEW: Fuel Cost Analytics Endpoints
# ============================================================

@enhanced_bp.route("/fuel/analysis", methods=["POST"])
def fuel_analysis():
    """
    Analyze fuel costs across fleet flights.
    """
    data = request.get_json(force=True, silent=True) or {}
    try:
        result = _analyze_fuel_costs(data.get("flights", []))
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@enhanced_bp.route("/fuel/casm", methods=["GET"])
def fuel_casm():
    """
    Calculate Cost per Available Seat Mile (CASM).
    """
    try:
        result = _calculate_casm(
            total_costs=float(request.args.get("total_costs", 50000)),
            asm=float(request.args.get("asm", 500000)),
            flight_count=int(request.args.get("flight_count", 10))
        )
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@enhanced_bp.route("/fuel/variance", methods=["GET"])
def fuel_variance():
    """
    Track fuel burn variance for operational insights.
    """
    try:
        result = _track_variance(
            planned=float(request.args.get("planned", 5000)),
            actual=float(request.args.get("actual", 5200)),
            distance=float(request.args.get("distance", 2000)),
            aircraft=request.args.get("aircraft", "A320")
        )
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@enhanced_bp.route("/fuel/emissions", methods=["POST"])
def fuel_emissions():
    """
    Generate emissions tracking report.
    """
    data = request.get_json(force=True, silent=True) or {}
    try:
        result = _emissions_report(
            data.get("flights", []),
            data.get("period", "monthly")
        )
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@enhanced_bp.route("/fuel/tankering", methods=["GET"])
def fuel_tankering():
    """
    Analyze tankering fuel economics.
    """
    try:
        result = _tankering_analysis(
            origin=request.args.get("origin", "IST"),
            destination=request.args.get("destination", "JFK"),
            aircraft_type=request.args.get("aircraft_type", "A320")
        )
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============================================================
# NEW: AI Concierge Endpoints
# ============================================================

@enhanced_bp.route("/concierge/journey", methods=["GET"])
def concierge_journey():
    """
    Generate personalized journey plan for passenger.
    """
    try:
        preferences = {
            "loyalty_tier": request.args.get("loyalty_tier", "bronze"),
            "fast_track": request.args.get("fast_track", "false").lower() == "true",
            "lounge_access": request.args.get("lounge_access", "false").lower() == "true",
            "shopping": request.args.get("shopping", "false").lower() == "true",
            "dining_preferences": request.args.get("dining_preferences", "").split(",") if request.args.get("dining_preferences") else [],
        }
        result = _journey_plan(
            airport=request.args.get("airport", "IST"),
            origin=request.args.get("origin", "SAW"),
            departure_time=request.args.get("departure_time", "2026-10-20T15:30:00Z"),
            preferences=preferences
        )
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@enhanced_bp.route("/concierge/rebook", methods=["POST"])
def concierge_rebook():
    """
    Generate rebooking options for disrupted passengers.
    """
    data = request.get_json(force=True, silent=True) or {}
    try:
        from datetime import datetime as dt
        result = _rebooking_options(
            booking_ref=data.get("booking_ref", "TK1234"),
            origin=data.get("origin", "IST"),
            destination=data.get("destination", "JFK"),
            original_departure=data.get("original_departure", "2026-10-20T15:30:00Z"),
            current_time=data.get("current_time", dt.now().isoformat() + "Z"),
            loyalty_tier=data.get("loyalty_tier", "silver"),
            fare_paid_usd=data.get("fare_paid_usd", 520),
            passenger_count=data.get("passenger_count", 1),
            disruption_type=data.get("disruption_type", "delay")
        )
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@enhanced_bp.route("/concierge/baggage", methods=["GET"])
def concierge_baggage():
    """
    Get baggage mishandling risk assessment.
    """
    try:
        tags = request.args.get("tags", "TK1234-879,TK1234-880").split(",")
        result = _baggage_alert(
            booking_ref=request.args.get("booking_ref", "TK1234"),
            baggage_tags=tags
        )
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@enhanced_bp.route("/concierge/wayfinding", methods=["GET"])
def concierge_wayfinding():
    """
    Get wayfinding guide and nearby amenities.
    """
    try:
        amenities = request.args.get("amenities", "coffee,lounge").split(",") if request.args.get("amenities") else None
        result = _wayfinding(
            airport=request.args.get("airport", "IST"),
            gate=request.args.get("gate", "A12"),
            amenities=amenities
        )
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@enhanced_bp.route("/concierge/comprehensive", methods=["GET"])
def concierge_comprehensive():
    """
    Generate comprehensive passenger experience package.
    """
    try:
        journey = _journey_plan(
            airport=request.args.get("airport", "IST"),
            origin=request.args.get("origin", "SAW"),
            departure_time=request.args.get("departure_time", "2026-10-20T15:30:00Z"),
            preferences={
                "loyalty_tier": request.args.get("loyalty_tier", "gold"),
                "fast_track": True,
                "lounge_access": True,
                "shopping": True,
                "dining_preferences": ["coffee"],
            }
        )
        wayfinding = _wayfinding(
            airport=request.args.get("airport", "IST"),
            gate=journey.get("estimated_gate", "A12"),
            amenities=["coffee", "lounge"]
        )
        baggage = _baggage_alert(
            booking_ref=request.args.get("booking_ref", "TK1234AB"),
        )
        
        return jsonify({"success": True, "data": {
            "journey_plan": journey,
            "wayfinding": wayfinding,
            "baggage_info": baggage,
            "status": "ready",
        }})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
