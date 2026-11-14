import math
import numpy as np
from config import Config

class SlopeAnalysisService:
    def __init__(self):
        self.slope_classes = Config.SLOPE_CLASSES

    def calculate_slope(self, elevation_matrix, lats, lons):
        """
        Calculates terrain slope in degrees using 2D central differences.
        elevation_matrix: 2D numpy array or list of elevations (m)
        lats: list of latitudes in descending order (North to South)
        lons: list of longitudes in ascending order (West to East)
        """
        Z = np.array(elevation_matrix, dtype=np.float64)
        nrows, ncols = Z.shape

        center_lat = np.mean(lats)
        # Approximate meter distances per degree
        # 1 deg lat ~ 111,139 m
        # 1 deg lon ~ 111,320 * cos(lat) m
        meters_per_deg_lat = 111139.0
        meters_per_deg_lon = 111320.0 * math.cos(math.radians(center_lat))

        # Grid cell resolutions
        dy = abs(lats[1] - lats[0]) * meters_per_deg_lat if len(lats) > 1 else 100.0
        dx = abs(lons[1] - lons[0]) * meters_per_deg_lon if len(lons) > 1 else 100.0

        # Gradient calculation using numpy
        # np.gradient returns [dZ/di, dZ/dj]
        # along axis 0 (rows/latitude) and axis 1 (cols/longitude)
        gy, gx = np.gradient(Z, dy, dx)

        # Gradient magnitude (rise over run)
        gradient_mag = np.hypot(gx, gy)

        # Slope angle in degrees: arctan(gradient) * 180 / pi
        slope_degrees = np.degrees(np.arctan(gradient_mag))

        center_r, center_c = nrows // 2, ncols // 2
        center_slope = float(slope_degrees[center_r, center_c])
        mean_slope = float(np.mean(slope_degrees))
        max_slope = float(np.max(slope_degrees))
        min_slope = float(np.min(slope_degrees))

        # Representative effective slope accounts for adjacent contributing flank gradient
        effective_slope = max(center_slope, 0.45 * center_slope + 0.55 * max_slope)

        slope_category = self.classify_slope(effective_slope)
        slope_score = self.calculate_slope_score(effective_slope)

        explanation = self.generate_slope_explanation(effective_slope, slope_category["name"])

        return {
            "center_slope_deg": round(effective_slope, 2),
            "point_slope_deg": round(center_slope, 2),
            "mean_slope_deg": round(mean_slope, 2),
            "max_slope_deg": round(max_slope, 2),
            "min_slope_deg": round(min_slope, 2),
            "slope_matrix": slope_degrees.round(2).tolist(),
            "slope_category": slope_category["name"],
            "slope_score": round(slope_score, 1),
            "color": slope_category["color"],
            "description": slope_category["description"],
            "explanation": explanation
        }

    def classify_slope(self, slope_deg):
        """Classify slope according to standard geomorphological categories."""
        if slope_deg < 15.0:
            return self.slope_classes[0] # Low
        elif slope_deg < 30.0:
            return self.slope_classes[1] # Moderate
        elif slope_deg <= 45.0:
            return self.slope_classes[2] # High
        else:
            return self.slope_classes[3] # Very High

    def calculate_slope_score(self, slope_deg):
        """
        Continuous susceptibility curve calibrated around the common
        shallow-slide/debris-flow slope band. Very steep faces remain highly
        hazardous, but the score does not assume that every >45° face is a
        shallow-soil failure.
        """
        x = max(0.0, min(90.0, float(slope_deg)))
        if x <= 5:
            return 2.0 * x
        elif x <= 15:
            return 10.0 + (x - 5.0) * 1.5
        elif x <= 30:
            return 25.0 + (x - 15.0) * 2.4
        elif x <= 45:
            return 61.0 + (x - 30.0) * 2.2
        else:
            return max(70.0, 94.0 - (x - 45.0) * 0.35)

    def generate_slope_explanation(self, slope_deg, category_name):
        """Explain the geomechanical influence of this slope on landslide hazard."""
        if slope_deg < 15.0:
            return (
                f"A gentle slope gradient of {slope_deg:.1f}° generates low tangential shear stress "
                f"({category_name}). Colluvium and regolith remain stable under normal gravitational loads."
            )
        elif slope_deg < 30.0:
            return (
                f"A moderate slope of {slope_deg:.1f}° introduces significant downslope shear force "
                f"({category_name}). Slope stability is conditionally sensitive to moisture saturation and pore-water pressure."
            )
        elif slope_deg <= 45.0:
            return (
                f"A steep slope of {slope_deg:.1f}° approaches and exceeds the internal friction angle (φ) of typical residual soils "
                f"({category_name}). High susceptibility to shallow translational slides and debris flows during intense rain."
            )
        else:
            return (
                f"An extreme precipitous slope of {slope_deg:.1f}° ({category_name}) experiences severe gravitational unbalance. "
                f"High susceptibility to rapid mass-wasting, rockfalls, and runaway translational slips."
            )
