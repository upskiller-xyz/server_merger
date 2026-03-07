"""Rotate window images step"""

import logging

from src.components.processing.context import WindowProcessingContext, ImagePair
from src.components.processing.steps.base import ProcessingStep
from src.components.processing.window_processor import WindowProcessor
from src.core.exceptions import MissingPositionError

logger = logging.getLogger("logger")


class RotateWindowStep(ProcessingStep):
    """Rotate window images and reference point by direction angle"""

    def __init__(self, window_processor: WindowProcessor):
        super().__init__()
        self.window_processor = window_processor

    def run(self, context: WindowProcessingContext) -> WindowProcessingContext:
        """Apply rotation transformation"""
        logger.debug(f"Step 3: Rotating window '{context.input.window_id}'")

        rotation_angle = context.input.window.direction_angle if context.input.window.direction_angle is not None else 0

        if context.position is None:
            raise MissingPositionError(f"Position context is None for window '{context.input.window_id}'")

        df_rotated, mask_rotated, ref_px_rotated = (
            self.window_processor.rotate_window_images(
                context.original_images.df_values,
                context.original_images.mask,
                context.position.ref_px_original,
                rotation_angle,
                context.input.window_id
            )
        )

        context.original_images = ImagePair(df_rotated, mask_rotated)
        context.position.ref_px_rotated = ref_px_rotated

        return context
