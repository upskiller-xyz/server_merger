"""Base validator class"""

from abc import ABC, abstractmethod
from typing import Any


class Validator(ABC):
    """Base class for validators"""

    @abstractmethod
    def validate(self, value: Any, field_path: str) -> None:
        """
        Validate a value.

        Args:
            value: Value to validate
            field_path: Dot-separated path to field (e.g., "windows.window1.x1")

        Raises:
            ValidationError: If validation fails
        """
        pass
