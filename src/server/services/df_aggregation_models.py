"""
Data models for Daylight Factor Aggregation

This module contains data classes used for DF aggregation.
"""

from dataclasses import dataclass
import numpy as np

from src.components.graphics_constants import GRAPHICS_CONSTANTS
from src.components.window import WindowGeometry


@dataclass
class ImageScale:
    """
    Image scale configuration calculated proportionally from reference scale.
    Reference: 128x128 image with 0.1 m/px, window_offset = 12px
    """
    size: int
    meters_per_pixel: float

    @property
    def window_offset(self) -> int:
        """Calculate window offset proportionally from reference (12px at 128px)."""
        scale_factor = self.size / GRAPHICS_CONSTANTS.BASE_IMAGE_SIZE_PX
        return int(GRAPHICS_CONSTANTS.WINDOW_OFFSET_PX * scale_factor)

    @classmethod
    def from_image_size(cls, img_size: int) -> 'ImageScale':
        """
        Calculate scale proportionally based on reference (128px = 0.1m/px).

        Args:
            img_size: Size of the square image

        Returns:
            ImageScale instance with calculated meters_per_pixel
        """
        # Reference scale: 128px = 0.1 m/px
        scale_factor = img_size / GRAPHICS_CONSTANTS.BASE_IMAGE_SIZE_PX
        meters_per_pixel = GRAPHICS_CONSTANTS.BASE_RESOLUTION_M_PER_PX * scale_factor

        return cls(size=img_size, meters_per_pixel=meters_per_pixel)


@dataclass
class SimulationData:
    """Represents simulation data for a window"""
    df_values: np.ndarray  # 2D array of DF values (0-10)
    mask: np.ndarray  # 2D binary mask (0 or 1)
    window: WindowGeometry
    scale: ImageScale


@dataclass
class OverlapRegion:
    """Defines source and destination regions for overlap calculations"""
    src_y_start: int
    src_y_end: int
    src_x_start: int
    src_x_end: int
    dst_y_start: int
    dst_y_end: int
    dst_x_start: int
    dst_x_end: int

    @property
    def src_height(self) -> int:
        """Source region height"""
        return self.src_y_end - self.src_y_start

    @property
    def src_width(self) -> int:
        """Source region width"""
        return self.src_x_end - self.src_x_start

    @property
    def dst_height(self) -> int:
        """Destination region height"""
        return self.dst_y_end - self.dst_y_start

    @property
    def dst_width(self) -> int:
        """Destination region width"""
        return self.dst_x_end - self.dst_x_start


@dataclass
class ProcessedWindow:
    """Represents a fully processed window ready for accumulation"""
    df_cropped: np.ndarray
    mask_cropped: np.ndarray
    translation: 'Point2D'
