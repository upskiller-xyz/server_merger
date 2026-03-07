"""Tests for NonEmptyValidator and RequiredFieldValidator"""

import pytest
from src.server.services.validation.non_empty_validator import NonEmptyValidator
from src.server.services.validation.required_field_validator import RequiredFieldValidator
from src.server.services.validation.validation_error import ValidationError
from src.server.services.validation.enums import ErrorCode


class TestNonEmptyValidator:
    """Test NonEmptyValidator class"""

    def test_validate_non_empty_list(self):
        """Test validation passes for non-empty list"""
        validator = NonEmptyValidator()
        # Should not raise
        validator.validate([1, 2, 3], "field")

    def test_validate_non_empty_dict(self):
        """Test validation passes for non-empty dict"""
        validator = NonEmptyValidator()
        # Should not raise
        validator.validate({"key": "value"}, "field")

    def test_validate_non_empty_string(self):
        """Test validation passes for non-empty string"""
        validator = NonEmptyValidator()
        # Should not raise
        validator.validate("hello", "field")

    def test_validate_empty_list(self):
        """Test validation fails for empty list"""
        validator = NonEmptyValidator()
        with pytest.raises(ValidationError) as exc_info:
            validator.validate([], "field")
        
        error = exc_info.value
        assert error.error_code == ErrorCode.EMPTY_DATA

    def test_validate_empty_dict(self):
        """Test validation fails for empty dict"""
        validator = NonEmptyValidator()
        with pytest.raises(ValidationError):
            validator.validate({}, "field")

    def test_validate_empty_string(self):
        """Test validation fails for empty string"""
        validator = NonEmptyValidator()
        with pytest.raises(ValidationError):
            validator.validate("", "field")

    def test_validate_zero_falsy(self):
        """Test validation fails for zero (falsy)"""
        validator = NonEmptyValidator()
        with pytest.raises(ValidationError):
            validator.validate(0, "count")

    def test_validate_false_falsy(self):
        """Test validation fails for False (falsy)"""
        validator = NonEmptyValidator()
        with pytest.raises(ValidationError):
            validator.validate(False, "flag")

    def test_validate_none_falsy(self):
        """Test validation fails for None (falsy)"""
        validator = NonEmptyValidator()
        with pytest.raises(ValidationError):
            validator.validate(None, "field")

    def test_field_path_in_error(self):
        """Test field path is in error"""
        validator = NonEmptyValidator()
        with pytest.raises(ValidationError) as exc_info:
            validator.validate([], "windows")
        
        error = exc_info.value
        assert "windows" in error.message


class TestRequiredFieldValidator:
    """Test RequiredFieldValidator class"""

    def test_validate_all_fields_present(self):
        """Test validation passes when all fields present"""
        validator = RequiredFieldValidator(["x", "y", "z"])
        data = {"x": 1, "y": 2, "z": 3}
        # Should not raise
        validator.validate(data, "point")

    def test_validate_extra_fields_allowed(self):
        """Test validation passes with extra fields"""
        validator = RequiredFieldValidator(["x", "y"])
        data = {"x": 1, "y": 2, "z": 3, "extra": "field"}
        # Should not raise
        validator.validate(data, "point")

    def test_validate_missing_one_field(self):
        """Test validation fails when one field missing"""
        validator = RequiredFieldValidator(["x", "y", "z"])
        data = {"x": 1, "z": 3}  # Missing y
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(data, "point")
        
        error = exc_info.value
        assert error.error_code == ErrorCode.MISSING_FIELD
        assert "y" in error.message

    def test_validate_missing_multiple_fields(self):
        """Test validation fails for first missing field"""
        validator = RequiredFieldValidator(["x", "y", "z"])
        data = {"x": 1}  # Missing y and z
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(data, "point")
        
        error = exc_info.value
        assert error.error_code == ErrorCode.MISSING_FIELD

    def test_validate_empty_required_fields(self):
        """Test validation passes with empty required fields list"""
        validator = RequiredFieldValidator([])
        data = {"any": "data"}
        # Should not raise
        validator.validate(data, "data")

    def test_validate_empty_data(self):
        """Test validation fails for empty data when fields required"""
        validator = RequiredFieldValidator(["x"])
        with pytest.raises(ValidationError):
            validator.validate({}, "point")

    def test_field_path_construction(self):
        """Test field path is correctly constructed"""
        validator = RequiredFieldValidator(["name"])
        with pytest.raises(ValidationError) as exc_info:
            validator.validate({}, "window.properties")
        
        error = exc_info.value
        assert "window.properties.name" in error.field

    def test_field_path_without_prefix(self):
        """Test field path without prefix"""
        validator = RequiredFieldValidator(["name"])
        with pytest.raises(ValidationError) as exc_info:
            validator.validate({}, "")
        
        error = exc_info.value
        assert error.field == "name"

    def test_validate_field_with_none_value(self):
        """Test field with None value is considered present"""
        validator = RequiredFieldValidator(["x", "y", "z"])
        data = {"x": 1, "y": None, "z": 3}
        # Should not raise - field exists even if value is None
        validator.validate(data, "point")

    def test_validate_field_with_false_value(self):
        """Test field with False value is considered present"""
        validator = RequiredFieldValidator(["enabled", "name"])
        data = {"enabled": False, "name": ""}
        # Should not raise - fields exist even if values are falsy
        validator.validate(data, "config")

    def test_validate_numeric_fields(self):
        """Test validation with numeric field names"""
        validator = RequiredFieldValidator(["0", "1", "2"])
        data = {"0": "a", "1": "b", "2": "c"}
        # Should not raise
        validator.validate(data, "array")

    def test_validate_special_character_fields(self):
        """Test validation with special character field names"""
        validator = RequiredFieldValidator(["x1", "y2", "z_3"])
        data = {"x1": 1, "y2": 2, "z_3": 3}
        # Should not raise
        validator.validate(data, "fields")

    def test_error_message_includes_field_name(self):
        """Test error message includes missing field name"""
        validator = RequiredFieldValidator(["required_field"])
        with pytest.raises(ValidationError) as exc_info:
            validator.validate({}, "")
        
        error = exc_info.value
        assert "required_field" in error.message
