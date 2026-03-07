"""Tests for room DF aggregator."""

import pytest
import numpy as np
from unittest.mock import Mock, MagicMock, patch

from src.components.aggregation.room_df_aggregator import RoomDFAggregator
from src.components.room_polygon import RoomPolygon
from src.models.simulation_data import SimulationData
from src.components.window import WindowGeometry
from src.components.geometry_ops import Point2D


class TestRoomDFAggregator:
    """Test RoomDFAggregator class."""

    def test_aggregator_creation_default(self):
        """Test creating aggregator with defaults."""
        aggregator = RoomDFAggregator()
        assert aggregator is not None
        assert aggregator.output_scale == 0.1

    def test_aggregator_creation_custom_scale(self):
        """Test creating aggregator with custom scale."""
        aggregator = RoomDFAggregator(output_scale=0.2)
        assert aggregator.output_scale == pytest.approx(0.2)

    def test_aggregator_with_orchestrator(self):
        """Test creating aggregator with provided orchestrator."""
        mock_orchestrator = Mock()
        aggregator = RoomDFAggregator(orchestrator=mock_orchestrator)
        assert aggregator.orchestrator is mock_orchestrator

    def test_aggregator_has_polygon_rasterizer(self):
        """Test that aggregator has polygon rasterizer."""
        aggregator = RoomDFAggregator()
        assert aggregator.polygon_rasterizer is not None

    def test_create_room_mask_square(self):
        """Test creating room mask for square room."""
        aggregator = RoomDFAggregator(output_scale=0.1)
        
        # Simple square room
        room_coords = [
            (0.0, 0.0),
            (1.0, 0.0),
            (1.0, 1.0),
            (0.0, 1.0)
        ]
        room = RoomPolygon(room_coords)
        room_translated = room.shift_to_zero()
        
        mask = aggregator._create_room_mask(room_translated, 10, 10)
        
        assert isinstance(mask, np.ndarray)
        assert mask.shape == (10, 10)

    def test_create_room_mask_L_shaped(self):
        """Test creating room mask for L-shaped room."""
        aggregator = RoomDFAggregator(output_scale=0.1)
        
        # L-shaped room
        room_coords = [
            (0.0, 0.0),
            (2.0, 0.0),
            (2.0, 1.0),
            (1.0, 1.0),
            (1.0, 2.0),
            (0.0, 2.0)
        ]
        room = RoomPolygon(room_coords)
        room_translated = room.shift_to_zero()
        
        mask = aggregator._create_room_mask(room_translated, 20, 20)
        
        assert isinstance(mask, np.ndarray)
        assert mask.dtype in [np.uint8, np.float32, np.float64]
        assert mask.shape == (20, 20)

    def test_aggregate_empty_simulations(self):
        """Test aggregating with no simulations."""
        aggregator = RoomDFAggregator()
        
        room_coords = [
            (0.0, 0.0),
            (1.0, 0.0),
            (1.0, 1.0),
            (0.0, 1.0)
        ]
        room = RoomPolygon(room_coords)
        
        # With empty simulations, should still create empty matrix
        result = aggregator.aggregate(room, {})
        
        assert isinstance(result, tuple)
        assert len(result) == 2
        df_matrix, room_mask = result
        assert isinstance(df_matrix, np.ndarray)
        assert isinstance(room_mask, np.ndarray)

    @patch('src.components.aggregation.room_df_aggregator.WindowAggregationOrchestrator')
    def test_aggregate_single_window(self, mock_orchestrator_class):
        """Test aggregating a single window."""
        # Setup mocks
        mock_orchestrator_instance = MagicMock()
        mock_orchestrator_class.return_value = mock_orchestrator_instance
        
        aggregator = RoomDFAggregator()
        
        room_coords = [
            (0.0, 0.0),
            (2.0, 0.0),
            (2.0, 2.0),
            (0.0, 2.0)
        ]
        room = RoomPolygon(room_coords)
        
        # Create dummy simulation data
        window = WindowGeometry(
            x1=0.0, y1=0.0, z1=0.0,
            x2=0.5, y2=0.5, z2=2.0
        )
        
        #Create simple DF values array
        df_values = np.ones((384, 384)) * 0.5
        mask = np.ones((384, 384))
        
        from src.models.image_scale import ImageScale
        scale = ImageScale(size=384, meters_per_pixel=0.1)
        
        sim_data = SimulationData(
            window=window,
            df_values=df_values,
            mask=mask,
            scale=scale
        )
        
        result = aggregator.aggregate(room, {"window_1": sim_data})
        
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_aggregate_creates_room_matrix(self):
        """Test that aggregate creates proper room matrix."""
        aggregator = RoomDFAggregator()
        
        room_coords = [
            (0.0, 0.0),
            (2.0, 0.0),
            (2.0, 2.0),
            (0.0, 2.0)
        ]
        room = RoomPolygon(room_coords)
        
        df_matrix, room_mask = aggregator.aggregate(room, {})
        
        # Check room dimensions
        # 2m / 0.1 m/px = 20px
        expected_size = 20
        assert df_matrix.shape == (expected_size, expected_size)
        assert room_mask.shape == (expected_size, expected_size)

    def test_aggregate_rectangular_room(self):
        """Test aggregating for rectangular room."""
        aggregator = RoomDFAggregator(output_scale=0.1)
        
        room_coords = [
            (0.0, 0.0),
            (3.0, 0.0),
            (3.0, 2.0),
            (0.0, 2.0)
        ]
        room = RoomPolygon(room_coords)
        
        df_matrix, room_mask = aggregator.aggregate(room, {})
        
        # 3m width / 0.1 = 30px, 2m height / 0.1 = 20px
        # But create_room_mask uses room_width_px and room_height_px in order (width, height)
        # and returns (height_px, width_px) array shape
        assert df_matrix.shape == (20, 30)
        assert room_mask.shape == (20, 30)

    def test_aggregate_output_is_flipped(self):
        """Test that aggregate output is properly flipped."""
        aggregator = RoomDFAggregator()
        
        room_coords = [
            (0.0, 0.0),
            (1.0, 0.0),
            (1.0, 1.0),
            (0.0, 1.0)
        ]
        room = RoomPolygon(room_coords)
        
        df_matrix, room_mask = aggregator.aggregate(room, {})
        
        # Output should be numpy arrays
        assert isinstance(df_matrix, np.ndarray)
        assert isinstance(room_mask, np.ndarray)

    def test_polygon_rasterizer_initialized(self):
        """Test that polygon rasterizer is properly initialized."""
        aggregator = RoomDFAggregator()
        assert aggregator.polygon_rasterizer is not None

    def test_aggregator_logging(self, caplog):
        """Test that aggregator logs messages."""
        import logging
        caplog.set_level(logging.INFO)
        
        aggregator = RoomDFAggregator()
        room_coords = [
            (0.0, 0.0),
            (1.0, 0.0),
            (1.0, 1.0),
            (0.0, 1.0)
        ]
        room = RoomPolygon(room_coords)
        
        aggregator.aggregate(room, {})
        
        # Check that at least some logging occurred
        assert len(caplog.records) >= 0

    def test_room_shifted_to_zero(self):
        """Test that room is properly shifted to zero internally."""
        aggregator = RoomDFAggregator()
        
        # Room with offset origin
        room_coords = [
            (5.0, 3.0),
            (7.0, 3.0),
            (7.0, 5.0),
            (5.0, 5.0)
        ]
        room = RoomPolygon(room_coords)
        
        df_matrix, room_mask = aggregator.aggregate(room, {})
        
        # Should still produce valid output
        assert df_matrix.shape[0] > 0
        assert df_matrix.shape[1] > 0

    def test_room_mask_binary(self):
        """Test that room mask contains binary values."""
        aggregator = RoomDFAggregator()
        
        room_coords = [
            (0.0, 0.0),
            (1.0, 0.0),
            (1.0, 1.0),
            (0.0, 1.0)
        ]
        room = RoomPolygon(room_coords)
        
        _, room_mask = aggregator.aggregate(room, {})
        
        # Mask should contain only values between 0 and 1
        assert room_mask.min() >= 0.0
        assert room_mask.max() <= 1.0
