"""
Room DF Matrix Management

This module provides the RoomDFMatrix class for managing the room daylight factor matrix.
"""

from typing import Tuple
import numpy as np
import logging

from src.components.enums import AggregationConstants
from src.components.geometry_ops import Point2D
from src.server.services.df_aggregation_models import OverlapRegion


class RoomDFMatrix:
    """
    Encapsulates the room DF matrix and room mask.
    Handles accumulation of window contributions.
    """

    def __init__(self, width_px: int, height_px: int):
        """
        Initialize room DF matrix.

        Args:
            width_px: Width of room in pixels
            height_px: Height of room in pixels
        """
        self.df_matrix = np.zeros((height_px, width_px), dtype=np.float32)
        self.room_mask = None
        self.width_px = width_px
        self.height_px = height_px
        self.logger = logging.getLogger(self.__class__.__name__)

    def set_mask(self, mask: np.ndarray) -> None:
        """Set the room mask."""
        if mask.shape != (self.height_px, self.width_px):
            raise ValueError(
                f"Mask shape {mask.shape} does not match matrix shape "
                f"({self.height_px}, {self.width_px})"
            )
        self.room_mask = mask

    def accumulate_window(
        self,
        df_window: np.ndarray,
        mask_window: np.ndarray,
        translation: Point2D,
        window_id: str
    ) -> None:
        """
        Place window contribution onto room canvas at correct position and accumulate.

        Args:
            df_window: Cropped window DF values
            mask_window: Cropped window mask
            translation: Translation to apply
            window_id: Window identifier for logging
        """
        window_height, window_width = df_window.shape
        self._validate_translation(translation, window_id)

        offset_y, offset_x = int(translation.y), int(translation.x)

        region = self._calculate_overlap_regions(
            window_width, window_height, offset_x, offset_y
        )

        self.logger.debug(
            f"  Window '{window_id}': offset=({offset_x}, {offset_y}), "
            f"size={window_width}x{window_height}"
        )

        if region.src_height != region.dst_height or region.src_width != region.dst_width:
            self.logger.warning(
                f"  Region size mismatch for '{window_id}': "
                f"src={region.src_height}x{region.src_width}, "
                f"dst={region.dst_height}x{region.dst_width}"
            )
            return

        if region.src_height <= AggregationConstants.ZERO_VALUE or region.src_width <= AggregationConstants.ZERO_VALUE:
            self.logger.warning(f"  No valid overlap region for '{window_id}' (size: {region.src_height}x{region.src_width})")
            return

        window_region_df = df_window[
            region.src_y_start:region.src_y_end,
            region.src_x_start:region.src_x_end
        ]
        window_region_mask = mask_window[
            region.src_y_start:region.src_y_end,
            region.src_x_start:region.src_x_end
        ]

        masked_values = window_region_df * window_region_mask

        self.logger.info(
            f"  Window '{window_id}': adding {np.count_nonzero(window_region_mask)} masked pixels, "
            f"DF contribution sum: {masked_values.sum():.4f}"
        )

        self.df_matrix[
            region.dst_y_start:region.dst_y_end,
            region.dst_x_start:region.dst_x_end
        ] += masked_values

    def _validate_translation(self, translation: Point2D, window_id: str) -> None:
        """
        Validate translation values are numeric and not None/NaN.

        Args:
            translation: Translation point to validate
            window_id: Window identifier for error messages

        Raises:
            ValueError: If translation contains None, NaN, or non-numeric values
        """
        if translation.y is None or translation.x is None:
            raise ValueError(
                f"Translation contains None: x={translation.x}, y={translation.y} for window {window_id}"
            )

        try:
            if np.isnan(translation.y) or np.isnan(translation.x):
                raise ValueError(
                    f"Translation contains NaN: x={translation.x}, y={translation.y} for window {window_id}"
                )
        except TypeError:
            raise ValueError(
                f"Translation contains invalid type: x={translation.x} (type: {type(translation.x)}), "
                f"y={translation.y} (type: {type(translation.y)}) for window {window_id}"
            )

    def _calculate_overlap_regions(
        self,
        window_width: int,
        window_height: int,
        offset_x: int,
        offset_y: int
    ) -> OverlapRegion:
        """
        Calculate overlap regions between window and room.

        Inverted convention: positive offset = skip source rows/cols.

        Args:
            window_width: Width of window image
            window_height: Height of window image
            offset_x: X offset for source window
            offset_y: Y offset for source window

        Returns:
            OverlapRegion with source and destination boundaries
        """
        src_y_start = max(AggregationConstants.ZERO_VALUE, offset_y)
        src_y_end = min(window_height, self.height_px + offset_y)
        dst_y_start = max(AggregationConstants.ZERO_VALUE, -offset_y)
        dst_y_end = dst_y_start + (src_y_end - src_y_start)

        src_x_start = max(AggregationConstants.ZERO_VALUE, offset_x)
        src_x_end = min(window_width, self.width_px + offset_x)
        dst_x_start = max(AggregationConstants.ZERO_VALUE, -offset_x)
        dst_x_end = dst_x_start + (src_x_end - src_x_start)

        return OverlapRegion(
            src_y_start=src_y_start,
            src_y_end=src_y_end,
            src_x_start=src_x_start,
            src_x_end=src_x_end,
            dst_y_start=dst_y_start,
            dst_y_end=dst_y_end,
            dst_x_start=dst_x_start,
            dst_x_end=dst_x_end
        )

    def apply_mask(self) -> None:
        """Apply room mask to final result."""
        if self.room_mask is not None:
            self.df_matrix *= self.room_mask
            self.logger.info("Room mask applied to DF matrix")

    def get_result(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Get final DF matrix and room mask.

        Returns:
            (df_matrix, room_mask): Final aggregated result
        """
        return self.df_matrix, self.room_mask
