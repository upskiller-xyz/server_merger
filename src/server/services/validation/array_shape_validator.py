"""Validator for array dimensions"""

from typing import Any, Optional, List
import numpy as np

from .base_validator import Validator
from .validation_error import ValidationError
from .enums import ErrorCode


class ArrayShapeValidator(Validator):
    """Validates array dimensions"""

    def __init__(self, expected_ndim: int, valid_shapes: Optional[List[tuple]] = None):
        self.expected_ndim = expected_ndim
        self.valid_shapes = valid_shapes

    def validate(self, value: Any, field_path: str) -> None:
        """Check array has correct dimensions"""
        if not isinstance(value, (list, np.ndarray)):
            raise ValidationError(
                message=f"Field '{field_path}' must be an array, got {type(value).__name__}",
                error_code=ErrorCode.INVALID_TYPE,
                field=field_path
            )

        arr = np.array(value) if isinstance(value, list) else value

        if arr.ndim != self.expected_ndim:
            raise ValidationError(
                message=f"Field '{field_path}' must be {self.expected_ndim}D array, got {arr.ndim}D",
                error_code=ErrorCode.INVALID_DIMENSIONS,
                field=field_path,
                context={"shape": arr.shape, "expected_ndim": self.expected_ndim}
            )

        if self.valid_shapes and arr.shape not in self.valid_shapes:
            valid_shapes_str = ", ".join(str(s) for s in self.valid_shapes)
            raise ValidationError(
                message=f"Field '{field_path}' has invalid shape {arr.shape}, expected one of: {valid_shapes_str}",
                error_code=ErrorCode.INVALID_DIMENSIONS,
                field=field_path,
                context={"shape": arr.shape, "valid_shapes": self.valid_shapes}
            )
