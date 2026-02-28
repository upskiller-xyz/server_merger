"""
Room DF Matrix Management

This module provides the RoomDFMatrix class for managing the room daylight factor matrix.
"""

from typing import Tuple
import numpy as np
import logging

from src.core.enums import AggregationConstants
from src.components.geometry_ops import Point2D
from src.models.overlap_region import OverlapRegion, Region

logger = logging.getLogger("logger")

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
        self.room_mask = np.ones((height_px, width_px), dtype=np.float32)
        self.width_px = width_px
        self.height_px = height_px

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

        # Calculate overlap regions between window and room
        region = self._calculate_overlap_regions(
            window_width, window_height, offset_x, offset_y
        )

        logger.debug(
            f"  Window '{window_id}': offset=({offset_x}, {offset_y}), "
            f"size={window_width}x{window_height}"
        )

        if region.src_height <= AggregationConstants.ZERO_VALUE or region.src_width <= AggregationConstants.ZERO_VALUE:
            logger.warning(f"  No valid overlap region for '{window_id}' (size: {region.src_height}x{region.src_width})")
            return

        # Crop and place window DF values
        df_placed = self.crop_and_place(
            values=df_window,
            src_region=region.src,
            dest_region=region.dest,
            offset=Point2D(x=0, y=0)  # Already positioned by region calculation
        )
        
        # Crop and place window mask
        mask_placed = self.crop_and_place(
            values=mask_window,
            src_region=region.src,
            dest_region=region.dest,
            offset=Point2D(x=0, y=0)  # Already positioned by region calculation
        )
        
        # Apply mask to DF values
        masked_values = df_placed * mask_placed

        logger.info(
            f"  Window '{window_id}': adding {np.count_nonzero(mask_placed)} masked pixels, "
            f"DF contribution sum: {masked_values.sum():.4f}"
        )

        # Accumulate into room matrix at destination position
        self.df_matrix[
            region.dest.y_start:region.dest.y_end,
            region.dest.x_start:region.dest.x_end
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

        Args:
            window_width: Width of window image
            window_height: Height of window image
            offset_x: X offset for placement
            offset_y: Y offset for placement

        Returns:
            OverlapRegion with source and destination Region objects
        """
        src_region = Region(
            y_start=AggregationConstants.ZERO_VALUE,
            y_end=min(window_height, self.height_px + offset_y),
            x_start=AggregationConstants.ZERO_VALUE,
            x_end=min(window_width - 1, self.width_px + offset_x)
        )
        dest_region = Region(
            y_start=max(AggregationConstants.ZERO_VALUE, -offset_y),
            y_end=self.height_px, #offset_y + window_height),
            x_start=max(AggregationConstants.ZERO_VALUE, -offset_x),
            x_end=self.width_px  #, offset_x + window_width)
        )
        
        return OverlapRegion(src=src_region, dest=dest_region)

    def apply_mask(self) -> None:
        """Apply room mask to final result."""
        if self.room_mask is not None:
            self.df_matrix *= self.room_mask
            logger.info("Room mask applied to DF matrix")

    def get_result(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Get final DF matrix and room mask.

        Returns:
            (df_matrix, room_mask): Final aggregated result
        """
        return self.df_matrix, self.room_mask
    
    def _flip(self, arr: np.ndarray) -> np.ndarray:
        return np.flipud(arr)
    
    def get_flipped(self) -> Tuple[np.ndarray, np.ndarray]:
        return (self._flip(self.df_matrix), self._flip(self.room_mask))

    @staticmethod
    def crop_and_place(
        values: np.ndarray,
        src_region: Region,
        dest_region: Region,
        offset: Point2D
    ) -> np.ndarray:
        """
        Crop values using source region and place in output of destination region size.
        
        Extracts a portion of the input array defined by src_region coordinates,
        then places it in an output array of dest_region size at the position
        specified by the offset. Areas without data are padded with zeros.
        
        Args:
            values: Input array to crop from
            src_region: Region defining coordinates to crop from input array
            dest_region: Region defining shape of output array
            offset: Point2D indicating where to place the cropped data in the output.
                    Positive offset means data is offset to right/down.
                    Negative offset means data starts outside the top-left corner.
        
        Returns:
            Array of shape (dest_region.height, dest_region.width) with cropped data
            placed at offset position and remaining areas zero-filled.
        """
        # Crop from source array using source region coordinates
        cropped = values[
            src_region.y_start:src_region.y_end,
            src_region.x_start:src_region.x_end
        ]
        
        # Create output array with destination region size, zero-filled
        output = np.zeros(
            (dest_region.height, dest_region.width),
            dtype=values.dtype
        )
        
        offset_y = int(offset.y)
        offset_x = int(offset.x)
        
        # Determine placement bounds in output array
        out_y_start = max(0, offset_y)
        out_x_start = max(0, offset_x)
        out_y_end = min(dest_region.height, offset_y + cropped.shape[0])
        out_x_end = min(dest_region.width, offset_x + cropped.shape[1])
        
        # Check if there's any valid overlap region
        if out_y_start >= out_y_end or out_x_start >= out_x_end:
            logger.debug(
                f"No overlap when placing at offset ({offset_x}, {offset_y}) "
                f"with cropped size {cropped.shape} into dest region "
                f"({dest_region.height}, {dest_region.width})"
            )
            return output
        
        # Determine corresponding source bounds in cropped array
        # (handles case where offset is negative, clipping from cropped data)
        src_y_start = max(0, -offset_y)
        src_x_start = max(0, -offset_x)
        src_y_end = src_y_start + (out_y_end - out_y_start)
        src_x_end = src_x_start + (out_x_end - out_x_start)
        
        # Place cropped data at offset position in output
        output[out_y_start:out_y_end, out_x_start:out_x_end] = cropped[
            src_y_start:src_y_end,
            src_x_start:src_x_end
        ]
        
        return output
