from typing import List, Tuple, Any, Union, Dict, Callable
from dataclasses import dataclass
from abc import ABC, abstractmethod
import cv2
import numpy as np

from src.core.enums import AggregationConstants

class PolygonRasterizer:
    """Rasterizes polygon to binary mask"""

    @staticmethod
    def rasterize(
        polygon: List[List[float]],
        width: int,
        height: int,
        scale: float
    ) -> np.ndarray:
        """
        Convert polygon to binary mask.

        Args:
            polygon: List of [x, y] coordinates in meters (origin at bottom-left)
            width: Output width in pixels
            height: Output height in pixels
            scale: Meters per pixel

        Returns:
            Binary mask (height x width) with origin at top-left (image coordinates)
        """

        # Convert polygon coordinates to pixel space
        # Use np.round() to match ScaleConverter's rounding strategy
        # Flip Y-axis: our coordinate system has origin at bottom-left,
        # but image coordinates have origin at top-left
        polygon_pixels = np.array(
            [[int(np.round(x / scale)), int(np.round((height - 1) - (y / scale)))] for x, y in polygon],
            dtype=np.int32
        )

        # Create empty mask
        mask = np.zeros((height, width), dtype=np.uint8)

        # Fill polygon
        cv2.fillPoly(mask, [polygon_pixels], AggregationConstants.ARRAY_OFFSET_ONE) # type: ignore

        return mask