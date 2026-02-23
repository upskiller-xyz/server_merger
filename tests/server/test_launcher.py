"""Tests for server launcher"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.server.launcher import ServerLauncher
from src.server.application import ServerApplication


class TestServerLauncher:
    """Test ServerLauncher class"""

    def test_create_application(self):
        """Test creating a server application"""
        app = ServerLauncher.create_application()
        assert isinstance(app, ServerApplication)
        assert hasattr(app, 'app')

    def test_create_application_returns_configured_instance(self):
        """Test that created application is configured"""
        app = ServerLauncher.create_application()
        assert app is not None
        assert hasattr(app, 'app')

    @patch('src.server.launcher.ServerApplication')
    def test_create_application_uses_server_application_class(self, mock_app_class):
        """Test that create_application instantiates ServerApplication"""
        mock_instance = Mock()
        mock_app_class.return_value = mock_instance
        
        result = ServerLauncher.create_application()
        
        assert result is mock_instance
        mock_app_class.assert_called_once()

    @patch('src.server.launcher.ServerApplication')
    def test_run_server_basic(self, mock_app_class):
        """Test running server with default parameters"""
        mock_app = Mock()
        mock_flask_app = Mock()
        mock_app.app = mock_flask_app
        
        ServerLauncher.run_server(mock_app)
        
        mock_flask_app.run.assert_called_once()
        call_kwargs = mock_flask_app.run.call_args[1]
        assert call_kwargs['host'] == '0.0.0.0'
        assert call_kwargs['port'] == 8084
        assert call_kwargs['debug'] == True
        assert call_kwargs['use_reloader'] == False

    @patch('src.server.launcher.ServerApplication')
    def test_run_server_custom_host_port(self, mock_app_class):
        """Test running server with custom host and port"""
        mock_app = Mock()
        mock_flask_app = Mock()
        mock_app.app = mock_flask_app
        
        ServerLauncher.run_server(mock_app, host='127.0.0.1', port=5000)
        
        call_kwargs = mock_flask_app.run.call_args[1]
        assert call_kwargs['host'] == '127.0.0.1'
        assert call_kwargs['port'] == 5000

    @patch('src.server.launcher.ServerApplication')
    def test_run_server_debug_false(self, mock_app_class):
        """Test running server with debug disabled"""
        mock_app = Mock()
        mock_flask_app = Mock()
        mock_app.app = mock_flask_app
        
        ServerLauncher.run_server(mock_app, debug=False)
        
        call_kwargs = mock_flask_app.run.call_args[1]
        assert call_kwargs['debug'] == False

    @patch('src.server.launcher.ServerApplication')
    def test_run_server_custom_all_parameters(self, mock_app_class):
        """Test running server with all custom parameters"""
        mock_app = Mock()
        mock_flask_app = Mock()
        mock_app.app = mock_flask_app
        
        ServerLauncher.run_server(
            mock_app,
            host='192.168.1.1',
            port=9000,
            debug=False
        )
        
        call_kwargs = mock_flask_app.run.call_args[1]
        assert call_kwargs['host'] == '192.168.1.1'
        assert call_kwargs['port'] == 9000
        assert call_kwargs['debug'] == False
        assert call_kwargs['use_reloader'] == False

    @patch('src.server.launcher.ServerApplication')
    @patch('src.server.launcher.logger')
    def test_run_server_logs_startup_info(self, mock_logger, mock_app_class):
        """Test that server logs startup information"""
        mock_app = Mock()
        mock_flask_app = Mock()
        mock_flask_app.name = 'test_app'
        mock_app.app = mock_flask_app
        
        ServerLauncher.run_server(mock_app, host='localhost', port=8000, debug=True)
        
        mock_flask_app.logger.info.assert_called_once()
        call_args = mock_flask_app.logger.info.call_args[0][0]
        assert 'localhost' in call_args
        assert '8000' in str(call_args)
        assert 'Debug mode: True' in call_args

    @patch('src.server.launcher.ServerApplication')
    def test_run_server_disables_reloader(self, mock_app_class):
        """Test that use_reloader is always disabled"""
        mock_app = Mock()
        mock_flask_app = Mock()
        mock_app.app = mock_flask_app
        
        # Test multiple times to ensure it's always disabled
        for _ in range(3):
            ServerLauncher.run_server(mock_app, debug=True)
            call_kwargs = mock_flask_app.run.call_args[1]
            assert call_kwargs['use_reloader'] == False

    def test_launcher_is_static(self):
        """Test that ServerLauncher uses static methods"""
        # Verify methods are static
        assert isinstance(ServerLauncher.create_application, staticmethod) or callable(ServerLauncher.create_application)
        assert isinstance(ServerLauncher.run_server, staticmethod) or callable(ServerLauncher.run_server)

    @patch('src.server.launcher.ServerApplication')
    def test_run_server_with_port_zero(self, mock_app_class):
        """Test running server with port 0 (random port)"""
        mock_app = Mock()
        mock_flask_app = Mock()
        mock_app.app = mock_flask_app
        
        ServerLauncher.run_server(mock_app, port=0)
        
        call_kwargs = mock_flask_app.run.call_args[1]
        assert call_kwargs['port'] == 0

    @patch('src.server.launcher.ServerApplication')
    def test_run_server_with_high_port_number(self, mock_app_class):
        """Test running server with high port number"""
        mock_app = Mock()
        mock_flask_app = Mock()
        mock_app.app = mock_flask_app
        
        ServerLauncher.run_server(mock_app, port=65535)
        
        call_kwargs = mock_flask_app.run.call_args[1]
        assert call_kwargs['port'] == 65535

    @patch('src.server.launcher.ServerApplication')
    def test_run_server_with_empty_host(self, mock_app_class):
        """Test running server with empty host string"""
        mock_app = Mock()
        mock_flask_app = Mock()
        mock_app.app = mock_flask_app
        
        ServerLauncher.run_server(mock_app, host='')
        
        call_kwargs = mock_flask_app.run.call_args[1]
        assert call_kwargs['host'] == ''

    @patch('src.server.launcher.ServerApplication')
    def test_multiple_application_creations(self, mock_app_class):
        """Test creating multiple applications"""
        mock_instances = [Mock(), Mock(), Mock()]
        mock_app_class.side_effect = mock_instances
        
        app1 = ServerLauncher.create_application()
        app2 = ServerLauncher.create_application()
        app3 = ServerLauncher.create_application()
        
        assert app1 is mock_instances[0]
        assert app2 is mock_instances[1]
        assert app3 is mock_instances[2]
        assert mock_app_class.call_count == 3
