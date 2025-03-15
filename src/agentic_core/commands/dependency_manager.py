#!/usr/bin/env python3
"""
Dependency Management System

This module provides version checking for dependencies like uv and fallback mechanisms
for critical functionality. It helps ensure compatibility and provides alternatives
when external tools change their API or behavior.
"""

import os
import sys
import json
import logging
import subprocess
import shutil
import re
import platform
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from datetime import datetime

# Import the config module from agentic_core
from agentic_core.commands import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.expanduser("~/Agentic/logs/dependency_manager.log"), mode='a')
    ]
)
logger = logging.getLogger("dependency_manager")

# Create logs directory if it doesn't exist
os.makedirs(os.path.expanduser("~/Agentic/logs"), exist_ok=True)

# Default dependency versions
DEFAULT_DEPENDENCIES = {
    "uv": {
        "min_version": "0.1.0",
        "recommended_version": "0.1.11",
        "install_command": "curl -LsSf https://astral.sh/uv/install.sh | sh",
        "version_command": "uv --version",
        "version_regex": r"(\d+\.\d+\.\d+)",
        "fallback": {
            "enabled": True,
            "module": "pip_fallback"
        }
    },
    "python": {
        "min_version": "3.8.0",
        "recommended_version": "3.12.0",
        "version_command": "python --version",
        "version_regex": r"Python (\d+\.\d+\.\d+)",
        "fallback": {
            "enabled": False
        }
    }
}

def get_dependency_config(dependency_name: str) -> Dict:
    """
    Get the configuration for a dependency.
    
    Args:
        dependency_name (str): The name of the dependency
    
    Returns:
        Dict: The dependency configuration
    """
    # Try to get from config first
    dependencies = config.get("dependencies", {})
    
    if dependency_name in dependencies:
        return dependencies[dependency_name]
    
    # Fall back to DEFAULT_DEPENDENCIES
    if dependency_name in DEFAULT_DEPENDENCIES:
        return DEFAULT_DEPENDENCIES[dependency_name]
    
    logger.warning(f"No configuration found for dependency: {dependency_name}")
    return {}

def parse_version(version_str: str) -> Tuple[int, ...]:
    """
    Parse a version string into a tuple of integers.
    
    Args:
        version_str (str): The version string (e.g., "1.2.3")
    
    Returns:
        Tuple[int, ...]: The parsed version as a tuple of integers
    """
    return tuple(map(int, version_str.split('.')))

def compare_versions(version1: str, version2: str) -> int:
    """
    Compare two version strings.
    
    Args:
        version1 (str): The first version string
        version2 (str): The second version string
    
    Returns:
        int: -1 if version1 < version2, 0 if version1 == version2, 1 if version1 > version2
    """
    v1 = parse_version(version1)
    v2 = parse_version(version2)
    
    if v1 < v2:
        return -1
    elif v1 > v2:
        return 1
    else:
        return 0

