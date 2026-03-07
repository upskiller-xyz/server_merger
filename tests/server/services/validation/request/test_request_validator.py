"""Tests for request validator service"""

import pytest
from unittest.mock import Mock
from src.server.services.validation.request_validator import RequestValidator
from src.server.services.validation.validation_error import ValidationError


class TestRequestValidator:
    """Test request validator strategy pattern"""

    def setup_method(self):
        """Set up validator"""
        self.validator = RequestValidator()

    def test_validate_without_registered_strategy(self):
        """Test error when strategy is not registered"""
        with pytest.raises(KeyError) as exc_info:
            self.validator.validate("unknown_strategy", {})
        
        assert "unknown_strategy" in str(exc_info.value)

    def test_register_strategy(self):
        """Test registering a validation strategy"""
        strategy_called = []
        
        def test_strategy(data):
            strategy_called.append(data)
        
        self.validator.register_strategy("test", test_strategy)
        self.validator.validate("test", {"key": "value"})
        
        assert strategy_called[0] == {"key": "value"}

    def test_validate_calls_correct_strategy(self):
        """Test that validate calls the correct strategy"""
        strategy1_called = []
        strategy2_called = []
        
        def strategy1(data):
            strategy1_called.append(data)
        
        def strategy2(data):
            strategy2_called.append(data)
        
        self.validator.register_strategy("strategy1", strategy1)
        self.validator.register_strategy("strategy2", strategy2)
        
        self.validator.validate("strategy1", {"data": "test1"})
        self.validator.validate("strategy2", {"data": "test2"})
        
        assert len(strategy1_called) == 1
        assert len(strategy2_called) == 1
        assert strategy1_called[0] == {"data": "test1"}
        assert strategy2_called[0] == {"data": "test2"}

    def test_validate_with_failing_strategy(self):
        """Test that validation errors from strategy are propagated"""
        def failing_strategy(data):
            raise ValidationError(
                message="Test error",
                error_code="TEST_ERROR",
                field="test_field"
            )
        
        self.validator.register_strategy("failing", failing_strategy)
        
        with pytest.raises(ValidationError) as exc_info:
            self.validator.validate("failing", {})
        
        assert "Test error" in exc_info.value.message

    def test_validate_with_generic_exception(self):
        """Test that generic exceptions from strategy are propagated"""
        def exception_strategy(data):
            raise ValueError("Generic error")
        
        self.validator.register_strategy("exception", exception_strategy)
        
        with pytest.raises(ValueError) as exc_info:
            self.validator.validate("exception", {})
        
        assert "Generic error" in str(exc_info.value)

    def test_register_multiple_strategies(self):
        """Test registering multiple strategies"""
        strategies = {}
        
        for i in range(5):
            strategy_name = f"strategy_{i}"
            strategies[strategy_name] = Mock()
            self.validator.register_strategy(strategy_name, strategies[strategy_name])
        
        # Verify all strategies are stored
        assert len(self.validator.validation_strategies) == 5

    def test_overwrite_existing_strategy(self):
        """Test that registering a strategy with same name overwrites"""
        old_strategy = Mock()
        new_strategy = Mock()
        
        self.validator.register_strategy("test", old_strategy)
        self.validator.register_strategy("test", new_strategy)
        
        self.validator.validate("test", {})
        
        # Only new_strategy should be called
        assert old_strategy.call_count == 0
        assert new_strategy.call_count == 1

    def test_strategy_receives_exact_data(self):
        """Test that strategy receives the exact data passed"""
        received_data = []
        
        def capture_strategy(data):
            received_data.append(data)
        
        self.validator.register_strategy("capture", capture_strategy)
        
        test_data = {
            "nested": {"deep": {"value": 42}},
            "list": [1, 2, 3],
            "string": "test"
        }
        
        self.validator.validate("capture", test_data)
        
        assert received_data[0] == test_data
        assert received_data[0] is test_data  # Same object

    def test_strategy_with_none_data(self):
        """Test strategy with None data"""
        received_data = []
        
        def null_strategy(data):
            received_data.append(data)
        
        self.validator.register_strategy("null", null_strategy)
        self.validator.validate("null", None)
        
        assert received_data[0] is None

    def test_strategy_with_empty_dict(self):
        """Test strategy with empty dict"""
        received_data = []
        
        def empty_strategy(data):
            received_data.append(data)
        
        self.validator.register_strategy("empty", empty_strategy)
        self.validator.validate("empty", {})
        
        assert received_data[0] == {}

    def test_strategy_with_complex_data(self):
        """Test strategy with complex nested data"""
        received_data = []
        
        def complex_strategy(data):
            received_data.append(data)
        
        self.validator.register_strategy("complex", complex_strategy)
        
        complex_data = {
            "users": [
                {"id": 1, "name": "Alice", "roles": ["admin", "user"]},
                {"id": 2, "name": "Bob", "roles": ["user"]}
            ],
            "metadata": {
                "version": "1.0",
                "timestamp": "2024-01-01T00:00:00Z"
            }
        }
        
        self.validator.validate("complex", complex_data)
        
        assert received_data[0] == complex_data

    def test_strategy_validation_error_preserves_details(self):
        """Test that ValidationError details are preserved"""
        def detail_strategy(data):
            raise ValidationError(
                message="Detailed error",
                error_code="DETAIL_CODE",
                field="field.path.deep",
                value="bad_value",
                context={"key": "value"}
            )
        
        self.validator.register_strategy("detail", detail_strategy)
        
        with pytest.raises(ValidationError) as exc_info:
            self.validator.validate("detail", {})
        
        error = exc_info.value
        assert error.message == "Detailed error"
        assert error.error_code == "DETAIL_CODE"
        assert error.field == "field.path.deep"
        assert error.value == "bad_value"
        assert error.context == {"key": "value"}

    def test_strategy_called_multiple_times(self):
        """Test calling same strategy multiple times"""
        call_count = []
        
        def counting_strategy(data):
            call_count.append(1)
        
        self.validator.register_strategy("counter", counting_strategy)
        
        for i in range(10):
            self.validator.validate("counter", {"iteration": i})
        
        assert len(call_count) == 10

    def test_initial_empty_strategies(self):
        """Test validator starts with no strategies"""
        validator = RequestValidator()
        assert len(validator.validation_strategies) == 0

    def test_strategy_exception_type_preserved(self):
        """Test that specific exception types are preserved"""
        class CustomException(Exception):
            pass
        
        def custom_strategy(data):
            raise CustomException("Custom error")
        
        self.validator.register_strategy("custom", custom_strategy)
        
        with pytest.raises(CustomException) as exc_info:
            self.validator.validate("custom", {})
        
        assert isinstance(exc_info.value, CustomException)
        assert "Custom error" in str(exc_info.value)

    def test_strategy_lambda_function(self):
        """Test registering lambda as strategy"""
        self.validator.register_strategy(
            "lambda",
            lambda data: None if data.get("valid") else (_ for _ in ()).throw(ValueError("Invalid"))
        )
        
        # Valid data passes
        self.validator.validate("lambda", {"valid": True})
        
        # Invalid data raises
        with pytest.raises(ValueError):
            self.validator.validate("lambda", {"valid": False})
