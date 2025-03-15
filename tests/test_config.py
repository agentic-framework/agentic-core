import os
import json
import tempfile
import unittest
from unittest.mock import patch, mock_open, MagicMock

from agentic_core.commands import config

class TestConfig(unittest.TestCase):
    """Test cases for the config module."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary config file for testing
        self.temp_config = {
            "paths": {
                "agentic_root": "/tmp/agentic",
                "tmp_dir": "/tmp/agentic/tmp",
                "projects_dir": "/tmp/agentic/projects",
                "shared_dir": "/tmp/agentic/shared"
            },
            "python": {
                "default_python_version": "3.12",
                "package_manager": "uv"
            },
            "security": {
                "allowed_areas": [
                    "/tmp/agentic",
                    "${HOME}/Agentic"
                ],
                "restricted_areas": [
                    "System files",
                    "Global configurations"
                ]
            }
        }
        
        # Mock the config file path
        self.config_path_patcher = patch('agentic_core.commands.config.CONFIG_PATH', '/tmp/config.json')
        self.mock_config_path = self.config_path_patcher.start()
        
    def tearDown(self):
        """Tear down test fixtures."""
        self.config_path_patcher.stop()

    @patch('agentic_core.commands.config.Config._load_config')
    def test_get(self, mock_load_config):
        """Test getting a value from the configuration."""
        # Create a mock Config instance
        mock_config = MagicMock()
        mock_config.get.return_value = self.temp_config["python"]["default_python_version"]
        
        # Patch the config singleton
        with patch('agentic_core.commands.config.config', mock_config):
            result = config.get('python.default_python_version')
            
            mock_config.get.assert_called_once_with('python.default_python_version', None)
            self.assertEqual(result, "3.12")
            
            # Test getting a non-existent key
            mock_config.get.reset_mock()
            mock_config.get.return_value = None
            
            result = config.get('non_existent_key')
            mock_config.get.assert_called_once_with('non_existent_key', None)
            self.assertIsNone(result)

    @patch('agentic_core.commands.config.Config._load_config')
    def test_set(self, mock_load_config):
        """Test setting a value in the configuration."""
        # Create a mock Config instance
        mock_config = MagicMock()
        mock_config.set.return_value = True
        
        # Patch the config singleton
        with patch('agentic_core.commands.config.config', mock_config):
            result = config.set('python.default_python_version', '3.11')
            
            mock_config.set.assert_called_once_with('python.default_python_version', '3.11')
            self.assertTrue(result)
            
            # Test setting with a failure
            mock_config.set.reset_mock()
            mock_config.set.return_value = False
            
            result = config.set('non_existent_key', 'value')
            mock_config.set.assert_called_once_with('non_existent_key', 'value')
            self.assertFalse(result)

    @patch('agentic_core.commands.config.Config._load_config')
    def test_get_path(self, mock_load_config):
        """Test getting a path from the configuration."""
        # Create a mock Config instance
        mock_config = MagicMock()
        mock_config.get_path.return_value = '/tmp/agentic'
        
        # Patch the config singleton
        with patch('agentic_core.commands.config.config', mock_config):
            result = config.get_path('agentic_root')
            
            mock_config.get_path.assert_called_once_with('agentic_root')
            self.assertEqual(result, '/tmp/agentic')
            
            # Test getting a non-existent path
            mock_config.get_path.reset_mock()
            mock_config.get_path.return_value = None
            
            result = config.get_path('non_existent_path')
            mock_config.get_path.assert_called_once_with('non_existent_path')
            self.assertIsNone(result)

    @patch('agentic_core.commands.config.get')
    def test_get_config(self, mock_get):
        """Test the get_config CLI function."""
        # Test getting a top-level key
        mock_get.return_value = self.temp_config["paths"]
        
        with patch('builtins.print') as mock_print:
            result = config.get_config(['paths'])
            
            mock_get.assert_called_once_with('paths')
            mock_print.assert_called_once()
            self.assertEqual(result, 0)
        
        # Test getting a nested key
        mock_get.reset_mock()
        mock_get.return_value = '/tmp/agentic'
        
        with patch('builtins.print') as mock_print:
            result = config.get_config(['paths.agentic_root'])
            
            mock_get.assert_called_once_with('paths.agentic_root')
            mock_print.assert_called_once()
            self.assertEqual(result, 0)
        
        # Test getting a non-existent key
        mock_get.reset_mock()
        mock_get.return_value = None
        
        with patch('builtins.print') as mock_print:
            result = config.get_config(['non_existent'])
            
            mock_get.assert_called_once_with('non_existent')
            mock_print.assert_called_once_with("Key 'non_existent' not found in configuration")
            self.assertEqual(result, 1)

    @patch('agentic_core.commands.config.set')
    def test_set_config(self, mock_set):
        """Test the set_config CLI function."""
        # Test setting a value successfully
        mock_set.return_value = True
        
        with patch('builtins.print') as mock_print:
            result = config.set_config(['python.default_python_version', '3.11'])
            
            mock_set.assert_called_once()
            mock_print.assert_called_once()
            self.assertEqual(result, 0)
        
        # Test setting a value with failure
        mock_set.reset_mock()
        mock_set.return_value = False
        
        with patch('builtins.print') as mock_print:
            result = config.set_config(['non_existent.key', 'value'])
            
            mock_set.assert_called_once()
            mock_print.assert_called_once_with('Failed to set non_existent.key')
            self.assertEqual(result, 1)

    @patch('agentic_core.commands.config.get')
    @patch('agentic_core.commands.config.get_all')
    def test_list_config(self, mock_get_all, mock_get):
        """Test the list_config CLI function."""
        # Test listing all config
        mock_get_all.return_value = self.temp_config
        
        with patch('builtins.print') as mock_print:
            result = config.list_config([])
            
            mock_get_all.assert_called_once()
            mock_print.assert_called_once()
            self.assertEqual(result, 0)
        
        # Test listing a specific section
        mock_get_all.reset_mock()
        mock_get.return_value = self.temp_config["paths"]
        
        with patch('builtins.print') as mock_print:
            result = config.list_config(['--section', 'paths'])
            
            mock_get.assert_called_once_with('paths')
            mock_print.assert_called()
            self.assertEqual(result, 0)
        
        # Test listing a non-existent section
        mock_get.reset_mock()
        mock_get.return_value = None
        
        with patch('builtins.print') as mock_print:
            result = config.list_config(['--section', 'non_existent'])
            
            mock_get.assert_called_once_with('non_existent')
            mock_print.assert_called_once_with("Section 'non_existent' not found in configuration")
            self.assertEqual(result, 1)

if __name__ == '__main__':
    unittest.main()
