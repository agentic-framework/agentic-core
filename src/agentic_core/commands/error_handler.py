#!/usr/bin/env python3
"""
Standardized Error Handling Library

This module provides a standardized way to handle errors across the Agentic framework.
It includes functions for logging errors, formatting error messages, and implementing
retry mechanisms with exponential backoff.
"""

import os
import sys
import logging
import time
import traceback
import json
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar, Union
from datetime import datetime
from functools import wraps
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.expanduser("~/Agentic/logs/error_handler.log"), mode='a')
    ]
)
logger = logging.getLogger("error_handler")

# Create logs directory if it doesn't exist
os.makedirs(os.path.expanduser("~/Agentic/logs"), exist_ok=True)

# Type variable for generic function return type
T = TypeVar('T')

class AgenticError(Exception):
    """Base class for all Agentic framework errors."""
    
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        """
        Initialize the error.
        
        Args:
            message (str): The error message
            error_code (Optional[str]): An optional error code
            details (Optional[Dict[str, Any]]): Additional details about the error
        """
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.timestamp = datetime.now().isoformat()
        
        # Format the error message
        formatted_message = message
        if error_code:
            formatted_message = f"[{error_code}] {formatted_message}"
        
        super().__init__(formatted_message)

class ValidationError(AgenticError):
    """Error raised when validation fails."""
    pass

class SecurityError(AgenticError):
    """Error raised when a security violation occurs."""
    pass

class ConfigurationError(AgenticError):
    """Error raised when there is a configuration issue."""
    pass

class DependencyError(AgenticError):
    """Error raised when there is an issue with a dependency."""
    pass

class NetworkError(AgenticError):
    """Error raised when there is a network issue."""
    pass

class FileSystemError(AgenticError):
    """Error raised when there is a file system issue."""
    pass

class RegistryError(AgenticError):
    """Error raised when there is an issue with the registry."""
    pass

def log_error(error: Exception, level: int = logging.ERROR, include_traceback: bool = True) -> None:
    """
    Log an error with optional traceback.
    
    Args:
        error (Exception): The error to log
        level (int): The logging level (default: logging.ERROR)
        include_traceback (bool): Whether to include the traceback in the log
    """
    error_message = str(error)
    
    if isinstance(error, AgenticError):
        # For AgenticError, include error code and details
        error_data = {
            "message": error.message,
            "error_code": error.error_code,
            "details": error.details,
            "timestamp": error.timestamp
        }
        error_message = json.dumps(error_data)
    
    if include_traceback:
        logger.log(level, f"Error: {error_message}\nTraceback: {traceback.format_exc()}")
    else:
        logger.log(level, f"Error: {error_message}")

def format_error_message(error: Exception) -> str:
    """
    Format an error message for display.
    
    Args:
        error (Exception): The error to format
    
    Returns:
        str: The formatted error message
    """
    if isinstance(error, AgenticError):
        # For AgenticError, include error code and details
        message = error.message
        if error.error_code:
            message = f"[{error.error_code}] {message}"
        
        if error.details:
            message = f"{message}\nDetails: {json.dumps(error.details, indent=2)}"
        
        return message
    else:
        # For other exceptions, just return the string representation
        return str(error)

