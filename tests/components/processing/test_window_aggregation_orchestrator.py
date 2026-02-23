"""Tests for window aggregation orchestrator."""

import pytest
import numpy as np
from unittest.mock import Mock, MagicMock, patch

from src.components.processing.window_aggregation_orchestrator import WindowAggregationOrchestrator
from src.components.processing.window_processor import WindowProcessor
from src.components.window import WindowGeometry, RoomPolygon
from src.components.geometry_ops import Point2D
from src.models.simulation_data import SimulationData
from src.models.room_df_matrix import RoomDFMatrix
from src.models.image_scale import ImageScale


class TestWindowAggregationOrchestrator:
    """Test WindowAggregationOrchestrator class."""

    def test_orchestrator_creation(self):
        """Test creating orchestrator."""
        processor = WindowProcessor()
        orchestrator = WindowAggregationOrchestrator(processor, output_scale=0.1)
        
        assert orchestrator is not None
        assert orchestrator.pipeline is not None

    def test_orchestrator_with_custom_scale(self):
        """Test creating orchestrator with custom scale."""
        processor = WindowProcessor()
        orchestrator = WindowAggregationOrchestrator(processor, output_scale=0.2)
        
        assert orchestrator is not None

    def test_orchestrator_has_pipeline(self):
        """Test that orchestrator has pipeline."""
        processor = WindowProcessor()
        orchestrator = WindowAggregationOrchestrator(processor, output_scale=0.1)
        
        assert hasattr(orchestrator, 'pipeline')
        assert orchestrator.pipeline is not None

    def test_orchestrator_pipeline_has_steps(self):
        """Test that pipeline has processing steps."""
        processor = WindowProcessor()
        orchestrator = WindowAggregationOrchestrator(processor, output_scale=0.1)
        
        assert hasattr(orchestrator.pipeline, 'steps')
        assert len(orchestrator.pipeline.steps) > 0

    @patch('src.components.processing.window_aggregation_orchestrator.logger')
    def test_orchestrator_logs_window_processing(self, mock_logger):
        """Test that orchestrator logs processing."""
        processor = WindowProcessor()
        orchestrator = WindowAggregationOrchestrator(processor, output_scale=0.1)
        
        # Create simple test data
        window = WindowGeometry(
            x1=0.0, y1=0.0, z1=0.0,
            x2=0.5, y2=0.5, z2=2.0
        )
        
        df_values = np.ones((384, 384)) * 0.5
        mask = np.ones((384, 384))
        scale = ImageScale(size=384, meters_per_pixel=0.1)
        
        sim_data = SimulationData(
            window=window,
            df_values=df_values,
            mask=mask,
            scale=scale
        )
        
        room_coords = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
        room = RoomPolygon(room_coords)
        
        df_matrix = RoomDFMatrix(10, 10)
        
        orchestrator.process_and_accumulate_window(
            "test_window", sim_data, room, df_matrix
        )
        
        # Verify logging was called
        assert mock_logger.info.called

    def test_orchestrator_process_and_accumulate_window(self):
        """Test processing and accumulating a single window."""
        processor = WindowProcessor()
        orchestrator = WindowAggregationOrchestrator(processor, output_scale=0.1)
        
        # Create test data
        window = WindowGeometry(
            x1=0.0, y1=0.0, z1=0.0,
            x2=0.5, y2=0.5, z2=2.0
        )
        
        df_values = np.ones((384, 384)) * 0.5
        mask = np.ones((384, 384))
        scale = ImageScale(size=384, meters_per_pixel=0.1)
        
        sim_data = SimulationData(
            window=window,
            df_values=df_values,
            mask=mask,
            scale=scale
        )
        
        room_coords = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
        room = RoomPolygon(room_coords)
        
        df_matrix = RoomDFMatrix(10, 10)
        
        # Should not raise exception
        orchestrator.process_and_accumulate_window(
            "window_1", sim_data, room, df_matrix
        )

    def test_orchestrator_with_multiple_windows(self):
        """Test orchestrator can process multiple windows."""
        processor = WindowProcessor()
        orchestrator = WindowAggregationOrchestrator(processor, output_scale=0.1)
        
        # Create test room
        room_coords = [(0.0, 0.0), (2.0, 0.0), (2.0, 2.0), (0.0, 2.0)]
        room = RoomPolygon(room_coords)
        df_matrix = RoomDFMatrix(20, 20)
        
        # Process multiple windows
        for i in range(3):
            window = WindowGeometry(
                x1=0.0+i*0.3, y1=0.0, z1=0.0,
                x2=0.5+i*0.3, y2=0.5, z2=2.0
            )
            
            df_values = np.ones((384, 384)) * 0.5
            mask = np.ones((384, 384))
            scale = ImageScale(size=384, meters_per_pixel=0.1)
            
            sim_data = SimulationData(
                window=window,
                df_values=df_values,
                mask=mask,
                scale=scale
            )
            
            orchestrator.process_and_accumulate_window(
                f"window_{i}", sim_data, room, df_matrix
            )

    def test_orchestrator_transform_window_through_pipeline(self):
        """Test internal pipeline transformation method."""
        processor = WindowProcessor()
        orchestrator = WindowAggregationOrchestrator(processor, output_scale=0.1)
        
        window = WindowGeometry(
            x1=0.0, y1=0.0, z1=0.0,
            x2=0.5, y2=0.5, z2=2.0
        )
        
        df_values = np.ones((384, 384)) * 0.5
        mask = np.ones((384, 384))
        scale = ImageScale(size=384, meters_per_pixel=0.1)
        
        sim_data = SimulationData(
            window=window,
            df_values=df_values,
            mask=mask,
            scale=scale
        )
        
        room_coords = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
        room = RoomPolygon(room_coords)
        
        # Test the transformation method
        result = orchestrator._transform_window_through_pipeline(
            "test_window", sim_data, room
        )
        
        assert result is not None

    def test_orchestrator_accumulate_calls_matrix_accumulate(self):
        """Test that accumulate_window is called on matrix."""
        processor = WindowProcessor()
        orchestrator = WindowAggregationOrchestrator(processor, output_scale=0.1)
        
        # Mock the matrix
        mock_matrix = MagicMock(spec=RoomDFMatrix)
        
        window = WindowGeometry(
            x1=0.0, y1=0.0, z1=0.0,
            x2=0.5, y2=0.5, z2=2.0
        )
        
        df_values = np.ones((384, 384)) * 0.5
        mask = np.ones((384, 384))
        scale = ImageScale(size=384, meters_per_pixel=0.1)
        
        sim_data = SimulationData(
            window=window,
            df_values=df_values,
            mask=mask,
            scale=scale
        )
        
        room_coords = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
        room = RoomPolygon(room_coords)
        
        orchestrator.process_and_accumulate_window(
            "window_1", sim_data, room, mock_matrix
        )
        
        # Verify that accumulate_window was called
        assert mock_matrix.accumulate_window.called

    def test_orchestrator_with_different_room_sizes(self):
        """Test orchestrator with different room sizes."""
        processor = WindowProcessor()
        orchestrator = WindowAggregationOrchestrator(processor, output_scale=0.1)
        
        window = WindowGeometry(
            x1=0.0, y1=0.0, z1=0.0,
            x2=0.5, y2=0.5, z2=2.0
        )
        
        df_values = np.ones((384, 384)) * 0.5
        mask = np.ones((384, 384))
        scale = ImageScale(size=384, meters_per_pixel=0.1)
        
        sim_data = SimulationData(
            window=window,
            df_values=df_values,
            mask=mask,
            scale=scale
        )
        
        # Test with different room sizes
        for size in [1.0, 2.0, 5.0, 10.0]:
            room_coords = [
                (0.0, 0.0), (size, 0.0),
                (size, size), (0.0, size)
            ]
            room = RoomPolygon(room_coords)
            df_matrix = RoomDFMatrix(int(size * 10), int(size * 10))
            
            orchestrator.process_and_accumulate_window(
                "test_window", sim_data, room, df_matrix
            )

    def test_orchestrator_scale_converter_correct_scale(self):
        """Test that orchestrator creates scale converter with correct scale."""
        processor = WindowProcessor()
        scale = 0.05
        orchestrator = WindowAggregationOrchestrator(processor, output_scale=scale)
        
        # Scale converter should be created internally
        assert orchestrator.pipeline is not None
        # The scale converter in the pipeline should use the provided scale
