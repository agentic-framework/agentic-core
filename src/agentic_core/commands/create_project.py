#!/usr/bin/env python3
"""
Project Creator

This module creates a new project with the standard structure defined in the agent rules.
It sets up a virtual environment, initializes a git repository, and creates basic files.
"""

import os
import sys
import argparse
import subprocess
import json
from datetime import datetime
import shutil

# Import the config module from agentic_core
from agentic_core.commands import config

# Base directory for projects
PROJECTS_DIR = config.get_path("projects_dir") or os.path.expanduser("~/Agentic/projects")

def run_command(command, cwd=None):
    """Run a shell command and return the output."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            text=True,
            capture_output=True,
            cwd=cwd
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {command}")
        print(f"Error message: {e.stderr}")
        return None

def create_directory_structure(project_path):
    """Create the standard directory structure for a project."""
    directories = [
        "src",
        "tests",
        "docs",
        "data",
        "notebooks"
    ]
    
    for directory in directories:
        os.makedirs(os.path.join(project_path, directory), exist_ok=True)
        # Create an empty __init__.py file in Python directories
        if directory in ["src", "tests"]:
            with open(os.path.join(project_path, directory, "__init__.py"), "w") as f:
                f.write("# This file is intentionally left empty to mark this directory as a Python package.\n")
    
    print(f"Created directory structure in {project_path}")

def create_readme(project_path, project_name, description):
    """Create a README.md file for the project."""
    readme_content = f"""# {project_name}

{description}

## Overview

This project follows the standard structure defined in the Agentic framework.

## Directory Structure

```
{project_name}/
├── .venv/                 # Virtual environment (not in version control)
├── src/                   # Source code
├── tests/                 # Test files
├── docs/                  # Documentation
├── data/                  # Data files
├── notebooks/             # Jupyter notebooks
├── .gitignore             # Git ignore file
├── README.md              # This file
├── LICENSE                # License file
└── pyproject.toml         # Project configuration
```

## Getting Started

1. Activate the virtual environment:
   ```bash
   source .venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   uv pip install -e .
   ```

3. Run tests:
   ```bash
   pytest
   ```

## License

See the [LICENSE](LICENSE) file for details.
"""
    
    with open(os.path.join(project_path, "README.md"), "w") as f:
        f.write(readme_content)
    
    print(f"Created README.md in {project_path}")

def create_license(project_path, license_type="MIT"):
    """Create a LICENSE file for the project."""
    current_year = datetime.now().year
    
    if license_type.upper() == "MIT":
        license_content = f"""MIT License

Copyright (c) {current_year} 

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
    else:
        # Default to a placeholder for other license types
        license_content = f"""Copyright (c) {current_year}

This project is licensed under the {license_type} License.
Please replace this file with the appropriate license text.
"""
    
    with open(os.path.join(project_path, "LICENSE"), "w") as f:
        f.write(license_content)
    
    print(f"Created LICENSE file in {project_path}")

def create_pyproject_toml(project_path, project_name, package_name, description):
    """Create a pyproject.toml file for the project."""
    pyproject_content = f"""[build-system]
requires = ["setuptools>=42", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "{package_name}"
version = "0.1.0"
description = "{description}"
readme = "README.md"
requires-python = ">=3.8"
license = {{file = "LICENSE"}}
authors = [
    {{name = "Author Name", email = "author@example.com"}}
]
classifiers = [
    "Programming Language :: Python :: 3",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
]

[project.urls]
"Homepage" = "https://github.com/username/{project_name}"
"Bug Tracker" = "https://github.com/username/{project_name}/issues"

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"

[tool.ruff]
line-length = 88
target-version = "py38"
select = ["E", "F", "B", "I"]
ignore = []

[tool.ruff.isort]
known-first-party = ["{package_name}"]

[tool.ruff.flake8-quotes]
docstring-quotes = "double"
"""
    
    with open(os.path.join(project_path, "pyproject.toml"), "w") as f:
        f.write(pyproject_content)
    
    print(f"Created pyproject.toml in {project_path}")

def create_gitignore(project_path):
    """Create a .gitignore file for the project."""
    # Copy the .gitignore from the agentic repository
    agentic_gitignore = os.path.expanduser("~/Agentic/agentic/.gitignore")
    
    if os.path.exists(agentic_gitignore):
        shutil.copy(agentic_gitignore, os.path.join(project_path, ".gitignore"))
        print(f"Copied .gitignore from agentic repository to {project_path}")
    else:
        # Create a basic .gitignore if the agentic one doesn't exist
        gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
.venv/
venv/
ENV/

# IDE
.idea/
.vscode/
*.swp
*.swo

# Jupyter Notebook
.ipynb_checkpoints

# Testing
.coverage
htmlcov/
.pytest_cache/

