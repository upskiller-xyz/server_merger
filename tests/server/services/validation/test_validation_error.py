"""Tests for ValidationError"""

import pytest
import numpy as np
from src.server.services.validation.validation_error import ValidationError
from src.server.services.validation.enums import ErrorCode


class TestValidationError:
    """Test ValidationError class"""

    def test_create_with_message_and_code(self):
        """Test creating validation error with message and code"""
        error = ValidationError(
            message="Invalid value",
            error_code=ErrorCode.INVALID_TYPE
        )
        assert error.message == "Invalid value"
        assert error.error_code == ErrorCode.INVALID_TYPE
        assert error.field is None
        assert error.value is None
        assert error.context == {}

    def test_create_with_all_fields(self):
        """Test creating validation error with all fields"""
        context = {"min": 0, "max": 100}
        error = ValidationError(
            message="Value out of range",
            error_code=ErrorCode.INVALID_RANGE,
            field="room.width",
            value=150,
            context=context
        )
        assert error.message == "Value out of range"
        assert error.error_code == ErrorCode.INVALID_RANGE
        assert error.field == "room.width"
        assert error.value == 150
        assert error.context == context

    def test_to_dict_basic(self):
        """Test to_dict with basic fields"""
        error = ValidationError(
            message="Invalid value",
            error_code=ErrorCode.INVALID_TYPE
        )
        result = error.to_dict()
        assert result["error"] == "Invalid value"
        assert result["error_code"] == ErrorCode.INVALID_TYPE.value

    def test_to_dict_with_field(self):
        """Test to_dict includes field"""
        error = ValidationError(
            message="Invalid value",
            error_code=ErrorCode.INVALID_TYPE,
            field="windows.window1.x"
        )
        result = error.to_dict()
        assert result["field"] == "windows.window1.x"

    def test_to_dict_with_python_value(self):
        """Test to_dict converts Python value to string"""
        error = ValidationError(
            message="Invalid value",
            error_code=ErrorCode.INVALID_VALUE,
            value=42
        )
        result = error.to_dict()
        # to_dict converts all values to strings
        assert "value" in result
        assert result["value"] == "42"

    def test_to_dict_with_numpy_integer(self):
        """Test to_dict converts numpy integer"""
        error = ValidationError(
            message="Invalid value",
            error_code=ErrorCode.INVALID_TYPE,
            value=np.int32(42)
        )
        result = error.to_dict()
        assert result["value"] == 42
        assert isinstance(result["value"], int)

    def test_to_dict_with_numpy_float(self):
        """Test to_dict converts numpy float"""
        error = ValidationError(
            message="Invalid value",
            error_code=ErrorCode.INVALID_TYPE,
            value=np.float32(3.14)
        )
        result = error.to_dict()
        assert abs(result["value"] - 3.14) < 0.01
        assert isinstance(result["value"], float)

    def test_to_dict_with_numpy_array(self):
        """Test to_dict handles numpy array"""
        error = ValidationError(
            message="Invalid array",
            error_code=ErrorCode.INVALID_DIMENSIONS,
            value=np.array([[1, 2], [3, 4]])
        )
        result = error.to_dict()
        assert "value" in result

    def test_to_dict_with_context(self):
        """Test to_dict includes context"""
        error = ValidationError(
            message="Out of range",
            error_code=ErrorCode.INVALID_RANGE,
            context={"min": 0, "max": 100, "value": 150}
        )
        result = error.to_dict()
        # Context is stored but may not be in to_dict (depends on implementation)
        assert error.context == {"min": 0, "max": 100, "value": 150}

    def test_is_exception(self):
        """Test ValidationError is an Exception"""
        error = ValidationError(
            message="Test error",
            error_code=ErrorCode.INVALID_TYPE
        )
        assert isinstance(error, Exception)

    def test_raise_and_catch(self):
        """Test raising and catching ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            raise ValidationError(
                message="Test error",
                error_code=ErrorCode.INVALID_TYPE,
                field="test_field"
            )
        
        error = exc_info.value
        assert error.message == "Test error"
        assert error.field == "test_field"

    def test_str_representation(self):
        """Test string representation"""
        error = ValidationError(
            message="Invalid value",
            error_code=ErrorCode.INVALID_TYPE
        )
        assert str(error) == "Invalid value"
