#!/usr/bin/env python3
"""
Agentic Framework Discovery Module

This module helps AI agents discover and load the Agentic framework.
It provides information about the framework structure, available tools,
and documentation.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Optional, Any

# Get the Agentic home directory from the environment variable or use the default
AGENTIC_HOME = os.environ.get("AGHOME", os.path.expanduser("~/Agentic"))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(AGENTIC_HOME, "logs", "discover_agentic.log"), mode='a')
    ]
)
logger = logging.getLogger("discover_agentic")

# Create logs directory if it doesn't exist
os.makedirs(os.path.join(AGENTIC_HOME, "logs"), exist_ok=True)

def find_agentic_root() -> Optional[str]:
    """
    Find the Agentic framework root directory.
    
    Returns:
        Optional[str]: The path to the Agentic framework root directory, or None if not found
    """
    # First, check if AGHOME environment variable is set
    if "AGHOME" in os.environ:
        aghome = os.environ["AGHOME"]
        if os.path.exists(aghome) and os.path.isdir(aghome):
            return aghome
    
    # Next, try the standard location
    standard_path = os.path.expanduser("~/Agentic")
    if os.path.exists(standard_path) and os.path.isdir(standard_path):
        return standard_path
    
    # If not found, try to find it in common locations
    common_locations = [
        os.path.expanduser("~"),
        os.path.expanduser("~/Documents"),
        os.path.expanduser("~/Projects"),
        os.path.expanduser("~/Desktop")
    ]
    
    for location in common_locations:
        if os.path.exists(location) and os.path.isdir(location):
            for item in os.listdir(location):
                item_path = os.path.join(location, item)
                if item.lower() == "agentic" and os.path.isdir(item_path):
                    return item_path
    
    # If still not found, return None
    return None

def load_agentic_info(agentic_root: str, json_output: bool = False) -> Optional[Dict[str, Any]]:
    """
    Load the Agentic framework information.
    
    Args:
        agentic_root (str): The path to the Agentic framework root directory
        json_output (bool): Whether to output in JSON format
    
    Returns:
        Optional[Dict[str, Any]]: The Agentic framework information, or None if not found
    """
    # First, try to find the file in the agentic-core repository
    agentic_core_path = os.path.join(agentic_root, "projects", "agentic-core", "agentic_info.json")
    
    # If not found in agentic-core, try the current directory (for backward compatibility)
    current_dir_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "agentic_info.json")
    
    # Check if the file exists in either location
    if os.path.exists(agentic_core_path):
        info_path = agentic_core_path
    elif os.path.exists(current_dir_path):
        info_path = current_dir_path
    else:
        info_path = None
    
    if info_path and os.path.exists(info_path):
        try:
            with open(info_path, 'r') as f:
                info = json.load(f)
            
            # For JSON output, we'll keep the $HOME placeholder
            # For human-readable output, we'll replace it with the actual home directory
            if not json_output:
                # Replace $HOME with the actual home directory
                home_dir = os.path.expanduser("~")
                for key, value in info.items():
                    if isinstance(value, str):
                        info[key] = value.replace("$HOME", home_dir)
                    elif isinstance(value, dict):
                        for subkey, subvalue in value.items():
                            if isinstance(subvalue, str):
                                info[key][subkey] = subvalue.replace("$HOME", home_dir)
            
            return info
        except Exception as e:
            logger.error(f"Error loading Agentic info: {e}")
            return None
    else:
        # Create a basic info structure
        return {
            "framework_name": "Agentic",
            "version": "1.0.0",  # Default version
            "description": "A framework for managing and operating AI agents with controlled access to a machine",
            "home_directory": agentic_root,
            "documentation": {
                "agent_rules": os.path.join(agentic_root, "docs", "AGENT_RULES.md"),
                "agent_quick_reference": os.path.join(agentic_root, "docs", "AGENT_QUICK_REFERENCE.md"),
                "human_guide": os.path.join(agentic_root, "docs", "HUMAN_GUIDE.md"),
                "readme": os.path.join(agentic_root, "docs", "README.md")
            },
            "directory_structure": {
                "projects": os.path.join(agentic_root, "projects"),
                "shared": os.path.join(agentic_root, "shared"),
                "tmp": os.path.join(agentic_root, "tmp"),
                "logs": os.path.join(agentic_root, "logs"),
                "cache": os.path.join(agentic_root, "cache"),
                "backups": os.path.join(agentic_root, "backups")
            },
            "utility_commands": {
                "check_environment": "ag check-environment",
                "venv_manager": "ag venv",
                "uv_manager": "ag uv",
                "create_project": "ag create-project",
                "cleanup_manager": "ag cleanup"
            },
            "registry": {
                "path": os.path.join(agentic_root, "venv_registry.json"),
                "description": "Registry of active Python virtual environments managed by uv"
            }
        }

def check_environment(agentic_root: str) -> bool:
    """
    Check if the Agentic environment is set up correctly.
    
    Args:
        agentic_root (str): The path to the Agentic framework root directory
    
    Returns:
        bool: True if the environment is set up correctly, False otherwise
    """
    # Check if the docs directory exists
    docs_dir = os.path.join(agentic_root, "docs")
    if not os.path.exists(docs_dir) or not os.path.isdir(docs_dir):
        logger.warning(f"Warning: Docs directory not found at {docs_dir}")
    
    # Check if the required files exist
    required_files = [
        os.path.join(docs_dir, "AGENT_RULES.md"),
        os.path.join(docs_dir, "AGENT_QUICK_REFERENCE.md"),
        os.path.join(docs_dir, "README.md")
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        logger.warning(f"Warning: Missing recommended files: {', '.join(missing_files)}")
    
    # Check if the required directories exist
    required_dirs = [
        "projects",
        "shared",
        "logs",
        "tmp",
        "cache",
        "backups"
    ]
    
    missing_dirs = []
    for dir_name in required_dirs:
        dir_path = os.path.join(agentic_root, dir_name)
        if not os.path.exists(dir_path) or not os.path.isdir(dir_path):
            missing_dirs.append(dir_name)
    
    if missing_dirs:
        logger.warning(f"Warning: Missing directories: {', '.join(missing_dirs)}")
        logger.info("You can create them using the 'ag check-environment' command.")
    
    return True

def print_framework_info(info: Dict[str, Any]) -> None:
    """
    Print information about the Agentic framework.
    
    Args:
        info (Dict[str, Any]): The Agentic framework information
    """
    print(f"\n{info['framework_name']} Framework (v{info['version']})")
    print("=" * 50)
    print(f"Description: {info['description']}")
    print(f"Home Directory: {info['home_directory']}")
    
    print("\nDocumentation:")
    for name, path in info['documentation'].items():
        print(f"  - {name.replace('_', ' ').title()}: {path}")
    
    print("\nDirectory Structure:")
    for name, path in info['directory_structure'].items():
        print(f"  - {name.replace('_', ' ').title()}: {path}")
    
    print("\nUtility Commands:")
    for name, command in info['utility_commands'].items():
        print(f"  - {name.replace('_', ' ').title()}: {command}")
    
    print("\nRegistry:")
    print(f"  - Path: {info['registry']['path']}")
    print(f"  - Description: {info['registry']['description']}")
    
    if "recommended_entry_prompt" in info:
        print("\nRecommended Entry Prompt:")
        print(f"  {info['recommended_entry_prompt']}")

def discover_cli(args):
    """
    Discover and load the Agentic framework, called by the ag script.
    
    Args:
        args: Command-line arguments
    
    Returns:
        int: Exit code
    """
    # Parse arguments
    path = None
    json_output = False
    check = False
    
    for i, arg in enumerate(args):
        if arg == "--path" and i + 1 < len(args):
            path = args[i + 1]
        elif arg == "--json":
            json_output = True
        elif arg == "--check":
            check = True
    
    # Find the Agentic root directory
    if path:
        agentic_root = path
    else:
        agentic_root = find_agentic_root()
    
    if not agentic_root:
        print("Error: Could not find the Agentic framework root directory.")
        print("Please specify the path using the --path option.")
        return 1
    
    # Load the Agentic framework information
    info = load_agentic_info(agentic_root, json_output)
    
    if not info:
        print("Error: Could not load Agentic framework information.")
        return 1
    
    # Check the environment if requested
    if check:
        if not check_environment(agentic_root):
            return 1
    
    # Output the information
    if json_output:
        # Write the JSON to a file in the current directory
        output_file = os.path.join(os.getcwd(), "agentic_info.json")
        with open(output_file, 'w') as f:
            json.dump(info, f, indent=2)
        print(f"JSON output written to {output_file}")
        
        # Also print the JSON to the terminal
        print(json.dumps(info, indent=2))
    else:
        print_framework_info(info)
    
    return 0

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Discover and load the Agentic framework")
    parser.add_argument("--path", help="Path to the Agentic framework root directory")
    parser.add_argument("--json", action="store_true", help="Output information in JSON format")
    parser.add_argument("--check", action="store_true", help="Check if the Agentic environment is set up correctly")
    
    args = parser.parse_args()
    
    # Find the Agentic root directory
    if args.path:
        agentic_root = args.path
    else:
        agentic_root = find_agentic_root()
    
    if not agentic_root:
        print("Error: Could not find the Agentic framework root directory.")
        print("Please specify the path using the --path option.")
        sys.exit(1)
    
    # Load the Agentic framework information
    info = load_agentic_info(agentic_root, args.json)
    
    if not info:
        print("Error: Could not load Agentic framework information.")
        sys.exit(1)
    
    # Check the environment if requested
    if args.check:
        if not check_environment(agentic_root):
            sys.exit(1)
    
    # Output the information
    if args.json:
        # Write the JSON to a file in the current directory
        output_file = os.path.join(os.getcwd(), "agentic_info.json")
        with open(output_file, 'w') as f:
            json.dump(info, f, indent=2)
        print(f"JSON output written to {output_file}")
        
        # Also print the JSON to the terminal
        print(json.dumps(info, indent=2))
    else:
        print_framework_info(info)
    
    sys.exit(0)
