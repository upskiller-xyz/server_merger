"""Validator for non-empty collections"""

from typing import Any

from .base_validator import Validator
from .validation_error import ValidationError
from .enums import ErrorCode


class NonEmptyValidator(Validator):
    """Validates that collections are not empty"""

    def validate(self, value: Any, field_path: str) -> None:
        """Check that value is not empty"""
        if not value:
            raise ValidationError(
                message=f"Field '{field_path}' cannot be empty",
                error_code=ErrorCode.EMPTY_DATA,
                field=field_path
            )
