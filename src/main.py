"""Main entry point for Local AI Development Environment.

This module provides the CLI interface for the Local AI Development Environment.
It handles:
- Initialization of all system components with configuration
- Command-line argument parsing for task execution
- Logging setup with configurable verbosity
- Graceful handling of initialization errors
- Progress tracking and output formatting

Requirements:
- 1.3: Initialize all components using local resources only
- 15.6: Provide different log verbosity levels
"""

import sys
import argparse
import logging
from pathlib import Path
from typing import Optional

from src.core.config import ConfigManager, ConfigurationError
from src.core.llm_interface import LocalLLMInterface, ModelUnavailableError
from src.core.task_executor import TaskExecutor
from src.agents.code_agent import CodeAgent
from src.agents.file_operations import FileOperations
from src.agents.code_search import CodeSearch
from src.agents.command_executor import CommandExecutor
from src.context.context_manager import ContextManager
from src.core.models import SystemConfig


# Version information
VERSION = "0.1.0"


def setup_logging(log_level: str) -> logging.Logger:
    """Configure logging with the specified verbosity level.
    
    Args:
        log_level: Logging level (debug, info, warning, error)
    
    Returns:
        Configured logger instance
    
    Requirements: 15.6 - Provide different log verbosity levels
    """
    # Map string level to logging constant
    level_map = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR
    }
    
    level = level_map.get(log_level.lower(), logging.INFO)
    
    # Configure root logger
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Create and return main logger
    logger = logging.getLogger("local_ai_dev")
    logger.setLevel(level)
    
    return logger


def initialize_components(config: SystemConfig, logger: logging.Logger) -> tuple:
    """Initialize all system components with the provided configuration.
    
    Args:
        config: System configuration
        logger: Logger for tracking initialization
    
    Returns:
        Tuple of (TaskExecutor, LocalLLMInterface, CodeAgent, ContextManager)
    
    Raises:
        ConfigurationError: If initialization fails due to invalid configuration
        ModelUnavailableError: If the local LLM is not available
    
    Requirements: 1.3 - Initialize all components using local resources only
    """
    logger.info("Initializing Local AI Development Environment...")
    
    # Initialize LLM Interface
    try:
        logger.debug(f"Connecting to LLM at {config.llm.endpoint} (model: {config.llm.model_name})")
        llm_interface = LocalLLMInterface(config.llm, logger=logger)
        
        # Verify LLM is available
        if not llm_interface.is_available():
            raise ModelUnavailableError(
                f"Local LLM at {config.llm.endpoint} is not responding. "
                f"Please ensure your LLM server is running."
            )
        
        logger.info(f"✓ Connected to local LLM: {config.llm.model_name}")
        
    except ModelUnavailableError:
        raise
    except Exception as e:
        logger.error(f"Failed to initialize LLM interface: {e}")
        raise ConfigurationError(f"LLM initialization failed: {e}")
    
    # Initialize File Operations
    try:
        logger.debug("Initializing file operations...")
        file_ops = FileOperations(
            root_path=config.project_root,
            excluded_dirs=config.excluded_directories,
            logger=logger
        )
        logger.info("✓ File operations initialized")
    except Exception as e:
        logger.error(f"Failed to initialize file operations: {e}")
        raise ConfigurationError(f"File operations initialization failed: {e}")
    
    # Initialize Code Search
    try:
        logger.debug("Initializing code search...")
        code_search = CodeSearch(
            root_path=config.project_root,
            excluded_dirs=config.excluded_directories,
            logger=logger
        )
        logger.info("✓ Code search initialized")
    except Exception as e:
        logger.error(f"Failed to initialize code search: {e}")
        raise ConfigurationError(f"Code search initialization failed: {e}")
    
    # Initialize Command Executor
    try:
        logger.debug("Initializing command executor...")
        command_executor = CommandExecutor(
            cwd=config.project_root,
            logger=logger
        )
        logger.info("✓ Command executor initialized")
    except Exception as e:
        logger.error(f"Failed to initialize command executor: {e}")
        raise ConfigurationError(f"Command executor initialization failed: {e}")
    
    # Initialize Code Agent
    try:
        logger.debug("Initializing code agent...")
        code_agent = CodeAgent(
            file_ops=file_ops,
            code_search=code_search,
            command_executor=command_executor,
            logger=logger
        )
        logger.info("✓ Code agent initialized")
    except Exception as e:
        logger.error(f"Failed to initialize code agent: {e}")
        raise ConfigurationError(f"Code agent initialization failed: {e}")
    
    # Initialize Context Manager
    try:
        logger.debug("Initializing context manager...")
        context_manager = ContextManager(
            root_path=config.project_root,
            excluded_dirs=config.excluded_directories,
            logger=logger
        )
        
        # Perform initial project scan
        logger.info("Scanning project structure...")
        project_context = context_manager.scan_project(config.project_root)
        
        logger.info(f"✓ Project scanned: {len(project_context.languages)} language(s) detected")
        if project_context.languages:
            logger.debug(f"  Languages: {', '.join(project_context.languages)}")
        if project_context.frameworks:
            logger.debug(f"  Frameworks: {', '.join(project_context.frameworks)}")
            
    except Exception as e:
        logger.error(f"Failed to initialize context manager: {e}")
        raise ConfigurationError(f"Context manager initialization failed: {e}")
    
    # Initialize Task Executor
    try:
        logger.debug("Initializing task executor...")
        task_executor = TaskExecutor(
            llm_interface=llm_interface,
            code_agent=code_agent,
            context_manager=context_manager,
            logger=logger
        )
        logger.info("✓ Task executor initialized")
    except Exception as e:
        logger.error(f"Failed to initialize task executor: {e}")
        raise ConfigurationError(f"Task executor initialization failed: {e}")
    
    logger.info("All components initialized successfully!")
    
    return task_executor, llm_interface, code_agent, context_manager


