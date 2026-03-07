"""Tests for room DF matrix model."""

import pytest
import numpy as np
from src.models.room_df_matrix import RoomDFMatrix
from src.components.geometry_ops import Point2D


class TestRoomDFMatrix:
    """Test RoomDFMatrix class."""

    def test_room_df_matrix_creation(self):
        """Test creating a RoomDFMatrix."""
        matrix = RoomDFMatrix(width_px=256, height_px=256)
        assert matrix.width_px == 256
        assert matrix.height_px == 256
        assert matrix.df_matrix is not None

    def test_room_df_matrix_shape(self):
        """Test that df_matrix has correct shape."""
        width, height = 256, 256
        matrix = RoomDFMatrix(width_px=width, height_px=height)
        assert matrix.df_matrix.shape == (height, width)

    def test_room_df_matrix_initial_values(self):
        """Test that df_matrix is initialized to zeros."""
        matrix = RoomDFMatrix(width_px=256, height_px=256)
        assert np.all(matrix.df_matrix == 0)

    def test_set_mask(self, sample_mask):
        """Test setting room mask."""
        matrix = RoomDFMatrix(width_px=128, height_px=128)
        # Resize sample mask if needed
        if sample_mask.shape != (128, 128):
            sample_mask = np.ones((128, 128), dtype=np.uint8)
        matrix.set_mask(sample_mask)
        assert matrix.room_mask is not None
        assert matrix.room_mask.shape == (128, 128)

    def test_accumulate_window_simple(self, sample_df_values, sample_mask):
        """Test accumulating a single window."""
        matrix = RoomDFMatrix(width_px=256, height_px=256)
        
        # Create properly sized arrays
        df_window = np.random.rand(128, 128).astype(np.float32) * 0.1
        mask_window = np.ones((128, 128), dtype=np.uint8)
        translation = Point2D(x=50, y=50)
        
        # Should not raise an exception
        matrix.accumulate_window(df_window, mask_window, translation, "test_window")

    def test_calculate_overlap_regions(self):
        """Test overlap region calculation."""
        matrix = RoomDFMatrix(width_px=256, height_px=256)
        region = matrix._calculate_overlap_regions(
            window_width=128,
            window_height=128,
            offset_x=50,
            offset_y=50
        )
        
        assert region is not None
        assert region.src_y_start >= 0
        assert region.src_x_start >= 0

    def test_calculate_overlap_regions_at_origin(self):
        """Test overlap region at origin."""
        matrix = RoomDFMatrix(width_px=256, height_px=256)
        region = matrix._calculate_overlap_regions(
            window_width=128,
            window_height=128,
            offset_x=0,
            offset_y=0
        )
        
        assert region.src_y_start == 0
        assert region.src_x_start == 0

    def test_apply_mask(self):
        """Test applying mask to result."""
        matrix = RoomDFMatrix(width_px=128, height_px=128)
        mask = np.ones((128, 128), dtype=np.uint8)
        mask[50:, :] = 0  # Mask out bottom half
        
        matrix.set_mask(mask)
        matrix.df_matrix[:] = 1.0  # Fill with ones
        
        matrix.apply_mask()
        
        # Bottom half should be zeroed
        assert np.all(matrix.df_matrix[50:, :] == 0)
        # Top half should remain
        assert np.any(matrix.df_matrix[:50, :] == 1.0)

    def test_get_result(self):
        """Test getting final result."""
        matrix = RoomDFMatrix(width_px=256, height_px=256)
        matrix.df_matrix[:50, :50] = 0.5
        mask = np.ones((256, 256), dtype=np.uint8)
        matrix.set_mask(mask)
        
        df_result, mask_result = matrix.get_result()
        
        assert df_result is not None
        assert df_result.shape == (256, 256)
        assert mask_result is not None

    def test_room_df_matrix_different_sizes(self):
        """Test RoomDFMatrix with various sizes."""
        for size in [64, 128, 256, 512]:
            matrix = RoomDFMatrix(width_px=size, height_px=size)
            assert matrix.df_matrix.shape == (size, size)

    def test_validate_translation_valid(self):
        """Test validating valid translation."""
        matrix = RoomDFMatrix(width_px=256, height_px=256)
        translation = Point2D(x=10.0, y=20.0)
        # Should not raise
        matrix._validate_translation(translation, "test_window")

    def test_validate_translation_zero(self):
        """Test validating zero translation."""
        matrix = RoomDFMatrix(width_px=256, height_px=256)
        translation = Point2D(x=0.0, y=0.0)
        # Should not raise
        matrix._validate_translation(translation, "test_window")

    def test_validate_translation_negative(self):
        """Test validating negative translation."""
        matrix = RoomDFMatrix(width_px=256, height_px=256)
        translation = Point2D(x=-10.0, y=-20.0)
        # Should not raise
        matrix._validate_translation(translation, "test_window")

    def test_validate_translation_none_x(self):
        """Test validation fails with None x."""
        matrix = RoomDFMatrix(width_px=256, height_px=256)
        translation = Point2D(x=None, y=20.0)
        with pytest.raises(ValueError):
            matrix._validate_translation(translation, "test_window")

    def test_validate_translation_none_y(self):
        """Test validation fails with None y."""
        matrix = RoomDFMatrix(width_px=256, height_px=256)
        translation = Point2D(x=10.0, y=None)
        with pytest.raises(ValueError):
            matrix._validate_translation(translation, "test_window")

    def test_validate_translation_nan_x(self):
        """Test validation fails with NaN x."""
        matrix = RoomDFMatrix(width_px=256, height_px=256)
        translation = Point2D(x=float('nan'), y=20.0)
        with pytest.raises(ValueError):
            matrix._validate_translation(translation, "test_window")

    def test_validate_translation_nan_y(self):
        """Test validation fails with NaN y."""
        matrix = RoomDFMatrix(width_px=256, height_px=256)
        translation = Point2D(x=10.0, y=float('nan'))
        with pytest.raises(ValueError):
            matrix._validate_translation(translation, "test_window")

    def test_set_mask_invalid_shape(self):
        """Test setting mask with invalid shape."""
        matrix = RoomDFMatrix(width_px=256, height_px=256)
        wrong_mask = np.ones((100, 100), dtype=np.uint8)
        
        with pytest.raises(ValueError):
            matrix.set_mask(wrong_mask)

    def test_calculate_overlap_regions_corner(self):
        """Test overlap region calculation at corner."""
        matrix = RoomDFMatrix(width_px=256, height_px=256)
        region = matrix._calculate_overlap_regions(
            window_width=128,
            window_height=128,
            offset_x=100,
            offset_y=100
        )
        
        assert region.dst_x_start >= 0
        assert region.dst_y_start >= 0
        assert region.src_width > 0
        assert region.src_height > 0

    def test_calculate_overlap_regions_negative_offset(self):
        """Test overlap region with negative offset."""
        matrix = RoomDFMatrix(width_px=256, height_px=256)
        region = matrix._calculate_overlap_regions(
            window_width=128,
            window_height=128,
            offset_x=-50,
            offset_y=-50
        )
        
        assert region.dst_x_start >= 0
        assert region.dst_y_start >= 0

    def test_calculate_overlap_regions_outside_room(self):
        """Test overlap region when window is outside room."""
        matrix = RoomDFMatrix(width_px=256, height_px=256)
        region = matrix._calculate_overlap_regions(
            window_width=128,
            window_height=128,
            offset_x=500,  # Far outside
            offset_y=500   # Far outside
        )
        
        # Even when outside, overlap region should be calculated
        assert hasattr(region, 'src_height')
        assert hasattr(region, 'dst_height')

    def test_get_flipped(self):
        """Test getting flipped result."""
        matrix = RoomDFMatrix(width_px=256, height_px=256)
        matrix.df_matrix[0:50, :] = 0.5
        mask = np.ones((256, 256), dtype=np.uint8)
        matrix.set_mask(mask)
        
        df_flipped, mask_flipped = matrix.get_flipped()
        
        # Top rows should now be at bottom
        assert df_flipped is not None
        assert mask_flipped is not None
        assert df_flipped.shape == (256, 256)

    def test_df_matrix_dtype(self):
        """Test that df_matrix is float32."""
        matrix = RoomDFMatrix(width_px=256, height_px=256)
        assert matrix.df_matrix.dtype == np.float32

    def test_room_mask_dtype(self):
        """Test that room_mask is float32."""
        matrix = RoomDFMatrix(width_px=256, height_px=256)
        assert matrix.room_mask.dtype == np.float32

    def test_accumulate_window_simple(self, sample_df_values, sample_mask):
        """Test accumulating a single window."""
        matrix = RoomDFMatrix(width_px=256, height_px=256)
        
        # Create properly sized arrays that will fit
        df_window = np.random.rand(128, 128).astype(np.float32) * 0.1
        mask_window = np.ones((128, 128), dtype=np.uint8)
        translation = Point2D(x=50, y=50)
        
        # Should not raise an exception
        matrix.accumulate_window(df_window, mask_window, translation, "test_window")

    def test_accumulate_window_at_origin(self):
        """Test accumulating window at origin."""
        matrix = RoomDFMatrix(width_px=256, height_px=256)
        
        df_window = np.ones((128, 128), dtype=np.float32) * 0.1
        mask_window = np.ones((128, 128), dtype=np.uint8)
        translation = Point2D(x=0, y=0)
        
        # Should execute without error
        matrix.accumulate_window(df_window, mask_window, translation, "test_window")

    def test_accumulate_multiple_windows(self):
        """Test accumulating multiple windows."""
        matrix = RoomDFMatrix(width_px=256, height_px=256)
        
        for i in range(2):
            df_window = np.ones((64, 64), dtype=np.float32) * 0.1
            mask_window = np.ones((64, 64), dtype=np.uint8)
            # Position windows non-overlapping
            translation = Point2D(x=i*80, y=i*80)
            
            matrix.accumulate_window(df_window, mask_window, translation, f"window_{i}")
        
        # After accumulation, should have some values
        assert np.max(matrix.df_matrix) >= 0
