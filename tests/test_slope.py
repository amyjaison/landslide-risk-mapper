import unittest
import numpy as np
from backend.slope_analysis import SlopeAnalysisService

class TestSlopeAnalysisService(unittest.TestCase):
    def setUp(self):
        self.service = SlopeAnalysisService()

    def test_flat_terrain_slope(self):
        # 5x5 perfectly flat elevation matrix
        flat_matrix = np.full((5, 5), 500.0)
        lats = [11.54, 11.53, 11.52, 11.51, 11.50]
        lons = [76.10, 76.11, 76.12, 76.13, 76.14]

        res = self.service.calculate_slope(flat_matrix, lats, lons)
        self.assertAlmostEqual(res["center_slope_deg"], 0.0, places=1)
        self.assertEqual(res["slope_category"], "Gentle / Low (0–15°)")
        self.assertAlmostEqual(res["slope_score"], 0.0, places=1)

    def test_steep_slope_classification(self):
        # Test classification function directly
        c_low = self.service.classify_slope(8.0)
        self.assertIn("0–15°", c_low["name"])

        c_mod = self.service.classify_slope(22.0)
        self.assertIn("15–30°", c_mod["name"])

        c_high = self.service.classify_slope(35.0)
        self.assertIn("30–45°", c_high["name"])

        c_vhigh = self.service.classify_slope(52.0)
        self.assertIn(">45°", c_vhigh["name"])

    def test_slope_score_monotonicity(self):
        # Slope score must increase monotonically with slope angle
        s5 = self.service.calculate_slope_score(5.0)
        s20 = self.service.calculate_slope_score(20.0)
        s38 = self.service.calculate_slope_score(38.0)
        s60 = self.service.calculate_slope_score(60.0)

        self.assertTrue(0 <= s5 < s20 < s38 < s60 <= 100)

if __name__ == '__main__':
    unittest.main()

