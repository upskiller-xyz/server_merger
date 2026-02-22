"""Calculate window position step"""

import logging

from src.components.processing.context import WindowProcessingContext, PositionData
from src.components.processing.steps.base import ProcessingStep
from src.core.utils import ScaleConverter

logger = logging.getLogger("logger")


class CalculateWindowPositionStep(ProcessingStep):
    """Calculate window position in room coordinates (meters and pixels)"""

    def __init__(self, scale_converter: ScaleConverter):
        super().__init__()
        self.scale_converter = scale_converter

    def run(self, context: WindowProcessingContext) -> WindowProcessingContext:
        """Calculate window room coordinates and reference point"""
        logger.debug(f"Step 1: Calculating window position for '{context.input.window_id}'")

        # Get window reference point on room polygon (edge midpoint on room wall)
        room_coord_meters = context.input.window.reference_from_polygon(context.input.room_polygon)

        # Convert to room canvas coordinates (point_to_zero handles Y-flip to image coords)
        point_shifted = context.input.room_polygon.point_to_zero(room_coord_meters)
        if point_shifted.x is None or point_shifted.y is None:
            raise ValueError(
                f"Window {context.input.window_id}: point calculation returned None coordinates: "
                f"x={point_shifted.x}, y={point_shifted.y}"
            )

        room_coord_pixels = self.scale_converter.point_meters_to_pixels(point_shifted)
        if room_coord_pixels.x is None or room_coord_pixels.y is None:
            raise ValueError(
                f"Window {context.input.window_id}: point_meters_to_pixels returned None coordinates: "
                f"x={room_coord_pixels.x}, y={room_coord_pixels.y}"
            )

        # Get window reference point in 128x128 image
        ref_px_original = context.input.window.get_reference_pixel()

        context.position = PositionData(
            room_coord_meters=room_coord_meters,
            room_coord_pixels=room_coord_pixels,
            ref_px_original=ref_px_original
        )

        return context
