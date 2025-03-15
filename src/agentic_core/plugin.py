"""
Plugin interface for the Agentic framework.

This module defines the interface for command plugins.
"""

def command_interface():
    """
    Interface definition for command plugins.

    Command plugins should provide a function that:
    1. Takes no arguments (it will parse sys.argv directly)
    2. Returns an integer exit code (0 for success, non-zero for failure)
    3. Handles its own argument parsing

    Example:

    def my_command():
        import argparse
        parser = argparse.ArgumentParser(description="My command")
        # ... add arguments ...
        args = parser.parse_args()
        # ... implement command logic ...
        return 0  # success
    """
    pass
