"""Tests for simulation data model."""

import pytest
import numpy as np
from src.models.simulation_data import SimulationData
from src.models.image_scale import ImageScale


class TestSimulationData:
    """Test SimulationData model."""

    def test_simulation_data_creation(self, sample_window, sample_large_df_values, sample_large_mask, sample_image_scale):
        """Test creating SimulationData."""
        sim_data = SimulationData(
            window=sample_window,
            df_values=sample_large_df_values,
            mask=sample_large_mask,
            scale=sample_image_scale
        )
        
        assert sim_data.window is not None
        assert sim_data.df_values.shape == (384, 384)
        assert sim_data.mask.shape == (384, 384)
        assert sim_data.scale is not None

    def test_simulation_data_with_different_sizes(self, sample_window):
        """Test SimulationData with various input sizes."""
        for size in [256, 384, 512]:
            df = np.random.rand(size, size).astype(np.float32)
            mask = np.ones((size, size), dtype=np.uint8)
            scale = ImageScale(size=size, meters_per_pixel=0.1)
            
            sim_data = SimulationData(
                window=sample_window,
                df_values=df,
                mask=mask,
                scale=scale
            )
            
            assert sim_data.df_values.shape == (size, size)
            assert sim_data.mask.shape == (size, size)
            assert sim_data.scale.size == size
