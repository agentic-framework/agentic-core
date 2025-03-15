#!/usr/bin/env python3
"""
Setup Manager

This module provides utilities for setting up the Agentic framework.
It handles installing dependencies, creating directories, and initializing the registry.
"""

import os
import sys
import subprocess
import logging
import shutil
import json
from datetime import datetime
import time
import platform

# Import the config module from agentic_core
from agentic_core.commands import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.expanduser("~/Agentic/logs/setup.log"), mode='a')
    ]
)
logger = logging.getLogger("setup")

# Create logs directory if it doesn't exist
os.makedirs(os.path.expanduser("~/Agentic/logs"), exist_ok=True)

# Base directories
AGENTIC_DIR = config.get_path("agentic_root") or os.path.expanduser("~/Agentic")
TMP_DIR = config.get_path("tmp_dir") or os.path.join(AGENTIC_DIR, "tmp")
PROJECTS_DIR = config.get_path("projects_dir") or os.path.join(AGENTIC_DIR, "projects")
SHARED_DIR = config.get_path("shared_dir") or os.path.join(AGENTIC_DIR, "shared")
LOGS_DIR = config.get_path("logs_dir") or os.path.join(AGENTIC_DIR, "logs")
CACHE_DIR = config.get_path("cache_dir") or os.path.join(AGENTIC_DIR, "cache")
BACKUP_DIR = config.get_path("backups_dir") or os.path.join(AGENTIC_DIR, "backups")
REGISTRY_PATH = config.get_path("registry_file") or os.path.join(AGENTIC_DIR, "venv_registry.json")

# Required directories
REQUIRED_DIRS = [
    (AGENTIC_DIR, "Agentic root directory"),
    (TMP_DIR, "Temporary files directory"),
    (PROJECTS_DIR, "Projects directory"),
    (SHARED_DIR, "Shared resources directory"),
    (LOGS_DIR, "Logs directory"),
    (CACHE_DIR, "Cache directory"),
    (BACKUP_DIR, "Backups directory")
]

def run_command(command, capture_output=True, timeout=300):
    """Run a shell command and return the output with error handling."""
    try:
        if capture_output:
            result = subprocess.run(
                command,
                shell=True,
                check=True,
                text=True,
                capture_output=True,
                timeout=timeout
            )
            return result.stdout.strip()
        else:
            # For commands where we want to see the output in real-time
            subprocess.run(
                command,
                shell=True,
                check=True,
                timeout=timeout
            )
            return True
    except subprocess.TimeoutExpired:
        logger.warning(f"Command timed out after {timeout} seconds: {command}")
        return None
    except subprocess.CalledProcessError as e:
        logger.warning(f"Command failed: {command}")
        if capture_output:
            logger.warning(f"Error message: {e.stderr}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error executing command: {e}")
        return None

def print_status(message, status, details=None):
    """Print a status message with color coding."""
    if status:
        status_str = "\033[92m✓\033[0m"  # Green checkmark
    else:
        status_str = "\033[91m✗\033[0m"  # Red X
    
    print(f"{status_str} {message}")
    
    if details and not status:
        print(f"  \033[93m{details}\033[0m")  # Yellow details

