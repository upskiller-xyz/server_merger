"""
Window Aggregation Orchestrator

This module provides the WindowAggregationOrchestrator class that orchestrates
the processing of individual windows through a transformation pipeline.
"""

import numpy as np
import logging

from src.components.window import RoomPolygon, WindowGeometry
from src.server.services.df_aggregation_models import SimulationData, ProcessedWindow
from src.server.services.window_processor import WindowProcessor
from src.server.services.room_df_matrix import RoomDFMatrix
from src.server.services.scale_converter import ScaleConverter
from src.server.services.processing_steps import WindowProcessingPipeline


class WindowAggregationOrchestrator:
    """
    Orchestrates the processing and accumulation of window data.

    Delegates window transformation to a processing pipeline that implements
    the Chain of Responsibility pattern.
    """

    def __init__(self, window_processor: WindowProcessor, output_scale: float, logger: logging.Logger):
        """
        Initialize orchestrator.

        Args:
            window_processor: Window processor for transformations
            output_scale: Output scale in meters per pixel
            logger: Logger instance
        """
        self.logger = logger

        self.pipeline = WindowProcessingPipeline(
            window_processor=window_processor,
            scale_converter=ScaleConverter(output_scale),
            logger=logger
        )

    def process_and_accumulate_window(
        self,
        window_id: str,
        sim_data: SimulationData,
        room_original: RoomPolygon,
        df_matrix_container: RoomDFMatrix
    ) -> None:
        """
        Process a single window through the transformation pipeline and accumulate.

        Pipeline: window -> standardize -> rotate -> crop -> translate -> accumulate

        Args:
            window_id: Window identifier
            sim_data: Simulation data for this window
            room_original: Original room polygon
            df_matrix_container: Container for DF matrix accumulation
        """
        self.logger.info(f"Processing window '{window_id}'")
        self._log_window_metadata(sim_data.window)

        processed_window = self._transform_window_through_pipeline(
            window_id, sim_data, room_original
        )

        df_matrix_container.accumulate_window(
            processed_window.df_cropped,
            processed_window.mask_cropped,
            processed_window.translation,
            window_id
        )

    def _transform_window_through_pipeline(
        self,
        window_id: str,
        sim_data: SimulationData,
        room_original: RoomPolygon
    ) -> ProcessedWindow:
        """
        Transform window through the processing pipeline.

        Args:
            window_id: Window identifier
            sim_data: Simulation data
            room_original: Original room polygon

        Returns:
            ProcessedWindow with transformed data and translation
        """
        context = self.pipeline.process(
            window_id=window_id,
            window=sim_data.window,
            df_values=sim_data.df_values,
            mask=sim_data.mask,
            room_polygon=room_original
        )

        return ProcessedWindow(
            df_cropped=context.original_images.df_values,
            mask_cropped=context.original_images.mask,
            translation=context.translation
        )

    def _log_window_metadata(self, window: WindowGeometry) -> None:
        """Log window metadata for debugging."""
        self.logger.debug(
            f"  Window bounding box: ({window.x1:.2f}, {window.y1:.2f}) "
            f"to ({window.x2:.2f}, {window.y2:.2f})"
        )
        if window.direction_angle:
            self.logger.debug(
                f"  Window direction: {window.direction_angle:.4f} rad "
                f"({np.degrees(window.direction_angle):.2f}deg)"
            )
