"""Tests that a blocked/rate-limited provider does not break the app."""
import tempfile
import unittest
from unittest import mock

from backend.elevation import ElevationService


class TestProviderFallbacks(unittest.TestCase):

    def test_elevation_uses_backup_provider(self):
        svc = ElevationService(tempfile.mkdtemp())
        with mock.patch.object(svc, "_fetch_open_meteo", return_value=None), \
             mock.patch.object(svc, "_fetch_opentopodata",
                               side_effect=lambda la, lo: [900.0] * len(la)):
            r = svc.fetch_elevation_grid(12.9716, 77.5946)
        self.assertFalse(r["is_fallback"])
        self.assertEqual(r["center_elevation"], 900.0)
        self.assertIn("OpenTopoData", r["source"])

    def test_elevation_offline_model_only_as_last_resort(self):
        svc = ElevationService(tempfile.mkdtemp())
        with mock.patch.object(svc, "_fetch_open_meteo", return_value=None), \
             mock.patch.object(svc, "_fetch_opentopodata", return_value=None):
            r = svc.fetch_elevation_grid(12.9716, 77.5946)
        self.assertTrue(r["is_fallback"])


if __name__ == "__main__":
    unittest.main()
