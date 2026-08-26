"""
Time-to-Spoilage (TTS) calculator.

Converts a sequence of temperature readings into a running estimate
of how much usable shelf life a shipment has left, using an
accelerated-degradation model: shelf life depletes faster the further
temperature rises above the safe threshold.
"""

import pandas as pd
import numpy as np

NOMINAL_SHELF_LIFE_HOURS = 72.0    # 3 days, at ideal safe-range temperature
SAFE_TEMP_MAX = 8.0                # degrees C
DEGRADATION_MULTIPLIER = 15.0      # controls how sharply degradation accelerates above threshold


def degradation_rate(temperature: float) -> float:
    """
    Returns the rate at which shelf life is consumed per hour of real time,
    given the current temperature.

    Rate = 1.0 when at or below the safe max (normal depletion).
    Rate increases sharply (quadratically) above the safe max.
    """
    if temperature <= SAFE_TEMP_MAX:
        return 1.0
    excess = temperature - SAFE_TEMP_MAX
    return 1.0 + DEGRADATION_MULTIPLIER * (excess ** 2)


def compute_tts(df: pd.DataFrame) -> pd.DataFrame:
    """
    Given a shipment sensor DataFrame (must have 'timestamp' and
    'temperature' columns, sorted chronologically), computes:
      - shelf_life_consumed_hours: cumulative equivalent hours consumed
      - tts_remaining_hours: nominal shelf life minus consumed
      - percent_remaining: tts_remaining as a % of nominal shelf life
      - risk_level: bucket based on percent_remaining

    Returns the DataFrame with these new columns added.
    """
    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    consumed = 0.0
    consumed_list = []

    for i in range(len(df)):
        if i == 0:
            elapsed_hours = 0.0
        else:
            elapsed_hours = (
                df.loc[i, "timestamp"] - df.loc[i - 1, "timestamp"]
            ).total_seconds() / 3600.0

        rate = degradation_rate(df.loc[i, "temperature"])
        consumed += elapsed_hours * rate
        consumed_list.append(consumed)

    df["shelf_life_consumed_hours"] = consumed_list
    df["tts_remaining_hours"] = NOMINAL_SHELF_LIFE_HOURS - df["shelf_life_consumed_hours"]
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

    output_path = "engine/sample_shipment_with_tts.csv"
    df_with_tts.to_csv(output_path, index=False)

    print(f"Saved to {output_path}")
    print(df_with_tts[["timestamp", "temperature", "tts_remaining_hours", "percent_remaining", "risk_level"]].tail(10))