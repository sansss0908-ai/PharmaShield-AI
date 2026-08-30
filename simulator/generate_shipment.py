"""
Simulates a pharmaceutical shipment traveling along a route,
generating GPS + temperature + humidity sensor readings over time,
with an optional injected cold-chain failure event.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Example route: Mumbai -> Pune (approx waypoints)
ROUTE_WAYPOINTS = [
    (19.0760, 72.8777),  # Mumbai
    (18.9894, 73.1175),
    (18.8000, 73.3500),
    (18.6500, 73.6500),
    (18.5308, 73.8478),  # Pune
]

SAFE_TEMP_MIN = 2.0   # degrees C (typical vaccine/biologic cold-chain range)
SAFE_TEMP_MAX = 8.0

def generate_shipment_data(
    failure_start_index: int = None,
    failure_severity: float = 1.0,
    points_per_leg: int = 6,
    start_time: datetime = None
) -> pd.DataFrame:
    """
    Generates a synthetic shipment sensor dataset.

    Args:
        failure_start_index: waypoint index after which temperature
            begins rising abnormally (simulating a cooling failure).
            If None, no failure is injected (fully healthy shipment).
        failure_severity: multiplier controlling how fast temperature
            rises once failure starts (1.0 = normal, 2.0 = twice as fast).
        points_per_leg: how many sensor readings between each waypoint pair.
        start_time: timestamp for the first reading. Defaults to now.

    Returns:
        DataFrame with columns: timestamp, waypoint_index, lat, lon, temperature, humidity
    """
    if start_time is None:
        start_time = datetime.now()

    records = []
    reading_index = 0
    temperature = 5.0  # start mid-safe-range

    for leg_idx in range(len(ROUTE_WAYPOINTS) - 1):
        lat1, lon1 = ROUTE_WAYPOINTS[leg_idx]
        lat2, lon2 = ROUTE_WAYPOINTS[leg_idx + 1]

        for step in range(points_per_leg):
            frac = step / points_per_leg
            lat = lat1 + (lat2 - lat1) * frac
            lon = lon1 + (lon2 - lon1) * frac

            failure_triggered = (
                failure_start_index is not None and leg_idx >= failure_start_index
            )

            if failure_triggered:
                temperature += np.random.uniform(0.3, 0.6) * failure_severity
                humidity_spike = np.random.uniform(0.5, 1.5) * failure_severity
            else:
                temperature += np.random.uniform(-0.2, 0.2)
                temperature = np.clip(temperature, SAFE_TEMP_MIN, SAFE_TEMP_MAX)

            if failure_triggered:
                humidity = min(95, 55 + humidity_spike * (leg_idx - failure_start_index + 1) * 3)
            else:
                humidity = np.random.uniform(40, 60)
            timestamp = start_time + timedelta(minutes=15 * reading_index)

            records.append({
                "timestamp": timestamp,
                "waypoint_index": leg_idx,
                "lat": round(lat, 5),
                "lon": round(lon, 5),
                "temperature": round(temperature, 2),
                "humidity": round(humidity, 2),
            })
            reading_index += 1

    return pd.DataFrame(records)

if __name__ == "__main__":
    # Generate a shipment WITH a failure starting at waypoint 2 (mid-journey)
    df = generate_shipment_data(failure_start_index=2)
    output_path = "simulator/sample_shipment.csv"
    df.to_csv(output_path, index=False)
    print(f"Generated {len(df)} sensor readings.")
    print(f"Saved to {output_path}")
    print(df.head(10))