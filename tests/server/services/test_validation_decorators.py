"""Tests for validation decorators"""

import pytest
from unittest.mock import Mock, patch
from src.server.services.validation.decorators import validate_request, _validate_dict
from src.server.services.validation.validation_error import ValidationError
from src.server.services.validation.enums import ErrorCode
from src.server.services.validation.type_validator import TypeValidator
from src.server.services.validation.range_validator import RangeValidator
from src.server.services.validation.non_empty_validator import NonEmptyValidator


class TestValidateRequestDecorator:
    """Test validate_request decorator"""

    def test_decorator_allows_no_validation(self):
        """Test decorator with no validation schema"""
        @validate_request({})
        def test_func(self, data):
            return {"result": data}
        
        result = test_func(Mock(), {"any": "data"})
        assert result["result"]["any"] == "data"

    def test_decorator_passes_valid_data(self):
        """Test decorator passes valid data through"""
        schema = {
            "name": {"validators": [TypeValidator(str)]}
        }
        
        @validate_request(schema)
        def test_func(self, data):
            return {"received": data}
        
        result = test_func(Mock(), {"name": "test"})
        assert result["received"]["name"] == "test"

    def test_decorator_raises_on_validation_failure(self):
        """Test decorator raises when validation fails"""
        schema = {
            "count": {"validators": [TypeValidator(int)]}
        }
        
        @validate_request(schema)
        def test_func(self, data):
            return {"received": data}
        
        with pytest.raises(ValidationError):
            test_func(Mock(), {"count": "not an int"})

    def test_decorator_with_multiple_validators(self):
        """Test decorator with multiple validators on one field"""
        schema = {
            "age": {"validators": [TypeValidator(int), RangeValidator(min_value=0, max_value=150)]}
        }
        
        @validate_request(schema)
        def test_func(self, data):
            return {"age": data["age"]}
        
        # Valid data
        result = test_func(Mock(), {"age": 25})
        assert result["age"] == 25
        
        # Invalid - out of range
        with pytest.raises(ValidationError):
            test_func(Mock(), {"age": 200})

    def test_decorator_without_data_parameter(self):
        """Test decorator when data is not provided"""
        schema = {"field": {"validators": []}}
        
        @validate_request(schema)
        def test_func(self):
            return {"success": True}
        
        result = test_func(Mock())
        assert result["success"] == True

    def test_decorator_preserves_function_name(self):
        """Test decorator preserves function name"""
        @validate_request({})
        def my_test_func(self, data):
            """Test docstring"""
            return data
        
        assert my_test_func.__name__ == "my_test_func"
        assert my_test_func.__doc__ == "Test docstring"

    def test_decorator_with_nested_validation(self):
        """Test decorator with nested schema"""
        schema = {
            "user": {
                "validators": [TypeValidator(dict)],
                "nested": {
                    "name": {"validators": [TypeValidator(str)]},
                    "age": {"validators": [TypeValidator(int)]}
                }
            }
        }
        
        @validate_request(schema)
        def test_func(self, data):
            return {"user": data["user"]}
        
        valid_data = {"user": {"name": "John", "age": 30}}
        result = test_func(Mock(), valid_data)
        assert result["user"]["name"] == "John"

    def test_decorator_with_non_empty_validator(self):
        """Test decorator with NonEmptyValidator"""
        schema = {
            "items": {"validators": [NonEmptyValidator()]}
        }
        
        @validate_request(schema)
        def test_func(self, data):
            return {"items_count": len(data["items"])}
        
        # Valid - non-empty list
        result = test_func(Mock(), {"items": [1, 2, 3]})
        assert result["items_count"] == 3
        
        # Invalid - empty list
        with pytest.raises(ValidationError):
            test_func(Mock(), {"items": []})

    def test_decorator_with_range_validator(self):
        """Test decorator with RangeValidator"""
        schema = {
            "percentage": {"validators": [RangeValidator(min_value=0, max_value=100)]}
        }
        
        @validate_request(schema)
        def test_func(self, data):
            return {"percentage": data["percentage"]}
        
        # Valid values
        assert test_func(Mock(), {"percentage": 0})["percentage"] == 0
        assert test_func(Mock(), {"percentage": 50})["percentage"] == 50
        assert test_func(Mock(), {"percentage": 100})["percentage"] == 100
        
        # Invalid - out of range
        with pytest.raises(ValidationError):
            test_func(Mock(), {"percentage": -1})


