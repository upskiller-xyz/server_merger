"""Service for handling DF aggregation requests"""

from typing import Any, Dict, List
import numpy as np
import cv2
import logging

from src.core.enums import AggregationConstants
from src.core.graphics_constants import GRAPHICS_CONSTANTS
from src.components.window import RoomPolygon, WindowGeometry
from src.components.aggregation import RoomDFAggregator
from src.models import ImageScale, SimulationData, AggregationResponse

logger = logging.getLogger("logger")


class DFAggregationService:
    """Service for handling DF aggregation requests"""

    def __init__(self, output_scale: float = AggregationConstants.DEFAULT_OUTPUT_SCALE):
        """
        Initialize service.

        Args:
            output_scale: Output scale in meters per pixel
        """
        self.output_scale = output_scale
        self.aggregator = RoomDFAggregator(output_scale)

    def process_request(
        self,
        room_polygon: List[List[float]],
        windows_data: Dict[str, dict],
        simulations: Dict[str, dict]
    ) -> Dict[str, Any]:
        """
        Process aggregation request.

        Args:
            room_polygon: Room polygon coordinates
            windows_data: Dictionary of window definitions
            simulations: Dictionary of simulation data (df_values, mask per window)

        Returns:
            Dictionary containing result and mask as lists
        """
        sim_objects = self._create_simulation_objects(windows_data, simulations)
        room_poly = RoomPolygon([(x[0], x[1]) for x in room_polygon])

        df_matrix, room_mask = self.aggregator.aggregate(room_poly, sim_objects)
        logger.info("Aggregation complete")

        return AggregationResponse.from_arrays(df_matrix, room_mask).to_dict()

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

        window = WindowGeometry.from_dict(windows_data[window_id])

        df_values = np.array(sim_dict['df_values'], dtype=np.float32)
        mask = np.array(sim_dict['mask'], dtype=np.uint8)

        if df_values.shape != mask.shape:
            logger.warning(
                f"Window {window_id}: df_values shape {df_values.shape} "
                f"does not match mask shape {mask.shape}. Resizing both to 128x128."
            )
            df_values = self._resize(df_values)
            mask = self._resize(mask)

        img_size = df_values.shape[0]
        scale = ImageScale.from_image_size(img_size)

        return SimulationData(
            df_values=df_values,
            mask=mask,
            window=window,
            scale=scale
        )

    def _resize(self, arr) -> np.ndarray:
        target_size = (GRAPHICS_CONSTANTS.BASE_IMAGE_SIZE_PX, GRAPHICS_CONSTANTS.BASE_IMAGE_SIZE_PX)
        return cv2.resize(arr, target_size, interpolation=cv2.INTER_NEAREST)
