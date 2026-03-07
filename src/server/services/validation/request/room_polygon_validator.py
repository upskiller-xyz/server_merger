"""Validator for room polygon structure"""

from typing import Any
import numpy as np

from ..validation_error import ValidationError
from ..enums import ErrorCode
from ..base_validator import Validator


class RoomPolygonValidator(Validator):
    """Validates room polygon structure"""

    def __init__(self, min_vertices: int = 3):
        self.min_vertices = min_vertices

    def validate(self, value: Any, field_path: str) -> None:
        """
        Validate room polygon is a valid 2D polygon.

        Args:
            value: Room polygon coordinates
            field_path: Path to polygon in request
        """
        if not isinstance(value, (list, np.ndarray)):
            raise ValidationError(
                message=f"Room polygon must be an array, got {type(value).__name__}",
                error_code=ErrorCode.INVALID_TYPE,
                field=field_path
            )

        polygon = np.array(value)

        # Check minimum vertices
        if len(polygon) < self.min_vertices:
            raise ValidationError(
                message=f"Room polygon must have at least {self.min_vertices} vertices, got {len(polygon)}",
                error_code=ErrorCode.INVALID_VALUE,
                field=field_path,
                context={"vertex_count": len(polygon), "min_vertices": self.min_vertices}
            )

        # Check each vertex is [x, y]
        for i, vertex in enumerate(polygon):
            try:
                vertex_arr = np.array(vertex)
            except (TypeError, ValueError) as e:
                raise ValidationError(
                    message=f"Room polygon vertex {i} is invalid: {e}",
                    error_code=ErrorCode.INVALID_VALUE,
                    field=f"{field_path}[{i}]",
                    value=str(vertex)
                )

            if not isinstance(vertex, (list, tuple, np.ndarray)) or len(vertex) != 2:
                raise ValidationError(
                    message=f"Room polygon vertex {i} must be [x, y] coordinate pair (2D), got {len(vertex)} dimensions",
                    error_code=ErrorCode.INVALID_VALUE,
                    field=f"{field_path}[{i}]",
                    value=str(vertex)
                )

            # Check both coordinates are numeric
            try:
                float(vertex[0])
                float(vertex[1])
            except (TypeError, ValueError):
                raise ValidationError(
                    message=f"Room polygon vertex {i} coordinates must be numeric, got {vertex}",
                    error_code=ErrorCode.INVALID_TYPE,
                    field=f"{field_path}[{i}]",
                    value=vertex
                )
