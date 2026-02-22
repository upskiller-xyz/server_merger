"""Validator for required fields"""

from typing import List, Dict, Any

from .base_validator import Validator
from .validation_error import ValidationError
from .enums import ErrorCode


class RequiredFieldValidator(Validator):
    """Validates that required fields are present"""

    def __init__(self, required_fields: List[str]):
        self.required_fields = required_fields

    def validate(self, value: Dict[str, Any], field_path: str = "") -> None:
        """Check that all required fields are present"""
        for field in self.required_fields:
            if field not in value:
                raise ValidationError(
                    message=f"Missing required field: {field}",
                    error_code=ErrorCode.MISSING_FIELD,
                    field=f"{field_path}.{field}" if field_path else field
                )
