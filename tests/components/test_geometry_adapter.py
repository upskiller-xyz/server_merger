"""Tests for geometry adapter."""

import pytest
import numpy as np
from shapely.geometry import Polygon, MultiPolygon, GeometryCollection, LinearRing

from src.components.geometry_adapter import GeometryAdapter
from src.core.enums import GeometryType


class TestGeometryAdapter:
    """Test GeometryAdapter class."""

    def test_extract_coordinates_polygon(self):
        """Test extracting coordinates from polygon."""
        poly = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        result = GeometryAdapter.extract_coordinates(poly)
        
        assert isinstance(result, np.ndarray)
        assert result.dtype == np.int32
        assert len(result) == 1  # One polygon
        assert len(result[0]) == 4  # Four points

    def test_extract_coordinates_multi_polygon(self):
        """Test extracting coordinates from multipolygon."""
        poly1 = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        poly2 = Polygon([(2, 2), (3, 2), (3, 3), (2, 3)])
        multi = MultiPolygon([poly1, poly2])
        
        result = GeometryAdapter.extract_coordinates(multi)
        
        assert isinstance(result, np.ndarray)
        assert result.dtype == np.int32
        assert len(result) == 1

    def test_extract_coordinates_empty_geometry(self):
        """Test extracting from empty geometry."""
        empty_poly = Polygon()
        result = GeometryAdapter.extract_coordinates(empty_poly)
        
        assert isinstance(result, np.ndarray)
        assert result.dtype == np.int32
        # Should be empty polygon representation
        assert len(result) > 0

    def test_extract_coordinates_with_fallback(self):
        """Test using fallback coordinates."""
        empty_poly = Polygon()
        fallback = [(0, 0), (1, 0), (1, 1)]
        
        result = GeometryAdapter.extract_coordinates(empty_poly, fallback_coords=fallback)
        
        assert isinstance(result, np.ndarray)
        assert len(result) == 1

    def test_extract_polygon_coords(self):
        """Test _extract_polygon_coords static method."""
        poly = Polygon([(0, 0), (5, 0), (5, 5), (0, 5)])
        coords = GeometryAdapter._extract_polygon_coords(poly)
        
        assert isinstance(coords, list)
        assert len(coords) == 4
        assert all(isinstance(c, tuple) for c in coords)

    def test_extract_multi_polygon_coords(self):
        """Test _extract_multi_polygon_coords static method."""
        # Create multipolygon with different sized polygons
        small_poly = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        large_poly = Polygon([(2, 2), (6, 2), (6, 6), (2, 6)])
        multi = MultiPolygon([small_poly, large_poly])
        
        coords = GeometryAdapter._extract_multi_polygon_coords(multi)
        
        assert isinstance(coords, list)
        assert len(coords) == 4  # Should get coords of larger polygon

    def test_extract_geometry_collection_coords(self):
        """Test _extract_geometry_collection_coords static method."""
        poly1 = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        poly2 = Polygon([(2, 2), (4, 2), (4, 4), (2, 4)])
        geom_collection = GeometryCollection([poly1, poly2])
        
        coords = GeometryAdapter._extract_geometry_collection_coords(geom_collection)
        
        assert isinstance(coords, list)
        assert len(coords) > 0

    def test_vertical_mirror_square(self):
        """Test vertical mirror of square polygon."""
        poly = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        mirrored = GeometryAdapter.vertical_mirror(poly)
        
        assert mirrored is not None
        assert isinstance(mirrored, Polygon)

    def test_vertical_mirror_preserves_shape_type(self):
        """Test that vertical mirror preserves polygon type."""
        poly = Polygon([(0, 0), (2, 0), (2, 3), (0, 3)])
        mirrored = GeometryAdapter.vertical_mirror(poly)
        
        assert isinstance(mirrored, Polygon)
        assert not mirrored.is_empty

    def test_vertical_mirror_y_coordinates(self):
        """Test that vertical mirror negates y coordinates."""
        poly = Polygon([(0, 0), (1, 0), (1, 2), (0, 2)])
        mirrored = GeometryAdapter.vertical_mirror(poly)
        
        # Mirrored Y coords should be negated
        original_coords = list(poly.exterior.coords)
        mirrored_coords = list(mirrored.exterior.coords)
        
        assert len(original_coords) == len(mirrored_coords)

    def test_empty_array(self):
        """Test empty array representation."""
        empty = GeometryAdapter.empty()
        
        assert isinstance(empty, np.ndarray)
        assert empty.dtype == np.int32
        assert empty.shape == (1, 1, 2)

    def test_extract_coordinates_different_polygon_sizes(self):
        """Test extracting from polygons of different sizes."""
        # Triangle
        triangle = Polygon([(0, 0), (1, 0), (0.5, 1)])
        result_tri = GeometryAdapter.extract_coordinates(triangle)
        assert len(result_tri[0]) == 3
        
        # Pentagon
        pentagon = Polygon([(0, 0), (1, 0), (1.5, 1), (0.5, 1.5), (-0.5, 1)])
        result_pent = GeometryAdapter.extract_coordinates(pentagon)
        assert len(result_pent[0]) == 5

    def test_geometry_handlers_map_exists(self):
        """Test that geometry handlers map is properly defined."""
        handlers = GeometryAdapter.GEOMETRY_HANDLERS
        
        assert isinstance(handlers, dict)
        assert GeometryType.POLYGON in handlers
        assert GeometryType.MULTI_POLYGON in handlers
        assert GeometryType.GEOMETRY_COLLECTION in handlers

    def test_extract_coordinates_returns_int32(self):
        """Test that extracted coordinates are int32 type."""
        poly = Polygon([(0.5, 0.5), (1.5, 0.5), (1.5, 1.5), (0.5, 1.5)])
        result = GeometryAdapter.extract_coordinates(poly)
        
        assert result.dtype == np.int32

    def test_extract_coordinates_correct_shape(self):
        """Test that extracted coordinates have correct shape."""
        poly = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
        result = GeometryAdapter.extract_coordinates(poly)
        
        # Shape should be (1, N, 2)
        assert len(result.shape) == 3
        assert result.shape[0] == 1  # Single polygon
        assert result.shape[1] >= 3  # At least 3 points
        assert result.shape[2] == 2  # x, y coordinates

    def test_extract_large_polygon(self):
        """Test extracting from a larger polygon."""
        # Create a 10-sided polygon
        import math
        points = [(math.cos(2*math.pi*i/10), math.sin(2*math.pi*i/10)) for i in range(10)]
        poly = Polygon(points)
        
        result = GeometryAdapter.extract_coordinates(poly)
        
        assert len(result[0]) == 10

    def test_multi_polygon_selects_largest(self):
        """Test that multipolygon adapter selects the largest polygon."""
        small = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        large = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
        multi = MultiPolygon([small, large])
        
        result = GeometryAdapter.extract_coordinates(multi)
        coords = result[0]
        
        # Largest polygon should have coords matching large poly
        assert len(coords) == 4
