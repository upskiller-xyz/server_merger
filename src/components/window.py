from typing import Tuple, List
import math
import numpy as np
from shapely.geometry import Polygon as ShapelyPolygon, LineString as ShapelyLine
from shapely.affinity import rotate as shapely_rotate
from src.components.enums import ParameterName
from src.components.graphics_constants import GRAPHICS_CONSTANTS
from src.components.geometry_ops import Point2D, Point3D, GeometryOps
# from src.components.room_polygon import RoomPolygon


class RoomPolygon:
    """
    Represents a room's floor plan as a polygon

    Coordinate system:
    - Origin is at window center on the outer façade plane
    - X-axis points right (parallel to façade)
    - Y-axis points into the room (perpendicular to façade)
    - Window is on the right side of the image
    """

    def __init__(self, vertices: List[Tuple[float, float]]):
        """
        Initialize room polygon

        Args:
            vertices: List of (x, y) coordinates in meters
        """
        if len(vertices) < 3:
            raise ValueError("Polygon must have at least 3 vertices")

        self._vertices = [Point2D(x, y) for x, y in vertices]

    @property
    def width(self)->float:
        min_x, _, max_x, _ = self.get_bounds()
        return max_x - min_x
    
    @property
    def height(self)->float:
        _, min_y, _, max_y = self.get_bounds()
        return max_y - min_y
        # room_height_px = int(np.ceil((max_y - min_y) / self.output_scale))

    @property
    def vertices(self) -> List[Point2D]:
        """Get polygon vertices"""
        return self._vertices

    def rotate(self, angle_degrees: float, center: Point2D = None) -> 'RoomPolygon':
        """
        Rotate polygon around a center point using Shapely

        Args:
            angle_degrees: Rotation angle in degrees (positive = counter-clockwise)
            center: Center of rotation (default: origin (0,0))

        Returns:
            New RoomPolygon with rotated vertices
        """
        if center is None:
            center = Point2D(0, 0)

        # Create Shapely polygon from vertices
        
        shapely_poly = ShapelyPolygon(self.get_coords())
        
        rotated_poly = shapely_rotate(
            shapely_poly,
            angle_degrees,
            origin=(center.x, center.y)
        )

        # Extract rotated vertices
        rotated_vertices = list(rotated_poly.exterior.coords)[:-1]  # Remove duplicate last point
        return RoomPolygon(rotated_vertices)

    def get_bounds(self):
        min_x, min_y = np.array(self.get_coords()).min(axis=0)
        max_x, max_y = np.array(self.get_coords()).max(axis=0)
        return (min_x, min_y, max_x, max_y)
    
    def translate(self, point:Point2D)->'RoomPolygon':
        verts = [(x - point.x, y - point.y) for x, y in self.get_coords()]
        return RoomPolygon(verts)
    
    def shift_to_zero(self)->'RoomPolygon':
        min_x, min_y, _, _ = self.get_bounds()
        return self.translate(Point2D(min_x, min_y))
    
    def point_to_zero(self, point:Point2D)->Point2D:
        min_x, min_y, _, max_y = self.get_bounds()
        # X: shift to min_x = 0
        # Y: flip from world coords (Y-up) to image coords (Y-down)
        # Formula: (height) - (point_y - min_y) = (max_y - min_y) - (point_y - min_y)
        
        height = max_y - min_y
        return Point2D(point.x - min_x, height - (point.y - min_y))
    
    def get_edges(self):
        polygon_coords = self.get_coords()
        
        return [ShapelyLine([
            polygon_coords[i], 
            polygon_coords[(i + 1) % len(polygon_coords)]]) for i in range(len(polygon_coords))]
    
    def get_coords(self):
        return [(v.x, v.y) for v in self._vertices]

    def _build_edge(self, ind:int):
        v1 = self._vertices[ind]
        v2 = self._vertices[(ind + 1) % len(self._vertices)]

        return ShapelyLine([(v1.x, v1.y), (v2.x, v2.y)])

    def _window_edge_and_rotation(
        self,
        window_line: ShapelyLine,
        tolerance: float = 0.01
    ) -> Tuple[ShapelyLine, int, float]:
        """
        Find which polygon edge contains the window and calculate rotation needed.

        Args:
            window_x1, window_y1: First window endpoint
            window_x2, window_y2: Second window endpoint
            tolerance: Distance tolerance for edge matching

        Returns:
            Tuple of (edge_index, rotation_angle_degrees, needs_flip)
            - edge_index: Index of the edge containing the window
            - rotation_angle_degrees: Angle to rotate so window edge is horizontal (constant y)
            - needs_flip: Whether to flip direction so room extends in -y direction
        """
        

        edges = [self._build_edge(i) for i in range(len(self._vertices))]
        edges = [(i,edge) for i,edge in enumerate(edges) if edge.buffer(tolerance).contains(window_line)]

        if len(edges)<1:
            raise ValueError(
            f"Window at ({window_line.coords[0][0]:.2f}, {window_line.coords[0][1]:.2f}) to ({window_line.coords[1][0]:.2f}, {window_line.coords[1][1]:.2f}) "
            f"does not lie on any polygon edge")
        
        ind, edge = edges[0]
        v1 = self._vertices[ind]
        v2 = self._vertices[(ind + 1) % len(self._vertices)]
        edge_angle = math.atan2(v2.y - v1.y, v2.x - v1.x) * 180 / math.pi

        return edge, ind, edge_angle
        
    def to_pixel_array(
        self,
        image_size: int = 128,
        window_x1: float = None,
        window_y1: float = None,
        window_x2: float = None,
        window_y2: float = None,
        direction_angle: float = None,
        wall_thickness: float = None
    ) -> np.ndarray:
        """
        Convert polygon to pixel coordinates for drawing on image

        The room polygon is positioned so that:
        - The edge containing the window is rotated to be horizontal (constant y)
        - The window edge aligns with the left edge of the window area on the image
        - The room extends to the left (negative x in image coordinates)
        - Window outer wall (left edge) is at: image_size - 12 - wall_thickness pixels from left
        - Resolution: 1 pixel = 0.1m (10cm) for 128x128 image, scales proportionally

        Args:
            image_size: Image dimension in pixels (default 128)
            window_x1: Window left x coordinate in meters (required)
            window_y1: Window front y coordinate in meters (required)
            window_x2: Window right x coordinate in meters (required)
            window_y2: Window back y coordinate in meters (required)
            direction_angle: Window direction angle in radians (optional, if not provided will be calculated from polygon edge)

        Returns:
            Numpy array of shape (N, 1, 2) for cv2.fillPoly
        """
        if window_x1 is None or window_y1 is None or window_x2 is None or window_y2 is None:
            raise ValueError("Window coordinates required for room positioning")
            
        rotated_polygon = self.get_coords()
        
        window = WindowGeometry.from_corners(window_x1, window_y1, 0, window_x2, window_y2, 0)
        w_edges = window.get_candidate_edges()

        # Create polygon from rotated coordinates to check which edge is on it
        rotated_room_poly = ShapelyPolygon(rotated_polygon)
        tolerance = 0.01

        # Check which edge is on the polygon boundary
        edge_on_boundary = None
        
        res = [w_edge for w_edge in w_edges if rotated_room_poly.boundary.buffer(tolerance).contains(w_edge)]

        window_center_rotated = Point2D((window_x1 + window_x2) *0.5, (window_y1 + window_y2) *0.5)
        if len(res)>0:
            edge_on_boundary = res[0]
            edge_coords = list(edge_on_boundary.coords)
            window_center_rotated = Point2D(
                (edge_coords[0][0] + edge_coords[1][0]) *0.5,
                (edge_coords[0][1] + edge_coords[1][1]) *0.5
            )
        
        rotated_polygon = RoomPolygon(rotated_polygon)
        
        
        wall_thickness_px = GRAPHICS_CONSTANTS.get_pixel_value(GRAPHICS_CONSTANTS.WALL_THICKNESS_M, image_size)

        if direction_angle is not None:
            window_geom = WindowGeometry(
                window_x1, window_y1, 0,
                window_x2, window_y2, 0,
                direction_angle=direction_angle
            )
            wall_thickness_px = window_geom.wall_thickness_px
                
        
        # Window's left edge position on image
        window_left_edge_x = image_size - GRAPHICS_CONSTANTS.WINDOW_OFFSET_PX - wall_thickness_px

        # Room should align 1 pixel to the left of window for perfect adjacency (C-frame)
        room_facade_x = window_left_edge_x - GRAPHICS_CONSTANTS.ROOM_FACADE_OFFSET_PX
        window_y_pixels = image_size // 2
        

        # First pass: calculate room extent to check for obstruction bar overlap
        dims = ImageDimensions(image_size)
        obs_bar_x_start, _, _, _ = dims.get_obstruction_bar_position()
        
        offsets = [GeometryOps.offset_coords(vertex, window_center_rotated) for vertex in rotated_polygon.vertices]

        offsets = [[GRAPHICS_CONSTANTS.get_pixel_value(i, image_size) for i in dd] for dd in offsets]

        # Flip y-axis: image coordinates have y increasing downward, geometric coordinates have y increasing upward
        pixel_coords = [[room_facade_x + dx,
                         window_y_pixels - dy] for [dx, dy] in offsets]
        
        # Clip room to avoid overlap with obstruction bar
        right_boundary = obs_bar_x_start - GRAPHICS_CONSTANTS.OBSTRUCTION_BAR_GAP_PX 
        # Create clipping rectangle: x from 0 to right_boundary, y from 0 to image_size
        room_poly = ShapelyPolygon(pixel_coords)
        clip_box = ShapelyBox(0, 0, right_boundary, image_size)

        # Clip the polygon
        clipped = room_poly.intersection(clip_box)
        
        # clipped = room_poly
        # Use GeometryAdapter to handle different geometry types (Adapter Pattern)
        return GeometryAdapter.extract_coordinates(clipped, fallback_coords=pixel_coords)

    @classmethod
    def from_dict(cls, data: List) -> 'RoomPolygon':
        """
        Create polygon from list of coordinate dictionaries or lists

        Args:
            data: List of dicts like [{"x": 0, "y": 0}, {"x": 3, "y": 0}, ...]
                  OR list of lists/tuples like [[0, 0], [3, 0], ...] or [(0, 0), (3, 0), ...]

        Returns:
            RoomPolygon instance

        Raises:
            ValueError: If data format is invalid
        """
        if not data:
            raise ValueError("Polygon data cannot be empty")

        # Check format of first element to determine data structure
        first_element = data[0]

        if isinstance(first_element, dict):
            # List of dictionaries format: [{"x": 0, "y": 0}, ...]
            vertices = [(point["x"], point["y"]) for point in data]
        elif isinstance(first_element, (list, tuple)):
            # List of lists/tuples format: [[0, 0], ...] or [(0, 0), ...]
            vertices = [(point[0], point[1]) for point in data]
        else:
            raise ValueError(
                f"Invalid polygon data format. Expected list of dicts or list of lists/tuples, "
                f"but got list of {type(first_element).__name__}"
            )

        return cls(vertices)


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
        image_size: int = 128,
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
    def from_dict(cls, data: dict) -> 'WindowGeometry':
        """
        Create window geometry from dictionary

        Args:
            data: Dict with keys x1, y1, z1, x2, y2, z2, and optionally direction_angle

        Returns:
            WindowGeometry instance
        """
        return cls(
            x1=data[ParameterName.X1.value],
            y1=data[ParameterName.Y1.value],
            z1=data[ParameterName.Z1.value],
            x2=data[ParameterName.X2.value],
            y2=data[ParameterName.Y2.value],
            z2=data[ParameterName.Z2.value],
            direction_angle=data.get(ParameterName.DIRECTION_ANGLE.value, 0)
        )

    def get_candidate_edges(self):
        # Create the two possible window edges from bounding box
        # The 4 corners are: (x1,y1), (x2,y1), (x1,y2), (x2,y2)
        # The two candidate edges (matching the validation logic) are:
        window_edge1 = ShapelyLine([(self.x1, self.y1), (self.x2, self.y1)])
        window_edge2 = ShapelyLine([(self.x1, self.y2), (self.x2, self.y2)])
        window_edge3 = ShapelyLine([(self.x1, self.y1), (self.x1, self.y2)])
        window_edge4 = ShapelyLine([(self.x2, self.y1), (self.x2, self.y2)])
        return [window_edge1, window_edge2, window_edge3, window_edge4]

    def get_room_edge(self, room_polygon:RoomPolygon, tolerance=0.01)->list:
        w_edges = self.get_candidate_edges()
        # Find which polygon edge contains one of the window edges

        poly_edges = room_polygon.get_edges()
        res = [(edge, i, j) for i,edge in enumerate(poly_edges) for j, w_edge in enumerate(w_edges) if edge.buffer(tolerance).contains(w_edge)]
        return res
    
    def reference_from_polygon(
        self,
        room_polygon: 'RoomPolygon',
        tolerance: float = 0.01
    ) -> Point2D:
        """
        Finds window's reference point from the room polygon, in meters
        the window is facing (perpendicular to the edge, pointing away from room).

        Args:
            room_polygon: The room polygon containing this window
            tolerance: Distance tolerance for edge matching (meters)

        Returns:
            reference point, meters

        Raises:
            ValueError: If window is not on any polygon edge
        """


        # w_edges = self.get_candidate_edges()
        # # Find which polygon edge contains one of the window edges
        # polygon_coords =  room_polygon.get_coords()

        res = self.get_room_edge(room_polygon, tolerance)
        if len(res)<1:
            raise ValueError(
            f"Window at ({self.x1:.2f}, {self.y1:.2f}) to ({self.x2:.2f}, {self.y2:.2f}) "
            f"does not lie on any polygon edge"
        )

        edge, i, j = res[0]
        w_edges = self.get_candidate_edges()
        w_edge = w_edges[j]
        edge_coords = list(w_edge.coords)

        return Point2D(0.5*(edge_coords[0][0] + edge_coords[1][0]),
                       0.5*(edge_coords[0][1] + edge_coords[1][1]) )

    def get_reference_pixel(self) -> Tuple[int, int]:
        """
        Calculate window reference point in pixel coordinates of the 128x128 image.

        Following DECODING_GUIDE Step 1:
        The window reference point is at the room-facing edge (room facade).
        Formula: room_facade_x = IMAGE_SIZE - WINDOW_OFFSET_PX - wall_thickness_px - ROOM_FACADE_OFFSET_PX

        Returns:
            (ref_x, ref_y) in pixels at 128x128 resolution
        """
        # Convert wall thickness to pixels using round (0.300m = 3px, not 2px)
        wall_thickness_px = round(self.wall_thickness / GRAPHICS_CONSTANTS.BASE_RESOLUTION_M_PER_PX)

        # Calculate room facade position
        room_facade_x = (
            GRAPHICS_CONSTANTS.BASE_IMAGE_SIZE_PX -
            GRAPHICS_CONSTANTS.WINDOW_OFFSET_PX -
            wall_thickness_px -
            GRAPHICS_CONSTANTS.ROOM_FACADE_OFFSET_PX
        )

        # Reference point is at vertical center
        ref_y = GRAPHICS_CONSTANTS.BASE_IMAGE_SIZE_PX // 2

        return (room_facade_x, ref_y)

    def calculate_direction_from_polygon(
        self,
        room_polygon: 'RoomPolygon',
        tolerance: float = 0.01
    ) -> float:
        """
        EXPERIMENTAL: Calculate direction_angle from room polygon edge

        Finds which polygon edge contains the window and calculates the direction
        the window is facing (perpendicular to the edge, pointing away from room).

        Args:
            room_polygon: The room polygon containing this window
            tolerance: Distance tolerance for edge matching (meters)

        Returns:
            direction_angle in radians (0 = pointing right/east, π/2 = pointing up/north)

        Raises:
            ValueError: If window is not on any polygon edge
        """
        
        
        # w_edges = self.get_candidate_edges()
        # # Find which polygon edge contains one of the window edges
        polygon_coords =  room_polygon.get_coords()

        res = self.get_room_edge(room_polygon, tolerance)
        if len(res)<1:
            raise ValueError(
            f"Window at ({self.x1:.2f}, {self.y1:.2f}) to ({self.x2:.2f}, {self.y2:.2f}) "
            f"does not lie on any polygon edge"
        )

        edge, i, j = res[0]
        v1 = polygon_coords[i]
        v2 = polygon_coords[(i + 1) % len(polygon_coords)]

        # Edge angle (direction along the edge)
        edge_angle = math.atan2(v2[1] - v1[1], v2[0] - v1[0])


        perps = [edge_angle + math.pi *0.5, edge_angle - math.pi *0.5]
        # Get center point of the window edge that's on the polygon boundary
        edge_coords = list(edge.coords)

        room_poly = ShapelyPolygon(polygon_coords)
        
        # Select the perpendicular pointing OUTSIDE the room (window facing direction)
        # Windows face outward from the building
        calculated_angle = perps[0]
        res = [perp for perp in perps if not GeometryOps.perpendicular_dir_inside_polygon(room_poly, edge_coords, perp)]
        if len(res)>0:
            calculated_angle = res[0]

        calculated_angle = GeometryOps.normalize_angle(calculated_angle)
        

        return calculated_angle
    