from pathlib import Path
import json
import numpy as np
import pandas as pd
import joblib


BASE = Path(__file__).resolve().parent

MODEL = BASE / "artifacts" / "landslide_rf.joblib"
METRICS = BASE / "artifacts" / "metrics.json"


class MLPredictor:

    def __init__(self):

        self.model = (
            joblib.load(MODEL)
            if MODEL.exists()
            else None
        )

        self.metrics = (
            json.loads(METRICS.read_text())
            if METRICS.exists()
            else None
        )

    @property
    def available(self):
        return self.model is not None

    def predict(
        self,
        slope_deg,
        rainfall_mm,
        elevation_m
    ):

        if self.model is None:
            return None

        # The trained model uses:
        # slope_deg
        # elevation_m
        #
        # rainfall_mm is kept in the function
        # because the existing application passes it,
        # but it is not directly used by this model.

        X = pd.DataFrame(
            [[
                float(slope_deg),
                float(elevation_m)
            ]],
            columns=[
                "slope_deg",
                "elevation_m"
            ]
        )

        probability = float(
            self.model.predict_proba(X)[0][1]
        )

        score = probability * 100

        if score < 25:

            level = "Low Risk"
            color = "#22c55e"

        elif score < 50:

            level = "Moderate Risk"
            color = "#eab308"

        elif score < 75:

            level = "High Risk"
            color = "#f97316"

        else:

            level = "Very High Risk"
            color = "#ef4444"

        return {
            "probability": round(probability, 4),
            "score": round(score, 1),
            "risk_level": level,
            "risk_color": color,
            "model": "Random Forest",
            "features_used": [
                "slope_deg",
                "elevation_m"
            ],
            "metrics": self.metrics
        }