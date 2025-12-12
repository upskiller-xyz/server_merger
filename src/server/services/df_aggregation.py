"""
Daylight Factor Aggregation Service

This module provides classes for aggregating daylight factor (DF) simulation results
from multiple windows into a single room polygon representation.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Optional
from enum import Enum
from dataclasses import dataclass
from pathlib import Path
import cv2
import numpy as np
import math
import logging

from src.components.enums import AggregationConstants
from src.components.geometry_ops import GeometryOps, Point3D, Point2D
from src.components.graphics_constants import GRAPHICS_CONSTANTS
from src.components.polygon_rasterizer import PolygonRasterizer
from src.components.window import RoomPolygon, WindowGeometry

# Constants for image processing and file handling

@dataclass
class ImageScale:
    """
    Image scale configuration calculated proportionally from reference scale.
    Reference: 128x128 image with 0.1 m/px, window_offset = 12px
    """
    size: int
    meters_per_pixel: float

    @property
    def window_offset(self) -> int:
        """Calculate window offset proportionally from reference (12px at 128px)."""
        scale_factor = self.size / GRAPHICS_CONSTANTS.BASE_IMAGE_SIZE_PX
        return int(GRAPHICS_CONSTANTS.WINDOW_OFFSET_PX * scale_factor)

    @classmethod
    def from_image_size(cls, img_size: int) -> 'ImageScale':
        """
        Calculate scale proportionally based on reference (128px = 0.1m/px).

        Args:
            img_size: Size of the square image

        Returns:
            ImageScale instance with calculated meters_per_pixel
        """
        # Reference scale: 128px = 0.1 m/px
        scale_factor = img_size / GRAPHICS_CONSTANTS.BASE_IMAGE_SIZE_PX
        meters_per_pixel = GRAPHICS_CONSTANTS.BASE_RESOLUTION_M_PER_PX * scale_factor

        return cls(size=img_size, meters_per_pixel=meters_per_pixel)


# @dataclass
# class Window:
#     """Represents a window with its bounding box and direction"""
#     x1: float
#     y1: float
#     z1: float
#     x2: float
#     y2: float
#     z2: float
#     direction_angle: float

#     @property
#     def center_x(self) -> float:
#         return (self.x1 + self.x2) / AggregationConstants.DIVISION_BY_TWO

#     @property
#     def center_y(self) -> float:
#         return (self.y1 + self.y2) / AggregationConstants.DIVISION_BY_TWO

#     @property
#     def width(self) -> float:
#         return abs(self.x2 - self.x1)

#     @property
#     def height(self) -> float:
#         return abs(self.y2 - self.y1)


@dataclass
class SimulationData:
    """Represents simulation data for a window"""
    df_values: np.ndarray  # 2D array of DF values (0-10)
    mask: np.ndarray  # 2D binary mask (0 or 1)
    window: WindowGeometry
    scale: ImageScale


class CoordinateTransformer(ABC):
    """Abstract base class for coordinate transformations"""

    @abstractmethod
    def transform(self, x: float, y: float) -> Tuple[float, float]:
        """Transform coordinates"""
        pass


class WindowToRoomTransformer(CoordinateTransformer):
    """Transforms coordinates from window-relative to room coordinates"""

    def __init__(self, window: WindowGeometry, scale: ImageScale):
        self.window = window
        self.scale = scale

    def transform(self, pixel_x: int, pixel_y: int) -> Tuple[float, float]:
        """
        Transform pixel coordinates from simulation image to room coordinates.

        The window center (external face) is at:
        - Vertical: center of image
        - Horizontal: window_offset pixels from right edge

        Args:
            pixel_x: X coordinate in simulation image
            pixel_y: Y coordinate in simulation image

        Returns: 
            (room_x, room_y): Coordinates in room space (meters)
        """
        # Calculate offset from window center in pixels

        window_center = self._calc_offset()

        dx_pixels = pixel_x - window_center.x
        dy_pixels = pixel_y - window_center.y

        # Convert to meters
        dx_meters = dx_pixels * self.scale.meters_per_pixel
        dy_meters = dy_pixels * self.scale.meters_per_pixel

        # Rotate by window direction angle
        cos_angle = math.cos(math.radians(self.window.direction_angle))
        sin_angle = math.sin(math.radians(self.window.direction_angle))

        dx_rotated = dx_meters * cos_angle - dy_meters * sin_angle
        dy_rotated = dx_meters * sin_angle + dy_meters * cos_angle

        # Translate to room coordinates (relative to window center)
        room_x = self.window.center_x + dx_rotated
        room_y = self.window.center_y + dy_rotated

        return room_x, room_y
    
    def _calc_offset(self)->Point2D:
        _x = self.scale.size - self.scale.window_offset
        _y = self.scale.size / AggregationConstants.DIVISION_BY_TWO
        return Point2D(_x, _y)




class RoomDFAggregator:
    """
    Aggregates daylight factor values from multiple windows into room polygon.

    Uses constants and geometry operations from the encoding components to ensure
    consistency between encoding and decoding operations.
    """

    def __init__(
        self,
        output_scale: float = AggregationConstants.DEFAULT_OUTPUT_SCALE,
        debug_dir: str = AggregationConstants.DEFAULT_DEBUG_DIR
    ):
        """
        Initialize aggregator.

        Args:
            output_scale: Output scale in meters per pixel (default: 0.1m/px)
            debug_dir: Directory to save debug images
        """
        self.output_scale = output_scale
        self.polygon_rasterizer = PolygonRasterizer()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.debug_dir = Path(debug_dir)
        self.debug_dir.mkdir(parents=True, exist_ok=True)

    def _calculate_window_ref_pixel(self, window: WindowGeometry) -> Tuple[int, int]:
        """
        Calculate window reference point in pixel coordinates of the 128x128 image.

        Following DECODING_GUIDE Step 1:
        The window reference point is at the room-facing edge (room facade).
        Formula: room_facade_x = IMAGE_SIZE - WINDOW_OFFSET_PX - wall_thickness_px - ROOM_FACADE_OFFSET_PX

        Args:
            window: Window object with geometry

        Returns:
            (ref_x, ref_y) in pixels
        """
        # Calculate wall thickness using GeometryOps
        p1 = Point3D(window.x1, window.y1, window.z1)
        p2 = Point3D(window.x2, window.y2, window.z2)
        wall_thickness_m = GeometryOps.projection_dist(p1, p2, window.direction_angle)

        # Convert to pixels
        wall_thickness_px = int(wall_thickness_m / GRAPHICS_CONSTANTS.BASE_RESOLUTION_M_PER_PX)

        # Calculate room facade position
        room_facade_x = (
            GRAPHICS_CONSTANTS.BASE_IMAGE_SIZE_PX -
            GRAPHICS_CONSTANTS.WINDOW_OFFSET_PX -
            wall_thickness_px -
            GRAPHICS_CONSTANTS.ROOM_FACADE_OFFSET_PX
        )

        # Reference point is at vertical center
        ref_y = GRAPHICS_CONSTANTS.BASE_IMAGE_SIZE_PX // 2

        self.logger.debug(f"  Wall thickness: {wall_thickness_m:.3f}m = {wall_thickness_px}px")
        self.logger.debug(f"  Window reference in 128x128 image: ({room_facade_x}, {ref_y})")

        return (room_facade_x, ref_y)

    def aggregate(
        self,
        room_polygon: List[Tuple[float, float]],
        simulations: Dict[str, SimulationData]
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Aggregate DF values from multiple window simulations into room polygon.

        Algorithm:
        1. Plot room polygon on image (scale 1px=0.1m, cropped to room extents)
        2. Standardize all window images to 128x128px at 0.1m/px scale
        3. Rotate each window image and mask by direction_angle
        4. Calculate window reference point position after rotation
        5. Map window reference point to room image coordinates
        6. Place rotated window image on room-sized canvas at correct position
        7. Sum all window contributions

        Args:
            room_polygon: List of [x, y] coordinates defining room polygon in meters
            simulations: Dictionary mapping window IDs to SimulationData

        Returns:
            (df_matrix, room_mask):
                - df_matrix: 2D array of aggregated DF values
                - room_mask: Binary mask of room polygon
        """

        # Step 1: Calculate room bounds and create room image
        polygon_array = np.array(room_polygon)
        vertices = [([x[0], x[1]]) for x in room_polygon]
        room_original = RoomPolygon(vertices)
        room_translated = room_original.shift_to_zero()
        # min_x, min_y = polygon_array.min(axis=0)
        # max_x, max_y = polygon_array.max(axis=0)

        # # Calculate room dimensions in pixels
        room_width_px = int(np.ceil(room_original.width / self.output_scale))
        room_height_px = int(np.ceil(room_original.height / self.output_scale))

        # self.logger.info(f"Room bounds: ({min_x:.2f}, {min_y:.2f}) to ({max_x:.2f}, {max_y:.2f}) meters")
        # self.logger.info(f"Room dimensions: {room_width_px}x{room_height_px} pixels at {self.output_scale}m/px")

        # Initialize room DF matrix
        df_matrix = np.zeros((room_height_px, room_width_px), dtype=np.float32)

        # Create room mask
        room_mask = self.polygon_rasterizer.rasterize(
            room_translated.get_coords(),
            room_width_px,
            room_height_px,
            self.output_scale
        )

        # Process each window simulation
        for window_id, sim_data in simulations.items():
            self.logger.info(f"Processing window '{window_id}'")
            self.logger.debug(f"  Window bounding box: ({sim_data.window.x1:.2f}, {sim_data.window.y1:.2f}) to ({sim_data.window.x2:.2f}, {sim_data.window.y2:.2f})")
            if sim_data.window.direction_angle:
                self.logger.debug(f"  Window direction: {sim_data.window.direction_angle:.4f} rad ({np.degrees(sim_data.window.direction_angle):.2f}°)")

            window = sim_data.window
            window_room_coord = room_original.point_to_zero(window.reference_from_polygon(room_original))

            print("window room coordinate", window_room_coord)
            # correct
            window_room_coord_px = Point2D(np.round(window_room_coord.x / self.output_scale), np.round(window_room_coord.y / self.output_scale))
            # Calculate window reference point in the 128x128 image (room facade position)
            print("window room coordinate px", window_room_coord_px)
            window_ref_px = self._calculate_window_ref_pixel(sim_data.window)

            # Step 2: Standardize window images to 128x128
            df_std, mask_std = self._standardize_window_images(
                sim_data.df_values,
                sim_data.mask,
                window_id
            )

            # Step 3: Rotate images by direction_angle
            df_rotated, mask_rotated, window_ref_px_rotated = self._rotate_window_images(
                df_std,
                mask_std,
                window_ref_px,
                -sim_data.window.direction_angle,
                window_id
            )
            print("window room coordinate px not rotated", window_ref_px)
            print("window room coordinate px ROTATED", window_ref_px_rotated)
            # Step 4: Crop to visible bounds
            df_cropped, mask_cropped, crop_offset = self._crop_to_visible_bounds(
                df_rotated,
                mask_rotated,
                window_id
            )
            min_x, min_y, _, _ = room_original.get_bounds()
            # Step 5-7: Place window on room canvas and accumulate
            translation = Point2D(
                window_room_coord_px.x - window_ref_px_rotated[0] + crop_offset[0],
                window_room_coord_px.y - window_ref_px_rotated[1] + crop_offset[1]
            )
            print("translation", translation)
            self._place_window_on_room(
                df_matrix,
                df_cropped,
                mask_cropped,
                translation,
                sim_data.window,
                window_id
            )

        # Apply room mask to final result
        df_matrix *= room_mask

        return df_matrix, room_mask

    def _standardize_window_images(
        self,
        df_values: np.ndarray,
        mask: np.ndarray,
        window_id: str
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Standardize window images to 128x128 at 0.1m/px scale.

        Args:
            df_values: Input DF values array
            mask: Input mask array
            window_id: Window identifier for logging

        Returns:
            (df_standardized, mask_standardized): Both at 128x128 resolution
        """
        current_size = df_values.shape[0]

        self.logger.debug(f"  Input DF shape: {df_values.shape}, range: [{df_values.min():.4f}, {df_values.max():.4f}]")
        self.logger.debug(f"  Input mask shape: {mask.shape}, unique values: {np.unique(mask)}")

        # Save original images
        self._save_debug_image(
            df_values,
            AggregationConstants.DEBUG_FILE_PATTERN_INPUT_DF.format(window_id=window_id)
        )
        self._save_debug_image(
            mask * AggregationConstants.GRAYSCALE_MAX,
            AggregationConstants.DEBUG_FILE_PATTERN_INPUT_MASK.format(window_id=window_id)
        )
        self._save_debug_image(
            df_values * mask,
            AggregationConstants.DEBUG_FILE_PATTERN_INPUT_MASKED.format(window_id=window_id)
        )

        if current_size == GRAPHICS_CONSTANTS.BASE_IMAGE_SIZE_PX:
            self.logger.debug(f"  Already at standard size {GRAPHICS_CONSTANTS.BASE_IMAGE_SIZE_PX}x{GRAPHICS_CONSTANTS.BASE_IMAGE_SIZE_PX}, skipping resize")
            return df_values.copy(), mask.copy()

        self.logger.info(f"  Resizing from {current_size}x{current_size} to {GRAPHICS_CONSTANTS.BASE_IMAGE_SIZE_PX}x{GRAPHICS_CONSTANTS.BASE_IMAGE_SIZE_PX}")


        interpolation = cv2.INTER_NEAREST

        df_std = cv2.resize(
            df_values,
            (GRAPHICS_CONSTANTS.BASE_IMAGE_SIZE_PX, GRAPHICS_CONSTANTS.BASE_IMAGE_SIZE_PX),
            interpolation=interpolation
        )
        mask_std = cv2.resize(
            mask,
            (GRAPHICS_CONSTANTS.BASE_IMAGE_SIZE_PX, GRAPHICS_CONSTANTS.BASE_IMAGE_SIZE_PX),
            interpolation=interpolation
        )

        self.logger.debug(f"  After resize - DF range: [{df_std.min():.4f}, {df_std.max():.4f}]")
        self.logger.debug(f"  After resize - Mask unique: {np.unique(mask_std)}")

        # Save resized images
        self._save_debug_image(
            df_std,
            AggregationConstants.DEBUG_FILE_PATTERN_RESIZED_DF.format(window_id=window_id)
        )
        self._save_debug_image(
            mask_std * AggregationConstants.GRAYSCALE_MAX,
            AggregationConstants.DEBUG_FILE_PATTERN_RESIZED_MASK.format(window_id=window_id)
        )
        self._save_debug_image(
            df_std * mask_std,
            AggregationConstants.DEBUG_FILE_PATTERN_RESIZED_MASKED.format(window_id=window_id)
        )

        return df_std, mask_std

    def _rotate_window_images(
        self,
        df_values: np.ndarray,
        mask: np.ndarray,
        window_ref_px: Tuple[int, int],
        direction_angle: float,
        window_id: str
    ) -> Tuple[np.ndarray, np.ndarray, Tuple[int, int]]:
        """
        Rotate window images by direction_angle (in radians) and also rotate the reference point.

        Args:
            df_values: Standardized DF values (128x128)
            mask: Standardized mask (128x128)
            window_ref_px: Reference point in original image (x, y)
            direction_angle: Rotation angle in radians
            window_id: Window identifier for logging

        Returns:
            (df_rotated, mask_rotated, ref_rotated): Rotated images and rotated reference point
        """
        # Convert radians to degrees for OpenCV
        angle_deg = np.degrees(direction_angle)

        self.logger.info(f"  Rotating by {direction_angle:.4f} rad ({angle_deg:.2f}°)")

        # Get rotation matrix around center
        center = (
            df_values.shape[1] / AggregationConstants.DIVISION_BY_TWO,
            df_values.shape[0] / AggregationConstants.DIVISION_BY_TWO
        )
        rotation_matrix = cv2.getRotationMatrix2D(center, -angle_deg, AggregationConstants.ROTATION_SCALE)

        self.logger.debug(f"  Rotation center: {center}")

        # Rotate DF values with linear interpolation
        df_rotated = cv2.warpAffine(
            df_values,
            rotation_matrix,
            (df_values.shape[1], df_values.shape[0]),
            flags=cv2.INTER_NEAREST,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=AggregationConstants.ZERO_VALUE
        )

        # Rotate mask with nearest neighbor
        mask_rotated = cv2.warpAffine(
            mask.astype(np.uint8),
            rotation_matrix,
            (mask.shape[1], mask.shape[0]),
            flags=cv2.INTER_NEAREST,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=AggregationConstants.ZERO_VALUE
        )

        # Rotate the reference point using the same rotation matrix
        # rotation_matrix is [2x3]: [[a, b, tx], [c, d, ty]]
        # new_point = rotation_matrix @ [x, y, 1]
        ref_x, ref_y = window_ref_px
        ref_point_homogeneous = np.array([ref_x, ref_y, AggregationConstants.ROTATION_SCALE])
        ref_rotated_xy = rotation_matrix @ ref_point_homogeneous
        ref_rotated = (int(round(ref_rotated_xy[0])), int(round(ref_rotated_xy[1])))

        self.logger.debug(f"  After rotation - DF range: [{df_rotated.min():.4f}, {df_rotated.max():.4f}]")
        self.logger.debug(f"  After rotation - Mask unique: {np.unique(mask_rotated)}")
        self.logger.debug(f"  After rotation - Non-zero mask pixels: {np.count_nonzero(mask_rotated)}")
        self.logger.debug(f"  After rotation - Reference point: ({ref_x}, {ref_y}) → {ref_rotated}")

        # Save rotated images
        self._save_debug_image(
            df_rotated,
            AggregationConstants.DEBUG_FILE_PATTERN_ROTATED_DF.format(window_id=window_id)
        )
        self._save_debug_image(
            mask_rotated * AggregationConstants.GRAYSCALE_MAX,
            AggregationConstants.DEBUG_FILE_PATTERN_ROTATED_MASK.format(window_id=window_id)
        )
        self._save_debug_image(
            df_rotated * mask_rotated,
            AggregationConstants.DEBUG_FILE_PATTERN_ROTATED_MASKED.format(window_id=window_id)
        )

        return df_rotated, mask_rotated, ref_rotated

    def _crop_to_visible_bounds(
        self,
        df_values: np.ndarray,
        mask: np.ndarray,
        window_id: str
    ) -> Tuple[np.ndarray, np.ndarray, Tuple[int, int]]:
        """
        Crop DF and mask to the visible (non-zero mask) bounds ONLY.
        The reference point should already be within the mask bounds.

        Args:
            df_values: Rotated DF values
            mask: Rotated mask
            window_id: Window identifier for logging

        Returns:
            (df_cropped, mask_cropped, crop_offset):
                - df_cropped: Cropped DF values
                - mask_cropped: Cropped mask
                - crop_offset: (offset_x, offset_y) of crop region in original image
        """
        # Find non-zero mask regions
        rows = np.any(mask > 0, axis=1)
        cols = np.any(mask > 0, axis=0)

        if not rows.any() or not cols.any():
            # No visible region, return empty
            self.logger.warning(f"  No visible region found in mask after rotation")
            return df_values, mask, (AggregationConstants.ZERO_VALUE, AggregationConstants.ZERO_VALUE)

        row_min, row_max = np.where(rows)[0][[0, -1]]
        col_min, col_max = np.where(cols)[0][[0, -1]]

        # Add 1 to max indices to include the last row/col in the slice
        row_max += AggregationConstants.ARRAY_OFFSET_ONE
        col_max += AggregationConstants.ARRAY_OFFSET_ONE

        # Crop both arrays to mask bounds only
        df_cropped = df_values[row_min:row_max, col_min:col_max]
        mask_cropped = mask[row_min:row_max, col_min:col_max]

        crop_offset = (col_min, row_min)

        self.logger.info(f"  Cropped from {df_values.shape} to {df_cropped.shape}, offset: {crop_offset}")

        # Save cropped images
        self._save_debug_image(
            df_cropped,
            AggregationConstants.DEBUG_FILE_PATTERN_CROPPED_DF.format(window_id=window_id)
        )
        self._save_debug_image(
            mask_cropped * AggregationConstants.GRAYSCALE_MAX,
            AggregationConstants.DEBUG_FILE_PATTERN_CROPPED_MASK.format(window_id=window_id)
        )
        self._save_debug_image(
            df_cropped * mask_cropped,
            AggregationConstants.DEBUG_FILE_PATTERN_CROPPED_MASKED.format(window_id=window_id)
        )

        return df_cropped, mask_cropped, crop_offset

    def _place_window_on_room(
        self,
        df_matrix: np.ndarray,
        df_window: np.ndarray,
        mask_window: np.ndarray,
        translation: Point2D,
        window: WindowGeometry,
        window_id: str
    ) -> None:
        """
        Place cropped window image onto room canvas at correct position.

        The window reference point is at the center of the window's edge that shares
        a common segment with the room polygon (the room-facing edge). This reference
        point is calculated as the midpoint of (x1,y1) and (x2,y2).

        At 128x128 with 0.1m/px scale, the window image represents a 12.8m x 12.8m area.
        After rotation and cropping, we need to account for the crop offset when placing.

        Args:
            df_matrix: Room DF matrix to accumulate into
            df_window: Cropped window DF values - already rotated and cropped
            mask_window: Cropped window mask - already rotated and cropped
            crop_offset: (offset_x, offset_y) of crop region in the 128x128 rotated image
            window: Window object with position info
            room_min_x: Room minimum X coordinate (meters)
            room_min_y: Room minimum Y coordinate (meters)
            window_id: Window identifier for logging
        """
       

        # Get dimensions
        room_height, room_width = df_matrix.shape
        window_height, window_width = df_window.shape

        offset_y, offset_x = int(translation.y), int(translation.x)

        # Calculate overlap region
        # Source region in cropped window image
        src_y_start = max(AggregationConstants.ZERO_VALUE, -offset_y)
        src_y_end = min(window_height, room_height - offset_y)
        src_x_start = max(AggregationConstants.ZERO_VALUE, -offset_x)
        src_x_end = min(window_width, room_width - offset_x)

        # Destination region in room image
        dst_y_start = max(AggregationConstants.ZERO_VALUE, offset_y)
        dst_y_end = min(room_height, offset_y + window_height)
        dst_x_start = max(AggregationConstants.ZERO_VALUE, offset_x)
        dst_x_end = min(room_width, offset_x + window_width)

        # Calculate actual region sizes
        src_height = src_y_end - src_y_start
        src_width = src_x_end - src_x_start
        dst_height = dst_y_end - dst_y_start
        dst_width = dst_x_end - dst_x_start

        self.logger.debug(f"  Source region: [{src_y_start}:{src_y_end}, {src_x_start}:{src_x_end}] = {src_height}x{src_width}")
        self.logger.debug(f"  Dest region: [{dst_y_start}:{dst_y_end}, {dst_x_start}:{dst_x_end}] = {dst_height}x{dst_width}")

        # Verify regions match
        if src_height != dst_height or src_width != dst_width:
            self.logger.warning(f"  Region size mismatch! src={src_height}x{src_width}, dst={dst_height}x{dst_width}")
            return

        # Only proceed if there's valid overlap
        if src_height > AggregationConstants.ZERO_VALUE and src_width > AggregationConstants.ZERO_VALUE:
            # Extract overlapping region from window image
            window_region_df = df_window[src_y_start:src_y_end, src_x_start:src_x_end]
            window_region_mask = mask_window[src_y_start:src_y_end, src_x_start:src_x_end]

            # Apply mask and accumulate to room matrix
            masked_values = window_region_df * window_region_mask
            contribution_sum = masked_values.sum()

            self.logger.info(f"  Adding {np.count_nonzero(window_region_mask)} masked pixels, DF contribution sum: {contribution_sum:.4f}")

            df_matrix[dst_y_start:dst_y_end, dst_x_start:dst_x_end] += masked_values
        else:
            self.logger.warning(f"  No valid overlap region (size: {src_height}x{src_width})") 

    def _save_debug_image(self, img: np.ndarray, filename: str) -> None:
        """
        Save debug image to tmp folder.

        Args:
            img: Image array (will be normalized to 0-255 for saving)
            filename: Output filename
        """
        try:
            output_path = self.debug_dir / filename

            # Normalize to 0-255 range for visualization
            if img.max() > AggregationConstants.ZERO_VALUE:
                img_normalized = (img / img.max() * AggregationConstants.GRAYSCALE_MAX).astype(np.uint8)
            else:
                img_normalized = img.astype(np.uint8)

            cv2.imwrite(str(output_path), img_normalized)
            self.logger.debug(f"  Saved debug image: {output_path}")
        except Exception as e:
            self.logger.warning(f"  Failed to save debug image {filename}: {e}")


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
            Dictionary containing df_matrix and room_mask as lists
        """
        # Parse and create simulation data objects
        sim_objects = {}

        for window_id, sim_dict in simulations.items():
            # Get window definition
            if window_id not in windows_data:
                raise ValueError(f"Window {window_id} not found in windows_data")

            window_dict = windows_data[window_id]
            window = WindowGeometry(
                x1=window_dict['x1'],
                y1=window_dict['y1'],
                z1=window_dict['z1'],
                x2=window_dict['x2'],
                y2=window_dict['y2'],
                z2=window_dict['z2'],
                direction_angle=window_dict['direction_angle']
            )

            # Parse simulation arrays
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

            sim_objects[window_id] = SimulationData(
                df_values=df_values,
                mask=mask,
                window=window,
                scale=scale
            )

        # Aggregate
        df_matrix, room_mask = self.aggregator.aggregate(room_polygon, sim_objects)

        # Convert to lists for JSON serialization
        return {
            'df_matrix': df_matrix.tolist(),
            'room_mask': room_mask.tolist()
        }