# UV
.uv/
uv.lock
"""
        
        with open(os.path.join(project_path, ".gitignore"), "w") as f:
            f.write(gitignore_content)
        
        print(f"Created .gitignore in {project_path}")

def create_virtual_environment(project_path):
    """Create a virtual environment using uv."""
    venv_path = os.path.join(project_path, ".venv")
    
    # Check if uv is installed
    if not shutil.which("uv"):
        print("Error: uv is not installed. Please install it first.")
        return None
    
    # Create the virtual environment
    result = run_command(f"uv venv {venv_path}")
    if result is None:
        return None
    
    print(f"Created virtual environment at {venv_path}")
    return venv_path

def initialize_git(project_path):
    """Initialize a git repository."""
    result = run_command("git init", cwd=project_path)
    if result is None:
        return False
    
    print(f"Initialized git repository in {project_path}")
    return True

def register_virtual_environment(venv_path, project_name, description):
    """Register the virtual environment in the registry."""
    # Get Python version
    python_path = os.path.join(venv_path, "bin", "python")
    python_version = None
    
    if os.path.exists(python_path):
        try:
            result = subprocess.run(
                [python_path, "-c", "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')"],
                capture_output=True,
                text=True,
                check=True
            )
            python_version = result.stdout.strip()
        except Exception as e:
            print(f"Warning: Could not determine Python version: {e}")
    
    # Build the command
    cmd = f"ag venv add {venv_path} {project_name}"
    
    if python_version:
        cmd += f" --python-version {python_version}"
    
    if description:
        cmd += f" --description \"{description}\""
    
    try:
        result = run_command(cmd)
        if result is not None:
            print(f"Registered virtual environment for {project_name}")
            return True
        else:
            print("Error registering virtual environment")
            return False
    except Exception as e:
        print(f"Error registering virtual environment: {e}")
        return False

def create_new_project(project_name, description, license_type="MIT"):
    """Create a new project with the standard structure."""
    # Convert project name to kebab-case for directory name
    dir_name = project_name.lower().replace(" ", "-")
    
    # Convert to valid Python package name (snake_case)
    package_name = dir_name.replace("-", "_")
    
    # Create the project directory
    project_path = os.path.join(PROJECTS_DIR, dir_name)
    
    if os.path.exists(project_path):
        print(f"Error: Project directory already exists: {project_path}")
        return False
    
    # Create the project directory
    os.makedirs(project_path, exist_ok=True)
    
    # Create the directory structure
    create_directory_structure(project_path)
    
    # Create basic files
    create_readme(project_path, project_name, description)
    create_license(project_path, license_type)
    create_pyproject_toml(project_path, dir_name, package_name, description)
    create_gitignore(project_path)
    
    # Initialize git repository
    initialize_git(project_path)
    
    # Create virtual environment
    venv_path = create_virtual_environment(project_path)
    
    if venv_path:
        # Register the virtual environment
        register_virtual_environment(venv_path, project_name, description)
    
    print(f"\nProject '{project_name}' created successfully at {project_path}")
    print("\nNext steps:")
    print(f"1. cd {project_path}")
    print("2. source .venv/bin/activate")
    print("3. uv pip install -e .")
    
    return True

def create_project(args):
    """Create a new project, called by the ag script."""
    # Check for help flag
    if len(args) > 0 and (args[0] == "--help" or args[0] == "-h"):
        print("Usage: ag project create <project_name> [options]")
        print("\nOptions:")
        print("  --description, -d <description>  Project description")
        print("  --license, -l <license>          License type (default: MIT)")
        print("\nExample:")
        print("  ag project create \"My Project\" --description \"A cool project\" --license Apache-2.0")
        return 0
        
    if len(args) < 1:
        print("Error: Missing required arguments")
        print("Usage: ag project create <project_name> [options]")
        return 1
    
    project_name = args[0]
    description = "A project created with the Agentic framework"
    license_type = "MIT"
    
    # Parse optional arguments
    i = 1
    while i < len(args):
        if (args[i] == "--description" or args[i] == "-d") and i + 1 < len(args):
            description = args[i + 1]
            i += 2
        elif (args[i] == "--license" or args[i] == "-l") and i + 1 < len(args):
            license_type = args[i + 1]
            i += 2
        else:
            i += 1
    
    success = create_new_project(project_name, description, license_type)
    return 0 if success else 1

def list_projects(args):
    """List existing projects, called by the ag script."""
    if not os.path.exists(PROJECTS_DIR):
        print(f"Projects directory does not exist: {PROJECTS_DIR}")
        return 1
    
    projects = []
    for item in os.listdir(PROJECTS_DIR):
        item_path = os.path.join(PROJECTS_DIR, item)
        if os.path.isdir(item_path):
            # Try to get project name and description from README.md
            readme_path = os.path.join(item_path, "README.md")
            name = item
            description = ""
            
            if os.path.exists(readme_path):
                try:
                    with open(readme_path, 'r') as f:
                        lines = f.readlines()
                        if lines and lines[0].startswith('# '):
                            name = lines[0][2:].strip()
                        if len(lines) > 1:
                            description = lines[2].strip()
                except Exception:
                    pass
            
            # Check if it has a virtual environment
            venv_path = os.path.join(item_path, ".venv")
            has_venv = os.path.isdir(venv_path)
            
            projects.append({
                "name": name,
                "directory": item,
                "path": item_path,
                "description": description,
                "has_venv": has_venv
            })
    
    if not projects:
        print("No projects found.")
        return 0
    
    print(f"Projects in {PROJECTS_DIR}:")
    print("-" * 80)
    
    for i, project in enumerate(sorted(projects, key=lambda p: p["name"]), 1):
        venv_status = "\033[92m✓\033[0m" if project["has_venv"] else "\033[91m✗\033[0m"
        print(f"{i}. {project['name']} ({project['directory']})")
        if project["description"]:
            print(f"   Description: {project['description']}")
        print(f"   Path: {project['path']}")
        print(f"   Virtual Environment: {venv_status}")
        print()
    
    return 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a new project with the standard structure")
    parser.add_argument("project_name", help="Name of the project")
    parser.add_argument("--description", "-d", default="A project created with the Agentic framework", help="Description of the project")
    parser.add_argument("--license", "-l", default="MIT", help="License type (default: MIT)")
    
    args = parser.parse_args()
    
    create_new_project(args.project_name, args.description, args.license)
