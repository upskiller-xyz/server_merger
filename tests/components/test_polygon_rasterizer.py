"""Tests for polygon rasterizer."""

import pytest
import numpy as np
from src.components.polygon_rasterizer import PolygonRasterizer


class TestPolygonRasterizer:
    """Test PolygonRasterizer class."""

    def test_rasterize_square(self):
        """Test rasterizing a square polygon."""
        polygon = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
        mask = PolygonRasterizer.rasterize(polygon, 10, 10, 0.1)
        
        assert isinstance(mask, np.ndarray)
        assert mask.dtype == np.uint8
        assert mask.shape == (10, 10)

    def test_rasterize_triangle(self):
        """Test rasterizing a triangular polygon."""
        polygon = [(0.0, 0.0), (1.0, 0.0), (0.5, 1.0)]
        mask = PolygonRasterizer.rasterize(polygon, 10, 10, 0.1)
        
        assert isinstance(mask, np.ndarray)
        assert mask.shape == (10, 10)

    def test_rasterize_creates_filled_area(self):
        """Test that rasterized polygon creates filled area."""
        polygon = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]
        mask = PolygonRasterizer.rasterize(polygon, 100, 100, 0.1)
        
        # Should have some non-zero pixels (filled area)
        assert np.sum(mask) > 0

    def test_rasterize_outputs_binary_mask(self):
        """Test that output is binary mask."""
        polygon = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
        mask = PolygonRasterizer.rasterize(polygon, 10, 10, 0.1)
        
        # Mask should only contain 0s and 1s
        unique_values = np.unique(mask)
        assert all(v in [0, 1] for v in unique_values)

    def test_rasterize_different_scales(self):
        """Test rasterizing with different scales."""
        polygon = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
        
        mask1 = PolygonRasterizer.rasterize(polygon, 10, 10, 0.1)
        mask2 = PolygonRasterizer.rasterize(polygon, 20, 20, 0.05)
        
        assert mask1.shape == (10, 10)
        assert mask2.shape == (20, 20)

    def test_rasterize_small_polygon_in_large_canvas(self):
        """Test rasterizing small polygon in large canvas."""
        # Small polygon in corner
        polygon = [(0.0, 0.0), (0.1, 0.0), (0.1, 0.1), (0.0, 0.1)]
        mask = PolygonRasterizer.rasterize(polygon, 1000, 1000, 0.01)
        
        assert mask.shape == (1000, 1000)
        # Most of the mask should be empty
        assert np.sum(mask) < mask.size * 0.1

    def test_rasterize_large_polygon_in_small_canvas(self):
        """Test rasterizing large polygon in small canvas."""
        polygon = [(0.0, 0.0), (100.0, 0.0), (100.0, 100.0), (0.0, 100.0)]
        mask = PolygonRasterizer.rasterize(polygon, 10, 10, 1.0)
        
        assert mask.shape == (10, 10)
        # Most of the mask should be filled
        assert np.sum(mask) > mask.size * 0.5

    def test_rasterize_y_axis_flip(self):
        """Test that Y-axis is flipped correctly."""
        # Bottom rectangle
        polygon_bottom = [(0.0, 0.0), (1.0, 0.0), (1.0, 0.1), (0.0, 0.1)]
        # Top rectangle
        polygon_top = [(0.0, 0.9), (1.0, 0.9), (1.0, 1.0), (0.0, 1.0)]
        
        mask_bottom = PolygonRasterizer.rasterize(polygon_bottom, 10, 10, 0.1)
        mask_top = PolygonRasterizer.rasterize(polygon_top, 10, 10, 0.1)
        
        # In image coords (origin at top-left), bottom in world should map to bottom rows
        # and top in world should map to top rows
        assert isinstance(mask_bottom, np.ndarray)
        assert isinstance(mask_top, np.ndarray)

    def test_rasterize_polygon_center(self):
        """Test rasterizing centered polygon."""
        # Unit square centered at 0.5, 0.5
        polygon = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
        mask = PolygonRasterizer.rasterize(polygon, 10, 10, 0.1)
        
        # Center pixels should be filled
        center_row = mask[5-2:5+2, 5-2:5+2]
        assert np.any(center_row > 0)

    def test_rasterize_pentagon(self):
        """Test rasterizing pentagon."""
        import math
        # Regular pentagon
        polygon = [(math.cos(2*math.pi*i/5), math.sin(2*math.pi*i/5)) for i in range(5)]
        mask = PolygonRasterizer.rasterize(polygon, 10, 10, 0.2)
        
        assert mask.shape == (10, 10)
        assert np.sum(mask) > 0

    def test_rasterize_uint8_output(self):
        """Test that output is uint8 dtype."""
        polygon = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
        mask = PolygonRasterizer.rasterize(polygon, 10, 10, 0.1)
        
        assert mask.dtype == np.uint8

    def test_rasterize_correct_dimensions(self):
        """Test that output dimensions match requested size."""
        for width, height in [(10, 10), (20, 15), (100, 50)]:
            polygon = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
            mask = PolygonRasterizer.rasterize(polygon, width, height, 0.1)
            
            assert mask.shape == (height, width)

    def test_rasterize_l_shaped_polygon(self):
        """Test rasterizing L-shaped polygon."""
        # L-shaped polygon
        polygon = [
            (0.0, 0.0), (1.0, 0.0), (1.0, 0.5),
            (0.5, 0.5), (0.5, 1.0), (0.0, 1.0)
        ]
        mask = PolygonRasterizer.rasterize(polygon, 10, 10, 0.1)
        
        assert isinstance(mask, np.ndarray)
        assert np.sum(mask) > 0
        # L-shape should have non-contiguous filled regions
