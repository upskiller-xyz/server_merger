"""Base class for processing steps"""

from abc import ABC, abstractmethod

from src.components.processing.context import WindowProcessingContext


class ProcessingStep(ABC):
    """
    Abstract base class for processing steps.

    Each step implements the run() method which operates on the context.
    """

    def __init__(self):
        """
        Initialize step with logger.

        Args:
            logger: Logger instance for step logging
        """
        pass

    @abstractmethod
    def run(self, context: WindowProcessingContext) -> WindowProcessingContext:
        """
        Execute this processing step.

        Args:
            context: Current processing context

        Returns:
            Updated context with this step's results
        """
        pass
