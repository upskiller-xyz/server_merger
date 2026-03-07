"""Custom exceptions for the server merger application."""


class MissingPositionError(AttributeError):
    """Raised when context.position is None when it should have a value."""

    def __init__(self, message: str = "Context position is None"):
        self.message = message
        super().__init__(self.message)


class WindowOrientationError(ValueError):
    """Raised when window orientation cannot be determined (all perpendicular directions point inside the room)."""

    def __init__(self, message: str = "Unable to determine window orientation: all perpendicular directions point inside the room"):
        self.message = message
        super().__init__(self.message)