def execute_task_interactive(task_executor: TaskExecutor, logger: logging.Logger):
    """Run interactive mode where user can input tasks continuously.
    
    Args:
        task_executor: Initialized task executor
        logger: Logger for output
    """
    print("\n" + "="*70)
    print("Local AI Development Environment - Interactive Mode")
    print("="*70)
    print("Type 'exit' or 'quit' to stop")
    print("Type 'help' for available commands")
    print("="*70 + "\n")
    
    while True:
        try:
            task_description = input("\n> Enter task: ").strip()
            
            if not task_description:
                continue
            
            if task_description.lower() in ['exit', 'quit']:
                print("Goodbye!")
                break
            
            if task_description.lower() == 'help':
                print_help()
                continue
            
            # Execute the task
            print(f"\nExecuting task: {task_description}")
            print("-" * 70)
            
            result = task_executor.execute_task(task_description)
            
            # Display results
            print("-" * 70)
            if result.success:
                print("✓ Task completed successfully!")
                
                if result.files_modified:
                    print(f"\nFiles modified ({len(result.files_modified)}):")
                    for file_path in result.files_modified:
                        print(f"  - {file_path}")
                
                if result.execution_log:
                    print(f"\nActions taken ({len(result.actions_taken)}):")
                    for action in result.actions_taken:
                        print(f"  - {action.action}: {action.rationale}")
                
                if result.tests_passed:
                    print("\n✓ All tests passed")
                    
            else:
                print("✗ Task failed!")
                if result.error_message:
                    print(f"\nError: {result.error_message}")
                
                if result.execution_log:
                    print(f"\nExecution log:")
                    for log_entry in result.execution_log[-5:]:  # Last 5 entries
                        print(f"  {log_entry}")
            
        except KeyboardInterrupt:
            print("\n\nInterrupted by user. Goodbye!")
            break
        except Exception as e:
            logger.error(f"Error during task execution: {e}", exc_info=True)
            print(f"\n✗ Error: {e}")


