#!/usr/bin/env python3
"""
Feedback CLI - Command Line Interface for the Agentic Feedback System

This module provides a command-line interface for interacting with the Agentic
feedback system. It allows users to list, view, update, and comment on feedback
items such as issues, improvements, questions, and compliance reports.
"""

import os
import sys
import json
import logging
from typing import List, Optional, Dict, Any

# Import from agentic_core
from agentic_core.commands.feedback_system import (
    FeedbackSystem,
    FeedbackType,
    FeedbackPriority,
    FeedbackStatus,
    list_feedback as list_feedback_func,
    get_feedback as get_feedback_func,
    submit_feedback as submit_feedback_func
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.expanduser("~/Agentic/logs/feedback_cli.log"), mode='a')
    ]
)
logger = logging.getLogger("feedback_cli")

# Create logs directory if it doesn't exist
os.makedirs(os.path.expanduser("~/Agentic/logs"), exist_ok=True)

# Create a feedback system instance for operations that aren't directly exposed
feedback_system = FeedbackSystem()

def print_issue(issue_data: Dict[str, Any]) -> None:
    """
    Print issue information in a readable format.
    
    Args:
        issue_data (Dict[str, Any]): The issue data to print
    """
    print("\nIssue ID: {}".format(issue_data.get("id")))
    print("Title: {}".format(issue_data.get("title")))
    print("Status: {}".format(issue_data.get("status")))
    print("Priority: {}".format(issue_data.get("priority")))
    print("Created at: {}".format(issue_data.get("created_at")))
    
    # Print comments if any
    comments = issue_data.get("comments", [])
    if comments:
        print("Comments:")
        for comment in comments:
            print("  - {} ({}): {}".format(
                comment.get("author"),
                comment.get("created_at"),
                comment.get("content")
            ))

def list_issues_cli(args: List[str]) -> int:
    """
    List all issues, called by the ag script.
    
    Args:
        args: Command-line arguments
    
    Returns:
        int: Exit code
    """
    # Parse arguments
    feedback_type = "issue"
    status = None
    priority = None
    tags = None
    
    for i, arg in enumerate(args):
        if arg == "--type" and i + 1 < len(args):
            feedback_type = args[i + 1]
        elif arg == "--status" and i + 1 < len(args):
            status = args[i + 1]
        elif arg == "--priority" and i + 1 < len(args):
            priority = args[i + 1]
        elif arg == "--tags" and i + 1 < len(args):
            tags = args[i + 1].split(",")
    
    # List all issues
    feedback_system = FeedbackSystem()
    issues = feedback_system.list_feedback(
        feedback_type=feedback_type,
        status=status,
        priority=priority,
        tags=tags
    )
    
    print("Found {} issues:".format(len(issues)))
    for issue in issues:
        print_issue(issue)
    
    return 0

def get_issue_cli(args: List[str]) -> int:
    """
    Get a specific issue, called by the ag script.
    
    Args:
        args: Command-line arguments
    
    Returns:
        int: Exit code
    """
    if not args:
        print("Error: No issue ID specified")
        print("Usage: ag feedback get <issue_id>")
        return 1
    
    issue_id = args[0]
    feedback_system = FeedbackSystem()
    issue_data = feedback_system.get_feedback(issue_id)
    
    if issue_data:
        print_issue(issue_data)
        return 0
    else:
        print("Issue not found: {}".format(issue_id))
        return 1

def update_issue_cli(args: List[str]) -> int:
    """
    Update an issue's status, called by the ag script.
    
    Args:
        args: Command-line arguments
    
    Returns:
        int: Exit code
    """
    if len(args) < 2:
        print("Error: Missing arguments")
        print("Usage: ag feedback update <issue_id> <status>")
        return 1
    
    issue_id = args[0]
    new_status = args[1]
    
    # Validate status
    valid_statuses = [
        FeedbackStatus.NEW,
        FeedbackStatus.ACKNOWLEDGED,
        FeedbackStatus.IN_PROGRESS,
        FeedbackStatus.RESOLVED,
        FeedbackStatus.CLOSED,
        FeedbackStatus.REJECTED
    ]
    
    if new_status not in valid_statuses:
        print("Error: Invalid status: {}".format(new_status))
        print("Valid statuses: {}".format(", ".join(valid_statuses)))
        return 1
    
    # Update the issue
    success = feedback_system.update_feedback(issue_id, {"status": new_status})
    
    if success:
        print("Issue status updated to '{}'".format(new_status))
        issue_data = feedback_system.get_feedback(issue_id)
        if issue_data:
            print_issue(issue_data)
        return 0
    else:
        print("Failed to update issue: {}".format(issue_id))
        return 1

def comment_issue_cli(args: List[str]) -> int:
    """
    Add a comment to an issue, called by the ag script.
    
    Args:
        args: Command-line arguments
    
    Returns:
        int: Exit code
    """
    if len(args) < 2:
        print("Error: Missing arguments")
        print("Usage: ag feedback comment <issue_id> <comment> [--author <author>]")
        return 1
    
    issue_id = args[0]
    comment_text = args[1]
    author = "User"
    
    # Parse author if provided
    for i, arg in enumerate(args):
        if arg == "--author" and i + 1 < len(args):
            author = args[i + 1]
    
    # Add the comment
    success = feedback_system.add_comment(issue_id, comment_text, author)
    
    if success:
        print("Comment added to issue: {}".format(issue_id))
        issue_data = feedback_system.get_feedback(issue_id)
        if issue_data:
            print_issue(issue_data)
        return 0
    else:
        print("Failed to add comment to issue: {}".format(issue_id))
        return 1

