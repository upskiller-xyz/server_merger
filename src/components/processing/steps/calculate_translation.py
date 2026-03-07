"""Calculate translation step"""

import logging

from src.components.geometry_ops import Point2D
from src.components.processing.context import WindowProcessingContext
from src.components.processing.steps.base import ProcessingStep
from src.core.exceptions import MissingPositionError

logger = logging.getLogger("logger")


class CalculateTranslationStep(ProcessingStep):
    """Calculate final translation offset for placing window on room canvas"""

    def __init__(self):
        super().__init__()

    def run(self, context: WindowProcessingContext) -> WindowProcessingContext:
        """Calculate translation vector for inverted overlap convention.

        Formula: translation = ref_px_rotated - crop_offset - room_coord_pixels
        This places the reference pixel (window facade position) at the
        correct room coordinate when using the inverted overlap convention
        where positive offset = skip source rows/cols.
        """
        logger.debug(f"Step 5: Calculating translation for '{context.input.window_id}'")

        if context.position is None:
            raise MissingPositionError(f"Position context is None for window '{context.input.window_id}'")
        if context.position.ref_px_rotated is None:
            raise MissingPositionError(f"Position context is None for window '{context.input.window_id}'")
        if context.cropped is None:
            raise MissingPositionError(f"Cropped geometry is None for window '{context.input.window_id}'")
        
        crop_offset_x, crop_offset_y = context.cropped.offset
        ref_px_x = context.position.ref_px_rotated[0]
        ref_px_y = context.position.ref_px_rotated[1]
        room_px_x = context.position.room_coord_pixels.x
        room_px_y = context.position.room_coord_pixels.y

        # Apply formula: translation = ref_px_rotated - crop_offset - room_coord_pixels
        offset_x = ref_px_x - crop_offset_x - room_px_x
        offset_y = ref_px_y - crop_offset_y - room_px_y

        context.translation = Point2D(offset_x, offset_y)
        
        logger.debug(
            f"  ref_px_rotated: ({ref_px_x}, {ref_px_y}), "
            f"crop_offset: ({crop_offset_x}, {crop_offset_y}), "
            f"room_coord_pixels: ({room_px_x}, {room_px_y})"
        )
        logger.debug(f"  Translation: {context.translation}")

        return context
