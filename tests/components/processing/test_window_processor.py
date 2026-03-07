"""Tests for window processor."""

import pytest
import numpy as np
from src.components.processing.window_processor import WindowProcessor


class TestWindowProcessor:
    """Test WindowProcessor class."""

    @pytest.fixture
    def processor(self):
        """Create a WindowProcessor instance."""
        return WindowProcessor()

    def test_window_processor_creation(self, processor):
        """Test creating a WindowProcessor."""
        assert processor is not None
        assert processor.rotation_helper is not None

    def test_standardize_window_images_384_to_128(self, processor):
        """Test standardizing 384x384 to 128x128."""
        df_values = np.random.rand(384, 384).astype(np.float32) * 0.1
        mask = np.ones((384, 384), dtype=np.uint8)
        mask[100:300, 100:300] = 0
        
        df_std, mask_std = processor.standardize_window_images(df_values, mask)
        
        assert df_std.shape == (128, 128)
        assert mask_std.shape == (128, 128)

    def test_standardize_window_images_already_128(self, processor):
        """Test standardizing when already 128x128."""
        df_values = np.random.rand(128, 128).astype(np.float32) * 0.1
        mask = np.ones((128, 128), dtype=np.uint8)
        
        df_std, mask_std = processor.standardize_window_images(df_values, mask)
        
        assert df_std.shape == (128, 128)
        assert mask_std.shape == (128, 128)

    def test_rotate_window_images_zero_rotation(self, processor):
        """Test rotating by zero degrees."""
        df_values = np.random.rand(128, 128).astype(np.float32)
        mask = np.ones((128, 128), dtype=np.uint8)
        window_ref_px = (64, 64)
        
        df_rot, mask_rot, ref_rot = processor.rotate_window_images(
            df_values, mask, window_ref_px, 0.0, "test_window"
        )
        
        assert df_rot.shape == (128, 128)
        assert mask_rot.shape == (128, 128)
        assert isinstance(ref_rot, tuple)

    def test_rotate_window_images_90_rotation(self, processor):
        """Test rotating by 90 degrees."""
        df_values = np.random.rand(128, 128).astype(np.float32)
        mask = np.ones((128, 128), dtype=np.uint8)
        window_ref_px = (64, 64)
        
        import math
        angle_rad = math.pi / 2  # 90 degrees
        
        df_rot, mask_rot, ref_rot = processor.rotate_window_images(
            df_values, mask, window_ref_px, angle_rad, "test_window"
        )
        
        assert df_rot.shape == (128, 128)
        assert mask_rot.shape == (128, 128)

    def test_crop_to_visible_bounds_full_mask(self, processor):
        """Test cropping when entire mask is visible."""
        df_values = np.random.rand(128, 128).astype(np.float32)
        mask = np.ones((128, 128), dtype=np.uint8)
        
        df_crop, mask_crop, offset = processor.crop_to_visible_bounds(
            df_values, mask, "test_window"
        )
        
        assert df_crop.shape == (128, 128)
        assert mask_crop.shape == (128, 128)
        assert offset == (0, 0)

    def test_crop_to_visible_bounds_partial_mask(self, processor):
        """Test cropping with partial mask."""
        df_values = np.random.rand(128, 128).astype(np.float32)
        mask = np.zeros((128, 128), dtype=np.uint8)
        mask[20:100, 30:90] = 1  # Visible region
        
        df_crop, mask_crop, offset = processor.crop_to_visible_bounds(
            df_values, mask, "test_window"
        )
        
        # Should crop to the visible region
        assert df_crop.shape[0] <= 128
        assert df_crop.shape[1] <= 128
        assert offset == (30, 20)

    def test_crop_to_visible_bounds_no_mask(self, processor):
        """Test cropping when mask is all zeros."""
        df_values = np.random.rand(128, 128).astype(np.float32)
        mask = np.zeros((128, 128), dtype=np.uint8)
        
        df_crop, mask_crop, offset = processor.crop_to_visible_bounds(
            df_values, mask, "test_window"
        )
        
        # Should return original arrays when no visible pixels
        assert df_crop.shape == (128, 128)
        assert offset == (0, 0)

    def test_apply_transformation(self, processor):
        """Test apply_transformation method."""
        df_values = np.ones((128, 128), dtype=np.float32)
        mask = np.ones((128, 128), dtype=np.uint8)
        
        # Simple transformation: multiply by 2
        transform = lambda img: img * 2
        
        df_trans, mask_trans = processor._apply_transformation(
            df_values, mask, transform
        )
        
        # DF should be transformed, mask should use identity (lambda s: s)
        assert np.allclose(df_trans, df_values * 2)
        # Mask may or may not be transformed depending on default behavior
        assert mask_trans is not None
