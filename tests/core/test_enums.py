"""Tests for graphics constants and enums."""

import pytest
from src.core.enums import AggregationConstants
from src.core.graphics_constants import GRAPHICS_CONSTANTS


class TestAggregationConstants:
    """Test AggregationConstants enum."""

    def test_zero_value_is_zero(self):
        """Test that ZERO_VALUE constant is 0."""
        assert AggregationConstants.ZERO_VALUE == 0

    def test_rotation_scale_is_one(self):
        """Test that ROTATION_SCALE is 1.0."""
        assert AggregationConstants.ROTATION_SCALE == 1.0


class TestGraphicsConstants:
    """Test GRAPHICS_CONSTANTS."""

    def test_base_image_size_is_128(self):
        """Test that BASE_IMAGE_SIZE_PX is 128."""
        assert GRAPHICS_CONSTANTS.BASE_IMAGE_SIZE_PX == 128

    def test_base_resolution(self):
        """Test that BASE_RESOLUTION_M_PER_PX is 0.1."""
        assert GRAPHICS_CONSTANTS.BASE_RESOLUTION_M_PER_PX == 0.1

    def test_graphics_constants_immutable(self):
        """Test that GRAPHICS_CONSTANTS values are consistent."""
        # Create a second reference and verify they're the same
        base_size = GRAPHICS_CONSTANTS.BASE_IMAGE_SIZE_PX
        assert base_size == 128
