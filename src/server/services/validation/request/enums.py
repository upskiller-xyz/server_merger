"""Enums for request validation"""

from enum import Enum


class WindowField(Enum):
    """Required fields for window geometry"""
    X1 = "x1"
    Y1 = "y1"
    Z1 = "z1"
    X2 = "x2"
    Y2 = "y2"
    Z2 = "z2"
    DIRECTION_ANGLE = "direction_angle"


class SimulationField(Enum):
    """Required fields for simulation data"""
    DF_VALUES = "df_values"
    MASK = "mask"


class RequestField(Enum):
    """Top-level required fields for DF aggregation request"""
    ROOM_POLYGON = "room_polygon"
    WINDOWS = "windows"
    SIMULATION = "simulation"


class ResponseField(Enum):
    """Response fields for DF aggregation"""
    RESULT = "result"
    MASK = "mask"
    ERROR = "error"
    ERROR_CODE = "error_code"
    FIELD = "field"
