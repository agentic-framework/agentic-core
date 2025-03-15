#!/usr/bin/env python3
"""
Virtual Environment Manager

This module provides utilities for managing the virtual environment registry.
It allows adding, removing, and listing virtual environments in the registry.
"""

import json
import os
import sys
import argparse
import subprocess
import shutil
import time
from datetime import datetime
import pathlib
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.expanduser("~/Agentic/logs/venv_manager.log"), mode='a')
    ]
)
logger = logging.getLogger("venv_manager")

# Create logs directory if it doesn't exist
os.makedirs(os.path.expanduser("~/Agentic/logs"), exist_ok=True)

# Registry file path
REGISTRY_PATH = os.path.expanduser("~/Agentic/venv_registry.json")
BACKUP_DIR = os.path.expanduser("~/Agentic/backups")

# Create backup directory if it doesn't exist
os.makedirs(BACKUP_DIR, exist_ok=True)

def backup_registry():
    """Create a backup of the registry file."""
    if not os.path.exists(REGISTRY_PATH):
        logger.warning("Cannot backup registry: file does not exist")
        return False
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(BACKUP_DIR, f"venv_registry_{timestamp}.json")
    
    try:
        shutil.copy2(REGISTRY_PATH, backup_path)
        logger.info(f"Created registry backup at {backup_path}")
        
        # Clean up old backups (keep last 10)
        backups = sorted([
            os.path.join(BACKUP_DIR, f) 
            for f in os.listdir(BACKUP_DIR) 
            if f.startswith("venv_registry_") and f.endswith(".json")
        ])
        
        if len(backups) > 10:
            for old_backup in backups[:-10]:
                os.remove(old_backup)
                logger.debug(f"Removed old backup: {old_backup}")
        
        return True
    except Exception as e:
        logger.error(f"Failed to backup registry: {e}")
        return False

def load_registry():
    """Load the virtual environment registry with error handling."""
    try:
        with open(REGISTRY_PATH, 'r') as f:
            registry = json.load(f)
            logger.debug("Registry loaded successfully")
            return registry
    except FileNotFoundError:
        # Create a new registry if it doesn't exist
        logger.info("Registry file not found, creating new registry")
        registry = {
            "virtual_environments": [],
            "last_updated": datetime.now().isoformat(),
            "registry_version": "1.0.0",
            "metadata": {
                "description": "Registry of active Python virtual environments managed by uv",
                "managed_by": "agentic framework"
            }
        }
        save_registry(registry)
        return registry
    except json.JSONDecodeError:
        logger.error("Registry file is corrupted or not valid JSON")
        
        # Try to restore from backup
        backups = sorted([
            os.path.join(BACKUP_DIR, f) 
            for f in os.listdir(BACKUP_DIR) 
            if f.startswith("venv_registry_") and f.endswith(".json")
        ], reverse=True)
        
        if backups:
            latest_backup = backups[0]
            logger.info(f"Attempting to restore from backup: {latest_backup}")
            try:
                with open(latest_backup, 'r') as f:
                    registry = json.load(f)
                
                # Save the restored registry
                save_registry(registry)
                logger.info("Registry restored from backup")
                return registry
            except Exception as e:
                logger.error(f"Failed to restore from backup: {e}")
        
        # Create a new registry if restoration fails
        logger.info("Creating new registry due to corruption")
        registry = {
            "virtual_environments": [],
            "last_updated": datetime.now().isoformat(),
            "registry_version": "1.0.0",
            "metadata": {
                "description": "Registry of active Python virtual environments managed by uv",
                "managed_by": "agentic framework",
                "note": "This registry was recreated due to corruption"
            }
        }
        save_registry(registry)
        return registry

