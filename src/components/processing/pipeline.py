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
from src.core.utils import ScaleConverter, ImageSaver


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

        # Save original images
        ImageSaver.save_step(df_values, mask, window_id, "00_original", 0)

        for idx, step in enumerate(self.steps, start=1):
            context = step.run(context)
            
            # Save after each step
            self._save_context_state(context, window_id, idx)

        return context
    
    def _save_context_state(
        self,
        context: WindowProcessingContext,
        window_id: str,
        step_number: int
    ) -> None:
        """
        Save the current context state to images.
        
        Args:
            context: Processing context
            window_id: Window identifier
            step_number: Step number in pipeline
        """
        ImageSaver.save_context_state(context, window_id, step_number)

