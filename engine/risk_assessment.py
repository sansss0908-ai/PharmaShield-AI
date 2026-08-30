"""
Unified risk assessment wrapper.

Combines the rule-based Time-to-Spoilage calculation, the trained
breach-prediction model, and the hub-selection decision engine into
a single function — the main entry point the dashboard (and any
future consumer) calls to get a complete risk picture for a shipment.
"""

import pandas as pd
import joblib

from engine.tts_calculator import compute_tts
from engine.hub_selector import select_recovery_hub

MODEL_PATH = "engine/breach_predictor.joblib"
FEATURE_COLUMNS = ["temp_current", "temp_delta_1", "temp_delta_3_avg", "humidity"]

_model = None  # lazy-loaded so importing this module doesn't require the file to exist yet


def _get_model():
    global _model
    if _model is None:
        _model = joblib.load(MODEL_PATH)
    return _model


def _add_trend_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Recomputes the same trend features used during training, so the
    model sees consistent inputs at prediction time.
    """
    df = df.copy()
    df["temp_delta_1"] = df["temperature"].diff().fillna(0)
    df["temp_delta_3_avg"] = df["temperature"].diff().rolling(3).mean().fillna(0)
    df["temp_current"] = df["temperature"]
    return df


def assess_shipment(sensor_df: pd.DataFrame) -> dict:
    """
    Given a shipment's sensor readings so far (chronological order),
    returns a full risk assessment for the LATEST reading:
      - tts info (remaining hours, percent, rule-based risk level)
      - ML-predicted breach probability and prediction
      - recovery recommendation (if risk warrants it)

    Args:
        sensor_df: DataFrame with at least 'timestamp', 'temperature',
            'humidity', 'lat', 'lon' columns, sorted chronologically.

    Returns:
        dict summarizing the current risk state and recommended action.
    """
    df_with_features = _add_trend_features(sensor_df)
    df_with_tts = compute_tts(df_with_features)

    latest = df_with_tts.iloc[-1]

    model = _get_model()
    X_latest = latest[FEATURE_COLUMNS].to_frame().T
    breach_probability = model.predict_proba(X_latest)[0][1]  # probability of class 1 (breach soon)
    breach_predicted = bool(model.predict(X_latest)[0])

    rule_based_risk = latest["risk_level"]
    needs_recovery_action = (rule_based_risk in ["WARNING", "CRITICAL", "SPOILED"]) or breach_predicted

    recovery = None
    if needs_recovery_action:
        recovery = select_recovery_hub(current_lat=latest["lat"], current_lon=latest["lon"])

    return {
        "timestamp": str(latest["timestamp"]),
        "current_temperature": latest["temperature"],
        "tts_remaining_hours": round(latest["tts_remaining_hours"], 2),
        "percent_remaining": round(latest["percent_remaining"], 2),
        "rule_based_risk_level": rule_based_risk,
        "ml_breach_probability": round(float(breach_probability), 3),
        "ml_breach_predicted": breach_predicted,
        "needs_recovery_action": needs_recovery_action,
        "recovery_recommendation": recovery,
    }


if __name__ == "__main__":
    from simulator.generate_shipment import generate_shipment_data

    df = generate_shipment_data(failure_start_index=2, failure_severity=1.5)
    assessment = assess_shipment(df)

    import json
    print(json.dumps(assessment, indent=2, default=str))