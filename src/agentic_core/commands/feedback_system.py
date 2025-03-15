#!/usr/bin/env python3
"""
Feedback System

This module provides a mechanism for AI agents to report issues, suggest improvements,
and provide feedback on the Agentic framework. It helps ensure that AI agents are
correctly following the rules during operation and allows for continuous improvement
of the framework.
"""

import os
import sys
import json
import logging
import time
import uuid
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from pathlib import Path

# Import the config module from agentic_core
from agentic_core.commands import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.expanduser("~/Agentic/logs/feedback.log"), mode='a')
    ]
)
logger = logging.getLogger("feedback_system")

# Create logs directory if it doesn't exist
os.makedirs(os.path.expanduser("~/Agentic/logs"), exist_ok=True)

# Path to the feedback directory
FEEDBACK_DIR = config.get_path("feedback_dir") or os.path.expanduser("~/Agentic/feedback")

# Create feedback directory if it doesn't exist
os.makedirs(FEEDBACK_DIR, exist_ok=True)

class FeedbackType:
    """Enum-like class for feedback types."""
    ISSUE = "issue"
    IMPROVEMENT = "improvement"
    QUESTION = "question"
    COMPLIANCE = "compliance"
    OTHER = "other"

class FeedbackStatus:
    """Enum-like class for feedback status."""
    NEW = "new"
    ACKNOWLEDGED = "acknowledged"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"
    REJECTED = "rejected"

