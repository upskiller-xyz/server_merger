"""
Scale Converter

Handles conversions between meters and pixels for DF aggregation.
"""

from src.components.geometry_ops import Point2D
import numpy as np


class ScaleConverter:
    """Converts between meters and pixels using a fixed scale factor"""

    def __init__(self, meters_per_pixel: float):
        """
        Initialize converter with scale.

        Args:
            meters_per_pixel: Scale factor (e.g., 0.1 = 1 pixel represents 0.1 meters)
        """
        self.meters_per_pixel = meters_per_pixel

    def meters_to_pixels(self, meters: float) -> int:
        """
        Convert meters to pixels.

        Args:
            meters: Distance in meters

        Returns:
            Distance in pixels (rounded)
        """
        return int(np.round(meters / self.meters_per_pixel))

    def point_meters_to_pixels(self, point: Point2D) -> Point2D:
        """
        Convert a point from meters to pixels.

        Args:
            point: Point in meters

        Returns:
            Point in pixels
        """
        return Point2D(
            np.round(point.x / self.meters_per_pixel) ,
            np.round(point.y / self.meters_per_pixel) 
        )

    def pixels_to_meters(self, pixels: int) -> float:
        """
        Convert pixels to meters.

        Args:
            pixels: Distance in pixels

        Returns:
            Distance in meters
        """
        return pixels * self.meters_per_pixel

    def point_pixels_to_meters(self, point: Point2D) -> Point2D:
        """
        Convert a point from pixels to meters.

        Args:
            point: Point in pixels

        Returns:
            Point in meters
        """
        return Point2D(
            point.x * self.meters_per_pixel,
            point.y * self.meters_per_pixel
        )
