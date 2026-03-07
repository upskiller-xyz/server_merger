"""Structured validation error with detailed information"""

from typing import Dict, Any, Optional
import numpy as np

from .enums import ErrorCode


class ValidationError(Exception):
    """
    Structured validation error with detailed information.

    Attributes:
        message: Human-readable error message
        error_code: Machine-readable error code
        field: Field path that caused the error (e.g., "windows.window1.x1")
        value: The invalid value (optional)
        context: Additional context information
    """

    def __init__(
        self,
        message: str,
        error_code: ErrorCode,
        field: Optional[str] = None,
        value: Any = None,
        context: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.field = field
        self.value = value
        self.context = context or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = {
            "error": self.message,
            "error_code": self.error_code.value
        }

        if self.field:
            result["field"] = self.field

        if self.value is not None:
            # Convert numpy types to Python types
            if isinstance(self.value, (np.integer, np.floating)):
                result["value"] = self.value.item()
            elif isinstance(self.value, np.ndarray):
                result["value"] = f"<array shape={self.value.shape}>"
            else:
                result["value"] = str(self.value)

        if self.context:
            result["context"] = self.context

        return result