def save_registry(registry):
    """Save the virtual environment registry with backup."""
    # Create a backup before saving
    if os.path.exists(REGISTRY_PATH):
        backup_registry()
    
    registry["last_updated"] = datetime.now().isoformat()
    
    try:
        # Write to a temporary file first
        temp_path = f"{REGISTRY_PATH}.tmp"
        with open(temp_path, 'w') as f:
            json.dump(registry, f, indent=2)
        
        # Rename the temporary file to the actual registry file
        os.replace(temp_path, REGISTRY_PATH)
        logger.debug("Registry saved successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to save registry: {e}")
        return False

def verify_venv(venv_path):
    """Verify that a virtual environment is valid and usable."""
    # Check for essential files/directories
    python_bin = os.path.join(venv_path, "bin", "python")
    pip_bin = os.path.join(venv_path, "bin", "pip")
    
    if not os.path.exists(python_bin) or not os.path.isfile(python_bin):
        logger.warning(f"Python binary not found in virtual environment: {python_bin}")
        return False
    
    if not os.path.exists(pip_bin) or not os.path.isfile(pip_bin):
        logger.warning(f"Pip binary not found in virtual environment: {pip_bin}")
        return False
    
    # Try to execute Python to verify it works
    try:
        result = subprocess.run(
            [python_bin, "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode != 0:
            logger.warning(f"Python binary exists but failed to execute: {result.stderr}")
            return False
        
        logger.info(f"Virtual environment Python version: {result.stdout.strip()}")
        return True
    except Exception as e:
        logger.warning(f"Failed to verify Python in virtual environment: {e}")
        return False

def get_python_version(venv_path):
    """Get the Python version from a virtual environment."""
    python_path = os.path.join(venv_path, "bin", "python")
    if not os.path.exists(python_path):
        return "unknown"
    
    try:
        result = subprocess.run(
            [python_path, "-c", "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception as e:
        logger.warning(f"Could not determine Python version: {e}")
    
    return "unknown"

def get_installed_packages(venv_path):
    """Get a list of installed packages in a virtual environment."""
    python_path = os.path.join(venv_path, "bin", "python")
    if not os.path.exists(python_path):
        return []
    
    try:
        result = subprocess.run(
            [python_path, "-m", "pip", "list", "--format=json"],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
    except Exception as e:
        logger.warning(f"Could not get installed packages: {e}")
    
    return []

def add_venv(venv_path, project_name, python_version=None, description=None, verify=True):
    """Add a virtual environment to the registry with verification."""
    registry = load_registry()
    
    # Convert to absolute path
    venv_path = os.path.abspath(os.path.expanduser(venv_path))
    
    # Check if venv exists
    if not os.path.isdir(venv_path):
        print(f"Error: Virtual environment directory not found: {venv_path}")
        logger.error(f"Virtual environment directory not found: {venv_path}")
        return False
    
    # Verify the virtual environment if requested
    if verify and not verify_venv(venv_path):
        print(f"Error: {venv_path} is not a valid virtual environment")
        logger.error(f"{venv_path} is not a valid virtual environment")
        
        # Ask if the user wants to add it anyway
        response = input("Add to registry anyway? (y/n): ").lower()
        if response != 'y':
            return False
    
    # Check if venv is already registered
    for venv in registry["virtual_environments"]:
        if venv["path"] == venv_path:
            print(f"Virtual environment already registered: {venv_path}")
            logger.info(f"Virtual environment already registered: {venv_path}")
            
            # Ask if the user wants to update it
            response = input("Update the existing entry? (y/n): ").lower()
            if response == 'y':
                # Update the entry
                venv["project_name"] = project_name
                if python_version:
                    venv["python_version"] = python_version
                if description:
                    venv["description"] = description
                venv["last_updated"] = datetime.now().isoformat()
                save_registry(registry)
                print(f"Updated virtual environment: {venv_path}")
                logger.info(f"Updated virtual environment: {venv_path}")
                return True
            return False
    
    # Get Python version if not provided
    if not python_version:
        python_version = get_python_version(venv_path)
    
    # Add venv to registry
    venv_info = {
        "path": venv_path,
        "project_name": project_name,
        "python_version": python_version,
        "description": description or f"Virtual environment for {project_name}",
        "created_at": datetime.now().isoformat(),
        "last_used": datetime.now().isoformat(),
        "last_updated": datetime.now().isoformat()
    }
    
    # Get installed packages
    packages = get_installed_packages(venv_path)
    if packages:
        venv_info["packages"] = packages
    
    registry["virtual_environments"].append(venv_info)
    save_registry(registry)
    print(f"Added virtual environment: {venv_path}")
    logger.info(f"Added virtual environment: {venv_path}")
    return True

def remove_venv(venv_path=None, project_name=None):
    """Remove a virtual environment from the registry."""
    if not venv_path and not project_name:
        print("Error: Either venv_path or project_name must be provided")
        logger.error("Cannot remove venv: no path or project name provided")
        return False
    
    registry = load_registry()
    
    if venv_path:
        venv_path = os.path.abspath(os.path.expanduser(venv_path))
    
    # Find and remove the venv
    updated_venvs = []
    removed = False
    
    for venv in registry["virtual_environments"]:
        if (venv_path and venv["path"] == venv_path) or (project_name and venv["project_name"] == project_name):
            print(f"Removing virtual environment: {venv['path']} ({venv['project_name']})")
            logger.info(f"Removing virtual environment: {venv['path']} ({venv['project_name']})")
            
            # Ask if the user wants to delete the directory as well
            if os.path.exists(venv["path"]):
                response = input(f"Delete the virtual environment directory at {venv['path']}? (y/n): ").lower()
                if response == 'y':
                    try:
                        shutil.rmtree(venv["path"])
                        print(f"Deleted directory: {venv['path']}")
                        logger.info(f"Deleted directory: {venv['path']}")
                    except Exception as e:
                        print(f"Error deleting directory: {e}")
                        logger.error(f"Error deleting directory {venv['path']}: {e}")
            
            removed = True
        else:
            updated_venvs.append(venv)
    
    if not removed:
        print("Virtual environment not found in registry")
        logger.warning("Virtual environment not found in registry for removal")
        return False
    
    registry["virtual_environments"] = updated_venvs
    save_registry(registry)
    return True

def list_venvs(verbose=False, show_packages=False):
    """List all registered virtual environments with enhanced output."""
    registry = load_registry()
    
    if not registry["virtual_environments"]:
        print("No virtual environments registered")
        return
    
    print(f"Registered Virtual Environments ({len(registry['virtual_environments'])}):")
    print("-" * 80)
    
    # Sort environments by last used date (most recent first)
    sorted_venvs = sorted(
        registry["virtual_environments"],
        key=lambda v: v.get("last_used", ""),
        reverse=True
    )
    
    for i, venv in enumerate(sorted_venvs, 1):
        # Check if the environment still exists
        exists = os.path.isdir(venv["path"])
        valid = exists and verify_venv(venv["path"])
        
        # Format the status indicator
        if valid:
            status = "\033[92m✓\033[0m"  # Green checkmark
        elif exists:
            status = "\033[93m!\033[0m"  # Yellow exclamation
        else:
            status = "\033[91m✗\033[0m"  # Red X
        
        print(f"{i}. {status} {venv['project_name']}")
        print(f"   Path: {venv['path']}")
        print(f"   Python: {venv['python_version']}")
        
        if verbose:
            print(f"   Description: {venv['description']}")
            print(f"   Created: {venv['created_at']}")
            print(f"   Last Used: {venv['last_used']}")
            
            if show_packages and "packages" in venv:
                print("   Installed Packages:")
                # Show top 10 packages
                for pkg in venv["packages"][:10]:
                    print(f"     - {pkg['name']} ({pkg['version']})")
                
                if len(venv["packages"]) > 10:
                    print(f"     ... and {len(venv['packages']) - 10} more")
        
        print()

def update_last_used(venv_path):
    """Update the last_used timestamp for a virtual environment."""
    registry = load_registry()
    venv_path = os.path.abspath(os.path.expanduser(venv_path))
    
    for venv in registry["virtual_environments"]:
        if venv["path"] == venv_path:
            venv["last_used"] = datetime.now().isoformat()
            save_registry(registry)
            logger.info(f"Updated last_used timestamp for {venv_path}")
            return True
    
    logger.warning(f"Could not update last_used: {venv_path} not found in registry")
    return False

def update_packages(venv_path=None, project_name=None):
    """Update the package list for a virtual environment."""
    if not venv_path and not project_name:
        print("Error: Either venv_path or project_name must be provided")
        logger.error("Cannot update packages: no path or project name provided")
        return False
    
    registry = load_registry()
    
    if venv_path:
        venv_path = os.path.abspath(os.path.expanduser(venv_path))
    
    # Find the venv
    found = False
    for venv in registry["virtual_environments"]:
        if (venv_path and venv["path"] == venv_path) or (project_name and venv["project_name"] == project_name):
            found = True
            
            # Check if the environment exists
            if not os.path.isdir(venv["path"]):
                print(f"Error: Virtual environment directory not found: {venv['path']}")
                logger.error(f"Virtual environment directory not found: {venv['path']}")
                return False
            
            # Get installed packages
            packages = get_installed_packages(venv["path"])
            if packages:
                venv["packages"] = packages
                venv["last_updated"] = datetime.now().isoformat()
                print(f"Updated package list for {venv['project_name']} ({len(packages)} packages)")
                logger.info(f"Updated package list for {venv['project_name']} ({len(packages)} packages)")
            else:
                print(f"Could not get package list for {venv['project_name']}")
                logger.warning(f"Could not get package list for {venv['project_name']}")
                return False
    
    if not found:
        print("Virtual environment not found in registry")
        logger.warning("Virtual environment not found in registry for package update")
        return False
    
    save_registry(registry)
    return True

def check_venv(venv_path=None, project_name=None):
    """Check if a virtual environment is registered and verify its status."""
    if not venv_path and not project_name:
        print("Error: Either venv_path or project_name must be provided")
        logger.error("Cannot check venv: no path or project name provided")
        return False
    
    registry = load_registry()
    
    if venv_path:
        venv_path = os.path.abspath(os.path.expanduser(venv_path))
    
    for venv in registry["virtual_environments"]:
        if (venv_path and venv["path"] == venv_path) or (project_name and venv["project_name"] == project_name):
            print(f"Virtual environment found: {venv['path']} ({venv['project_name']})")
            
            # Check if the directory exists
            if not os.path.isdir(venv["path"]):
                print(f"Warning: Directory does not exist: {venv['path']}")
                logger.warning(f"Virtual environment directory does not exist: {venv['path']}")
                return False
            
            # Verify the virtual environment
            if verify_venv(venv["path"]):
                print("Status: Valid")
                logger.info(f"Virtual environment is valid: {venv['path']}")
                return True
            else:
                print("Status: Invalid or corrupted")
                logger.warning(f"Virtual environment is invalid: {venv['path']}")
                return False
    
    print("Virtual environment not found in registry")
    logger.warning("Virtual environment not found in registry during check")
    return False

def cleanup_nonexistent():
    """Remove entries for virtual environments that no longer exist."""
    registry = load_registry()
    original_count = len(registry["virtual_environments"])
    
    updated_venvs = []
    for venv in registry["virtual_environments"]:
        if os.path.isdir(venv["path"]):
            updated_venvs.append(venv)
        else:
            print(f"Removing non-existent virtual environment: {venv['path']} ({venv['project_name']})")
            logger.info(f"Removing non-existent virtual environment: {venv['path']} ({venv['project_name']})")
    
    registry["virtual_environments"] = updated_venvs
    save_registry(registry)
    
    removed_count = original_count - len(updated_venvs)
    print(f"Cleanup complete. Removed {removed_count} non-existent virtual environments.")
    logger.info(f"Cleanup complete. Removed {removed_count} non-existent virtual environments")
    return removed_count > 0

def repair_registry():
    """Attempt to repair the registry by scanning for virtual environments."""
    print("Repairing registry...")
    logger.info("Starting registry repair")
    
    # Load the registry (this will create a new one if corrupted)
    registry = load_registry()
    
    # Keep track of existing paths
    existing_paths = {venv["path"] for venv in registry["virtual_environments"]}
    
    # Scan common locations for virtual environments
    scan_locations = [
        os.path.expanduser("~/Agentic/projects"),
        os.path.expanduser("~/Climate")
    ]
    
    found_venvs = []
    
    for location in scan_locations:
        if not os.path.isdir(location):
            continue
        
        print(f"Scanning {location} for virtual environments...")
        
        # Walk through the directory
        for root, dirs, files in os.walk(location):
            # Check if this directory is a virtual environment
            if ".venv" in dirs:
                venv_path = os.path.join(root, ".venv")
                
                # Skip if already in registry
                if venv_path in existing_paths:
                    continue
                
                # Verify it's a valid virtual environment
                if verify_venv(venv_path):
                    project_name = os.path.basename(root)
                    python_version = get_python_version(venv_path)
                    
                    found_venvs.append({
                        "path": venv_path,
                        "project_name": project_name,
                        "python_version": python_version
                    })
                    
                    print(f"Found virtual environment: {venv_path} ({project_name}, Python {python_version})")
    
    if found_venvs:
        print(f"\nFound {len(found_venvs)} new virtual environments.")
        
        for venv in found_venvs:
            response = input(f"Add {venv['path']} ({venv['project_name']}) to registry? (y/n): ").lower()
            if response == 'y':
                add_venv(
                    venv["path"],
                    venv["project_name"],
                    venv["python_version"],
                    f"Virtual environment for {venv['project_name']} (auto-discovered)",
                    verify=False
                )
    else:
        print("No new virtual environments found.")
    
    print("Registry repair complete.")
    logger.info("Registry repair complete")
    return True

# Functions for the ag CLI

def list_environments(args):
    """List registered virtual environments, called by the ag script."""
    verbose = "--verbose" in args or "-v" in args
    show_packages = "--packages" in args or "-p" in args
    return list_venvs(verbose, show_packages)

def create_environment(args):
    """Create a new virtual environment, called by the ag script."""
    if len(args) < 2:
        print("Error: Missing required arguments")
        print("Usage: ag venv create <venv_path> <project_name> [options]")
        return 1
    
    venv_path = args[0]
    project_name = args[1]
    
    # Parse optional arguments
    python_version = None
    description = None
    verify = True
    
    i = 2
    while i < len(args):
        if args[i] == "--python-version" and i + 1 < len(args):
            python_version = args[i + 1]
            i += 2
        elif args[i] == "--description" and i + 1 < len(args):
            description = args[i + 1]
            i += 2
        elif args[i] == "--no-verify":
            verify = False
            i += 1
        else:
            i += 1
    
    return add_venv(venv_path, project_name, python_version, description, verify)

def add_environment(args):
    """Add an existing virtual environment to the registry, called by the ag script."""
    if len(args) < 2:
        print("Error: Missing required arguments")
        print("Usage: ag venv add <venv_path> <project_name> [options]")
        return 1
    
    venv_path = args[0]
    project_name = args[1]
    
    # Parse optional arguments
    python_version = None
    description = None
    verify = True
    force = False
    
    i = 2
    while i < len(args):
        if args[i] == "--python-version" and i + 1 < len(args):
            python_version = args[i + 1]
            i += 2
        elif args[i] == "--description" and i + 1 < len(args):
            description = args[i + 1]
            i += 2
        elif args[i] == "--no-verify":
            verify = False
            i += 1
        elif args[i] == "--force":
            force = True
            verify = False
            i += 1
        else:
            i += 1
    
    # If force is true, we'll add the environment without verification or prompts
    if force:
        registry = load_registry()
        
        # Convert to absolute path
        venv_path = os.path.abspath(os.path.expanduser(venv_path))
        
        # Check if venv exists
        if not os.path.isdir(venv_path):
            print(f"Error: Virtual environment directory not found: {venv_path}")
            logger.error(f"Virtual environment directory not found: {venv_path}")
            return False
        
        # Check if venv is already registered
        for venv in registry["virtual_environments"]:
            if venv["path"] == venv_path:
                print(f"Virtual environment already registered: {venv_path}")
                logger.info(f"Virtual environment already registered: {venv_path}")
                
                # Update the entry
                venv["project_name"] = project_name
                if python_version:
                    venv["python_version"] = python_version
                if description:
                    venv["description"] = description
                venv["last_updated"] = datetime.now().isoformat()
                save_registry(registry)
                print(f"Updated virtual environment: {venv_path}")
                logger.info(f"Updated virtual environment: {venv_path}")
                return True
        
        # Get Python version if not provided
        if not python_version:
            python_version = get_python_version(venv_path)
        
        # Add venv to registry
        venv_info = {
            "path": venv_path,
            "project_name": project_name,
            "python_version": python_version,
            "description": description or f"Virtual environment for {project_name}",
            "created_at": datetime.now().isoformat(),
            "last_used": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat()
        }
        
        # Get installed packages
        packages = get_installed_packages(venv_path)
        if packages:
            venv_info["packages"] = packages
        
        registry["virtual_environments"].append(venv_info)
        save_registry(registry)
        print(f"Added virtual environment: {venv_path}")
        logger.info(f"Added virtual environment: {venv_path}")
        return True
    else:
        return add_venv(venv_path, project_name, python_version, description, verify)

def remove_environment(args):
    """Remove a virtual environment, called by the ag script."""
    venv_path = None
    project_name = None
    
    i = 0
    while i < len(args):
        if args[i] == "--venv-path" and i + 1 < len(args):
            venv_path = args[i + 1]
            i += 2
        elif args[i] == "--project-name" and i + 1 < len(args):
            project_name = args[i + 1]
            i += 2
        else:
            i += 1
    
    return remove_venv(venv_path, project_name)

def check_environment(args):
    """Check a virtual environment, called by the ag script."""
    venv_path = None
    project_name = None
    
    i = 0
    while i < len(args):
        if args[i] == "--venv-path" and i + 1 < len(args):
            venv_path = args[i + 1]
            i += 2
        elif args[i] == "--project-name" and i + 1 < len(args):
            project_name = args[i + 1]
            i += 2
        else:
            i += 1
    
    return check_venv(venv_path, project_name)

def cleanup_environments(args):
    """Clean up non-existent virtual environments, called by the ag script."""
    return cleanup_nonexistent()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Manage Python virtual environments registry")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Add command
    add_parser = subparsers.add_parser("add", help="Add a virtual environment to the registry")
    add_parser.add_argument("venv_path", help="Path to the virtual environment")
    add_parser.add_argument("project_name", help="Name of the project")
    add_parser.add_argument("--python-version", help="Python version (detected automatically if not provided)")
    add_parser.add_argument("--description", help="Description of the virtual environment")
    add_parser.add_argument("--no-verify", dest="verify", action="store_false", help="Skip verification of the virtual environment")
    
    # Remove command
    remove_parser = subparsers.add_parser("remove", help="Remove a virtual environment from the registry")
    remove_parser.add_argument("--venv-path", help="Path to the virtual environment")
    remove_parser.add_argument("--project-name", help="Name of the project")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List all registered virtual environments")
    list_parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed information")
    list_parser.add_argument("--packages", "-p", action="store_true", help="Show installed packages")
    
    # Check command
    check_parser = subparsers.add_parser("check", help="Check if a virtual environment is registered and verify its status")
    check_parser.add_argument("--venv-path", help="Path to the virtual environment")
    check_parser.add_argument("--project-name", help="Name of the project")
    
    # Update last used command
    update_parser = subparsers.add_parser("update-last-used", help="Update the last_used timestamp for a virtual environment")
    update_parser.add_argument("venv_path", help="Path to the virtual environment")
    
    # Update packages command
