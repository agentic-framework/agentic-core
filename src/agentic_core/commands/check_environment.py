#!/usr/bin/env python3
"""
Environment Checker

This module checks if the current environment is set up correctly according to the agent rules.
It verifies the installation of uv, the directory structure, and the registry file.
"""

import os
import sys
import json
import shutil
import subprocess
import time
import logging
from pathlib import Path
from datetime import datetime

# Import the config module from agentic_core
from agentic_core.commands import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.expanduser("~/Agentic/logs/check_environment.log"), mode='a')
    ]
)
logger = logging.getLogger("check_environment")

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

def print_status(message, status, details=None):
    """Print a status message with color coding."""
    if status:
        status_str = "\033[92m✓\033[0m"  # Green checkmark
    else:
        status_str = "\033[91m✗\033[0m"  # Red X
    
    print(f"{status_str} {message}")
    
    if details and not status:
        print(f"  \033[93m{details}\033[0m")  # Yellow details

def run_command(command, capture_output=True, timeout=30):
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

def check_uv_installation():
    """Check if uv is installed and get its version."""
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
            print_status(f"uv is installed (version {version})", True)
            logger.info(f"uv is installed (version {version})")
            return True
        except subprocess.CalledProcessError:
            print_status("uv is installed but failed to get version", False, "Try running 'uv --version' manually")
            logger.warning("uv is installed but failed to get version")
            return False
    else:
        print_status("uv is not installed", False, "Install uv using 'ag uv install'")
        logger.warning("uv is not installed")
        return False

def check_directory_structure():
    """Check if the required directory structure exists and create missing directories."""
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
    
    return all_exist

def check_registry_file():
    """Check if the registry file exists and is valid."""
    if not os.path.exists(REGISTRY_PATH):
        print_status(f"Virtual environment registry: {REGISTRY_PATH}", False, "Registry file does not exist")
        logger.warning(f"Registry file does not exist: {REGISTRY_PATH}")
        
        # Try to create the registry file
        try:
            registry = {
                "virtual_environments": [],
                "last_updated": datetime.now().isoformat(),
                "registry_version": "1.0.0",
                "metadata": {
                    "description": "Registry of active Python virtual environments managed by uv",
                    "managed_by": "agentic framework",
                    "created_by": "check_environment.py"
                }
            }
            
            with open(REGISTRY_PATH, 'w') as f:
                json.dump(registry, f, indent=2)
            
            print_status(f"Created new registry file: {REGISTRY_PATH}", True)
            logger.info(f"Created new registry file: {REGISTRY_PATH}")
            return True
        except Exception as e:
            print_status(f"Failed to create registry file: {REGISTRY_PATH}", False, str(e))
            logger.error(f"Failed to create registry file: {e}")
            return False
    
    try:
        with open(REGISTRY_PATH, 'r') as f:
            registry = json.load(f)
        
        if "virtual_environments" in registry:
            venv_count = len(registry["virtual_environments"])
            print_status(f"Virtual environment registry: {REGISTRY_PATH} ({venv_count} environments)", True)
            logger.info(f"Registry file is valid: {REGISTRY_PATH} ({venv_count} environments)")
            return True
        else:
            print_status(f"Virtual environment registry: {REGISTRY_PATH}", False, "Registry file is missing required fields")
            logger.warning(f"Registry file is missing required fields: {REGISTRY_PATH}")
            return False
    except json.JSONDecodeError:
        print_status(f"Virtual environment registry: {REGISTRY_PATH}", False, "Registry file is not valid JSON")
        logger.error(f"Registry file is not valid JSON: {REGISTRY_PATH}")
        
        # Try to backup and recreate
        backup_path = f"{REGISTRY_PATH}.bak.{int(time.time())}"
        try:
            shutil.copy2(REGISTRY_PATH, backup_path)
            print_status(f"Backed up corrupted registry to {backup_path}", True)
            logger.info(f"Backed up corrupted registry to {backup_path}")
            
            # Create a new registry file
            registry = {
                "virtual_environments": [],
                "last_updated": datetime.now().isoformat(),
                "registry_version": "1.0.0",
                "metadata": {
                    "description": "Registry of active Python virtual environments managed by uv",
                    "managed_by": "agentic framework",
                    "created_by": "check_environment.py",
                    "note": "This registry was recreated due to corruption"
                }
            }
            
            with open(REGISTRY_PATH, 'w') as f:
                json.dump(registry, f, indent=2)
            
            print_status(f"Created new registry file: {REGISTRY_PATH}", True)
            logger.info(f"Created new registry file: {REGISTRY_PATH}")
            return True
        except Exception as e:
            print_status(f"Failed to backup and recreate registry file", False, str(e))
            logger.error(f"Failed to backup and recreate registry file: {e}")
            return False
    except Exception as e:
        print_status(f"Virtual environment registry: {REGISTRY_PATH}", False, f"Error reading registry file: {e}")
        logger.error(f"Error reading registry file: {e}")
        return False

