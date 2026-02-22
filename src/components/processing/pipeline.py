"""Window processing pipeline"""

import numpy as np

from src.components.window import WindowGeometry, RoomPolygon
from src.components.processing.context import WindowInputData, ImagePair, WindowProcessingContext
from src.components.processing.steps import (
    CalculateWindowPositionStep,
    StandardizeWindowStep,
    RotateWindowStep,
    CropWindowStep,
    CalculateTranslationStep,
)
from src.components.processing.window_processor import WindowProcessor
from src.core.utils import ScaleConverter


class WindowProcessingPipeline:
    """
    Pipeline that executes a sequence of processing steps.

    Implements the Pipeline pattern where each step operates on a shared context.
    """

    def __init__(
        self,
        window_processor: WindowProcessor,
        scale_converter: ScaleConverter
    ):
        """
        Initialize pipeline with dependencies.

        Args:
            window_processor: Window processor for transformations
            scale_converter: Scale converter for coordinate transformations
            logger: Logger instance
        """
        self.steps = [
            CalculateWindowPositionStep(scale_converter),
            StandardizeWindowStep(window_processor),
            RotateWindowStep(window_processor),
            CropWindowStep(window_processor),
            CalculateTranslationStep()
        ]

    def process(
        self,
        window_id: str,
        window: WindowGeometry,
        df_values: np.ndarray,
        mask: np.ndarray,
        room_polygon: RoomPolygon
    ) -> WindowProcessingContext:
        """
        Process window through the pipeline.

        Args:
            window_id: Window identifier
            window: Window geometry
            df_values: Original DF values
            mask: Original mask
            room_polygon: Room polygon

        Returns:
            Completed context with all processing results
        """
        context = WindowProcessingContext(
            input=WindowInputData(window_id, window, room_polygon),
            original_images=ImagePair(df_values, mask)
        )

        for step in self.steps:
            context = step.run(context)

        return context
