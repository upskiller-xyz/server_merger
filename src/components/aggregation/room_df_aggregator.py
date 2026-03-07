"""
Room Daylight Factor Aggregator

Aggregates daylight factor values from multiple windows into room polygon.
"""

from typing import Dict, Optional, Tuple
import numpy as np
import logging

from src.core.enums import AggregationConstants
from src.components.polygon_rasterizer import PolygonRasterizer
from src.components.window import RoomPolygon
from src.models import SimulationData, RoomDFMatrix
from src.components.processing.window_processor import WindowProcessor
from src.components.processing.window_aggregation_orchestrator import WindowAggregationOrchestrator

logger = logging.getLogger("logger")


class RoomDFAggregator:
    """
    Aggregates daylight factor values from multiple windows into room polygon.

    Uses constants and geometry operations from the encoding components to ensure
    consistency between encoding and decoding operations.
    """

    def __init__(
        self,
        output_scale: float = AggregationConstants.DEFAULT_OUTPUT_SCALE,
        orchestrator: Optional[WindowAggregationOrchestrator] = None
    ):
        """
        Initialize aggregator.

        Args:
            output_scale: Output scale in meters per pixel (default: 0.1m/px)
            orchestrator: Optional orchestrator (will create default if not provided)
        """
        self.output_scale = output_scale
        self.polygon_rasterizer = PolygonRasterizer()

        if orchestrator is None:
            window_processor = WindowProcessor()
            self.orchestrator = WindowAggregationOrchestrator(
                window_processor, self.output_scale
            )
        else:
            self.orchestrator = orchestrator

    def aggregate(
        self,
        room_polygon: RoomPolygon,
        simulations: Dict[str, SimulationData]
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Aggregate DF values from multiple window simulations into room polygon.

        Algorithm:
        1. Calculate room bounds and create room image
        2. Process each window: standardize, rotate, crop
        3. Accumulate window contributions to room matrix
        4. Apply room mask to final result

        Args:
            room_polygon: RoomPolygon instance defining room polygon in meters
            simulations: Dictionary mapping window IDs to SimulationData

        Returns:
            (df_matrix, room_mask):
                - df_matrix: 2D array of aggregated DF values
                - room_mask: Binary mask of room polygon
        """
        room_original = room_polygon
        room_translated = room_original.shift_to_zero()

        room_width_px = int(np.ceil(room_original.width / self.output_scale))
        room_height_px = int(np.ceil(room_original.height / self.output_scale))

        df_matrix_container = RoomDFMatrix(room_width_px, room_height_px)

        # Create room mask in image coords (Y-down).
        # PolygonRasterizer already flips Y internally, matching point_to_zero() convention.
        room_mask = self._create_room_mask(room_translated, room_width_px, room_height_px)
        df_matrix_container.set_mask(room_mask)

        for window_id, sim_data in simulations.items():
            self.orchestrator.process_and_accumulate_window(
                window_id, sim_data, room_original, df_matrix_container
            )

        logger.info(f"All {len(simulations)} windows processed")

        df_matrix_container.apply_mask()
        
        # Frontend maps row 0 -> minY (Y-up convention), so we flip the output.

        return df_matrix_container.get_result() #.get_flipped()

    def _create_room_mask(
        self,
        room_translated: RoomPolygon,
        width_px: int,
        height_px: int
    ) -> np.ndarray:
        """
        Create room mask from translated polygon.

        PolygonRasterizer handles the Y-flip from world coords (Y-up) to
        image coords (Y-down) internally, so we pass coords as-is.

        Args:
            room_translated: Room polygon shifted to zero (Y-up world coords)
            width_px: Width in pixels
            height_px: Height in pixels

        Returns:
            Binary room mask in image coordinates (Y-down)
        """
        return self.polygon_rasterizer.rasterize(
            room_translated.get_coords(), # type: ignore
            width_px,
            height_px,
            self.output_scale
        )
