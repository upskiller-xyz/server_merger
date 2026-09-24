"""Custom exceptions for the server merger application."""


class ClientInputError(ValueError):
    """A validation failure caused by the caller's payload.

    Only these messages are safe to echo to the client; a plain ValueError may
    carry internal details (coordinates, array shapes, window state) and must
    be answered with a generic error instead.
    """


class MissingPositionError(AttributeError):
    """Raised when context.position is None when it should have a value."""

    def __init__(self, message: str = "Context position is None"):
        self.message = message
        super().__init__(self.message)


class WindowOrientationError(ClientInputError):
    """Raised when window orientation cannot be determined (all perpendicular directions point inside the room)."""

    def __init__(self, message: str = "Unable to determine window orientation: all perpendicular directions point inside the room"):
        self.message = message
        super().__init__(self.message)
