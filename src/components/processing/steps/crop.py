"""Crop window images step"""

import logging

from src.components.processing.context import WindowProcessingContext, ImagePair, CropData
from src.components.processing.steps.base import ProcessingStep
from src.components.processing.window_processor import WindowProcessor

logger = logging.getLogger("logger")


class CropWindowStep(ProcessingStep):
    """Crop window images to visible (non-zero mask) bounds"""

    def __init__(self, window_processor: WindowProcessor):
        super().__init__()
        self.window_processor = window_processor

    def run(self, context: WindowProcessingContext) -> WindowProcessingContext:
        """Crop to mask bounds"""
        logger.debug(f"Step 4: Cropping window '{context.input.window_id}' to visible bounds")
        
        df_cropped, mask_cropped, crop_offset = (
            self.window_processor.crop_to_visible_bounds(
                context.original_images.df_values,
                context.original_images.mask,
                context.input.window_id
            )
        )

        context.original_images = ImagePair(df_cropped, mask_cropped)
        context.cropped = CropData(
            images=ImagePair(df_cropped, mask_cropped),
            offset=crop_offset
        )

        return context
