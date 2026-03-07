"""Tests for DFAggregationService"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from src.server.services.df_aggregation_service import DFAggregationService
from src.core.graphics_constants import GRAPHICS_CONSTANTS


class TestDFAggregationService:
    """Test DFAggregationService class"""

    def test_create_service_default_scale(self):
        """Test creating service with default scale"""
        service = DFAggregationService()
        assert service.aggregator is not None

    def test_create_service_custom_scale(self):
        """Test creating service with custom scale"""
        custom_scale = 0.05
        service = DFAggregationService(output_scale=custom_scale)
        assert service.aggregator is not None

    def test_service_has_process_request_method(self):
        """Test service has process_request method"""
        service = DFAggregationService()
        assert hasattr(service, "process_request")
        assert callable(getattr(service, "process_request"))

    def test_service_has_create_simulation_objects_method(self):
        """Test service has _create_simulation_objects method"""
        service = DFAggregationService()
        assert hasattr(service, "_create_simulation_objects")
        assert callable(getattr(service, "_create_simulation_objects"))

    def test_service_has_create_simulation_data_method(self):
        """Test service has _create_simulation_data method"""
        service = DFAggregationService()
        assert hasattr(service, "_create_simulation_data")
        assert callable(getattr(service, "_create_simulation_data"))

    def test_service_has_resize_method(self):
        """Test service has _resize method"""
        service = DFAggregationService()
        assert hasattr(service, "_resize")
        assert callable(getattr(service, "_resize"))

    def test_resize_array_to_base_size(self):
        """Test resizing array to base image size"""
        service = DFAggregationService()
        
        # Create array with different size
        original = np.ones((64, 64))
        resized = service._resize(original)
        
        expected_size = GRAPHICS_CONSTANTS.BASE_IMAGE_SIZE_PX
        assert resized.shape == (expected_size, expected_size)

    def test_resize_array_float(self):
        """Test resizing float array"""
        service = DFAggregationService()
        
        original = np.ones((64, 64), dtype=np.float32) * 0.5
        resized = service._resize(original)
        
        assert resized.shape == (GRAPHICS_CONSTANTS.BASE_IMAGE_SIZE_PX, 
                                 GRAPHICS_CONSTANTS.BASE_IMAGE_SIZE_PX)

    def test_resize_array_uint8(self):
        """Test resizing uint8 array"""
        service = DFAggregationService()
        
        original = np.ones((64, 64), dtype=np.uint8) * 128
        resized = service._resize(original)
        
        assert resized.shape == (GRAPHICS_CONSTANTS.BASE_IMAGE_SIZE_PX,
                                 GRAPHICS_CONSTANTS.BASE_IMAGE_SIZE_PX)

    def test_resize_array_from_256(self):
        """Test resizing from 256x256 array"""
        service = DFAggregationService()
        
        original = np.random.rand(256, 256).astype(np.float32)
        resized = service._resize(original)
        
        assert resized.shape == (GRAPHICS_CONSTANTS.BASE_IMAGE_SIZE_PX,
                                 GRAPHICS_CONSTANTS.BASE_IMAGE_SIZE_PX)

    def test_resize_array_from_512(self):
        """Test resizing from 512x512 array"""
        service = DFAggregationService()
        
        original = np.random.rand(512, 512).astype(np.uint8)
        resized = service._resize(original)
        
        assert resized.shape == (GRAPHICS_CONSTANTS.BASE_IMAGE_SIZE_PX,
                                 GRAPHICS_CONSTANTS.BASE_IMAGE_SIZE_PX)

    def test_resize_with_ones(self):
        """Test resizing array of ones"""
        service = DFAggregationService()
        original = np.ones((100, 100))
        resized = service._resize(original)
        
        assert resized.shape == (GRAPHICS_CONSTANTS.BASE_IMAGE_SIZE_PX,
                                 GRAPHICS_CONSTANTS.BASE_IMAGE_SIZE_PX)
        # All values should be similar (all ones resized to ones)
        assert np.all(resized > 0)

    def test_resize_with_zeros(self):
        """Test resizing array of zeros"""
        service = DFAggregationService()
        original = np.zeros((100, 100))
        resized = service._resize(original)
        
        assert resized.shape == (GRAPHICS_CONSTANTS.BASE_IMAGE_SIZE_PX,
                                 GRAPHICS_CONSTANTS.BASE_IMAGE_SIZE_PX)
        # All values should be zero
        assert np.all(resized == 0)

    def test_resize_with_mixed_values(self):
        """Test resizing array with mixed values"""
        service = DFAggregationService()
        original = np.random.uniform(0, 1, (100, 100)).astype(np.float32)
        resized = service._resize(original)
        
        assert resized.shape == (GRAPHICS_CONSTANTS.BASE_IMAGE_SIZE_PX,
                                 GRAPHICS_CONSTANTS.BASE_IMAGE_SIZE_PX)
        # Values should stay in similar range
        assert np.min(resized) >= -0.1
        assert np.max(resized) <= 1.1

    def test_create_simulation_objects_missing_window(self):
        """Test error when window not found"""
        service = DFAggregationService()
        
        windows_data = {}
        simulations = {
            "window1": {
                "df_values": np.ones((128, 128), dtype=np.float32) * 0.1,
                "mask": np.ones((128, 128), dtype=np.uint8)
            }
        }
        
        with pytest.raises(ValueError) as exc_info:
            service._create_simulation_objects(windows_data, simulations)
        
        assert "not found" in str(exc_info.value).lower()

    def test_create_simulation_data_window_not_found(self):
        """Test error when window definition not found"""
        service = DFAggregationService()
        
        windows_data = {}  # Empty
        sim_dict = {
            "df_values": np.ones((128, 128), dtype=np.float32) * 0.1,
            "mask": np.ones((128, 128), dtype=np.uint8)
        }
        
        with pytest.raises(ValueError) as exc_info:
            service._create_simulation_data("missing_window", sim_dict, windows_data)
        
        assert "Window" in str(exc_info.value)
        assert "missing_window" in str(exc_info.value)

    def test_service_attributes(self):
        """Test service has expected attributes"""
        service = DFAggregationService()
        
        assert hasattr(service, "aggregator")
        assert service.aggregator is not None

    def test_multiple_service_instances(self):
        """Test creating multiple service instances"""
        service1 = DFAggregationService()
        service2 = DFAggregationService(output_scale=0.1)
        
        assert service1.aggregator is not None
        assert service2.aggregator is not None
        assert service1 is not service2


    def test_create_simulation_objects_missing_window(self):
        """Test error when window not found"""
        service = DFAggregationService()
        
        windows_data = {}
        simulations = {
            "window1": {
                "df_values": np.ones((128, 128), dtype=np.float32) * 0.1,
                "mask": np.ones((128, 128), dtype=np.uint8)
            }
        }
        
        with pytest.raises(ValueError) as exc_info:
            service._create_simulation_objects(windows_data, simulations)
        
        assert "not found" in str(exc_info.value).lower()

    def test_create_simulation_data_basic(self):
        """Test creating single simulation data"""
        service = DFAggregationService()
        
        windows_data = {
            "window1": {"x1": 0, "y1": 0, "z1": 0, "x2": 2, "y2": 2, "z2": 3}
        }
        sim_dict = {
            "df_values": np.ones((128, 128), dtype=np.float32) * 0.1,
            "mask": np.ones((128, 128), dtype=np.uint8)
        }
        
        result = service._create_simulation_data("window1", sim_dict, windows_data)
        
        assert result is not None
        assert hasattr(result, "df_values")
        assert hasattr(result, "mask")
        assert hasattr(result, "window")
        assert hasattr(result, "scale")

    def test_create_simulation_data_shape_mismatch(self):
        """Test handling shape mismatch between df_values and mask"""
        service = DFAggregationService()
        
        windows_data = {
            "window1": {"x1": 0, "y1": 0, "z1": 0, "x2": 2, "y2": 2, "z2": 3}
        }
        sim_dict = {
            "df_values": np.ones((100, 100), dtype=np.float32) * 0.1,  # 100x100
            "mask": np.ones((128, 128), dtype=np.uint8)  # 128x128
        }
        
        result = service._create_simulation_data("window1", sim_dict, windows_data)
        
        # Should resize both to same base size
        assert result.df_values.shape == result.mask.shape

    def test_create_simulation_data_numpy_arrays(self):
        """Test creating simulation data with numpy arrays"""
        service = DFAggregationService()
        
        windows_data = {
            "window1": {"x1": 0, "y1": 0, "z1": 0, "x2": 2, "y2": 2, "z2": 3}
        }
        sim_dict = {
            "df_values": np.ones((128, 128), dtype=np.float32) * 0.5,
            "mask": np.ones((128, 128), dtype=np.uint8)
        }
        
        result = service._create_simulation_data("window1", sim_dict, windows_data)
        
        assert result.df_values.shape == (128, 128)
        assert result.mask.shape == (128, 128)
        assert result.df_values.dtype == np.float32
        assert result.mask.dtype == np.uint8

    def test_dtype_conversion_df_values(self):
        """Test df_values converted to float32"""
        service = DFAggregationService()
        
        windows_data = {
            "window1": {"x1": 0, "y1": 0, "z1": 0, "x2": 2, "y2": 2, "z2": 3}
        }
        sim_dict = {
            "df_values": np.ones((128, 128), dtype=np.float64) * 0.5,
            "mask": np.ones((128, 128), dtype=np.uint8)
        }
        
        result = service._create_simulation_data("window1", sim_dict, windows_data)
        
        assert result.df_values.dtype == np.float32

    def test_dtype_conversion_mask(self):
        """Test mask converted to uint8"""
        service = DFAggregationService()
        
        windows_data = {
            "window1": {"x1": 0, "y1": 0, "z1": 0, "x2": 2, "y2": 2, "z2": 3}
        }
        sim_dict = {
            "df_values": np.ones((128, 128), dtype=np.float32) * 0.5,
            "mask": np.ones((128, 128), dtype=np.int32)
        }
        
        result = service._create_simulation_data("window1", sim_dict, windows_data)
        
        assert result.mask.dtype == np.uint8

    def test_multiple_windows_processing(self):
        """Test creating simulation objects with multiple windows"""
        service = DFAggregationService()
        
        windows_data = {
            "window1": {"x1": 0, "y1": 0, "z1": 0, "x2": 2, "y2": 2, "z2": 3},
            "window2": {"x1": 5, "y1": 5, "z1": 0, "x2": 7, "y2": 7, "z2": 3},
            "window3": {"x1": 10, "y1": 0, "z1": 0, "x2": 12, "y2": 2, "z2": 3}
        }
        simulations = {
            "window1": {
                "df_values": np.ones((128, 128), dtype=np.float32) * 0.1,
                "mask": np.ones((128, 128), dtype=np.uint8)
            },
            "window2": {
                "df_values": np.ones((128, 128), dtype=np.float32) * 0.2,
                "mask": np.ones((128, 128), dtype=np.uint8)
            },
            "window3": {
                "df_values": np.ones((128, 128), dtype=np.float32) * 0.3,
                "mask": np.ones((128, 128), dtype=np.uint8)
            }
        }
        
        result = service._create_simulation_objects(windows_data, simulations)
        
        assert len(result) == 3
        assert "window1" in result
        assert "window2" in result
        assert "window3" in result
