import math
import numpy as np
from config import Config


class RiskCalculationEngine:
    """
    Interaction-aware landslide susceptibility engine.

    The original model was a simple weighted sum of three factors. This version
    keeps that transparent structure but improves calibration by:
      1. using continuous factor curves rather than hard category jumps;
      2. modelling the slope × rainfall triggering interaction;
      3. optionally incorporating nearby historical-event evidence;
      4. reporting a data-quality/confidence estimate;
      5. preserving the existing API fields so the frontend remains compatible.

    This remains a screening-level susceptibility model, not a deterministic
    landslide forecast.
    """

    MODEL_VERSION = "2.0-interaction-aware"

    def __init__(self, default_weights=None):
        if default_weights is None:
            self.weights = self.normalize_weights({
                "slope": Config.WEIGHT_SLOPE,
                "rainfall": Config.WEIGHT_RAINFALL,
                "terrain": Config.WEIGHT_TERRAIN
            })
        else:
            self.weights = self.normalize_weights(default_weights)
        self.risk_levels = Config.RISK_LEVELS

    def normalize_weights(self, weights):
        """Ensure weights are non-negative and sum to 1.0."""
        w_slope = max(0.0, float(weights.get("slope", 0.40)))
        w_rain = max(0.0, float(weights.get("rainfall", 0.35)))
        w_terr = max(0.0, float(weights.get("terrain", 0.25)))
        total = w_slope + w_rain + w_terr
        if total <= 0:
            return {"slope": 0.40, "rainfall": 0.35, "terrain": 0.25}
        return {
            "slope": round(w_slope / total, 4),
            "rainfall": round(w_rain / total, 4),
            "terrain": round(w_terr / total, 4)
        }

    @staticmethod
    def _clip(x):
        return max(0.0, min(100.0, float(x)))

    def calculate_score(
        self,
        slope_score,
        rainfall_score,
        terrain_score,
        custom_weights=None,
        historical_count=0,
        nearest_historical_km=None,
        rainfall_intensity=None,
        data_quality=None,
    ):
        """
        Calculate a susceptibility score from 0-100.

        The base score is the transparent weighted overlay. A bounded
        interaction term captures the fact that steep terrain becomes more
        susceptible when intense/antecedent rainfall is also high. Historical
        evidence is deliberately capped so a catalog cluster cannot overwhelm
        physical terrain/rainfall factors.
        """
        w = self.normalize_weights(custom_weights) if custom_weights else self.weights

        s_score = self._clip(slope_score)
        r_score = self._clip(rainfall_score)
        t_score = self._clip(terrain_score)

        contrib_slope = s_score * w["slope"]
        contrib_rain = r_score * w["rainfall"]
        contrib_terrain = t_score * w["terrain"]
        base_score = contrib_slope + contrib_rain + contrib_terrain

        # Non-linear trigger interaction. It is near zero for dry/gentle
        # conditions and reaches a bounded maximum only when both factors are
        # simultaneously high.
        trigger_synergy = 0.0
        if s_score > 45 and r_score > 45:
            trigger_synergy = min(
                8.0,
                8.0 * ((s_score - 45.0) / 55.0) * ((r_score - 45.0) / 55.0)
            )

        # Short-duration intense bursts add a small bounded trigger adjustment.
        intensity_bonus = 0.0
        if rainfall_intensity is not None:
            intensity = max(0.0, float(rainfall_intensity))
            intensity_bonus = min(4.0, max(0.0, intensity - 10.0) * 0.20)

        # Historical events are supporting evidence, not a primary physical
        # predictor. Distance is more important than raw event count.
        history_bonus = 0.0
        if nearest_historical_km is not None:
            d = max(0.0, float(nearest_historical_km))
            if d <= 10:
                history_bonus = 5.0
            elif d <= 25:
                history_bonus = 4.0
            elif d <= 50:
                history_bonus = 2.5
            elif d <= 100:
                history_bonus = 1.0
            if historical_count >= 3:
                history_bonus = min(5.0, history_bonus + 0.5)

        raw_score = base_score + trigger_synergy + intensity_bonus + history_bonus
        total_score = round(self._clip(raw_score), 1)

        risk_category = self.classify_risk(total_score)
        confidence = self._confidence(
            data_quality=data_quality,
            historical_count=historical_count,
            has_intensity=rainfall_intensity is not None
        )

        explanation = self.generate_detailed_explanation(
            total_score,
            risk_category,
            s_score,
            r_score,
            t_score,
            contrib_slope,
            contrib_rain,
            contrib_terrain,
            w,
            trigger_synergy,
            intensity_bonus,
            history_bonus
        )

        return {
            "vulnerability_score": total_score,
            "risk_level": risk_category["name"],
            "risk_code": risk_category["code"],
            "risk_color": risk_category["color"],
            "risk_description": risk_category["description"],
            "model_version": self.MODEL_VERSION,
            "weights_used": w,
            "factor_scores": {
                "slope": round(s_score, 1),
                "rainfall": round(r_score, 1),
                "terrain": round(t_score, 1)
            },
            "factor_contributions": {
                "slope": round(contrib_slope, 1),
                "rainfall": round(contrib_rain, 1),
                "terrain": round(contrib_terrain, 1)
            },
            "adjustments": {
                "slope_rainfall_synergy": round(trigger_synergy, 1),
                "rainfall_intensity_bonus": round(intensity_bonus, 1),
                "historical_evidence_bonus": round(history_bonus, 1)
            },
            "confidence": confidence,
            "explanation": explanation,
            "disclaimer": (
                "SCREENING-LEVEL ASSESSMENT ONLY: This tool estimates landslide "
                "susceptibility from terrain and precipitation indicators. It is "
                "not a real-time deterministic landslide prediction system and "
                "cannot predict exact timing or occurrence. Official warnings "
                "and site-specific geotechnical investigations take precedence."
            )
        }

    def _confidence(self, data_quality=None, historical_count=0, has_intensity=False):
        """Return an interpretable confidence score based on input quality."""
        score = 70.0
        if data_quality:
            if data_quality.get("elevation_fallback"):
                score -= 15
            if data_quality.get("rainfall_fallback"):
                score -= 10
            if data_quality.get("rainfall_simulation"):
                score -= 8
        if has_intensity:
            score += 5
        if historical_count > 0:
            score += 3
        score = int(max(35, min(95, round(score))))
        label = "High" if score >= 80 else ("Moderate" if score >= 60 else "Low")
        return {"score": score, "label": label}

    def classify_risk(self, score):
        score_val = float(score)
        if score_val <= 25.0:
            return self.risk_levels[0]
        elif score_val <= 50.0:
            return self.risk_levels[1]
        elif score_val <= 75.0:
            return self.risk_levels[2]
        return self.risk_levels[3]

    def generate_detailed_explanation(
        self, score, category, s_score, r_score, t_score,
        c_s, c_r, c_t, weights, synergy, intensity_bonus, history_bonus
    ):
        drivers = [
            ("Slope Gradient", c_s),
            ("Recent Precipitation", c_r),
            ("Terrain Morphometry", c_t),
        ]
        top_driver = max(drivers, key=lambda x: x[1])

        reasons = []
        if s_score >= 60:
            reasons.append(f"steep slope gradients ({s_score:.1f}/100)")
        elif s_score <= 25:
            reasons.append(f"gentle relief ({s_score:.1f}/100)")

        if r_score >= 60:
            reasons.append(f"high antecedent rainfall ({r_score:.1f}/100)")
        elif r_score <= 25:
            reasons.append(f"low recent rainfall ({r_score:.1f}/100)")

        if t_score >= 60:
            reasons.append(f"rugged terrain ({t_score:.1f}/100)")
        elif t_score <= 25:
            reasons.append(f"low-gradient landform ({t_score:.1f}/100)")

        if synergy > 0:
            reasons.append(f"combined slope-rainfall trigger (+{synergy:.1f})")
        if intensity_bonus > 0:
            reasons.append(f"intense short-duration rainfall (+{intensity_bonus:.1f})")
        if history_bonus > 0:
            reasons.append(f"nearby historical evidence (+{history_bonus:.1f})")

        return (
            f"This location is classified as '{category['name']}' with a "
            f"composite susceptibility score of {score:.1f}/100. The strongest "
            f"weighted driver is {top_driver[0]}, contributing {top_driver[1]:.1f} "
            f"points. Key signals: {'; '.join(reasons) if reasons else 'no dominant hazard signal'}. "
            f"Current weights are {int(weights['slope']*100)}% slope, "
            f"{int(weights['rainfall']*100)}% rainfall and "
            f"{int(weights['terrain']*100)}% terrain."
        )

    @staticmethod
    def slope_score(slope_deg):
        """Continuous slope susceptibility curve."""
        x = max(0.0, min(90.0, float(slope_deg)))
        # Peak susceptibility is around the common shallow-slide/debris-flow
        # slope band; very steep faces shift toward rockfall rather than simply
        # increasing shallow-slide susceptibility.
        if x <= 5:
            return 2.0 * x
        if x <= 15:
            return 10.0 + (x - 5.0) * 1.5
        if x <= 30:
            return 25.0 + (x - 15.0) * 2.4
        if x <= 45:
            return 61.0 + (x - 30.0) * 2.2
        return max(70.0, 94.0 - (x - 45.0) * 0.35)

    def generate_spatial_grid_geojson(
        self, elev_grid, slope_matrix, rain_data, terrain_data,
        lats, lons, weights=None
    ):
        w = self.normalize_weights(weights) if weights else self.weights
        rain_score = self._clip(rain_data["rainfall_score"])
        t_score = self._clip(terrain_data["terrain_score"])

        nrows, ncols = len(lats), len(lons)
        features = []
        half_dlat = abs(lats[1] - lats[0]) / 2.0 if nrows > 1 else 0.005
        half_dlon = abs(lons[1] - lons[0]) / 2.0 if ncols > 1 else 0.005

        for i in range(nrows):
            for j in range(ncols):
                cell_lat = lats[i]
                cell_lon = lons[j]
                elev = float(elev_grid[i][j])
                slope_deg = float(slope_matrix[i][j])
                cell_slope_score = self.slope_score(slope_deg)

                # Local terrain variation is kept bounded around the regional
                # terrain score to avoid inventing large unsupported gradients.
                cell_t_score = min(
                    100.0,
                    max(5.0, t_score + (slope_deg - 20.0) * 0.65)
                )

                cell_risk = (
                    cell_slope_score * w["slope"] +
                    rain_score * w["rainfall"] +
                    cell_t_score * w["terrain"]
                )

                if cell_slope_score > 45 and rain_score > 45:
                    cell_risk += min(
                        8.0,
                        8.0 * ((cell_slope_score - 45) / 55) *
                        ((rain_score - 45) / 55)
                    )
                cell_risk = round(self._clip(cell_risk), 1)
                cell_class = self.classify_risk(cell_risk)

                coords = [
                    [round(cell_lon-half_dlon, 5), round(cell_lat-half_dlat, 5)],
                    [round(cell_lon+half_dlon, 5), round(cell_lat-half_dlat, 5)],
                    [round(cell_lon+half_dlon, 5), round(cell_lat+half_dlat, 5)],
                    [round(cell_lon-half_dlon, 5), round(cell_lat+half_dlat, 5)],
                    [round(cell_lon-half_dlon, 5), round(cell_lat-half_dlat, 5)]
                ]

                features.append({
                    "type": "Feature",
                    "geometry": {"type": "Polygon", "coordinates": [coords]},
                    "properties": {
                        "row": i,
                        "col": j,
                        "lat": round(cell_lat, 5),
                        "lon": round(cell_lon, 5),
                        "elevation": round(elev, 1),
                        "slope_deg": round(slope_deg, 1),
                        "slope_score": round(cell_slope_score, 1),
                        "rainfall_mm": round(rain_data.get("rain_72h_mm", 0), 1),
                        "rainfall_score": round(rain_score, 1),
                        "terrain_score": round(cell_t_score, 1),
                        "vulnerability_score": cell_risk,
                        "risk_level": cell_class["name"],
                        "risk_code": cell_class["code"],
                        "color": cell_class["color"]
                    }
                })

        return {"type": "FeatureCollection", "features": features}
