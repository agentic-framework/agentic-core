"""
Agentic CLI - Main Command Line Interface for the Agentic Framework

This module provides a unified command-line interface for the Agentic framework
using a git-style command-subcommand pattern. It serves as the main entry point
for all CLI operations dispatching to appropriate modules based on commands.

Usage:
  ag <command> <subcommand> [<args>]

Examples:
  ag env check                # Check the environment setup
  ag venv create my-project   # Create a virtual environment
  ag project create my-app    # Create a new project
  ag feedback submit          # Submit feedback
  ag config get paths.root    # Get a configuration value
"""

import os
import sys
import argparse
import importlib.util
import importlib.metadata
from typing import Dict, List, Callable, Optional, Any

# Define the command structure
COMMAND_STRUCTURE = {
    "dependency": {
        "description": "Dependency management commands",
        "subcommands": {
            "check": {
                "description": "Check if a dependency is installed and meets requirements",
                "module": "agentic_core.commands.dependency_manager",
                "function": "check_dependency_cli"
            },
            "install": {
                "description": "Install a dependency",
                "module": "agentic_core.commands.dependency_manager",
                "function": "install_dependency_cli"
            },
            "update": {
                "description": "Update a dependency to the recommended version",
                "module": "agentic_core.commands.dependency_manager",
                "function": "update_dependency_cli"
            },
            "list": {
                "description": "List all dependencies and their status",
                "module": "agentic_core.commands.dependency_manager",
                "function": "list_dependencies_cli"
            },
            "fallback": {
                "description": "Use a fallback implementation for a dependency",
                "module": "agentic_core.commands.dependency_manager",
                "function": "fallback_cli"
            }
        }
    },
    "discover": {
        "description": "Discover and load the Agentic framework",
        "subcommands": {
            "info": {
                "description": "Get information about the Agentic framework",
                "module": "agentic_core.commands.discover_agentic",
                "function": "discover_cli"
            }
        }
    },
    "error": {
        "description": "Error handling commands",
        "subcommands": {
            "example": {
                "description": "Run error handling examples",
                "module": "agentic_core.commands.error_handler",
                "function": "error_handler_cli"
            }
        }
    },
    "issues": {
        "description": "GitHub issues management commands",
        "subcommands": {
            "list": {
                "description": "List GitHub issues",
                "module": "agentic_core.commands.issues_command",
                "function": "issues_command"
            }
        }
    },
    "env": {
        "description": "Environment management commands",
        "subcommands": {
            "check": {
                "description": "Check the environment setup",
                "module": "agentic_core.commands.check_environment",
                "function": "check_environment"
            },
            "fix": {
                "description": "Fix common environment issues",
                "module": "agentic_core.commands.check_environment",
                "function": "fix_environment"
            }
        }
    },
    "venv": {
        "description": "Virtual environment management commands",
        "subcommands": {
            "list": {
                "description": "List registered virtual environments",
                "module": "agentic_core.commands.venv_manager",
                "function": "list_environments"
            },
            "create": {
                "description": "Create a new virtual environment",
                "module": "agentic_core.commands.venv_manager",
                "function": "create_environment"
            },
            "add": {
                "description": "Add an existing virtual environment to the registry",
                "module": "agentic_core.commands.venv_manager",
                "function": "add_environment"
            },
            "remove": {
                "description": "Remove a virtual environment",
                "module": "agentic_core.commands.venv_manager",
                "function": "remove_environment"
            },
            "check": {
                "description": "Check a virtual environment",
                "module": "agentic_core.commands.venv_manager",
                "function": "check_environment"
            },
            "cleanup": {
                "description": "Clean up non-existent virtual environments",
                "module": "agentic_core.commands.venv_manager",
                "function": "cleanup_environments"
            }
        }
    },
    "project": {
        "description": "Project management commands",
        "subcommands": {
            "create": {
                "description": "Create a new project",
                "module": "agentic_core.commands.create_project",
                "function": "create_project"
            },
            "list": {
                "description": "List existing projects",
                "module": "agentic_core.commands.create_project",
                "function": "list_projects"
            }
        }
    },
    "feedback": {
        "description": "Feedback system commands",
        "subcommands": {
            "submit": {
                "description": "Submit feedback",
                "module": "agentic_core.commands.feedback_cli",
                "function": "submit_issue_cli"
            },
            "list": {
                "description": "List feedback items",
                "module": "agentic_core.commands.feedback_cli",
                "function": "list_issues_cli"
            },
            "get": {
                "description": "Get feedback details",
                "module": "agentic_core.commands.feedback_cli",
                "function": "get_issue_cli"
            },
            "update": {
                "description": "Update feedback status",
                "module": "agentic_core.commands.feedback_cli",
                "function": "update_issue_cli"
            },
            "comment": {
                "description": "Add a comment to feedback",
                "module": "agentic_core.commands.feedback_cli",
                "function": "comment_issue_cli"
            }
        }
    },
    "config": {
        "description": "Configuration management commands",
        "subcommands": {
            "get": {
                "description": "Get a configuration value",
                "module": "agentic_core.commands.config",
                "function": "get_config"
            },
            "set": {
                "description": "Set a configuration value",
                "module": "agentic_core.commands.config",
                "function": "set_config"
            },
            "list": {
                "description": "List configuration values",
                "module": "agentic_core.commands.config",
                "function": "list_config"
            },
            "reset": {
                "description": "Reset configuration to defaults",
                "module": "agentic_core.commands.config",
                "function": "reset_config"
            }
        }
    },
    "uv": {
        "description": "UV package manager commands",
        "subcommands": {
            "install": {
                "description": "Install UV",
                "module": "agentic_core.commands.uv_manager",
                "function": "install_uv"
            },
            "update": {
                "description": "Update UV",
                "module": "agentic_core.commands.uv_manager",
                "function": "update_uv"
            },
            "list-python": {
                "description": "List available Python versions",
                "module": "agentic_core.commands.uv_manager",
                "function": "list_python_versions"
            },
            "install-python": {
                "description": "Install a specific Python version",
                "module": "agentic_core.commands.uv_manager",
                "function": "install_python"
            },
            "clean-cache": {
                "description": "Clean the UV cache",
                "module": "agentic_core.commands.uv_manager",
                "function": "clean_cache"
            }
        }
    },
    "security": {
        "description": "Security enforcement commands",
        "subcommands": {
            "check-path": {
                "description": "Check if a path is allowed",
                "module": "agentic_core.commands.security",
                "function": "check_path"
            },
            "validate-command": {
                "description": "Validate a command for execution",
                "module": "agentic_core.commands.security",
                "function": "validate_command_cli"
            },
            "scan-file": {
                "description": "Scan a file for potential security violations",
                "module": "agentic_core.commands.security",
                "function": "scan_file"
            },
            "hash-file": {
                "description": "Calculate the SHA-256 hash of a file",
                "module": "agentic_core.commands.security",
                "function": "hash_file"
            }
        }
    },
    "cleanup": {
        "description": "Cleanup and maintenance commands",
        "subcommands": {
            "tmp": {
                "description": "Clean up temporary files",
                "module": "agentic_core.commands.cleanup_manager",
                "function": "cleanup_tmp"
            },
            "check-orphaned-venvs": {
                "description": "Check for orphaned virtual environments",
                "module": "agentic_core.commands.cleanup_manager",
                "function": "check_orphaned_venvs_cli"
            },
            "disk-usage": {
                "description": "Analyze disk usage",
                "module": "agentic_core.commands.cleanup_manager",
                "function": "disk_usage"
            }
        }
    },
    "rule": {
        "description": "Rule loading and verification commands",
        "subcommands": {
            "verify": {
                "description": "Verify an AI agent's understanding of the rules",
                "module": "agentic_core.commands.rule_loader",
                "function": "verify_rules"
            },
            "query": {
                "description": "Query specific rules",
                "module": "agentic_core.commands.rule_loader",
                "function": "query_rules"
            },
            "list": {
                "description": "List rule categories",
                "module": "agentic_core.commands.rule_loader",
                "function": "list_categories"
            }
        }
    },
    "setup": {
        "description": "Setup commands for the Agentic framework",
        "subcommands": {
            "install-dependencies": {
                "description": "Install required dependencies",
                "module": "agentic_core.commands.setup",
                "function": "install_dependencies"
            },
            "create-directories": {
                "description": "Create the required directory structure",
                "module": "agentic_core.commands.setup",
                "function": "create_directories"
            },
            "initialize-registry": {
                "description": "Initialize the virtual environment registry",
                "module": "agentic_core.commands.setup",
                "function": "initialize_registry"
            },
            "all": {
                "description": "Run all setup steps",
                "module": "agentic_core.commands.setup",
                "function": "setup_all"
            }
        }
    }
}

