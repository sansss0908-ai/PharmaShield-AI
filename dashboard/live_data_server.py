"""
Live ESP32 Hardware Data Server.
Listens on port 5001 for ESP32 sensor posts (temperature, humidity, lat, lon)
and broadcasts live telemetry to both the Streamlit dashboard and the Hospital App.
"""

from flask import Flask, request, jsonify
from datetime import datetime
import os
import sys
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.risk_assessment import assess_shipment
from engine.state_bridge import broadcast_shipment_state

app = Flask(__name__)

LATEST_READING = {
    "timestamp": datetime.now().isoformat(),
    "temperature": None,
    "humidity": None,
    "lat": 19.0760,
    "lon": 72.8777
}

LIVE_READINGS_HISTORY = []

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET,PUT,POST,DELETE,OPTIONS'
    return response

@app.route("/api/live-reading", methods=["GET", "POST"])
def live_reading():
    global LATEST_READING
    if request.method == "POST":
        data = request.get_json(silent=True) or request.form.to_dict()
        if not data:
            try:
                data = request.json
            except Exception:
                data = {}
                
        if data and "temperature" in data:
            LATEST_READING = {
                "timestamp": datetime.now().isoformat(),
                "temperature": float(data.get("temperature")),
                "humidity": float(data.get("humidity", 50.0)),
                "lat": float(data.get("lat", 19.0760)),
                "lon": float(data.get("lon", 72.8777))
            }
            LIVE_READINGS_HISTORY.append(LATEST_READING)
            
            # Assess risk and broadcast to state bridge immediately
            df = pd.DataFrame(LIVE_READINGS_HISTORY[-30:])
            if len(df) >= 1:
                assessment = assess_shipment(df)
                rec = assessment.get("recovery_recommendation")
                hub = rec.get("hub") if rec else None
                
                broadcast_shipment_state(
                    scenario_name="🔴 LIVE Hardware Feed",
                    reading_index=len(df) - 1,
                    total_readings=len(df),
                    lat=LATEST_READING["lat"],
                    lon=LATEST_READING["lon"],
                    temperature=LATEST_READING["temperature"],
                    humidity=LATEST_READING["humidity"],
                    assessment=assessment,
                    rerouted=assessment.get("needs_recovery_action", False),
                    recovery_hub=hub,
                    arrived_at_hub=False
                )
            return jsonify({"status": "SUCCESS", "reading": LATEST_READING}), 200

    return jsonify(LATEST_READING), 200

@app.route("/api/live-reading/simulate", methods=["POST"])
def simulate_live_post():
    """Helper endpoint to inject live hardware sensor posts during testing."""
    data = request.get_json(silent=True) or {}
    temp = float(data.get("temperature", 9.4))
    hum = float(data.get("humidity", 68.5))
    
    dummy_req = {
        "temperature": temp,
        "humidity": hum,
        "lat": 18.9894,
        "lon": 73.1175
    }
    with app.test_request_context(json=dummy_req):
        return live_reading()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)
