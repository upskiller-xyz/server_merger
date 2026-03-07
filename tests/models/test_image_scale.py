"""Tests for image scale model."""

import pytest
from src.models.image_scale import ImageScale
from src.core.graphics_constants import GRAPHICS_CONSTANTS


class TestImageScale:
    """Test ImageScale class."""

    def test_image_scale_creation(self):
        """Test creating ImageScale."""
        scale = ImageScale(size=384, meters_per_pixel=0.1)
        assert scale.size == 384
        assert scale.meters_per_pixel == pytest.approx(0.1)

    def test_image_scale_window_offset(self):
        """Test window offset calculation."""
        scale = ImageScale(size=128, meters_per_pixel=0.1)
        offset = scale.window_offset
        # At reference size (128), should be WINDOW_OFFSET_PX
        assert offset == GRAPHICS_CONSTANTS.WINDOW_OFFSET_PX

    def test_image_scale_window_offset_scaled(self):
        """Test window offset with different scale."""
        scale = ImageScale(size=256, meters_per_pixel=0.05)
        offset = scale.window_offset
        # At 256 (2x reference), offset should be 2x
        expected = GRAPHICS_CONSTANTS.WINDOW_OFFSET_PX * 2
        assert offset == expected

    def test_image_scale_window_offset_half_size(self):
        """Test window offset at half size."""
        scale = ImageScale(size=64, meters_per_pixel=0.2)
        offset = scale.window_offset
        # At 64 (0.5x reference), offset should be 0.5x
        expected = GRAPHICS_CONSTANTS.WINDOW_OFFSET_PX // 2
        assert offset == expected

    def test_image_scale_from_image_size(self):
        """Test creating scale from image size."""
        scale = ImageScale.from_image_size(128)
        assert scale.size == 128
        assert scale.meters_per_pixel == pytest.approx(GRAPHICS_CONSTANTS.BASE_RESOLUTION_M_PER_PX)

    def test_image_scale_from_image_size_double(self):
        """Test from_image_size with double size."""
        scale = ImageScale.from_image_size(256)
        assert scale.size == 256
        # meters_per_pixel should double at 2x size
        expected = GRAPHICS_CONSTANTS.BASE_RESOLUTION_M_PER_PX * 2
        assert scale.meters_per_pixel == pytest.approx(expected)

    def test_image_scale_from_image_size_half(self):
        """Test from_image_size with half size."""
        scale = ImageScale.from_image_size(64)
        assert scale.size == 64
        # meters_per_pixel should be half at 0.5x size
        expected = GRAPHICS_CONSTANTS.BASE_RESOLUTION_M_PER_PX * 0.5
        assert scale.meters_per_pixel == pytest.approx(expected)

    def test_image_scale_different_sizes(self):
        """Test ImageScale with various sizes."""
        for size in [64, 128, 256, 512]:
            scale = ImageScale(size=size, meters_per_pixel=0.1)
            assert scale.size == size

    def test_image_scale_window_offset_proportional(self):
        """Test that window offset scales proportionally."""
        scale_128 = ImageScale(size=128, meters_per_pixel=0.1)
        scale_256 = ImageScale(size=256, meters_per_pixel=0.05)
        
        # Offset should scale with size
        ratio = scale_256.size / scale_128.size
        assert scale_256.window_offset == pytest.approx(scale_128.window_offset * ratio)

    def test_image_scale_reference_consistency(self):
        """Test that reference size gives reference scale."""
        scale = ImageScale.from_image_size(GRAPHICS_CONSTANTS.BASE_IMAGE_SIZE_PX)
        assert scale.size == GRAPHICS_CONSTANTS.BASE_IMAGE_SIZE_PX
        assert scale.meters_per_pixel == pytest.approx(GRAPHICS_CONSTANTS.BASE_RESOLUTION_M_PER_PX)

    def test_image_scale_zero_meters_per_pixel(self):
        """Test handling of zero or very small meters_per_pixel."""
        scale = ImageScale(size=128, meters_per_pixel=0.0001)
        assert scale.meters_per_pixel == pytest.approx(0.0001)

    def test_image_scale_large_meters_per_pixel(self):
        """Test handling of large meters_per_pixel."""
        scale = ImageScale(size=128, meters_per_pixel=1.0)
        assert scale.meters_per_pixel == pytest.approx(1.0)

    def test_image_scale_window_offset_is_int(self):
        """Test that window_offset is integer."""
        scale = ImageScale(size=100, meters_per_pixel=0.1)
        offset = scale.window_offset
        assert isinstance(offset, int)

    def test_image_scale_from_image_size_various_sizes(self):
        """Test from_image_size with various image sizes."""
        for size in [32, 64, 128, 256, 384, 512, 1024]:
            scale = ImageScale.from_image_size(size)
            assert scale.size == size
            assert scale.meters_per_pixel > 0
