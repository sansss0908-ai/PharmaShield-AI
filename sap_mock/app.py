"""
Mock SAP S/4HANA integration endpoint.

Simulates the enterprise execution layer: receives Stock Transport
Order (STO) requests triggered by the risk/decision engine and
returns confirmations, as a real SAP integration would.

This is a stand-in for real SAP API access, which is not available
in a hackathon prototype context. It demonstrates the integration
pattern and data contract, not real SAP connectivity.
"""

from flask import Flask, request, jsonify
from datetime import datetime
import itertools

app = Flask(__name__)

# In-memory "database" of orders processed so far (resets on restart)
ORDER_LOG = []
order_id_counter = itertools.count(1000)

REQUIRED_FIELDS = ["shipment_id", "origin_hub", "destination_hub", "reason", "tts_remaining_hours"]


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

    return jsonify({
        "status": "SUCCESS",
        "message": "Stock Transport Order created and confirmed.",
        "order": order_record,
    }), 201


@app.route("/api/sap/orders", methods=["GET"])
def list_orders():
    return jsonify({"count": len(ORDER_LOG), "orders": ORDER_LOG}), 200


@app.route("/api/sap/health", methods=["GET"])
def health_check():
    return jsonify({"status": "OK", "service": "Mock SAP S/4HANA Integration"}), 200


if __name__ == "__main__":
    app.run(debug=True, port=5000)