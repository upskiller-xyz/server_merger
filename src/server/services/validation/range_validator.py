"""Validator for numeric ranges"""

from typing import Any, Optional

from .base_validator import Validator
from .validation_error import ValidationError
from .enums import ErrorCode


class RangeValidator(Validator):
    """Validates numeric values are within range"""

    def __init__(self, min_value: Optional[float] = None, max_value: Optional[float] = None):
        self.min_value = min_value
        self.max_value = max_value

    def validate(self, value: Any, field_path: str) -> None:
        """Check that value is within range"""
        try:
            num_value = float(value)
        except (TypeError, ValueError):
            raise ValidationError(
                message=f"Field '{field_path}' must be numeric, got {type(value).__name__}",
                error_code=ErrorCode.INVALID_TYPE,
                field=field_path,
                value=value
            )

        if self.min_value is not None and num_value < self.min_value:
            raise ValidationError(
                message=f"Field '{field_path}' must be >= {self.min_value}, got {num_value}",
                error_code=ErrorCode.INVALID_RANGE,
                field=field_path,
                value=value,
                context={"min": self.min_value, "max": self.max_value}
            )

        if self.max_value is not None and num_value > self.max_value:
            raise ValidationError(
                message=f"Field '{field_path}' must be <= {self.max_value}, got {num_value}",
                error_code=ErrorCode.INVALID_RANGE,
                field=field_path,
                value=value,
                context={"min": self.min_value, "max": self.max_value}
            )
