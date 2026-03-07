"""Tests for scale converter utilities."""

import pytest
import numpy as np
from src.core.utils.scale_converter import ScaleConverter
from src.components.geometry_ops import Point2D


class TestScaleConverter:
    """Test ScaleConverter class."""

    def test_scale_converter_initialization(self):
        """Test ScaleConverter initialization."""
        converter = ScaleConverter(0.1)
        assert converter is not None
        assert converter.meters_per_pixel == pytest.approx(0.1)

    def test_meters_to_pixels_basic(self):
        """Test converting meters to pixels."""
        converter = ScaleConverter(0.1)
        pixels = converter.meters_to_pixels(1.0)
        assert pixels == 10

    def test_meters_to_pixels_zero(self):
        """Test converting zero meters."""
        converter = ScaleConverter(0.1)
        pixels = converter.meters_to_pixels(0.0)
        assert pixels == 0

    def test_meters_to_pixels_small_scale(self):
        """Test converting with small scale."""
        converter = ScaleConverter(0.01)
        pixels = converter.meters_to_pixels(1.0)
        assert pixels == 100

    def test_meters_to_pixels_large_scale(self):
        """Test converting with large scale."""
        converter = ScaleConverter(1.0)
        pixels = converter.meters_to_pixels(10.0)
        assert pixels == 10

    def test_pixels_to_meters_basic(self):
        """Test converting pixels to meters."""
        converter = ScaleConverter(0.1)
        meters = converter.pixels_to_meters(10)
        assert meters == pytest.approx(1.0)

    def test_pixels_to_meters_zero(self):
        """Test converting zero pixels."""
        converter = ScaleConverter(0.1)
        meters = converter.pixels_to_meters(0)
        assert meters == pytest.approx(0.0)

    def test_pixels_to_meters_various_scales(self):
        """Test pixels to meters with various scales."""
        for scale in [0.05, 0.1, 0.2]:
            converter = ScaleConverter(scale)
            meters = converter.pixels_to_meters(100)
            assert meters == pytest.approx(100 * scale)

    def test_point_meters_to_pixels(self):
        """Test converting point from meters to pixels."""
        converter = ScaleConverter(0.1)
        point = Point2D(1.0, 2.0)
        result = converter.point_meters_to_pixels(point)
        assert result.x == pytest.approx(10)
        assert result.y == pytest.approx(20)

    def test_point_meters_to_pixels_zero(self):
        """Test converting zero point."""
        converter = ScaleConverter(0.1)
        point = Point2D(0.0, 0.0)
        result = converter.point_meters_to_pixels(point)
        assert result.x == pytest.approx(0)
        assert result.y == pytest.approx(0)

    def test_point_pixels_to_meters(self):
        """Test converting point from pixels to meters."""
        converter = ScaleConverter(0.1)
        point = Point2D(10, 20)
        result = converter.point_pixels_to_meters(point)
        assert result.x == pytest.approx(1.0)
        assert result.y == pytest.approx(2.0)

    def test_point_pixels_to_meters_zero(self):
        """Test converting zero pixel point."""
        converter = ScaleConverter(0.1)
        point = Point2D(0, 0)
        result = converter.point_pixels_to_meters(point)
        assert result.x == pytest.approx(0.0)
        assert result.y == pytest.approx(0.0)

    def test_round_trip_meters_to_pixels_to_meters(self):
        """Test round trip conversion."""
        converter = ScaleConverter(0.1)
        original = 3.5
        pixels = converter.meters_to_pixels(original)
        back_to_meters = converter.pixels_to_meters(pixels)
        assert back_to_meters == pytest.approx(original, abs=0.1)

    def test_round_trip_point_conversion(self):
        """Test round trip point conversion."""
        converter = ScaleConverter(0.1)
        original = Point2D(1.5, 2.5)
        pixels = converter.point_meters_to_pixels(original)
        back_to_meters = converter.point_pixels_to_meters(pixels)
        assert back_to_meters.x == pytest.approx(original.x, abs=0.1)
        assert back_to_meters.y == pytest.approx(original.y, abs=0.1)

    def test_scale_converter_for_output_scale(self):
        """Test ScaleConverter with typical output scale."""
        output_scale = 0.05  # 5cm per pixel
        converter = ScaleConverter(output_scale)
        assert converter.meters_per_pixel == pytest.approx(0.05)

    def test_scale_converter_different_scales(self):
        """Test ScaleConverter with various scales."""
        for scale in [0.01, 0.05, 0.1, 0.2, 1.0]:
            converter = ScaleConverter(scale)
            assert converter.meters_per_pixel == pytest.approx(scale)

    def test_scale_converter_negative_meters(self):
        """Test converting negative meters."""
        converter = ScaleConverter(0.1)
        pixels = converter.meters_to_pixels(-1.0)
        assert pixels == -10

    def test_scale_converter_negative_pixels(self):
        """Test converting negative pixels."""
        converter = ScaleConverter(0.1)
        meters = converter.pixels_to_meters(-10)
        assert meters == pytest.approx(-1.0)

    def test_scale_converter_fractional_pixels(self):
        """Test rounding behavior with fractional pixels."""
        converter = ScaleConverter(0.1)
        # 1.5 meters / 0.1 = 15 pixels (no rounding needed)
        pixels = converter.meters_to_pixels(1.5)
        assert pixels == 15

    def test_scale_converter_rounding(self):
        """Test rounding behavior."""
        converter = ScaleConverter(0.3)
        # 1.0 / 0.3 = 3.333... should round to 3
        pixels = converter.meters_to_pixels(1.0)
        assert isinstance(pixels, int)
