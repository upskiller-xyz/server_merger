from typing import List, Tuple, Any, Union, Dict, Callable
from dataclasses import dataclass
from abc import ABC, abstractmethod
import math
import numpy as np
import cv2
from shapely.geometry import Polygon as ShapelyPolygon, Point as ShapelyPoint, LineString as ShapelyLine, box as ShapelyBox
from shapely.affinity import rotate as shapely_rotate
from src.components.enums import ImageDimensions
from src.components.graphics_constants import GRAPHICS_CONSTANTS
from src.components.geometry_ops import Point2D, Point3D, GeometryOps
from src.components.window import WindowGeometry
