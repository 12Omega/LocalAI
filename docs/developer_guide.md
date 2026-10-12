# Developer Guide

Welcome to the Local AI Development Environment developer guide. This document provides comprehensive information for developers who want to understand, contribute to, or extend the system.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Component Interactions](#component-interactions)
3. [API Documentation](#api-documentation)
4. [Contributing Guidelines](#contributing-guidelines)
5. [Testing Strategy](#testing-strategy)
6. [Development Workflow](#development-workflow)

## Architecture Overview

The Local AI Development Environment is an autonomous AI system that executes entirely on a local machine. It uses a modular architecture with clear separation of concerns:

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        User Interface                        │
│                          (CLI)                               │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                     Task Executor                            │
│  (Orchestrates agent loop: Plan → Execute → Observe)        │
└───┬──────────┬──────────┬──────────┬──────────┬────────────┘
    │          │          │          │          │
    ▼          ▼          ▼          ▼          ▼
┌───────┐ ┌────────┐ ┌─────────┐ ┌──────┐ ┌──────────────┐
│ Code  │ │Context │ │   Web   │ │ LLM  │ │     Self     │
│ Agent │ │Manager │ │Research │ │ I/F  │ │ Improvement  │
└───┬───┘ └────┬───┘ └────┬────┘ └──┬───┘ └──────┬───────┘
    │          │          │          │             │
    ▼          ▼          ▼          ▼             ▼
┌──────────────────────────────────────────────────────────┐
│            Local Resources (File System, LLM)            │
└──────────────────────────────────────────────────────────┘
```

### Core Components

**Task Executor** (`src/core/task_executor.py`)
- Central orchestrator that implements the agent loop pattern
- Plans tasks by breaking them into execution steps
- Executes steps using appropriate components
- Observes results and reflects on progress
- Iterates until task completion or failure

**Local LLM Interface** (`src/core/llm_interface.py`)
- Abstracts communication with local language models
- Supports multiple backends: Ollama, llama.cpp, OpenAI-compatible
- Handles tool calling protocol translation
- Implements retry logic and error handling

**Code Agent** (`src/agents/code_agent.py`)
- Generates new code following project conventions
- Edits existing code with precise modifications
- Analyzes code style and structure
- Integrates with File Operations, Code Search, and Command Executor

**Context Manager** (`src/context/context_manager.py`)
- Analyzes project structure and technology stack
- Builds dependency graphs between components
- Identifies relevant files for tasks
- Tracks project changes incrementally

**Web Research Module** (`src/web/web_research.py`)
- Searches web for documentation and information
- Fetches and extracts content from web pages
- Prioritizes official documentation sources
- Provides attribution for sources

**Self-Improvement Engine** (`src/self_improvement/self_improvement.py`)
- Analyzes system codebase for improvements
- Proposes and implements capability enhancements
- Tests improvements with automatic rollback on failure
- Maintains audit trail of modifications

### Supporting Components

**File Operations** (`src/agents/file_operations.py`)
- Handles all file system operations (create, read, update, delete, move)
- Updates import references when moving files
- Validates file operations and provides detailed error messages

**Code Search** (`src/agents/code_search.py`)
- Searches code by text pattern, filename, or symbol
- Supports regex patterns and directory exclusions
- Returns results with file paths, line numbers, and context

**Command Executor** (`src/agents/command_executor.py`)
- Executes shell commands with output capture
- Handles synchronous and asynchronous command execution
- Provides timeout and working directory control

**AST Parser** (`src/context/ast_parser.py`)
- Parses source code using Tree-sitter
- Extracts symbols (functions, classes, methods)
- Identifies imports and dependencies
- Supports Python, JavaScript, TypeScript, Java, Go, Rust, C++

## Component Interactions

### Task Execution Flow

```
1. User provides task description
   │
   ▼
2. Task Executor uses LLM to create ExecutionPlan
   │
   ▼
3. For each ExecutionStep in plan:
   │
   ├──▶ Task Executor routes step to appropriate component
   │    (Code Agent, Context Manager, Web Research, etc.)
   │
   ├──▶ Component executes step and returns OperationResult
   │
   ├──▶ Task Executor observes result
   │
   └──▶ LLM reflects on progress and decides next action
        │
        ├─ Success: Continue to next step
        ├─ Need more work: Generate additional step
        └─ Complete: Return TaskResult
```

### Code Generation Flow

```
1. Task Executor requests code generation
   │
   ▼
2. Code Agent requests relevant context
   │
   ▼
3. Context Manager analyzes project:
   ├─ Identifies relevant files
   ├─ Extracts dependency information
   └─ Detects code style conventions
   │
   ▼
4. Code Agent uses LLM to generate code with context
   │
   ▼
5. File Operations writes generated code to file system
   │
   ▼
6. Task Executor verifies code (runs tests, checks syntax)
```

### Self-Improvement Flow

```
1. Self-Improvement Engine analyzes system code
   │
   ▼
2. Identifies improvement opportunity
   │
   ▼
3. Uses LLM to propose specific changes
   │
   ▼
4. Creates backup of affected files
   │
   ▼
5. Implements changes to system code
   │
   ▼
6. Runs comprehensive test suite
   │
   ├─ Tests pass: Keep improvement, log in audit trail
   └─ Tests fail: Rollback changes, log failure
```

## API Documentation

### Task Executor API

**Class**: `TaskExecutor`

**Constructor**:
```python
def __init__(
    self,
    llm_interface: LocalLLMInterface,
    code_agent: CodeAgent,
    context_manager: ContextManager,
    web_research: Optional[WebResearchModule] = None,
    logger: Optional[logging.Logger] = None
)
```

**Primary Methods**:

```python
def execute_task(self, task_description: str) -> TaskResult:
    """
    Execute a complete development task from description to verified implementation.
    
    Args:
        task_description: Natural language description of the task
        
    Returns:
        TaskResult containing:
            - success: bool indicating task completion
            - actions_taken: List of ExecutionSteps performed
            - files_modified: List of file paths changed
            - tests_passed: bool indicating test status
            - error_message: Optional error description
            - execution_log: List of log messages
    """
```

```python
def plan_task(self, task_description: str) -> Optional[ExecutionPlan]:
    """
    Break task into executable steps using LLM.
    
    Args:
        task_description: Natural language task description
        
    Returns:
        ExecutionPlan with steps, complexity estimate, and required tools
        Returns None if planning fails
    """
```

```python
def execute_step(self, step: ExecutionStep) -> OperationResult:
    """
    Execute a single step and return results.
    
    Args:
        step: ExecutionStep with action and parameters
        
    Returns:
        OperationResult with success status, output, and error information
    """
```

```python
def should_continue(self, results: List[Dict[str, Any]]) -> bool:
    """
    Determine if task execution should continue.
    
    Args:
        results: List of execution results from previous steps
        
    Returns:
        True if more work needed, False if task complete
    """
```

### Local LLM Interface API

**Class**: `LocalLLMInterface`

**Constructor**:
```python
def __init__(self, config: LLMConfig):
    """
    Initialize LLM interface with configuration.
    
    Args:
        config: LLMConfig with endpoint, model name, temperature, etc.
    """
```

**Methods**:

```python
def generate(self, prompt: str, tools: Optional[List[Tool]] = None) -> LLMResponse:
    """
    Generate response from LLM with optional tool definitions.
    
    Args:
        prompt: Input text for the model
        tools: Optional list of Tool definitions for function calling
        
    Returns:
        LLMResponse with text response and optional tool calls
        
    Raises:
        ModelUnavailableError: If LLM endpoint is unreachable
        LLMTimeoutError: If request exceeds timeout
        InvalidResponseError: If response format is invalid
    """
```

```python
def stream_generate(self, prompt: str) -> Iterator[str]:
    """
    Stream response tokens as they're generated.
    
    Args:
        prompt: Input text for the model
        
    Yields:
        Response tokens as strings
    """
```

```python
def encode(self, text: str) -> List[int]:
    """
    Tokenize text for context length calculation.
    
    Args:
        text: Text to tokenize
        
    Returns:
        List of token IDs
    """
```

### Code Agent API

**Class**: `CodeAgent`

**Constructor**:
```python
def __init__(
    self,
    file_ops: FileOperations,
    code_search: CodeSearch,
    command_executor: CommandExecutor,
    llm_interface: LocalLLMInterface,
    logger: Optional[logging.Logger] = None
)
```

**Methods**:

```python
def create_code(self, task_description: str, context: Dict[str, Any]) -> OperationResult:
    """
    Generate new code for a task.
    
    Args:
        task_description: What code to create
        context: Dict with:
            - relevant_files: List of related file paths
            - project_info: ProjectContext
            - code_style: Style conventions detected
            
    Returns:
        OperationResult with:
            - success: bool
            - output: Generated code content
            - files_created: List of new file paths
            - error_message: Optional error description
    """
```

```python
def edit_code(
    self,
    file_path: str,
    modification_request: str,
    context: Dict[str, Any]
) -> OperationResult:
    """
    Edit existing code file.
    
    Args:
        file_path: Path to file to edit
        modification_request: Desired changes
        context: Dict with relevant code context
        
    Returns:
        OperationResult with success status and changes made
    """
```

### Context Manager API

**Class**: `ContextManager`

**Constructor**:
```python
def __init__(
    self,
    ast_parser: ASTParser,
    code_search: CodeSearch,
    logger: Optional[logging.Logger] = None
)
```

**Methods**:

```python
def scan_project(self, root_path: str) -> ProjectContext:
    """
    Perform initial project analysis.
    
    Args:
        root_path: Project root directory
        
    Returns:
        ProjectContext with:
            - languages: Detected programming languages
            - frameworks: Identified frameworks
            - file_tree: Project structure
            - dependency_graph: Import relationships
            - key_files: Important project files
    """
```

```python
def get_relevant_files(self, task_description: str) -> List[str]:
    """
    Identify files relevant to a task.
    
    Args:
        task_description: Natural language task description
        
    Returns:
        List of file paths likely related to the task
    """
```

```python
def get_dependencies(self, file_path: str) -> DependencyGraph:
    """
    Build dependency graph for a file.
    
    Args:
        file_path: Path to analyze
        
    Returns:
        DependencyGraph showing imports and dependents
    """
```

```python
def analyze_code(self, file_path: str) -> CodeAnalysis:
    """
    Extract structure and symbols from code file.
    
    Args:
        file_path: Path to analyze
        
    Returns:
        CodeAnalysis with:
            - language: Detected language
            - imports: Import statements
            - symbols: Functions and classes defined
            - dependencies: Other files referenced
            - structure: High-level outline
    """
```

```python
def detect_language_stack(self) -> LanguageStack:
    """
    Identify languages and frameworks in project.
    
    Returns:
        LanguageStack with primary language, all languages, and frameworks
    """
```

### File Operations API

**Class**: `FileOperations`

**Methods**:

```python
def create_file(self, path: str, content: str) -> OperationResult:
    """Create new file with content."""
```

```python
def read_file(self, path: str) -> str:
    """Read and return file contents."""
```

```python
def update_file(self, path: str, content: str) -> OperationResult:
    """Replace entire file content."""
```

```python
def patch_file(self, path: str, edits: List[Edit]) -> OperationResult:
    """Apply precise edits to specific line ranges."""
```

```python
def delete_file(self, path: str) -> OperationResult:
    """Delete a file."""
```

```python
def move_file(self, src: str, dst: str) -> OperationResult:
    """Move or rename file and update references."""
```

### Code Search API

**Class**: `CodeSearch`

**Methods**:

```python
def search_text(self, pattern: str, file_pattern: str = "*") -> List[SearchResult]:
    """
    Search for text pattern across files.
    
    Args:
        pattern: Regex pattern to search for
        file_pattern: Glob pattern for files to search
        
    Returns:
        List of SearchResult with file_path, line_number, match_text, context
    """
```

```python
def search_files(self, name_pattern: str) -> List[str]:
    """
    Find files matching name pattern.
    
    Args:
        name_pattern: Glob pattern for filenames
        
    Returns:
        List of matching file paths
    """
```

```python
def find_symbol(self, symbol_name: str) -> List[SymbolLocation]:
    """
    Find function/class definitions.
    
    Args:
        symbol_name: Name of symbol to locate
        
    Returns:
        List of SymbolLocation with file_path, line_number, symbol_type
    """
```

### Command Executor API

**Class**: `CommandExecutor`

**Methods**:

```python
def execute(self, command: str, cwd: str = None, timeout: int = 60) -> CommandResult:
    """
    Execute shell command and capture output.
    
    Args:
        command: Shell command to run
        cwd: Working directory (defaults to current)
        timeout: Timeout in seconds
        
    Returns:
        CommandResult with:
            - returncode: Exit code
            - stdout: Standard output
            - stderr: Standard error
            - success: True if returncode == 0
    """
```

```python
def execute_async(self, command: str, cwd: str = None) -> AsyncCommandHandle:
    """
    Execute long-running command asynchronously.
    
    Args:
        command: Shell command to run
        cwd: Working directory
        
    Returns:
        AsyncCommandHandle for monitoring progress
    """
```

### Web Research Module API

**Class**: `WebResearchModule`

**Methods**:

```python
def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
    """
    Search web for information.
    
    Args:
        query: Search query
        max_results: Maximum number of results
        
    Returns:
        List of SearchResult with title, url, snippet, domain
    """
```

```python
def fetch_page(self, url: str) -> WebPage:
    """
    Fetch and parse web page.
    
    Args:
        url: URL to fetch
        
    Returns:
        WebPage with content, code_examples, title
    """
```

```python
def extract_code_examples(self, content: str) -> List[CodeExample]:
    """
    Extract code blocks from HTML/Markdown.
    
    Args:
        content: HTML or Markdown content
        
    Returns:
        List of CodeExample with code, language, context
    """
```

### Self-Improvement Engine API

**Class**: `SelfImprovementEngine`

**Methods**:

```python
def analyze_system(self) -> List[ImprovementOpportunity]:
    """Analyze system codebase for improvement opportunities."""
```

```python
def propose_improvement(self, opportunity: ImprovementOpportunity) -> ImprovementProposal:
    """Generate specific code changes for improvement."""
```

```python
def implement_improvement(self, proposal: ImprovementProposal) -> ImplementationResult:
    """Apply improvement to system code."""
```

```python
def test_improvement(self) -> TestResult:
    """Verify improvement works correctly."""
```

```python
def revert_improvement(self, proposal: ImprovementProposal) -> None:
    """Rollback improvement if it reduces effectiveness."""
```

## Contributing Guidelines

We welcome contributions to the Local AI Development Environment! This section outlines how to contribute effectively.

### Getting Started

1. **Fork the repository** and clone your fork locally
2. **Set up the development environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```
3. **Run the test suite** to ensure everything works:
   ```bash
   pytest
   ```

### Development Workflow

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following the code style guidelines below

3. **Write tests** for your changes:
   - Property tests for deterministic logic
   - Unit tests for specific examples and edge cases
   - Integration tests for component interactions

4. **Run tests locally**:
   ```bash
   pytest tests/
   ```

5. **Commit your changes** with clear, descriptive messages:
   ```bash
   git commit -m "Add feature: description of what you added"
   ```

6. **Push to your fork** and create a pull request

### Code Style Guidelines

**Python Style**:
- Follow PEP 8 style guide
- Use type hints for all function signatures
- Maximum line length: 100 characters
- Use descriptive variable names
- Add docstrings to all public classes and methods

**Code Organization**:
- Keep functions focused on a single responsibility
- Limit function complexity (aim for < 15 lines per function)
- Use meaningful abstractions and avoid duplication
- Organize imports: standard library, third-party, local

**Example**:
```python
def search_text(
    self,
    pattern: str,
    file_pattern: str = "*",
    exclude_dirs: Optional[List[str]] = None
) -> List[SearchResult]:
    """
    Search for text pattern across files using regex.
    
    Args:
        pattern: Regex pattern to search for
        file_pattern: Glob pattern for files to include
        exclude_dirs: Directories to exclude from search
        
    Returns:
        List of SearchResult with file path, line number, and match text
        
    Raises:
        ValueError: If pattern is invalid regex
    """
    # Implementation here
```

**Error Handling**:
- Use specific exception types
- Provide descriptive error messages
- Include context in error messages (file paths, line numbers, etc.)
- Log errors with appropriate severity

**Logging**:
- Use the provided logger instance
- Log at appropriate levels:
  - DEBUG: Detailed diagnostic information
  - INFO: General informational messages
  - WARNING: Unexpected but recoverable situations
  - ERROR: Error conditions that prevent operation completion
- Include context in log messages

### Testing Guidelines

**Property-Based Tests**:
- Use `hypothesis` for property tests
- Set minimum 100 iterations: `@given(st.text())` with `@settings(max_examples=100)`
- Test universal properties that should hold for all inputs
- Tag tests with feature and property information

**Unit Tests**:
- Test specific examples and edge cases
- Use descriptive test names: `test_search_finds_pattern_in_file()`
- Arrange-Act-Assert pattern
- Mock external dependencies (LLM, file system, network)

**Integration Tests**:
- Test component interactions
- Use temporary directories for file system tests
- Clean up resources after tests

**Test Organization**:
```
tests/
├── properties/       # Property-based tests
├── unit/            # Unit tests
├── integration/     # Integration tests
├── system/          # End-to-end tests
└── fixtures/        # Test data and mocks
```

### Pull Request Guidelines

**Before Submitting**:
- Ensure all tests pass
- Add tests for new functionality
- Update documentation if needed
- Run linter: `pylint src/`
- Check type hints: `mypy src/`

**PR Description**:
- Describe what the PR does
- Reference related issues
- List breaking changes if any
- Provide testing instructions

**PR Size**:
- Keep PRs focused and reasonably sized
- Large changes should be broken into multiple PRs
- Each PR should be independently reviewable

**Code Review Process**:
- Address reviewer feedback
- Keep discussions constructive and professional
- Update PR based on feedback
- Maintainer will merge when ready

### Adding New Components

When adding a new component to the system:

1. **Design the interface** first:
   - Define clear input/output contracts
   - Document expected behavior
   - Consider error cases

2. **Implement the component**:
   - Follow existing architectural patterns
   - Use dependency injection for testability
   - Add comprehensive logging

3. **Write tests**:
   - Property tests for core logic
   - Unit tests for methods
   - Integration tests with other components

4. **Update documentation**:
   - Add API documentation to this guide
   - Update architecture diagrams if needed
   - Add usage examples

5. **Integrate with Task Executor**:
   - Add execution handler method
   - Update step routing logic
   - Test end-to-end workflow

### Reporting Issues

**Bug Reports**:
- Use issue template
- Provide minimal reproduction steps
- Include system information (OS, Python version, LLM backend)
- Attach relevant logs
- Describe expected vs actual behavior

**Feature Requests**:
- Describe the use case
- Explain why the feature is valuable
- Suggest possible implementation approach
- Consider backward compatibility

### Community Guidelines

- Be respectful and inclusive
- Welcome newcomers and help them contribute
- Provide constructive feedback
- Focus on code and ideas, not people
- Follow the project's code of conduct

## Testing Strategy

The Local AI Development Environment uses a comprehensive testing strategy that combines property-based testing with traditional unit and integration tests.

### Testing Philosophy

1. **Property tests verify universal correctness** across many randomized inputs
2. **Unit tests verify specific examples** and edge cases
3. **Integration tests verify component interactions**
4. **System tests verify end-to-end workflows**

### Test Types

#### Property-Based Tests

Property tests use the `hypothesis` library to verify that certain properties hold true across a wide range of inputs.

**Location**: `tests/properties/`

**Framework**: pytest + hypothesis

**Configuration**:
```python
from hypothesis import given, settings, strategies as st

@given(st.text(), st.text())
@settings(max_examples=100)  # Minimum 100 iterations
def test_file_roundtrip(self, path, content):
    """Property 8: Writing and reading returns identical content"""
```

**Properties Implemented**:
1. HTML Content Extraction (Property 1)
2. Documentation Source Prioritization (Property 2)
3. Dependency Graph Accuracy (Property 3)
4. Framework Detection Consistency (Property 4)
5. Code Search with Exclusions (Property 5)
6. Symbol Extraction Completeness (Property 6)
7. Search Result Structure (Property 7)
8. File Content Round-Trip (Property 8)
9. Reference Updates on File Move (Property 9)
10. Command Argument Formatting (Property 10)
11. Primary Language Detection (Property 11)

#### Unit Tests

Unit tests verify specific functionality in isolation using mocks for dependencies.

**Location**: `tests/unit/`

**Example**:
```python
def test_search_text_finds_pattern(self):
    """Test that search_text finds expected pattern in file."""
    # Arrange
    search = CodeSearch(excluded_dirs=['.git'])
    
    # Act
    results = search.search_text(r'def\s+\w+', '*.py')
    
    # Assert
    assert len(results) > 0
    assert all(r.file_path.endswith('.py') for r in results)
    assert all('def' in r.match_text for r in results)
```

**Coverage Goals**:
- 90%+ line coverage for individual components
- 100% coverage of error handling paths
- All edge cases documented and tested

#### Integration Tests

Integration tests verify that components work together correctly.

**Location**: `tests/integration/`

**Example**:
```python
def test_task_executor_with_code_agent(mock_llm):
    """Test Task Executor coordinating Code Agent."""
    # Arrange
    executor = TaskExecutor(mock_llm, code_agent, context_manager)
    
    # Act
    result = executor.execute_task("Create a Python function to sort numbers")
    
    # Assert
    assert result.success
    assert len(result.files_modified) > 0
    assert result.tests_passed
```

#### System Tests

System tests verify complete workflows end-to-end.

**Location**: `tests/system/`

**Examples**:
- Create Python module with tests
- Create JavaScript React component
- Debug failing test and fix code
- Refactor code while maintaining tests
- Research web documentation and implement API client
- Self-improvement cycle

### Running Tests

**Run all tests**:
```bash
pytest
```

**Run specific test category**:
```bash
pytest tests/properties/     # Property tests only
pytest tests/unit/          # Unit tests only
pytest tests/integration/   # Integration tests only
pytest tests/system/        # System tests only
```

**Run with coverage**:
```bash
pytest --cov=src --cov-report=html
```

**Run specific test file**:
```bash
pytest tests/properties/test_file_roundtrip.py
```

**Run specific test**:
```bash
pytest tests/unit/test_code_search.py::test_search_text_finds_pattern
```

**Run with verbose output**:
```bash
pytest -v
```

**Run with logging output**:
```bash
pytest -s --log-cli-level=DEBUG
```

### Test Configuration

**pytest.ini**:
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --strict-markers
    --tb=short
markers =
    property: Property-based tests
    unit: Unit tests
    integration: Integration tests
    system: System tests
    slow: Tests that take significant time
```

### Mocking Strategy

**LLM Mocking**:
Use `pytest-mock` to mock LLM responses for predictable testing:
```python
@pytest.fixture
def mock_llm(mocker):
    mock = mocker.Mock(spec=LocalLLMInterface)
    mock.generate.return_value = LLMResponse(
        text="Generated code here",
        tool_calls=[]
    )
    return mock
```

**File System Mocking**:
Use temporary directories for file operations:
```python
@pytest.fixture
def temp_project(tmp_path):
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    return project_dir
```

**Web Mocking**:
Use `responses` library to mock HTTP requests:
```python
import responses

@responses.activate
def test_web_fetch():
    responses.add(
        responses.GET,
        'http://example.com',
        body='<html><body>Test</body></html>',
        status=200
    )
    # Test code here
```

### Continuous Integration

Tests run automatically on:
- Every commit to main branch
- Every pull request
- Nightly builds with extended test suite

**CI Configuration** (.github/workflows/test.yml):
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - run: pip install -r requirements.txt
      - run: pip install -r requirements-dev.txt
      - run: pytest --cov=src --cov-report=xml
      - uses: codecov/codecov-action@v2
```

### Test Data and Fixtures

**Fixture Organization**:
```
tests/fixtures/
├── sample_projects/
│   ├── python_project/
│   ├── javascript_project/
│   └── multi_language_project/
├── mock_llm_responses/
│   ├── code_generation.json
│   └── task_planning.json
└── mock_web_content/
    ├── official_docs.html
    └── code_examples.html
```

**Loading Fixtures**:
```python
@pytest.fixture
def sample_python_project():
    fixture_path = Path(__file__).parent / 'fixtures' / 'sample_projects' / 'python_project'
    return fixture_path
```

### Performance Testing

**Measure operation latency**:
```python
import time

def test_search_performance():
    start = time.time()
    results = code_search.search_text(pattern, '*.py')
    duration = time.time() - start
    assert duration < 1.0  # Should complete within 1 second
```

**Test with large codebases**:
- 100 files
- 1,000 files
- 10,000 files

### Testing Best Practices

1. **Test behavior, not implementation**: Focus on what the code does, not how
2. **Use descriptive test names**: `test_search_excludes_gitignored_directories()`
3. **One assertion per test** (when practical)
4. **Arrange-Act-Assert pattern**: Clear test structure
5. **Test edge cases**: Empty inputs, very large inputs, invalid inputs
6. **Mock external dependencies**: LLM, network, file system (when appropriate)
7. **Clean up resources**: Use fixtures with teardown
8. **Keep tests fast**: Unit tests should run in milliseconds
9. **Make tests deterministic**: No random failures
10. **Write tests first** (TDD) when adding new features

## Development Workflow

### Setting Up Development Environment

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd local-ai-dev-environment
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

4. **Configure local LLM**:
   ```bash
   cp config.example.yaml config.yaml
   # Edit config.yaml with your LLM endpoint
   ```

5. **Run tests to verify setup**:
   ```bash
   pytest
   ```

### Daily Development Workflow

1. **Update main branch**:
   ```bash
   git checkout main
   git pull origin main
   ```

2. **Create feature branch**:
   ```bash
   git checkout -b feature/my-feature
   ```

3. **Make changes iteratively**:
   - Write failing test
   - Implement feature
   - Make test pass
   - Refactor if needed
   - Commit

4. **Run tests frequently**:
   ```bash
   pytest tests/unit/  # Quick unit tests
   pytest              # All tests before committing
   ```

5. **Commit with clear messages**:
   ```bash
   git add <files>
   git commit -m "Add feature: clear description"
   ```

6. **Push and create PR**:
   ```bash
   git push origin feature/my-feature
   # Create PR on GitHub/GitLab
   ```

### Debugging Tips

**Enable debug logging**:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Use pytest debugger**:
```bash
pytest --pdb  # Drop into debugger on failure
pytest -x     # Stop on first failure
```

**Inspect LLM prompts and responses**:
```python
llm_interface.logger.setLevel(logging.DEBUG)  # Logs all LLM interactions
```

**Use temporary breakpoints**:
```python
import pdb; pdb.set_trace()  # Classic Python debugger
breakpoint()                 # Python 3.7+ built-in
```

### Code Quality Tools

**Linting**:
```bash
pylint src/
flake8 src/
```

**Type checking**:
```bash
mypy src/
```

**Code formatting**:
```bash
black src/ tests/     # Auto-format code
isort src/ tests/     # Sort imports
```

**Security scanning**:
```bash
bandit -r src/        # Security issue detection
```

### Documentation Updates

When adding features, update:
- API documentation in this file
- Docstrings in code
- README.md if user-facing changes
- Architecture diagrams if structure changes

### Release Process

1. Update version in `setup.py`
2. Update CHANGELOG.md
3. Run full test suite
4. Create release branch
5. Tag release
6. Build and publish (if applicable)

---

## Additional Resources

- **Design Document**: See `design.md` for detailed architecture and design decisions
- **Requirements Document**: See `requirements.md` for functional requirements
- **Configuration Guide**: See `docs/configuration.md` for setup details
- **Self-Improvement Details**: See `docs/self_improvement_implementation.md`

## Getting Help

- Check existing documentation
- Search closed issues for similar problems
- Open an issue with details
- Join community discussions (if applicable)

## License

See LICENSE file in repository root.
