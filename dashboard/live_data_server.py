"""
Lightweight Flask server that receives live sensor readings from the
ESP32 hardware (temperature, humidity, GPS) and stores the latest
reading in memory, for the dashboard to poll and display.
"""

from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

latest_reading = {
    "temperature": None,
    "humidity": None,
    "lat": None,
    "lon": None,
    "timestamp": None,
}


@app.route("/api/live-reading", methods=["POST"])
def receive_reading():
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"status": "ERROR", "message": "Invalid JSON"}), 400

    latest_reading["temperature"] = data.get("temperature")
    latest_reading["humidity"] = data.get("humidity")
    latest_reading["lat"] = data.get("lat")
    latest_reading["lon"] = data.get("lon")
    latest_reading["timestamp"] = datetime.now().isoformat()

    print(f"Received: {latest_reading}")
    return jsonify({"status": "SUCCESS"}), 200


@app.route("/api/live-reading", methods=["GET"])
def get_latest_reading():
    return jsonify(latest_reading), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)