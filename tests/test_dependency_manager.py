#!/usr/bin/env python3
"""
Tests for the dependency_manager module.
"""

import os
import sys
import json
import unittest
from unittest.mock import patch, MagicMock, mock_open

# Add the src directory to the path so we can import the module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agentic_core.commands.dependency_manager import (
    get_dependency_config,
    parse_version,
    compare_versions,
    get_installed_version,
    check_dependency,
    install_dependency,
    update_dependency,
    check_dependency_cli,
    install_dependency_cli,
    update_dependency_cli,
    list_dependencies_cli,
    fallback_cli
)

class TestDependencyManager(unittest.TestCase):
    """Test cases for the dependency_manager module."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a mock for the config module
        self.config_patcher = patch('src.agentic_core.commands.dependency_manager.config')
        self.mock_config = self.config_patcher.start()
        self.mock_config.get.return_value = {}

    def tearDown(self):
        """Tear down test fixtures."""
        self.config_patcher.stop()

    def test_parse_version(self):
        """Test parsing version strings."""
        self.assertEqual(parse_version("1.2.3"), (1, 2, 3))
        self.assertEqual(parse_version("0.1.0"), (0, 1, 0))
        self.assertEqual(parse_version("10.20.30"), (10, 20, 30))

    def test_compare_versions(self):
        """Test comparing version strings."""
        self.assertEqual(compare_versions("1.2.3", "1.2.3"), 0)
        self.assertEqual(compare_versions("1.2.3", "1.2.4"), -1)
        self.assertEqual(compare_versions("1.2.3", "1.2.2"), 1)
        self.assertEqual(compare_versions("1.2.3", "1.3.0"), -1)
        self.assertEqual(compare_versions("2.0.0", "1.9.9"), 1)

    @patch('src.agentic_core.commands.dependency_manager.subprocess.run')
    def test_get_installed_version(self, mock_run):
        """Test getting the installed version of a dependency."""
        # Mock the subprocess.run result
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = "uv 0.1.11\n"
        mock_run.return_value = mock_process

        # Test with a valid dependency
        with patch('src.agentic_core.commands.dependency_manager.get_dependency_config') as mock_get_config:
            mock_get_config.return_value = {
                "version_command": "uv --version",
                "version_regex": r"(\d+\.\d+\.\d+)"
            }
            self.assertEqual(get_installed_version("uv"), "0.1.11")

        # Test with a non-existent dependency
        with patch('src.agentic_core.commands.dependency_manager.get_dependency_config') as mock_get_config:
            mock_get_config.return_value = {}
            self.assertIsNone(get_installed_version("nonexistent"))

        # Test with a failed command
        mock_process.returncode = 1
        mock_process.stderr = "Command not found"
        with patch('src.agentic_core.commands.dependency_manager.get_dependency_config') as mock_get_config:
            mock_get_config.return_value = {
                "version_command": "nonexistent --version",
                "version_regex": r"(\d+\.\d+\.\d+)"
            }
            self.assertIsNone(get_installed_version("nonexistent"))

    @patch('src.agentic_core.commands.dependency_manager.get_installed_version')
    def test_check_dependency(self, mock_get_version):
        """Test checking a dependency."""
        # Test with an installed dependency that meets requirements
        mock_get_version.return_value = "0.1.11"
        with patch('src.agentic_core.commands.dependency_manager.get_dependency_config') as mock_get_config:
            mock_get_config.return_value = {
                "min_version": "0.1.0",
                "recommended_version": "0.1.11",
                "fallback": {"enabled": True}
            }
            result = check_dependency("uv")
            self.assertTrue(result["installed"])
            self.assertTrue(result["meets_min_requirements"])
            self.assertTrue(result["is_recommended_version"])
            self.assertTrue(result["fallback_available"])

        # Test with an installed dependency that doesn't meet requirements
        mock_get_version.return_value = "0.0.9"
        with patch('src.agentic_core.commands.dependency_manager.get_dependency_config') as mock_get_config:
            mock_get_config.return_value = {
                "min_version": "0.1.0",
                "recommended_version": "0.1.11",
                "fallback": {"enabled": True}
            }
            result = check_dependency("uv")
            self.assertTrue(result["installed"])
            self.assertFalse(result["meets_min_requirements"])
            self.assertFalse(result["is_recommended_version"])

        # Test with a non-installed dependency
        mock_get_version.return_value = None
        with patch('src.agentic_core.commands.dependency_manager.get_dependency_config') as mock_get_config:
            mock_get_config.return_value = {
                "min_version": "0.1.0",
                "recommended_version": "0.1.11"
            }
            result = check_dependency("nonexistent")
            self.assertFalse(result["installed"])
            self.assertFalse(result["meets_min_requirements"])
            self.assertFalse(result["is_recommended_version"])

    @patch('src.agentic_core.commands.dependency_manager.subprocess.run')
    def test_install_dependency(self, mock_run):
        """Test installing a dependency."""
        # Mock the subprocess.run result
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_run.return_value = mock_process

        # Test with a valid dependency
        with patch('src.agentic_core.commands.dependency_manager.get_dependency_config') as mock_get_config:
            mock_get_config.return_value = {
                "install_command": "curl -LsSf https://astral.sh/uv/install.sh | sh"
            }
            self.assertTrue(install_dependency("uv"))

        # Test with a non-existent dependency
        with patch('src.agentic_core.commands.dependency_manager.get_dependency_config') as mock_get_config:
            mock_get_config.return_value = {}
            self.assertFalse(install_dependency("nonexistent"))

        # Test with a failed command
        mock_process.returncode = 1
        mock_process.stderr = "Installation failed"
        with patch('src.agentic_core.commands.dependency_manager.get_dependency_config') as mock_get_config:
            mock_get_config.return_value = {
                "install_command": "nonexistent-command"
            }
            self.assertFalse(install_dependency("uv"))

    @patch('src.agentic_core.commands.dependency_manager.install_dependency')
    def test_update_dependency(self, mock_install):
        """Test updating a dependency."""
        # Test with a successful update
        mock_install.return_value = True
        self.assertTrue(update_dependency("uv"))

        # Test with a failed update
        mock_install.return_value = False
        self.assertFalse(update_dependency("uv"))

    @patch('src.agentic_core.commands.dependency_manager.check_dependency')
    def test_check_dependency_cli(self, mock_check):
        """Test the check_dependency_cli function."""
        # Test with a valid dependency that meets requirements
        mock_check.return_value = {
            "installed": True,
            "meets_min_requirements": True
        }
        self.assertEqual(check_dependency_cli(["uv"]), 0)

        # Test with a valid dependency that doesn't meet requirements
        mock_check.return_value = {
            "installed": True,
            "meets_min_requirements": False
        }
        self.assertEqual(check_dependency_cli(["uv"]), 1)

        # Test with a non-installed dependency
        mock_check.return_value = {
            "installed": False
        }
        self.assertEqual(check_dependency_cli(["nonexistent"]), 1)

        # Test with no arguments
        self.assertEqual(check_dependency_cli([]), 1)

    @patch('src.agentic_core.commands.dependency_manager.install_dependency')
    def test_install_dependency_cli(self, mock_install):
        """Test the install_dependency_cli function."""
        # Test with a successful installation
        mock_install.return_value = True
        self.assertEqual(install_dependency_cli(["uv"]), 0)

        # Test with a failed installation
        mock_install.return_value = False
        self.assertEqual(install_dependency_cli(["uv"]), 1)

        # Test with no arguments
        self.assertEqual(install_dependency_cli([]), 1)

    @patch('src.agentic_core.commands.dependency_manager.update_dependency')
    def test_update_dependency_cli(self, mock_update):
        """Test the update_dependency_cli function."""
        # Test with a successful update
        mock_update.return_value = True
        self.assertEqual(update_dependency_cli(["uv"]), 0)

        # Test with a failed update
        mock_update.return_value = False
        self.assertEqual(update_dependency_cli(["uv"]), 1)

        # Test with no arguments
        self.assertEqual(update_dependency_cli([]), 1)

    @patch('src.agentic_core.commands.dependency_manager.check_dependency')
    def test_list_dependencies_cli(self, mock_check):
        """Test the list_dependencies_cli function."""
        # Mock the config.get function to return a list of dependencies
        self.mock_config.get.return_value = {}

        # Mock the check_dependency function
        mock_check.return_value = {
            "installed": True,
            "meets_min_requirements": True
        }

        # Test with no arguments
        with patch('src.agentic_core.commands.dependency_manager.DEFAULT_DEPENDENCIES', {"uv": {}, "python": {}}):
            self.assertEqual(list_dependencies_cli([]), 0)

if __name__ == '__main__':
    unittest.main()
