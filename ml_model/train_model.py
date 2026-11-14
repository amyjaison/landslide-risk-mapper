from pathlib import Path
import json
import zipfile

import joblib
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    classification_report,
    confusion_matrix
)


BASE = Path(__file__).resolve().parent
DATASET_ZIP = BASE / "dataset" / "mendeley_dataset.zip"
ARTIFACTS = BASE / "artifacts"

ARTIFACTS.mkdir(exist_ok=True)


def find_dataset():
    """Find the 12,409-row modelling dataset inside the ZIP."""

    with zipfile.ZipFile(DATASET_ZIP, "r") as z:

        for name in z.namelist():

            if name.endswith("landslide_modelling_dataset_12409.csv"):
                return z.read(name)

    raise FileNotFoundError(
        "landslide_modelling_dataset_12409.csv was not found inside the ZIP."
    )


def main():

    print("=" * 60)
    print("LANDSLIDE RISK ML MODEL TRAINING")
    print("=" * 60)

    # ---------------------------------------------------------
    # LOAD DATASET
    # ---------------------------------------------------------

    print("\nReading Mendeley modelling dataset...")

    csv_bytes = find_dataset()

    from io import BytesIO

    df = pd.read_csv(BytesIO(csv_bytes))

    print(f"\nDataset shape: {df.shape}")

    print("\nColumns:")
    print(df.columns.tolist())

    # ---------------------------------------------------------
    # CHECK TARGET
    # ---------------------------------------------------------

    target = "class"

    if target not in df.columns:
        raise ValueError(
            f"Target column '{target}' was not found."
        )

    print("\nClass distribution:")
    print(df[target].value_counts())

    if df[target].nunique() < 2:
        raise ValueError(
            "Dataset does not contain both classes."
        )

    # ---------------------------------------------------------
    # FEATURES
    # ---------------------------------------------------------

    features = [
        "slope_deg",
        "elevation_m"
    ]

    for feature in features:

        if feature not in df.columns:
            raise ValueError(
                f"Required feature '{feature}' was not found."
            )

    X = df[features].copy()
    y = df[target].astype(int)

    # ---------------------------------------------------------
    # CLEAN DATA
    # ---------------------------------------------------------

    X = X.replace([float("inf"), float("-inf")], pd.NA)

    print("\nMissing values:")
    print(X.isna().sum())

    # ---------------------------------------------------------
    # TRAIN / TEST SPLIT
    # ---------------------------------------------------------

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=42,
        stratify=y
    )

    print("\nTraining samples:", len(X_train))
    print("Testing samples:", len(X_test))

    # ---------------------------------------------------------
    # MODEL
    # ---------------------------------------------------------

    model = Pipeline([
        (
            "imputer",
            SimpleImputer(strategy="median")
        ),

        (
            "scaler",
            StandardScaler()
        ),

        (
            "random_forest",
            RandomForestClassifier(
                n_estimators=300,
                max_depth=12,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42,
                class_weight="balanced",
                n_jobs=-1
            )
        )
    ])

    print("\nTraining Random Forest...")

    model.fit(X_train, y_train)

    print("Training completed.")

    # ---------------------------------------------------------
    # PREDICTIONS
    # ---------------------------------------------------------

    y_pred = model.predict(X_test)

    y_probability = model.predict_proba(X_test)[:, 1]

    # ---------------------------------------------------------
    # METRICS
    # ---------------------------------------------------------

    accuracy = accuracy_score(y_test, y_pred)

    precision = precision_score(
        y_test,
        y_pred,
        zero_division=0
    )

    recall = recall_score(
        y_test,
        y_pred,
        zero_division=0
    )

    f1 = f1_score(
        y_test,
        y_pred,
        zero_division=0
    )

    roc_auc = roc_auc_score(
        y_test,
        y_probability
    )

    cm = confusion_matrix(y_test, y_pred)

    print("\n" + "=" * 60)
    print("MODEL PERFORMANCE")
    print("=" * 60)

    print(f"\nAccuracy : {accuracy * 100:.2f}%")
    print(f"Precision: {precision * 100:.2f}%")
    print(f"Recall   : {recall * 100:.2f}%")
    print(f"F1 Score : {f1 * 100:.2f}%")
    print(f"ROC-AUC  : {roc_auc * 100:.2f}%")

    print("\nClassification Report:")
    print(
        classification_report(
            y_test,
            y_pred,
            zero_division=0
        )
    )

    print("Confusion Matrix:")
    print(cm)

    # ---------------------------------------------------------
    # SAVE MODEL
    # ---------------------------------------------------------

    model_path = ARTIFACTS / "landslide_rf.joblib"

    joblib.dump(model, model_path)

    print(
        f"\nModel saved to:\n{model_path}"
    )

    # ---------------------------------------------------------
    # SAVE METRICS
    # ---------------------------------------------------------

    metrics = {
        "model": "Random Forest",
        "dataset": "Mendeley Data - landslide_modelling_dataset_12409.csv",
        "samples": int(len(df)),
        "training_samples": int(len(X_train)),
        "testing_samples": int(len(X_test)),
        "features": features,
        "target": target,
        "accuracy": round(float(accuracy), 4),
        "precision": round(float(precision), 4),
        "recall": round(float(recall), 4),
        "f1_score": round(float(f1), 4),
        "roc_auc": round(float(roc_auc), 4),
        "confusion_matrix": cm.tolist()
    }

    metrics_path = ARTIFACTS / "metrics.json"

    metrics_path.write_text(
        json.dumps(metrics, indent=4)
    )

    print(
        f"Metrics saved to:\n{metrics_path}"
    )

    # ---------------------------------------------------------
    # SAVE FEATURE MAP
    # ---------------------------------------------------------

    feature_map = {
        "slope": "slope_deg",
        "elevation": "elevation_m"
    }

    feature_map_path = ARTIFACTS / "feature_map.json"

    feature_map_path.write_text(
        json.dumps(feature_map, indent=4)
    )

    print(
        f"Feature map saved to:\n{feature_map_path}"
    )

    print("\n" + "=" * 60)
    print("TRAINING FINISHED SUCCESSFULLY")
    print("=" * 60)


if __name__ == "__main__":
    main()