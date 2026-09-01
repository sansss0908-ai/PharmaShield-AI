"""
Mock SAP S/4HANA integration & Hub Dispatch Notification endpoint.

Simulates the enterprise execution layer: receives Stock Transport
Order (STO) requests triggered by the risk/decision engine and
returns confirmations, as a real SAP integration would.

Also handles automated Cold-Storage Hub notifications when rerouting occurs.
"""

from flask import Flask, request, jsonify
from datetime import datetime
import itertools
import os
import json

app = Flask(__name__)

# In-memory "database" of orders and notifications (resets on restart)
ORDER_LOG = []
HUB_NOTIFICATIONS = []
order_id_counter = itertools.count(1000)

REQUIRED_FIELDS = ["shipment_id", "origin_hub", "destination_hub", "reason", "tts_remaining_hours"]

# Optional SMS / Twilio simulation handler structure
def dispatch_twilio_sms_simulation(phone_number: str, message: str) -> bool:
    """
    Placeholder structure for future Twilio / SMS API integration.
    """
    print(f"[SMS SIMULATION to {phone_number}]: {message}")
    return True

@app.route("/api/sap/stock-transport-order", methods=["POST"])
def create_stock_transport_order():
    payload = request.get_json(silent=True)

    if payload is None:
        return jsonify({"status": "ERROR", "message": "Request body must be valid JSON"}), 400

    missing_fields = [field for field in REQUIRED_FIELDS if field not in payload]
    if missing_fields:
        return jsonify({
            "status": "ERROR",
            "message": f"Missing required fields: {missing_fields}"
        }), 400

    order_number = f"STO-{next(order_id_counter)}"
    order_record = {
        "order_number": order_number,
        "shipment_id": payload["shipment_id"],
        "origin_hub": payload["origin_hub"],
        "destination_hub": payload["destination_hub"],
        "reason": payload["reason"],
        "tts_remaining_hours": payload["tts_remaining_hours"],
        "created_at": datetime.now().isoformat(),
        "status": "CONFIRMED",
    }
    ORDER_LOG.append(order_record)

    # Automatically notify destination cold hub
    hub_notification = {
        "notification_id": f"NOTIF-{len(HUB_NOTIFICATIONS) + 101}",
        "order_number": order_number,
        "shipment_id": payload["shipment_id"],
        "destination_hub": payload["destination_hub"],
        "tts_remaining_hours": payload["tts_remaining_hours"],
        "risk_level": payload.get("risk_level", "WARNING"),
        "distance_km": payload.get("distance_km", 0.0),
        "timestamp": datetime.now().isoformat(),
        "message": f"INCOMING COMPROMISED SHIPMENT: {payload['shipment_id']} rerouted to {payload['destination_hub']} due to {payload['reason']}."
    }
    HUB_NOTIFICATIONS.append(hub_notification)
    dispatch_twilio_sms_simulation("+91 98200 77889", hub_notification["message"])

    return jsonify({
        "status": "SUCCESS",
        "message": "Stock Transport Order created and hub notification dispatched.",
        "order": order_record,
        "hub_notification": hub_notification
    }), 201


@app.route("/api/sap/orders", methods=["GET"])
def list_orders():
    return jsonify({"count": len(ORDER_LOG), "orders": ORDER_LOG}), 200


@app.route("/api/hub/notifications", methods=["GET"])
def list_hub_notifications():
    return jsonify({"count": len(HUB_NOTIFICATIONS), "notifications": HUB_NOTIFICATIONS}), 200


@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET,PUT,POST,DELETE,OPTIONS'
    return response

@app.route("/api/sap/health", methods=["GET"])
def health_check():
    return jsonify({"status": "OK", "service": "Mock SAP S/4HANA Integration & Hub Dispatcher"}), 200


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
