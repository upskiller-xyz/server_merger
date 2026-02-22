"""Composite validator that combines multiple validators"""

from typing import Any, List

from .base_validator import Validator


class CompositeValidator(Validator):
    """Combines multiple validators"""

    def __init__(self, validators: List[Validator]):
        self.validators = validators

    def validate(self, value: Any, field_path: str) -> None:
        """Run all validators in sequence"""
        for validator in self.validators:
            validator.validate(value, field_path)
