from typing import List, Tuple, Any, Union, Dict, Callable
from dataclasses import dataclass
from abc import ABC, abstractmethod
import math
import numpy as np
import cv2
from shapely.geometry import Polygon as ShapelyPolygon, Point as ShapelyPoint, LineString as ShapelyLine, box as ShapelyBox
from shapely.affinity import rotate as shapely_rotate
from src.components.graphics_constants import GRAPHICS_CONSTANTS

@dataclass
class Point2D:
    """Represents a 2D point in meters"""
    x: float
    y: float

    def to_pixel(self, resolution: float = 0.1) -> Tuple[int, int]:
        """
        Convert point from meters to pixels

        Args:
            resolution: Meters per pixel (default 0.1m = 10cm)

        Returns:
            (x_pixel, y_pixel) tuple
        """
        return (GRAPHICS_CONSTANTS.get_pixel_value(self.x), GRAPHICS_CONSTANTS.get_pixel_value(self.y))


@dataclass
class Point3D:
    """Represents a 3D point in meters"""
    x: float
    y: float
    z: float

    def to_point2d(self) -> Point2D:
        """Convert to 2D point by dropping z coordinate"""
        return Point2D(self.x, self.y)

    def to_pixel(self, resolution: float = 0.1) -> Tuple[int, int]:
        """
        Convert point from meters to pixels (x, y only)

        Args:
            resolution: Meters per pixel (default 0.1m = 10cm)

        Returns:
            (x_pixel, y_pixel) tuple
        """
        return self.to_point2d().to_pixel(resolution)



class GeometryOps:

    @classmethod 
    def project(cls, vv:Point2D | Point3D, sin_a:float, cos_a:float):
        return vv.x * cos_a + vv.y * sin_a
    
    @classmethod
    def offset_coords(cls, vv:Point2D|Point3D, vv1:Point2D|Point3D):
        dx = vv.x - vv1.x  # Along façade
        dy = vv.y - vv1.y  # Perpendicular to façade
        return [dx, dy]
    
    @classmethod
    def projection_dist(cls, vv:Point2D|Point3D, vv1:Point2D|Point3D, angle):
        # Unit vector perpendicular to direction_angle
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)

        # Project both points onto the perpendicular direction
        # Point 1 projection
        proj1 = GeometryOps.project(vv, sin_a, cos_a)
        proj2 = GeometryOps.project(vv1, sin_a, cos_a)
        
        # Window width is the distance between projections
        return abs(proj2 - proj1)
    
    @classmethod
    def rotate_vertex(cls, vv:Point2D|Point3D, sin_a:float, cos_a:float):
        rot_x = cls.rotate_coord(vv, sin_a, cos_a) 
        rot_y = cls.rotate_coord(vv, sin_a, cos_a, False)
        return (rot_x, rot_y)
    
    @classmethod
    def rotate_coord(cls, vv:Point2D|Point3D, sin_a:float, cos_a:float, x_axis=True):
        if x_axis:
            return vv.x * cos_a - vv.y * sin_a 
        return vv.x * sin_a + vv.y * cos_a
    
    @classmethod
    def perpendicular_dir_inside_polygon(cls, room_poly, edge_coords, perp)->bool:
        test_offset = 0.1
        edge_center_x = (edge_coords[0][0] + edge_coords[1][0]) *0.5
        edge_center_y = (edge_coords[0][1] + edge_coords[1][1]) *0.5
        test_x1 = edge_center_x + test_offset * math.cos(perp)
        test_y1 = edge_center_y + test_offset * math.sin(perp)
        test_point1 = ShapelyPoint(test_x1, test_y1)
        return room_poly.contains(test_point1)
    
    @classmethod
    def normalize_angle(cls, angle):
        # Normalize to [0, 2π)
        while angle < 0:
            angle += 2 * math.pi
        while angle >= 2 * math.pi:
            angle -= 2 * math.pi
        return angle