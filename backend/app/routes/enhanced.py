"""
Enhanced API routes with live aviation data.
"""

from flask import Blueprint, request, jsonify
import json

# Import the enhanced prediction function
from ..services.ml_engine_enhanced import predict_with_live_data, get_system_status

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
