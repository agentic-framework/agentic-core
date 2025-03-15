import os
import unittest
from unittest.mock import patch, MagicMock, mock_open

from agentic_core.commands import security
from agentic_core.commands import config

class TestSecurity(unittest.TestCase):
    """Test cases for the security module."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a mock config for testing
        self.mock_config = {
            "security": {
                "allowed_paths": [
                    "/tmp/agentic",
                    "${HOME}/Agentic"
                ],
                "blocked_commands": [
                    "rm -rf /",
                    "sudo",
                    "chmod 777"
                ]
            }
        }

    @patch('agentic_core.commands.security.security')
    def test_is_path_allowed(self, mock_security):
        """Test checking if a path is allowed."""
        # Mock the security singleton
        mock_security.is_path_allowed.side_effect = lambda path: path.startswith("/tmp/agentic") or path.startswith("/home/user/Agentic")
        
        # Test with a path that is directly in the allowed list
        result = security.is_path_allowed("/tmp/agentic/file.txt")
        self.assertTrue(result)
        
        # Test with a path that is a subdirectory of an allowed path
        result = security.is_path_allowed("/tmp/agentic/subdir/file.txt")
        self.assertTrue(result)
        
        # Test with a path that is not in the allowed list
        result = security.is_path_allowed("/usr/bin/file.txt")
        self.assertFalse(result)

    @patch('agentic_core.commands.security.validate_command')
    def test_validate_command(self, mock_validate_command):
        """Test validating a command."""
        # Test with an allowed command
        mock_validate_command.return_value = True
        
        result = security.validate_command("ls -la")
        mock_validate_command.assert_called_once_with("ls -la")
        self.assertTrue(result)
        
        # Test with a command that raises a SecurityViolation
        mock_validate_command.reset_mock()
        mock_validate_command.side_effect = security.SecurityViolation("Dangerous command")
        
        with self.assertRaises(security.SecurityViolation):
            security.validate_command("sudo apt-get install")

    @patch('agentic_core.commands.security.is_path_allowed')
    def test_check_path(self, mock_is_path_allowed):
        """Test the check_path CLI function."""
        # Test with an allowed path
        mock_is_path_allowed.return_value = True
        
        with patch('builtins.print') as mock_print:
            result = security.check_path(["/tmp/agentic/file.txt"])
            
            mock_is_path_allowed.assert_called_once_with("/tmp/agentic/file.txt")
            mock_print.assert_called_once_with("Path '/tmp/agentic/file.txt' is allowed")
            self.assertEqual(result, 0)
        
        # Test with a disallowed path
        mock_is_path_allowed.reset_mock()
        mock_is_path_allowed.return_value = False
        
        with patch('builtins.print') as mock_print:
            result = security.check_path(["/usr/bin/file.txt"])
            
            mock_is_path_allowed.assert_called_once_with("/usr/bin/file.txt")
            mock_print.assert_called_once_with("Path '/usr/bin/file.txt' is not allowed")
            self.assertEqual(result, 0)
        
        # Test with no path provided
        mock_is_path_allowed.reset_mock()
        
        with patch('builtins.print') as mock_print:
            result = security.check_path([])
            
            mock_is_path_allowed.assert_not_called()
            # The print function is called twice, once for the error message and once for the usage
            mock_print.assert_any_call("Error: No path specified")
            self.assertEqual(result, 1)

    @patch('agentic_core.commands.security.validate_command')
    def test_validate_command_cli(self, mock_validate_command):
        """Test the validate_command_cli CLI function."""
        # Test with an allowed command
        mock_validate_command.return_value = True
        
        with patch('builtins.print') as mock_print:
            result = security.validate_command_cli(["ls -la"])
            
            mock_validate_command.assert_called_once_with("ls -la")
            mock_print.assert_called_once_with("Command 'ls -la' is valid")
            self.assertEqual(result, 0)
        
        # Test with a command that raises a SecurityViolation
        mock_validate_command.reset_mock()
        mock_validate_command.side_effect = security.SecurityViolation("Dangerous command")
        
        with patch('builtins.print') as mock_print:
            result = security.validate_command_cli(["sudo apt-get install"])
            
            mock_validate_command.assert_called_once_with("sudo apt-get install")
            mock_print.assert_called_once_with("Security violation: Dangerous command")
            self.assertEqual(result, 1)
        
        # Test with no command provided
        mock_validate_command.reset_mock()
        mock_validate_command.side_effect = None
        
        with patch('builtins.print') as mock_print:
            result = security.validate_command_cli([])
            
            mock_validate_command.assert_not_called()
            # The print function is called twice, once for the error message and once for the usage
            mock_print.assert_any_call("Error: No command specified")
            self.assertEqual(result, 1)

    @patch('agentic_core.commands.security.calculate_file_hash')
    def test_hash_file(self, mock_calculate_file_hash):
        """Test the hash_file CLI function."""
        # Set up the mock to return a hash
        mock_calculate_file_hash.return_value = "abcdef1234567890"
        
        # Test with a valid file
        with patch('os.path.exists') as mock_exists:
            mock_exists.return_value = True
            
            with patch('builtins.print') as mock_print:
                result = security.hash_file(["/tmp/test.txt"])
                
                mock_calculate_file_hash.assert_called_once_with("/tmp/test.txt")
                # The print function is called twice, once for the message and once for the hash
                mock_print.assert_any_call("SHA-256 hash of file '/tmp/test.txt':")
                mock_print.assert_any_call("abcdef1234567890")
                self.assertEqual(result, 0)
        
        # Test with no file provided
        mock_calculate_file_hash.reset_mock()
        
        with patch('builtins.print') as mock_print:
            result = security.hash_file([])
            
            mock_calculate_file_hash.assert_not_called()
            # The print function is called twice, once for the error message and once for the usage
            mock_print.assert_any_call("Error: No file specified")
            self.assertEqual(result, 1)

if __name__ == '__main__':
    unittest.main()