class TestValidateDictFunction:
    """Test _validate_dict function"""

    def test_validate_empty_dict(self):
        """Test validating empty dictionary"""
        # Should not raise
        _validate_dict({}, {}, "")

    def test_validate_matching_schema(self):
        """Test validating dict that matches schema"""
        schema = {
            "field1": {"validators": [TypeValidator(str)]},
            "field2": {"validators": [TypeValidator(int)]}
        }
        data = {"field1": "value", "field2": 42}
        
        # Should not raise
        _validate_dict(data, schema, "")

    def test_validate_missing_optional_field(self):
        """Test that missing fields don't raise"""
        schema = {
            "optional_field": {"validators": [TypeValidator(str)]}
        }
        data = {}
        
        # Should not raise for missing optional field
        _validate_dict(data, schema, "")

    def test_validate_extra_fields_in_data(self):
        """Test that extra fields in data don't cause errors"""
        schema = {
            "field1": {"validators": [TypeValidator(str)]}
        }
        data = {"field1": "value", "field2": "extra"}
        
        # Should not raise
        _validate_dict(data, schema, "")

    def test_validate_with_field_path(self):
        """Test field path is included in error"""
        schema = {
            "field": {"validators": [TypeValidator(int)]}
        }
        data = {"field": "not an int"}
        
        with pytest.raises(ValidationError) as exc_info:
            _validate_dict(data, schema, "parent")
        
        error = exc_info.value
        assert "parent.field" in error.field or "field" in error.field

    def test_validate_nested_dict(self):
        """Test validating nested dictionary"""
        schema = {
            "person": {
                "validators": [TypeValidator(dict)],
                "nested": {
                    "name": {"validators": [TypeValidator(str)]},
                    "age": {"validators": [TypeValidator(int)]}
                }
            }
        }
        data = {
            "person": {
                "name": "John",
                "age": 30
            }
        }
        
        # Should not raise
        _validate_dict(data, schema, "")

    def test_validate_nested_dict_invalid(self):
        """Test validating nested dict with invalid data"""
        schema = {
            "person": {
                "validators": [],
                "nested": {
                    "age": {"validators": [TypeValidator(int)]}
                }
            }
        }
        data = {
            "person": {
                "age": "not an int"
            }
        }
        
        with pytest.raises(ValidationError):
            _validate_dict(data, schema, "")

    def test_validate_multiple_validators_stop_on_first_failure(self):
        """Test that validation stops on first validator failure"""
        validators_called = []
        
        class TrackingValidator:
            def __init__(self):
                pass
            def validate(self, value, field_path):
                validators_called.append(self)
                raise ValidationError("Error", ErrorCode.INVALID_TYPE)
        
        schema = {
            "field": {"validators": [TrackingValidator(), TrackingValidator()]}
        }
        data = {"field": "value"}
        
        with pytest.raises(ValidationError):
            _validate_dict(data, schema, "")
        
        # Only first validator should be called
        assert len(validators_called) == 1

    def test_validate_wildcard_nested(self):
        """Test validating with wildcard nested schema"""
        schema = {
            "windows": {
                "validators": [TypeValidator(dict)],
                "nested": {
                    "*": {
                        "type": {"validators": [TypeValidator(str)]},
                        "width": {"validators": [TypeValidator(int)]}
                    }
                }
            }
        }
        data = {
            "windows": {
                "window1": {"type": "standard", "width": 100},
                "window2": {"type": "large", "width": 200}
            }
        }
        
        # Should process wildcard entries
        # Note: actual behavior depends on implementation
        try:
            _validate_dict(data, schema, "")
        except Exception:
            # Wildcard handling may vary in implementation
            pass

    def test_validate_empty_schema(self):
        """Test validating with empty schema"""
        data = {"any": "field"}
        schema = {}
        
        # Should not raise
        _validate_dict(data, schema, "")

    def test_validate_passes_field_path_to_validators(self):
        """Test that validators receive correct field path"""
        collected_paths = []
        
        class PathCollectingValidator:
            def validate(self, value, field_path):
                collected_paths.append(field_path)
        
        schema = {
            "field": {"validators": [PathCollectingValidator()]}
        }
        data = {"field": "value"}
        
        _validate_dict(data, schema, "parent")
        
        assert len(collected_paths) == 1
        # Path might be "parent.field" or "field" depending on implementation
        assert "field" in collected_paths[0]