def install_dependencies(args):
    """Install required dependencies."""
    print("\n\033[1mInstalling Dependencies\033[0m\n")
    logger.info("Starting dependency installation")
    
    # Check if uv is already installed
    uv_path = shutil.which("uv")
    if uv_path:
        try:
            result = subprocess.run(
                ["uv", "--version"],
                capture_output=True,
                text=True,
                check=True
            )
            version = result.stdout.strip()
            print_status(f"uv is already installed (version {version})", True)
            logger.info(f"uv is already installed (version {version})")
            
            # Ask if the user wants to update uv
            if "--force" not in args:
                print("\nWould you like to update uv to the latest version? (y/n)")
                response = input("> ").lower()
                if response == 'y':
                    update_uv()
            
            return 0
        except subprocess.CalledProcessError:
            print_status("uv is installed but failed to get version", False, "Will attempt to reinstall")
            logger.warning("uv is installed but failed to get version")
    
    # Install uv
    print("\nInstalling uv...")
    logger.info("Installing uv")
    
    # Determine the installation command based on the platform
    if platform.system() == "Darwin":  # macOS
        if platform.machine() == "arm64":  # Apple Silicon
            install_cmd = 'curl -LsSf https://astral.sh/uv/install.sh | sh'
        else:  # Intel Mac
            install_cmd = 'curl -LsSf https://astral.sh/uv/install.sh | sh'
    elif platform.system() == "Linux":
        install_cmd = 'curl -LsSf https://astral.sh/uv/install.sh | sh'
    elif platform.system() == "Windows":
        install_cmd = 'powershell -Command "irm https://astral.sh/uv/install.ps1 | iex"'
    else:
        print_status("Unsupported platform", False, f"Platform: {platform.system()}")
        logger.error(f"Unsupported platform: {platform.system()}")
        return 1
    
    # Run the installation command
    result = run_command(install_cmd, capture_output=False)
    if result is None:
        print_status("Failed to install uv", False, "Check the logs for details")
        logger.error("Failed to install uv")
        return 1
    
    # Verify the installation
    uv_path = shutil.which("uv")
    if uv_path:
        try:
            result = subprocess.run(
                ["uv", "--version"],
                capture_output=True,
                text=True,
                check=True
            )
            version = result.stdout.strip()
            print_status(f"uv installed successfully (version {version})", True)
            logger.info(f"uv installed successfully (version {version})")
            return 0
        except subprocess.CalledProcessError:
            print_status("uv was installed but failed to run", False, "Check the logs for details")
            logger.error("uv was installed but failed to run")
            return 1
    else:
        print_status("uv installation failed", False, "Check the logs for details")
        logger.error("uv installation failed")
        return 1

