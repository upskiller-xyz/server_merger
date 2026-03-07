"""Tests for overlap region model."""

import pytest
from src.models.overlap_region import OverlapRegion, Region


class TestOverlapRegion:
    """Test OverlapRegion model."""

    def test_overlap_region_creation(self):
        """Test creating an OverlapRegion."""
        region = OverlapRegion(
            src=Region(y_start=10, y_end=100, x_start=10, x_end=100),
            dest=Region(y_start=0, y_end=90, x_start=0, x_end=90)
        )
        assert region.src_y_start == 10
        assert region.src_y_end == 100
        assert region.src_x_start == 10
        assert region.src_x_end == 100

    def test_overlap_region_dimensions(self):
        """Test that OverlapRegion calculates dimensions correctly."""
        region = OverlapRegion(
            src=Region(y_start=0, y_end=128, x_start=0, x_end=64),
            dest=Region(y_start=0, y_end=128, x_start=0, x_end=64)
        )
        # src_width should be 64 (64 - 0)
        # src_height should be 128 (128 - 0)
        assert region.src_width == 64
        assert region.src_height == 128
        assert region.dst_width == 64
        assert region.dst_height == 128

    def test_overlap_region_no_overlap(self):
        """Test OverlapRegion with zero dimensions."""
        region = OverlapRegion(
            src=Region(y_start=0, y_end=0, x_start=0, x_end=0),
            dest=Region(y_start=0, y_end=0, x_start=0, x_end=0)
        )
        # Region with zero size should be valid
        assert region.src_y_start == 0
        assert region.src_y_end == 0
        assert region.src_width == 0
        assert region.src_height == 0

    def test_overlap_region_with_offset(self):
        """Test OverlapRegion with various offsets."""
        region = OverlapRegion(
            src=Region(y_start=5, y_end=120, x_start=10, x_end=110),
            dest=Region(y_start=0, y_end=115, x_start=5, x_end=105)
        )
        assert region.src_y_start == 5
        assert region.dst_x_start == 5
        assert region.src_width == 100  # 110 - 10
        assert region.src_height == 115  # 120 - 5

    def test_overlap_region_src_dimensions(self):
        """Test source region dimension properties."""
        region = OverlapRegion(
            src=Region(y_start=10, y_end=50, x_start=20, x_end=80),
            dest=Region(y_start=0, y_end=40, x_start=0, x_end=60)
        )
        assert region.src_height == 40  # 50 - 10
        assert region.src_width == 60   # 80 - 20

    def test_overlap_region_dst_dimensions(self):
        """Test destination region dimension properties."""
        region = OverlapRegion(
            src=Region(y_start=0, y_end=100, x_start=0, x_end=100),
            dest=Region(y_start=5, y_end=95, x_start=10, x_end=90)
        )
        assert region.dst_height == 90  # 95 - 5
        assert region.dst_width == 80   # 90 - 10

    def test_overlap_region_negative_offsets(self):
        """Test OverlapRegion with all coordinate combinations."""
        region = OverlapRegion(
            src=Region(y_start=25, y_end=75, x_start=30, x_end=70),
            dest=Region(y_start=10, y_end=60, x_start=15, x_end=55)
        )
        assert region.src_height == 50  # 75 - 25
        assert region.src_width == 40   # 70 - 30
        assert region.dst_height == 50  # 60 - 10
        assert region.dst_width == 40   # 55 - 15

    def test_overlap_region_equal_dimensions(self):
        """Test region where src and dst have equal dimensions."""
        region = OverlapRegion(
            src=Region(y_start=0, y_end=100, x_start=0, x_end=100),
            dest=Region(y_start=0, y_end=100, x_start=0, x_end=100)
        )
        assert region.src_height == region.dst_height
        assert region.src_width == region.dst_width

    def test_overlap_region_mismatched_dimensions(self):
        """Test region where src and dst have different dimensions."""
        region = OverlapRegion(
            src=Region(y_start=0, y_end=200, x_start=0, x_end=200),
            dest=Region(y_start=0, y_end=100, x_start=0, x_end=100)
        )
        assert region.src_height == 200
        assert region.dst_height == 100
        assert region.src_width == 200
        assert region.dst_width == 100

    def test_overlap_region_large_values(self):
        """Test OverlapRegion with large coordinate values."""
        region = OverlapRegion(
            src=Region(y_start=1000, y_end=5000, x_start=2000, x_end=6000),
            dest=Region(y_start=500, y_end=4500, x_start=1000, x_end=5000)
        )
        assert region.src_height == 4000  # 5000 - 1000
        assert region.src_width == 4000   # 6000 - 2000
        assert region.dst_height == 4000  # 4500 - 500
        assert region.dst_width == 4000   # 5000 - 1000
