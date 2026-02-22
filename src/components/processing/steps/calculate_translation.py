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

        Formula: offset = ref_in_crop - room_coord_pixels
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
            raise MissingPositionError(f"Position context is None for window '{context.input.window_id}'")
        
        ref_x_in_crop = self._get_crop(context, axis=0)
        ref_y_in_crop = self._get_crop(context, axis=1)

        # crop_offset_x, crop_offset_y = context.cropped.offset
        # ref_in_crop_x = context.position.ref_px_rotated[0] - crop_offset_x
        # ref_in_crop_y = context.position.ref_px_rotated[1] - crop_offset_y

        context.translation = Point2D(
            ref_x_in_crop,
            ref_y_in_crop)
        
        logger.debug(
            f"  room_coord_pixels: ({context.position.room_coord_pixels.x}, "
            f"{context.position.room_coord_pixels.y})"
        )

        # context.translation = Point2D(offset_x, offset_y)
        logger.debug(f"  Translation: {context.translation}")

        return context
    
    def _get_crop(self, context:WindowProcessingContext, axis:int)->int:
        pt = context.position.room_coord_pixels.x # type: ignore
        
        if axis == 1:
            pt = context.position.room_coord_pixels.y # type: ignore
        _crop = pt
        if context.position.ref_px_rotated[axis] > 105: # type: ignore
            _crop = context.position.ref_px_rotated[axis] - pt # type: ignore

        if context.position.ref_px_rotated[axis] ==64: # type: ignore
            _crop = 64 - pt
            
        return int(_crop)
