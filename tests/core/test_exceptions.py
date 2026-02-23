"""Tests for core exception classes."""

import pytest
from src.core.exceptions import (
    MissingPositionError,
    WindowOrientationError
)


class TestMissingPositionError:
    """Test MissingPositionError exception."""

    def test_missing_position_error_message(self):
        """Test that error message is properly set."""
        msg = "Position context required"
        with pytest.raises(MissingPositionError, match=msg):
            raise MissingPositionError(msg)

    def test_missing_position_error_default_message(self):
        """Test default error message."""
        with pytest.raises(MissingPositionError):
            raise MissingPositionError()

    def test_missing_position_error_is_exception(self):
        """Test that MissingPositionError is an Exception."""
        assert issubclass(MissingPositionError, Exception)


class TestWindowOrientationError:
    """Test WindowOrientationError exception."""

    def test_window_orientation_error_message(self):
        """Test that error message is properly set."""
        msg = "Cannot determine window orientation"
        with pytest.raises(WindowOrientationError, match=msg):
            raise WindowOrientationError(msg)

    def test_window_orientation_error_default_message(self):
        """Test default error message."""
        with pytest.raises(WindowOrientationError):
            raise WindowOrientationError()

    def test_window_orientation_error_is_exception(self):
        """Test that WindowOrientationError is an Exception."""
        assert issubclass(WindowOrientationError, Exception)
