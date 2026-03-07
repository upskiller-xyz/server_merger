"""Service for validating complete request payloads"""

from typing import Dict, Any, Callable

from .validation_error import ValidationError


class RequestValidator:
    """
    Service for validating complete request payloads.

    Uses Strategy pattern for different validation strategies.
    """

    def __init__(self):
        self.validation_strategies: Dict[str, Callable] = {}

    def register_strategy(self, name: str, validator: Callable) -> None:
        """Register a validation strategy"""
        self.validation_strategies[name] = validator

    def validate(self, strategy_name: str, data: Any) -> None:
        """
        Validate data using named strategy.

        Args:
            strategy_name: Name of validation strategy to use
            data: Data to validate

        Raises:
            ValidationError: If validation fails
            KeyError: If strategy not found
        """
        if strategy_name not in self.validation_strategies:
            raise KeyError(f"Validation strategy '{strategy_name}' not found")

        self.validation_strategies[strategy_name](data)
