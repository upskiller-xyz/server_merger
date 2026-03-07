"""Processed window model"""

from dataclasses import dataclass
import numpy as np

from src.components.geometry_ops import Point2D


@dataclass
class ProcessedWindow:
    """Represents a fully processed window ready for accumulation"""
    df_cropped: np.ndarray
    mask_cropped: np.ndarray
    translation: Point2D
