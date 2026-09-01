"""
State bridge module. Broadcasts live shipment data, current risk assessment,
and hub rerouting notifications from the main dashboard to the hospital app / REST API.
"""

import os
import json
from datetime import datetime

STATE_FILE_PATH = os.path.join(os.path.dirname(__file__), "live_state.json")

def broadcast_shipment_state(
    scenario_name: str,
    reading_index: int,
    total_readings: int,
    lat: float,
    lon: float,
    temperature: float,
    humidity: float,
    assessment: dict,
    rerouted: bool = False,
    recovery_hub: dict = None,
    arrived_at_hub: bool = False
):
    """
    Persists current shipment telemetry and risk assessment so external
    viewers (such as the Hospital Notification App) can display live updates.
    """
    state_payload = {
        "scenario_name": scenario_name,
        "reading_index": reading_index + 1,
        "total_readings": total_readings,
        "lat": lat,
        "lon": lon,
        "temperature": temperature,
        "humidity": humidity,
        "timestamp": assessment.get("timestamp", datetime.now().isoformat()),
        "tts_remaining_hours": assessment.get("tts_remaining_hours", 72.0),
        "percent_remaining": assessment.get("percent_remaining", 100.0),
        "rule_based_risk_level": assessment.get("rule_based_risk_level", "SAFE"),
        "ml_breach_probability": assessment.get("ml_breach_probability", 0.0),
        "ml_breach_predicted": assessment.get("ml_breach_predicted", False),
        "needs_recovery_action": assessment.get("needs_recovery_action", False),
        "rerouted": rerouted,
        "recovery_hub": recovery_hub,
        "arrived_at_hub": arrived_at_hub,
        "last_updated": datetime.now().isoformat()
    }
    
    try:
        with open(STATE_FILE_PATH, "w") as f:
            json.dump(state_payload, f, indent=2)
    except Exception as e:
        print(f"Error persisting state bridge data: {e}")

def read_shipment_state() -> dict:
    """
    Reads the latest persisted shipment telemetry state.
    Returns default safe initial state if file doesn't exist yet.
    """
    if not os.path.exists(STATE_FILE_PATH):
        return {
            "scenario_name": "Initial State",
            "reading_index": 1,
            "total_readings": 24,
            "lat": 19.0760,
            "lon": 72.8777,
            "temperature": 5.0,
            "humidity": 45.0,
            "timestamp": datetime.now().isoformat(),
            "tts_remaining_hours": 72.0,
            "percent_remaining": 100.0,
            "rule_based_risk_level": "SAFE",
            "ml_breach_probability": 0.0,
            "ml_breach_predicted": False,
            "needs_recovery_action": False,
            "rerouted": False,
            "recovery_hub": None,
            "arrived_at_hub": False,
            "last_updated": datetime.now().isoformat()
        }
        
    try:
        with open(STATE_FILE_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return read_shipment_state()
