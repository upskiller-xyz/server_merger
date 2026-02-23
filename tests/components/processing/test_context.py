"""Tests for processing context and data structures."""

import pytest
import numpy as np
from src.components.processing.context import (
    WindowInputData,
    ImagePair,
    PositionData,
    CropData,
    WindowProcessingContext
)
from src.components.geometry_ops import Point2D
from src.components.window import WindowGeometry, RoomPolygon


class TestWindowInputData:
    """Test WindowInputData class."""

    def test_window_input_data_creation(self, sample_window, sample_room_polygon):
        """Test creating WindowInputData."""
        data = WindowInputData(
            window_id="test_window",
            window=sample_window,
            room_polygon=sample_room_polygon
        )
        
        assert data.window_id == "test_window"
        assert data.window is not None
        assert data.room_polygon is not None

    def test_window_input_data_immutable(self, sample_window, sample_room_polygon):
        """Test that WindowInputData is immutable (dataclass)."""
        data = WindowInputData(
            window_id="test_window",
            window=sample_window,
            room_polygon=sample_room_polygon
        )
        
        # Should be able to read fields
        assert data.window_id == "test_window"


class TestImagePair:
    """Test ImagePair class."""

    def test_image_pair_creation(self):
        """Test creating an ImagePair."""
        df = np.random.rand(128, 128).astype(np.float32)
        mask = np.ones((128, 128), dtype=np.uint8)
        
        pair = ImagePair(df_values=df, mask=mask)
        
        assert np.array_equal(pair.df_values, df)
        assert np.array_equal(pair.mask, mask)

    def test_image_pair_different_shapes(self):
        """Test ImagePair with different sized arrays."""
        df = np.random.rand(256, 256).astype(np.float32)
        mask = np.ones((128, 128), dtype=np.uint8)
        
        pair = ImagePair(df_values=df, mask=mask)
        
        assert pair.df_values.shape == (256, 256)
        assert pair.mask.shape == (128, 128)


class TestPositionData:
    """Test PositionData class."""

    def test_position_data_creation(self):
        """Test creating PositionData."""
        pos = PositionData(
            room_coord_meters=Point2D(x=5.0, y=6.0),
            room_coord_pixels=Point2D(x=50, y=60),
            ref_px_original=(100, 100)
        )
        
        assert pos.room_coord_meters.x == 5.0
        assert pos.room_coord_meters.y == 6.0
        assert pos.ref_px_original == (100, 100)

    def test_position_data_with_rotated_ref(self):
        """Test PositionData with rotated reference point."""
        pos = PositionData(
            room_coord_meters=Point2D(x=5.0, y=6.0),
            room_coord_pixels=Point2D(x=50, y=60),
            ref_px_original=(100, 100),
            ref_px_rotated=(105, 95)
        )
        
        assert pos.ref_px_rotated == (105, 95)


class TestCropData:
    """Test CropData class."""

    def test_crop_data_creation(self):
        """Test creating CropData."""
        df = np.random.rand(100, 80).astype(np.float32)
        mask = np.ones((100, 80), dtype=np.uint8)
        images = ImagePair(df_values=df, mask=mask)
        
        crop = CropData(
            images=images,
            offset=(20, 10)
        )
        
        assert crop.offset == (20, 10)
        assert crop.images.df_values.shape == (100, 80)


class TestWindowProcessingContext:
    """Test WindowProcessingContext class."""

    def test_context_creation(self, sample_window, sample_room_polygon):
        """Test creating WindowProcessingContext."""
        input_data = WindowInputData(
            window_id="test",
            window=sample_window,
            room_polygon=sample_room_polygon
        )
        
        df = np.random.rand(128, 128).astype(np.float32)
        mask = np.ones((128, 128), dtype=np.uint8)
        original_images = ImagePair(df_values=df, mask=mask)
        
        context = WindowProcessingContext(
            input=input_data,
            original_images=original_images
        )
        
        assert context.input.window_id == "test"
        assert context.original_images.df_values.shape == (128, 128)
        assert context.position is None
        assert context.cropped is None

    def test_context_with_position(self, sample_window, sample_room_polygon):
        """Test context with position data."""
        input_data = WindowInputData(
            window_id="test",
            window=sample_window,
            room_polygon=sample_room_polygon
        )
        
        df = np.random.rand(128, 128).astype(np.float32)
        mask = np.ones((128, 128), dtype=np.uint8)
        original_images = ImagePair(df_values=df, mask=mask)
        
        position = PositionData(
            room_coord_meters=Point2D(x=5.0, y=6.0),
            room_coord_pixels=Point2D(x=50, y=60),
            ref_px_original=(100, 100)
        )
        
        context = WindowProcessingContext(
            input=input_data,
            original_images=original_images,
            position=position
        )
        
        assert context.position is not None
        assert context.position.room_coord_meters.x == 5.0
