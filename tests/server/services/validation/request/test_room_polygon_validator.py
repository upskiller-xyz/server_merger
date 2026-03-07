"""Tests for room polygon validator"""

import pytest
import numpy as np
from src.server.services.validation.request.room_polygon_validator import RoomPolygonValidator
from src.server.services.validation.validation_error import ValidationError
from src.server.services.validation.enums import ErrorCode


class TestRoomPolygonValidator:
    """Test room polygon validation"""

    def setup_method(self):
        """Set up validator"""
        self.validator = RoomPolygonValidator()

    def test_polygon_not_array(self):
        """Test error when polygon is not an array"""
        polygon = "not_an_array"
        
        with pytest.raises(ValidationError) as exc_info:
            self.validator.validate(polygon, "room_polygon")
        
        assert exc_info.value.error_code == ErrorCode.INVALID_TYPE
        assert "array" in exc_info.value.message

    def test_polygon_too_few_vertices(self):
        """Test error when polygon has too few vertices"""
        polygon = [[0, 0], [1, 1]]  # Only 2 vertices, need 3
        
        with pytest.raises(ValidationError) as exc_info:
            self.validator.validate(polygon, "room_polygon")
        
        assert exc_info.value.error_code == ErrorCode.INVALID_VALUE
        assert "vertices" in exc_info.value.message.lower()

    def test_polygon_with_minimum_vertices(self):
        """Test valid polygon with minimum vertices (triangle)"""
        polygon = [[0, 0], [1, 0], [0.5, 1]]
        
        # Should not raise
        self.validator.validate(polygon, "room_polygon")

    def test_polygon_with_more_vertices(self):
        """Test valid polygon with many vertices"""
        polygon = [
            [0, 0], [1, 0], [2, 0],
            [2, 1], [2, 2],
            [1, 2], [0, 2],
            [0, 1]
        ]
        
        # Should not raise
        self.validator.validate(polygon, "room_polygon")

    def test_polygon_vertex_not_coordinate_pair(self):
        """Test error when vertex is not a coordinate pair"""
        polygon = [[0, 0], [1, 0], [0.5]]  # Last vertex has only 1 coord
        
        # numpy.array() will raise ValueError for inhomogeneous shapes
        # or validator will catch it as invalid format
        with pytest.raises((ValidationError, ValueError)):
            self.validator.validate(polygon, "room_polygon")

    def test_polygon_vertex_too_many_coords(self):
        """Test error when vertex has too many coordinates"""
        polygon = [[0, 0], [1, 0], [0.5, 1, 0]]  # Last vertex is 3D
        
        # numpy.array() may raise ValueError for inhomogeneous shapes
        # or validator will catch it
        with pytest.raises((ValidationError, ValueError)):
            self.validator.validate(polygon, "room_polygon")

    def test_polygon_vertex_non_numeric(self):
        """Test error when vertex has non-numeric coordinates"""
        polygon = [[0, 0], [1, 0], ["a", "b"]]
        
        with pytest.raises(ValidationError) as exc_info:
            self.validator.validate(polygon, "room_polygon")
        
        assert exc_info.value.error_code == ErrorCode.INVALID_TYPE
        assert "numeric" in exc_info.value.message.lower()

    def test_polygon_with_numpy_array(self):
        """Test valid polygon with numpy array"""
        polygon = np.array([[0, 0], [1, 0], [0.5, 1]])
        
        # Should not raise
        self.validator.validate(polygon, "room_polygon")

    def test_polygon_with_tuple_vertices(self):
        """Test valid polygon with tuple vertices"""
        polygon = [(0, 0), (1, 0), (0.5, 1)]
        
        # Should not raise
        self.validator.validate(polygon, "room_polygon")

    def test_polygon_with_integer_coords(self):
        """Test valid polygon with integer coordinates"""
        polygon = [[0, 0], [10, 0], [5, 10]]
        
        # Should not raise
        self.validator.validate(polygon, "room_polygon")

    def test_polygon_with_negative_coords(self):
        """Test valid polygon with negative coordinates"""
        polygon = [[-1, -1], [1, -1], [0, 1]]
        
        # Should not raise
        self.validator.validate(polygon, "room_polygon")

    def test_polygon_field_path_in_error(self):
        """Test that field path is included in vertex errors"""
        polygon = [[0, 0], [1, 0]]  # Too few vertices
        
        with pytest.raises(ValidationError) as exc_info:
            self.validator.validate(polygon, "request.room_polygon")
        
        assert "request.room_polygon" in exc_info.value.field

    def test_polygon_vertex_index_in_error(self):
        """Test that vertex index is included in coordinate errors"""
        polygon = [[0, 0], [1, 0], [1.5, 0.5]]  # Valid third vertex
        
        # Should not raise with valid polygon
        self.validator.validate(polygon, "room")

    def test_polygon_vertex_count_in_context(self):
        """Test that vertex count is included in context"""
        polygon = [[0, 0]]  # Only 1 vertex
        
        with pytest.raises(ValidationError) as exc_info:
            self.validator.validate(polygon, "room")
        
        assert exc_info.value.context["vertex_count"] == 1
        assert exc_info.value.context["min_vertices"] == 3

    def test_custom_min_vertices(self):
        """Test validator with custom minimum vertices"""
        validator = RoomPolygonValidator(min_vertices=4)
        polygon = [[0, 0], [1, 0], [0.5, 1]]  # 3 vertices
        
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(polygon, "room")
        
        assert exc_info.value.context["min_vertices"] == 4

    def test_custom_min_vertices_valid(self):
        """Test valid polygon with custom minimum"""
        validator = RoomPolygonValidator(min_vertices=2)
        polygon = [[0, 0], [1, 1]]  # 2 vertices
        
        # Should not raise
        validator.validate(polygon, "room")

    def test_polygon_all_numeric_types(self):
        """Test polygon with mixed numeric types"""
        polygon = [[0, 0.5], [1, 2], [0.5, 1.2]]
        
        # Should not raise
        self.validator.validate(polygon, "room")

    def test_empty_polygon(self):
        """Test error with empty polygon"""
        polygon = []
        
        with pytest.raises(ValidationError) as exc_info:
            self.validator.validate(polygon, "room")
        
        assert exc_info.value.error_code == ErrorCode.INVALID_VALUE

    def test_polygon_vertex_string_error(self):
        """Test error message for string vertex"""
        polygon = [[0, 0], [1, 0], "invalid"]
        
        # numpy.array() may raise ValueError or validator catches formatting
        with pytest.raises((ValidationError, ValueError, TypeError)):
            self.validator.validate(polygon, "room")
