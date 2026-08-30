"""
Time-to-Spoilage (TTS) calculator.

Once temperature or humidity exceeds the safe range, the shipment is
considered compromised and given a fixed short rescue window (rather
than a slowly-declining estimate) — reflecting that biologics degrade
sharply, not gradually, once excursion begins.
"""

import pandas as pd

NOMINAL_SHELF_LIFE_HOURS = 72.0
SAFE_TEMP_MAX = 8.0
SAFE_HUMIDITY_MAX = 65.0
RESCUE_WINDOW_HOURS = 2.0   # fixed window once ANY excursion (temp or humidity) begins


def compute_tts(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    tts_remaining = NOMINAL_SHELF_LIFE_HOURS
    breach_start_time = None
    results = []

    for i in range(len(df)):
        row = df.iloc[i]
        temp_breach = row["temperature"] > SAFE_TEMP_MAX
        humidity_breach = row["humidity"] > SAFE_HUMIDITY_MAX
        excursion = temp_breach or humidity_breach

        if excursion and breach_start_time is None:
            # First moment of excursion: drop remaining life to the fixed rescue window
            breach_start_time = row["timestamp"]
            tts_remaining = min(tts_remaining, RESCUE_WINDOW_HOURS)
        elif breach_start_time is not None:
            # Already breached: countdown the rescue window using real elapsed time
            elapsed_hours = (row["timestamp"] - breach_start_time).total_seconds() / 3600.0
            tts_remaining = max(0.0, RESCUE_WINDOW_HOURS - elapsed_hours)
        else:
            # Still healthy: normal 1:1 depletion of nominal shelf life
            if i > 0:
                elapsed_hours = (row["timestamp"] - df.iloc[i - 1]["timestamp"]).total_seconds() / 3600.0
                tts_remaining -= elapsed_hours

        results.append(tts_remaining)

    df["tts_remaining_hours"] = results
    df["percent_remaining"] = (df["tts_remaining_hours"] / NOMINAL_SHELF_LIFE_HOURS) * 100

    def bucket(pct):
        if pct <= 0:
            return "SPOILED"
        elif pct < 15:
            return "CRITICAL"
        elif pct < 50:
            return "WARNING"
        else:
            return "SAFE"

    df["risk_level"] = df["percent_remaining"].apply(bucket)
    return df


if __name__ == "__main__":
    from simulator.generate_shipment import generate_shipment_data

    df = generate_shipment_data(failure_start_index=2)
    df_with_tts = compute_tts(df)
    df_with_tts.to_csv("engine/sample_shipment_with_tts.csv", index=False)
    print(df_with_tts[["timestamp", "temperature", "humidity", "tts_remaining_hours", "percent_remaining", "risk_level"]].tail(10))