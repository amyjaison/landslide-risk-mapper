import unittest
import json
from app import create_app

class TestLandslideRiskMapperAPI(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def test_health_endpoint(self):
        resp = self.client.get('/api/health')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "healthy")
        self.assertIn("weights", data)

    def test_search_endpoint(self):
        # Valid search
        resp = self.client.get('/api/search?location=Wayanad')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data["success"])
        self.assertGreater(data["count"], 0)

        # Missing location parameter
        err_resp = self.client.get('/api/search')
        self.assertEqual(err_resp.status_code, 400)

    def test_demo_locations_endpoint(self):
        resp = self.client.get('/api/demo-locations')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data["success"])
        self.assertGreaterEqual(len(data["locations"]), 4)

    def test_location_endpoint_valid_coordinates(self):
        # Test Wayanad coordinates
        resp = self.client.get('/api/location?lat=11.5273&lon=76.1264')
        self.assertEqual(resp.status_code, 200)
        payload = resp.get_json()
        self.assertTrue(payload["success"])
        data = payload["data"]

        # Validate sections
        self.assertIn("elevation", data)
        self.assertIn("slope", data)
        self.assertIn("rainfall", data)
        self.assertIn("terrain", data)
        self.assertIn("risk", data)
        self.assertIn("grid_geojson", data)
        self.assertIn("historical", data)

        # Validate risk score range
        v_score = data["risk"]["vulnerability_score"]
        self.assertTrue(0 <= v_score <= 100)
        self.assertIn(data["risk"]["risk_level"], ["Low Risk", "Moderate Risk", "High Risk", "Very High Risk"])

    def test_location_endpoint_monsoon_mode_and_weights(self):
        # Test disaster peak mode with custom weights
        resp = self.client.get('/api/location?lat=11.5273&lon=76.1264&weather_mode=monsoon_event&w_slope=0.50&w_rain=0.30&w_terrain=0.20')
        self.assertEqual(resp.status_code, 200)
        payload = resp.get_json()
        self.assertTrue(payload["success"])
        data = payload["data"]
        self.assertEqual(data["risk"]["weights_used"]["slope"], 0.50)
        self.assertEqual(data["rainfall"]["is_simulation"], True)

    def test_location_endpoint_invalid_coordinates(self):
        # Lat out of bounds
        resp = self.client.get('/api/location?lat=195.0&lon=76.0')
        self.assertEqual(resp.status_code, 400)
        data = resp.get_json()
        self.assertFalse(data["success"])

        # Non-numeric
        resp2 = self.client.get('/api/location?lat=abc&lon=xyz')
        self.assertEqual(resp2.status_code, 400)

    def test_sub_endpoints(self):
        # Slope endpoint
        slope_resp = self.client.get('/api/slope?lat=11.5273&lon=76.1264')
        self.assertEqual(slope_resp.status_code, 200)

        # Rainfall endpoint
        rain_resp = self.client.get('/api/rainfall?lat=11.5273&lon=76.1264')
        self.assertEqual(rain_resp.status_code, 200)

        # Terrain endpoint
        terr_resp = self.client.get('/api/terrain?lat=11.5273&lon=76.1264')
        self.assertEqual(terr_resp.status_code, 200)

        # Historical catalog
        hist_resp = self.client.get('/api/historical?lat=11.5273&lon=76.1264&radius=200')
        self.assertEqual(hist_resp.status_code, 200)

    def test_html_pages_render(self):
        # Home
        r_home = self.client.get('/')
        self.assertEqual(r_home.status_code, 200)
        self.assertIn(b"Landslide Risk Mapper", r_home.data)

        # About
        r_about = self.client.get('/about')
        self.assertEqual(r_about.status_code, 200)

        # Methodology
        r_method = self.client.get('/methodology')
        self.assertEqual(r_method.status_code, 200)
        self.assertIn(b"Weighted Overlay", r_method.data)

        # Data Sources
        r_sources = self.client.get('/data-sources')
        self.assertEqual(r_sources.status_code, 200)

if __name__ == '__main__':
    unittest.main()
