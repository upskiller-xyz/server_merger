"""Tests for geometry operations."""

import pytest
import math
from src.components.geometry_ops import Point2D, Point3D, GeometryOps
from src.components.room_polygon import RoomPolygon


class TestPoint2D:
    """Test Point2D class."""

    def test_point2d_creation(self):
        """Test creating a 2D point."""
        point = Point2D(1.0, 2.0)
        assert point.x == pytest.approx(1.0)
        assert point.y == pytest.approx(2.0)

    def test_point2d_to_pixel(self):
        """Test converting 2D point to pixels."""
        point = Point2D(1.0, 2.0)
        pixel = point.to_pixel(resolution=0.1)
        assert isinstance(pixel, tuple)
        assert len(pixel) == 2

    def test_point2d_zero(self):
        """Test zero point."""
        point = Point2D(0.0, 0.0)
        assert point.x == pytest.approx(0.0)
        assert point.y == pytest.approx(0.0)

    def test_point2d_negative(self):
        """Test negative coordinates."""
        point = Point2D(-1.5, -3.0)
        assert point.x == pytest.approx(-1.5)
        assert point.y == pytest.approx(-3.0)


class TestPoint3D:
    """Test Point3D class."""

    def test_point3d_creation(self):
        """Test creating a 3D point."""
        point = Point3D(1.0, 2.0, 3.0)
        assert point.x == pytest.approx(1.0)
        assert point.y == pytest.approx(2.0)
        assert point.z == pytest.approx(3.0)

    def test_point3d_to_point2d(self):
        """Test converting 3D point to 2D."""
        point = Point3D(1.0, 2.0, 3.0)
        point2d = point.to_point2d()
        assert isinstance(point2d, Point2D)
        assert point2d.x == pytest.approx(1.0)
        assert point2d.y == pytest.approx(2.0)

    def test_point3d_to_pixel(self):
        """Test converting 3D point to pixels."""
        point = Point3D(1.0, 2.0, 3.0)
        pixel = point.to_pixel(resolution=0.1)
        assert isinstance(pixel, tuple)
        assert len(pixel) == 2

    def test_point3d_zero(self):
        """Test zero 3D point."""
        point = Point3D(0.0, 0.0, 0.0)
        assert point.x == pytest.approx(0.0)
        assert point.y == pytest.approx(0.0)
        assert point.z == pytest.approx(0.0)


