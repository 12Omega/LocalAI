# Contributing to Local AI Development Environment

Thank you for your interest in contributing to the Local AI Development Environment! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)
- [Pull Request Process](#pull-request-process)
- [Issue Reporting](#issue-reporting)
- [Community](#community)

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive experience for everyone. We pledge to:

- Use welcoming and inclusive language
- Respect differing viewpoints and experiences
- Accept constructive criticism gracefully
- Focus on what is best for the community
- Show empathy towards other community members

### Our Standards

**Positive behavior includes**:
- Being respectful and professional
- Providing constructive feedback
- Helping newcomers learn and contribute
- Celebrating others' contributions
- Staying focused on technical merit

**Unacceptable behavior includes**:
- Harassment, discrimination, or personal attacks
- Trolling, insulting comments, or inflammatory remarks
- Publishing others' private information
- Any conduct that would be inappropriate in a professional setting

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- A local LLM (Ollama recommended for testing)
- Basic understanding of AI agents and language models

### Setting Up Development Environment

1. **Fork and clone the repository**:
   ```bash
   git fork <repository-url>
   git clone https://github.com/YOUR_USERNAME/local-ai-dev-environment.git
   cd local-ai-dev-environment
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   
   # On Windows:
   venv\Scripts\activate
   
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   # Core dependencies
   pip install -r requirements.txt
   
   # Development dependencies (linting, testing, etc.)
   pip install -r requirements-dev.txt
   ```

4. **Set up pre-commit hooks** (optional but recommended):
   ```bash
   pre-commit install
   ```

5. **Verify setup**:
   ```bash
   # Run tests
   pytest
   
   # Run linter
   pylint src/
   
   # Check type hints
   mypy src/
   ```

### Project Structure

```
local-ai-dev-environment/
├── src/                    # Source code
│   ├── core/              # Core models and utilities
│   ├── agents/            # Agent components
│   ├── context/           # Context management
│   ├── web/               # Web research
│   └── self_improvement/  # Self-improvement engine
├── tests/                 # Test suite
│   ├── properties/        # Property-based tests
│   ├── unit/             # Unit tests
│   ├── integration/      # Integration tests
│   └── system/           # End-to-end tests
├── docs/                  # Documentation
├── examples/              # Example code and projects
└── requirements.txt       # Dependencies
```

## Development Workflow

### Creating a Feature Branch

1. **Ensure your main branch is up to date**:
   ```bash
   git checkout main
   git pull upstream main
   ```

2. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```
   
   Use prefixes:
   - `feature/` for new features
   - `bugfix/` for bug fixes
   - `docs/` for documentation changes
   - `refactor/` for code refactoring
   - `test/` for test additions/improvements

### Making Changes

1. **Write your code** following the [Coding Standards](#coding-standards)

2. **Add tests** for your changes:
   - Property tests for universal correctness properties
   - Unit tests for specific functionality
   - Integration tests for component interactions

3. **Run tests locally**:
   ```bash
   # Run all tests
   pytest
   
   # Run specific test category
   pytest tests/unit/
   
   # Run with coverage
   pytest --cov=src --cov-report=html
   ```

4. **Lint your code**:
   ```bash
   pylint src/
   flake8 src/
   ```

5. **Check type hints**:
   ```bash
   mypy src/
   ```

6. **Update documentation** if needed

### Committing Changes

1. **Stage your changes**:
   ```bash
   git add <files>
   ```

2. **Commit with descriptive message**:
   ```bash
   git commit -m "Add feature: descriptive message"
   ```
   
   **Commit message format**:
   ```
   <type>: <subject>
   
   <body>
   
   <footer>
   ```
   
   Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`
   
   Example:
   ```
   feat: Add support for Rust language parsing
   
   - Integrate Tree-sitter Rust grammar
   - Add Rust file extension mapping
   - Implement Rust-specific symbol extraction
   - Add unit tests for Rust parsing
   
   Closes #123
   ```

3. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

## Coding Standards

### Python Style Guide

We follow **PEP 8** with some specific guidelines:

**General**:
- Maximum line length: 100 characters
- Use 4 spaces for indentation (no tabs)
- Use UTF-8 encoding
- Use Unix line endings (LF)

**Naming Conventions**:
```python
# Variables and functions: snake_case
user_name = "John"
def calculate_total(): pass

# Classes: PascalCase
class TaskExecutor: pass

# Constants: UPPER_SNAKE_CASE
MAX_RETRIES = 3

# Private members: leading underscore
def _internal_method(): pass
self._private_attribute = value
```

**Type Hints**:
All functions must have type hints:
```python
def search_text(
    self,
    pattern: str,
    file_pattern: str = "*",
    exclude_dirs: Optional[List[str]] = None
) -> List[SearchResult]:
    """Search for text pattern across files."""
    pass
```

**Docstrings**:
Use Google-style docstrings:
```python
def execute_task(self, task_description: str) -> TaskResult:
    """Execute a complete development task.
    
    Args:
        task_description: Natural language description of the task
        
    Returns:
        TaskResult containing success status, actions taken, and logs
        
    Raises:
        TaskExecutionError: If task cannot be completed
        LLMError: If LLM becomes unavailable
        
    Example:
        >>> executor = TaskExecutor(llm, code_agent, context_manager)
        >>> result = executor.execute_task("Create a Python calculator module")
        >>> print(result.success)
        True
    """
    pass
```

**Imports**:
Organize imports in three groups:
```python
# Standard library
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Third-party
import requests
from tree_sitter import Language

# Local
from src.core.models import TaskResult
from src.agents.file_operations import FileOperations
```

**Error Handling**:
```python
# Specific exception types
try:
    result = risky_operation()
except FileNotFoundError as e:
    logger.error(f"File not found: {e.filename}")
    raise
except PermissionError as e:
    logger.error(f"Permission denied: {e}")
    return OperationResult(success=False, error_message=str(e))

# Provide context in error messages
raise ValueError(f"Invalid pattern '{pattern}' at line {line_num}: {reason}")
```

**Logging**:
```python
# Use appropriate log levels
logger.debug("Detailed diagnostic information")
logger.info("General informational message")
logger.warning("Unexpected but recoverable situation")
logger.error("Error that prevented operation completion")

# Include context
logger.info(f"Scanning project: {project_root}")
logger.error(f"Failed to parse {file_path}: {error}")
```

### Code Organization

**Keep functions focused**:
```python
# Bad: Function does too much
def process_task(task):
    # 100 lines of code...
    pass

# Good: Break into smaller functions
def process_task(task):
    plan = create_plan(task)
    results = execute_plan(plan)
    return summarize_results(results)
```

**Limit function complexity**:
- Aim for < 15 lines per function
- Maximum cyclomatic complexity: 10
- If function is complex, break it down

**Use meaningful names**:
```python
# Bad
def f(x, y):
    return x + y

# Good
def calculate_total_price(base_price: float, tax: float) -> float:
    return base_price + tax
```

**Avoid duplication**:
```python
# Bad: Duplicated logic
def process_python_file(path):
    # 20 lines of parsing...
    pass

def process_java_file(path):
    # 20 similar lines of parsing...
    pass

# Good: Extract common logic
def process_file(path, language):
    ast = parse_file(path, language)
    return extract_symbols(ast)
```

## Testing Guidelines

### Test Categories

We use four types of tests:

1. **Property-Based Tests** (`tests/properties/`)
   - Verify universal correctness properties
   - Use Hypothesis framework
   - Minimum 100 iterations per test

2. **Unit Tests** (`tests/unit/`)
   - Test individual components in isolation
   - Use mocks for dependencies
   - Fast execution (< 1 second)

3. **Integration Tests** (`tests/integration/`)
   - Test component interactions
   - Use minimal mocking
   - Moderate execution time

4. **System Tests** (`tests/system/`)
   - End-to-end workflow testing
   - Use real or mock LLMs
   - Slower execution

### Writing Property Tests

```python
from hypothesis import given, settings, strategies as st
import pytest

class TestFileOperations:
    @given(st.text(), st.text())
    @settings(max_examples=100)
    def test_file_roundtrip_property(self, path, content):
        """Property 8: Writing and reading returns identical content.
        
        **Validates: Requirements 9.2**
        """
        # Arrange
        file_ops = FileOperations()
        
        # Act
        file_ops.create_file(path, content)
        read_content = file_ops.read_file(path)
        
        # Assert
        assert read_content == content
```

### Writing Unit Tests

```python
import pytest
from unittest.mock import Mock, patch

class TestCodeSearch:
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
    
    def test_search_handles_invalid_regex(self):
        """Test that invalid regex raises ValueError."""
        # Arrange
        search = CodeSearch()
        
        # Act & Assert
        with pytest.raises(ValueError, match="Invalid regex"):
            search.search_text(r'[invalid', '*.py')
```

### Test Fixtures

```python
@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project structure."""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    
    # Create sample files
    (project_dir / "main.py").write_text("def main(): pass")
    (project_dir / "utils.py").write_text("def helper(): pass")
    
    return project_dir

@pytest.fixture
def mock_llm():
    """Mock LLM interface for testing."""
    llm = Mock(spec=LocalLLMInterface)
    llm.generate.return_value = LLMResponse(
        text="Generated response",
        tool_calls=[]
    )
    return llm
```

### Test Coverage

- **Minimum coverage**: 80% for all code
- **Target coverage**: 90% for core components
- **Required coverage**: 100% for error handling paths

```bash
# Generate coverage report
pytest --cov=src --cov-report=html

# View report
open htmlcov/index.html
```

### Test Naming

```python
# Unit test names
def test_<what>_<when>_<expected_result>():
    pass

# Examples:
def test_search_text_with_valid_pattern_returns_matches():
    pass

def test_file_operations_when_permission_denied_raises_error():
    pass

# Property test names
def test_<component>_<property_name>_property():
    pass

# Examples:
def test_file_roundtrip_property():
    pass

def test_dependency_graph_accuracy_property():
    pass
```

## Documentation

### Code Documentation

**Document all public APIs**:
```python
class TaskExecutor:
    """Orchestrates task execution through the agent loop.
    
    The TaskExecutor coordinates all system components to complete
    development tasks autonomously. It implements the plan-execute-
    observe-reflect agent loop pattern.
    
    Attributes:
        llm_interface: Interface to local language model
        code_agent: Agent for code operations
        context_manager: Manager for project context
        
    Example:
        >>> executor = TaskExecutor(llm, code_agent, context_manager)
        >>> result = executor.execute_task("Create a calculator module")
        >>> print(result.success)
        True
    """
```

**Update docs when changing APIs**:
- Update docstrings
- Update `docs/developer_guide.md` API section
- Update relevant examples

### Writing Documentation

Documentation files use Markdown:

**File headers**:
```markdown
# Title

Brief description of the document.

## Table of Contents

- [Section 1](#section-1)
- [Section 2](#section-2)
```

**Code examples**:
```markdown
Use fenced code blocks with language specifiers:

\`\`\`python
def example():
    pass
\`\`\`
```

**Links**:
```markdown
- Internal: [Architecture](docs/architecture.md)
- External: [Python Docs](https://docs.python.org)
```

## Pull Request Process

### Before Submitting

**Checklist**:
- [ ] All tests pass (`pytest`)
- [ ] Code is linted (`pylint src/`)
- [ ] Type hints are checked (`mypy src/`)
- [ ] Coverage is adequate (`pytest --cov`)
- [ ] Documentation is updated
- [ ] CHANGELOG.md is updated (for features/fixes)
- [ ] Commit messages are clear and descriptive

### PR Description Template

```markdown
## Description
Brief description of what this PR does.

## Motivation
Why is this change needed? What problem does it solve?

## Changes Made
- Change 1
- Change 2
- Change 3

## Testing
How was this tested? Include:
- Test files added/modified
- Manual testing performed
- Edge cases considered

## Breaking Changes
List any breaking changes, or write "None"

## Related Issues
Closes #123
Relates to #456

## Screenshots (if applicable)
Add screenshots for UI changes

## Checklist
- [ ] Tests pass
- [ ] Documentation updated
- [ ] Breaking changes documented
```

### PR Guidelines

**Size**:
- Keep PRs focused and reasonably sized
- Large changes should be broken into multiple PRs
- Aim for < 500 lines changed per PR

**Commits**:
- Each commit should be logical and complete
- Squash "fix typo" commits before submitting
- Use interactive rebase to clean up history if needed

**Reviews**:
- Respond to review feedback promptly
- Address all comments or explain why you disagree
- Be open to suggestions and alternative approaches
- Request re-review after making changes

### Review Process

1. **Automated checks run** (tests, linting, coverage)
2. **Maintainer reviews** code and design
3. **Feedback provided** via comments
4. **Changes requested** if needed
5. **Approval granted** when ready
6. **PR merged** by maintainer

**Review timeline**:
- Initial review: within 2-3 days
- Follow-up reviews: within 1-2 days
- Complex PRs may take longer

## Issue Reporting

### Bug Reports

Use the bug report template:

```markdown
**Describe the bug**
A clear description of what the bug is.

**To Reproduce**
Steps to reproduce:
1. Step 1
2. Step 2
3. See error

**Expected behavior**
What you expected to happen.

**Actual behavior**
What actually happened.

**Environment**
- OS: [e.g., Windows 10, Ubuntu 20.04, macOS 12]
- Python version: [e.g., 3.9.7]
- LLM backend: [e.g., Ollama, llama.cpp]
- Model: [e.g., codellama:13b]

**Logs**
Attach relevant log output (use debug level).

**Additional context**
Any other relevant information.
```

### Feature Requests

Use the feature request template:

```markdown
**Is your feature request related to a problem?**
A clear description of the problem.

**Desired solution**
How would you like this to work?

**Use case**
When would you use this feature?

**Alternatives considered**
What alternatives have you considered?

**Additional context**
Any other relevant information.
```

### Good Issue Practices

- **Search first**: Check if issue already exists
- **One issue per bug/feature**: Don't combine multiple issues
- **Be specific**: Provide concrete examples
- **Be respectful**: Maintainers are volunteers
- **Follow up**: Respond to questions and provide requested information

## Community

### Getting Help

- **Documentation**: Check README and docs/ first
- **Examples**: Look at examples/ directory
- **Issues**: Search existing issues for similar problems
- **Discussions**: Use GitHub Discussions for questions

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: Questions, ideas, and general discussion
- **Pull Requests**: Code contributions and reviews

### Recognition

Contributors are recognized in:
- CONTRIBUTORS.md file
- Release notes
- Documentation acknowledgments

## GUI Development

The Desktop GUI Application is built with a Python backend and HTML/CSS/JavaScript frontend, bridged by the Eel framework.

### Project Structure

```
local-ai-dev-environment/
├── src/
│   ├── gui/                   # Python backend for GUI
│   │   ├── gui_app.py        # Main Eel application entry point
│   │   ├── gui_task_manager.py    # Task execution threading
│   │   ├── gui_config_manager.py  # Configuration management
│   │   ├── gui_history_manager.py # History database
│   │   ├── platform_paths.py      # Cross-platform paths
│   │   └── crash_logger.py        # Error logging
│   └── web/                   # Frontend (HTML/CSS/JS)
│       ├── index.html         # Main HTML structure
│       ├── css/               # Stylesheets
│       │   ├── main.css       # Base styles
│       │   ├── themes/        # Light/dark themes
│       │   └── components/    # Component styles
│       ├── js/                # JavaScript
│       │   ├── main.js        # App initialization
│       │   ├── state.js       # State management
│       │   └── components/    # UI components
│       └── assets/            # Icons and images
├── build/
│   ├── pyinstaller/           # PyInstaller configuration
│   │   ├── local-ai-dev.spec  # Build specification
│   │   └── hooks/             # PyInstaller hooks
│   └── installers/            # Platform-specific installers
│       ├── windows.nsi        # Windows NSIS script
│       ├── macos.pkgproj      # macOS Packages project
│       └── linux-install.sh   # Linux install script
└── requirements-gui.txt       # GUI-specific dependencies
```

### Running GUI in Development Mode

```bash
# Install GUI dependencies
pip install -r requirements-gui.txt

# Run GUI application
python -m src.gui.gui_app

# Run with debug logging
export LOCAL_AI_LOG_LEVEL="debug"
python -m src.gui.gui_app
```

The GUI opens in your default browser but runs as a standalone application window.

### Understanding the Eel Bridge

Eel creates a bridge between Python and JavaScript, allowing bidirectional communication.

#### Python → JavaScript (Calling JS from Python)

```python
import eel

# Call JavaScript function from Python
eel.update_progress({
    'type': 'info',
    'message': 'Task started',
    'timestamp': datetime.now().isoformat()
})
```

#### JavaScript → Python (Calling Python from JS)

```javascript
// Call Python function from JavaScript
const config = await eel.get_config()();

// With parameters
const result = await eel.save_config(configData)();

// Handle errors
try {
    const result = await eel.run_task(description)();
    if (!result.success) {
        console.error('Task failed:', result.error);
    }
} catch (error) {
    console.error('Communication error:', error);
}
```

#### Exposing Python Functions

In `src/gui/gui_app.py`, functions are exposed to JavaScript using the `@eel.expose` decorator:

```python
@eel.expose
def get_config() -> Dict[str, Any]:
    """Get current configuration for GUI display."""
    try:
        config_data = config_manager_gui.get_config_for_gui()
        return {
            'success': True,
            'config': config_data
        }
    except Exception as e:
        logger.error(f"Error getting config: {e}")
        return {
            'success': False,
            'error': str(e)
        }
```

**Best Practices:**
- Always return dictionaries with `success` boolean
- Include `error` field when `success` is False
- Use try-except blocks for error handling
- Log errors before returning
- Validate inputs before processing

### Adding New Configuration Settings

To add a new configuration field:

1. **Update the Config Model** (if needed, in `src/core/models.py`):
```python
@dataclass
class SystemConfig:
    # ... existing fields ...
    new_feature_enabled: bool = False  # New field with default
```

2. **Update GUI Config Manager** (`src/gui/gui_config_manager.py`):
```python
def validate_field(self, field_name: str, value: Any) -> tuple[bool, str]:
    # ... existing validation ...
    elif field_name == 'new_feature_enabled':
        if not isinstance(value, bool):
            return False, "Must be true or false"
        return True, ""
```

3. **Add HTML Form Field** (`src/web/index.html`):
```html
<div class="form-group">
    <label for="new-feature-enabled">
        Enable New Feature
        <span class="help-icon" title="Description of the feature">ⓘ</span>
    </label>
    <input type="checkbox" 
           id="new-feature-enabled" 
           name="new_feature_enabled">
</div>
```

4. **Add JavaScript Handler** (`src/web/js/components/settings.js`):
```javascript
async loadConfig() {
    // ... existing code ...
    document.getElementById('new-feature-enabled').checked = 
        config.new_feature_enabled || false;
}

async saveConfig() {
    // ... existing code ...
    const configData = {
        // ... existing fields ...
        new_feature_enabled: document.getElementById('new-feature-enabled').checked
    };
    // ... save logic ...
}
```

5. **Update Documentation** (`docs/configuration.md`):
```markdown
- **new_feature_enabled** (optional, default: false): Enable experimental feature
  - Set to `true` to enable the new feature
  - Description of what it does
```

### Code Style Guidelines

#### Python Backend

Follow the same standards as the core project (see [Coding Standards](#coding-standards) section):

- PEP 8 style guide
- Type hints for all functions
- Google-style docstrings
- Comprehensive error handling

**GUI-Specific Patterns:**

```python
# Use threading for long-running operations
def run_task_async(self, task_description: str, callback: callable) -> None:
    """Run task in background thread with progress callbacks."""
    def task_worker():
        try:
            # Execute task
            result = self.task_executor.execute(task_description)
            callback('completed', result)
        except Exception as e:
            logger.error(f"Task failed: {e}")
            callback('error', {'error': str(e)})
    
    thread = threading.Thread(target=task_worker, daemon=True)
    thread.start()

# Always use pathlib for cross-platform paths
from pathlib import Path
config_dir = Path.home() / '.local-ai-dev'
config_file = config_dir / 'config.yaml'

# Use platform-specific paths via PlatformPaths
from src.gui.platform_paths import PlatformPaths
paths = PlatformPaths()
config_dir = paths.get_config_dir()
```

#### JavaScript Frontend

**Modern ES6+ JavaScript:**

```javascript
// Use async/await for Eel calls
async function runTask() {
    const description = document.getElementById('task-input').value;
    const result = await eel.run_task(description)();
    
    if (!result.success) {
        showError(result.error);
        return;
    }
    
    updateStatus('running');
}

// Use const/let, not var
const taskId = result.task_id;
let isRunning = false;

// Use template literals
const message = `Task ${taskId} completed in ${duration}s`;

// Use arrow functions for callbacks
element.addEventListener('click', (e) => {
    e.preventDefault();
    handleClick();
});
```

**State Management:**

```javascript
// Centralized state in state.js
const AppState = {
    currentView: 'task',
    taskRunning: false,
    config: null,
    
    setState(updates) {
        Object.assign(this, updates);
        this.notifyListeners();
    },
    
    listeners: [],
    
    subscribe(listener) {
        this.listeners.push(listener);
    },
    
    notifyListeners() {
        this.listeners.forEach(listener => listener(this));
    }
};

// Components subscribe to state changes
AppState.subscribe((state) => {
    updateUI(state);
});
```

**Component Pattern:**

```javascript
// Each component is a separate file
class TaskInputComponent {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.loadState();
    }
    
    setupEventListeners() {
        this.container.querySelector('#run-button')
            .addEventListener('click', () => this.runTask());
    }
    
    async runTask() {
        // Implementation
    }
}

// Initialize component
const taskInput = new TaskInputComponent('task-input-panel');
```

#### CSS Styling

**Use CSS Custom Properties (Variables):**

```css
/* Define theme variables in themes/light.css */
:root {
    --color-primary: #2563eb;
    --color-background: #ffffff;
    --color-text: #1f2937;
    --spacing-sm: 8px;
    --spacing-md: 16px;
}

/* Use variables in components */
.button-primary {
    background-color: var(--color-primary);
    padding: var(--spacing-sm) var(--spacing-md);
    color: var(--color-background);
}
```

**Component-Based Organization:**

```css
/* components/buttons.css */
.btn {
    /* Base button styles */
}

.btn-primary {
    /* Primary button variant */
}

.btn-secondary {
    /* Secondary button variant */
}
```

**Responsive Design:**

```css
/* Mobile-first approach */
.container {
    padding: 8px;
}

/* Tablet and up */
@media (min-width: 800px) {
    .container {
        padding: 16px;
    }
}

/* Desktop and up */
@media (min-width: 1200px) {
    .container {
        padding: 24px;
    }
}
```

### Testing GUI Components

**Python Backend Tests:**

```python
# tests/unit/test_gui_task_manager.py
def test_task_execution_with_callback(mock_task_executor):
    """Test that task execution calls progress callback."""
    manager = GUITaskManager(mock_task_executor)
    callback_data = []
    
    def callback(event_type, data):
        callback_data.append((event_type, data))
    
    manager.run_task("test task", callback)
    manager.wait_for_completion()  # Test helper
    
    assert len(callback_data) > 0
    assert callback_data[-1][0] == 'completed'
```

**Manual Frontend Testing:**

Since JavaScript UI components interact with the DOM:

1. **Start the GUI in development mode**
2. **Open browser DevTools** (F12)
3. **Test each component:**
   - Enter input and click buttons
   - Check Console for errors
   - Verify Network tab shows Eel communication
   - Test keyboard shortcuts
   - Test responsive behavior (resize window)

**Automated Frontend Tests (Future):**

Consider tools like:
- **Playwright** or **Selenium** for end-to-end testing
- **Jest** for JavaScript unit tests
- **Lighthouse** for performance audits

### Debugging Tips

**Python Backend:**

```python
# Add debug logging
logger.debug(f"Config loaded: {config}")

# Use pdb for breakpoints
import pdb; pdb.set_trace()

# Run with debug logging
export LOCAL_AI_LOG_LEVEL="debug"
python -m src.gui.gui_app
```

**JavaScript Frontend:**

```javascript
// Use console for debugging
console.log('Current state:', AppState);
console.error('Failed to load config:', error);

// Inspect Eel communication
console.log('Calling Python function...');
const result = await eel.get_config()();
console.log('Result:', result);

// Browser DevTools
// - Console: View logs and errors
// - Network: Monitor Eel WebSocket communication
// - Elements: Inspect DOM and styles
// - Sources: Set JavaScript breakpoints
```

**Testing Eel Communication:**

```javascript
// Test from browser console
eel.get_config()().then(result => console.log(result));
eel.run_task('test task')().then(result => console.log(result));
```

### Building and Packaging

**Build Executable:**

```bash
# Run PyInstaller with spec file
pyinstaller build/pyinstaller/local-ai-dev.spec

# Output in dist/LocalAIDev/
ls dist/LocalAIDev/
```

**Test Built Executable:**

```bash
# Run from dist directory (without Python)
cd dist/LocalAIDev
./LocalAIDev  # Linux/macOS
LocalAIDev.exe  # Windows

# Test on clean system without Python installed
```

**Create Installer (Platform-Specific):**

```bash
# Windows (requires NSIS)
makensis build/installers/windows.nsi

# macOS (requires Packages app)
# Open build/installers/macos.pkgproj in Packages

# Linux
bash build/installers/linux-install.sh
```

### Cross-Platform Considerations

**Always use PlatformPaths for file paths:**

```python
from src.gui.platform_paths import PlatformPaths

paths = PlatformPaths()
config_dir = paths.get_config_dir()  # Platform-specific
data_dir = paths.get_data_dir()      # Platform-specific
```

**Keyboard shortcuts:**

```javascript
// Check both Ctrl (Windows/Linux) and Cmd (macOS)
document.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        runTask();
    }
});
```

**Test on all platforms:**
- Windows 10/11
- macOS 10.15+
- Linux (Ubuntu, Fedora, Arch)
- Different DPI settings (100%, 125%, 150%, 200%)

### Accessibility Requirements

All GUI components must be accessible:

**ARIA Labels:**

```html
<button id="run-button" 
        aria-label="Run task"
        aria-describedby="run-help-text">
    Run
</button>
<span id="run-help-text" class="sr-only">
    Execute the task described in the input field
</span>
```

**Keyboard Navigation:**

- All interactive elements must be keyboard-accessible
- Tab order must be logical
- Focus indicators must be visible
- Escape key should close dialogs

**Screen Reader Support:**

```javascript
// Announce status changes
function announceStatus(message) {
    const announcement = document.getElementById('aria-live-region');
    announcement.textContent = message;
}

// In HTML
<div id="aria-live-region" 
     role="status" 
     aria-live="polite" 
     class="sr-only">
</div>
```

### Common GUI Development Tasks

**Adding a New View:**

1. Add HTML section in `index.html`
2. Create CSS file in `css/components/`
3. Create JS component in `js/components/`
4. Add navigation tab in navigation bar
5. Update view routing in `main.js`

**Adding a New Eel Function:**

1. Add `@eel.expose` function in `gui_app.py`
2. Call from JavaScript with `await eel.function_name()()`
3. Handle errors on both sides
4. Document the function

**Updating Styles:**

1. Edit theme variables in `css/themes/` for colors
2. Edit component CSS in `css/components/` for layout
3. Test in both light and dark themes
4. Test at different window sizes

## Development Tips

### Debugging

```python
# Use logging for debugging
import logging
logger = logging.getLogger(__name__)

logger.debug(f"Variable value: {variable}")
logger.info(f"Processing {item}")

# Use debugger
import pdb; pdb.set_trace()

# Or with pytest
pytest --pdb  # Drop into debugger on failure
```

### Testing with Real LLM

```python
# Mark tests that require real LLM
@pytest.mark.integration
@pytest.mark.requires_llm
def test_with_real_llm():
    pass

# Run only unit tests (no LLM required)
pytest -m "not requires_llm"

# Run integration tests with LLM
pytest -m requires_llm
```

### Performance Profiling

```python
# Profile code execution
python -m cProfile -o output.prof src/main.py

# Analyze profile
python -m pstats output.prof

# Or use line_profiler
@profile
def slow_function():
    pass
```

## Questions?

If you have questions not covered in this guide:
1. Check the [Developer Guide](docs/developer_guide.md)
2. Search [existing issues](https://github.com/your-repo/issues)
3. Ask in [GitHub Discussions](https://github.com/your-repo/discussions)
4. Open a new issue with the "question" label

Thank you for contributing to the Local AI Development Environment!
