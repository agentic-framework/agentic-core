#!/usr/bin/env python3
"""
Issues command for the Agentic framework.

This module provides the `ag issues` command for the Agentic framework.
"""

import sys
import os
import logging
import importlib.util
import subprocess
from typing import List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.expanduser("~/Agentic/logs/issues_command.log"), mode='a')
    ]
)
logger = logging.getLogger("issues_command")

# Create logs directory if it doesn't exist
os.makedirs(os.path.expanduser("~/Agentic/logs"), exist_ok=True)

def issues_command(args: List[str]) -> int:
    """
    Handle the `ag issues` command.
    
    Args:
        args: Command-line arguments passed to the `ag issues` command.
    
    Returns:
        int: Exit code.
    """
    try:
        # Try to import the agentic_issues package
        import agentic_issues.ag_issues
        return agentic_issues.ag_issues.issues_command(args)
    except ImportError:
        # If the package is not installed, suggest installing it
        print("Error: The Agentic Issues package is not installed.")
        print("Please install it by running:")
        print("  cd ~/Agentic/projects/agentic-issues")
        print("  source .venv/bin/activate")
        print("  uv pip install -e .")
        return 1

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Agentic Framework Issues Command")
    parser.add_argument("args", nargs="*", help="Arguments to pass to the issues command")
    
    args = parser.parse_args()
    
    sys.exit(issues_command(args.args))