def discover_plugins():
    """Discover and load all agentic command plugins."""
    commands = {}

    # Find all entry points in the 'agentic.commands' group
    try:
        for entry_point in importlib.metadata.entry_points(group='agentic.commands'):
            try:
                # Load the command function
                command_func = entry_point.load()
                commands[entry_point.name] = command_func
                print(f"Discovered plugin command: {entry_point.name}")
            except Exception as e:
                print(f"Error loading command {entry_point.name}: {e}", file=sys.stderr)
    except Exception as e:
        print(f"Error discovering plugins: {e}", file=sys.stderr)

    return commands

class AgenticCLI:
    """Main CLI class for the Agentic framework."""

    def __init__(self):
        """Initialize the CLI."""
        self.parser = argparse.ArgumentParser(
            description="Agentic Framework CLI",
            usage="ag <command> <subcommand> [<args>]"
        )
        self.parser.add_argument("command", help="Command to run")

        # Store the original sys.argv
        self.original_argv = sys.argv.copy()

        # Set up module paths
        self.agentic_root = os.path.expanduser("~/Agentic")
        self.agentic_dir = os.path.join(self.agentic_root, "agentic")

    def run(self):
        """Run the CLI."""
        # No command provided
        if len(sys.argv) < 2:
            self.parser.print_help()
            self.print_commands()
            return 1

        # Parse the command
        args = self.parser.parse_args(sys.argv[1:2])
        command = args.command

        # Check if the command exists in built-in commands
        if command in COMMAND_STRUCTURE:
            # Handle the built-in command
            return self.handle_command(command)
        else:
            # Check if it's a plugin command
            plugin_commands = discover_plugins()
            if command in plugin_commands:
                # Remove the command name from argv and pass the rest to the plugin
                sys.argv.pop(1)
                return plugin_commands[command]()
            else:
                print(f"Unknown command: {command}")
                self.print_commands()
                return 1

    def handle_command(self, command):
        """Handle a command."""
        command_info = COMMAND_STRUCTURE[command]

        # Create a parser for the subcommand
        parser = argparse.ArgumentParser(
            description=command_info["description"],
            usage=f"ag {command} <subcommand> [<args>]"
        )
        parser.add_argument("subcommand", help=f"Subcommand for {command}")

        # No subcommand provided
        if len(sys.argv) < 3:
            parser.print_help()
            self.print_subcommands(command)
            return 1

        # Parse the subcommand
        args = parser.parse_args(sys.argv[2:3])
        subcommand = args.subcommand

        # Check if the subcommand exists
        if subcommand not in command_info["subcommands"]:
            print(f"Unknown subcommand: {subcommand}")
            self.print_subcommands(command)
            return 1

        # Handle the subcommand
        return self.handle_subcommand(command, subcommand)

    def handle_subcommand(self, command, subcommand):
        """Handle a subcommand."""
        subcommand_info = COMMAND_STRUCTURE[command]["subcommands"][subcommand]

        # Import the module
        module_name = subcommand_info["module"]
        function_name = subcommand_info["function"]

        try:
            # Try to import the module
            module = importlib.import_module(module_name)

            # Get the function
            if not hasattr(module, function_name):
                print(f"Error: Function not found: {function_name}")
                return 1

            function = getattr(module, function_name)

            # Call the function with the remaining arguments
            return function(sys.argv[3:])
        except ImportError as e:
            print(f"Error: Could not import module: {module_name}")
            print(f"Details: {e}")
            return 1
        except Exception as e:
            print(f"Error: {e}")
            return 1

    def print_commands(self):
        """Print available commands."""
        print("\nAvailable commands:")
        for command, info in COMMAND_STRUCTURE.items():
            print(f"  {command:<10} {info['description']}")
        
        # Print plugin commands
        plugin_commands = discover_plugins()
        if plugin_commands:
            print("\nPlugin commands:")
            for command in plugin_commands:
                print(f"  {command}")
        
        print("\nRun 'ag <command> --help' for more information on a command.")

    def print_subcommands(self, command):
        """Print available subcommands for a command."""
        command_info = COMMAND_STRUCTURE[command]
        print(f"\nAvailable subcommands for '{command}':")
        for subcommand, info in command_info["subcommands"].items():
            print(f"  {subcommand:<15} {info['description']}")
        print(f"\nRun 'ag {command} <subcommand> --help' for more information on a subcommand.")

def main():
    """Main function."""
    cli = AgenticCLI()
    return cli.run()

if __name__ == "__main__":
    sys.exit(main())
