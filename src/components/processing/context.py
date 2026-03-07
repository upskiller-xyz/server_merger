"""Processing context and data structures"""

from dataclasses import dataclass
from typing import Tuple, Optional
import numpy as np

from src.components.geometry_ops import Point2D
from src.components.window import WindowGeometry, RoomPolygon


@dataclass
class WindowInputData:
    """Immutable input data for window processing"""
    window_id: str
    window: WindowGeometry
    room_polygon: RoomPolygon


@dataclass
class ImagePair:
    """Pair of DF values and mask arrays at a processing stage"""
    df_values: np.ndarray
    mask: np.ndarray


@dataclass
class PositionData:
    """Window position information in room coordinates"""
    room_coord_meters: Point2D
    room_coord_pixels: Point2D
    ref_px_original: Tuple[int, int]
    ref_px_rotated: Optional[Tuple[int, int]] = None


@dataclass
class CropData:
    """Cropped image data with offset information"""
    images: ImagePair
    offset: Tuple[int, int]


@dataclass
class WindowProcessingContext:
    """
    Context object that passes through the processing pipeline.

    Groups related data semantically for better organization.
    """
    # Input data (immutable)
    input: WindowInputData
    original_images: ImagePair

    # Processing state (populated by steps)
    position: Optional[PositionData] = None
    cropped: Optional[CropData] = None
    translation: Optional[Point2D] = None