def get_installed_version(dependency_name: str) -> Optional[str]:
    """
    Get the installed version of a dependency.
    
    Args:
        dependency_name (str): The name of the dependency
    
    Returns:
        Optional[str]: The installed version, or None if not installed or version cannot be determined
    """
    dependency_config = get_dependency_config(dependency_name)
    
    if not dependency_config or "version_command" not in dependency_config:
        logger.warning(f"No version command found for dependency: {dependency_name}")
        return None
    
    version_command = dependency_config["version_command"]
    version_regex = dependency_config.get("version_regex", r"(\d+\.\d+\.\d+)")
    
    try:
        # Run the version command
        result = subprocess.run(
            version_command,
            shell=True,
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode != 0:
            logger.warning(f"Failed to get version for {dependency_name}: {result.stderr}")
            return None
        
        # Extract the version using regex
        output = result.stdout.strip() or result.stderr.strip()
        match = re.search(version_regex, output)
        
        if match:
            return match.group(1)
        else:
            logger.warning(f"Could not extract version from output: {output}")
            return None
    except Exception as e:
        logger.error(f"Error getting version for {dependency_name}: {e}")
        return None

def check_dependency(dependency_name: str) -> Dict:
    """
    Check if a dependency is installed and meets the minimum version requirements.
    
    Args:
        dependency_name (str): The name of the dependency
    
    Returns:
        Dict: A dictionary with the check results
    """
    dependency_config = get_dependency_config(dependency_name)
    
    if not dependency_config:
        return {
            "name": dependency_name,
            "installed": False,
            "version": None,
            "min_version": None,
            "recommended_version": None,
            "meets_min_requirements": False,
            "is_recommended_version": False,
            "fallback_available": False,
            "error": "No configuration found for dependency"
        }
    
    installed_version = get_installed_version(dependency_name)
    min_version = dependency_config.get("min_version")
    recommended_version = dependency_config.get("recommended_version")
    fallback_available = dependency_config.get("fallback", {}).get("enabled", False)
    
    result = {
        "name": dependency_name,
        "installed": installed_version is not None,
        "version": installed_version,
        "min_version": min_version,
        "recommended_version": recommended_version,
        "meets_min_requirements": False,
        "is_recommended_version": False,
        "fallback_available": fallback_available
    }
    
    if installed_version and min_version:
        result["meets_min_requirements"] = compare_versions(installed_version, min_version) >= 0
    
    if installed_version and recommended_version:
        result["is_recommended_version"] = compare_versions(installed_version, recommended_version) >= 0
    
    return result

def install_dependency(dependency_name: str) -> bool:
    """
    Install a dependency.
    
    Args:
        dependency_name (str): The name of the dependency
    
    Returns:
        bool: True if the installation was successful, False otherwise
    """
    dependency_config = get_dependency_config(dependency_name)
    
    if not dependency_config or "install_command" not in dependency_config:
        logger.warning(f"No install command found for dependency: {dependency_name}")
        return False
    
    install_command = dependency_config["install_command"]
    
    try:
        logger.info(f"Installing {dependency_name}...")
        result = subprocess.run(
            install_command,
            shell=True,
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode != 0:
            logger.error(f"Failed to install {dependency_name}: {result.stderr}")
            return False
        
        logger.info(f"Successfully installed {dependency_name}")
        return True
    except Exception as e:
        logger.error(f"Error installing {dependency_name}: {e}")
        return False

def update_dependency(dependency_name: str) -> bool:
    """
    Update a dependency to the recommended version.
    
    Args:
        dependency_name (str): The name of the dependency
    
    Returns:
        bool: True if the update was successful, False otherwise
    """
    # For most dependencies, update is the same as install
    return install_dependency(dependency_name)

def load_fallback_module(dependency_name: str):
    """
    Load a fallback module for a dependency.
    
    Args:
        dependency_name (str): The name of the dependency
    
    Returns:
        module: The fallback module, or None if not available
    """
    dependency_config = get_dependency_config(dependency_name)
    
    if not dependency_config or "fallback" not in dependency_config:
        logger.warning(f"No fallback configuration found for dependency: {dependency_name}")
        return None
    
    fallback_config = dependency_config["fallback"]
    
    if not fallback_config.get("enabled", False):
        logger.warning(f"Fallback is not enabled for dependency: {dependency_name}")
        return None
    
    module_name = fallback_config.get("module")
    
    if not module_name:
        logger.warning(f"No fallback module specified for dependency: {dependency_name}")
        return None
    
    try:
        # Try to import the fallback module
        module = __import__(module_name)
        logger.info(f"Successfully loaded fallback module for {dependency_name}: {module_name}")
        return module
    except ImportError:
        logger.error(f"Failed to import fallback module for {dependency_name}: {module_name}")
        return None

# Fallback implementations

class PipFallback:
    """Fallback implementation for uv using pip."""
    
    @staticmethod
    def install_package(package_name: str, venv_path: Optional[str] = None) -> bool:
        """
        Install a package using pip.
        
        Args:
            package_name (str): The name of the package to install
            venv_path (Optional[str]): The path to the virtual environment
        
        Returns:
            bool: True if the installation was successful, False otherwise
        """
        pip_command = "pip"
        
        if venv_path:
            # Determine the pip path based on the virtual environment
            if platform.system() == "Windows":
                pip_path = os.path.join(venv_path, "Scripts", "pip.exe")
            else:
                pip_path = os.path.join(venv_path, "bin", "pip")
            
            if os.path.exists(pip_path):
                pip_command = pip_path
        
        try:
            logger.info(f"Installing {package_name} using pip fallback...")
            result = subprocess.run(
                f"{pip_command} install {package_name}",
                shell=True,
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode != 0:
                logger.error(f"Failed to install {package_name} using pip: {result.stderr}")
                return False
            
            logger.info(f"Successfully installed {package_name} using pip")
            return True
        except Exception as e:
            logger.error(f"Error installing {package_name} using pip: {e}")
            return False
    
    @staticmethod
    def create_venv(venv_path: str, python_version: Optional[str] = None) -> bool:
        """
        Create a virtual environment using venv.
        
        Args:
            venv_path (str): The path to create the virtual environment
            python_version (Optional[str]): The Python version to use
        
        Returns:
            bool: True if the creation was successful, False otherwise
        """
        python_command = "python"
        
        if python_version:
            # Try to find the specified Python version
            for cmd in [f"python{python_version}", f"python{python_version.split('.')[0]}"]:
                if shutil.which(cmd):
                    python_command = cmd
                    break
        
        try:
            logger.info(f"Creating virtual environment at {venv_path} using venv fallback...")
            result = subprocess.run(
                f"{python_command} -m venv {venv_path}",
                shell=True,
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode != 0:
                logger.error(f"Failed to create virtual environment: {result.stderr}")
                return False
            
            logger.info(f"Successfully created virtual environment at {venv_path}")
            return True
        except Exception as e:
            logger.error(f"Error creating virtual environment: {e}")
            return False

# Register fallback implementations
pip_fallback = PipFallback()

# CLI functions

def check_dependency_cli(args):
    """
    Check if a dependency is installed and meets requirements, called by the ag script.
    
    Args:
        args: Command-line arguments
    
    Returns:
        int: Exit code
    """
    if not args:
        print("Error: No dependency specified")
        print("Usage: ag dependency check <dependency>")
        return 1
    
    dependency_name = args[0]
    result = check_dependency(dependency_name)
    
    print(json.dumps(result, indent=2))
    
    if not result.get("installed", False):
        return 1
    
    if not result.get("meets_min_requirements", False):
        return 1
    
    return 0

def install_dependency_cli(args):
    """
    Install a dependency, called by the ag script.
    
    Args:
        args: Command-line arguments
    
    Returns:
        int: Exit code
    """
    if not args:
        print("Error: No dependency specified")
        print("Usage: ag dependency install <dependency>")
        return 1
    
    dependency_name = args[0]
    success = install_dependency(dependency_name)
    
    if success:
        print(f"Successfully installed {dependency_name}")
        return 0
    else:
        print(f"Failed to install {dependency_name}")
        return 1

def update_dependency_cli(args):
    """
    Update a dependency to the recommended version, called by the ag script.
    
    Args:
        args: Command-line arguments
    
    Returns:
        int: Exit code
    """
    if not args:
        print("Error: No dependency specified")
        print("Usage: ag dependency update <dependency>")
        return 1
    
    dependency_name = args[0]
    success = update_dependency(dependency_name)
    
    if success:
        print(f"Successfully updated {dependency_name}")
        return 0
    else:
        print(f"Failed to update {dependency_name}")
        return 1

def list_dependencies_cli(args):
    """
    List all dependencies and their status, called by the ag script.
    
    Args:
        args: Command-line arguments
    
    Returns:
        int: Exit code
    """
    # Get dependencies from config and DEFAULT_DEPENDENCIES
    config_dependencies = config.get("dependencies", {})
    all_dependencies = {**DEFAULT_DEPENDENCIES, **config_dependencies}
    
    results = {}
    
    for dependency_name in all_dependencies.keys():
        results[dependency_name] = check_dependency(dependency_name)
    
    print(json.dumps(results, indent=2))
    return 0

def fallback_cli(args):
    """
    Use a fallback implementation for a dependency, called by the ag script.
    
    Args:
        args: Command-line arguments
    
    Returns:
        int: Exit code
    """
    if len(args) < 2:
        print("Error: Missing arguments")
        print("Usage: ag dependency fallback <dependency> <action> [--args <json_args>]")
        return 1
    
    dependency_name = args[0]
    action = args[1]
    action_args_str = None
    
    # Parse --args if provided
    for i in range(2, len(args)):
        if args[i] == "--args" and i + 1 < len(args):
            action_args_str = args[i + 1]
            break
    
    if dependency_name == "uv" and action == "install-package":
        if not action_args_str:
            print("Error: --args is required for install-package action")
            return 1
        
        try:
            action_args = json.loads(action_args_str)
            package_name = action_args.get("package_name")
            venv_path = action_args.get("venv_path")
            
            if not package_name:
                print("Error: package_name is required for install-package action")
                return 1
            
            success = pip_fallback.install_package(package_name, venv_path)
            
            if success:
                print(f"Successfully installed {package_name} using pip fallback")
                return 0
            else:
                print(f"Failed to install {package_name} using pip fallback")
                return 1
        except json.JSONDecodeError:
            print("Error: Invalid JSON format for --args")
            return 1
    elif dependency_name == "uv" and action == "create-venv":
        if not action_args_str:
            print("Error: --args is required for create-venv action")
            return 1
        
        try:
            action_args = json.loads(action_args_str)
            venv_path = action_args.get("venv_path")
            python_version = action_args.get("python_version")
            
            if not venv_path:
                print("Error: venv_path is required for create-venv action")
                return 1
            
            success = pip_fallback.create_venv(venv_path, python_version)
            
            if success:
                print(f"Successfully created virtual environment at {venv_path} using venv fallback")
                return 0
            else:
                print(f"Failed to create virtual environment at {venv_path} using venv fallback")
                return 1
        except json.JSONDecodeError:
            print("Error: Invalid JSON format for --args")
            return 1
    else:
        print(f"Error: Unsupported fallback action: {action} for dependency: {dependency_name}")
        return 1

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Agentic Framework Dependency Manager")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Check command
    check_parser = subparsers.add_parser("check", help="Check if a dependency is installed and meets requirements")
    check_parser.add_argument("dependency", help="The name of the dependency to check")
    
    # Install command
    install_parser = subparsers.add_parser("install", help="Install a dependency")
    install_parser.add_argument("dependency", help="The name of the dependency to install")
    
    # Update command
    update_parser = subparsers.add_parser("update", help="Update a dependency to the recommended version")
    update_parser.add_argument("dependency", help="The name of the dependency to update")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List all dependencies and their status")
    
    # Fallback command
    fallback_parser = subparsers.add_parser("fallback", help="Use a fallback implementation for a dependency")
    fallback_parser.add_argument("dependency", help="The name of the dependency to use fallback for")
    fallback_parser.add_argument("action", help="The action to perform with the fallback")
    fallback_parser.add_argument("--args", help="Arguments for the fallback action (JSON format)")
    
    args = parser.parse_args()
    
    if args.command == "check":
        result = check_dependency(args.dependency)
        print(json.dumps(result, indent=2))
    elif args.command == "install":
        success = install_dependency(args.dependency)
        if success:
            print(f"Successfully installed {args.dependency}")
        else:
            print(f"Failed to install {args.dependency}")
            sys.exit(1)
    elif args.command == "update":
        success = update_dependency(args.dependency)
        if success:
            print(f"Successfully updated {args.dependency}")
        else:
            print(f"Failed to update {args.dependency}")
            sys.exit(1)
    elif args.command == "list":
        dependencies = {**DEFAULT_DEPENDENCIES, **config.get("dependencies", {})}
        results = {}
        
        for dependency in dependencies.keys():
            results[dependency] = check_dependency(dependency)
        
        print(json.dumps(results, indent=2))
    elif args.command == "fallback":
        if args.dependency == "uv" and args.action == "install-package":
            if not args.args:
                print("Error: --args is required for install-package action")
                sys.exit(1)
            
            try:
                action_args = json.loads(args.args)
                package_name = action_args.get("package_name")
                venv_path = action_args.get("venv_path")
                
                if not package_name:
                    print("Error: package_name is required for install-package action")
                    sys.exit(1)
                
                success = pip_fallback.install_package(package_name, venv_path)
                
                if success:
                    print(f"Successfully installed {package_name} using pip fallback")
                else:
                    print(f"Failed to install {package_name} using pip fallback")
                    sys.exit(1)
            except json.JSONDecodeError:
                print("Error: Invalid JSON format for --args")
                sys.exit(1)
        elif args.dependency == "uv" and args.action == "create-venv":
            if not args.args:
                print("Error: --args is required for create-venv action")
                sys.exit(1)
            
            try:
                action_args = json.loads(args.args)
                venv_path = action_args.get("venv_path")
                python_version = action_args.get("python_version")
                
                if not venv_path:
                    print("Error: venv_path is required for create-venv action")
                    sys.exit(1)
                
                success = pip_fallback.create_venv(venv_path, python_version)
                
                if success:
                    print(f"Successfully created virtual environment at {venv_path} using venv fallback")
                else:
                    print(f"Failed to create virtual environment at {venv_path} using venv fallback")
                    sys.exit(1)
            except json.JSONDecodeError:
                print("Error: Invalid JSON format for --args")
                sys.exit(1)
        else:
            print(f"Error: Unsupported fallback action: {args.action} for dependency: {args.dependency}")
            sys.exit(1)
    else:
        parser.print_help()