def retry(max_attempts: int = 3, initial_delay: float = 1.0, backoff_factor: float = 2.0,
         retry_exceptions: Tuple[type[Exception], ...] = (Exception,),
         should_retry: Optional[Callable[[Exception], bool]] = None) -> Callable:
    """
    Decorator for retrying a function with exponential backoff.
    
    Args:
        max_attempts (int): Maximum number of attempts (default: 3)
        initial_delay (float): Initial delay in seconds (default: 1.0)
        backoff_factor (float): Backoff factor for exponential backoff (default: 2.0)
        retry_exceptions (Tuple[Exception, ...]): Exceptions to retry on (default: (Exception,))
        should_retry (Optional[Callable[[Exception], bool]]): Function to determine if retry should occur
    
    Returns:
        Callable: Decorated function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception = None
            delay = initial_delay
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except retry_exceptions as e:
                    last_exception = e
                    
                    # Check if we should retry
                    if should_retry and not should_retry(e):
                        logger.warning(f"Not retrying {func.__name__} due to exception: {e}")
                        raise
                    
                    # Check if this is the last attempt
                    if attempt == max_attempts:
                        logger.error(f"Failed to execute {func.__name__} after {max_attempts} attempts")
                        raise
                    
                    # Log the retry
                    logger.warning(f"Retrying {func.__name__} (attempt {attempt}/{max_attempts}) after exception: {e}")
                    
                    # Wait before retrying
                    time.sleep(delay)
                    
                    # Increase the delay for the next attempt
                    delay *= backoff_factor
            
            # This should never be reached, but just in case
            if last_exception:
                raise last_exception
            
            # This should also never be reached
            raise RuntimeError(f"Failed to execute {func.__name__} for unknown reasons")
        
        return wrapper
    
    return decorator

def safe_execute(func: Callable[..., T], *args: Any, default_value: Optional[T] = None,
                log_level: int = logging.ERROR, **kwargs: Any) -> Optional[T]:
    """
    Execute a function safely, catching and logging any exceptions.
    
    Args:
        func (Callable[..., T]): The function to execute
        *args: Arguments to pass to the function
        default_value (Optional[T]): Default value to return if an exception occurs
        log_level (int): The logging level for errors (default: logging.ERROR)
        **kwargs: Keyword arguments to pass to the function
    
    Returns:
        T: The result of the function or the default value if an exception occurs
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        log_error(e, level=log_level)
        return default_value

def validate_path(path: str, must_exist: bool = False, must_be_file: bool = False,
                 must_be_dir: bool = False, create_parents: bool = False) -> bool:
    """
    Validate a file or directory path.
    
    Args:
        path (str): The path to validate
        must_exist (bool): Whether the path must exist
        must_be_file (bool): Whether the path must be a file
        must_be_dir (bool): Whether the path must be a directory
        create_parents (bool): Whether to create parent directories if they don't exist
    
    Returns:
        bool: True if the path is valid, False otherwise
    
    Raises:
        ValidationError: If the path is invalid
    """
    try:
        path_obj = Path(os.path.expanduser(path))
        
        # Check if the path exists
        if must_exist and not path_obj.exists():
            raise ValidationError(f"Path does not exist: {path}", "PATH_NOT_FOUND")
        
        # Check if the path is a file
        if must_be_file and path_obj.exists() and not path_obj.is_file():
            raise ValidationError(f"Path is not a file: {path}", "NOT_A_FILE")
        
        # Check if the path is a directory
        if must_be_dir and path_obj.exists() and not path_obj.is_dir():
            raise ValidationError(f"Path is not a directory: {path}", "NOT_A_DIRECTORY")
        
        # Create parent directories if requested
        if create_parents and not path_obj.parent.exists():
            path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        return True
    except ValidationError:
        # Re-raise validation errors
        raise
    except Exception as e:
        # Convert other exceptions to ValidationError
        raise ValidationError(f"Invalid path: {path}", "INVALID_PATH", {"original_error": str(e)})

def validate_config(config: Dict[str, Any], required_keys: List[str],
                   optional_keys: Optional[List[str]] = None) -> bool:
    """
    Validate a configuration dictionary.
    
    Args:
        config (Dict[str, Any]): The configuration to validate
        required_keys (List[str]): Keys that must be present in the configuration
        optional_keys (Optional[List[str]]): Keys that may be present in the configuration
    
    Returns:
        bool: True if the configuration is valid, False otherwise
    
    Raises:
        ValidationError: If the configuration is invalid
    """
    # Check for missing required keys
    missing_keys = [key for key in required_keys if key not in config]
    if missing_keys:
        raise ValidationError(
            f"Missing required configuration keys: {', '.join(missing_keys)}",
            "MISSING_CONFIG_KEYS",
            {"missing_keys": missing_keys}
        )
    
    # Check for unknown keys if optional_keys is provided
    if optional_keys is not None:
        allowed_keys = required_keys + optional_keys
        unknown_keys = [key for key in config if key not in allowed_keys]
        if unknown_keys:
            raise ValidationError(
                f"Unknown configuration keys: {', '.join(unknown_keys)}",
                "UNKNOWN_CONFIG_KEYS",
                {"unknown_keys": unknown_keys}
            )
    
    return True

