"""
Pytest configuration and shared fixtures for the test suite.
"""

import pytest
import numpy as np
from pathlib import Path
from src.components.window import WindowGeometry, RoomPolygon
from src.components.geometry_ops import Point2D
from src.models import SimulationData
from src.models.image_scale import ImageScale


@pytest.fixture
def sample_df_values():
    """Create sample DF values array (128x128)."""
    return np.random.rand(128, 128).astype(np.float32) * 0.1


@pytest.fixture
def sample_mask():
    """Create sample mask array (128x128) with white square."""
    mask = np.zeros((128, 128), dtype=np.uint8)
    mask[20:100, 20:100] = 1
    return mask


@pytest.fixture
def sample_large_df_values():
    """Create sample large DF values array (384x384)."""
    return np.random.rand(384, 384).astype(np.float32) * 0.1


@pytest.fixture
def sample_large_mask():
    """Create sample large mask array (384x384)."""
    mask = np.zeros((384, 384), dtype=np.uint8)
    mask[50:300, 50:300] = 1
    return mask


@pytest.fixture
def sample_window():
    """Create a sample window geometry."""
    return WindowGeometry(
        x1=0.0,
        y1=1.0,
        z1=0.0,
        x2=0.4,
        y2=3.8,
        z2=2.0,
        direction_angle=0.0
    )


@pytest.fixture
def sample_room_polygon():
    """Create a sample room polygon."""
    coords = [
        (0.0, 0.0),
        (10.0, 0.0),
        (10.0, 10.0),
        (0.0, 10.0)
    ]
    return RoomPolygon(coords)


@pytest.fixture
def sample_image_scale():
    """Create a sample ImageScale."""
    return ImageScale(size=384, meters_per_pixel=0.1)


@pytest.fixture
def sample_simulation_data(sample_window, sample_large_df_values, sample_large_mask, sample_image_scale):
    """Create sample simulation data."""
    return SimulationData(
        window=sample_window,
        df_values=sample_large_df_values,
        mask=sample_large_mask,
        scale=sample_image_scale
    )


@pytest.fixture
def temp_test_dir(tmp_path):
    """Create a temporary test directory."""
    return tmp_path
