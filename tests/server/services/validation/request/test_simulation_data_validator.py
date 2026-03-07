"""Tests for simulation data validator"""

import pytest
import numpy as np
from src.server.services.validation.request.simulation_data_validator import SimulationDataValidator
from src.server.services.validation.validation_error import ValidationError
from src.server.services.validation.enums import ErrorCode


class TestSimulationDataValidator:
    """Test simulation data validation"""

    def setup_method(self):
        """Set up validator"""
        self.validator = SimulationDataValidator()

    def test_missing_df_values_field(self):
        """Test error when df_values field is missing"""
        data = {"mask": [[1, 0], [0, 1]]}
        
        with pytest.raises(ValidationError) as exc_info:
            self.validator.validate(data, "sim")
        
        assert exc_info.value.error_code == ErrorCode.MISSING_FIELD
        assert "df_values" in exc_info.value.message

    def test_missing_mask_field(self):
        """Test error when mask field is missing"""
        data = {"df_values": [[1, 0], [0, 1]]}
        
        with pytest.raises(ValidationError) as exc_info:
            self.validator.validate(data, "sim")
        
        assert exc_info.value.error_code == ErrorCode.MISSING_FIELD
        assert "mask" in exc_info.value.message

    def test_df_values_not_array(self):
        """Test error when df_values is not an array"""
        data = {
            "df_values": "not_an_array",
            "mask": [[1, 0], [0, 1]]
        }
        
        with pytest.raises(ValidationError) as exc_info:
            self.validator.validate(data, "sim")
        
        assert exc_info.value.error_code == ErrorCode.INVALID_TYPE
        assert "df_values" in exc_info.value.message

    def test_df_values_not_2d(self):
        """Test error when df_values is not 2D"""
        data = {
            "df_values": [1, 2, 3],  # 1D array
            "mask": [[1, 0], [0, 1]]
        }
        
        with pytest.raises(ValidationError) as exc_info:
            self.validator.validate(data, "sim")
        
        assert exc_info.value.error_code == ErrorCode.INVALID_DIMENSIONS
        assert "2D" in exc_info.value.message

    def test_df_values_not_square(self):
        """Test error when df_values is not square"""
        data = {
            "df_values": [[1, 2, 3], [4, 5, 6]],  # 2x3 not square
            "mask": [[1, 0], [0, 1]]
        }
        
        with pytest.raises(ValidationError) as exc_info:
            self.validator.validate(data, "sim")
        
        assert exc_info.value.error_code == ErrorCode.INVALID_DIMENSIONS
        assert "square" in exc_info.value.message.lower()

    def test_df_values_invalid_size(self):
        """Test error when df_values size is not valid"""
        data = {
            "df_values": [[1] * 256] * 256,  # 256x256, not in valid_sizes
            "mask": [[1, 0], [0, 1]]
        }
        
        with pytest.raises(ValidationError) as exc_info:
            self.validator.validate(data, "sim")
        
        assert exc_info.value.error_code == ErrorCode.INVALID_DIMENSIONS
        assert "128" in exc_info.value.message or "384" in exc_info.value.message

    def test_mask_not_array(self):
        """Test error when mask is not an array"""
        data = {
            "df_values": np.zeros((128, 128)),  # Use valid size
            "mask": "not_an_array"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            self.validator.validate(data, "sim")
        
        assert exc_info.value.error_code == ErrorCode.INVALID_TYPE
        assert "mask" in exc_info.value.message

    def test_mask_not_2d(self):
        """Test error when mask is not 2D"""
        data = {
            "df_values": np.zeros((128, 128)),  # Use valid size
            "mask": [1, 0, 0, 1]  # 1D array
        }
        
        with pytest.raises(ValidationError) as exc_info:
            self.validator.validate(data, "sim")
        
        assert exc_info.value.error_code == ErrorCode.INVALID_DIMENSIONS
        assert "2D" in exc_info.value.message

    def test_valid_128x128_simulation(self):
        """Test valid 128x128 simulation data"""
        data = {
            "df_values": np.zeros((128, 128)),
            "mask": np.ones((128, 128))
        }
        
        # Should not raise
        self.validator.validate(data, "sim")

    def test_valid_384x384_simulation(self):
        """Test valid 384x384 simulation data"""
        data = {
            "df_values": np.random.rand(384, 384),
            "mask": np.random.randint(0, 2, (384, 384))
        }
        
        # Should not raise
        self.validator.validate(data, "sim")

    def test_valid_list_input(self):
        """Test valid simulation with list input"""
        data = {
            "df_values": [[i + j for j in range(128)] for i in range(128)],
            "mask": [[1, 0] * 64 for _ in range(128)]
        }
        
        # Should not raise
        self.validator.validate(data, "sim")

    def test_custom_valid_sizes(self):
        """Test validator with custom valid sizes"""
        validator = SimulationDataValidator(valid_sizes=(256, 512))
        data = {
            "df_values": np.zeros((256, 256)),
            "mask": np.ones((256, 256))
        }
        
        # Should not raise
        validator.validate(data, "sim")

    def test_custom_valid_sizes_invalid(self):
        """Test invalid size with custom valid sizes"""
        validator = SimulationDataValidator(valid_sizes=(256, 512))
        data = {
            "df_values": np.zeros((128, 128)),
            "mask": np.ones((128, 128))
        }
        
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(data, "sim")
        
        assert exc_info.value.error_code == ErrorCode.INVALID_DIMENSIONS

    def test_field_path_in_error(self):
        """Test that field path is included in error"""
        data = {
            "df_values": "invalid",
            "mask": [[1, 0], [0, 1]]
        }
        
        with pytest.raises(ValidationError) as exc_info:
            self.validator.validate(data, "request.sims[0]")
        
        assert "request.sims[0].df_values" in exc_info.value.field

    def test_shape_context_in_error(self):
        """Test that shape is included in error context"""
        data = {
            "df_values": np.zeros((3, 3)),  # Invalid size
            "mask": np.ones((3, 3))
        }
        
        with pytest.raises(ValidationError) as exc_info:
            self.validator.validate(data, "sim")
        
        assert exc_info.value.context["shape"] == (3, 3)
