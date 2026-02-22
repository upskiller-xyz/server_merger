"""Validator for field types"""

from typing import Any

from .base_validator import Validator
from .validation_error import ValidationError
from .enums import ErrorCode


class TypeValidator(Validator):
    """Validates field types"""

    def __init__(self, expected_type: type):
        self.expected_type = expected_type

    def validate(self, value: Any, field_path: str) -> None:
        """Check that value has expected type"""
        if not isinstance(value, self.expected_type):
            raise ValidationError(
                message=f"Field '{field_path}' must be {self.expected_type.__name__}, got {type(value).__name__}",
                error_code=ErrorCode.INVALID_TYPE,
                field=field_path,
                value=value
            )
