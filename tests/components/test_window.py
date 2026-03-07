"""Tests for window geometry."""

import pytest
import math
from src.components.window import WindowGeometry, RoomPolygon
from src.components.geometry_ops import Point2D
from src.core.enums import ParameterName


class TestWindowGeometry:
    """Test WindowGeometry class."""

    def test_window_geometry_creation(self):
        """Test creating a WindowGeometry."""
        window = WindowGeometry(
            x1=0.0,
            y1=1.0,
            z1=0.0,
            x2=0.4,
            y2=3.8,
            z2=2.0,
            direction_angle=0.0
        )
        
        assert window is not None

    def test_window_geometry_with_direction(self):
        """Test window with direction angle."""
        window = WindowGeometry(
            x1=0.0,
            y1=7.0,
            z1=0.0,
            x2=-0.7,
            y2=7.3,
            z2=2.0,
            direction_angle=math.pi / 2  # 90 degrees
        )
        
        assert window.direction_angle == pytest.approx(math.pi / 2)

    def test_window_geometry_properties(self):
        """Test WindowGeometry properties."""
        window = WindowGeometry(
            x1=0.0,
            y1=1.0,
            z1=0.0,
            x2=2.0,
            y2=5.0,
            z2=2.0,
            direction_angle=0.0
        )
        
        # Check niche_center property
        center = window.niche_center
        assert center.x == pytest.approx(1.0)  # (0.0 + 2.0) / 2
        assert center.y == pytest.approx(3.0)  # (1.0 + 5.0) / 2

    def test_window_geometry_negative_coordinates(self):
        """Test window with negative coordinates."""
        window = WindowGeometry(
            x1=-1.0,
            y1=0.0,
            z1=0.0,
            x2=0.0,
            y2=1.0,
            z2=2.0,
            direction_angle=0.0
        )
        
        assert window is not None

    # Additional tests for properties
    def test_window_width_3d_no_direction(self):
        """Test window_width_3d without direction angle."""
        window = WindowGeometry(
            x1=0.0, y1=0.0, z1=0.0,
            x2=4.0, y2=6.0, z2=2.0
        )
        # max(4-0, 6-0) = 6
        assert window.window_width_3d == pytest.approx(6.0)

    def test_window_width_3d_with_direction(self):
        """Test window_width_3d with direction angle."""
        window = WindowGeometry(
            x1=0.0, y1=0.0, z1=0.0,
            x2=2.0, y2=3.0, z2=2.0,
            direction_angle=0.0
        )
        assert window.window_width_3d > 0

    def test_wall_thickness_no_direction(self):
        """Test wall_thickness without direction angle."""
        window = WindowGeometry(
            x1=0.0, y1=0.0, z1=0.0,
            x2=4.0, y2=6.0, z2=2.0
        )
        # min(4-0, 6-0) = 4
        assert window.wall_thickness == pytest.approx(4.0)

    def test_wall_thickness_with_direction(self):
        """Test wall_thickness with direction angle."""
        window = WindowGeometry(
            x1=0.0, y1=0.0, z1=0.0,
            x2=2.0, y2=3.0, z2=2.0,
            direction_angle=math.pi / 4
        )
        assert window.wall_thickness > 0

    def test_window_height_3d(self):
        """Test window height in 3D."""
        window = WindowGeometry(
            x1=0.0, y1=0.0, z1=1.0,
            x2=2.0, y2=3.0, z2=3.5
        )
        assert window.window_height_3d == pytest.approx(2.5)

    def test_sill_height(self):
        """Test sill height."""
        window = WindowGeometry(
            x1=0.0, y1=0.0, z1=1.2,
            x2=2.0, y2=3.0, z2=3.2
        )
        assert window.sill_height == pytest.approx(1.2)

    def test_top_height(self):
        """Test top height."""
        window = WindowGeometry(
            x1=0.0, y1=0.0, z1=1.0,
            x2=2.0, y2=3.0, z2=3.0
        )
        assert window.top_height == pytest.approx(3.0)

    def test_corner_properties(self):
        """Test individual corner coordinate properties."""
        window = WindowGeometry(
            x1=1.0, y1=2.0, z1=0.5,
            x2=3.0, y2=4.0, z2=2.5
        )
        assert window.x1 == pytest.approx(1.0)
        assert window.y1 == pytest.approx(2.0)
        assert window.z1 == pytest.approx(0.5)
        assert window.x2 == pytest.approx(3.0)
        assert window.y2 == pytest.approx(4.0)
        assert window.z2 == pytest.approx(2.5)

    def test_rotate_window(self):
        """Test rotating a window."""
        window = WindowGeometry(
            x1=0.0, y1=0.0, z1=0.0,
            x2=2.0, y2=0.0, z2=2.0,
            direction_angle=0.0
        )
        rotated = window.rotate(90.0, center=Point2D(0, 0))
        assert rotated is not None
        assert rotated.z1 == pytest.approx(0.0)
        assert rotated.z2 == pytest.approx(2.0)

    def test_get_pixel_bounds(self):
        """Test getting pixel bounds."""
        window = WindowGeometry(
            x1=0.0, y1=0.0, z1=0.0,
            x2=0.3, y2=0.3, z2=2.0,
            direction_angle=0.0
        )
        bounds = window.get_pixel_bounds(image_size=128)
        assert len(bounds) == 4
        x_start, y_start, x_end, y_end = bounds
        assert x_start < x_end
        assert y_start < y_end
        assert 0 <= x_start <= 128
        assert 0 <= x_end <= 128

    def test_wall_thickness_px(self):
        """Test wall thickness in pixels."""
        window = WindowGeometry(
            x1=0.0, y1=0.0, z1=0.0,
            x2=0.5, y2=0.5, z2=2.0
        )
        thickness_px = window.wall_thickness_px
        assert thickness_px > 0

    def test_from_corners_classmethod(self):
        """Test creating window from corners classmethod."""
        window = WindowGeometry.from_corners(
            1.0, 2.0, 0.5,
            3.0, 4.0, 2.5
        )
        assert window.x1 == pytest.approx(1.0)
        assert window.y2 == pytest.approx(4.0)
        assert window.z2 == pytest.approx(2.5)

    def test_from_dict_classmethod(self):
        """Test creating window from dictionary."""
        data = {
            ParameterName.X1.value: 0.0,
            ParameterName.Y1.value: 0.0,
            ParameterName.Z1.value: 1.0,
            ParameterName.X2.value: 2.0,
            ParameterName.Y2.value: 3.0,
            ParameterName.Z2.value: 3.0,
            ParameterName.DIRECTION_ANGLE.value: 0.0
        }
        window = WindowGeometry.from_dict(data)
        assert window.x1 == pytest.approx(0.0)
        assert window.z1 == pytest.approx(1.0)
        assert window.direction_angle == pytest.approx(0.0)

    def test_rotated_corner(self):
        """Test _rotated_corner internal method."""
        window = WindowGeometry(
            x1=0.0, y1=0.0, z1=0.0,
            x2=2.0, y2=3.0, z2=2.0,
            direction_angle=0.0
        )
        # Test all four corner combinations
        c1 = window._rotated_corner(up=True, right=True)
        c2 = window._rotated_corner(up=True, right=False)
        c3 = window._rotated_corner(up=False, right=True)
        c4 = window._rotated_corner(up=False, right=False)
        
        assert len(c1) == 2
        assert isinstance(c1[0], float)
        assert isinstance(c1[1], float)

    def test_get_candidate_edges(self):
        """Test getting candidate edges."""
        window = WindowGeometry(
            x1=0.0, y1=0.0, z1=0.0,
            x2=2.0, y2=3.0, z2=2.0,
            direction_angle=0.0
        )
        edges = window.get_candidate_edges()
        assert len(edges) == 4


