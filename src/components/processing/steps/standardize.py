"""Standardize window images step"""

import logging

from src.components.processing.context import WindowProcessingContext, ImagePair
from src.components.processing.steps.base import ProcessingStep
from src.components.processing.window_processor import WindowProcessor

logger = logging.getLogger("logger")


class StandardizeWindowStep(ProcessingStep):
    """Standardize window images to 128x128 at 0.1m/px"""

    def __init__(self, window_processor: WindowProcessor):
        super().__init__()
        self.window_processor = window_processor

    def run(self, context: WindowProcessingContext) -> WindowProcessingContext:
        """Resize images to standard 128x128 resolution"""
        logger.debug(f"Step 2: Standardizing window '{context.input.window_id}' to 128x128")

        df_std, mask_std = self.window_processor.standardize_window_images(
            context.original_images.df_values,
            context.original_images.mask
        )

        context.original_images = ImagePair(df_std, mask_std)

        return context
