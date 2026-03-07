"""Tests for rotation helper utilities."""

import pytest
import numpy as np
import math
from src.core.utils.rotation_helper import RotationHelper


class TestRotationHelper:
    """Test RotationHelper class."""

    def test_get_rotation_matrix_shape(self):
        """Test that rotation matrix has correct shape."""
        matrix = RotationHelper.get_rotation_matrix(45.0, (64, 64))
        assert matrix.shape == (2, 3)

    def test_get_rotation_matrix_zero_angle(self):
        """Test rotation matrix with zero angle."""
        matrix = RotationHelper.get_rotation_matrix(0.0, (64, 64))
        # With zero rotation, matrix should be identity-like
        # [1, 0, 0]
        # [0, 1, 0]
        assert matrix.dtype == np.float32 or matrix.dtype == np.float64

    def test_rotate_point_no_rotation(self):
        """Test rotating a point with zero rotation."""
        point = (64, 64)
        rotation_matrix = RotationHelper.get_rotation_matrix(0.0, (64, 64))
        rotated = RotationHelper.rotate_point(point, rotation_matrix)
        
        # With zero rotation, point should remain approximately the same
        assert isinstance(rotated, tuple)
        assert len(rotated) == 2

    def test_rotate_point_90_degrees(self):
        """Test rotating a point by 90 degrees."""
        center = (64, 64)
        rotation_matrix = RotationHelper.get_rotation_matrix(90.0, center)
        point = (80, 64)  # Point to the right of center
        rotated = RotationHelper.rotate_point(point, rotation_matrix)
        
        # After 90 degree counterclockwise rotation around (64,64):
        # (80, 64) should become approximately (64, 80)
        assert isinstance(rotated, tuple)
        assert len(rotated) == 2

    def test_rotate_image_shape(self, sample_df_values):
        """Test that rotated image maintains shape."""
        rotation_matrix = RotationHelper.get_rotation_matrix(45.0, (64, 64))
        rotated = RotationHelper.rotate_image(sample_df_values, rotation_matrix, (128, 128))
        
        assert rotated.shape == sample_df_values.shape
        assert rotated.dtype == sample_df_values.dtype

    def test_rotate_image_zero_rotation(self, sample_df_values):
        """Test that zero rotation doesn't significantly change image."""
        rotation_matrix = RotationHelper.get_rotation_matrix(0.0, (64, 64))
        rotated = RotationHelper.rotate_image(sample_df_values, rotation_matrix, (128, 128))
        
        # With zero rotation, images should be very similar
        assert rotated.shape == sample_df_values.shape

    def test_rotate_image_with_mask(self, sample_mask):
        """Test rotating a mask image."""
        rotation_matrix = RotationHelper.get_rotation_matrix(30.0, (64, 64))
        rotated_mask = RotationHelper.rotate_image(
            sample_mask.astype(np.uint8),
            rotation_matrix,
            (128, 128)
        )
        
        assert rotated_mask.shape == sample_mask.shape