class TestRoomPolygon:
    """Test RoomPolygon class."""

    def test_room_polygon_creation(self):
        """Test creating a RoomPolygon."""
        coords = [
            (0.0, 0.0),
            (10.0, 0.0),
            (10.0, 10.0),
            (0.0, 10.0)
        ]
        polygon = RoomPolygon(coords)
        
        assert polygon is not None

    def test_room_polygon_square(self):
        """Test square room polygon."""
        coords = [
            (0.0, 0.0),
            (100.0, 0.0),
            (100.0, 100.0),
            (0.0, 100.0)
        ]
        polygon = RoomPolygon(coords)
        
        # Get coordinates back
        retrieved_coords = polygon.get_coords()
        assert len(retrieved_coords) == 4

    def test_room_polygon_triangle(self):
        """Test triangular room polygon."""
        coords = [
            (0.0, 0.0),
            (10.0, 0.0),
            (5.0, 10.0)
        ]
        polygon = RoomPolygon(coords)
        
        retrieved_coords = polygon.get_coords()
        assert len(retrieved_coords) == 3

    def test_room_polygon_complex_shape(self):
        """Test L-shaped room polygon."""
        coords = [
            (0.0, 0.0),
            (10.0, 0.0),
            (10.0, 5.0),
            (5.0, 5.0),
            (5.0, 10.0),
            (0.0, 10.0)
        ]
        polygon = RoomPolygon(coords)
        
        retrieved_coords = polygon.get_coords()
        assert len(retrieved_coords) == 6

    def test_room_polygon_with_negative_coords(self):
        """Test polygon with negative coordinates."""
        coords = [
            (-5.0, -5.0),
            (5.0, -5.0),
            (5.0, 5.0),
            (-5.0, 5.0)
        ]
        polygon = RoomPolygon(coords)
        
        retrieved_coords = polygon.get_coords()
        assert len(retrieved_coords) == 4

    def test_room_polygon_bounds(self):
        """Test getting bounds from polygon."""
        coords = [
            (0.0, 0.0),
            (20.0, 0.0),
            (20.0, 15.0),
            (0.0, 15.0)
        ]
        polygon = RoomPolygon(coords)
        
        # Polygon should contain its coordinates
        retrieved_coords = polygon.get_coords()
        assert len(retrieved_coords) > 0

    def test_room_polygon_width(self):
        """Test room width calculation."""
        coords = [
            (0.0, 0.0),
            (20.0, 0.0),
            (20.0, 10.0),
            (0.0, 10.0)
        ]
        polygon = RoomPolygon(coords)
        assert polygon.width == pytest.approx(20.0)

    def test_room_polygon_height(self):
        """Test room height calculation."""
        coords = [
            (0.0, 0.0),
            (20.0, 0.0),
            (20.0, 15.0),
            (0.0, 15.0)
        ]
        polygon = RoomPolygon(coords)
        assert polygon.height == pytest.approx(15.0)

    def test_room_polygon_vertices(self):
        """Test vertices property."""
        coords = [
            (1.0, 2.0),
            (3.0, 2.0),
            (3.0, 5.0),
            (1.0, 5.0)
        ]
        polygon = RoomPolygon(coords)
        vertices = polygon.vertices
        assert len(vertices) == 4
        assert vertices[0].x == pytest.approx(1.0)
        assert vertices[0].y == pytest.approx(2.0)

    def test_room_polygon_get_bounds(self):
        """Test get_bounds method."""
        coords = [
            (5.0, 10.0),
            (15.0, 10.0),
            (15.0, 20.0),
            (5.0, 20.0)
        ]
        polygon = RoomPolygon(coords)
        min_x, min_y, max_x, max_y = polygon.get_bounds()
        assert min_x == pytest.approx(5.0)
        assert min_y == pytest.approx(10.0)
        assert max_x == pytest.approx(15.0)
        assert max_y == pytest.approx(20.0)

    def test_room_polygon_rotate(self):
        """Test rotating a room polygon."""
        coords = [
            (0.0, 0.0),
            (10.0, 0.0),
            (10.0, 10.0),
            (0.0, 10.0)
        ]
        polygon = RoomPolygon(coords)
        rotated = polygon.rotate(90.0, center=Point2D(0, 0))
        assert rotated is not None
        assert len(rotated.vertices) == 4

    def test_room_polygon_translate(self):
        """Test translating a room polygon."""
        coords = [
            (0.0, 0.0),
            (10.0, 0.0),
            (10.0, 10.0),
            (0.0, 10.0)
        ]
        polygon = RoomPolygon(coords)
        translated = polygon.translate(Point2D(5.0, 3.0))
        assert translated is not None
        coords_after = translated.get_coords()
        # Points should be shifted by (-5, -3)
        assert coords_after[0][0] == pytest.approx(-5.0)
        assert coords_after[0][1] == pytest.approx(-3.0)

    def test_room_polygon_shift_to_zero(self):
        """Test shifting polygon to zero."""
        coords = [
            (5.0, 3.0),
            (15.0, 3.0),
            (15.0, 13.0),
            (5.0, 13.0)
        ]
        polygon = RoomPolygon(coords)
        shifted = polygon.shift_to_zero()
        assert shifted is not None
        shifted_coords = shifted.get_coords()
        # Should be shifted so min_x=0, min_y=0
        min_x, min_y, _, _ = shifted.get_bounds()
        assert min_x == pytest.approx(0.0)
        assert min_y == pytest.approx(0.0)

    def test_room_polygon_point_to_zero(self):
        """Test point_to_zero transformation."""
        coords = [
            (0.0, 0.0),
            (10.0, 0.0),
            (10.0, 10.0),
            (0.0, 10.0)
        ]
        polygon = RoomPolygon(coords)
        point = Point2D(5.0, 3.0)
        transformed = polygon.point_to_zero(point)
        assert transformed is not None
        assert isinstance(transformed, Point2D)

    def test_room_polygon_get_edges(self):
        """Test getting edges from polygon."""
        coords = [
            (0.0, 0.0),
            (10.0, 0.0),
            (10.0, 10.0),
            (0.0, 10.0)
        ]
        polygon = RoomPolygon(coords)
        edges = polygon.get_edges()
        assert len(edges) == 4

    def test_room_polygon_from_dict_list_of_lists(self):
        """Test creating polygon from list of lists."""
        data = [[0, 0], [10, 0], [10, 10], [0, 10]]
        polygon = RoomPolygon.from_dict(data)
        assert len(polygon.vertices) == 4

    def test_room_polygon_from_dict_list_of_dicts(self):
        """Test creating polygon from list of dicts."""
        data = [
            {"x": 0, "y": 0},
            {"x": 10, "y": 0},
            {"x": 10, "y": 10},
            {"x": 0, "y": 10}
        ]
        polygon = RoomPolygon.from_dict(data)
        assert len(polygon.vertices) == 4

    def test_room_polygon_from_dict_list_of_tuples(self):
        """Test creating polygon from list of tuples."""
        data = [(0, 0), (10, 0), (10, 10), (0, 10)]
        polygon = RoomPolygon.from_dict(data)
        assert len(polygon.vertices) == 4

    def test_room_polygon_invalid_vertices_count(self):
        """Test that polygon requires at least 3 vertices."""
        with pytest.raises(ValueError):
            RoomPolygon([(0, 0), (1, 1)])

    def test_room_polygon_window_edge_and_rotation(self):
        """Test _window_edge_and_rotation method."""
        from shapely.geometry import LineString
        coords = [
            (0.0, 0.0),
            (10.0, 0.0),
            (10.0, 10.0),
            (0.0, 10.0)
        ]
        polygon = RoomPolygon(coords)
        # Create a window line on one of the polygon edges
        window_line = LineString([(0.0, 0.0), (10.0, 0.0)])
        edge, edge_ind, edge_angle = polygon._window_edge_and_rotation(window_line)
        assert edge is not None
        assert isinstance(edge_ind, int)
        assert isinstance(edge_angle, float)
