"""Tests for DF aggregation request validator"""

import pytest
import numpy as np
from src.server.services.validation.request.df_aggregation_request_validator import DFAggregationRequestValidator
from src.server.services.validation.validation_error import ValidationError
from src.server.services.validation.enums import ErrorCode


class TestDFAggregationRequestValidator:
    """Test DF aggregation request validation"""

    def setup_method(self):
        """Set up validator"""
        self.validator = DFAggregationRequestValidator()

    def test_missing_room_polygon(self):
        """Test error when room_polygon is missing"""
        data = {
            "windows": {"w1": self._valid_window()},
            "simulation": {"w1": self._valid_simulation()}
        }
        
        with pytest.raises(ValidationError) as exc_info:
            self.validator.validate(data)
        
        assert exc_info.value.error_code == ErrorCode.MISSING_FIELD
        assert "room_polygon" in exc_info.value.message

    def test_missing_windows(self):
        """Test error when windows field is missing"""
        data = {
            "room_polygon": self._valid_polygon(),
            "simulation": {"w1": self._valid_simulation()}
        }
        
        with pytest.raises(ValidationError) as exc_info:
            self.validator.validate(data)
        
        assert exc_info.value.error_code == ErrorCode.MISSING_FIELD

    def test_missing_simulation(self):
        """Test error when simulation field is missing"""
        data = {
            "room_polygon": self._valid_polygon(),
            "windows": {"w1": self._valid_window()}
        }
        
        with pytest.raises(ValidationError) as exc_info:
            self.validator.validate(data)
        
        assert exc_info.value.error_code == ErrorCode.MISSING_FIELD

    def test_empty_windows_dict(self):
        """Test error when windows dict is empty"""
        data = {
            "room_polygon": self._valid_polygon(),
            "windows": {},
            "simulation": {"w1": self._valid_simulation()}
        }
        
        with pytest.raises(ValidationError) as exc_info:
            self.validator.validate(data)
        
        assert exc_info.value.error_code == ErrorCode.EMPTY_DATA
        assert "windows" in exc_info.value.message.lower()

    def test_empty_simulation_dict(self):
        """Test error when simulation dict is empty"""
        data = {
            "room_polygon": self._valid_polygon(),
            "windows": {"w1": self._valid_window()},
            "simulation": {}
        }
        
        with pytest.raises(ValidationError) as exc_info:
            self.validator.validate(data)
        
        assert exc_info.value.error_code == ErrorCode.EMPTY_DATA
        assert "simulation" in exc_info.value.message.lower()

    def test_window_not_dict(self):
        """Test error when window is not a dict"""
        data = {
            "room_polygon": self._valid_polygon(),
            "windows": {"w1": "not_a_dict"},
            "simulation": {"w1": self._valid_simulation()}
        }
        
        with pytest.raises(ValidationError) as exc_info:
            self.validator.validate(data)
        
        assert exc_info.value.error_code == ErrorCode.INVALID_TYPE

    def test_simulation_not_dict(self):
        """Test error when simulation is not a dict"""
        data = {
            "room_polygon": self._valid_polygon(),
            "windows": {"w1": self._valid_window()},
            "simulation": {"w1": "not_a_dict"}
        }
        
        with pytest.raises(ValidationError) as exc_info:
            self.validator.validate(data)
        
        assert exc_info.value.error_code == ErrorCode.INVALID_TYPE

    def test_missing_simulation_for_window(self):
        """Test error when window has no corresponding simulation"""
        data = {
            "room_polygon": self._valid_polygon(),
            "windows": {"w1": self._valid_window(), "w2": self._valid_window()},
            "simulation": {"w1": self._valid_simulation()}
        }
        
        with pytest.raises(ValidationError) as exc_info:
            self.validator.validate(data)
        
        assert exc_info.value.error_code == ErrorCode.MISSING_FIELD
        assert "w2" in str(exc_info.value.message) or "w2" in str(exc_info.value.context)

    def test_missing_window_for_simulation(self):
        """Test error when simulation has no corresponding window"""
        data = {
            "room_polygon": self._valid_polygon(),
            "windows": {"w1": self._valid_window()},
            "simulation": {"w1": self._valid_simulation(), "w2": self._valid_simulation()}
        }
        
        with pytest.raises(ValidationError) as exc_info:
            self.validator.validate(data)
        
        assert exc_info.value.error_code == ErrorCode.MISSING_FIELD
        assert "w2" in str(exc_info.value.message) or "w2" in str(exc_info.value.context)

    def test_valid_single_window(self):
        """Test valid request with single window"""
        data = {
            "room_polygon": self._valid_polygon(),
            "windows": {"w1": self._valid_window()},
            "simulation": {"w1": self._valid_simulation()}
        }
        
        # Should not raise
        self.validator.validate(data)

    def test_valid_multiple_windows(self):
        """Test valid request with multiple windows"""
        data = {
            "room_polygon": self._valid_polygon(),
            "windows": {
                "w1": self._valid_window(),
                "w2": self._valid_window(),
                "w3": self._valid_window()
            },
            "simulation": {
                "w1": self._valid_simulation(),
                "w2": self._valid_simulation(),
                "w3": self._valid_simulation()
            }
        }
        
        # Should not raise
        self.validator.validate(data)

    def test_invalid_room_polygon(self):
        """Test error when room polygon is invalid"""
        data = {
            "room_polygon": [[0, 0], [1, 1]],  # Too few vertices
            "windows": {"w1": self._valid_window()},
            "simulation": {"w1": self._valid_simulation()}
        }
        
        with pytest.raises(ValidationError) as exc_info:
            self.validator.validate(data)
        
        assert exc_info.value.error_code == ErrorCode.INVALID_VALUE

    def test_invalid_window_geometry(self):
        """Test error when window geometry is invalid"""
        data = {
            "room_polygon": self._valid_polygon(),
            "windows": {"w1": {
                "x1": 0.0, "y1": 0.0, "z1": 2.0,
                "x2": 1.0, "y2": 1.0, "z2": 1.0,  # z1 > z2
                "direction_angle": 0.0
            }},
            "simulation": {"w1": self._valid_simulation()}
        }
        
        with pytest.raises(ValidationError) as exc_info:
            self.validator.validate(data)
        
        assert exc_info.value.error_code == ErrorCode.INVALID_VALUE

    def test_invalid_simulation_data(self):
        """Test error when simulation data is invalid"""
        data = {
            "room_polygon": self._valid_polygon(),
            "windows": {"w1": self._valid_window()},
            "simulation": {"w1": {"df_values": np.zeros((128, 128))}}  # Missing mask
        }
        
        with pytest.raises(ValidationError) as exc_info:
            self.validator.validate(data)
        
        assert exc_info.value.error_code == ErrorCode.MISSING_FIELD

    def test_multiple_windows_missing_simulation(self):
        """Test error message with multiple missing simulations"""
        data = {
            "room_polygon": self._valid_polygon(),
            "windows": {
                "w1": self._valid_window(),
                "w2": self._valid_window(),
                "w3": self._valid_window()
            },
            "simulation": {
                "w1": self._valid_simulation()
            }
        }
        
        with pytest.raises(ValidationError) as exc_info:
            self.validator.validate(data)
        
        # Should mention missing windows
        assert "w2" in str(exc_info.value.context) or "w3" in str(exc_info.value.context)

    def test_window_id_with_special_chars(self):
        """Test valid window IDs with special characters"""
        data = {
            "room_polygon": self._valid_polygon(),
            "windows": {
                "window-1": self._valid_window(),
                "window_2": self._valid_window(),
                "w.3": self._valid_window()
            },
            "simulation": {
                "window-1": self._valid_simulation(),
                "window_2": self._valid_simulation(),
                "w.3": self._valid_simulation()
            }
        }
        
        # Should not raise
        self.validator.validate(data)

    def test_extra_fields_ignored(self):
        """Test that extra fields don't cause errors"""
        data = {
            "room_polygon": self._valid_polygon(),
            "windows": {"w1": self._valid_window()},
            "simulation": {"w1": self._valid_simulation()},
            "extra_field": "ignored",
            "another_extra": {"nested": "data"}
        }
        
        # Should not raise - extra fields are ignored
        self.validator.validate(data)

    # Helper methods
    @staticmethod
    def _valid_polygon():
        """Return valid room polygon"""
        return [[0, 0], [10, 0], [10, 10], [0, 10]]

    @staticmethod
    def _valid_window():
        """Return valid window geometry"""
        return {
            "x1": 0.0, "y1": 0.0, "z1": 0.0,
            "x2": 1.0, "y2": 1.0, "z2": 2.0,
            "direction_angle": 0.0
        }

    @staticmethod
    def _valid_simulation():
        """Return valid simulation data"""
        return {
            "df_values": np.zeros((128, 128)),
            "mask": np.ones((128, 128))
        }