class TestGeometryOps:
    """Test GeometryOps class."""

    def test_project_point2d(self):
        """Test projecting a 2D point."""
        point = Point2D(3.0, 4.0)
        sin_a = math.sin(0)
        cos_a = math.cos(0)
        result = GeometryOps.project(point, sin_a, cos_a)
        assert isinstance(result, float)

    def test_project_point3d(self):
        """Test projecting a 3D point."""
        point = Point3D(3.0, 4.0, 5.0)
        sin_a = math.sin(math.pi / 4)
        cos_a = math.cos(math.pi / 4)
        result = GeometryOps.project(point, sin_a, cos_a)
        assert isinstance(result, float)

    def test_project_with_0_degrees(self):
        """Test projection at 0 degrees."""
        point = Point2D(3.0, 4.0)
        sin_a = math.sin(0)
        cos_a = math.cos(0)
        result = GeometryOps.project(point, sin_a, cos_a)
        assert result == pytest.approx(3.0)

    def test_project_with_90_degrees(self):
        """Test projection at 90 degrees."""
        point = Point2D(3.0, 4.0)
        sin_a = math.sin(math.pi / 2)
        cos_a = math.cos(math.pi / 2)
        result = GeometryOps.project(point, sin_a, cos_a)
        assert result == pytest.approx(4.0, abs=0.01)

    def test_offset_coords_point2d(self):
        """Test offset coordinates with 2D points."""
        p1 = Point2D(0.0, 0.0)
        p2 = Point2D(3.0, 4.0)
        offset = GeometryOps.offset_coords(p2, p1)
        assert offset == [3.0, 4.0]

    def test_offset_coords_point3d(self):
        """Test offset coordinates with 3D points."""
        p1 = Point3D(1.0, 1.0, 0.0)
        p2 = Point3D(4.0, 5.0, 3.0)
        offset = GeometryOps.offset_coords(p2, p1)
        assert offset == [3.0, 4.0]

    def test_offset_coords_negative(self):
        """Test offset with negative coordinates."""
        p1 = Point2D(5.0, 5.0)
        p2 = Point2D(2.0, 1.0)
        offset = GeometryOps.offset_coords(p2, p1)
        assert offset == [-3.0, -4.0]

    def test_projection_dist_same_point(self):
        """Test projection distance for same point."""
        p1 = Point2D(1.0, 1.0)
        p2 = Point2D(1.0, 1.0)
        distance = GeometryOps.projection_dist(p1, p2, 0)
        assert distance == pytest.approx(0.0)

    def test_projection_dist_different_points(self):
        """Test projection distance for different points."""
        p1 = Point2D(0.0, 0.0)
        p2 = Point2D(3.0, 4.0)
        distance = GeometryOps.projection_dist(p1, p2, 0)
        assert distance > 0

    def test_projection_dist_with_angle(self):
        """Test projection distance with various angles."""
        p1 = Point2D(0.0, 0.0)
        p2 = Point2D(1.0, 0.0)
        # Test at different angles
        for angle in [0, math.pi / 4, math.pi / 2]:
            distance = GeometryOps.projection_dist(p1, p2, angle)
            assert distance >= 0

    def test_rotate_vertex_zero_angle(self):
        """Test rotating vertex at zero angle."""
        point = Point2D(1.0, 0.0)
        sin_a = math.sin(0)
        cos_a = math.cos(0)
        rot_x, rot_y = GeometryOps.rotate_vertex(point, sin_a, cos_a)
        assert rot_x == pytest.approx(1.0)
        assert rot_y == pytest.approx(0.0)

    def test_rotate_vertex_90_degrees(self):
        """Test rotating vertex at 90 degrees."""
        point = Point2D(1.0, 0.0)
        sin_a = math.sin(math.pi / 2)
        cos_a = math.cos(math.pi / 2)
        rot_x, rot_y = GeometryOps.rotate_vertex(point, sin_a, cos_a)
        assert rot_x == pytest.approx(0.0, abs=0.01)
        assert rot_y == pytest.approx(1.0, abs=0.01)

    def test_rotate_coord_x_axis(self):
        """Test rotating coordinate on x-axis."""
        point = Point2D(1.0, 0.0)
        sin_a = math.sin(math.pi / 4)
        cos_a = math.cos(math.pi / 4)
        rotated = GeometryOps.rotate_coord(point, sin_a, cos_a, x_axis=True)
        assert isinstance(rotated, float)

    def test_rotate_coord_y_axis(self):
        """Test rotating coordinate on y-axis."""
        point = Point2D(1.0, 0.0)
        sin_a = math.sin(math.pi / 4)
        cos_a = math.cos(math.pi / 4)
        rotated = GeometryOps.rotate_coord(point, sin_a, cos_a, x_axis=False)
        assert isinstance(rotated, float)

    def test_perpendicular_dir_inside_polygon(self):
        """Test checking if perpendicular points inside polygon."""
        from shapely.geometry import Polygon
        room_coords = [
            (0.0, 0.0),
            (10.0, 0.0),
            (10.0, 10.0),
            (0.0, 10.0)
        ]
        shapely_poly = Polygon(room_coords)
        
        # Edge coordinates (top edge)
        edge_coords = [(0.0, 10.0), (10.0, 10.0)]
        
        # Perpendicular pointing downward (into polygon)
        perp_inside = math.pi * 1.5  # 270 degrees
        result_inside = GeometryOps.perpendicular_dir_inside_polygon(
            shapely_poly, edge_coords, perp_inside
        )
        assert isinstance(result_inside, bool)

    def test_normalize_angle_positive(self):
        """Test normalizing positive angles."""
        angle = 3 * math.pi
        normalized = GeometryOps.normalize_angle(angle)
        assert 0 <= normalized < 2 * math.pi

    def test_normalize_angle_negative(self):
        """Test normalizing negative angles."""
        angle = -math.pi
        normalized = GeometryOps.normalize_angle(angle)
        assert 0 <= normalized < 2 * math.pi

    def test_normalize_angle_zero(self):
        """Test normalizing zero angle."""
        angle = 0.0
        normalized = GeometryOps.normalize_angle(angle)
        assert normalized == pytest.approx(0.0)

    def test_normalize_angle_2pi(self):
        """Test normalizing 2π angle."""
        angle = 2 * math.pi
        normalized = GeometryOps.normalize_angle(angle)
        assert normalized == pytest.approx(0.0)

    def test_normalize_angle_large_positive(self):
        """Test normalizing large positive angles."""
        angle = 5 * math.pi
        normalized = GeometryOps.normalize_angle(angle)
        assert 0 <= normalized < 2 * math.pi

    def test_normalize_angle_large_negative(self):
        """Test normalizing large negative angles."""
        angle = -5 * math.pi
        normalized = GeometryOps.normalize_angle(angle)
        assert 0 <= normalized < 2 * math.pi
