"""Tests for processing steps."""

import pytest
import numpy as np
from src.components.processing.steps.standardize import StandardizeWindowStep
from src.components.processing.steps.rotate import RotateWindowStep
from src.components.processing.steps.crop import CropWindowStep
from src.components.processing.steps.calculate_position import CalculateWindowPositionStep
from src.components.processing.steps.calculate_translation import CalculateTranslationStep
from src.components.processing.context import WindowInputData, ImagePair, WindowProcessingContext
from src.components.processing.window_processor import WindowProcessor
from src.core.utils import ScaleConverter


class TestStandardizeWindowStep:
    """Test StandardizeWindowStep."""

    @pytest.fixture
    def step(self):
        """Create a StandardizeWindowStep."""
        return StandardizeWindowStep(WindowProcessor())

    def test_standardize_step_execution(self, step, sample_window, sample_room_polygon):
        """Test executing standardize step."""
        input_data = WindowInputData(
            window_id="test",
            window=sample_window,
            room_polygon=sample_room_polygon
        )
        
        df = np.random.rand(384, 384).astype(np.float32) * 0.1
        mask = np.ones((384, 384), dtype=np.uint8)
        original_images = ImagePair(df_values=df, mask=mask)
        
        context = WindowProcessingContext(
            input=input_data,
            original_images=original_images
        )
        
        result = step.run(context)
        
        assert result.original_images.df_values.shape == (128, 128)
        assert result.original_images.mask.shape == (128, 128)


class TestRotateWindowStep:
    """Test RotateWindowStep."""

    @pytest.fixture
    def step(self):
        """Create a RotateWindowStep."""
        return RotateWindowStep(WindowProcessor())

    def test_rotate_step_execution(self, step, sample_window, sample_room_polygon):
        """Test executing rotate step."""
        from src.components.processing.context import PositionData
        from src.components.geometry_ops import Point2D
        
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
            ref_px_original=(64, 64)
        )
        
        context = WindowProcessingContext(
            input=input_data,
            original_images=original_images,
            position=position
        )
        
        result = step.run(context)
        
        assert result.original_images.df_values.shape == (128, 128)
        assert result.position is not None


class TestCropWindowStep:
    """Test CropWindowStep."""

    @pytest.fixture
    def step(self):
        """Create a CropWindowStep."""
        return CropWindowStep(WindowProcessor())

    def test_crop_step_execution(self, step, sample_window, sample_room_polygon):
        """Test executing crop step."""
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
        
        result = step.run(context)
        
        assert result.cropped is not None
        assert result.cropped.images.df_values.shape[0] > 0
        assert result.cropped.images.df_values.shape[1] > 0


class TestCalculateWindowPositionStep:
    """Test CalculateWindowPositionStep."""

    @pytest.fixture
    def step(self):
        """Create a CalculateWindowPositionStep."""
        return CalculateWindowPositionStep(ScaleConverter(0.05))

    def test_calculate_position_step(self, step, sample_window, sample_room_polygon):
        """Test executing calculate position step."""
        input_data = WindowInputData(
            window_id="test",
            window=sample_window,
            room_polygon=sample_room_polygon
        )
        
        df = np.random.rand(384, 384).astype(np.float32)
        mask = np.ones((384, 384), dtype=np.uint8)
        original_images = ImagePair(df_values=df, mask=mask)
        
        context = WindowProcessingContext(
            input=input_data,
            original_images=original_images
        )
        
        result = step.run(context)
        
        assert result.position is not None
        assert result.position.room_coord_meters is not None


class TestCalculateTranslationStep:
    """Test CalculateTranslationStep."""

    @pytest.fixture
    def step(self):
        """Create a CalculateTranslationStep."""
        return CalculateTranslationStep()

    def test_calculate_translation_step(self, step, sample_window, sample_room_polygon):
        """Test executing calculate translation step."""
        from src.components.processing.context import PositionData, CropData
        from src.components.geometry_ops import Point2D
        
        input_data = WindowInputData(
            window_id="test",
            window=sample_window,
            room_polygon=sample_room_polygon
        )
        
        df = np.random.rand(74, 128).astype(np.float32)
        mask = np.ones((74, 128), dtype=np.uint8)
        cropped_images = ImagePair(df_values=df, mask=mask)
        
        position = PositionData(
            room_coord_meters=Point2D(x=5.0, y=6.0),
            room_coord_pixels=Point2D(x=50, y=60),
            ref_px_original=(64, 64),
            ref_px_rotated=(64, 64)  # Add rotated reference
        )
        
        cropped = CropData(
            images=cropped_images,
            offset=(10, 20)
        )
        
        context = WindowProcessingContext(
            input=input_data,
            original_images=cropped_images,
            position=position,
            cropped=cropped
        )
        
        result = step.run(context)
        
        assert result.translation is not None
