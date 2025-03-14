# agentic-core

Command line tool framework that implements the 'ag' command and manages how it loads sub-tools.

## Overview

The `agentic-core` project is the central component of the Agentic ecosystem. It provides the main command-line interface (`ag`) that serves as the entry point for all Agentic tools and utilities. The core framework is designed to dynamically load and manage sub-tools, making it easy to extend the functionality of the Agentic ecosystem.

### Key Features

- Git-style command-subcommand pattern for intuitive CLI usage
- Dynamic loading of command modules
- Extensible architecture for adding new commands and subcommands
- Unified error handling and logging
- Comprehensive help system

## Directory Structure

```
agentic-core/
├── .venv/                 # Virtual environment (not in version control)
├── src/                   # Source code
│   └── agentic_core/      # Main package
│       ├── __init__.py    # Package initialization
│       ├── cli.py         # Main CLI implementation
│       ├── bin/           # Executable scripts
│       │   └── ag         # Main entry point script
│       └── commands/      # Command implementations
│           ├── __init__.py
│           ├── check_environment.py
│           ├── cleanup_manager.py
│           ├── config.py
│           ├── create_project.py
│           ├── dependency_manager.py
│           ├── error_handler.py
│           ├── feedback_system.py
│           ├── rule_loader.py
│           ├── security.py
│           ├── setup.py
│           ├── uv_manager.py
│           └── venv_manager.py
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

2. Install the package in development mode:
   ```bash
   uv pip install -e .
   ```

3. Run the CLI:
   ```bash
   ag --help
   ```

4. Run tests:
   ```bash
   pytest
   ```

## Usage

The `ag` command follows a git-style command-subcommand pattern:

```bash
ag <command> <subcommand> [<args>]
```

Examples:
```bash
ag env check                # Check the environment setup
ag venv create my-project   # Create a virtual environment
ag project create my-app    # Create a new project
ag feedback submit          # Submit feedback
ag config get paths.root    # Get a configuration value
```

To see all available commands:
```bash
ag
```

To see all available subcommands for a command:
```bash
ag <command>
```

To get help for a specific subcommand:
```bash
ag <command> <subcommand> --help
```

## License

See the [LICENSE](LICENSE) file for details.
