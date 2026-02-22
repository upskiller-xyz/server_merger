"""Simulation data model"""

from dataclasses import dataclass
import numpy as np

from src.components.window import WindowGeometry
from src.models.image_scale import ImageScale


@dataclass
class SimulationData:
    """Represents simulation data for a window"""
    df_values: np.ndarray  # 2D array of DF values (0-10)
    mask: np.ndarray  # 2D binary mask (0 or 1)
    window: WindowGeometry
    scale: ImageScale
