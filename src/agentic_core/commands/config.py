#!/usr/bin/env python3
"""
Centralized Configuration System

This module provides a centralized configuration system for the Agentic framework.
It allows scripts to access configuration values in a consistent way and handles
path variability across different installations.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.expanduser("~/Agentic/logs/config.log"), mode='a')
    ]
)
logger = logging.getLogger("config")

# Create logs directory if it doesn't exist
os.makedirs(os.path.expanduser("~/Agentic/logs"), exist_ok=True)

# Default configuration values
DEFAULT_CONFIG = {
    "version": "1.0.0",
    "paths": {
        "agentic_root": "~/Agentic",
        "agentic_repo": "~/Agentic/agentic",
        "projects_dir": "~/Agentic/projects",
        "shared_dir": "~/Agentic/shared",
        "tmp_dir": "~/Agentic/tmp",
        "logs_dir": "~/Agentic/logs",
        "cache_dir": "~/Agentic/cache",
        "backups_dir": "~/Agentic/backups",
        "registry_file": "~/Agentic/venv_registry.json",
        "rules_file": "~/Agentic/agentic/rules.json"
    },
    "python": {
        "package_manager": "uv",
        "default_python_version": "3.11",
        "virtual_env_location": ".venv",
        "requirements_file": "requirements.txt"
    },
    "project": {
        "default_license": "MIT",
        "naming_convention": "kebab-case",
        "standard_directories": [
            "src",
            "tests",
            "docs",
            "data",
            "notebooks",
            "logs"
        ],
        "standard_files": [
            "README.md",
            "LICENSE",
            ".gitignore",
            "pyproject.toml"
        ]
    },
    "security": {
        "allowed_areas": [
            "~/Agentic"
        ],
        "restricted_areas": [
            "System files",
            "Global configurations"
        ]
    },
    "logging": {
        "log_level": "INFO",
        "log_rotation": True,
        "max_log_size": 10485760,  # 10 MB
        "backup_count": 5
    },
    "backup": {
        "auto_backup": True,
        "max_backups": 10,
        "backup_interval": 86400  # 24 hours
    }
}

# Path to the configuration file
CONFIG_PATH = os.path.expanduser("~/Agentic/agentic_config.json")

class Config:
    """Class for managing the Agentic framework configuration."""
    
    _instance = None
    
    def __new__(cls):
        """Implement the Singleton pattern."""
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the configuration."""
        if self._initialized:
            return
        
        self._config = self._load_config()
        self._initialized = True
    
    def _load_config(self) -> Dict[str, Any]:
        """Load the configuration from the configuration file."""
        try:
            if os.path.exists(CONFIG_PATH):
                with open(CONFIG_PATH, 'r') as f:
                    config = json.load(f)
                logger.info(f"Configuration loaded from {CONFIG_PATH}")
                
                # Merge with default config to ensure all keys are present
                merged_config = self._merge_configs(DEFAULT_CONFIG, config)
                return merged_config
            else:
                logger.info(f"Configuration file not found at {CONFIG_PATH}, using default configuration")
                return DEFAULT_CONFIG.copy()
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return DEFAULT_CONFIG.copy()
    
    def _merge_configs(self, default: Dict[str, Any], custom: Dict[str, Any]) -> Dict[str, Any]:
        """Merge the custom configuration with the default configuration."""
        result = default.copy()
        
        for key, value in custom.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def save_config(self) -> bool:
        """Save the configuration to the configuration file."""
        try:
            os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
            
            with open(CONFIG_PATH, 'w') as f:
                json.dump(self._config, f, indent=2)
            
            logger.info(f"Configuration saved to {CONFIG_PATH}")
            return True
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            return False
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get a configuration value by its key path.
        
        Args:
            key_path (str): The key path in dot notation (e.g., 'paths.agentic_root')
            default (Any, optional): The default value to return if the key is not found
        
        Returns:
            The configuration value, or the default value if the key is not found
        """
        keys = key_path.split('.')
        value = self._config
        
        try:
            for key in keys:
                value = value[key]
            
            # If the value is a path, expand it
            if isinstance(value, str) and any(keys[0] == category for category in ["paths"]):
                return os.path.expanduser(value)
            
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path: str, value: Any) -> bool:
        """
        Set a configuration value by its key path.
        
        Args:
            key_path (str): The key path in dot notation (e.g., 'paths.agentic_root')
            value (Any): The value to set
        
        Returns:
            bool: True if the value was set successfully, False otherwise
        """
        keys = key_path.split('.')
        config = self._config
        
        try:
            # Navigate to the parent of the key to set
            for key in keys[:-1]:
                if key not in config:
                    config[key] = {}
                config = config[key]
            
            # Set the value
            config[keys[-1]] = value
            
            # Save the configuration
            return self.save_config()
        except Exception as e:
            logger.error(f"Error setting configuration value: {e}")
            return False
    
    def get_path(self, path_key: str) -> Optional[str]:
        """
        Get a path from the configuration, ensuring it is an absolute path.
        
        Args:
            path_key (str): The key for the path in the paths section
        
        Returns:
            Optional[str]: The absolute path, or None if the path is not found
        """
        path = self.get(f"paths.{path_key}")
        
        if path is None:
            logger.warning(f"Path '{path_key}' not found in configuration")
            return None
        
        return os.path.abspath(os.path.expanduser(path))
    
    def is_path_allowed(self, path: str) -> bool:
        """
        Check if a path is allowed according to the security configuration.
        
        Args:
            path (str): The path to check
        
        Returns:
            bool: True if the path is allowed, False otherwise
        """
        path = os.path.abspath(os.path.expanduser(path))
        allowed_areas = [os.path.abspath(os.path.expanduser(area)) for area in self.get("security.allowed_areas", [])]
        
        for area in allowed_areas:
            if path.startswith(area):
                return True
        
        return False
    
    def reset_to_defaults(self) -> bool:
        """Reset the configuration to the default values."""
        self._config = DEFAULT_CONFIG.copy()
        return self.save_config()
    
    def get_all(self) -> Dict[str, Any]:
        """Get the entire configuration."""
        return self._config.copy()

# Create a singleton instance
config = Config()

def get(key_path: str, default: Any = None) -> Any:
    """
    Get a configuration value by its key path.
    
    Args:
        key_path (str): The key path in dot notation (e.g., 'paths.agentic_root')
        default (Any, optional): The default value to return if the key is not found
    
    Returns:
        The configuration value, or the default value if the key is not found
    """
    return config.get(key_path, default)

def set(key_path: str, value: Any) -> bool:
    """
    Set a configuration value by its key path.
    
    Args:
        key_path (str): The key path in dot notation (e.g., 'paths.agentic_root')
        value (Any): The value to set
    
    Returns:
        bool: True if the value was set successfully, False otherwise
    """
    return config.set(key_path, value)

def get_path(path_key: str) -> Optional[str]:
    """
    Get a path from the configuration, ensuring it is an absolute path.
    
    Args:
        path_key (str): The key for the path in the paths section
    
    Returns:
        Optional[str]: The absolute path, or None if the path is not found
    """
    return config.get_path(path_key)

def is_path_allowed(path: str) -> bool:
    """
    Check if a path is allowed according to the security configuration.
    
    Args:
        path (str): The path to check
    
    Returns:
        bool: True if the path is allowed, False otherwise
    """
    return config.is_path_allowed(path)

def reset_to_defaults() -> bool:
    """Reset the configuration to the default values."""
    return config.reset_to_defaults()

def get_all() -> Dict[str, Any]:
    """Get the entire configuration."""
    return config.get_all()

# Functions for the ag CLI

def get_config(args):
    """
    Get a configuration value, called by the ag script.
    
    Args:
        args: Command-line arguments
    
    Returns:
        int: Exit code
    """
    if not args:
        print("Error: No key specified")
        print("Usage: ag config get <key>")
        return 1
    
    key = args[0]
    value = get(key)
    
    if value is not None:
        print(f"{key}: {value}")
    else:
        print(f"Key '{key}' not found in configuration")
        return 1
    
    return 0

def set_config(args):
    """
    Set a configuration value, called by the ag script.
    
    Args:
        args: Command-line arguments
    
    Returns:
        int: Exit code
    """
    if len(args) < 2:
        print("Error: Not enough arguments")
        print("Usage: ag config set <key> <value>")
        return 1
    
    key = args[0]
    value_str = args[1]
    
    # Try to convert the value to the appropriate type
    try:
        # Try to convert to int
        value = int(value_str)
    except ValueError:
        try:
            # Try to convert to float
            value = float(value_str)
        except ValueError:
            # Try to convert to bool
            if value_str.lower() in ["true", "yes", "1"]:
                value = True
            elif value_str.lower() in ["false", "no", "0"]:
                value = False
            else:
                # Keep as string
                value = value_str
    
    if set(key, value):
        print(f"Set {key} to {value}")
    else:
        print(f"Failed to set {key}")
        return 1
    
    return 0

def list_config(args):
    """
    List all configuration values, called by the ag script.
    
    Args:
        args: Command-line arguments
    
    Returns:
        int: Exit code
    """
    if args and "--section" in args:
        section_index = args.index("--section")
        if section_index + 1 < len(args):
            section = args[section_index + 1]
            section_data = get(section)
            if section_data is not None:
                print(f"{section}:")
                for key, value in section_data.items():
                    print(f"  {key}: {value}")
            else:
                print(f"Section '{section}' not found in configuration")
                return 1
        else:
            print("Error: No section specified after --section")
            return 1
    else:
        config_dict = get_all()
        print(json.dumps(config_dict, indent=2))
    
    return 0

def reset_config(args):
    """
    Reset the configuration to the default values, called by the ag script.
    
    Args:
        args: Command-line arguments
    
    Returns:
        int: Exit code
    """
    if reset_to_defaults():
        print("Configuration reset to defaults")
    else:
        print("Failed to reset configuration")
        return 1
    
    return 0

def check_path(args):
    """
    Check if a path is allowed, called by the ag script.
    
    Args:
        args: Command-line arguments
    
    Returns:
        int: Exit code
    """
    if not args:
        print("Error: No path specified")
        print("Usage: ag config check <path>")
        return 1
    
    path = args[0]
    
    if is_path_allowed(path):
        print(f"Path '{path}' is allowed")
    else:
        print(f"Path '{path}' is not allowed")
        return 1
    
    return 0

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Agentic Framework Configuration Manager")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Get command
    get_parser = subparsers.add_parser("get", help="Get a configuration value")
    get_parser.add_argument("key", help="The key path in dot notation (e.g., 'paths.agentic_root')")
    
    # Set command
    set_parser = subparsers.add_parser("set", help="Set a configuration value")
    set_parser.add_argument("key", help="The key path in dot notation (e.g., 'paths.agentic_root')")
    set_parser.add_argument("value", help="The value to set")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List all configuration values")
    list_parser.add_argument("--section", help="The section to list (e.g., 'paths')")
    
    # Reset command
    reset_parser = subparsers.add_parser("reset", help="Reset the configuration to the default values")
    
    # Check command
    check_parser = subparsers.add_parser("check", help="Check if a path is allowed")
    check_parser.add_argument("path", help="The path to check")
    
    args = parser.parse_args()
    
    if args.command == "get":
        value = get(args.key)
        if value is not None:
            print(f"{args.key}: {value}")
        else:
            print(f"Key '{args.key}' not found in configuration")
    elif args.command == "set":
        # Try to convert the value to the appropriate type
        try:
            # Try to convert to int
            value = int(args.value)
        except ValueError:
            try:
                # Try to convert to float
                value = float(args.value)
            except ValueError:
                # Try to convert to bool
                if args.value.lower() in ["true", "yes", "1"]:
                    value = True
                elif args.value.lower() in ["false", "no", "0"]:
                    value = False
                else:
                    # Keep as string
                    value = args.value
        
        if set(args.key, value):
            print(f"Set {args.key} to {value}")
        else:
            print(f"Failed to set {args.key}")
    elif args.command == "list":
        if args.section:
            section = get(args.section)
            if section is not None:
                print(f"{args.section}:")
                for key, value in section.items():
                    print(f"  {key}: {value}")
            else:
                print(f"Section '{args.section}' not found in configuration")
        else:
            config_dict = get_all()
            print(json.dumps(config_dict, indent=2))
    elif args.command == "reset":
        if reset_to_defaults():
            print("Configuration reset to defaults")
        else:
            print("Failed to reset configuration")
    elif args.command == "check":
        if is_path_allowed(args.path):
            print(f"Path '{args.path}' is allowed")
        else:
            print(f"Path '{args.path}' is not allowed")
    else:
        parser.print_help()
