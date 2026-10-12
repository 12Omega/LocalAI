"""Example usage of TaskExecutor for Local AI Development Environment.

This example demonstrates how to use the TaskExecutor to orchestrate
development tasks through the agent loop pattern.

The TaskExecutor coordinates:
- Local LLM Interface for planning and reflection
- Code Agent for file operations and code generation
- Context Manager for project analysis

To run this example, you need:
1. A local LLM running (e.g., Ollama with a code model)
2. A project directory to work in
"""

import logging
from pathlib import Path

from src.core.task_executor import TaskExecutor
from src.core.llm_interface import LocalLLMInterface
from src.core.models import LLMConfig, SystemConfig
from src.agents.code_agent import CodeAgent
from src.context.context_manager import ContextManager


def setup_logging():
    """Configure logging for the example."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def create_task_executor(project_root: str) -> TaskExecutor:
    """Create and configure a TaskExecutor instance.
    
    Args:
        project_root: Root directory of the project
        
    Returns:
        Configured TaskExecutor ready to execute tasks
    """
    # Configure local LLM
    llm_config = LLMConfig(
        endpoint="http://localhost:11434",  # Ollama default endpoint
        model_name="codellama:13b",  # Or another code-capable model
        temperature=0.2,
        max_tokens=4096,
        context_length=16384,
        backend_type="ollama"
    )
    
    # Create LLM interface
    llm_interface = LocalLLMInterface(llm_config)
    
    # Configure system
    system_config = SystemConfig(
        llm=llm_config,
        project_root=project_root,
        log_level="info",
        web_research_enabled=False,  # Disable for this example
        self_improvement_enabled=False,
        excluded_directories=[
            "node_modules", ".git", "__pycache__", 
            ".pytest_cache", "venv", ".venv", "build", "dist"
        ]
    )
    
    # Create components
    code_agent = CodeAgent(
        project_root=project_root,
        excluded_dirs=set(system_config.excluded_directories)
    )
    
    context_manager = ContextManager(config=system_config)
    
    # Scan project to build context
    print(f"Scanning project: {project_root}")
    context_manager.scan_project(project_root)
    print(f"Project scan complete")
    
    # Create TaskExecutor
    task_executor = TaskExecutor(
        llm_interface=llm_interface,
        code_agent=code_agent,
        context_manager=context_manager
    )
    
    return task_executor


def example_simple_task():
    """Example: Execute a simple file creation task."""
    print("\n" + "="*60)
    print("Example 1: Simple File Creation Task")
    print("="*60 + "\n")
    
    # Setup
    project_root = str(Path.cwd() / "example_project")
    Path(project_root).mkdir(exist_ok=True)
    
    setup_logging()
    
    try:
        executor = create_task_executor(project_root)
        
        # Execute task
        task_description = "Create a Python utility module called math_utils.py with basic arithmetic functions"
        
        print(f"\nExecuting task: {task_description}\n")
        
        result = executor.execute_task(task_description)
        
        # Display results
        print("\n" + "-"*60)
        print("Task Results:")
        print("-"*60)
        print(f"Success: {result.success}")
        print(f"Actions taken: {len(result.actions_taken)}")
        print(f"Files modified: {result.files_modified}")
        print(f"Tests passed: {result.tests_passed}")
        
        if result.error_message:
            print(f"Error: {result.error_message}")
        
        print("\nExecution Log:")
        for log_entry in result.execution_log:
            print(f"  {log_entry}")
        
    except Exception as e:
        print(f"Error: {e}")


def example_multi_step_task():
    """Example: Execute a multi-step development task."""
    print("\n" + "="*60)
    print("Example 2: Multi-Step Development Task")
    print("="*60 + "\n")
    
    # Setup
    project_root = str(Path.cwd() / "example_project")
    Path(project_root).mkdir(exist_ok=True)
    
    setup_logging()
    
    try:
        executor = create_task_executor(project_root)
        
        # Execute more complex task
        task_description = """
        Create a simple calculator module with the following:
        1. A Calculator class with methods for add, subtract, multiply, divide
        2. Error handling for division by zero
        3. Unit tests for all methods
        4. A main function that demonstrates usage
        """
        
        print(f"\nExecuting task: {task_description}\n")
        
        result = executor.execute_task(task_description)
        
        # Display results
        print("\n" + "-"*60)
        print("Task Results:")
        print("-"*60)
        print(f"Success: {result.success}")
        print(f"Actions taken: {len(result.actions_taken)}")
        print(f"Files modified: {result.files_modified}")
        print(f"Tests passed: {result.tests_passed}")
        
        if result.error_message:
            print(f"Error: {result.error_message}")
        
        print("\nActions Taken:")
        for i, action in enumerate(result.actions_taken, 1):
            print(f"  {i}. {action.action}: {action.rationale}")
        
    except Exception as e:
        print(f"Error: {e}")


def example_with_testing():
    """Example: Task that includes test creation and execution."""
    print("\n" + "="*60)
    print("Example 3: Task with Test Creation and Execution")
    print("="*60 + "\n")
    
    # Setup
    project_root = str(Path.cwd() / "example_project")
    Path(project_root).mkdir(exist_ok=True)
    
    setup_logging()
    
    try:
        executor = create_task_executor(project_root)
        
        # Task that explicitly requires tests
        task_description = """
        Create a string_utils.py module with functions:
        - reverse_string(s): returns reversed string
        - is_palindrome(s): checks if string is palindrome
        - count_vowels(s): counts vowels in string
        
        Create comprehensive unit tests and run them to verify correctness.
        """
        
        print(f"\nExecuting task: {task_description}\n")
        
        result = executor.execute_task(task_description)
        
        # Display results
        print("\n" + "-"*60)
        print("Task Results:")
        print("-"*60)
        print(f"Success: {result.success}")
        print(f"Files modified: {result.files_modified}")
        print(f"Tests passed: {result.tests_passed}")
        
        if result.test_results:
            print("\nTest Results:")
            for test_cmd, passed in executor.test_results.items():
                status = "✓ PASSED" if passed else "✗ FAILED"
                print(f"  {status}: {test_cmd}")
        
        print("\nExecution History:")
        print(f"  Total iterations: {executor.current_iteration}")
        print(f"  Total actions: {len(result.actions_taken)}")
        
    except Exception as e:
        print(f"Error: {e}")


def main():
    """Run all examples."""
    print("\n" + "="*60)
    print("TaskExecutor Usage Examples")
    print("Local AI Development Environment")
    print("="*60)
    
    print("\nNOTE: These examples require a local LLM to be running.")
    print("Start Ollama with a code model before running:")
    print("  ollama pull codellama:13b")
    print("  ollama serve")
    print("\n")
    
    # Run examples
    try:
        # Example 1: Simple task
        example_simple_task()
        
        # Example 2: Multi-step task
        example_multi_step_task()
        
        # Example 3: Task with testing
        example_with_testing()
        
    except KeyboardInterrupt:
        print("\n\nExamples interrupted by user.")
    except Exception as e:
        print(f"\n\nError running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
