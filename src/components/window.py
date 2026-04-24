from typing import Tuple
import math

from shapely.geometry import Polygon as ShapelyPolygon, LineString as ShapelyLine, Point as ShapelyPoint
from shapely.affinity import rotate as shapely_rotate
from src.core.enums import ParameterName
from src.core.graphics_constants import GRAPHICS_CONSTANTS
from src.components.geometry_ops import Point2D, Point3D, GeometryOps
from src.components.room_polygon import RoomPolygon
from src.core.exceptions import WindowOrientationError


class WindowGeometry:
    """
    Represents window geometry from bounding box coordinates

    Window is viewed from top (plan view):
    - Appears as a vertical line/rectangle
    - Width (horizontal) = outer wall thickness (appears as horizontal width on image)
    - Height (vertical on image) = window width in 3D (x2 - x1)
    - Located 12 pixels from right edge (8 pixels from obstruction bar)

    Coordinate system:
    - X-axis: along façade (horizontal)
    - Y-axis: perpendicular to façade (into room, not used in top view)
    - Z-axis: vertical (height)
    """

    def __init__(
        self,
        x1: float,
        y1: float,
        z1: float,
        x2: float,
        y2: float,
        z2: float,
        direction_angle: float|None = None
    ):
        """
        Initialize window geometry from bounding box

        Args:
            x1, y1, z1: Left-bottom corner coordinates in meters
            x2, y2, z2: Right-top corner coordinates in meters
            direction_angle: Window direction angle in radians (optional)
        """
        self._corner1 = Point3D(x1, y1, z1)
        self._corner2 = Point3D(x2, y2, z2)
        self._direction_angle = direction_angle

        # Ensure corner1 is bottom-left and corner2 is top-right
        self._x_min = min(x1, x2)
        self._x_max = max(x1, x2)
        self._z_min = min(z1, z2)
        self._z_max = max(z1, z2)
        self._y_min = min(y1,y2)
        self._y_max = max(y1, y2)

    @property
    def window_width_3d(self) -> float:
        """
        Get window width in 3D space (perpendicular to direction_angle)

        If direction_angle is provided, calculates the perpendicular distance
        between the two lines perpendicular to direction_angle passing through
        (x1,y1) and (x2,y2).

        Otherwise falls back to max of x-span and y-span.
        """
        if self._direction_angle is None:
            return max(self._x_max - self._x_min, self._y_max - self._y_min)
        edge_angle = self._direction_angle + math.pi *0.5
        return GeometryOps.projection_dist(self._corner1, self._corner2, edge_angle)
            
    @property
    def wall_thickness(self) -> float:
        """
        Get wall thickness from window bounding box (distance in direction_angle direction)

        This is the distance between the two parallel edges of the window rectangle
        that are perpendicular to direction_angle. It represents the wall thickness
        where the window is installed.

        If direction_angle is not provided, falls back to min of bounding box dimensions.
        """
        if self._direction_angle is None:
            return min(self._y_max - self._y_min, self._x_max - self._x_min)
        
        return GeometryOps.projection_dist(self._corner1, self._corner2, self._direction_angle)
        
    @property
    def window_height_3d(self) -> float:
        """Get window height in 3D space (vertical, z-direction)"""
        return self._z_max - self._z_min

    @property
    def sill_height(self) -> float:
        """Get sill height (minimum z coordinate)"""
        return self._z_min

    @property
    def top_height(self) -> float:
        """Get top height (maximum z coordinate)"""
        return self._z_max

    @property
    def x1(self) -> float:
        """Get x1 coordinate"""
        return self._corner1.x

    @property
    def y1(self) -> float:
        """Get y1 coordinate"""
        return self._corner1.y

    @property
    def x2(self) -> float:
        """Get x2 coordinate"""
        return self._corner2.x

    @property
    def y2(self) -> float:
        """Get y2 coordinate"""
        return self._corner2.y

    @property
    def z1(self) -> float:
        """Get z1 coordinate"""
        return self._corner1.z

    @property
    def z2(self) -> float:
        """Get z2 coordinate"""
        return self._corner2.z
    
    @property
    def niche_center(self)->Point2D:
        return Point2D((self.x1 + self.x2) *0.5, 
                       (self.y1 + self.y2) *0.5)

    @property
    def direction_angle(self) -> float|None:
        """Get window direction angle in radians (None if not set)"""
        return self._direction_angle

    def rotate(self, angle_degrees: float, center: Point2D|None = None) -> 'WindowGeometry':
        """
        Rotate window geometry around a center point using Shapely

        Args:
            angle_degrees: Rotation angle in degrees (positive = counter-clockwise)
            center: Center of rotation in 2D (default: origin (0,0))

        Returns:
            New WindowGeometry with rotated coordinates
        """
        if center is None:
            center = Point2D(0, 0)

        # Create line segment from the two corners
        line = ShapelyLine([(self._corner1.x, self._corner1.y), (self._corner2.x, self._corner2.y)])
        rotated_line = shapely_rotate(line, angle_degrees, origin=(center.x, center.y))

        # Extract rotated coordinates
        coords = list(rotated_line.coords)
        new_x1, new_y1 = coords[0]
        new_x2, new_y2 = coords[1]

        return WindowGeometry(
            new_x1, new_y1, self._corner1.z,
            new_x2, new_y2, self._corner2.z
        )

    def get_pixel_bounds(
        self,
        image_size: int = GRAPHICS_CONSTANTS.BASE_IMAGE_SIZE_PX,
        window_offset_px: int|None = None
    ) -> Tuple[int, int, int, int]:
        """
        Get window bounds in pixel coordinates for top view

        In top view:
        - Window appears as vertical line at fixed x position (default 12px from right)
        - Horizontal extent = wall thickness (approximately constant)
        - Vertical extent = window width in 3D converted to pixels

        Args:
            image_size: Image dimension in pixels (default 128)
            window_offset_px: Distance from right edge in pixels (uses GRAPHICS_CONSTANTS if None)

        Returns:
            (x_start, y_start, x_end, y_end) tuple in pixels
        """
        if window_offset_px is None:
            window_offset_px = GRAPHICS_CONSTANTS.WINDOW_OFFSET_PX

        window_x_end = image_size - window_offset_px
        window_x_start = window_x_end - self.wall_thickness_px
        
        window_height_px = GRAPHICS_CONSTANTS.get_pixel_value(self.window_width_3d)  

        # Center vertically
        
        window_y_start = image_size // 2 - window_height_px // 2
        window_y_end = window_y_start + window_height_px

        # Clamp to image bounds
        x_start = max(0, window_x_start)
        x_end = min(image_size, window_x_end)
        y_start = max(0, window_y_start)
        y_end = min(image_size, window_y_end)

        return (x_start, y_start, x_end, y_end)
    
    @property
    def wall_thickness_px(self):
        wall_thickness_m = self.wall_thickness
        # Fallback to default if calculated thickness is 0 (e.g., when y1==y2)
        if wall_thickness_m == 0:
            wall_thickness_m = GRAPHICS_CONSTANTS.WALL_THICKNESS_M
        return GRAPHICS_CONSTANTS.get_pixel_value(wall_thickness_m) 

    @classmethod
    def from_corners(
        cls,
        x1: float, y1: float, z1: float,
        x2: float, y2: float, z2: float
    ) -> 'WindowGeometry':
        """
        Create window geometry from corner coordinates

        Args:
            x1, y1, z1: First corner in meters
            x2, y2, z2: Second corner in meters

        Returns:
            WindowGeometry instance
        """
        return cls(x1, y1, z1, x2, y2, z2)

    @classmethod
    def from_dict(cls, content: dict) -> 'WindowGeometry':
        """
        Create window geometry from dictionary

        Args:
            data: Dict with keys x1, y1, z1, x2, y2, z2, and optionally direction_angle

        Returns:
            WindowGeometry instance
        """
        return cls(
            x1=content[ParameterName.X1.value],
            y1=content[ParameterName.Y1.value],
            z1=content[ParameterName.Z1.value],
            x2=content[ParameterName.X2.value],
            y2=content[ParameterName.Y2.value],
            z2=content[ParameterName.Z2.value],
            direction_angle=content.get(ParameterName.DIRECTION_ANGLE.value, 0)
        )
    
    def _rotated_corner(self, up:bool=True, right:bool=True)->Tuple[float, float]:
        center = self.niche_center
        _up = up
        _right = right
        if not up:
            _up = -1
        if not right:
            _right = -1

        # Use direction_angle if set, otherwise default to 0 (facing right)
        angle = self._direction_angle if self._direction_angle is not None else 0.0

        # Wall direction (perpendicular to window normal)
        wall_angle = angle + math.pi * 0.5
        wall_dx = math.cos(wall_angle)
        wall_dy = math.sin(wall_angle)

        norm_dx = math.cos(angle)
        norm_dy = math.sin(angle)

        half_width = self.window_width_3d * 0.5
        half_thick = self.wall_thickness * 0.5

        x = center.x + _up * half_width * wall_dx + _right * half_thick * norm_dx
        y = center.y + _up * half_width * wall_dy + _right * half_thick * norm_dy

        return (x, y)

    def get_candidate_edges(self):
        """Compute edges of the rotated window rectangle using direction_angle."""
        # 4 corners of rotated rectangle
        c1 = self._rotated_corner(up=False, right=False)
        c2 = self._rotated_corner(up=True, right=False)
        c3 = self._rotated_corner(up=True, right=True)
        c4 = self._rotated_corner(up=False, right=True)

        # 4 edges: interior, exterior, and two sides
        return [
            ShapelyLine([c1, c2]),  # interior (away from normal)
            ShapelyLine([c3, c4]),  # exterior (toward normal)
            ShapelyLine([c1, c4]),  # side
            ShapelyLine([c2, c3]),  # side
        ]

    def get_room_edge(self, room_polygon:RoomPolygon, tolerance=GRAPHICS_CONSTANTS.WINDOW_PLACEMENT_TOLERANCE)->list:
        w_edges = self.get_candidate_edges()
        # Find which polygon edge contains one of the window edges

        poly_edges = room_polygon.get_edges()
        res = [(edge, i, j) for i,edge in enumerate(poly_edges) for j, w_edge in enumerate(w_edges) if edge.buffer(tolerance).contains(w_edge)]
        return res
    
    def reference_from_polygon(
        self,
        room_polygon: 'RoomPolygon',
        tolerance: float = GRAPHICS_CONSTANTS.WINDOW_PLACEMENT_TOLERANCE
    ) -> Point2D:
        """
        Finds window's reference point from the room polygon, in meters.
        Projects window center onto nearest polygon edge.

        Args:
            room_polygon: The room polygon containing this window
            tolerance: Distance tolerance for edge matching (meters)

        Returns:
            reference point, meters
        """
        res = self.get_room_edge(room_polygon, tolerance)
        if len(res) >= 1:
            edge, i, j = res[0]
            w_edges = self.get_candidate_edges()
            w_edge = w_edges[j]
            edge_coords = list(w_edge.coords)
            return Point2D(0.5*(edge_coords[0][0] + edge_coords[1][0]),
                           0.5*(edge_coords[0][1] + edge_coords[1][1]) )

        # Fallback: project window center onto polygon boundary
        
        center = self.niche_center
        window_center = ShapelyPoint(center.x, center.y)
        coords = room_polygon.get_coords()
        poly_boundary = ShapelyLine(coords + [coords[0]])
        projected = poly_boundary.interpolate(poly_boundary.project(window_center))
        return Point2D(projected.x, projected.y)

    def get_reference_pixel(self) -> Tuple[int, int]:
        """
        Calculate window reference point in pixel coordinates of the 128x128 image.

        Following DECODING_GUIDE Step 1:
        The window reference point is at the room-facing edge (room facade).
        Formula: room_facade_x = IMAGE_SIZE - WINDOW_OFFSET_PX - wall_thickness_px - ROOM_FACADE_OFFSET_PX

        Returns:
            (ref_x, ref_y) in pixels at 128x128 resolution
        """
        # Calculate room facade position — use wall_thickness_px property which applies
        # the same 0.3m fallback used by the encoder when wall thickness rounds to zero.
        room_facade_x = (
            GRAPHICS_CONSTANTS.BASE_IMAGE_SIZE_PX -
            GRAPHICS_CONSTANTS.WINDOW_OFFSET_PX -
            self.wall_thickness_px -
            GRAPHICS_CONSTANTS.ROOM_FACADE_OFFSET_PX
        )

        # Reference point is at vertical center
        ref_y = GRAPHICS_CONSTANTS.BASE_IMAGE_SIZE_PX // 2

        return (room_facade_x, ref_y)
    
    def _project_to_polygon_edge(
        self,
        room_polygon,
        tolerance: float = GRAPHICS_CONSTANTS.WINDOW_PLACEMENT_TOLERANCE
    ) -> tuple:
        """
        Project window center onto the polygon boundary and find the containing edge.

        This is a shared helper for calculate_reference_point_from_polygon and
        calculate_direction_from_polygon.

        Args:
            room_polygon: The room polygon containing this window
            tolerance: Distance tolerance for edge matching (meters)

        Returns:
            Tuple of (projected_point: ShapelyPoint, edge_index: int, edge: ShapelyLine)

        Raises:
            ValueError: If projected point is not on any polygon edge
        """
        # Calculate center of the window bounding box
        window_center = ShapelyPoint(self.niche_center.x, self.niche_center.y)

        # Create polygon boundary as closed line
        poly_boundary = ShapelyLine(room_polygon.get_coords() + [room_polygon.get_coords()[0]])

        # Project window center onto the closest point on the boundary
        dist_along = poly_boundary.project(window_center)
        projected_point = poly_boundary.interpolate(dist_along)

        # Find which edge contains the projected point
        poly_edges = room_polygon.get_edges()
        for i, edge in enumerate(poly_edges):
            if edge.buffer(tolerance).contains(projected_point):
                return (projected_point, i, edge)

        # No edge found - raise error
        raise ValueError(
            f"Projected point ({projected_point.x:.2f}, {projected_point.y:.2f}) "
            f"does not lie on any polygon edge (tolerance: {tolerance}m)"
        )

    def calculate_direction_from_polygon(
        self,
        room_polygon: 'RoomPolygon',
        tolerance: float = GRAPHICS_CONSTANTS.WINDOW_PLACEMENT_TOLERANCE
    ) -> float:
        """
        Calculate direction_angle from room polygon edge.

        Finds which polygon edge contains the window and calculates the direction
        the window is facing (perpendicular to the edge, pointing away from room).
        Falls back to projection-based approach for diagonal walls.

        Args:
            room_polygon: The room polygon containing this window
            tolerance: Distance tolerance for edge matching (meters)

        Returns:
            direction_angle in radians (0 = pointing right/east, π/2 = pointing up/north)
        """
        polygon_coords = room_polygon.get_coords()

        # res = self.get_room_edge(room_polygon, tolerance)
        _, edge_index, edge = self._project_to_polygon_edge(room_polygon, tolerance)
        

        v1 = polygon_coords[edge_index]
        v2 = polygon_coords[(edge_index + 1) % len(polygon_coords)]

        # Edge angle (direction along the edge)
        edge_angle = math.atan2(v2[1] - v1[1], v2[0] - v1[0])

        perps = [edge_angle + math.pi * 0.5, edge_angle - math.pi * 0.5]
        edge_coords = list(edge.coords)
        room_poly = ShapelyPolygon(polygon_coords)

        # Select the perpendicular pointing OUTSIDE the room (window facing direction)
        calculated_angle = perps[0]
        res = [perp for perp in perps if not GeometryOps.perpendicular_dir_inside_polygon(room_poly, edge_coords, perp)]
        if len(res) < 1:
            raise WindowOrientationError()
        calculated_angle = res[0]

        return GeometryOps.normalize_angle(calculated_angle)
    