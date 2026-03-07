"""Tests for window geometry validator"""

import pytest
import numpy as np
from src.server.services.validation.request.window_geometry_validator import WindowGeometryValidator
from src.server.services.validation.validation_error import ValidationError
from src.server.services.validation.enums import ErrorCode


class TestWindowGeometryValidator:
    """Test window geometry validation"""

    def setup_method(self):
        """Set up validator"""
        self.validator = WindowGeometryValidator()

    def test_missing_x1_field(self):
        """Test error when x1 field is missing"""
        window = {
            "y1": 0.0, "z1": 0.0,
            "x2": 1.0, "y2": 1.0, "z2": 2.0,
            "direction_angle": 0.0
        }
        
        with pytest.raises(ValidationError) as exc_info:
            self.validator.validate(window, "windows[0]")
        
        assert exc_info.value.error_code == ErrorCode.MISSING_FIELD
        assert "x1" in exc_info.value.message

    def test_missing_all_fields(self):
        """Test error when multiple fields are missing"""
        window = {"x1": 0.0}
        
        with pytest.raises(ValidationError) as exc_info:
            self.validator.validate(window, "window")
        
        assert exc_info.value.error_code == ErrorCode.MISSING_FIELD

    def test_x1_not_numeric(self):
        """Test error when x1 is not numeric"""
        window = {
            "x1": "not_a_number",
            "y1": 0.0, "z1": 0.0,
            "x2": 1.0, "y2": 1.0, "z2": 2.0,
            "direction_angle": 0.0
        }
        
        with pytest.raises(ValidationError) as exc_info:
            self.validator.validate(window, "window")
        
        assert exc_info.value.error_code == ErrorCode.INVALID_TYPE
        assert "numeric" in exc_info.value.message.lower()

    def test_all_string_values(self):
        """Test error when all values are strings"""
        window = {
            "x1": "0", "y1": "0", "z1": "0",
            "x2": "1", "y2": "1", "z2": "2",
            "direction_angle": "0"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            self.validator.validate(window, "window")
        
        assert exc_info.value.error_code == ErrorCode.INVALID_TYPE

    def test_z1_greater_than_z2(self):
        """Test error when z1 >= z2"""
        window = {
            "x1": 0.0, "y1": 0.0, "z1": 2.0,
            "x2": 1.0, "y2": 1.0, "z2": 1.0,
            "direction_angle": 0.0
        }
        
        with pytest.raises(ValidationError) as exc_info:
            self.validator.validate(window, "window")
        
        assert exc_info.value.error_code == ErrorCode.INVALID_VALUE
        assert "z1" in exc_info.value.message.lower()
        assert "z2" in exc_info.value.message.lower()

    def test_z1_equal_z2(self):
        """Test error when z1 equals z2"""
        window = {
            "x1": 0.0, "y1": 0.0, "z1": 1.5,
            "x2": 1.0, "y2": 1.0, "z2": 1.5,
            "direction_angle": 0.0
        }
        
        with pytest.raises(ValidationError) as exc_info:
            self.validator.validate(window, "window")
        
        assert exc_info.value.error_code == ErrorCode.INVALID_VALUE

    def test_valid_window_integers(self):
        """Test valid window with integer parameters"""
        window = {
            "x1": 0, "y1": 0, "z1": 0,
            "x2": 1, "y2": 1, "z2": 2,
            "direction_angle": 0
        }
        
        # Should not raise
        self.validator.validate(window, "window")

    def test_valid_window_floats(self):
        """Test valid window with float parameters"""
        window = {
            "x1": 0.5, "y1": 0.5, "z1": 1.0,
            "x2": 1.5, "y2": 2.5, "z2": 2.5,
            "direction_angle": 45.5
        }
        
        # Should not raise
        self.validator.validate(window, "window")

    def test_valid_window_mixed_types(self):
        """Test valid window with mixed int/float"""
        window = {
            "x1": 0, "y1": 0.5, "z1": 1,
            "x2": 1.0, "y2": 2, "z2": 3.5,
            "direction_angle": 90
        }
        
        # Should not raise
        self.validator.validate(window, "window")

    def test_valid_window_negative_coords(self):
        """Test valid window with negative coordinates"""
        window = {
            "x1": -1.0, "y1": -1.0, "z1": -1.0,
            "x2": -0.5, "y2": -0.5, "z2": 0.5,
            "direction_angle": 180.0
        }
        
        # Should not raise
        self.validator.validate(window, "window")

    def test_valid_window_numpy_types(self):
        """Test valid window with numpy numeric types"""
        window = {
            "x1": np.float32(0.0),
            "y1": np.float64(0.0),
            "z1": np.int32(0),
            "x2": np.float32(1.0),
            "y2": np.float64(1.0),
            "z2": np.int32(2),
            "direction_angle": np.float32(45.0)
        }
        
        # Should not raise
        self.validator.validate(window, "window")

    def test_valid_window_z1_much_less_than_z2(self):
        """Test valid window with large z difference"""
        window = {
            "x1": 0.0, "y1": 0.0, "z1": -100.0,
            "x2": 1.0, "y2": 1.0, "z2": 100.0,
            "direction_angle": 0.0
        }
        
        # Should not raise
        self.validator.validate(window, "window")

    def test_field_path_in_error(self):
        """Test that field path is included in error"""
        window = {
            "x1": "invalid",
            "y1": 0.0, "z1": 0.0,
            "x2": 1.0, "y2": 1.0, "z2": 2.0,
            "direction_angle": 0.0
        }
        
        with pytest.raises(ValidationError) as exc_info:
            self.validator.validate(window, "request.windows['w1']")
        
        assert "request.windows['w1'].x1" in exc_info.value.field

    def test_z_constraint_context(self):
        """Test that z values are in error context"""
        window = {
            "x1": 0.0, "y1": 0.0, "z1": 5.0,
            "x2": 1.0, "y2": 1.0, "z2": 3.0,
            "direction_angle": 0.0
        }
        
        with pytest.raises(ValidationError) as exc_info:
            self.validator.validate(window, "window")
        
        assert exc_info.value.context["z1"] == 5.0
        assert exc_info.value.context["z2"] == 3.0

    def test_z1_negative_z2_positive(self):
        """Test valid window crossing z=0"""
        window = {
            "x1": 0.0, "y1": 0.0, "z1": -1.5,
            "x2": 1.0, "y2": 1.0, "z2": 1.5,
            "direction_angle": 270.0
        }
        
        # Should not raise
        self.validator.validate(window, "window")

    def test_all_zero_coordinates_valid(self):
        """Test valid window with zeros (only z constraint matters)"""
        window = {
            "x1": 0.0, "y1": 0.0, "z1": 0.0,
            "x2": 0.0, "y2": 0.0, "z2": 1.0,
            "direction_angle": 0.0
        }
        
        # Should not raise
        self.validator.validate(window, "window")

    def test_very_small_z_difference(self):
        """Test valid window with very small z difference"""
        window = {
            "x1": 0.0, "y1": 0.0, "z1": 0.0,
            "x2": 1.0, "y2": 1.0, "z2": 0.0001,
            "direction_angle": 0.0
        }
        
        # Should not raise
        self.validator.validate(window, "window")

    def test_direction_angle_360(self):
        """Test valid window with large direction angle"""
        window = {
            "x1": 0.0, "y1": 0.0, "z1": 0.0,
            "x2": 1.0, "y2": 1.0, "z2": 2.0,
            "direction_angle": 360.0
        }
        
        # Should not raise
        self.validator.validate(window, "window")

    def test_numeric_string_not_accepted(self):
        """Test that numeric strings are not accepted"""
        window = {
            "x1": 0.0, "y1": 0.0, "z1": 0.0,
            "x2": 1.0, "y2": 1.0, "z2": "2.0",  # String number
            "direction_angle": 0.0
        }
        
        with pytest.raises(ValidationError) as exc_info:
            self.validator.validate(window, "window")
        
        assert exc_info.value.error_code == ErrorCode.INVALID_TYPE
