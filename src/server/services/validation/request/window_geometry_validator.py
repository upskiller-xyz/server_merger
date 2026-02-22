"""Validator for window geometry parameters"""

from typing import Dict, Any
import numpy as np

from ..validation_error import ValidationError
from ..enums import ErrorCode
from ..base_validator import Validator
from .enums import WindowField


class WindowGeometryValidator(Validator):
    """Validates window geometry parameters"""

    def validate(self, value: Dict[str, Any], field_path: str) -> None:
        """
        Validate window geometry has all required fields and valid values.

        Args:
            value: Window geometry dictionary
            field_path: Path to this window in request
        """
        required_fields = [field.value for field in WindowField]

        # Check required fields
        for field in required_fields:
            if field not in value:
                raise ValidationError(
                    message=f"Window geometry missing required field: {field}",
                    error_code=ErrorCode.MISSING_FIELD,
                    field=f"{field_path}.{field}"
                )

            # Validate numeric type
            if not isinstance(value[field], (int, float, np.integer, np.floating)):
                raise ValidationError(
                    message=f"Window parameter '{field}' must be numeric, got {type(value[field]).__name__}",
                    error_code=ErrorCode.INVALID_TYPE,
                    field=f"{field_path}.{field}",
                    value=value[field]
                )

        # Validate z1 < z2 (height constraint)
        z1_field = WindowField.Z1.value
        z2_field = WindowField.Z2.value

        if value[z1_field] >= value[z2_field]:
            raise ValidationError(
                message=f"Window {z1_field} ({value[z1_field]}) must be less than {z2_field} ({value[z2_field]})",
                error_code=ErrorCode.INVALID_VALUE,
                field=f"{field_path}.{z1_field}",
                context={z1_field: value[z1_field], z2_field: value[z2_field]}
            )
