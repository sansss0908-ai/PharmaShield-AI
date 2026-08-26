"""
Trains a classifier to predict whether a shipment will breach the
safe temperature threshold in the near future, based on current
temperature and recent trend features.

This is the core predictive "AI" layer referenced in the pitch:
it forecasts risk before the breach actually happens, using only
information available in real time (no future data).
"""

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
import joblib

FEATURE_COLUMNS = ["temp_current", "temp_delta_1", "temp_delta_3_avg", "humidity"]
LABEL_COLUMN = "will_breach_soon"


def train_and_evaluate():
    df = pd.read_csv("engine/training_data.csv")

    X = df[FEATURE_COLUMNS]
    y = df[LABEL_COLUMN]

    # Split by shipment_id would be more rigorous, but a random split
    # is a reasonable and fast approach for a prototype.
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    model = RandomForestClassifier(n_estimators=100, max_depth=6, random_state=42)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)

    print("Classification Report:")
    print(classification_report(y_test, y_pred, target_names=["No Breach Soon", "Breach Soon"]))

    print("Confusion Matrix:")
    print(confusion_matrix(y_test, y_pred))

    print("\nFeature Importances:")
    for feature, importance in zip(FEATURE_COLUMNS, model.feature_importances_):
        print(f"  {feature}: {importance:.3f}")

    output_path = "engine/breach_predictor.joblib"
    joblib.dump(model, output_path)
    print(f"\nModel saved to {output_path}")

    return model


if __name__ == "__main__":
    train_and_evaluate()