def submit_issue_cli(args: List[str]) -> int:
    """
    Submit a new issue, called by the ag script.
    
    Args:
        args: Command-line arguments
    
    Returns:
        int: Exit code
    """
    if len(args) < 2:
        print("Error: Missing arguments")
        print("Usage: ag feedback submit <title> <description> [--type <type>] [--priority <priority>] [--tags <tags>]")
        return 1
    
    title = args[0]
    description = args[1]
    feedback_type = FeedbackType.ISSUE
    priority = FeedbackPriority.MEDIUM
    tags = ["cli"]
    
    # Parse optional arguments
    for i, arg in enumerate(args):
        if arg == "--type" and i + 1 < len(args):
            feedback_type = args[i + 1]
        elif arg == "--priority" and i + 1 < len(args):
            priority = args[i + 1]
        elif arg == "--tags" and i + 1 < len(args):
            tags = args[i + 1].split(",")
    
    # Submit the issue
    feedback_system = FeedbackSystem()
    issue_id = feedback_system.submit_feedback(
        feedback_type=feedback_type,
        title=title,
        description=description,
        priority=priority,
        tags=tags
    )
    
    if issue_id:
        print("Issue submitted with ID: {}".format(issue_id))
        issue_data = feedback_system.get_feedback(issue_id)
        if issue_data:
            print_issue(issue_data)
        return 0
    else:
        print("Failed to submit issue")
        return 1

def feedback_cli(args: List[str]) -> int:
    """
    Main CLI function for the feedback system, called by the ag script.
    
    Args:
        args: Command-line arguments
    
    Returns:
        int: Exit code
    """
    if not args:
        print("Error: No command specified")
        print("Usage: ag feedback <command> [args]")
        print("Commands: list, get, update, comment, submit")
        return 1
    
    command = args[0]
    command_args = args[1:]
    
    if command == "list":
        return list_issues_cli(command_args)
    elif command == "get":
        return get_issue_cli(command_args)
    elif command == "update":
        return update_issue_cli(command_args)
    elif command == "comment":
        return comment_issue_cli(command_args)
    elif command == "submit":
        return submit_issue_cli(command_args)
    else:
        print("Error: Unknown command: {}".format(command))
        print("Commands: list, get, update, comment, submit")
        return 1

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Agentic Framework Feedback CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List all issues")
    list_parser.add_argument("--type", help="Filter by feedback type")
    list_parser.add_argument("--status", help="Filter by status")
    list_parser.add_argument("--priority", help="Filter by priority")
    list_parser.add_argument("--tags", help="Filter by tags (comma-separated)")
    
    # Get command
    get_parser = subparsers.add_parser("get", help="Get a specific issue")
    get_parser.add_argument("issue_id", help="The ID of the issue to get")
    
    # Update command
    update_parser = subparsers.add_parser("update", help="Update an issue's status")
    update_parser.add_argument("issue_id", help="The ID of the issue to update")
    update_parser.add_argument("status", help="The new status")
    
    # Comment command
    comment_parser = subparsers.add_parser("comment", help="Add a comment to an issue")
    comment_parser.add_argument("issue_id", help="The ID of the issue to comment on")
    comment_parser.add_argument("comment", help="The comment text")
    comment_parser.add_argument("--author", help="The author of the comment")
    
    # Submit command
    submit_parser = subparsers.add_parser("submit", help="Submit a new issue")
    submit_parser.add_argument("title", help="The issue title")
    submit_parser.add_argument("description", help="The issue description")
    submit_parser.add_argument("--type", help="The feedback type")
    submit_parser.add_argument("--priority", help="The issue priority")
    submit_parser.add_argument("--tags", help="The issue tags (comma-separated)")
    
    args = parser.parse_args()
    
    if args.command == "list":
        list_args = []
        if args.type:
            list_args.extend(["--type", args.type])
        if args.status:
            list_args.extend(["--status", args.status])
        if args.priority:
            list_args.extend(["--priority", args.priority])
        if args.tags:
            list_args.extend(["--tags", args.tags])
        sys.exit(list_issues_cli(list_args))
    elif args.command == "get":
        sys.exit(get_issue_cli([args.issue_id]))
    elif args.command == "update":
        sys.exit(update_issue_cli([args.issue_id, args.status]))
    elif args.command == "comment":
        comment_args = [args.issue_id, args.comment]
        if args.author:
            comment_args.extend(["--author", args.author])
        sys.exit(comment_issue_cli(comment_args))
    elif args.command == "submit":
        submit_args = [args.title, args.description]
        if args.type:
            submit_args.extend(["--type", args.type])
        if args.priority:
            submit_args.extend(["--priority", args.priority])
        if args.tags:
            submit_args.extend(["--tags", args.tags])
        sys.exit(submit_issue_cli(submit_args))
    else:
        parser.print_help()
        sys.exit(1)