def execute_single_task(task_executor: TaskExecutor, task_description: str, logger: logging.Logger) -> int:
    """Execute a single task and return exit code.
    
    Args:
        task_executor: Initialized task executor
        task_description: Description of task to execute
        logger: Logger for output
    
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    logger.info(f"Executing task: {task_description}")
    
    try:
        result = task_executor.execute_task(task_description)
        
        if result.success:
            logger.info("Task completed successfully")
            
            if result.files_modified:
                logger.info(f"Modified {len(result.files_modified)} file(s)")
                for file_path in result.files_modified:
                    logger.debug(f"  - {file_path}")
            
            return 0
        else:
            logger.error(f"Task failed: {result.error_message}")
            return 1
            
    except Exception as e:
        logger.error(f"Task execution failed with exception: {e}", exc_info=True)
        return 1


def print_help():
    """Print help information about available commands."""
    print("\nAvailable commands:")
    print("  exit, quit    - Exit the program")
    print("  help          - Show this help message")
    print("\nTask examples:")
    print("  Create a new Python module with a function to calculate fibonacci numbers")
    print("  Fix the bug in src/utils.py where division by zero is not handled")
    print("  Refactor the DatabaseManager class to use connection pooling")
    print("  Add unit tests for the authentication module")


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments.
    
    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description="Local AI Development Environment - Autonomous code writing and editing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  python -m src.main
  
  # Execute single task
  python -m src.main --task "Create a new Python module for parsing JSON"
  
  # Use custom config file
  python -m src.main --config /path/to/config.yaml
  
  # Set log level to debug
  python -m src.main --log-level debug
        """
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version=f'Local AI Development Environment v{VERSION}'
    )
    
    parser.add_argument(
        '--task',
        type=str,
        help='Execute a single task and exit (if not provided, runs in interactive mode)'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        help='Path to configuration file (YAML or JSON). If not provided, uses default locations.'
    )
    
    parser.add_argument(
        '--log-level',
        type=str,
        choices=['debug', 'info', 'warning', 'error'],
        help='Set logging verbosity level (overrides config file)'
    )
    
    parser.add_argument(
        '--project-root',
        type=str,
        help='Override project root directory'
    )
    
    return parser.parse_args()


def main() -> int:
    """Main entry point for the application.
    
    Returns:
        Exit code (0 for success, non-zero for failure)
    
    Requirements:
    - 1.3: Initialize all components using local resources only
    - 15.6: Provide different log verbosity levels
    """
    args = parse_arguments()
    
    # Set up initial logging (may be reconfigured after loading config)
    logger = setup_logging(args.log_level or 'info')
    
    try:
        # Load configuration
        logger.info("Loading configuration...")
        config_manager = ConfigManager(config_path=args.config)
        
        try:
            config = config_manager.load_config()
            logger.info("✓ Configuration loaded")
        except ConfigurationError as e:
            logger.error(f"Configuration error: {e}")
            print(f"\n✗ Configuration error: {e}", file=sys.stderr)
            print("\nPlease check your configuration file or create one from config.example.yaml", file=sys.stderr)
            return 1
        
        # Override log level if specified on command line
        if args.log_level:
            config.log_level = args.log_level
            logger = setup_logging(config.log_level)
        else:
            # Reconfigure logging with config file settings
            logger = setup_logging(config.log_level)
        
        # Override project root if specified on command line
        if args.project_root:
            config.project_root = args.project_root
            logger.info(f"Using project root: {config.project_root}")
        
        # Initialize all system components
        try:
            task_executor, llm_interface, code_agent, context_manager = initialize_components(
                config, logger
            )
        except ModelUnavailableError as e:
            logger.error(str(e))
            print(f"\n✗ {e}", file=sys.stderr)
            print("\nPlease ensure your local LLM server is running:", file=sys.stderr)
            print(f"  Endpoint: {config.llm.endpoint}", file=sys.stderr)
            print(f"  Model: {config.llm.model_name}", file=sys.stderr)
            return 1
        except ConfigurationError as e:
            logger.error(f"Initialization error: {e}")
            print(f"\n✗ Initialization error: {e}", file=sys.stderr)
            return 1
        
        # Execute task or enter interactive mode
        if args.task:
            # Single task execution
            exit_code = execute_single_task(task_executor, args.task, logger)
            return exit_code
        else:
            # Interactive mode
            execute_task_interactive(task_executor, logger)
            return 0
            
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
        return 130  # Standard exit code for SIGINT
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        print(f"\n✗ Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
