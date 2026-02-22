"""Decorator for validating request parameters"""

from typing import Dict, Any, Callable
from functools import wraps

from .validation_error import ValidationError
from .enums import ErrorCode
from .required_field_validator import RequiredFieldValidator


def validate_request(validation_schema: Dict[str, Any]) -> Callable:
    """
    Decorator for validating request parameters.

    Args:
        validation_schema: Dictionary defining validation rules

    Example:
        @validate_request({
            "room_polygon": {
                "validators": [NonEmptyValidator(), ArrayShapeValidator(2)],
                "nested": None
            },
            "windows": {
                "validators": [NonEmptyValidator()],
                "nested": {
                    "*": {  # Apply to all window entries
                        "x1": [TypeValidator(float), RangeValidator(min_value=0)],
                        "y1": [TypeValidator(float), RangeValidator(min_value=0)]
                    }
                }
            }
        })
        def my_endpoint(data):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get the data parameter (assume first arg after self)
            if args and len(args) > 1:
                data = args[1] if isinstance(args[0], object) else args[0]
            else:
                data = kwargs.get('data')

            if data:
                try:
                    _validate_dict(data, validation_schema, "")
                except ValidationError:
                    raise  # Re-raise to be caught by endpoint handler

            return func(*args, **kwargs)
        return wrapper
    return decorator


def _validate_dict(data: Dict[str, Any], schema: Dict[str, Any], path: str) -> None:
    """
    Recursively validate dictionary against schema.

    Args:
        data: Data to validate
        schema: Validation schema
        path: Current field path
    """
    for field, rules in schema.items():
        field_path = f"{path}.{field}" if path else field

        # Check if field exists
        if field not in data:
            if "validators" in rules:
                for validator in rules.get("validators", []):
                    if isinstance(validator, RequiredFieldValidator):
                        raise ValidationError(
                            message=f"Missing required field: {field}",
                            error_code=ErrorCode.MISSING_FIELD,
                            field=field_path
                        )
            continue

        value = data[field]

        # Apply validators
        if "validators" in rules:
            for validator in rules["validators"]:
                validator.validate(value, field_path)

        # Handle nested validation
        if "nested" in rules and rules["nested"]:
            nested_schema = rules["nested"]

            # Handle wildcard for dict entries
            if "*" in nested_schema and isinstance(value, dict):
                wildcard_schema = nested_schema["*"]
                for key, nested_value in value.items():
                    nested_path = f"{field_path}.{key}"
                    if isinstance(wildcard_schema, dict):
                        _validate_dict({k: nested_value.get(k) for k in wildcard_schema},
                                     {k: {"validators": v} if isinstance(v, list) else v
                                      for k, v in wildcard_schema.items()},
                                     nested_path)
            elif isinstance(value, dict):
                _validate_dict(value, nested_schema, field_path)