def handle_network_error(error: Exception) -> NetworkError:
    """
    Convert a network-related exception to a NetworkError.
    
    Args:
        error (Exception): The original error
    
    Returns:
        NetworkError: A NetworkError with details from the original error
    """
    error_type = type(error).__name__
    error_message = str(error)
    
    # Create a NetworkError with details from the original error
    return NetworkError(
        f"Network error: {error_message}",
        "NETWORK_ERROR",
        {
            "error_type": error_type,
            "original_error": error_message
        }
    )

def handle_file_system_error(error: Exception, path: str) -> FileSystemError:
    """
    Convert a file system-related exception to a FileSystemError.
    
    Args:
        error (Exception): The original error
        path (str): The path that caused the error
    
    Returns:
        FileSystemError: A FileSystemError with details from the original error
    """
    error_type = type(error).__name__
    error_message = str(error)
    
    # Create a FileSystemError with details from the original error
    return FileSystemError(
        f"File system error: {error_message}",
        "FILE_SYSTEM_ERROR",
        {
            "error_type": error_type,
            "original_error": error_message,
            "path": path
        }
    )

def with_error_handling(error_type: type = AgenticError, reraise: bool = True,
                       default_value: Optional[Any] = None) -> Callable:
    """
    Decorator for handling errors in a function.
    
    Args:
        error_type (type): The type of error to convert exceptions to
        reraise (bool): Whether to reraise the converted error
        default_value (Optional[Any]): Default value to return if an exception occurs
    
    Returns:
        Callable: Decorated function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., Optional[T]]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Optional[T]:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Skip conversion if the exception is already of the target type
                if isinstance(e, error_type):
                    converted_error = e
                else:
                    # Convert the exception to the target type
                    error_message = str(e)
                    error_code = type(e).__name__.upper()
                    details = {"original_error": error_message}
                    
                    converted_error = error_type(error_message, error_code, details)
                
                # Log the error
                log_error(converted_error)
                
                # Reraise the converted error if requested
                if reraise:
                    raise converted_error
                
                # Otherwise, return the default value
                return default_value
        
        return wrapper
    
    return decorator

def error_handler_cli(args):
    """
    CLI function for the error handler, called by the ag script.
    
    Args:
        args: Command-line arguments
    
    Returns:
        int: Exit code
    """
    if not args:
        print("Error: No command specified")
        print("Usage: ag error-handler <command>")
        return 1
    
    command = args[0]
    
    if command == "example":
        # Example usage of retry decorator
        @retry(max_attempts=3, initial_delay=1.0, backoff_factor=2.0)
        def example_retry_function(success_on_attempt: int, attempt_counter: List[int]) -> str:
            """Example function that succeeds on a specific attempt."""
            attempt_counter[0] += 1
            
            if attempt_counter[0] < success_on_attempt:
                raise ValueError(f"Simulated error on attempt {attempt_counter[0]}")
            
            return "Success!"
        
        # Example usage of with_error_handling decorator
        @with_error_handling(error_type=ValidationError, reraise=False, default_value="Default Value")
        def example_error_handling_function(raise_error: bool) -> str:
            """Example function that may raise an error."""
            if raise_error:
                raise ValueError("Simulated error")
            
            return "Success!"
        
        # Example usage of safe_execute function
        def example_function_that_may_fail(raise_error: bool) -> str:
            """Example function that may raise an error."""
            if raise_error:
                raise ValueError("Simulated error")
            
            return "Success!"
        
        # Test retry decorator
        print("Testing retry decorator:")
        attempt_counter = [0]  # Use a list to track attempts
        try:
            result = example_retry_function(success_on_attempt=3, attempt_counter=attempt_counter)
            print(f"Result: {result}")
        except Exception as e:
            print(f"Error: {e}")
        
        # Test with_error_handling decorator
        print("\nTesting with_error_handling decorator:")
        result = example_error_handling_function(raise_error=False)
        print(f"Result (no error): {result}")
        result = example_error_handling_function(raise_error=True)
        print(f"Result (with error): {result}")
        
        # Test safe_execute function
        print("\nTesting safe_execute function:")
        result = safe_execute(example_function_that_may_fail, False, default_value="Default Value")
        print(f"Result (no error): {result}")
        result = safe_execute(example_function_that_may_fail, True, default_value="Default Value")
        print(f"Result (with error): {result}")
        
        # Test error formatting
        print("\nTesting error formatting:")
        try:
            raise ValidationError("Invalid input", "INVALID_INPUT", {"field": "username", "reason": "too short"})
        except ValidationError as e:
            formatted_message = format_error_message(e)
            print(f"Formatted error message: {formatted_message}")
        
        return 0
    else:
        print(f"Error: Unknown command: {command}")
        print("Available commands: example")
        return 1

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Agentic Framework Error Handler")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Example command
    example_parser = subparsers.add_parser("example", help="Run error handling examples")
    
    args = parser.parse_args()
    
    if args.command == "example":
        # Example usage of retry decorator
        @retry(max_attempts=3, initial_delay=1.0, backoff_factor=2.0)
        def example_retry_function(success_on_attempt: int, attempt_counter: List[int]) -> str:
            """Example function that succeeds on a specific attempt."""
            attempt_counter[0] += 1
            
            if attempt_counter[0] < success_on_attempt:
                raise ValueError(f"Simulated error on attempt {attempt_counter[0]}")
            
            return "Success!"
        
        # Example usage of with_error_handling decorator
        @with_error_handling(error_type=ValidationError, reraise=False, default_value="Default Value")
        def example_error_handling_function(raise_error: bool) -> str:
            """Example function that may raise an error."""
            if raise_error:
                raise ValueError("Simulated error")
            
            return "Success!"
        
        # Example usage of safe_execute function
        def example_function_that_may_fail(raise_error: bool) -> str:
            """Example function that may raise an error."""
            if raise_error:
                raise ValueError("Simulated error")
            
            return "Success!"
        
        # Test retry decorator
        print("Testing retry decorator:")
        attempt_counter = [0]  # Use a list to track attempts
        try:
            result = example_retry_function(success_on_attempt=3, attempt_counter=attempt_counter)
            print(f"Result: {result}")
        except Exception as e:
            print(f"Error: {e}")
        
        # Test with_error_handling decorator
        print("\nTesting with_error_handling decorator:")
        result = example_error_handling_function(raise_error=False)
        print(f"Result (no error): {result}")
        result = example_error_handling_function(raise_error=True)
        print(f"Result (with error): {result}")
        
        # Test safe_execute function
        print("\nTesting safe_execute function:")
        result = safe_execute(example_function_that_may_fail, False, default_value="Default Value")
        print(f"Result (no error): {result}")
        result = safe_execute(example_function_that_may_fail, True, default_value="Default Value")
        print(f"Result (with error): {result}")
        
        # Test error formatting
        print("\nTesting error formatting:")
        try:
            raise ValidationError("Invalid input", "INVALID_INPUT", {"field": "username", "reason": "too short"})
        except ValidationError as e:
            formatted_message = format_error_message(e)
            print(f"Formatted error message: {formatted_message}")
    else:
        parser.print_help()
