#!/usr/bin/env python3
"""
Cleanup Manager

This module helps with cleaning up temporary files and managing the directory structure.
It provides commands to clean up temporary files, check for orphaned virtual environments,
and maintain the directory structure according to the agent rules.
"""

import os
import sys
import argparse
import json
import shutil
import time
from datetime import datetime, timedelta
from pathlib import Path

# Import the config module from agentic_core
from agentic_core.commands import config

# Base directories
AGENTIC_DIR = config.get_path("agentic_root") or os.path.expanduser("~/Agentic")
TMP_DIR = config.get_path("tmp_dir") or os.path.join(AGENTIC_DIR, "tmp")
PROJECTS_DIR = config.get_path("projects_dir") or os.path.join(AGENTIC_DIR, "projects")
SHARED_DIR = config.get_path("shared_dir") or os.path.join(AGENTIC_DIR, "shared")
REGISTRY_PATH = config.get_path("registry_file") or os.path.join(AGENTIC_DIR, "venv_registry.json")

def load_registry():
    """Load the virtual environment registry."""
    try:
        with open(REGISTRY_PATH, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: Registry file not found at {REGISTRY_PATH}")
        return {"virtual_environments": []}
    except json.JSONDecodeError:
        print(f"Warning: Registry file is not valid JSON: {REGISTRY_PATH}")
        return {"virtual_environments": []}

def save_registry(registry):
    """Save the virtual environment registry."""
    registry["last_updated"] = datetime.now().isoformat()
    with open(REGISTRY_PATH, 'w') as f:
        json.dump(registry, f, indent=2)

def cleanup_tmp_files(days=7, dry_run=False):
    """Clean up files in the tmp directory older than the specified number of days."""
    if not os.path.exists(TMP_DIR):
        print(f"Temporary directory does not exist: {TMP_DIR}")
        return
    
    print(f"Cleaning up files in {TMP_DIR} older than {days} days...")
    
    cutoff_time = time.time() - (days * 86400)  # Convert days to seconds
    total_size = 0
    file_count = 0
    
    for root, dirs, files in os.walk(TMP_DIR):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                file_stat = os.stat(file_path)
                if file_stat.st_mtime < cutoff_time:
                    file_size = file_stat.st_size
                    total_size += file_size
                    file_count += 1
                    
                    if dry_run:
                        print(f"Would delete: {file_path} ({file_size / 1024:.1f} KB)")
                    else:
                        print(f"Deleting: {file_path} ({file_size / 1024:.1f} KB)")
                        os.remove(file_path)
            except Exception as e:
                print(f"Error processing {file_path}: {e}")
    
    # Clean up empty directories
    if not dry_run:
        for root, dirs, files in os.walk(TMP_DIR, topdown=False):
            for dir in dirs:
                dir_path = os.path.join(root, dir)
                try:
                    if not os.listdir(dir_path):  # Check if directory is empty
                        print(f"Removing empty directory: {dir_path}")
                        os.rmdir(dir_path)
                except Exception as e:
                    print(f"Error removing directory {dir_path}: {e}")
    
    print(f"\nSummary:")
    if dry_run:
        print(f"Would delete {file_count} files ({total_size / 1024 / 1024:.2f} MB)")
    else:
        print(f"Deleted {file_count} files ({total_size / 1024 / 1024:.2f} MB)")

def check_orphaned_venvs(remove=False):
    """Check for orphaned virtual environments (not in the registry)."""
    registry = load_registry()
    registered_venvs = {venv["path"] for venv in registry["virtual_environments"]}
    
    # Find all .venv directories in the projects directory
    orphaned_venvs = []
    total_size = 0
    
    for root, dirs, files in os.walk(PROJECTS_DIR):
        for dir in dirs:
            if dir == ".venv":
                venv_path = os.path.join(root, dir)
                if venv_path not in registered_venvs:
                    # Calculate size
                    size = get_directory_size(venv_path)
                    total_size += size
                    orphaned_venvs.append((venv_path, size))
    
    if not orphaned_venvs:
        print("No orphaned virtual environments found.")
        return
    
    print(f"Found {len(orphaned_venvs)} orphaned virtual environments:")
    for venv_path, size in orphaned_venvs:
        print(f"  {venv_path} ({size / 1024 / 1024:.2f} MB)")
    
    print(f"\nTotal size: {total_size / 1024 / 1024:.2f} MB")
    
    if remove:
        print("\nRemoving orphaned virtual environments...")
        for venv_path, _ in orphaned_venvs:
            try:
                print(f"Removing: {venv_path}")
                shutil.rmtree(venv_path)
            except Exception as e:
                print(f"Error removing {venv_path}: {e}")
        print("Removal complete.")

def get_directory_size(path):
    """Calculate the total size of a directory in bytes."""
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            try:
                total_size += os.path.getsize(fp)
            except OSError:
                pass
    return total_size

def check_directory_structure():
    """Check if the required directory structure exists."""
    directories = [
        (AGENTIC_DIR, "Agentic root directory"),
        (TMP_DIR, "Temporary files directory"),
        (PROJECTS_DIR, "Projects directory"),
        (SHARED_DIR, "Shared resources directory")
    ]
    
    all_exist = True
    
    print("Checking directory structure...")
    for dir_path, description in directories:
        if os.path.exists(dir_path):
            print(f"✓ {description} exists: {dir_path}")
        else:
            print(f"✗ {description} does not exist: {dir_path}")
            all_exist = False
    
    if not all_exist:
        print("\nSome directories are missing. Create them? (y/n)")
        choice = input().lower()
        if choice == 'y':
            for dir_path, description in directories:
                if not os.path.exists(dir_path):
                    os.makedirs(dir_path, exist_ok=True)
                    print(f"Created {description}: {dir_path}")
            print("Directory structure created successfully.")
    
    # Check registry file
    if os.path.exists(REGISTRY_PATH):
        print(f"✓ Virtual environment registry exists: {REGISTRY_PATH}")
    else:
        print(f"✗ Virtual environment registry does not exist: {REGISTRY_PATH}")
        print("Creating registry file...")
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
        print("Registry file created successfully.")

def analyze_disk_usage():
    """Analyze disk usage of the Agentic directories."""
    directories = [
        (TMP_DIR, "Temporary files"),
        (PROJECTS_DIR, "Projects"),
        (SHARED_DIR, "Shared resources")
    ]
    
    print("Analyzing disk usage...")
    
    for dir_path, description in directories:
        if os.path.exists(dir_path):
            size = get_directory_size(dir_path)
            print(f"{description}: {size / 1024 / 1024:.2f} MB")
            
            # If it's the projects directory, break down by project
            if dir_path == PROJECTS_DIR and os.path.exists(dir_path):
                print("\nProject breakdown:")
                for project in os.listdir(dir_path):
                    project_path = os.path.join(dir_path, project)
                    if os.path.isdir(project_path):
                        project_size = get_directory_size(project_path)
                        print(f"  {project}: {project_size / 1024 / 1024:.2f} MB")
        else:
            print(f"{description}: Directory does not exist")

# Functions for the ag CLI

def cleanup_tmp(args):
    """Clean up temporary files, called by the ag script."""
    days = 7  # Default value
    dry_run = False
    
    for i in range(len(args)):
        if args[i] == "--days" and i + 1 < len(args):
            try:
                days = int(args[i + 1])
            except ValueError:
                print(f"Invalid value for --days: {args[i + 1]}")
                return 1
        elif args[i] == "--dry-run":
            dry_run = True
    
    cleanup_tmp_files(days, dry_run)
    return 0

def check_orphaned_venvs_cli(args):
    """Check for orphaned virtual environments, called by the ag script."""
    remove = "--remove" in args
    check_orphaned_venvs(remove)
    return 0

def check_structure(args):
    """Check if the required directory structure exists, called by the ag script."""
    check_directory_structure()
    return 0

def disk_usage(args):
    """Analyze disk usage of the Agentic directories, called by the ag script."""
    analyze_disk_usage()
    return 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Manage cleanup and directory structure")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Cleanup tmp files command
    cleanup_parser = subparsers.add_parser("cleanup-tmp", help="Clean up temporary files")
    cleanup_parser.add_argument("--days", type=int, default=7, help="Delete files older than this many days")
    cleanup_parser.add_argument("--dry-run", action="store_true", help="Show what would be deleted without actually deleting")
    
    # Check orphaned venvs command
    orphaned_parser = subparsers.add_parser("check-orphaned-venvs", help="Check for orphaned virtual environments")
    orphaned_parser.add_argument("--remove", action="store_true", help="Remove orphaned virtual environments")
    
    # Check directory structure command
    subparsers.add_parser("check-structure", help="Check if the required directory structure exists")
    
    # Analyze disk usage command
    subparsers.add_parser("disk-usage", help="Analyze disk usage of the Agentic directories")
    
    args = parser.parse_args()
    
    if args.command == "cleanup-tmp":
        cleanup_tmp_files(args.days, args.dry_run)
    elif args.command == "check-orphaned-venvs":
        check_orphaned_venvs(args.remove)
    elif args.command == "check-structure":
        check_directory_structure()
    elif args.command == "disk-usage":
        analyze_disk_usage()
    else:
        parser.print_help()
