"""Tests for CompositeValidator"""

import pytest
from unittest.mock import Mock, MagicMock
from src.server.services.validation.composite_validator import CompositeValidator
from src.server.services.validation.validation_error import ValidationError


class TestCompositeValidator:
    """Test CompositeValidator class"""

    def test_validate_single_validator_passes(self):
        """Test validation passes when single validator passes"""
        mock_validator = Mock()
        composite = CompositeValidator([mock_validator])
        
        # Should not raise
        composite.validate(42, "field")
        
        # Verify validator was called
        mock_validator.validate.assert_called_once_with(42, "field")

    def test_validate_multiple_validators_pass(self):
        """Test validation passes when all validators pass"""
        mock_validator1 = Mock()
        mock_validator2 = Mock()
        mock_validator3 = Mock()
        composite = CompositeValidator([mock_validator1, mock_validator2, mock_validator3])
        
        # Should not raise
        composite.validate(42, "field")
        
        # Verify all validators were called
        mock_validator1.validate.assert_called_once_with(42, "field")
        mock_validator2.validate.assert_called_once_with(42, "field")
        mock_validator3.validate.assert_called_once_with(42, "field")

    def test_validate_first_validator_fails(self):
        """Test validation fails when first validator fails"""
        mock_validator1 = Mock()
        mock_validator2 = Mock()
        
        error = ValidationError("Invalid", None)
        mock_validator1.validate.side_effect = error
        
        composite = CompositeValidator([mock_validator1, mock_validator2])
        
        with pytest.raises(ValidationError):
            composite.validate(42, "field")
        
        # Second validator should not be called
        mock_validator2.validate.assert_not_called()

    def test_validate_second_validator_fails(self):
        """Test validation fails when second validator fails"""
        mock_validator1 = Mock()
        mock_validator2 = Mock()
        
        error = ValidationError("Invalid", None)
        mock_validator2.validate.side_effect = error
        
        composite = CompositeValidator([mock_validator1, mock_validator2])
        
        with pytest.raises(ValidationError):
            composite.validate(42, "field")
        
        # Both validators should be called (if first succeeds)
        mock_validator1.validate.assert_called_once()
        mock_validator2.validate.assert_called_once()

    def test_validate_no_validators(self):
        """Test validation passes with no validators"""
        composite = CompositeValidator([])
        
        # Should not raise
        composite.validate(42, "field")

    def test_validate_runs_in_sequence(self):
        """Test validators run in sequence"""
        call_order = []
        
        mock_validator1 = Mock()
        mock_validator2 = Mock()
        mock_validator3 = Mock()
        
        mock_validator1.validate.side_effect = lambda v, f: call_order.append(1)
        mock_validator2.validate.side_effect = lambda v, f: call_order.append(2)
        mock_validator3.validate.side_effect = lambda v, f: call_order.append(3)
        
        composite = CompositeValidator([mock_validator1, mock_validator2, mock_validator3])
        composite.validate(42, "field")
        
        assert call_order == [1, 2, 3]

    def test_validate_stops_on_first_failure(self):
        """Test execution stops on first validation error"""
        mock_validator1 = Mock()
        mock_validator2 = Mock()
        mock_validator3 = Mock()
        
        error = ValidationError("Fail", None)
        mock_validator2.validate.side_effect = error
        
        composite = CompositeValidator([mock_validator1, mock_validator2, mock_validator3])
        
        with pytest.raises(ValidationError):
            composite.validate(42, "field")
        
        mock_validator1.validate.assert_called_once()
        mock_validator2.validate.assert_called_once()
        # Third validator should not run
        mock_validator3.validate.assert_not_called()

    def test_validate_exception_propagates(self):
        """Test validation error propagates"""
        mock_validator = Mock()
        error = ValidationError("Test error", None, field="test_field")
        mock_validator.validate.side_effect = error
        
        composite = CompositeValidator([mock_validator])
        
        with pytest.raises(ValidationError) as exc_info:
            composite.validate(42, "field")
        
        assert exc_info.value.field == "test_field"

    def test_validators_stored(self):
        """Test validators are stored correctly"""
        mock_validator1 = Mock()
        mock_validator2 = Mock()
        composite = CompositeValidator([mock_validator1, mock_validator2])
        
        assert composite.validators == [mock_validator1, mock_validator2]

    def test_validate_with_different_values(self):
        """Test validators receive correct values"""
        mock_validator = Mock()
        composite = CompositeValidator([mock_validator])
        
        # Test with different value types
        composite.validate([1, 2, 3], "array")
        mock_validator.validate.assert_called_with([1, 2, 3], "array")
        
        composite.validate({"key": "value"}, "dict_field")
        mock_validator.validate.assert_called_with({"key": "value"}, "dict_field")
        
        composite.validate("string", "string_field")
        mock_validator.validate.assert_called_with("string", "string_field")

    def test_composite_of_composites(self):
        """Test composite validator containing other composite validators"""
        inner_mock1 = Mock()
        inner_mock2 = Mock()
        inner_composite1 = CompositeValidator([inner_mock1])
        inner_composite2 = CompositeValidator([inner_mock2])
        
        outer_composite = CompositeValidator([inner_composite1, inner_composite2])
        
        outer_composite.validate(42, "field")
        
        inner_mock1.validate.assert_called_once_with(42, "field")
        inner_mock2.validate.assert_called_once_with(42, "field")

    def test_validate_field_path_propagation(self):
        """Test field path is correctly passed through"""
        mock_validator1 = Mock()
        mock_validator2 = Mock()
        composite = CompositeValidator([mock_validator1, mock_validator2])
        
        composite.validate(42, "window.properties.width")
        
        mock_validator1.validate.assert_called_with(42, "window.properties.width")
        mock_validator2.validate.assert_called_with(42, "window.properties.width")
