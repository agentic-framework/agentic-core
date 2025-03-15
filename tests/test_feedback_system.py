import os
import json
import unittest
from unittest.mock import patch, MagicMock, mock_open
from datetime import datetime
import uuid

from agentic_core.commands import feedback_system

class TestFeedbackSystem(unittest.TestCase):
    """Test cases for the feedback system module."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a mock feedback for testing
        self.mock_feedback = {
            "id": "12345678-1234-5678-1234-567812345678",
            "type": "issue",
            "title": "Test Issue",
            "description": "This is a test issue",
            "priority": "medium",
            "tags": ["test", "issue"],
            "context": {},
            "status": "new",
            "created_at": "2025-01-01T00:00:00",
            "updated_at": "2025-01-01T00:00:00",
            "comments": []
        }
        
        # Mock the feedback directory
        self.feedback_dir_patcher = patch('agentic_core.commands.feedback_system.FEEDBACK_DIR', '/tmp/feedback')
        self.mock_feedback_dir = self.feedback_dir_patcher.start()
        
        # Mock the uuid.uuid4 function to return a predictable value
        self.uuid_patcher = patch('uuid.uuid4')
        self.mock_uuid = self.uuid_patcher.start()
        self.mock_uuid.return_value = uuid.UUID("12345678-1234-5678-1234-567812345678")
        
        # Mock the datetime.now function to return a predictable value
        self.datetime_patcher = patch('datetime.datetime')
        self.mock_datetime = self.datetime_patcher.start()
        self.mock_datetime.now.return_value = datetime.fromisoformat("2025-01-01T00:00:00")
        self.mock_datetime.fromisoformat = datetime.fromisoformat
        
    def tearDown(self):
        """Tear down test fixtures."""
        self.feedback_dir_patcher.stop()
        self.uuid_patcher.stop()
        self.datetime_patcher.stop()

    @patch('os.makedirs')
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    def test_submit_feedback(self, mock_json_dump, mock_file_open, mock_makedirs):
        """Test submitting feedback."""
        # Create a mock FeedbackSystem instance
        feedback_system_instance = feedback_system.FeedbackSystem()
        
        # Test submitting feedback
        result = feedback_system_instance.submit_feedback(
            feedback_system.FeedbackType.ISSUE,
            "Test Issue",
            "This is a test issue",
            feedback_system.FeedbackPriority.MEDIUM,
            ["test", "issue"],
            {}
        )
        
        # Check that the directories were created
        mock_makedirs.assert_called()
        
        # Check that the file was opened for writing
        mock_file_open.assert_called_once_with('/tmp/feedback/issue/12345678-1234-5678-1234-567812345678.json', 'w')
        
        # Check that the feedback was written to the file
        mock_json_dump.assert_called_once()
        args, kwargs = mock_json_dump.call_args
        self.assertEqual(args[0]["id"], "12345678-1234-5678-1234-567812345678")
        self.assertEqual(args[0]["type"], "issue")
        self.assertEqual(args[0]["title"], "Test Issue")
        self.assertEqual(args[0]["description"], "This is a test issue")
        self.assertEqual(args[0]["priority"], "medium")
        self.assertEqual(args[0]["tags"], ["test", "issue"])
        self.assertEqual(args[0]["status"], "new")
        
        # Check the return value
        self.assertEqual(result, "12345678-1234-5678-1234-567812345678")

    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data=json.dumps({
        "id": "12345678-1234-5678-1234-567812345678",
        "type": "issue",
        "title": "Test Issue",
        "description": "This is a test issue",
        "priority": "medium",
        "tags": ["test", "issue"],
        "context": {},
        "status": "new",
        "created_at": "2025-01-01T00:00:00",
        "updated_at": "2025-01-01T00:00:00",
        "comments": []
    }))
    def test_get_feedback(self, mock_file_open, mock_exists):
        """Test getting feedback by ID."""
        # Set up the mock to return True for the file existence check
        mock_exists.return_value = True
        
        # Create a mock FeedbackSystem instance
        feedback_system_instance = feedback_system.FeedbackSystem()
        
        # Test getting feedback
        result = feedback_system_instance.get_feedback("12345678-1234-5678-1234-567812345678")
        
        # Check that the file was opened for reading
        mock_file_open.assert_called_once_with('/tmp/feedback/issue/12345678-1234-5678-1234-567812345678.json', 'r')
        
        # Check the return value
        self.assertIsNotNone(result)
        if result:  # Only check properties if result is not None
            self.assertEqual(result["id"], "12345678-1234-5678-1234-567812345678")
            self.assertEqual(result["type"], "issue")
            self.assertEqual(result["title"], "Test Issue")
            self.assertEqual(result["description"], "This is a test issue")
            self.assertEqual(result["priority"], "medium")
            self.assertEqual(result["tags"], ["test", "issue"])
            self.assertEqual(result["status"], "new")
        
        # Test getting non-existent feedback
        mock_exists.return_value = False
        mock_file_open.reset_mock()
        
        result = feedback_system_instance.get_feedback("non-existent-id")
        
        # Check that the file was not opened
        mock_file_open.assert_not_called()
        
        # Check the return value
        self.assertIsNone(result)

    @patch('agentic_core.commands.feedback_system.FeedbackSystem.get_feedback')
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    def test_update_feedback(self, mock_json_dump, mock_file_open, mock_get_feedback):
        """Test updating feedback."""
        # Set up the mock to return a feedback object
        mock_get_feedback.return_value = self.mock_feedback.copy()
        
        # Create a mock FeedbackSystem instance
        feedback_system_instance = feedback_system.FeedbackSystem()
        
        # Test updating feedback
        result = feedback_system_instance.update_feedback(
            "12345678-1234-5678-1234-567812345678",
            {"status": "acknowledged", "priority": "high"}
        )
        
        # Check that the feedback was retrieved
        mock_get_feedback.assert_called_once_with("12345678-1234-5678-1234-567812345678")
        
        # Check that the file was opened for writing
        mock_file_open.assert_called_once_with('/tmp/feedback/issue/12345678-1234-5678-1234-567812345678.json', 'w')
        
        # Check that the feedback was written to the file with the updates
        mock_json_dump.assert_called_once()
        args, kwargs = mock_json_dump.call_args
        self.assertEqual(args[0]["id"], "12345678-1234-5678-1234-567812345678")
        self.assertEqual(args[0]["status"], "acknowledged")
        self.assertEqual(args[0]["priority"], "high")
        
        # Check the return value
        self.assertTrue(result)
        
        # Test updating non-existent feedback
        mock_get_feedback.reset_mock()
        mock_file_open.reset_mock()
        mock_json_dump.reset_mock()
        mock_get_feedback.return_value = None
        
        result = feedback_system_instance.update_feedback(
            "non-existent-id",
            {"status": "acknowledged"}
        )
        
        # Check that the feedback was retrieved
        mock_get_feedback.assert_called_once_with("non-existent-id")
        
        # Check that the file was not opened
        mock_file_open.assert_not_called()
        
        # Check that the feedback was not written to the file
        mock_json_dump.assert_not_called()
        
        # Check the return value
        self.assertFalse(result)

    @patch('agentic_core.commands.feedback_system.FeedbackSystem.get_feedback')
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    def test_add_comment(self, mock_json_dump, mock_file_open, mock_get_feedback):
        """Test adding a comment to feedback."""
        # Set up the mock to return a feedback object
        mock_get_feedback.return_value = self.mock_feedback.copy()
        
        # Create a mock FeedbackSystem instance
        feedback_system_instance = feedback_system.FeedbackSystem()
        
        # Test adding a comment
        result = feedback_system_instance.add_comment(
            "12345678-1234-5678-1234-567812345678",
            "This is a test comment",
            "Test User"
        )
        
        # Check that the feedback was retrieved
        mock_get_feedback.assert_called_once_with("12345678-1234-5678-1234-567812345678")
        
        # Check that the file was opened for writing
        mock_file_open.assert_called_once_with('/tmp/feedback/issue/12345678-1234-5678-1234-567812345678.json', 'w')
        
        # Check that the feedback was written to the file with the comment
        mock_json_dump.assert_called_once()
        args, kwargs = mock_json_dump.call_args
        self.assertEqual(args[0]["id"], "12345678-1234-5678-1234-567812345678")
        self.assertEqual(len(args[0]["comments"]), 1)
        self.assertEqual(args[0]["comments"][0]["author"], "Test User")
        self.assertEqual(args[0]["comments"][0]["content"], "This is a test comment")
        
        # Check the return value
        self.assertTrue(result)
        
        # Test adding a comment to non-existent feedback
        mock_get_feedback.reset_mock()
        mock_file_open.reset_mock()
        mock_json_dump.reset_mock()
        mock_get_feedback.return_value = None
        
        result = feedback_system_instance.add_comment(
            "non-existent-id",
            "This is a test comment",
            "Test User"
        )
        
        # Check that the feedback was retrieved
        mock_get_feedback.assert_called_once_with("non-existent-id")
        
        # Check that the file was not opened
        mock_file_open.assert_not_called()
        
        # Check that the feedback was not written to the file
        mock_json_dump.assert_not_called()
        
        # Check the return value
        self.assertFalse(result)

    @patch('os.listdir')
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data=json.dumps({
        "id": "12345678-1234-5678-1234-567812345678",
        "type": "issue",
        "title": "Test Issue",
        "description": "This is a test issue",
        "priority": "medium",
        "tags": ["test", "issue"],
        "context": {},
        "status": "new",
        "created_at": "2025-01-01T00:00:00",
        "updated_at": "2025-01-01T00:00:00",
        "comments": []
    }))
    def test_list_feedback(self, mock_file_open, mock_exists, mock_listdir):
        """Test listing feedback."""
        # Set up the mocks
        mock_exists.return_value = True
        mock_listdir.return_value = ["12345678-1234-5678-1234-567812345678.json"]
        
        # Create a mock FeedbackSystem instance
        feedback_system_instance = feedback_system.FeedbackSystem()
        
        # Test listing all feedback
        result = feedback_system_instance.list_feedback()
        
        # Check that the directory was checked
        mock_exists.assert_called()
        
        # Check that the directory was listed
        mock_listdir.assert_called()
        
        # Check that the file was opened for reading
        mock_file_open.assert_called()
        
        # Check the return value
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "12345678-1234-5678-1234-567812345678")
        self.assertEqual(result[0]["type"], "issue")
        self.assertEqual(result[0]["title"], "Test Issue")
        self.assertEqual(result[0]["description"], "This is a test issue")
        self.assertEqual(result[0]["priority"], "medium")
        self.assertEqual(result[0]["tags"], ["test", "issue"])
        self.assertEqual(result[0]["status"], "new")
        
        # Test listing feedback with filters
        mock_exists.reset_mock()
        mock_listdir.reset_mock()
        mock_file_open.reset_mock()
        
        result = feedback_system_instance.list_feedback(
            feedback_type="issue",
            status="new",
            priority="medium",
            tags=["test"]
        )
        
        # Check that the directory was checked
        mock_exists.assert_called()
        
        # Check that the directory was listed
        mock_listdir.assert_called()
        
        # Check that the file was opened for reading
        mock_file_open.assert_called()
        
        # Check the return value
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "12345678-1234-5678-1234-567812345678")

    @patch('agentic_core.commands.feedback_system.FeedbackSystem.submit_feedback')
    def test_submit_feedback_cli(self, mock_submit_feedback):
        """Test the submit_feedback CLI function."""
        # Set up the mock to return a feedback ID
        mock_submit_feedback.return_value = "12345678-1234-5678-1234-567812345678"
        
        # Test submitting feedback
        with patch('builtins.print') as mock_print:
            result = feedback_system.submit_feedback([
                "--type", "issue",
                "--title", "Test Issue",
                "--description", "This is a test issue",
                "--priority", "medium",
                "--tags", "test", "issue"
            ])
            
            # Check that the feedback was submitted
            mock_submit_feedback.assert_called_once()
            args, kwargs = mock_submit_feedback.call_args
            self.assertEqual(args[0], "issue")
            self.assertEqual(args[1], "Test Issue")
            self.assertEqual(args[2], "This is a test issue")
            self.assertEqual(args[3], "medium")
            self.assertEqual(args[4], ["test", "issue"])
            
            # Check that the result was printed
            mock_print.assert_called_once_with("Feedback submitted with ID: 12345678-1234-5678-1234-567812345678")
            
            # Check the return value
            self.assertEqual(result, 0)
        
        # Test submitting feedback with missing required arguments
        mock_submit_feedback.reset_mock()
        
        with patch('builtins.print') as mock_print:
            result = feedback_system.submit_feedback([])
            
            # Check that the feedback was not submitted
            mock_submit_feedback.assert_not_called()
            
            # Check that an error was printed
            mock_print.assert_called()
            
            # Check the return value
            self.assertEqual(result, 1)

    @patch('agentic_core.commands.feedback_system.FeedbackSystem.get_feedback')
    def test_get_feedback_cli(self, mock_get_feedback):
        """Test the get_feedback CLI function."""
        # Set up the mock to return a feedback object
        mock_get_feedback.return_value = self.mock_feedback.copy()
        
        # Test getting feedback
        with patch('builtins.print') as mock_print:
            result = feedback_system.get_feedback(["12345678-1234-5678-1234-567812345678"])
            
            # Check that the feedback was retrieved
            mock_get_feedback.assert_called_once_with("12345678-1234-5678-1234-567812345678")
            
            # Check that the result was printed
            mock_print.assert_called_once()
            
            # Check the return value
            self.assertEqual(result, 0)
        
        # Test getting non-existent feedback
        mock_get_feedback.reset_mock()
        mock_get_feedback.return_value = None
        
        with patch('builtins.print') as mock_print:
            result = feedback_system.get_feedback(["non-existent-id"])
            
            # Check that the feedback was retrieved
            mock_get_feedback.assert_called_once_with("non-existent-id")
            
            # Check that an error was printed
            mock_print.assert_called_once_with("Feedback not found: non-existent-id")
            
            # Check the return value
            self.assertEqual(result, 1)
        
        # Test getting feedback with no ID
        mock_get_feedback.reset_mock()
        
        with patch('builtins.print') as mock_print:
            result = feedback_system.get_feedback([])
            
            # Check that the feedback was not retrieved
            mock_get_feedback.assert_not_called()
            
            # Check that an error was printed
            mock_print.assert_called_once_with("Error: Missing required argument <id>")
            
            # Check the return value
            self.assertEqual(result, 1)

if __name__ == '__main__':
    unittest.main()
