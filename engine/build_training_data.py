"""
Builds a labeled training dataset from many simulated shipments.

For each sensor reading, we compute short-term trend features
(recent temperature change) and a label: will this shipment
breach the safe temperature threshold within the next N readings?

This lets the model learn to predict breaches *before* they happen,
using only the kind of trend information available in real time.
"""

import pandas as pd
import numpy as np
import random

from simulator.generate_shipment import generate_shipment_data, SAFE_TEMP_MAX

LOOKAHEAD_WINDOW = 3   # how many future readings count as "soon"
NUM_SHIPMENTS = 200    # how many simulated shipments to generate


def add_trend_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds short-term trend features usable at prediction time:
      - temp_delta_1: change from previous reading
      - temp_delta_3_avg: average change over last 3 readings
      - temp_current: current temperature itself
    """
    df = df.copy()
    df["temp_delta_1"] = df["temperature"].diff().fillna(0)
    df["temp_delta_3_avg"] = df["temperature"].diff().rolling(3).mean().fillna(0)
    df["temp_current"] = df["temperature"]
    return df


def add_future_breach_label(df: pd.DataFrame) -> pd.DataFrame:
    """
    Labels each row 1 if the temperature exceeds SAFE_TEMP_MAX at any
    point within the next LOOKAHEAD_WINDOW readings, else 0.
    """
    df = df.copy()
    future_max = df["temperature"].shift(-1).rolling(LOOKAHEAD_WINDOW, min_periods=1).max()
    # rolling looks backward, so we reverse-engineer a forward rolling max:
    reversed_temp = df["temperature"][::-1]
    forward_max = reversed_temp.rolling(LOOKAHEAD_WINDOW, min_periods=1).max()[::-1]
    df["will_breach_soon"] = (forward_max > SAFE_TEMP_MAX).astype(int)
    return df


def build_dataset() -> pd.DataFrame:
    all_rows = []

    for i in range(NUM_SHIPMENTS):
        # Randomize scenario: ~40% healthy shipments, 60% with a failure
        has_failure = random.random() < 0.6

        if has_failure:
            failure_start_index = random.choice([0, 1, 2, 3])
            failure_severity = random.uniform(0.5, 2.5)
        else:
            failure_start_index = None
            failure_severity = 1.0

        df = generate_shipment_data(
            failure_start_index=failure_start_index,
            failure_severity=failure_severity,
        )
        df = add_trend_features(df)
        df = add_future_breach_label(df)
        df["shipment_id"] = i
        all_rows.append(df)

    return pd.concat(all_rows, ignore_index=True)


if __name__ == "__main__":
    dataset = build_dataset()
    output_path = "engine/training_data.csv"
    dataset.to_csv(output_path, index=False)

    print(f"Built dataset with {len(dataset)} rows from {NUM_SHIPMENTS} shipments")
    print(f"Saved to {output_path}")
    print("\nLabel balance:")
    print(dataset["will_breach_soon"].value_counts())
    print("\nSample rows:")
    print(dataset[["shipment_id", "temperature", "temp_delta_1", "temp_delta_3_avg", "will_breach_soon"]].head(15))