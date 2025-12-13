"""
Daylight Factor Aggregation Service

This module provides the main aggregation service for combining daylight factor (DF)
simulation results from multiple windows into a single room polygon representation.

"""

from typing import Dict, List, Tuple
from pathlib import Path
import numpy as np
import logging

from src.components.enums import AggregationConstants, ParameterName
from src.components.geometry_ops import Point2D
from src.components.polygon_rasterizer import PolygonRasterizer
from src.components.window import RoomPolygon, WindowGeometry
from src.server.services.df_aggregation_models import ImageScale, SimulationData
from src.server.services.room_df_matrix import RoomDFMatrix
from src.server.services.window_processor import WindowProcessor
from src.server.services.window_aggregation_orchestrator import WindowAggregationOrchestrator


class RoomDFAggregator:
    """
    Aggregates daylight factor values from multiple windows into room polygon.

    Uses constants and geometry operations from the encoding components to ensure
    consistency between encoding and decoding operations.
    """

    def __init__(
        self,
        output_scale: float = AggregationConstants.DEFAULT_OUTPUT_SCALE,
        debug_dir: str = AggregationConstants.DEFAULT_DEBUG_DIR,
        orchestrator: WindowAggregationOrchestrator = None
    ):
        """
        Initialize aggregator.

        Args:
            output_scale: Output scale in meters per pixel (default: 0.1m/px)
            debug_dir: Directory to save debug images
            orchestrator: Optional orchestrator (will create default if not provided)
        """
        self.output_scale = output_scale
        self.polygon_rasterizer = PolygonRasterizer()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.debug_dir = Path(debug_dir)
        self.debug_dir.mkdir(parents=True, exist_ok=True)

        # Initialize orchestrator via dependency injection
        if orchestrator is None:
            window_processor = WindowProcessor(self.debug_dir, self.logger)
            self.orchestrator = WindowAggregationOrchestrator(
                window_processor, self.output_scale, self.logger
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
        # Step 1: Calculate room bounds and create room image
        room_original = room_polygon
        room_translated = room_original.shift_to_zero()

        room_width_px = int(np.ceil(room_original.width / self.output_scale))
        room_height_px = int(np.ceil(room_original.height / self.output_scale))

        # Initialize room DF matrix
        df_matrix_container = RoomDFMatrix(room_width_px, room_height_px)

        # Create room mask
        room_mask = self._create_room_mask(room_translated, room_width_px, room_height_px)
        df_matrix_container.set_mask(room_mask)

        # Step 2-3: Process each window and accumulate (using orchestrator)
        list(map(
            lambda item: self.orchestrator.process_and_accumulate_window(
                item[0], item[1], room_original, df_matrix_container
            ),
            simulations.items()
        ))

        # Step 4: Apply room mask to final result
        df_matrix_container.apply_mask()

        return df_matrix_container.get_result()

    def _create_room_mask(
        self,
        room_translated: RoomPolygon,
        width_px: int,
        height_px: int
    ) -> np.ndarray:
        """
        Create room mask from translated polygon.

        Args:
            room_translated: Room polygon shifted to zero
            width_px: Width in pixels
            height_px: Height in pixels

        Returns:
            Binary room mask
        """
        return self.polygon_rasterizer.rasterize(
            room_translated.get_coords(),
            width_px,
            height_px,
            self.output_scale
        )


class DFAggregationService:
    """Service for handling DF aggregation requests"""

    def __init__(self, output_scale: float = AggregationConstants.DEFAULT_OUTPUT_SCALE):
        """
        Initialize service.

        Args:
            output_scale: Output scale in meters per pixel
        """
        self.aggregator = RoomDFAggregator(output_scale)

    def process_request(
        self,
        room_polygon: List[List[float]],
        windows_data: Dict[str, dict],
        simulations: Dict[str, dict]
    ) -> Dict[str, any]:
        """
        Process aggregation request.

        Args:
            room_polygon: Room polygon coordinates
            windows_data: Dictionary of window definitions
            simulations: Dictionary of simulation data (df_values, mask per window)

        Returns:
            Dictionary containing result and mask as lists
        """
        # Parse and create simulation data objects
        sim_objects = self._create_simulation_objects(windows_data, simulations)

        # Create RoomPolygon from coordinates
        room_poly = RoomPolygon([(x[0], x[1]) for x in room_polygon])

        # Aggregate
        df_matrix, room_mask = self.aggregator.aggregate(room_poly, sim_objects)

        # Convert to lists for JSON serialization
        return {
            'result': df_matrix.tolist(),
            'mask': room_mask.tolist()
        }

    def _create_simulation_objects(
        self,
        windows_data: Dict[str, dict],
        simulations: Dict[str, dict]
    ) -> Dict[str, SimulationData]:
        """
        Create simulation data objects from request data.

        Args:
            windows_data: Dictionary of window definitions
            simulations: Dictionary of simulation data

        Returns:
            Dictionary mapping window IDs to SimulationData objects
        """
        return {
            window_id: self._create_simulation_data(window_id, sim_dict, windows_data)
            for window_id, sim_dict in simulations.items()
        }

    def _create_simulation_data(
        self,
        window_id: str,
        sim_dict: dict,
        windows_data: Dict[str, dict]
    ) -> SimulationData:
        """
        Create a single SimulationData object.

        Args:
            window_id: Window identifier
            sim_dict: Simulation data dictionary
            windows_data: Dictionary of window definitions

        Returns:
            SimulationData object
        """
        if window_id not in windows_data:
            raise ValueError(f"Window {window_id} not found in windows_data")

        window_dict = windows_data[window_id]
        window = WindowGeometry(
            x1=window_dict[ParameterName.X1.value],
            y1=window_dict[ParameterName.Y1.value],
            z1=window_dict[ParameterName.Z1.value],
            x2=window_dict[ParameterName.X2.value],
            y2=window_dict[ParameterName.Y2.value],
            z2=window_dict[ParameterName.Z2.value],
            direction_angle=window_dict[ParameterName.DIRECTION_ANGLE.value]
        )

        # Parse simulation arrays (keys from API request)
        df_values = np.array(sim_dict['df_values'], dtype=np.float32)
        mask = np.array(sim_dict['mask'], dtype=np.uint8)

        # Validate dimensions match
        if df_values.shape != mask.shape:
            raise ValueError(
                f"Window {window_id}: df_values shape {df_values.shape} "
                f"does not match mask shape {mask.shape}. Both must be the same size."
            )

        # Calculate scale proportionally from image size
        img_size = df_values.shape[0]
        scale = ImageScale.from_image_size(img_size)

        return SimulationData(
            df_values=df_values,
            mask=mask,
            window=window,
            scale=scale
        )
