"""Tests for base server controller"""

import pytest
from unittest.mock import Mock, patch
from src.server.controllers.base_controller import ServerController
from src.core.enums import ServerStatus


class TestServerController:
    """Test ServerController class"""

    def test_create_controller_no_services(self):
        """Test creating controller without services"""
        controller = ServerController()
        assert controller._services == {}
        assert controller._status == ServerStatus.STARTING

    def test_create_controller_with_services(self):
        """Test creating controller with services"""
        mock_service1 = Mock()
        mock_service2 = Mock()
        services = {"service1": mock_service1, "service2": mock_service2}
        
        controller = ServerController(services=services)
        assert controller._services == services
        assert controller._status == ServerStatus.STARTING

    def test_create_controller_with_empty_dict(self):
        """Test creating controller with empty services dict"""
        controller = ServerController(services={})
        assert controller._services == {}
        assert controller._status == ServerStatus.STARTING

    def test_create_controller_with_none(self):
        """Test creating controller with None services"""
        controller = ServerController(services=None)
        assert controller._services == {}
        assert controller._status == ServerStatus.STARTING

    @patch('src.server.controllers.base_controller.logger')
    def test_initialize_no_services(self, mock_logger):
        """Test initializing controller with no services"""
        controller = ServerController()
        controller.initialize()
        
        assert controller._status == ServerStatus.RUNNING
        mock_logger.info.assert_called()

    @patch('src.server.controllers.base_controller.logger')
    def test_initialize_with_services_having_initialize(self, mock_logger):
        """Test initializing controller with services that have initialize method"""
        mock_service = Mock()
        mock_service.initialize = Mock()
        services = {"service1": mock_service}
        
        controller = ServerController(services=services)
        controller.initialize()
        
        mock_service.initialize.assert_called_once()
        assert controller._status == ServerStatus.RUNNING

    @patch('src.server.controllers.base_controller.logger')
    def test_initialize_with_services_without_initialize(self, mock_logger):
        """Test initializing controller with services without initialize method"""
        mock_service = Mock(spec=[])  # No initialize method
        services = {"service1": mock_service}
        
        controller = ServerController(services=services)
        controller.initialize()
        
        assert controller._status == ServerStatus.RUNNING

    @patch('src.server.controllers.base_controller.logger')
    def test_initialize_service_raises_exception(self, mock_logger):
        """Test initialize fails when service initialization raises"""
        mock_service = Mock()
        mock_service.initialize = Mock(side_effect=RuntimeError("Service init failed"))
        services = {"service1": mock_service}
        
        controller = ServerController(services=services)
        
        with pytest.raises(RuntimeError) as exc_info:
            controller.initialize()
        
        assert "Service init failed" in str(exc_info.value)
        assert controller._status == ServerStatus.ERROR

    def test_get_status_no_services(self):
        """Test getting status with no services"""
        controller = ServerController()
        controller._status = ServerStatus.RUNNING
        
        status = controller.get_status()
        
        assert status["status"] == ServerStatus.RUNNING.value
        assert status["services"] == {}

    def test_get_status_with_services_having_get_status(self):
        """Test getting status with services that have get_status method"""
        mock_service = Mock()
        mock_service.get_status = Mock(return_value={"component": "ready"})
        services = {"service1": mock_service}
        
        controller = ServerController(services=services)
        controller._status = ServerStatus.RUNNING
        
        status = controller.get_status()
        
        assert status["status"] == ServerStatus.RUNNING.value
        assert status["services"]["service1"] == {"component": "ready"}
        mock_service.get_status.assert_called_once()

    def test_get_status_with_services_without_get_status(self):
        """Test getting status with services without get_status method"""
        mock_service = Mock(spec=[])  # No get_status method
        services = {"service1": mock_service}
        
        controller = ServerController(services=services)
        controller._status = ServerStatus.RUNNING
        
        status = controller.get_status()
        
        assert status["status"] == ServerStatus.RUNNING.value
        assert status["services"]["service1"] == "ready"

    def test_get_status_mixed_services(self):
        """Test getting status with mixed services"""
        mock_service1 = Mock()
        mock_service1.get_status = Mock(return_value={"status": "active"})
        mock_service2 = Mock(spec=[])  # No get_status
        
        services = {"service1": mock_service1, "service2": mock_service2}
        
        controller = ServerController(services=services)
        controller._status = ServerStatus.RUNNING
        
        status = controller.get_status()
        
        assert status["services"]["service1"] == {"status": "active"}
        assert status["services"]["service2"] == "ready"

    def test_get_service_existing(self):
        """Test getting existing service"""
        mock_service = Mock()
        services = {"service1": mock_service}
        
        controller = ServerController(services=services)
        
        result = controller.get_service("service1")
        assert result is mock_service

    def test_get_service_multiple(self):
        """Test getting one of multiple services"""
        mock_service1 = Mock()
        mock_service2 = Mock()
        mock_service3 = Mock()
        services = {
            "service1": mock_service1,
            "service2": mock_service2,
            "service3": mock_service3
        }
        
        controller = ServerController(services=services)
        
        assert controller.get_service("service1") is mock_service1
        assert controller.get_service("service2") is mock_service2
        assert controller.get_service("service3") is mock_service3

    def test_get_service_not_found(self):
        """Test getting non-existent service raises KeyError"""
        mock_service = Mock()
        services = {"service1": mock_service}
        
        controller = ServerController(services=services)
        
        with pytest.raises(KeyError) as exc_info:
            controller.get_service("nonexistent")
        
        assert "Service" in str(exc_info.value)
        assert "nonexistent" in str(exc_info.value)

    def test_get_service_from_empty_controller(self):
        """Test getting service from controller with no services"""
        controller = ServerController()
        
        with pytest.raises(KeyError):
            controller.get_service("any_service")

    def test_status_transitions(self):
        """Test status transitions during initialize"""
        mock_service = Mock()
        mock_service.initialize = Mock()
        services = {"service1": mock_service}
        
        controller = ServerController(services=services)
        assert controller._status == ServerStatus.STARTING
        
        controller.initialize()
        assert controller._status == ServerStatus.RUNNING

    def test_multiple_services_initialization_order(self):
        """Test that all services are initialized"""
        call_order = []
        
        mock_service1 = Mock()
        mock_service1.initialize = Mock(side_effect=lambda: call_order.append(1))
        
        mock_service2 = Mock()
        mock_service2.initialize = Mock(side_effect=lambda: call_order.append(2))
        
        services = {"service1": mock_service1, "service2": mock_service2}
        
        controller = ServerController(services=services)
        controller.initialize()
        
        # Both should be called
        assert len(call_order) == 2
        assert set(call_order) == {1, 2}
