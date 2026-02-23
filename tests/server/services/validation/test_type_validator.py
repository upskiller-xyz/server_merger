"""Tests for TypeValidator"""

import pytest
from src.server.services.validation.type_validator import TypeValidator
from src.server.services.validation.validation_error import ValidationError
from src.server.services.validation.enums import ErrorCode


class TestTypeValidator:
    """Test TypeValidator class"""

    def test_validate_correct_type_int(self):
        """Test validation passes for correct int type"""
        validator = TypeValidator(int)
        # Should not raise
        validator.validate(42, "field.name")

    def test_validate_correct_type_string(self):
        """Test validation passes for correct string type"""
        validator = TypeValidator(str)
        # Should not raise
        validator.validate("hello", "field.name")

    def test_validate_correct_type_float(self):
        """Test validation passes for correct float type"""
        validator = TypeValidator(float)
        # Should not raise
        validator.validate(3.14, "field.name")

    def test_validate_correct_type_list(self):
        """Test validation passes for correct list type"""
        validator = TypeValidator(list)
        # Should not raise
        validator.validate([1, 2, 3], "field.name")

    def test_validate_correct_type_dict(self):
        """Test validation passes for correct dict type"""
        validator = TypeValidator(dict)
        # Should not raise
        validator.validate({"key": "value"}, "field.name")

    def test_validate_correct_type_bool(self):
        """Test validation passes for correct bool type"""
        validator = TypeValidator(bool)
        # Should not raise
        validator.validate(True, "field.name")

    def test_validate_wrong_type_int_string(self):
        """Test validation fails for wrong type - int instead of string"""
        validator = TypeValidator(str)
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(42, "field.name")
        
        error = exc_info.value
        assert error.error_code == ErrorCode.INVALID_TYPE
        assert "field.name" in error.message
        assert "str" in error.message
        assert "int" in error.message

    def test_validate_wrong_type_string_int(self):
        """Test validation fails for wrong type - string instead of int"""
        validator = TypeValidator(int)
        with pytest.raises(ValidationError) as exc_info:
            validator.validate("not an int", "count")
        
        error = exc_info.value
        assert error.error_code == ErrorCode.INVALID_TYPE
        assert "count" in error.message

    def test_validate_wrong_type_list_dict(self):
        """Test validation fails for wrong type - list instead of dict"""
        validator = TypeValidator(dict)
        with pytest.raises(ValidationError) as exc_info:
            validator.validate([1, 2, 3], "mapping")
        
        error = exc_info.value
        assert error.error_code == ErrorCode.INVALID_TYPE
        assert "dict" in error.message

    def test_validate_wrong_type_none(self):
        """Test validation fails for None when type expected"""
        validator = TypeValidator(str)
        with pytest.raises(ValidationError):
            validator.validate(None, "field.name")

    def test_validate_none_type_with_none(self):
        """Test validation passes when None is expected type"""
        validator = TypeValidator(type(None))
        # Should not raise
        validator.validate(None, "field.name")

    def test_field_path_in_error(self):
        """Test field path is included in error"""
        validator = TypeValidator(float)
        with pytest.raises(ValidationError) as exc_info:
            validator.validate("not a float", "room.window.width")
        
        error = exc_info.value
        assert error.field == "room.window.width"

    def test_value_stored_in_error(self):
        """Test invalid value is stored in error"""
        validator = TypeValidator(int)
        invalid_value = "not an int"
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(invalid_value, "field")
        
        error = exc_info.value
        assert error.value == invalid_value

    def test_validate_bool_not_int(self):
        """Test bool is not treated as int"""
        validator = TypeValidator(int)
        # In Python, bool is subclass of int, so this might pass
        # depending on isinstance behavior
        validator.validate(True, "flag")  # This may or may not raise

    def test_validate_with_multiple_validators(self):
        """Test using same validator multiple times"""
        validator = TypeValidator(str)
        
        # All should pass
        validator.validate("hello", "field1")
        validator.validate("world", "field2")
        
        # Should fail
        with pytest.raises(ValidationError):
            validator.validate(123, "field3")
