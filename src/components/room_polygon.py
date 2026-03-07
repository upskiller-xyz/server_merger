from typing import List, Tuple
import math
import numpy as np

from shapely.geometry import Polygon as ShapelyPolygon, LineString as ShapelyLine
from shapely.affinity import rotate as shapely_rotate
from src.components.geometry_ops import Point2D


class RoomPolygon:
    """
    Represents a room's floor plan as a polygon

    Coordinate system:
    - Origin is at window center on the outer façade plane
    - X-axis points right (parallel to façade)
    - Y-axis points into the room (perpendicular to façade)
    - Window is on the right side of the image
    """

    def __init__(self, vertices: List[Tuple[float, ...]]):
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

    def rotate(self, angle_degrees: float, center: Point2D = Point2D(0, 0)) -> 'RoomPolygon':
        """
        Rotate polygon around a center point using Shapely

        Args:
            angle_degrees: Rotation angle in degrees (positive = counter-clockwise)
            center: Center of rotation (default: origin (0,0))

        Returns:
            New RoomPolygon with rotated vertices
        """

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
