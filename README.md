# Local AI Development Environment

An autonomous AI-powered development system that runs entirely on your local machine to write, edit, and improve code without relying on cloud services. The system follows a plan-execute-observe agent loop pattern, using a local language model (LLM) as the reasoning engine to complete development tasks from start to finish.

## Table of Contents

- [Features](#features)
- [System Requirements](#system-requirements)
- [Supported LLM Backends](#supported-llm-backends)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
  - [Basic Usage](#basic-usage)
  - [Example Tasks](#example-tasks)
  - [Command Line Interface](#command-line-interface)
- [Privacy and Security](#privacy-and-security)
- [Architecture](#architecture)
- [Development](#development)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [License](#license)

## Features

- **🏠 Local-First**: Runs entirely on your machine without cloud dependencies
- **🤖 Autonomous Operation**: Completes development tasks from description to verified implementation
- **🔧 Multi-Language Support**: Python, JavaScript, TypeScript, Java, Go, Rust, and C++
- **📁 Code Generation & Editing**: Creates and modifies code following project conventions
- **🧪 Testing Integration**: Writes and runs tests to verify implementations
- **🔍 Code Search & Analysis**: Navigates codebases and understands project structure
- **🌐 Web Research**: Fetches documentation and examples from the internet (optional)
- **🔄 Self-Improvement**: Can enhance its own capabilities (optional, use with caution)
- **🔒 Privacy-Focused**: Your code never leaves your machine

## System Requirements

### Minimum Requirements

- **Operating System**: Windows, macOS, or Linux
- **Python**: 3.8 or higher
- **RAM**: 8 GB minimum (16 GB recommended for larger models)
- **Storage**: 10 GB free space (more for larger LLM models)
- **CPU**: Modern multi-core processor
- **GPU**: Optional, but recommended for faster LLM inference (NVIDIA with CUDA support)

### For Optimal Performance

- **RAM**: 16-32 GB
- **GPU**: NVIDIA GPU with 8+ GB VRAM (for running 13B+ parameter models)
- **Storage**: SSD with 50+ GB free space
- **CPU**: 8+ core processor

## Supported LLM Backends

The system supports multiple local LLM backends:

### 1. Ollama (Recommended)

**Why Ollama?** Easiest to set up and use, with automatic model management.

- **Installation**: [https://ollama.ai/](https://ollama.ai/)
- **Models**: `codellama`, `llama2`, `mistral`, `deepseek-coder`, and more
- **Endpoint**: `http://localhost:11434` (default)

**Setup Steps**:
```bash
# Install Ollama (see ollama.ai for platform-specific instructions)

# Pull a code-focused model
ollama pull codellama:13b

# Test the model
ollama run codellama:13b "Write a hello world function in Python"
```

**Recommended Models**:
- `codellama:13b` - Best balance of performance and quality for code tasks
- `codellama:34b` - Higher quality, requires more resources
- `deepseek-coder:33b` - Excellent for coding tasks, requires GPU

### 2. llama.cpp Server

**Why llama.cpp?** Highly optimized C++ implementation with OpenAI-compatible API.

- **Installation**: [https://github.com/ggerganov/llama.cpp](https://github.com/ggerganov/llama.cpp)
- **Models**: Download GGUF format models from Hugging Face
- **Endpoint**: `http://localhost:8080` (configurable)

**Setup Steps**:
```bash
# Build llama.cpp with server support
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
make server

# Download a GGUF model (example: CodeLlama-13B)
# Get models from Hugging Face: https://huggingface.co/TheBloke

# Start server
./server -m /path/to/model.gguf --port 8080 --ctx-size 16384
```

### 3. Generic OpenAI-Compatible Servers

Any server implementing the OpenAI Completions API format, such as:
- **LocalAI**: [https://github.com/mudler/LocalAI](https://github.com/mudler/LocalAI)
- **text-generation-webui** (oobabooga): [https://github.com/oobabooga/text-generation-webui](https://github.com/oobabooga/text-generation-webui)
- **vLLM**: [https://github.com/vllm-project/vllm](https://github.com/vllm-project/vllm)

## Installation

### CLI Installation

#### 1. Clone or Download the Repository

```bash
cd Local\ dev\ ai
```

#### 2. Create a Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

#### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 4. Set Up Your Local LLM

Choose and install one of the [supported LLM backends](#supported-llm-backends). We recommend Ollama for ease of use.

#### 5. Create Configuration File

```bash
# Copy example configuration
cp config.example.yaml config.yaml

# Edit config.yaml with your settings
# At minimum, update:
#   - llm.endpoint (your LLM server URL)
#   - llm.model_name (your model name)
#   - project_root (directory where the AI will work)
```

#### 6. Verify Installation

```bash
# Run tests to ensure everything is working
pytest tests/unit/

# Test LLM connectivity (if you've configured it)
python src/main.py --test-llm
```

### GUI Installation

The Desktop GUI Application provides a modern graphical interface for the Local AI Development Environment.

#### 1. Install GUI Dependencies

After completing the CLI installation steps above, install additional GUI requirements:

```bash
pip install -r requirements-gui.txt
```

This installs:
- **Eel**: Python-JavaScript bridge for the GUI
- **pystray**: System tray integration
- **PyInstaller**: Executable packaging tool
- **watchdog**: Configuration file monitoring
- **cryptography**: Secure storage of sensitive configuration values

#### 2. Run GUI in Development Mode

```bash
python -m src.gui.gui_app
```

The GUI will launch in your default web browser with a native application window.

#### 3. Build Standalone Executable

To create a standalone executable that doesn't require Python:

```bash
# Build with PyInstaller
pyinstaller build/pyinstaller/local-ai-dev.spec

# The executable will be in dist/LocalAIDev/
# On Windows: dist/LocalAIDev/LocalAIDev.exe
# On macOS: dist/LocalAIDev/LocalAIDev.app
# On Linux: dist/LocalAIDev/LocalAIDev
```

#### 4. Install from Platform-Specific Installers

For end users, platform-specific installers are available:

**Windows:**
```bash
# Build installer with NSIS (requires NSIS installed)
makensis build/installers/windows.nsi

# Install from: dist/LocalAIDev-Setup.exe
# Creates desktop shortcut and Start menu entry
```

**macOS:**
```bash
# Build installer package (requires Packages app)
# Install .pkg file to Applications folder
# See build/installers/macos.pkgproj for configuration
```

**Linux:**
```bash
# Run installation script
bash build/installers/linux-install.sh

# Installs to ~/.local/share/LocalAIDev/ or /opt/LocalAIDev/
# Creates application menu entry and desktop icon
```

For detailed installer build instructions, see `build/installers/README.md`.

## Configuration

Configuration is managed through `config.yaml`. Copy `config.example.yaml` to get started:

```yaml
# Language Model Configuration
llm:
  endpoint: "http://localhost:11434"      # LLM server URL
  model_name: "codellama:13b"             # Model to use
  temperature: 0.2                        # Lower = more deterministic
  max_tokens: 4096                        # Max tokens per response
  context_length: 16384                   # Total context window
  backend_type: "ollama"                  # ollama, llamacpp, or openai-compatible

# Project Configuration
project_root: "."                         # Working directory
log_level: "info"                         # debug, info, warning, error

# Feature Flags
web_research_enabled: true                # Enable web search
self_improvement_enabled: false           # Enable self-modification (USE WITH CAUTION)

# Exclusions
excluded_directories:
  - "node_modules"
  - ".git"
  - "__pycache__"
  - ".pytest_cache"
  - "venv"
  - ".venv"
```

### Environment Variable Overrides

You can override any configuration setting using environment variables:

```bash
export LOCAL_AI_LLM_ENDPOINT="http://localhost:8080"
export LOCAL_AI_LLM_MODEL="llama2:13b"
export LOCAL_AI_LOG_LEVEL="debug"
export LOCAL_AI_WEB_RESEARCH="false"
```

## Usage

### GUI Usage

The Desktop GUI Application provides an intuitive interface for all features.

#### First Run Setup

On first launch, the GUI will prompt you to configure your LLM endpoint:

1. **Welcome Dialog**: A setup wizard appears automatically
2. **LLM Configuration**:
   - Enter your LLM endpoint URL (e.g., `http://localhost:11434`)
   - Enter the model name (e.g., `codellama:13b`)
   - Select backend type (Ollama, llama.cpp, or OpenAI-compatible)
3. **Project Settings**:
   - Browse and select your working directory
4. **Test Connection**: Verify the LLM is accessible
5. **Save and Continue**: Complete setup to access the main application

The configuration is saved to a platform-specific location:
- **Windows**: `%APPDATA%\local-ai-dev\config.yaml`
- **macOS**: `~/Library/Application Support/local-ai-dev/config.yaml`
- **Linux**: `~/.config/local-ai-dev/config.yaml`

#### Running Tasks

1. **Open the Task View** (default view on launch)
2. **Enter Your Task**: Type a task description in the input area (up to 5000 characters)
   - Example: "Create a Python calculator module with unit tests"
3. **Run**: Click the "Run Task" button or press `Ctrl+Enter` (`Cmd+Enter` on macOS)
4. **View Progress**: Real-time progress updates appear in the output panel
5. **Stop if Needed**: Click "Stop Task" or press `Esc` to cancel execution

#### Viewing History

1. **Navigate to History**: Press `Ctrl+H` (`Cmd+H` on macOS) or click the History tab
2. **Search**: Use the search box to filter tasks by description
3. **Filter**: Filter by status (Completed, Error, Stopped)
4. **View Details**: Click any entry to see full output and configuration
5. **Re-run**: Click "Re-run" to execute the same task again
6. **Export**: Export history to JSON or CSV format
7. **Delete**: Remove individual entries or clear all history

#### Managing Settings

1. **Open Settings**: Press `Ctrl+,` (`Cmd+,` on macOS) or click the Settings tab
2. **LLM Settings**: Configure endpoint, model, temperature, token limits
3. **Project Settings**: Change working directory, log level, exclusions
4. **Feature Flags**: Enable/disable web research or self-improvement
5. **GUI Settings**: Configure theme, system tray behavior
6. **Save Changes**: Click "Save Settings" to apply changes
7. **Reset**: Click "Reset to Defaults" to restore default configuration

#### Keyboard Shortcuts

| Action | Windows/Linux | macOS |
|--------|---------------|-------|
| Run Task | `Ctrl+Enter` | `Cmd+Enter` |
| Stop Task | `Esc` | `Esc` |
| Open Settings | `Ctrl+,` | `Cmd+,` |
| Open History | `Ctrl+H` | `Cmd+H` |
| Switch to Task View | `Ctrl+1` | `Cmd+1` |
| Switch to History View | `Ctrl+2` | `Cmd+2` |
| Switch to Settings View | `Ctrl+3` | `Cmd+3` |
| Copy Output | `Ctrl+C` | `Cmd+C` |

For complete keyboard shortcuts reference, see [docs/keyboard_shortcuts.md](docs/keyboard_shortcuts.md).

#### System Tray Integration

When enabled, the GUI minimizes to the system tray instead of closing:

- **Minimize to Tray**: Click the window close button
- **Restore**: Click the tray icon or select "Show" from the context menu
- **Quick Access**: Right-click tray icon for Settings and Exit options
- **Task Indicator**: Tray icon shows visual indication when tasks are running

#### Troubleshooting GUI Issues

**Application won't start:**
- Ensure all GUI dependencies are installed: `pip install -r requirements-gui.txt`
- Check for port conflicts (default port 8080)
- Review logs in the application data directory

**LLM connection errors:**
- Verify your LLM server is running
- Test connectivity from Settings → "Test Connection"
- Check endpoint URL and model name are correct

**Configuration not saving:**
- Ensure the application has write permissions to the config directory
- Check for external editors holding locks on config.yaml
- Review error messages in the status bar

For more troubleshooting, see [docs/user_guide.md](docs/user_guide.md).

### CLI Usage

#### Basic CLI Commands

The system is designed to execute complete development tasks autonomously:

```bash
# Execute a task
python src/main.py "Create a new Python module called calculator.py with add, subtract, multiply, and divide functions. Include unit tests."

# With verbose logging
python src/main.py --log-level debug "Add a new endpoint to the Flask app for user registration"

# Disable web research for a task
python src/main.py --no-web-research "Refactor the authentication module to use JWT tokens"
```

### Example Tasks

The system can handle a wide variety of development tasks:

#### 1. Creating New Code

```bash
# Create a new module
python src/main.py "Create a new Python class EmailValidator with methods to validate email format and domain existence. Include comprehensive unit tests."

# Create a React component
python src/main.py "Create a React component called UserProfile that displays user information with avatar, name, email, and bio. Include TypeScript types and unit tests."

# Create a REST API endpoint
python src/main.py "Add a new Flask endpoint POST /api/users that creates a new user with validation. Include error handling and tests."
```

#### 2. Editing Existing Code

```bash
# Refactor code
python src/main.py "Refactor the authentication module to use async/await instead of callbacks"

# Add functionality
python src/main.py "Add input validation to all public methods in the UserService class"

# Fix bugs
python src/main.py "Fix the bug where the date picker crashes when selecting dates before 1970"
```

#### 3. Testing and Debugging

```bash
# Add tests
python src/main.py "Add unit tests for the PaymentProcessor class, covering success cases and error conditions"

# Debug failures
python src/main.py "The test_user_authentication test is failing. Debug and fix the issue."

# Add property-based tests
python src/main.py "Add property-based tests for the sorting algorithm using Hypothesis"
```

#### 4. Research and Implementation

```bash
# Research and implement
python src/main.py "Research the Stripe API and implement a payment processing module for our e-commerce app"

# Learn from documentation
python src/main.py "Use the FastAPI documentation to add proper request validation to all endpoints"
```

### Command Line Interface

```
usage: main.py [-h] [--config CONFIG] [--log-level {debug,info,warning,error}]
               [--no-web-research] [--test-llm] [--version]
               [task_description]

Local AI Development Environment - Autonomous coding assistant

positional arguments:
  task_description      Description of the development task to execute

optional arguments:
  -h, --help            Show this help message and exit
  --config CONFIG       Path to configuration file (default: config.yaml)
  --log-level LEVEL     Logging level (default: info)
  --no-web-research     Disable web research for this task
  --test-llm            Test connection to LLM and exit
  --version             Show version information and exit
```

## Privacy and Security

### Privacy Guarantees

Your code and project data remain private and secure:

- **✅ Local Execution**: All AI reasoning happens on your local machine using your local LLM
- **✅ No Code Transmission**: Your code is never sent to external servers or cloud services
- **✅ No Telemetry**: The system does not collect or transmit usage data
- **✅ Local Storage**: All logs, history, and state are stored locally on your filesystem

### What Data Leaves Your Machine?

The system is designed with privacy as a priority. Here's exactly what may leave your machine:

#### When Web Research is Enabled (`web_research_enabled: true`)

1. **Search Queries**: Text search queries are sent to web search providers (e.g., DuckDuckGo)
   - Example: "Python requests library documentation"
   - **Code is never included in search queries**

2. **Documentation Fetching**: HTTP requests to fetch documentation pages
   - Example: Fetching `https://docs.python.org/3/library/requests.html`
   - **Your code is not transmitted when fetching documentation**

3. **Request Logging**: All web requests are logged locally for transparency
   - Check logs to see exactly what was requested

#### When Web Research is Disabled

- **No network traffic** related to your tasks
- The system operates in completely offline mode for core functionality

### Disabling All Network Access

For maximum security and air-gapped environments:

```yaml
# In config.yaml
web_research_enabled: false
```

Or use environment variable:
```bash
export LOCAL_AI_NETWORK_DISABLED="true"
python src/main.py "your task here"
```

### Self-Improvement Security

The Self-Improvement Engine can modify the system's own code. This is an advanced feature that should be used with caution:

- **Disabled by Default**: `self_improvement_enabled: false`
- **Automatic Backups**: Creates backups before any self-modification
- **Automatic Rollback**: Reverts changes if system effectiveness degrades
- **Audit Log**: Maintains a complete log of all self-modifications
- **Test Before Apply**: Runs comprehensive tests before finalizing changes

**⚠️ Warning**: Only enable self-improvement if you understand the risks and have proper backups of your system.

### Recommended Security Practices

1. **Run in a Virtual Environment**: Isolate dependencies and permissions
2. **Review Generated Code**: Always review code before committing or deploying
3. **Use Version Control**: Commit your work regularly so you can revert changes
4. **Restrict Project Root**: Set `project_root` to only the directories the system should access
5. **Monitor Logs**: Check logs to understand what actions were taken
6. **Backup Regularly**: Keep backups of important projects

## Architecture

The system consists of modular components orchestrated by a central Task Executor:

```
┌─────────────────────────────────────────────────────────────┐
│                        User                                  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │   Task Executor      │
              │  (Agent Loop)        │
              └──────────┬───────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         ▼               ▼               ▼
  ┌──────────┐   ┌─────────────┐  ┌──────────────┐
  │   Code   │   │   Context   │  │     Web      │
  │  Agent   │   │   Manager   │  │   Research   │
  └──────────┘   └─────────────┘  └──────────────┘
         │               │               │
         └───────────────┼───────────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │   Local LLM          │
              │   (Your Machine)     │
              └──────────────────────┘
```

### Key Components

- **Task Executor**: Orchestrates the agent loop (plan → execute → observe → reflect)
- **Code Agent**: Handles file operations, code generation/editing, command execution
- **Context Manager**: Analyzes project structure, tracks dependencies, extracts code context
- **Web Research Module**: Searches web and fetches documentation (optional)
- **Local LLM Interface**: Abstracts communication with your local language model
- **Self-Improvement Engine**: Enhances system capabilities (optional)

See `docs/architecture.md` for detailed component documentation.

## Development

### Project Structure

```
Local dev ai/
├── src/
│   ├── core/               # Core models and utilities
│   │   ├── models.py       # Data models
│   │   ├── config.py       # Configuration management
│   │   ├── llm_interface.py # LLM communication
│   │   └── task_executor.py # Task orchestration
│   ├── agents/             # Agent components
│   │   ├── file_operations.py
│   │   ├── code_search.py
│   │   ├── command_executor.py
│   │   └── code_agent.py
│   ├── context/            # Context management
│   │   ├── ast_parser.py
│   │   └── context_manager.py
│   ├── web/                # Web research
│   │   └── web_research.py
│   ├── self_improvement/   # Self-improvement
│   │   └── self_improvement.py
│   └── main.py             # Entry point
├── tests/
│   ├── properties/         # Property-based tests (Hypothesis)
│   ├── unit/               # Unit tests
│   ├── integration/        # Integration tests
│   └── system/             # End-to-end tests
├── config.yaml             # Configuration (create from example)
├── config.example.yaml     # Example configuration
├── requirements.txt        # Python dependencies
└── pytest.ini             # Test configuration
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/unit/          # Unit tests only
pytest tests/properties/    # Property-based tests only
pytest tests/integration/   # Integration tests only

# Run with coverage
pytest --cov=src --cov-report=html

# Run property tests with more iterations
pytest tests/properties/ --hypothesis-profile=thorough
```

### Contributing

Contributions are welcome! See `CONTRIBUTING.md` for guidelines.

## Testing

The system uses a comprehensive testing strategy:

- **Property-Based Tests**: 11 correctness properties tested with 100+ random inputs each
- **Unit Tests**: 90%+ coverage of individual components
- **Integration Tests**: Component interaction testing
- **System Tests**: End-to-end workflow testing with real projects

### Property-Based Tests

The system includes property-based tests that verify universal correctness properties:

1. HTML Content Extraction
2. Documentation Source Prioritization
3. Dependency Graph Accuracy
4. Framework Detection Consistency
5. Code Search with Exclusions
6. Symbol Extraction Completeness
7. Search Result Structure
8. File Content Round-Trip
9. Reference Updates on File Move
10. Command Argument Formatting
11. Primary Language Detection

These tests run with randomized inputs to ensure correctness across a wide range of scenarios.

## Troubleshooting

### Common Issues

#### LLM Connection Failed

**Problem**: `Error: Could not connect to LLM at http://localhost:11434`

**Solutions**:
- Verify your LLM server is running (e.g., `ollama list` for Ollama)
- Check the endpoint in `config.yaml` matches your server
- Test connectivity: `curl http://localhost:11434/api/tags` (for Ollama)

#### Model Not Found

**Problem**: `Error: Model 'codellama:13b' not found`

**Solutions**:
- Pull the model: `ollama pull codellama:13b` (for Ollama)
- Verify available models: `ollama list`
- Update `model_name` in `config.yaml` to match an available model

#### Out of Memory

**Problem**: System crashes or becomes unresponsive during task execution

**Solutions**:
- Use a smaller model (e.g., `codellama:7b` instead of `codellama:34b`)
- Reduce `context_length` in `config.yaml`
- Close other applications to free RAM
- Enable swap space on your system

#### Slow Performance

**Problem**: Tasks take a very long time to complete

**Solutions**:
- Use GPU acceleration if available (configure in your LLM backend)
- Switch to a smaller, faster model
- Reduce `max_tokens` in `config.yaml`
- Limit project scope with `excluded_directories`

#### Import Errors

**Problem**: `ModuleNotFoundError` when running the system

**Solutions**:
- Ensure virtual environment is activated
- Reinstall dependencies: `pip install -r requirements.txt`
- Check Python version: `python --version` (must be 3.8+)

### Debug Mode

Enable detailed logging to diagnose issues:

```bash
# In config.yaml
log_level: "debug"

# Or via command line
python src/main.py --log-level debug "your task"
```

### Getting Help

1. Check logs in the project directory for detailed error messages
2. Review the configuration in `config.yaml`
3. Test LLM connectivity: `python src/main.py --test-llm`
4. Open an issue on the project repository with:
   - Your configuration (remove sensitive data)
   - Error messages from logs
   - Steps to reproduce the issue

## License

TBD
