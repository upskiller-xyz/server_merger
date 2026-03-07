"""Error codes for validation failures"""

from enum import Enum


class ErrorCode(Enum):
    """Error codes for different validation failures"""
    MISSING_FIELD = "missing_field"
    INVALID_TYPE = "invalid_type"
    INVALID_VALUE = "invalid_value"
    INVALID_RANGE = "invalid_range"
    INVALID_DIMENSIONS = "invalid_dimensions"
    EMPTY_DATA = "empty_data"
