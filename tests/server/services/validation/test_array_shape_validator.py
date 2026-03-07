"""Tests for ArrayShapeValidator"""

import pytest
import numpy as np
from src.server.services.validation.array_shape_validator import ArrayShapeValidator
from src.server.services.validation.validation_error import ValidationError
from src.server.services.validation.enums import ErrorCode


class TestArrayShapeValidator:
    """Test ArrayShapeValidator class"""

    def test_validate_1d_array_list(self):
        """Test validation passes for 1D list"""
        validator = ArrayShapeValidator(expected_ndim=1)
        # Should not raise
        validator.validate([1, 2, 3], "field.name")

    def test_validate_1d_array_numpy(self):
        """Test validation passes for 1D numpy array"""
        validator = ArrayShapeValidator(expected_ndim=1)
        arr = np.array([1, 2, 3])
        # Should not raise
        validator.validate(arr, "field.name")

    def test_validate_2d_array_list_of_lists(self):
        """Test validation passes for 2D list"""
        validator = ArrayShapeValidator(expected_ndim=2)
        # Should not raise
        validator.validate([[1, 2], [3, 4]], "image")

    def test_validate_2d_array_numpy(self):
        """Test validation passes for 2D numpy array"""
        validator = ArrayShapeValidator(expected_ndim=2)
        arr = np.array([[1, 2], [3, 4]])
        # Should not raise
        validator.validate(arr, "image")

    def test_validate_3d_array_numpy(self):
        """Test validation passes for 3D numpy array"""
        validator = ArrayShapeValidator(expected_ndim=3)
        arr = np.ones((10, 20, 30))
        # Should not raise
        validator.validate(arr, "volume")

    def test_validate_wrong_dimensionality(self):
        """Test validation fails for wrong number of dimensions"""
        validator = ArrayShapeValidator(expected_ndim=2)
        with pytest.raises(ValidationError) as exc_info:
            validator.validate([1, 2, 3], "image")
        
        error = exc_info.value
        assert error.error_code == ErrorCode.INVALID_DIMENSIONS
        assert "2D" in error.message

    def test_validate_3d_array_expecting_2d(self):
        """Test validation fails for 3D when 2D expected"""
        validator = ArrayShapeValidator(expected_ndim=2)
        arr = np.ones((10, 20, 30))
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(arr, "image")
        
        error = exc_info.value
        assert error.error_code == ErrorCode.INVALID_DIMENSIONS

    def test_validate_not_array_type(self):
        """Test validation fails for non-array type"""
        validator = ArrayShapeValidator(expected_ndim=1)
        with pytest.raises(ValidationError) as exc_info:
            validator.validate("not an array", "field")
        
        error = exc_info.value
        assert error.error_code == ErrorCode.INVALID_TYPE

    def test_validate_scalar_type(self):
        """Test validation fails for scalar"""
        validator = ArrayShapeValidator(expected_ndim=1)
        with pytest.raises(ValidationError):
            validator.validate(42, "field")

    def test_validate_with_valid_shapes(self):
        """Test validation passes when shape is in valid_shapes"""
        validator = ArrayShapeValidator(
            expected_ndim=2,
            valid_shapes=[(128, 128), (256, 256)]
        )
        # Should not raise
        validator.validate(np.ones((128, 128)), "image")

    def test_validate_with_valid_shapes_second_option(self):
        """Test validation passes for second valid shape"""
        validator = ArrayShapeValidator(
            expected_ndim=2,
            valid_shapes=[(128, 128), (256, 256)]
        )
        # Should not raise
        validator.validate(np.ones((256, 256)), "image")

    def test_validate_with_invalid_shape(self):
        """Test validation fails when shape not in valid_shapes"""
        validator = ArrayShapeValidator(
            expected_ndim=2,
            valid_shapes=[(128, 128), (256, 256)]
        )
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(np.ones((64, 64)), "image")
        
        error = exc_info.value
        assert error.error_code == ErrorCode.INVALID_DIMENSIONS
        assert "invalid shape" in error.message.lower()

    def test_validate_with_valid_shapes_1d(self):
        """Test validation with 1D valid shapes"""
        validator = ArrayShapeValidator(
            expected_ndim=1,
            valid_shapes=[(100,), (200,), (300,)]
        )
        # Should not raise
        validator.validate(np.ones(100), "vector")

    def test_validate_with_valid_shapes_wrong_size(self):
        """Test validation fails for wrong 1D size"""
        validator = ArrayShapeValidator(
            expected_ndim=1,
            valid_shapes=[(100,), (200,), (300,)]
        )
        with pytest.raises(ValidationError):
            validator.validate(np.ones(150), "vector")

    def test_field_path_in_error(self):
        """Test field path is in error message"""
        validator = ArrayShapeValidator(expected_ndim=2)
        with pytest.raises(ValidationError) as exc_info:
            validator.validate([1, 2, 3], "room.image")
        
        error = exc_info.value
        assert error.field == "room.image"

    def test_context_includes_shape(self):
        """Test error context includes shape info"""
        validator = ArrayShapeValidator(expected_ndim=2)
        with pytest.raises(ValidationError) as exc_info:
            validator.validate([1, 2, 3], "field")
        
        error = exc_info.value
        assert "shape" in error.context

    def test_context_includes_valid_shapes(self):
        """Test error context includes valid_shapes"""
        validator = ArrayShapeValidator(
            expected_ndim=2,
            valid_shapes=[(128, 128), (256, 256)]
        )
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(np.ones((64, 64)), "image")
        
        error = exc_info.value
        assert "valid_shapes" in error.context

    def test_validate_empty_array(self):
        """Test validation with empty array"""
        validator = ArrayShapeValidator(expected_ndim=1)
        # Should not raise
        validator.validate(np.array([]), "empty")

    def test_validate_2d_empty_array(self):
        """Test validation with 2D empty array"""
        validator = ArrayShapeValidator(expected_ndim=2)
        # Should not raise
        validator.validate(np.zeros((0, 10)), "empty")
