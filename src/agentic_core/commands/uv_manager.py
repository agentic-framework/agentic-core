#!/usr/bin/env python3
"""
UV Manager

This module helps with installing and managing uv, the Python package manager
specified in the agent rules. It provides commands to install, update, and
manage Python installations with uv.
"""

import os
import sys
import subprocess
import argparse
import platform
import shutil
import time
import signal
import json
import tempfile
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.expanduser("~/Agentic/logs/uv_manager.log"), mode='a')
    ]
)
logger = logging.getLogger("uv_manager")

# Create logs directory if it doesn't exist
os.makedirs(os.path.expanduser("~/Agentic/logs"), exist_ok=True)

# Constants
DEFAULT_TIMEOUT = 300  # 5 minutes
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds
CACHE_DIR = os.path.expanduser("~/Agentic/cache/uv")
DOWNLOAD_CACHE = os.path.join(CACHE_DIR, "downloads")
INTERRUPTED = False

# Create cache directories
os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(DOWNLOAD_CACHE, exist_ok=True)

def signal_handler(sig, frame):
    """Handle interruption signals gracefully."""
    global INTERRUPTED
    INTERRUPTED = True
    print("\nOperation interrupted. Cleaning up...")
    logger.warning("Operation interrupted by user")

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def run_command(command, capture_output=True, timeout=DEFAULT_TIMEOUT, retries=MAX_RETRIES, check_interruption=True):
    """Run a shell command and return the output with retry logic and timeout."""
    attempt = 0
    
    while attempt < retries:
        if check_interruption and INTERRUPTED:
            logger.warning("Command execution aborted due to interruption")
            return None
            
        try:
            attempt += 1
            logger.debug(f"Running command (attempt {attempt}/{retries}): {command}")
            
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
            if attempt < retries:
                logger.info(f"Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
            else:
                logger.error(f"Command failed after {retries} attempts due to timeout")
                return None
        except subprocess.CalledProcessError as e:
            logger.warning(f"Command failed (attempt {attempt}/{retries}): {command}")
            if capture_output:
                logger.warning(f"Error message: {e.stderr}")
            
            if attempt < retries:
                logger.info(f"Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
            else:
                logger.error(f"Command failed after {retries} attempts")
                return None
        except Exception as e:
            logger.error(f"Unexpected error executing command: {e}")
            return None

def is_uv_installed():
    """Check if uv is installed."""
    return shutil.which("uv") is not None

def get_uv_version():
    """Get the installed uv version."""
    if not is_uv_installed():
        return None
    
    result = run_command("uv --version")
    return result

def is_homebrew_installed():
    """Check if Homebrew is installed."""
    return shutil.which("brew") is not None

def install_uv(args=None):
    """Install uv using the appropriate method for the current OS."""
    if is_uv_installed():
        print(f"uv is already installed (version {get_uv_version()})")
        return True
    
    print("Installing uv...")
    logger.info("Installing uv")
    
    # Check if we're on macOS
    is_macos = platform.system() == "Darwin"
    
    if is_macos:
        print("Detected macOS. Attempting to install uv using direct download...")
        logger.info("Attempting to install uv using direct download")
        
        # Create directories for installation
        home_dir = Path.home()
        bin_dir = home_dir / ".local" / "bin"
        os.makedirs(bin_dir, exist_ok=True)
        
        # Determine architecture
        arch = platform.machine()
        if arch == "x86_64":
            arch_name = "x64"
        elif arch == "arm64":
            arch_name = "aarch64"
        else:
            print(f"Unsupported architecture: {arch}. Falling back to official installer.")
            logger.warning(f"Unsupported architecture: {arch}. Falling back to official installer")
            arch_name = None
        
        if arch_name:
            # Download pre-compiled binary
            uv_url = f"https://github.com/astral-sh/uv/releases/latest/download/uv-{arch_name}-apple-darwin.tar.gz"
            temp_dir = tempfile.mkdtemp(prefix="uv_install_", dir=CACHE_DIR)
            tar_path = os.path.join(temp_dir, "uv.tar.gz")
            
            try:
                # Download the tarball
                download_cmd = f"curl -sSL {uv_url} -o {tar_path}"
                download_result = run_command(download_cmd, capture_output=True)
                
                if download_result is None:
                    print("Failed to download uv binary.")
                    logger.error("Failed to download uv binary")
                else:
                    # Extract the binary
                    extract_cmd = f"tar -xzf {tar_path} -C {temp_dir}"
                    extract_result = run_command(extract_cmd, capture_output=True)
                    
                    if extract_result is None:
                        print("Failed to extract uv binary.")
                        logger.error("Failed to extract uv binary")
                    else:
                        # Copy the binary to the bin directory
                        uv_bin_path = os.path.join(temp_dir, "uv")
                        if os.path.exists(uv_bin_path):
                            dest_path = os.path.join(bin_dir, "uv")
                            shutil.copy2(uv_bin_path, dest_path)
                            os.chmod(dest_path, 0o755)
                            
                            print(f"uv binary installed to {dest_path}")
                            logger.info(f"uv binary installed to {dest_path}")
                            
                            # Add to PATH if not already there
                            if not is_uv_installed():
                                print(f"\nuv was installed but is not in your PATH.")
                                print(f"Add this directory to your PATH: {bin_dir}")
                                print(f"Run: export PATH=\"{bin_dir}:$PATH\"")
                                logger.warning("uv installed but not in PATH")
                                
                                # Try to add to PATH temporarily for this session
                                os.environ["PATH"] = f"{bin_dir}:{os.environ.get('PATH', '')}"
                                
                                if is_uv_installed():
                                    version = get_uv_version()
                                    print(f"uv is now available in this session (version {version})")
                                    logger.info(f"uv is now available in this session (version {version})")
                                    return True
                            else:
                                version = get_uv_version()
                                print(f"uv installed successfully (version {version})")
                                logger.info(f"uv installed successfully (version {version})")
                                return True
            finally:
                # Clean up the temporary directory
                try:
                    shutil.rmtree(temp_dir)
                except Exception as e:
                    logger.warning(f"Failed to clean up temporary directory: {e}")
        
        # If we get here, direct download failed or was skipped
        print("Direct download method failed. Trying Homebrew if available...")
        logger.warning("Direct download method failed. Trying Homebrew if available...")
        
        # Check if Homebrew is installed
        has_homebrew = is_homebrew_installed()
        if has_homebrew:
            print("Attempting to install uv using Homebrew...")
            logger.info("Attempting to install uv using Homebrew")
            
            # Try to install uv using Homebrew with increased timeout
            brew_cmd = "brew install uv"
            brew_result = run_command(brew_cmd, capture_output=False, timeout=600)  # 10 minutes timeout
            
            if brew_result is not None:
                # Check if uv is now in the PATH
                if is_uv_installed():
                    version = get_uv_version()
                    print(f"uv installed successfully via Homebrew (version {version})")
                    logger.info(f"uv installed successfully via Homebrew (version {version})")
                    return True
                else:
                    print("Homebrew installation completed but uv is not in PATH.")
                    logger.warning("Homebrew installation completed but uv is not in PATH")
            else:
                print("Failed to install uv via Homebrew. Falling back to official installer.")
                logger.warning("Failed to install uv via Homebrew. Falling back to official installer")
    
    # Use a different approach - download the installer to a temp file and execute it
    temp_dir = tempfile.mkdtemp(prefix="uv_install_", dir=CACHE_DIR)
    installer_path = os.path.join(temp_dir, "uv-installer.sh")
    
    try:
        # Download the installer
        download_cmd = f"curl -sSf https://github.com/astral-sh/uv/releases/latest/download/uv-installer.sh -o {installer_path}"
        download_result = run_command(download_cmd, capture_output=True)
        
        if download_result is None:
            print("Failed to download the uv installer.")
            logger.error("Failed to download the uv installer")
            return False
        
        # Make the installer executable
        os.chmod(installer_path, 0o755)
        
        # Execute the installer with verbose output
        install_cmd = f"bash -x {installer_path}"
        install_output = run_command(install_cmd, capture_output=True)
        
        if install_output:
            print("Installation output:")
            print(install_output)
            logger.info(f"Installation output: {install_output}")
            
        # Consider the installation successful if we got output
        result = install_output is not None
    finally:
        # Clean up the temporary directory
        try:
            shutil.rmtree(temp_dir)
        except Exception as e:
            logger.warning(f"Failed to clean up temporary directory: {e}")
    
    if result is None:
        print("Failed to install uv.")
        logger.error("Failed to install uv")
        return False
    
    # Check if uv is now in the PATH
    if not is_uv_installed():
        print("\nuv was installed but is not in your PATH.")
        print("You may need to restart your terminal or add the installation directory to your PATH.")
        logger.warning("uv installed but not in PATH")
        
        # Try to find the installation directory
        home_dir = Path.home()
        possible_paths = [
            home_dir / ".cargo" / "bin",
            home_dir / ".local" / "bin"
        ]
        
        for path in possible_paths:
            if (path / "uv").exists():
                print(f"\nFound uv at: {path / 'uv'}")
                print(f"Add this directory to your PATH: {path}")
                logger.info(f"Found uv at: {path / 'uv'}")
                break
        
        return False
    
    version = get_uv_version()
    print(f"uv installed successfully (version {version})")
    logger.info(f"uv installed successfully (version {version})")
    return True

def update_uv(args=None):
    """Update uv to the latest version."""
    if not is_uv_installed():
        print("uv is not installed. Installing...")
        logger.info("uv not installed, installing instead of updating")
        return install_uv()
    
    current_version = get_uv_version()
    print(f"Current uv version: {current_version}")
    print("Updating uv...")
    logger.info(f"Updating uv from version {current_version}")
    
    # Check if we're on macOS
    is_macos = platform.system() == "Darwin"
    
    if is_macos:
        print("Detected macOS. Attempting to update uv using direct download...")
        logger.info("Attempting to update uv using direct download")
        
        # Determine architecture
        arch = platform.machine()
        if arch == "x86_64":
            arch_name = "x64"
        elif arch == "arm64":
            arch_name = "aarch64"
        else:
            print(f"Unsupported architecture: {arch}. Falling back to official installer.")
            logger.warning(f"Unsupported architecture: {arch}. Falling back to official installer")
            arch_name = None
        
        if arch_name:
            # Find the current uv binary path
            uv_path = shutil.which("uv")
            if uv_path:
                uv_dir = os.path.dirname(uv_path)
                
                # Download pre-compiled binary
                uv_url = f"https://github.com/astral-sh/uv/releases/latest/download/uv-{arch_name}-apple-darwin.tar.gz"
                temp_dir = tempfile.mkdtemp(prefix="uv_update_", dir=CACHE_DIR)
                tar_path = os.path.join(temp_dir, "uv.tar.gz")
                
                try:
                    # Download the tarball
                    download_cmd = f"curl -sSL {uv_url} -o {tar_path}"
                    download_result = run_command(download_cmd, capture_output=True)
                    
                    if download_result is None:
                        print("Failed to download uv binary.")
                        logger.error("Failed to download uv binary")
                    else:
                        # Extract the binary
                        extract_cmd = f"tar -xzf {tar_path} -C {temp_dir}"
                        extract_result = run_command(extract_cmd, capture_output=True)
                        
                        if extract_result is None:
                            print("Failed to extract uv binary.")
                            logger.error("Failed to extract uv binary")
                        else:
                            # Copy the binary to the existing location
                            uv_bin_path = os.path.join(temp_dir, "uv")
                            if os.path.exists(uv_bin_path):
                                # Backup the old binary
                                backup_path = f"{uv_path}.bak"
                                try:
                                    shutil.copy2(uv_path, backup_path)
                                    logger.info(f"Backed up old uv binary to {backup_path}")
                                except Exception as e:
                                    logger.warning(f"Failed to backup old uv binary: {e}")
                                
                                # Replace with the new binary
                                try:
                                    shutil.copy2(uv_bin_path, uv_path)
                                    os.chmod(uv_path, 0o755)
                                    
                                    new_version = get_uv_version()
                                    if new_version == current_version:
                                        print("uv is already at the latest version.")
                                        logger.info("uv is already at the latest version")
                                    else:
                                        print(f"uv updated successfully via direct download: {current_version} -> {new_version}")
                                        logger.info(f"uv updated successfully via direct download: {current_version} -> {new_version}")
                                    return True
                                except Exception as e:
                                    logger.error(f"Failed to replace uv binary: {e}")
                                    print(f"Failed to replace uv binary: {e}")
                                    
                                    # Try to restore backup
                                    try:
                                        if os.path.exists(backup_path):
                                            shutil.copy2(backup_path, uv_path)
                                            logger.info("Restored backup of uv binary")
                                            print("Restored backup of uv binary")
                                    except Exception as e:
                                        logger.error(f"Failed to restore backup: {e}")
                finally:
                    # Clean up the temporary directory
                    try:
                        shutil.rmtree(temp_dir)
                    except Exception as e:
                        logger.warning(f"Failed to clean up temporary directory: {e}")
        
        # If we get here, direct download failed or was skipped
        print("Direct download method failed. Trying Homebrew if available...")
        logger.warning("Direct download method failed. Trying Homebrew if available...")
        
        # Check if Homebrew is installed
        has_homebrew = is_homebrew_installed()
        if has_homebrew:
            print("Attempting to update uv using Homebrew...")
            logger.info("Attempting to update uv using Homebrew")
            
            # Try to update uv using Homebrew with increased timeout
            brew_cmd = "brew upgrade uv || brew install uv"
            brew_result = run_command(brew_cmd, capture_output=False, timeout=600)  # 10 minutes timeout
            
            if brew_result is not None:
                # Check if uv is now in the PATH
                if is_uv_installed():
                    new_version = get_uv_version()
                    if new_version == current_version:
                        print("uv is already at the latest version.")
                        logger.info("uv is already at the latest version")
                    else:
                        print(f"uv updated successfully via Homebrew: {current_version} -> {new_version}")
                        logger.info(f"uv updated successfully via Homebrew: {current_version} -> {new_version}")
                    return True
                else:
                    print("Homebrew update completed but uv is not in PATH.")
                    logger.warning("Homebrew update completed but uv is not in PATH")
            else:
                print("Failed to update uv via Homebrew. Falling back to official installer.")
                logger.warning("Failed to update uv via Homebrew. Falling back to official installer")
    
    # Fall back to the official installer method
    print("Using official installer script for update...")
    logger.info("Using official installer script for update")
    
    # Use the official installation script to update
    result = run_command("curl -sSf https://github.com/astral-sh/uv/releases/latest/download/uv-installer.sh | sh", capture_output=False)
    
    if result is None:
        print("Failed to update uv.")
        logger.error("Failed to update uv")
        return False
    
    new_version = get_uv_version()
    if new_version == current_version:
        print("uv is already at the latest version.")
        logger.info("uv is already at the latest version")
    else:
        print(f"uv updated successfully: {current_version} -> {new_version}")
        logger.info(f"uv updated successfully: {current_version} -> {new_version}")
    
    return True

def list_python_versions(args=None):
    """List Python versions available through uv."""
    if not is_uv_installed():
        print("uv is not installed. Please install it first.")
        logger.warning("Cannot list Python versions: uv is not installed")
        return False
    
    print("Available Python versions:")
    run_command("uv python list", capture_output=False)
    logger.info("Listed available Python versions")
    return True

def install_python(args=None):
    """Install a Python version using uv."""
    if not is_uv_installed():
        print("uv is not installed. Please install it first.")
        logger.warning("Cannot install Python: uv is not installed")
        return False
    
    # Extract version from args if provided
    version = None
    if args and len(args) > 0:
        version = args[0]
    
    if version:
        print(f"Installing Python {version}...")
        logger.info(f"Installing Python {version}")
        command = f"uv python install {version}"
    else:
        print("Installing the latest Python version...")
        logger.info("Installing the latest Python version")
        command = "uv python install"
    
    result = run_command(command, capture_output=False)
    
    if result is None:
        print("Failed to install Python.")
        logger.error(f"Failed to install Python {version if version else 'latest'}")
        return False
    
    # Verify the installation
    if version:
        verify_cmd = f"uv python list | grep -q {version}"
    else:
        verify_cmd = "uv python list | head -1"
    
    verify_result = run_command(verify_cmd)
    if verify_result is None:
        print("Python installation could not be verified. Please check manually.")
        logger.warning("Python installation could not be verified")
    else:
        print("Python installed and verified successfully.")
        logger.info(f"Python {version if version else 'latest'} installed and verified successfully")
    
    return True

def create_venv(path, python_version=None, timeout=DEFAULT_TIMEOUT, retries=MAX_RETRIES):
    """Create a virtual environment using uv with enhanced error handling and verification."""
    if not is_uv_installed():
        print("uv is not installed. Please install it first.")
        logger.warning("Cannot create venv: uv is not installed")
        return False
    
    # Expand the path
    path = os.path.abspath(os.path.expanduser(path))
    
    # Create the command
    command = f"uv venv {path}"
    if python_version:
        command += f" --python {python_version}"
    
    print(f"Creating virtual environment at {path}...")
    logger.info(f"Creating virtual environment at {path} with Python {python_version if python_version else 'default'}")
    
    # Check if the directory already exists
    if os.path.exists(path):
        print(f"Warning: Directory {path} already exists. It will be used if it's a valid virtual environment or overwritten.")
        logger.warning(f"Directory {path} already exists")
    
    # Run the command with increased timeout and retries
    result = run_command(command, capture_output=False, timeout=timeout, retries=retries)
    
    if result is None:
        print("Failed to create virtual environment.")
        logger.error(f"Failed to create virtual environment at {path}")
        
        # Check if the directory was partially created
        if os.path.exists(path):
            print("A partial virtual environment directory exists. Attempting to verify...")
            logger.info("Attempting to verify partial virtual environment")
            if verify_venv(path):
                print("The existing virtual environment appears to be valid.")
                logger.info("Existing virtual environment is valid")
                print(f"Activate with: source {path}/bin/activate")
                return True
            else:
                print("The existing virtual environment is invalid or incomplete.")
                logger.warning("Existing virtual environment is invalid or incomplete")
                return False
        return False
    
    # Verify the virtual environment
    if verify_venv(path):
        print(f"Virtual environment created and verified successfully at {path}")
        print(f"Activate with: source {path}/bin/activate")
        logger.info(f"Virtual environment created and verified successfully at {path}")
        return True
    else:
        print("Virtual environment creation failed verification.")
        logger.error("Virtual environment creation failed verification")
        return False

def verify_venv(path):
    """Verify that a virtual environment is valid and usable."""
    # Check for essential files/directories
    python_bin = os.path.join(path, "bin", "python")
    pip_bin = os.path.join(path, "bin", "pip")
    
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

def install_dependencies(venv_path, requirements_file=None, package_list=None, dev=False, parallel=True):
    """Install dependencies in a virtual environment with parallel option."""
    if not verify_venv(venv_path):
        print(f"Cannot install dependencies: {venv_path} is not a valid virtual environment")
        logger.error(f"Cannot install dependencies: {venv_path} is not a valid virtual environment")
        return False
    
    python_bin = os.path.join(venv_path, "bin", "python")
    
    # Determine what to install
    if requirements_file:
        print(f"Installing dependencies from {requirements_file}...")
        logger.info(f"Installing dependencies from {requirements_file}")
        
        # Use uv pip install with the requirements file
        command = f"{python_bin} -m uv pip install -r {requirements_file}"
        if dev:
            command += " --dev"
        if parallel:
            command += " --parallel"
    elif package_list:
        packages = " ".join(package_list)
        print(f"Installing packages: {packages}")
        logger.info(f"Installing packages: {packages}")
        
        # Use uv pip install with the package list
        command = f"{python_bin} -m uv pip install {packages}"
        if parallel:
            command += " --parallel"
    else:
        print("No dependencies specified")
        logger.warning("No dependencies specified for installation")
        return False
    
    result = run_command(command, capture_output=False, timeout=600)  # 10 minutes timeout for installations
    
    if result is None:
        print("Failed to install dependencies.")
        logger.error("Failed to install dependencies")
        return False
    
    print("Dependencies installed successfully.")
    logger.info("Dependencies installed successfully")
    return True

def install_editable(venv_path, project_path, parallel=True):
    """Install a project in editable mode."""
    if not verify_venv(venv_path):
        print(f"Cannot install project: {venv_path} is not a valid virtual environment")
        logger.error(f"Cannot install project: {venv_path} is not a valid virtual environment")
        return False
    
    python_bin = os.path.join(venv_path, "bin", "python")
    
    print(f"Installing project {project_path} in editable mode...")
    logger.info(f"Installing project {project_path} in editable mode")
    
    command = f"{python_bin} -m uv pip install -e {project_path}"
    if parallel:
        command += " --parallel"
    
    result = run_command(command, capture_output=False, timeout=600)  # 10 minutes timeout
    
    if result is None:
        print("Failed to install project in editable mode.")
        logger.error("Failed to install project in editable mode")
        return False
    
    print("Project installed successfully in editable mode.")
    logger.info("Project installed successfully in editable mode")
    return True

def show_uv_info():
    """Show information about uv."""
    if not is_uv_installed():
        print("uv is not installed. Please install it first.")
        logger.warning("Cannot show uv info: uv is not installed")
        return False
    
    print("UV Information:")
    version = get_uv_version()
    print(f"Version: {version}")
    logger.info(f"UV version: {version}")
    
    print("\nPython Versions:")
    run_command("uv python list", capture_output=False)
    
    print("\nCache Information:")
    cache_size = get_directory_size(CACHE_DIR)
    print(f"Cache directory: {CACHE_DIR}")
    print(f"Cache size: {format_size(cache_size)}")
    logger.info(f"Cache size: {format_size(cache_size)}")
    
    print("\nFor more information, visit: https://github.com/astral-sh/uv")
    return True

def get_directory_size(path):
    """Get the size of a directory in bytes."""
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.exists(fp):
                total_size += os.path.getsize(fp)
    return total_size

def format_size(size_bytes):
    """Format a size in bytes to a human-readable string."""
    if size_bytes < 1024:
        return f"{size_bytes} bytes"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"

def clean_cache(args=None):
    """Clean the uv cache."""
    if not os.path.exists(CACHE_DIR):
        print(f"Cache directory {CACHE_DIR} does not exist.")
        return True
    
    before_size = get_directory_size(CACHE_DIR)
    print(f"Current cache size: {format_size(before_size)}")
    
    # Extract older_than_days from args if provided
    older_than_days = None
    if args:
        for i in range(len(args)):
            if args[i] == "--older-than" and i + 1 < len(args):
                try:
                    older_than_days = int(args[i + 1])
                    break
                except ValueError:
                    print(f"Invalid value for --older-than: {args[i + 1]}")
                    logger.warning(f"Invalid value for --older-than: {args[i + 1]}")
    
    if older_than_days:
        print(f"Cleaning cache files older than {older_than_days} days...")
        cutoff_time = time.time() - (older_than_days * 24 * 60 * 60)
        
        for dirpath, dirnames, filenames in os.walk(CACHE_DIR):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if os.path.exists(fp) and os.path.getmtime(fp) < cutoff_time:
                    try:
                        os.remove(fp)
                        logger.debug(f"Removed old cache file: {fp}")
                    except Exception as e:
                        logger.warning(f"Failed to remove cache file {fp}: {e}")
    else:
        print("Cleaning all cache files...")
        try:
            shutil.rmtree(CACHE_DIR)
            os.makedirs(CACHE_DIR, exist_ok=True)
            os.makedirs(DOWNLOAD_CACHE, exist_ok=True)
            logger.info("Cleared all cache files")
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            print(f"Failed to clear cache: {e}")
            return False
    
    after_size = get_directory_size(CACHE_DIR)
    freed_space = before_size - after_size
    print(f"Freed {format_size(freed_space)} of space.")
    print(f"New cache size: {format_size(after_size)}")
    logger.info(f"Cache cleanup freed {format_size(freed_space)} of space")
    
    return True

# Functions for the ag CLI

def install_uv_cli(args):
    """Install uv, called by the ag script."""
    return install_uv(args)

def update_uv_cli(args):
    """Update uv, called by the ag script."""
    return update_uv(args)

def list_python_versions_cli(args):
    """List available Python versions, called by the ag script."""
    return list_python_versions(args)

def install_python_cli(args):
    """Install a Python version, called by the ag script."""
    return install_python(args)

def clean_cache_cli(args):
    """Clean the uv cache, called by the ag script."""
    return clean_cache(args)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Manage uv and Python installations")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Install command
    subparsers.add_parser("install", help="Install uv")
    
    # Update command
    subparsers.add_parser("update", help="Update uv to the latest version")
    
    # List Python versions command
    subparsers.add_parser("list-python", help="List available Python versions")
    
    # Install Python command
    install_python_parser = subparsers.add_parser("install-python", help="Install a Python version")
    install_python_parser.add_argument("version", nargs="?", help="Python version to install (e.g., 3.11)")
    
    # Create virtual environment command
    create_venv_parser = subparsers.add_parser("create-venv", help="Create a virtual environment")
    create_venv_parser.add_argument("path", help="Path for the virtual environment")
    create_venv_parser.add_argument("--python", help="Python version to use")
    create_venv_parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, 
                                   help=f"Timeout in seconds (default: {DEFAULT_TIMEOUT})")
    create_venv_parser.add_argument("--retries", type=int, default=MAX_RETRIES, 
                                   help=f"Number of retry attempts (default: {MAX_RETRIES})")
    
    # Install dependencies command
    install_deps_parser = subparsers.add_parser("install-deps", help="Install dependencies in a virtual environment")
    install_deps_parser.add_argument("venv_path", help="Path to the virtual environment")
    install_deps_parser.add_argument("--requirements", help="Path to requirements.txt file")
    install_deps_parser.add_argument("--packages", nargs="+", help="List of packages to install")
    install_deps_parser.add_argument("--dev", action="store_true", help="Install development dependencies")
    install_deps_parser.add_argument("--no-parallel", dest="parallel", action="store_false", 
                                    help="Disable parallel installation")
    
    # Install project in editable mode command
    install_editable_parser = subparsers.add_parser("install-editable", help="Install a project in editable mode")
    install_editable_parser.add_argument("venv_path", help="Path to the virtual environment")
    install_editable_parser.add_argument("project_path", help="Path to the project")
    install_editable_parser.add_argument("--no-parallel", dest="parallel", action="store_false", 
                                        help="Disable parallel installation")
    
    # Info command
    subparsers.add_parser("info", help="Show information about uv")
    
    # Clean cache command
    clean_cache_parser = subparsers.add_parser("clean-cache", help="Clean the uv cache")
    clean_cache_parser.add_argument("--older-than", type=int, help="Clean files older than specified days")
    
    args = parser.parse_args()
    
    if args.command == "install":
        install_uv()
    elif args.command == "update":
        update_uv()
    elif args.command == "list-python":
        list_python_versions()
    elif args.command == "install-python":
        install_python(args.version)
    elif args.command == "create-venv":
        create_venv(args.path, args.python, args.timeout, args.retries)
    elif args.command == "install-deps":
        install_dependencies(args.venv_path, args.requirements, args.packages, args.dev, args.parallel)
    elif args.command == "install-editable":
        install_editable(args.venv_path, args.project_path, args.parallel)
    elif args.command == "info":
        show_uv_info()
    elif args.command == "clean-cache":
        clean_cache(args.older_than)
    else:
        if is_uv_installed():
            print(f"uv is installed (version {get_uv_version()})")
            parser.print_help()
        else:
            print("uv is not installed. Run 'ag uv install' to install it.")
            parser.print_help()