class FeedbackPriority:
    """Enum-like class for feedback priority."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class FeedbackSystem:
    """Class for managing feedback from AI agents."""
    
    def __init__(self, feedback_dir: str = FEEDBACK_DIR):
        """
        Initialize the feedback system.
        
        Args:
            feedback_dir (str): The directory to store feedback files
        """
        self.feedback_dir = feedback_dir
        
        # Create feedback directory if it doesn't exist
        os.makedirs(self.feedback_dir, exist_ok=True)
        
        # Create subdirectories for different feedback types
        for feedback_type in [FeedbackType.ISSUE, FeedbackType.IMPROVEMENT, 
                             FeedbackType.QUESTION, FeedbackType.COMPLIANCE, 
                             FeedbackType.OTHER]:
            os.makedirs(os.path.join(self.feedback_dir, feedback_type), exist_ok=True)
    
    def submit_feedback(self, feedback_type: str, title: str, description: str,
                       priority: str = FeedbackPriority.MEDIUM,
                       tags: Optional[List[str]] = None,
                       context: Optional[Dict[str, Any]] = None) -> str:
        """
        Submit feedback to the system.
        
        Args:
            feedback_type (str): The type of feedback (issue, improvement, question, compliance, other)
            title (str): A short title for the feedback
            description (str): A detailed description of the feedback
            priority (str): The priority of the feedback (low, medium, high, critical)
            tags (Optional[List[str]]): Tags to categorize the feedback
            context (Optional[Dict[str, Any]]): Additional context for the feedback
        
        Returns:
            str: The ID of the submitted feedback
        """
        # Validate feedback type
        if feedback_type not in [FeedbackType.ISSUE, FeedbackType.IMPROVEMENT, 
                                FeedbackType.QUESTION, FeedbackType.COMPLIANCE, 
                                FeedbackType.OTHER]:
            logger.warning(f"Invalid feedback type: {feedback_type}, using 'other' instead")
            feedback_type = FeedbackType.OTHER
        
        # Validate priority
        if priority not in [FeedbackPriority.LOW, FeedbackPriority.MEDIUM, 
                           FeedbackPriority.HIGH, FeedbackPriority.CRITICAL]:
            logger.warning(f"Invalid priority: {priority}, using 'medium' instead")
            priority = FeedbackPriority.MEDIUM
        
        # Generate a unique ID for the feedback
        feedback_id = str(uuid.uuid4())
        
        # Create the feedback data
        feedback_data = {
            "id": feedback_id,
            "type": feedback_type,
            "title": title,
            "description": description,
            "priority": priority,
            "tags": tags or [],
            "context": context or {},
            "status": FeedbackStatus.NEW,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "comments": []
        }
        
        # Save the feedback to a file
        feedback_path = os.path.join(self.feedback_dir, feedback_type, f"{feedback_id}.json")
        
        try:
            with open(feedback_path, 'w') as f:
                json.dump(feedback_data, f, indent=2)
            
            logger.info(f"Feedback submitted: {feedback_id} ({feedback_type})")
            return feedback_id
        except Exception as e:
            logger.error(f"Error submitting feedback: {e}")
            return ""
    
    def get_feedback(self, feedback_id: str) -> Optional[Dict[str, Any]]:
        """
        Get feedback by ID.
        
        Args:
            feedback_id (str): The ID of the feedback to get
        
        Returns:
            Optional[Dict[str, Any]]: The feedback data, or None if not found
        """
        # Search for the feedback in all subdirectories
        for feedback_type in [FeedbackType.ISSUE, FeedbackType.IMPROVEMENT, 
                             FeedbackType.QUESTION, FeedbackType.COMPLIANCE, 
                             FeedbackType.OTHER]:
            feedback_path = os.path.join(self.feedback_dir, feedback_type, f"{feedback_id}.json")
            
            if os.path.exists(feedback_path):
                try:
                    with open(feedback_path, 'r') as f:
                        return json.load(f)
                except Exception as e:
                    logger.error(f"Error reading feedback {feedback_id}: {e}")
                    return None
        
        logger.warning(f"Feedback not found: {feedback_id}")
        return None
    
    def update_feedback(self, feedback_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update feedback by ID.
        
        Args:
            feedback_id (str): The ID of the feedback to update
            updates (Dict[str, Any]): The updates to apply to the feedback
        
        Returns:
            bool: True if the update was successful, False otherwise
        """
        # Get the current feedback data
        feedback_data = self.get_feedback(feedback_id)
        
        if not feedback_data:
            logger.warning(f"Cannot update feedback {feedback_id}: not found")
            return False
        
        # Apply the updates
        for key, value in updates.items():
            if key in ["id", "created_at"]:
                # Don't allow updating these fields
                continue
            
            feedback_data[key] = value
        
        # Update the updated_at timestamp
        feedback_data["updated_at"] = datetime.now().isoformat()
        
        # Save the updated feedback
        feedback_type = feedback_data["type"]
        feedback_path = os.path.join(self.feedback_dir, feedback_type, f"{feedback_id}.json")
        
        try:
            with open(feedback_path, 'w') as f:
                json.dump(feedback_data, f, indent=2)
            
            logger.info(f"Feedback updated: {feedback_id}")
            return True
        except Exception as e:
            logger.error(f"Error updating feedback {feedback_id}: {e}")
            return False
    
    def add_comment(self, feedback_id: str, comment: str, author: str = "AI Agent") -> bool:
        """
        Add a comment to feedback.
        
        Args:
            feedback_id (str): The ID of the feedback to comment on
            comment (str): The comment to add
            author (str): The author of the comment
        
        Returns:
            bool: True if the comment was added successfully, False otherwise
        """
        # Get the current feedback data
        feedback_data = self.get_feedback(feedback_id)
        
        if not feedback_data:
            logger.warning(f"Cannot add comment to feedback {feedback_id}: not found")
            return False
        
        # Create the comment
        comment_data = {
            "id": str(uuid.uuid4()),
            "author": author,
            "content": comment,
            "created_at": datetime.now().isoformat()
        }
        
        # Add the comment to the feedback
        feedback_data["comments"].append(comment_data)
        
        # Update the updated_at timestamp
        feedback_data["updated_at"] = datetime.now().isoformat()
        
        # Save the updated feedback
        feedback_type = feedback_data["type"]
        feedback_path = os.path.join(self.feedback_dir, feedback_type, f"{feedback_id}.json")
        
        try:
            with open(feedback_path, 'w') as f:
                json.dump(feedback_data, f, indent=2)
            
            logger.info(f"Comment added to feedback {feedback_id}")
            return True
        except Exception as e:
            logger.error(f"Error adding comment to feedback {feedback_id}: {e}")
            return False
    
    def list_feedback(self, feedback_type: Optional[str] = None, 
                     status: Optional[str] = None,
                     priority: Optional[str] = None,
                     tags: Optional[List[str]] = None,
                     limit: int = 100) -> List[Dict[str, Any]]:
        """
        List feedback with optional filtering.
        
        Args:
            feedback_type (Optional[str]): Filter by feedback type
            status (Optional[str]): Filter by status
            priority (Optional[str]): Filter by priority
            tags (Optional[List[str]]): Filter by tags (must have all tags)
            limit (int): Maximum number of results to return
        
        Returns:
            List[Dict[str, Any]]: List of feedback data
        """
        results = []
        
        # Determine which directories to search
        if feedback_type:
            if feedback_type in [FeedbackType.ISSUE, FeedbackType.IMPROVEMENT, 
                                FeedbackType.QUESTION, FeedbackType.COMPLIANCE, 
                                FeedbackType.OTHER]:
                directories = [os.path.join(self.feedback_dir, feedback_type)]
            else:
                logger.warning(f"Invalid feedback type: {feedback_type}, searching all types")
                directories = [os.path.join(self.feedback_dir, t) for t in 
                              [FeedbackType.ISSUE, FeedbackType.IMPROVEMENT, 
                               FeedbackType.QUESTION, FeedbackType.COMPLIANCE, 
                               FeedbackType.OTHER]]
        else:
            directories = [os.path.join(self.feedback_dir, t) for t in 
                          [FeedbackType.ISSUE, FeedbackType.IMPROVEMENT, 
                           FeedbackType.QUESTION, FeedbackType.COMPLIANCE, 
                           FeedbackType.OTHER]]
        
        # Search for feedback files
        for directory in directories:
            if not os.path.exists(directory):
                continue
            
            for filename in os.listdir(directory):
                if not filename.endswith(".json"):
                    continue
                
                file_path = os.path.join(directory, filename)
                
                try:
                    with open(file_path, 'r') as f:
                        feedback_data = json.load(f)
                    
                    # Apply filters
                    if status and feedback_data.get("status") != status:
                        continue
                    
                    if priority and feedback_data.get("priority") != priority:
                        continue
                    
                    if tags:
                        feedback_tags = feedback_data.get("tags", [])
                        if not all(tag in feedback_tags for tag in tags):
                            continue
                    
                    results.append(feedback_data)
                    
                    # Check if we've reached the limit
                    if len(results) >= limit:
                        break
                except Exception as e:
                    logger.error(f"Error reading feedback file {file_path}: {e}")
            
            # Check if we've reached the limit
            if len(results) >= limit:
                break
        
        # Sort results by created_at (newest first)
        results.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        return results[:limit]
    
    def get_feedback_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the feedback system.
        
        Returns:
            Dict[str, Any]: Statistics about the feedback system
        """
        stats = {
            "total": 0,
            "by_type": {},
            "by_status": {},
            "by_priority": {}
        }
        
        # Initialize counters
        for feedback_type in [FeedbackType.ISSUE, FeedbackType.IMPROVEMENT, 
                             FeedbackType.QUESTION, FeedbackType.COMPLIANCE, 
                             FeedbackType.OTHER]:
            stats["by_type"][feedback_type] = 0
        
        for status in [FeedbackStatus.NEW, FeedbackStatus.ACKNOWLEDGED, 
                      FeedbackStatus.IN_PROGRESS, FeedbackStatus.RESOLVED, 
                      FeedbackStatus.CLOSED, FeedbackStatus.REJECTED]:
            stats["by_status"][status] = 0
        
        for priority in [FeedbackPriority.LOW, FeedbackPriority.MEDIUM, 
                        FeedbackPriority.HIGH, FeedbackPriority.CRITICAL]:
            stats["by_priority"][priority] = 0
        
        # Count feedback
        for feedback_type in [FeedbackType.ISSUE, FeedbackType.IMPROVEMENT, 
                             FeedbackType.QUESTION, FeedbackType.COMPLIANCE, 
                             FeedbackType.OTHER]:
            directory = os.path.join(self.feedback_dir, feedback_type)
            
            if not os.path.exists(directory):
                continue
            
            for filename in os.listdir(directory):
                if not filename.endswith(".json"):
                    continue
                
                file_path = os.path.join(directory, filename)
                
                try:
                    with open(file_path, 'r') as f:
                        feedback_data = json.load(f)
                    
                    stats["total"] += 1
                    stats["by_type"][feedback_type] += 1
                    
                    status = feedback_data.get("status", FeedbackStatus.NEW)
                    if status in stats["by_status"]:
                        stats["by_status"][status] += 1
                    
                    priority = feedback_data.get("priority", FeedbackPriority.MEDIUM)
                    if priority in stats["by_priority"]:
                        stats["by_priority"][priority] += 1
                except Exception as e:
                    logger.error(f"Error reading feedback file {file_path}: {e}")
        
        return stats
    
    def export_feedback(self, output_path: str, feedback_type: Optional[str] = None,
                       status: Optional[str] = None) -> bool:
        """
        Export feedback to a JSON file.
        
        Args:
            output_path (str): The path to save the exported feedback
            feedback_type (Optional[str]): Filter by feedback type
            status (Optional[str]): Filter by status
        
        Returns:
            bool: True if the export was successful, False otherwise
        """
        # Get the feedback to export
        feedback_list = self.list_feedback(feedback_type=feedback_type, status=status, limit=1000)
        
        # Create the export data
        export_data = {
            "exported_at": datetime.now().isoformat(),
            "total": len(feedback_list),
            "feedback": feedback_list
        }
        
        # Save the export to a file
        try:
            with open(output_path, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            logger.info(f"Feedback exported to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error exporting feedback: {e}")
            return False
    
    def import_feedback(self, input_path: str) -> int:
        """
        Import feedback from a JSON file.
        
        Args:
            input_path (str): The path to the JSON file to import
        
        Returns:
            int: The number of feedback items imported
        """
        try:
            with open(input_path, 'r') as f:
                import_data = json.load(f)
            
            feedback_list = import_data.get("feedback", [])
            imported_count = 0
            
            for feedback_data in feedback_list:
                feedback_id = feedback_data.get("id")
                feedback_type = feedback_data.get("type")
                
                if not feedback_id or not feedback_type:
                    logger.warning(f"Skipping feedback without ID or type")
                    continue
                
                # Check if the feedback already exists
                existing_feedback = self.get_feedback(feedback_id)
                if existing_feedback:
                    logger.warning(f"Skipping existing feedback: {feedback_id}")
                    continue
                
                # Save the feedback to a file
                feedback_path = os.path.join(self.feedback_dir, feedback_type, f"{feedback_id}.json")
                
                try:
                    with open(feedback_path, 'w') as f:
                        json.dump(feedback_data, f, indent=2)
                    
                    imported_count += 1
                except Exception as e:
                    logger.error(f"Error importing feedback {feedback_id}: {e}")
            
            logger.info(f"Imported {imported_count} feedback items from {input_path}")
            return imported_count
        except Exception as e:
            logger.error(f"Error importing feedback: {e}")
            return 0
    
    def cleanup_old_feedback(self, days: int = 90, status: Optional[str] = None) -> int:
        """
        Clean up old feedback.
        
        Args:
            days (int): Remove feedback older than this many days
            status (Optional[str]): Only remove feedback with this status
        
        Returns:
            int: The number of feedback items removed
        """
        cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)
        removed_count = 0
        
        # Search for old feedback files
        for feedback_type in [FeedbackType.ISSUE, FeedbackType.IMPROVEMENT, 
                             FeedbackType.QUESTION, FeedbackType.COMPLIANCE, 
                             FeedbackType.OTHER]:
            directory = os.path.join(self.feedback_dir, feedback_type)
            
            if not os.path.exists(directory):
                continue
            
            for filename in os.listdir(directory):
                if not filename.endswith(".json"):
                    continue
                
                file_path = os.path.join(directory, filename)
                
                try:
                    with open(file_path, 'r') as f:
                        feedback_data = json.load(f)
                    
                    # Check if the feedback is old enough
                    created_at = feedback_data.get("created_at", "")
                    if not created_at:
                        continue
                    
                    try:
                        created_timestamp = datetime.fromisoformat(created_at).timestamp()
                    except ValueError:
                        continue
                    
                    if created_timestamp > cutoff_date:
                        continue
                    
                    # Check if the feedback has the specified status
                    if status and feedback_data.get("status") != status:
                        continue
                    
                    # Remove the feedback file
                    os.remove(file_path)
                    removed_count += 1
                except Exception as e:
                    logger.error(f"Error cleaning up feedback file {file_path}: {e}")
        
        logger.info(f"Removed {removed_count} old feedback items")
        return removed_count

# Functions for the ag CLI

def submit_feedback(args):
    """Submit feedback, called by the ag script."""
    # Check for help flag
    if "--help" in args or "-h" in args:
        print("Usage: ag feedback submit [options]")
        print("\nOptions:")
        print("  --type <type>              The type of feedback (issue, improvement, question, compliance, other)")
        print("  --title <title>            A short title for the feedback")
        print("  --description <description> A detailed description of the feedback")
        print("  --priority <priority>      The priority of the feedback (low, medium, high, critical)")
        print("  --tags <tag1> <tag2> ...   Tags to categorize the feedback")
        print("  --context <json>           Additional context for the feedback (JSON format)")
        return 0
    
    # Parse arguments
    feedback_type = None
    title = None
    description = None
    priority = FeedbackPriority.MEDIUM
    tags = None
    context = None
    
    i = 0
    while i < len(args):
        if args[i] == "--type" and i + 1 < len(args):
            feedback_type = args[i + 1]
            i += 2
        elif args[i] == "--title" and i + 1 < len(args):
            title = args[i + 1]
            i += 2
        elif args[i] == "--description" and i + 1 < len(args):
            description = args[i + 1]
            i += 2
        elif args[i] == "--priority" and i + 1 < len(args):
            priority = args[i + 1]
            i += 2
        elif args[i] == "--tags" and i + 1 < len(args):
            tags = []
            j = i + 1
            while j < len(args) and not args[j].startswith("--"):
                tags.append(args[j])
                j += 1
            i = j
        elif args[i] == "--context" and i + 1 < len(args):
            try:
                context = json.loads(args[i + 1])
                i += 2
            except json.JSONDecodeError:
                print("Error: Invalid JSON format for context")
                return 1
        else:
            i += 1
    
    # Validate required arguments
    if not feedback_type:
        print("Error: Missing required argument --type")
        return 1
    
    if not title:
        print("Error: Missing required argument --title")
        return 1
    
    if not description:
        print("Error: Missing required argument --description")
        return 1
    
    # Submit feedback
    feedback_system = FeedbackSystem()
    feedback_id = feedback_system.submit_feedback(
        feedback_type,
        title,
        description,
        priority,
        tags,
        context
    )
    
    if feedback_id:
        print(f"Feedback submitted with ID: {feedback_id}")
        return 0
    else:
        print("Error submitting feedback")
        return 1

def get_feedback(args):
    """Get feedback by ID, called by the ag script."""
    # Check for help flag
    if "--help" in args or "-h" in args:
        print("Usage: ag feedback get <id>")
        return 0
    
    # Validate required arguments
    if len(args) < 1:
        print("Error: Missing required argument <id>")
        return 1
    
    feedback_id = args[0]
    
    # Get feedback
    feedback_system = FeedbackSystem()
    feedback_data = feedback_system.get_feedback(feedback_id)
    
    if feedback_data:
        print(json.dumps(feedback_data, indent=2))
        return 0
    else:
        print(f"Feedback not found: {feedback_id}")
        return 1

def list_feedback(args):
    """List feedback with optional filtering, called by the ag script."""
    # Check for help flag
    if "--help" in args or "-h" in args:
        print("Usage: ag feedback list [options]")
        print("\nOptions:")
        print("  --type <type>              Filter by feedback type (issue, improvement, question, compliance, other)")
        print("  --status <status>          Filter by status (new, acknowledged, in_progress, resolved, closed, rejected)")
        print("  --priority <priority>      Filter by priority (low, medium, high, critical)")
        print("  --tags <tag1> <tag2> ...   Filter by tags (must have all tags)")
        print("  --limit <limit>            Maximum number of results to return")
        return 0
    
    # Parse arguments
    feedback_type = None
    status = None
    priority = None
    tags = None
    limit = 100
    
    i = 0
    while i < len(args):
        if args[i] == "--type" and i + 1 < len(args):
            feedback_type = args[i + 1]
            i += 2
        elif args[i] == "--status" and i + 1 < len(args):
            status = args[i + 1]
            i += 2
        elif args[i] == "--priority" and i + 1 < len(args):
            priority = args[i + 1]
            i += 2
        elif args[i] == "--tags" and i + 1 < len(args):
            tags = []
            j = i + 1
            while j < len(args) and not args[j].startswith("--"):
                tags.append(args[j])
                j += 1
            i = j
        elif args[i] == "--limit" and i + 1 < len(args):
            try:
                limit = int(args[i + 1])
                i += 2
            except ValueError:
                print(f"Error: Invalid value for --limit: {args[i + 1]}")
                return 1
        else:
            i += 1
    
    # List feedback
    feedback_system = FeedbackSystem()
    feedback_list = feedback_system.list_feedback(
        feedback_type=feedback_type,
        status=status,
        priority=priority,
        tags=tags,
        limit=limit
    )
    
    if feedback_list:
        print(json.dumps(feedback_list, indent=2))
    else:
        print("No feedback found matching the criteria")
    
    return 0

def update_feedback(args):
    """Update feedback by ID, called by the ag script."""
    # Check for help flag
    if "--help" in args or "-h" in args:
        print("Usage: ag feedback update <id> [options]")
        print("\nOptions:")
        print("  --status <status>          Update the status (new, acknowledged, in_progress, resolved, closed, rejected)")
        print("  --priority <priority>      Update the priority (low, medium, high, critical)")
        print("  --title <title>            Update the title")
        print("  --description <description> Update the description")
        return 0
    
    # Validate required arguments
    if len(args) < 1:
        print("Error: Missing required argument <id>")
        return 1
    
    feedback_id = args[0]
    
    # Parse arguments
    updates = {}
    
    i = 1
    while i < len(args):
        if args[i] == "--status" and i + 1 < len(args):
            updates["status"] = args[i + 1]
            i += 2
        elif args[i] == "--priority" and i + 1 < len(args):
            updates["priority"] = args[i + 1]
            i += 2
        elif args[i] == "--title" and i + 1 < len(args):
            updates["title"] = args[i + 1]
            i += 2
        elif args[i] == "--description" and i + 1 < len(args):
            updates["description"] = args[i + 1]
            i += 2
        else:
            i += 1
    
    # Validate updates
    if not updates:
        print("Error: No updates specified")
        return 1
    
    # Update feedback
    feedback_system = FeedbackSystem()
    success = feedback_system.update_feedback(feedback_id, updates)
    
    if success:
        print(f"Feedback {feedback_id} updated successfully")
        return 0
    else:
        print(f"Error updating feedback {feedback_id}")
        return 1

def add_comment(args):
    """Add a comment to feedback, called by the ag script."""
    # Check for help flag
    if "--help" in args or "-h" in args:
        print("Usage: ag feedback comment <id> [options]")
        print("\nOptions:")
        print("  --comment <comment>        The comment to add")
        print("  --author <author>          The author of the comment (default: AI Agent)")
        return 0
    
    # Validate required arguments
    if len(args) < 1:
        print("Error: Missing required argument <id>")
        return 1
    
    feedback_id = args[0]
    
    # Parse arguments
    comment = None
    author = "AI Agent"
    
    i = 1
    while i < len(args):
        if args[i] == "--comment" and i + 1 < len(args):
            comment = args[i + 1]
            i += 2
        elif args[i] == "--author" and i + 1 < len(args):
            author = args[i + 1]
            i += 2
        else:
            i += 1
    
    # Validate required arguments
    if not comment:
        print("Error: Missing required argument --comment")
        return 1
    
    # Add comment
    feedback_system = FeedbackSystem()
    success = feedback_system.add_comment(feedback_id, comment, author)
    
    if success:
        print(f"Comment added to feedback {feedback_id}")
        return 0
    else:
        print(f"Error adding comment to feedback {feedback_id}")
        return 1

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Agentic Framework Feedback System")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Submit feedback command
    submit_parser = subparsers.add_parser("submit", help="Submit feedback")
    submit_parser.add_argument("--type", required=True, choices=["issue", "improvement", "question", "compliance", "other"],
                             help="The type of feedback")
    submit_parser.add_argument("--title", required=True, help="A short title for the feedback")
    submit_parser.add_argument("--description", required=True, help="A detailed description of the feedback")
    submit_parser.add_argument("--priority", choices=["low", "medium", "high", "critical"],
                             default="medium", help="The priority of the feedback")
