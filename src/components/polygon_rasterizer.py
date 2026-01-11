from typing import List, Tuple, Any, Union, Dict, Callable
from dataclasses import dataclass
from abc import ABC, abstractmethod
import cv2
import numpy as np

from src.components.enums import AggregationConstants

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
            polygon: List of [x, y] coordinates in meters
            width: Output width in pixels
            height: Output height in pixels
            scale: Meters per pixel

        Returns:
            Binary mask (height x width)
        """
        

        # Convert polygon coordinates to pixel space
        # Use np.round() to match ScaleConverter's rounding strategy
        polygon_pixels = np.array(
            [[int(np.round(x / scale)), int(np.round(y / scale))] for x, y in polygon],
            dtype=np.int32
        )

        # Create empty mask
        mask = np.zeros((height, width), dtype=np.uint8)

        # Fill polygon
        cv2.fillPoly(mask, [polygon_pixels], AggregationConstants.ARRAY_OFFSET_ONE)

        return mask