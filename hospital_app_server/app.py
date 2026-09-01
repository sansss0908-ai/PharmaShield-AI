"""
Hospital Notification App & Web Server.

Serves a smartphone-optimized mobile interface (iOS/Android compatible)
and REST API for hospital personnel, displaying real-time shipment risk,
key contacts (Vaibhav, Vaishnavi), visual early-warning alerts, and cold-hub rerouting.
"""

import os
import json
from datetime import datetime
from flask import Flask, render_template, jsonify, request
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.state_bridge import read_shipment_state

app = Flask(__name__, template_folder="templates")

CONTACTS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "contacts.json")

def load_contacts():
    if os.path.exists(CONTACTS_FILE):
        try:
            with open(CONTACTS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "personnel": {
            "driver": {"name": "VAIBHAV", "phone": "+91 75004 94102"},
            "delivery_manager": {"name": "VAISHNAVI", "phone": "+91 8057882151"}
        }
    }

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/manifest.json")
def manifest():
    manifest_path = os.path.join(os.path.dirname(__file__), "templates", "manifest.json")
    with open(manifest_path, "r") as f:
        return jsonify(json.load(f))

@app.route("/api/hospital/shipment-status", methods=["GET"])
def get_shipment_status():
    state = read_shipment_state()
    contacts = load_contacts()
    state["contacts"] = contacts
    return jsonify(state), 200

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET,PUT,POST,DELETE,OPTIONS'
    return response

@app.route("/api/hospital/contacts", methods=["GET"])
def get_contacts():
    return jsonify(load_contacts()), 200

@app.route("/api/sap/orders", methods=["GET"])
def get_sap_orders():
    try:
        import requests
        res = requests.get("http://127.0.0.1:5000/api/sap/orders", timeout=2)
        if res.status_code == 200:
            return jsonify(res.json()), 200
    except Exception:
        pass
    from sap_mock.app import ORDER_LOG
    return jsonify({"count": len(ORDER_LOG), "orders": ORDER_LOG}), 200

@app.route("/api/sap/stock-transport-order", methods=["POST"])
def post_sap_sto():
    payload = request.get_json(silent=True) or {}
    try:
        import requests
        res = requests.post("http://127.0.0.1:5000/api/sap/stock-transport-order", json=payload, timeout=2)
        if res.status_code in [200, 201]:
            return jsonify(res.json()), res.status_code
    except Exception:
        pass
    from sap_mock.app import ORDER_LOG, order_id_counter
    order_number = f"STO-{next(order_id_counter)}"
    order_record = {
        "order_number": order_number,
        "shipment_id": payload.get("shipment_id", "SHP-9942"),
        "origin_hub": payload.get("origin_hub", "Origin Transit MH-12"),
        "destination_hub": payload.get("destination_hub", "Panvel Cold Hub"),
        "reason": payload.get("reason", "EMERGENCY_MANUAL_DISPATCH"),
        "tts_remaining_hours": payload.get("tts_remaining_hours", 1.5),
        "created_at": datetime.now().isoformat(),
        "status": "CONFIRMED",
    }
    ORDER_LOG.append(order_record)
    return jsonify({
        "status": "SUCCESS",
        "message": "Stock Transport Order created and confirmed.",
        "order": order_record
    }), 201

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5002)
