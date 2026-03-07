"""Tests for RangeValidator"""

import pytest
import numpy as np
from src.server.services.validation.range_validator import RangeValidator
from src.server.services.validation.validation_error import ValidationError
from src.server.services.validation.enums import ErrorCode


class TestRangeValidator:
    """Test RangeValidator class"""

    def test_validate_within_range(self):
        """Test validation passes for value within range"""
        validator = RangeValidator(min_value=0, max_value=100)
        # Should not raise
        validator.validate(50, "field")

    def test_validate_at_min_boundary(self):
        """Test validation passes at minimum boundary"""
        validator = RangeValidator(min_value=0, max_value=100)
        # Should not raise
        validator.validate(0, "field")

    def test_validate_at_max_boundary(self):
        """Test validation passes at maximum boundary"""
        validator = RangeValidator(min_value=0, max_value=100)
        # Should not raise
        validator.validate(100, "field")

    def test_validate_below_min(self):
        """Test validation fails for value below minimum"""
        validator = RangeValidator(min_value=0, max_value=100)
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(-1, "field")
        
        error = exc_info.value
        assert error.error_code == ErrorCode.INVALID_RANGE
        assert ">=" in error.message

    def test_validate_above_max(self):
        """Test validation fails for value above maximum"""
        validator = RangeValidator(min_value=0, max_value=100)
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(101, "field")
        
        error = exc_info.value
        assert error.error_code == ErrorCode.INVALID_RANGE
        assert "<=" in error.message

    def test_validate_only_min_set(self):
        """Test validation with only minimum set"""
        validator = RangeValidator(min_value=0)
        # Should pass
        validator.validate(1000, "field")
        # Should fail
        with pytest.raises(ValidationError):
            validator.validate(-1, "field")

    def test_validate_only_max_set(self):
        """Test validation with only maximum set"""
        validator = RangeValidator(max_value=100)
        # Should pass
        validator.validate(-1000, "field")
        # Should fail
        with pytest.raises(ValidationError):
            validator.validate(101, "field")

    def test_validate_no_range(self):
        """Test validation with no range (any number passes)"""
        validator = RangeValidator()
        # Should pass
        validator.validate(-1000, "field")
        validator.validate(1000, "field")
        validator.validate(0, "field")

    def test_validate_float_values(self):
        """Test validation with float values"""
        validator = RangeValidator(min_value=0.0, max_value=1.0)
        # Should pass
        validator.validate(0.5, "field")
        # Should fail
        with pytest.raises(ValidationError):
            validator.validate(1.5, "field")

    def test_validate_string_numeric(self):
        """Test validation converts string to number"""
        validator = RangeValidator(min_value=0, max_value=100)
        # Should pass
        validator.validate("50", "field")

    def test_validate_non_numeric_string(self):
        """Test validation fails for non-numeric string"""
        validator = RangeValidator(min_value=0, max_value=100)
        with pytest.raises(ValidationError) as exc_info:
            validator.validate("not a number", "field")
        
        error = exc_info.value
        assert error.error_code == ErrorCode.INVALID_TYPE

    def test_validate_numpy_int(self):
        """Test validation with numpy int"""
        validator = RangeValidator(min_value=0, max_value=100)
        # Should pass
        validator.validate(np.int32(50), "field")
        # Should fail
        with pytest.raises(ValidationError):
            validator.validate(np.int32(150), "field")

    def test_validate_numpy_float(self):
        """Test validation with numpy float"""
        validator = RangeValidator(min_value=0.0, max_value=100.0)
        # Should pass
        validator.validate(np.float32(50.5), "field")
        # Should fail
        with pytest.raises(ValidationError):
            validator.validate(np.float32(150.5), "field")

    def test_validate_none_value(self):
        """Test validation fails for None"""
        validator = RangeValidator(min_value=0, max_value=100)
        with pytest.raises(ValidationError):
            validator.validate(None, "field")

    def test_validate_list_value(self):
        """Test validation fails for list"""
        validator = RangeValidator(min_value=0, max_value=100)
        with pytest.raises(ValidationError):
            validator.validate([1, 2, 3], "field")

    def test_field_path_in_error(self):
        """Test field path is included in error"""
        validator = RangeValidator(min_value=0, max_value=100)
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(150, "room.width")
        
        error = exc_info.value
        assert error.field == "room.width"

    def test_value_stored_in_error(self):
        """Test invalid value is stored in error"""
        validator = RangeValidator(min_value=0, max_value=100)
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(150, "field")
        
        error = exc_info.value
        assert error.value == 150

    def test_context_includes_bounds(self):
        """Test error context includes min/max bounds"""
        validator = RangeValidator(min_value=0, max_value=100)
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(150, "field")
        
        error = exc_info.value
        assert error.context["min"] == 0
        assert error.context["max"] == 100

    def test_negative_range(self):
        """Test validation with negative range"""
        validator = RangeValidator(min_value=-100, max_value=-10)
        # Should pass
        validator.validate(-50, "field")
        # Should fail
        with pytest.raises(ValidationError):
            validator.validate(0, "field")

    def test_zero_range(self):
        """Test validation with zero range (min == max)"""
        validator = RangeValidator(min_value=42, max_value=42)
        # Should pass
        validator.validate(42, "field")
        # Should fail
        with pytest.raises(ValidationError):
            validator.validate(41, "field")
        with pytest.raises(ValidationError):
            validator.validate(43, "field")
