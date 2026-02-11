"""
Room DF Matrix Management

This module provides the RoomDFMatrix class for managing the room daylight factor matrix.
"""

from typing import Tuple, Optional
from pathlib import Path
import numpy as np
import logging
import cv2
import os

from src.components.enums import AggregationConstants
from src.components.geometry_ops import Point2D
from src.server.services.df_aggregation_models import OverlapRegion
logger = logging.Logger("logger")

class RoomDFMatrix:
    """
    Encapsulates the room DF matrix and room mask.
    Handles accumulation of window contributions.
    """

    def __init__(self, width_px: int, height_px: int, debug_dir: Optional[Path] = None):
        """
        Initialize room DF matrix.

        Args:
            width_px: Width of room in pixels
            height_px: Height of room in pixels
            debug_dir: Optional debug directory for saving intermediate images
        """
        self.df_matrix = np.zeros((height_px, width_px), dtype=np.float32)
        self.room_mask = None
        self.width_px = width_px
        self.height_px = height_px
        self.logger = logging.getLogger(self.__class__.__name__)
        self.debug_dir = debug_dir
        self.window_count = 0

    def set_mask(self, mask: np.ndarray) -> None:
        """Set the room mask."""
        if mask.shape != (self.height_px, self.width_px):
            raise ValueError(
                f"Mask shape {mask.shape} does not match matrix shape "
                f"({self.height_px}, {self.width_px})"
            )
        self.room_mask = mask

        self._save_debug_image(mask, "room_00_mask")

    def accumulate_window(
        self,
        df_window: np.ndarray,
        mask_window: np.ndarray,
        translation: Point2D,
        window_id: str,
        room_coord_pixels: Point2D = None
    ) -> None:
        """
        Place window contribution onto room canvas at correct position and accumulate.

        Args:
            df_window: Cropped window DF values
            mask_window: Cropped window mask
            translation: Translation to apply
            window_id: Window identifier for logging
            room_coord_pixels: Optional room coordinate for debug visualization
        """

        window_height, window_width = df_window.shape

        # Validate translation before converting to int
        if translation.y is None or translation.x is None:
            raise ValueError(
                f"Translation contains None: x={translation.x}, y={translation.y} for window {window_id}"
            )

        # Check for NaN using numpy
        try:
            if np.isnan(translation.y) or np.isnan(translation.x):
                raise ValueError(
                    f"Translation contains NaN: x={translation.x}, y={translation.y} for window {window_id}"
                )
        except TypeError:
            # If np.isnan fails, the value might be None or another non-numeric type
            raise ValueError(
                f"Translation contains invalid type: x={translation.x} (type: {type(translation.x)}), "
                f"y={translation.y} (type: {type(translation.y)}) for window {window_id}"
            )

        offset_y, offset_x = int(translation.y), int(translation.x)

        # Calculate overlap regions using helper
        region = self._calculate_overlap_regions(
            window_width, window_height, offset_x, offset_y
        )

        self.logger.debug(
            f"  Source region: [{region.src_y_start}:{region.src_y_end}, "
            f"{region.src_x_start}:{region.src_x_end}] = {region.src_height}x{region.src_width}"
        )
        self.logger.debug(
            f"  Dest region: [{region.dst_y_start}:{region.dst_y_end}, "
            f"{region.dst_x_start}:{region.dst_x_end}] = {region.dst_height}x{region.dst_width}"
        )
        self.logger.debug(
            f"  Window offsets: offset_x={offset_x}, offset_y={offset_y}"
        )
        self.logger.debug(
            f"  Window size: {window_width}x{window_height}"
        )
        self.logger.debug(
            f"  Reference in simulation would be at row: 64 in original 128x128 image"
        )
        self.logger.debug(
            f"  Reference in room should be at: offset_y + 64 = {offset_y} + 64 = {offset_y + 64}"
        )

        # Verify regions match
        if region.src_height != region.dst_height or region.src_width != region.dst_width:
            self.logger.warning(
                f"  Region size mismatch! src={region.src_height}x{region.src_width}, "
                f"dst={region.dst_height}x{region.dst_width}"
            )
            return

        # Only proceed if there's valid overlap
        if region.src_height > AggregationConstants.ZERO_VALUE and region.src_width > AggregationConstants.ZERO_VALUE:
            window_region_df = df_window[
                region.src_y_start:region.src_y_end,
                region.src_x_start:region.src_x_end
            ]
            window_region_mask = mask_window[
                region.src_y_start:region.src_y_end,
                region.src_x_start:region.src_x_end
            ]

            masked_values = window_region_df * window_region_mask
            contribution_sum = masked_values.sum()

            self.logger.info(
                f"  Adding {np.count_nonzero(window_region_mask)} masked pixels, "
                f"DF contribution sum: {contribution_sum:.4f}"
            )

            self.df_matrix[
                region.dst_y_start:region.dst_y_end,
                region.dst_x_start:region.dst_x_end
            ] += masked_values

            self.window_count += 1
            ref_for_debug = (int(room_coord_pixels.x), int(room_coord_pixels.y)) if room_coord_pixels else None
            self._save_debug_image(self.df_matrix, f"room_{self.window_count:02d}_after_{window_id}", ref_for_debug)
        else:
            self.logger.warning(f"  No valid overlap region (size: {region.src_height}x{region.src_width})")

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
        self.logger.info(self.room_mask is None)
        if self.room_mask is not None:
            self.logger.info(np.unique(self.df_matrix))
            self.logger.info(np.unique(self.room_mask))

            self._save_debug_image(self.df_matrix, "room_99_before_mask")

            self.df_matrix *= self.room_mask
            self.logger.info("multiplication succeeded")

            self._save_debug_image(self.df_matrix, "room_final_result")

    def get_result(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Get final DF matrix and room mask.

        Returns:
            (df_matrix, room_mask): Final aggregated result
        """
        return self.df_matrix, self.room_mask

    def _save_debug_image(self, img: np.ndarray, filename: str, ref_point: tuple = None) -> None:
        """
        Save debug image with room polygon outline and optional reference point.
        Only saves if DEBUG_SAVE_STEPS environment variable is set to 'true' or '1'.

        Args:
            img: Image array to save
            filename: Base filename (without extension)
            ref_point: Optional (x, y) to draw as red crosshair
        """
        debug_enabled = os.getenv('DEBUG_SAVE_STEPS', '').lower() in ('true', '1', 'yes')

        if not debug_enabled or self.debug_dir is None:
            return

        try:
            output_path = self.debug_dir / f"{filename}.png"

            # Normalize to 0-255 range for visualization
            if img.max() > 0:
                img_normalized = (img / img.max() * 255).astype(np.uint8)
            else:
                img_normalized = img.astype(np.uint8)

            # Convert to color to draw annotations
            img_color = cv2.cvtColor(img_normalized, cv2.COLOR_GRAY2BGR)

            # Draw room polygon outline in green
            if self.room_mask is not None:
                mask_uint8 = (self.room_mask * 255).astype(np.uint8)
                contours, _ = cv2.findContours(mask_uint8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                cv2.drawContours(img_color, contours, -1, (0, 255, 0), 1)

            # Draw reference point in red
            if ref_point is not None:
                x, y = int(ref_point[0]), int(ref_point[1])
                cv2.drawMarker(img_color, (x, y), (0, 0, 255), cv2.MARKER_CROSS, 10, 1)
                cv2.circle(img_color, (x, y), 3, (0, 0, 255), -1)

            cv2.imwrite(str(output_path), img_color)
            self.logger.debug(f"  [DEBUG] Saved aggregation image: {output_path}")
        except Exception as e:
            self.logger.warning(f"  Failed to save debug image {filename}: {e}")
