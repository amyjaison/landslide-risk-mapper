import unittest
from backend.risk_calculation import RiskCalculationEngine

class TestRiskCalculationEngine(unittest.TestCase):
    def setUp(self):
        self.engine = RiskCalculationEngine()

    def test_default_weights_sum(self):
        weights = self.engine.weights
        total = weights["slope"] + weights["rainfall"] + weights["terrain"]
        self.assertAlmostEqual(total, 1.0, places=4)
        self.assertEqual(weights["slope"], 0.40)
        self.assertEqual(weights["rainfall"], 0.35)
        self.assertEqual(weights["terrain"], 0.25)

    def test_normalize_weights(self):
        normalized = self.engine.normalize_weights({"slope": 2, "rainfall": 2, "terrain": 1})
        self.assertAlmostEqual(normalized["slope"] + normalized["rainfall"] + normalized["terrain"], 1.0, places=4)
        self.assertAlmostEqual(normalized["slope"], 0.40, places=2)
        self.assertAlmostEqual(normalized["terrain"], 0.20, places=2)

    def test_risk_formula_calculation(self):
        # The new model retains the weighted base score and adds a bounded
        # slope-rainfall interaction because simultaneous triggers are more
        # hazardous than either factor alone.
        result = self.engine.calculate_score(slope_score=80, rainfall_score=60, terrain_score=40)
        self.assertGreater(result["vulnerability_score"], 63.0)
        self.assertLessEqual(result["vulnerability_score"], 71.0)
        self.assertEqual(result["risk_level"], "High Risk")
        self.assertEqual(result["risk_code"], "HIGH")
        self.assertIn("slope_rainfall_synergy", result["adjustments"])

    def test_risk_categories_boundaries(self):
        # Low: <= 25
        low_res = self.engine.calculate_score(15, 10, 20)
        self.assertEqual(low_res["risk_level"], "Low Risk")

        # Moderate: 26 to 50
        # (40 * 0.4) + (40 * 0.35) + (40 * 0.25) = 40.0
        mod_res = self.engine.calculate_score(40, 40, 40)
        self.assertEqual(mod_res["risk_level"], "Moderate Risk")

        # High: 51 to 75
        # (70 * 0.4) + (70 * 0.35) + (70 * 0.25) = 70.0
        high_res = self.engine.calculate_score(70, 70, 70)
        self.assertEqual(high_res["risk_level"], "High Risk")

        # Very High: 76 to 100
        # (90 * 0.4) + (90 * 0.35) + (90 * 0.25) = 90.0
        vhigh_res = self.engine.calculate_score(90, 90, 90)
        self.assertEqual(vhigh_res["risk_level"], "Very High Risk")

    def test_extreme_bounds_handling(self):
        # All zeros
        zero_res = self.engine.calculate_score(0, 0, 0)
        self.assertEqual(zero_res["vulnerability_score"], 0.0)
        self.assertEqual(zero_res["risk_level"], "Low Risk")

        # All 100s
        max_res = self.engine.calculate_score(100, 100, 100)
        self.assertEqual(max_res["vulnerability_score"], 100.0)
        self.assertEqual(max_res["risk_level"], "Very High Risk")

        # Out-of-bounds inputs clamped
        clamped_res = self.engine.calculate_score(-20, 150, 200)
        self.assertTrue(0 <= clamped_res["vulnerability_score"] <= 100)


    def test_historical_evidence_is_bounded(self):
        base = self.engine.calculate_score(60, 60, 60)
        with_history = self.engine.calculate_score(
            60, 60, 60, historical_count=5, nearest_historical_km=5
        )
        self.assertGreater(with_history["vulnerability_score"], base["vulnerability_score"])
        self.assertLessEqual(
            with_history["vulnerability_score"] - base["vulnerability_score"], 5.0
        )

    def test_confidence_output(self):
        result = self.engine.calculate_score(
            40, 40, 40,
            data_quality={"elevation_fallback": True, "rainfall_fallback": True}
        )
        self.assertIn(result["confidence"]["label"], ["Low", "Moderate", "High"])
        self.assertGreaterEqual(result["confidence"]["score"], 35)
        self.assertLessEqual(result["confidence"]["score"], 95)

if __name__ == '__main__':
    unittest.main()