def check_python_installations():
    """Check Python installations managed by uv."""
    if not shutil.which("uv"):
        print_status("Python installations", False, "uv is not installed")
        logger.warning("Cannot check Python installations: uv is not installed")
        return False
    
    try:
        result = subprocess.run(
            ["uv", "python", "list"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            python_versions = [line.strip() for line in result.stdout.splitlines() if line.strip()]
            
            if python_versions:
                print_status(f"Python installations: {len(python_versions)} version(s) available", True)
                logger.info(f"Python installations: {len(python_versions)} version(s) available")
                for version in python_versions:
                    print(f"  - {version}")
                return True
            else:
                print_status("Python installations", False, "No Python versions installed with uv")
                logger.warning("No Python versions installed with uv")
                
                # Ask if the user wants to install Python
                print("\nWould you like to install the latest Python version? (y/n)")
                response = input("> ").lower()
                if response == 'y':
                    print("\nInstalling the latest Python version...")
                    result = run_command("ag uv install-python", capture_output=False)
                    if result is not None:
                        print_status("Python installation", True)
                        logger.info("Python installed successfully")
                        return True
                    else:
                        print_status("Python installation", False, "Failed to install Python")
                        logger.error("Failed to install Python")
                        return False
                
                return False
        else:
            print_status("Python installations", False, "Failed to list Python versions")
            logger.warning("Failed to list Python versions")
            return False
    except Exception as e:
        print_status("Python installations", False, f"Error checking Python installations: {e}")
        logger.error(f"Error checking Python installations: {e}")
        return False

def check_virtual_environments():
    """Check registered virtual environments."""
    if not os.path.exists(REGISTRY_PATH):
        print_status("Virtual environments", False, "Registry file does not exist")
        logger.warning("Cannot check virtual environments: registry file does not exist")
        return False
    
    try:
        with open(REGISTRY_PATH, 'r') as f:
            registry = json.load(f)
        
        venvs = registry.get("virtual_environments", [])
        
        if not venvs:
            print_status("Virtual environments", False, "No virtual environments registered")
            logger.warning("No virtual environments registered")
            return False
        
        valid_count = 0
        invalid_count = 0
        
        print(f"\nRegistered Virtual Environments ({len(venvs)}):")
        
        for venv in venvs:
            path = venv.get("path", "")
            project_name = venv.get("project_name", "Unknown")
            
            if os.path.isdir(path):
                # Check if it's a valid virtual environment
                python_bin = os.path.join(path, "bin", "python")
                if os.path.exists(python_bin) and os.path.isfile(python_bin):
                    try:
                        result = subprocess.run(
                            [python_bin, "--version"],
                            capture_output=True,
                            text=True,
                            timeout=5
                        )
                        if result.returncode == 0:
                            print(f"  \033[92m✓\033[0m {project_name}: {path} (Python {result.stdout.strip()})")
                            valid_count += 1
                            continue
                    except Exception:
                        pass
                
                print(f"  \033[93m!\033[0m {project_name}: {path} (Invalid or corrupted)")
                invalid_count += 1
            else:
                print(f"  \033[91m✗\033[0m {project_name}: {path} (Directory does not exist)")
                invalid_count += 1
        
        print(f"\nValid: {valid_count}, Invalid: {invalid_count}")
        
        if invalid_count > 0:
            print("\nWould you like to clean up invalid virtual environments from the registry? (y/n)")
            response = input("> ").lower()
            if response == 'y':
                print("\nCleaning up invalid virtual environments...")
                result = run_command("ag venv cleanup", capture_output=False)
                if result is not None:
                    print_status("Cleanup", True)
                    logger.info("Cleaned up invalid virtual environments")
                else:
                    print_status("Cleanup", False, "Failed to clean up invalid virtual environments")
                    logger.error("Failed to clean up invalid virtual environments")
        
        return valid_count > 0
    except Exception as e:
        print_status("Virtual environments", False, f"Error checking virtual environments: {e}")
        logger.error(f"Error checking virtual environments: {e}")
        return False

def check_disk_space():
    """Check available disk space."""
    try:
        if sys.platform == "darwin" or sys.platform.startswith("linux"):
            result = run_command("df -h /")
            if result:
                print("\nDisk Space:")
                print(result)
                return True
        elif sys.platform == "win32":
            result = run_command("wmic logicaldisk get deviceid,freespace,size")
            if result:
                print("\nDisk Space:")
                print(result)
                return True
        
        return False
    except Exception as e:
        print(f"Error checking disk space: {e}")
        logger.error(f"Error checking disk space: {e}")
        return False

def apply_environment_fixes():
    """Attempt to fix common environment issues."""
    fixes_applied = []
    
    # Create required directories
    for dir_path, description in REQUIRED_DIRS:
        if not os.path.exists(dir_path):
            try:
                os.makedirs(dir_path, exist_ok=True)
                fixes_applied.append(f"Created directory: {dir_path}")
                logger.info(f"Created directory: {dir_path}")
            except Exception as e:
                logger.error(f"Failed to create directory {dir_path}: {e}")
    
    # Create or repair registry file
    if not os.path.exists(REGISTRY_PATH) or not check_registry_file():
        try:
            # Backup existing file if it exists
            if os.path.exists(REGISTRY_PATH):
                backup_path = f"{REGISTRY_PATH}.bak.{int(time.time())}"
                shutil.copy2(REGISTRY_PATH, backup_path)
                fixes_applied.append(f"Backed up registry file to: {backup_path}")
                logger.info(f"Backed up registry file to: {backup_path}")
            
            # Create new registry file
            registry = {
                "virtual_environments": [],
                "last_updated": datetime.now().isoformat(),
                "registry_version": "1.0.0",
                "metadata": {
                    "description": "Registry of active Python virtual environments managed by uv",
                    "managed_by": "agentic framework",
                    "created_by": "check_environment.py",
                    "note": "This registry was created/repaired by check_environment.py"
                }
            }
            
            with open(REGISTRY_PATH, 'w') as f:
                json.dump(registry, f, indent=2)
            
            fixes_applied.append(f"Created/repaired registry file: {REGISTRY_PATH}")
            logger.info(f"Created/repaired registry file: {REGISTRY_PATH}")
        except Exception as e:
            logger.error(f"Failed to create/repair registry file: {e}")
    
    # Clean up temporary files
    try:
        if os.path.exists(TMP_DIR):
            # Remove files older than 7 days
            cutoff_time = time.time() - (7 * 24 * 60 * 60)
            removed_count = 0
            
            for root, dirs, files in os.walk(TMP_DIR):
                for file in files:
                    file_path = os.path.join(root, file)
                    if os.path.getmtime(file_path) < cutoff_time:
                        try:
                            os.remove(file_path)
                            removed_count += 1
                        except Exception as e:
                            logger.warning(f"Failed to remove temporary file {file_path}: {e}")
            
            if removed_count > 0:
                fixes_applied.append(f"Removed {removed_count} old temporary files")
                logger.info(f"Removed {removed_count} old temporary files")
    except Exception as e:
        logger.error(f"Failed to clean up temporary files: {e}")
    
    return fixes_applied

def run_environment_check(fix_mode=False):
    """Run the environment check."""
    print("\n\033[1mAgentic Environment Check\033[0m\n")
    logger.info("Starting environment check")
    
    if fix_mode:
        print("Running in fix mode. Will attempt to fix common issues.\n")
        logger.info("Running in fix mode")
        
        # Apply fixes
        fixes = apply_environment_fixes()
        if fixes:
            print("\n\033[1mFixes Applied:\033[0m")
            for fix in fixes:
                print(f"- {fix}")
            print()
    
    print("\033[1m1. UV Installation\033[0m")
    uv_ok = check_uv_installation()
    print()
    
    print("\033[1m2. Directory Structure\033[0m")
    dirs_ok = check_directory_structure()
    print()
    
    print("\033[1m3. Registry File\033[0m")
    registry_ok = check_registry_file()
    print()
    
    print("\033[1m4. Python Installations\033[0m")
    python_ok = check_python_installations()
    print()
    
    print("\033[1m5. Virtual Environments\033[0m")
    venvs_ok = check_virtual_environments()
    print()
    
    # Check disk space
    check_disk_space()
    print()
    
    # Summary
    print("\033[1mSummary\033[0m")
    all_ok = uv_ok and dirs_ok and registry_ok and python_ok and venvs_ok
    
    if all_ok:
        print("\033[92mEnvironment is set up correctly according to the agent rules.\033[0m")
        logger.info("Environment check passed")
        return 0
    else:
        print("\033[91mEnvironment has issues that need to be addressed.\033[0m")
        logger.warning("Environment check failed")
        
        if not uv_ok:
            print("- Install uv using 'ag uv install'")
        
        if not dirs_ok:
            print("- Create missing directories using 'ag cleanup check-structure'")
        
        if not registry_ok:
            print("- Create or fix the registry file")
        
        if not python_ok:
            print("- Install Python using 'ag uv install-python'")
        
        if not venvs_ok:
            print("- Clean up invalid virtual environments using 'ag venv cleanup'")
        
        print("\nRun with --fix flag to attempt automatic fixes: ag env fix")
        return 1

def check_environment(args):
    """Function to check the environment setup, called by the ag script."""
    return run_environment_check(False)

def fix_environment(args):
    """Function to fix common environment issues, called by the ag script."""
    return run_environment_check(True)

if __name__ == "__main__":
    # Check if --fix flag is provided
    fix_mode = "--fix" in sys.argv
    sys.exit(run_environment_check(fix_mode))
