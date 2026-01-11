"""
Validation utilities for request handling.

This module provides decorators and classes for validating request parameters
and providing clear, actionable error messages to users.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable
from functools import wraps
from enum import Enum
import numpy as np


class ErrorCode(Enum):
    """Error codes for different validation failures"""
    MISSING_FIELD = "missing_field"
    INVALID_TYPE = "invalid_type"
    INVALID_VALUE = "invalid_value"
    INVALID_RANGE = "invalid_range"
    INVALID_DIMENSIONS = "invalid_dimensions"
    EMPTY_DATA = "empty_data"


class ValidationError(Exception):
    """
    Structured validation error with detailed information.

    Attributes:
        message: Human-readable error message
        error_code: Machine-readable error code
        field: Field path that caused the error (e.g., "windows.window1.x1")
        value: The invalid value (optional)
        context: Additional context information
    """

    def __init__(
        self,
        message: str,
        error_code: ErrorCode,
        field: Optional[str] = None,
        value: Any = None,
        context: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.field = field
        self.value = value
        self.context = context or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = {
            "error": self.message,
            "error_code": self.error_code.value
        }

        if self.field:
            result["field"] = self.field

        if self.value is not None:
            # Convert numpy types to Python types
            if isinstance(self.value, (np.integer, np.floating)):
                result["value"] = self.value.item()
            elif isinstance(self.value, np.ndarray):
                result["value"] = f"<array shape={self.value.shape}>"
            else:
                result["value"] = str(self.value)

        if self.context:
            result["context"] = self.context

        return result


class Validator(ABC):
    """Base class for validators"""

    @abstractmethod
    def validate(self, value: Any, field_path: str) -> None:
        """
        Validate a value.

        Args:
            value: Value to validate
            field_path: Dot-separated path to field (e.g., "windows.window1.x1")

        Raises:
            ValidationError: If validation fails
        """
        pass


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


class CompositeValidator(Validator):
    """Combines multiple validators"""

    def __init__(self, validators: List[Validator]):
        self.validators = validators

    def validate(self, value: Any, field_path: str) -> None:
        """Run all validators in sequence"""
        for validator in self.validators:
            validator.validate(value, field_path)


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


class RequestValidator:
    """
    Service for validating complete request payloads.

    Uses Strategy pattern for different validation strategies.
    """

    def __init__(self):
        self.validation_strategies: Dict[str, Callable] = {}

    def register_strategy(self, name: str, validator: Callable) -> None:
        """Register a validation strategy"""
        self.validation_strategies[name] = validator

    def validate(self, strategy_name: str, data: Any) -> None:
        """
        Validate data using named strategy.

        Args:
            strategy_name: Name of validation strategy to use
            data: Data to validate

        Raises:
            ValidationError: If validation fails
            KeyError: If strategy not found
        """
        if strategy_name not in self.validation_strategies:
            raise KeyError(f"Validation strategy '{strategy_name}' not found")

        self.validation_strategies[strategy_name](data)