def update_uv():
    """Update uv to the latest version."""
    print("\nUpdating uv...")
    logger.info("Updating uv")
    
    # Determine the update command based on the platform
    if platform.system() == "Darwin" or platform.system() == "Linux":  # macOS or Linux
        update_cmd = 'curl -LsSf https://astral.sh/uv/install.sh | sh'
    elif platform.system() == "Windows":
        update_cmd = 'powershell -Command "irm https://astral.sh/uv/install.ps1 | iex"'
    else:
        print_status("Unsupported platform", False, f"Platform: {platform.system()}")
        logger.error(f"Unsupported platform: {platform.system()}")
        return 1
    
    # Run the update command
    result = run_command(update_cmd, capture_output=False)
    if result is None:
        print_status("Failed to update uv", False, "Check the logs for details")
        logger.error("Failed to update uv")
        return 1
    
    # Verify the update
    try:
        result = subprocess.run(
            ["uv", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        version = result.stdout.strip()
        print_status(f"uv updated successfully (version {version})", True)
        logger.info(f"uv updated successfully (version {version})")
        return 0
    except subprocess.CalledProcessError:
        print_status("uv was updated but failed to run", False, "Check the logs for details")
        logger.error("uv was updated but failed to run")
        return 1

def create_directories(args):
    """Create the required directory structure."""
    print("\n\033[1mCreating Directory Structure\033[0m\n")
    logger.info("Creating directory structure")
    
    all_exist = True
    created_dirs = []
    
    for dir_path, description in REQUIRED_DIRS:
        exists = os.path.exists(dir_path) and os.path.isdir(dir_path)
        
        if not exists:
            try:
                os.makedirs(dir_path, exist_ok=True)
                created_dirs.append(dir_path)
                exists = True
                print_status(f"{description}: {dir_path}", exists, "Created directory")
                logger.info(f"Created directory: {dir_path}")
            except Exception as e:
                print_status(f"{description}: {dir_path}", False, f"Failed to create directory: {e}")
                logger.error(f"Failed to create directory {dir_path}: {e}")
                all_exist = False
        else:
            print_status(f"{description}: {dir_path}", exists)
    
    if created_dirs:
        print("\nCreated the following directories:")
        for dir_path in created_dirs:
            print(f"  - {dir_path}")
    
    return 0 if all_exist else 1

def initialize_registry(args):
    """Initialize the virtual environment registry."""
    print("\n\033[1mInitializing Virtual Environment Registry\033[0m\n")
    logger.info("Initializing virtual environment registry")
    
    # Check if registry already exists
    if os.path.exists(REGISTRY_PATH) and "--force" not in args:
        try:
            with open(REGISTRY_PATH, 'r') as f:
                registry = json.load(f)
            
            if "virtual_environments" in registry:
                venv_count = len(registry["virtual_environments"])
                print_status(f"Registry already exists: {REGISTRY_PATH} ({venv_count} environments)", True)
                logger.info(f"Registry already exists: {REGISTRY_PATH} ({venv_count} environments)")
                
                # Ask if the user wants to reinitialize
                print("\nWould you like to reinitialize the registry? This will backup the current registry. (y/n)")
                response = input("> ").lower()
                if response != 'y':
                    return 0
                
                # Backup the existing registry
                backup_path = f"{REGISTRY_PATH}.bak.{int(time.time())}"
                shutil.copy2(REGISTRY_PATH, backup_path)
                print_status(f"Backed up registry to {backup_path}", True)
                logger.info(f"Backed up registry to {backup_path}")
        except Exception as e:
            print_status(f"Error reading existing registry: {e}", False, "Will create a new registry")
            logger.warning(f"Error reading existing registry: {e}")
    
    # Create the registry file
    try:
        registry = {
            "virtual_environments": [],
            "last_updated": datetime.now().isoformat(),
            "registry_version": "1.0.0",
            "metadata": {
                "description": "Registry of active Python virtual environments managed by uv",
                "managed_by": "agentic framework",
                "created_by": "setup.py"
            }
        }
        
        with open(REGISTRY_PATH, 'w') as f:
            json.dump(registry, f, indent=2)
        
        print_status(f"Created registry file: {REGISTRY_PATH}", True)
        logger.info(f"Created registry file: {REGISTRY_PATH}")
        return 0
    except Exception as e:
        print_status(f"Failed to create registry file: {REGISTRY_PATH}", False, str(e))
        logger.error(f"Failed to create registry file: {e}")
        return 1

def setup_all(args):
    """Run all setup steps."""
    print("\n\033[1mAgentic Framework Setup\033[0m")
    print("Running all setup steps...\n")
    logger.info("Starting complete setup")
    
    # Run all setup steps
    install_result = install_dependencies(args)
    create_result = create_directories(args)
    registry_result = initialize_registry(args)
    
    # Print summary
    print("\n\033[1mSetup Summary\033[0m")
    print_status("Install dependencies", install_result == 0)
    print_status("Create directories", create_result == 0)
    print_status("Initialize registry", registry_result == 0)
    
    all_success = (install_result == 0 and create_result == 0 and registry_result == 0)
    
    if all_success:
        print("\n\033[92mSetup completed successfully!\033[0m")
        print("You can now use the Agentic framework.")
        print("Run 'ag env check' to verify the environment is set up correctly.")
        logger.info("Setup completed successfully")
        return 0
    else:
        print("\n\033[91mSetup completed with errors.\033[0m")
        print("Please check the logs for details.")
        print("You can run individual setup steps to retry:")
        print("  ag setup install-dependencies")
        print("  ag setup create-directories")
        print("  ag setup initialize-registry")
        logger.warning("Setup completed with errors")
        return 1

if __name__ == "__main__":
    # Parse command line arguments
    if len(sys.argv) < 2:
        print("Error: No command specified")
        print("Usage: python setup.py <command> [options]")
        print("\nAvailable commands:")
        print("  install-dependencies  Install required dependencies")
        print("  create-directories    Create the required directory structure")
        print("  initialize-registry   Initialize the virtual environment registry")
        print("  all                   Run all setup steps")
        sys.exit(1)
    
    command = sys.argv[1]
    args = sys.argv[2:]
    
    if command == "install-dependencies":
        sys.exit(install_dependencies(args))
    elif command == "create-directories":
        sys.exit(create_directories(args))
    elif command == "initialize-registry":
        sys.exit(initialize_registry(args))
    elif command == "all":
        sys.exit(setup_all(args))
    else:
        print(f"Error: Unknown command '{command}'")
        sys.exit(1)
