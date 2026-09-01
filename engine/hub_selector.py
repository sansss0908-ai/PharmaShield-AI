"""
Decision engine for recovery-hub selection.

Given a shipment's current location and a risk trigger, evaluates
available cold-storage hubs and selects the best recovery option
based on distance and available capacity.
"""

import math

# Hardcoded cold-storage hub network (lat, lon roughly along/near the
# Mumbai-Pune corridor used in the simulator, plus one off-route option)
COLD_STORAGE_HUBS = [
    {"id": "HUB-01", "name": "Panvel Cold Hub",      "lat": 18.9894, "lon": 73.1175, "capacity": 50, "current_load": 42, "operational": True},
    {"id": "HUB-02", "name": "Lonavala Cold Hub",     "lat": 18.7500, "lon": 73.4050, "capacity": 30, "current_load": 28, "operational": True},
    {"id": "HUB-03", "name": "Pune Central Cold Hub", "lat": 18.5308, "lon": 73.8478, "capacity": 100, "current_load": 60, "operational": True},
    {"id": "HUB-04", "name": "Khopoli Cold Hub",      "lat": 18.7900, "lon": 73.3400, "capacity": 20, "current_load": 20, "operational": True},  # full
    {"id": "HUB-05", "name": "Satara Cold Hub",       "lat": 17.6805, "lon": 74.0183, "capacity": 40, "current_load": 10, "operational": False}, # offline
]


def haversine_distance_km(lat1, lon1, lat2, lon2) -> float:
    """
    Calculates great-circle distance between two lat/lon points in km.
    """
    R = 6371.0  # Earth radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)

    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def select_recovery_hub(current_lat: float, current_lon: float) -> dict:
    """
    Selects the best recovery hub given the shipment's current location.

    Eligibility: hub must be operational and have free capacity.
    Selection: nearest eligible hub by straight-line distance.

    Returns a dict with the selected hub's info and distance, or
    a dict indicating no eligible hub was found.
    """
    eligible_hubs = [
        hub for hub in COLD_STORAGE_HUBS
        if hub["operational"] and hub["current_load"] < hub["capacity"]
    ]

    if not eligible_hubs:
        return {"status": "NO_HUB_AVAILABLE", "hub": None, "distance_km": None}

    scored_hubs = []
    for hub in eligible_hubs:
        distance = haversine_distance_km(current_lat, current_lon, hub["lat"], hub["lon"])
        scored_hubs.append((distance, hub))

    scored_hubs.sort(key=lambda x: x[0])
    best_distance, best_hub = scored_hubs[0]

    return {
        "status": "HUB_SELECTED",
        "hub": best_hub,
        "distance_km": round(best_distance, 2),
    }


if __name__ == "__main__":
    result = select_recovery_hub(current_lat=18.8, current_lon=73.35)
    print("Recovery decision:")
    print(f"  Status: {result['status']}")
    if result["hub"]:
        print(f"  Selected hub: {result['hub']['name']} ({result['hub']['id']})")
        print(f"  Distance: {result['distance_km']} km")
        print(f"  Load: {result['hub']['current_load']}/{result['hub']['capacity']}")
