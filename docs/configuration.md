# Configuration Management

The Local AI Development Environment uses a flexible configuration system that supports:
- YAML and JSON configuration files
- Environment variable overrides
- Configuration validation
- Runtime configuration reloading

## Configuration File

The system looks for configuration files in the following order:

1. Explicitly specified path (passed to `load_config()`)
2. Current directory: `config.yaml`, `config.yml`, or `config.json`
3. User home directory: `~/.local_ai_dev/config.yaml`, `config.yml`, or `config.json`
4. Built-in defaults (if no file found)

### Example Configuration (YAML)

```yaml
llm:
  endpoint: "http://localhost:11434"
  model_name: "codellama:13b"
  temperature: 0.2
  max_tokens: 4096
  context_length: 16384
  backend_type: "ollama"

project_root: "."
log_level: "info"
web_research_enabled: true
self_improvement_enabled: false

excluded_directories:
  - "node_modules"
  - ".git"
  - "__pycache__"
  - ".pytest_cache"
  - "venv"
  - ".venv"
  - "build"
  - "dist"
  - ".hypothesis"
```

### Example Configuration (JSON)

```json
{
  "llm": {
    "endpoint": "http://localhost:11434",
    "model_name": "codellama:13b",
    "temperature": 0.2,
    "max_tokens": 4096,
    "context_length": 16384,
    "backend_type": "ollama"
  },
  "project_root": ".",
  "log_level": "info",
  "web_research_enabled": true,
  "self_improvement_enabled": false,
  "excluded_directories": [
    "node_modules",
    ".git",
    "__pycache__",
    ".pytest_cache",
    "venv",
    ".venv",
    "build",
    "dist",
    ".hypothesis"
  ]
}
```

## Configuration Options

### LLM Configuration

- **endpoint** (required): URL of the local LLM server
  - Must start with `http://` or `https://`
  - Example: `"http://localhost:11434"`

- **model_name** (required): Name of the model to use
  - Must be available on your LLM endpoint
  - Example: `"codellama:13b"`, `"llama2:7b"`, `"mistral:7b"`

- **temperature** (optional, default: 0.2): Controls randomness in generation
  - Range: 0.0 to 2.0
  - Lower values (0.0-0.3) = more deterministic, good for code
  - Higher values (0.7-2.0) = more creative, good for brainstorming

- **max_tokens** (optional, default: 4096): Maximum tokens to generate per response
  - Must be positive integer
  - Should be less than context_length

- **context_length** (optional, default: 16384): Total context window size
  - Must be positive integer
  - Must be >= max_tokens

- **backend_type** (optional, default: "ollama"): Type of LLM backend
  - Options: `"ollama"`, `"llamacpp"`, `"openai-compatible"`

### System Configuration

- **project_root** (required): Root directory for the project
  - Must be an existing directory
  - Can be absolute or relative path
  - Default: current working directory (CLI) or user-selected directory (GUI)
  - Example: `/home/user/my-project` or `C:\Users\User\Projects\MyApp`

- **log_level** (optional, default: "info"): Logging verbosity
  - Options: `"debug"`, `"info"`, `"warning"`, `"error"`
  - Case-insensitive
  - **debug**: Detailed diagnostic information
  - **info**: General informational messages (recommended)
  - **warning**: Warning messages and errors
  - **error**: Only critical errors

- **web_research_enabled** (optional, default: true): Enable web research
  - Set to `false` to disable web search and fetching
  - Useful for offline operation or privacy concerns
  - When disabled, AI can only use local context

- **self_improvement_enabled** (optional, default: false): Enable self-improvement
  - **WARNING**: Allows system to modify its own code
  - Enable only if you understand the implications
  - Automatic backups created before modifications
  - Rollback mechanism available if issues occur

- **excluded_directories** (optional): List of directories to exclude
  - Used by code search and project analysis
  - Default includes common build/cache directories
  - Examples: `node_modules`, `.git`, `__pycache__`, `venv`, `build`, `dist`
  - Supports glob patterns

### GUI-Specific Configuration

These options only apply to the Desktop GUI Application:

- **theme** (optional, default: "light"): Visual theme
  - Options: `"light"`, `"dark"`
  - Applied immediately without restart
  - Saved to GUI preferences (separate from config.yaml)

- **tray_enabled** (optional, default: true): System tray integration
  - When `true`: Close button minimizes to system tray
  - When `false`: Close button exits application
  - Platform support varies (see System Tray section below)

- **auto_scroll** (optional, default: true): Auto-scroll progress output
  - When `true`: Output panel scrolls to show latest messages
  - When `false`: Scroll position maintained, manual scrolling required
  - Can be toggled during task execution

- **history_limit** (optional, default: 0 - unlimited): Maximum history entries
  - When `0`: No limit
  - When positive integer: Automatically delete oldest entries beyond limit
  - Helps manage database size for long-term usage

### Platform-Specific Settings

#### Configuration File Locations

**CLI Mode:**
- Searches in order:
  1. Path specified via `--config` flag
  2. Current directory: `config.yaml` or `config.yml` or `config.json`
  3. User home: `~/.local_ai_dev/config.yaml`
  4. Built-in defaults

**GUI Mode:**
- Platform-specific locations:
  - **Windows**: `%APPDATA%\local-ai-dev\config.yaml`
  - **macOS**: `~/Library/Application Support/local-ai-dev/config.yaml`
  - **Linux**: `~/.config/local-ai-dev/config.yaml`

#### Data File Locations

**History Database (GUI only):**
- **Windows**: `%LOCALAPPDATA%\local-ai-dev\history.db`
- **macOS**: `~/Library/Application Support/local-ai-dev/history.db`
- **Linux**: `~/.local/share/local-ai-dev/history.db`

**Log Files:**
- **Windows**: `%LOCALAPPDATA%\local-ai-dev\logs\`
- **macOS**: `~/Library/Logs/local-ai-dev/`
- **Linux**: `~/.local/share/local-ai-dev/logs/`

#### System Tray Support

System tray integration availability:
- **Windows 10/11**: Full support
- **macOS 10.15+**: Full support (menu bar)
- **Linux**: Depends on desktop environment
  - GNOME: Requires extension (e.g., AppIndicator)
  - KDE: Full support
  - XFCE: Full support
  - Other DEs: Varies

If system tray is not supported, set `tray_enabled: false` in configuration.

## Configuration Options Reference

### Complete Configuration Table

| Field | Type | Default | Range/Options | Shared CLI/GUI | Description |
|-------|------|---------|---------------|----------------|-------------|
| **llm.endpoint** | string (URL) | `http://localhost:11434` | Valid HTTP/HTTPS URL | ✅ Yes | LLM server endpoint URL |
| **llm.model_name** | string | `codellama:13b` | Any string | ✅ Yes | Model identifier |
| **llm.temperature** | float | `0.2` | `0.0` - `2.0` | ✅ Yes | Generation randomness |
| **llm.max_tokens** | integer | `4096` | `1` - `100000` | ✅ Yes | Max tokens per response |
| **llm.context_length** | integer | `16384` | `1` - `100000` | ✅ Yes | Total context window |
| **llm.backend_type** | string | `ollama` | `ollama`, `llamacpp`, `openai-compatible` | ✅ Yes | LLM backend type |
| **project_root** | string (path) | `.` (CLI) / user-selected (GUI) | Valid directory path | ✅ Yes | Working directory |
| **log_level** | string | `info` | `debug`, `info`, `warning`, `error` | ✅ Yes | Logging verbosity |
| **web_research_enabled** | boolean | `true` | `true`, `false` | ✅ Yes | Enable web research |
| **self_improvement_enabled** | boolean | `false` | `true`, `false` | ✅ Yes | Enable self-improvement |
| **excluded_directories** | list[string] | See below | Glob patterns | ✅ Yes | Directories to exclude |
| **theme** | string | `light` | `light`, `dark` | ❌ GUI only | Visual theme |
| **tray_enabled** | boolean | `true` | `true`, `false` | ❌ GUI only | System tray integration |
| **auto_scroll** | boolean | `true` | `true`, `false` | ❌ GUI only | Auto-scroll output |
| **history_limit** | integer | `0` | `0` - unlimited | ❌ GUI only | Max history entries (0 = no limit) |

**Default Excluded Directories:**
```yaml
excluded_directories:
  - node_modules
  - .git
  - __pycache__
  - .pytest_cache
  - venv
  - .venv
  - build
  - dist
  - .hypothesis
  - .tox
  - .eggs
  - *.egg-info
```

### CLI and GUI Compatibility

The configuration file (`config.yaml`) is fully compatible between CLI and GUI modes:

**Shared Fields:**
- All LLM settings (endpoint, model, temperature, etc.)
- Project settings (project_root, log_level, excluded_directories)
- Feature flags (web_research_enabled, self_improvement_enabled)

**GUI-Only Fields:**
- Theme, tray_enabled, auto_scroll, history_limit
- CLI ignores these fields (no errors)
- Safe to edit config.yaml with both modes installed

**Example Shared Configuration:**

```yaml
# This config works for both CLI and GUI
llm:
  endpoint: "http://localhost:11434"
  model_name: "codellama:13b"
  temperature: 0.2
  max_tokens: 4096
  context_length: 16384
  backend_type: "ollama"

project_root: "/home/user/my-project"
log_level: "info"
web_research_enabled: true
self_improvement_enabled: false

excluded_directories:
  - node_modules
  - .git
  - __pycache__
  - venv
  - build

# GUI-only fields (ignored by CLI)
theme: "dark"
tray_enabled: true
auto_scroll: true
history_limit: 500
```

## Environment Variable Overrides

All configuration options can be overridden using environment variables. This is useful for:
- Temporary configuration changes
- CI/CD pipelines
- Docker containers
- Security-sensitive values

### Available Environment Variables

| Environment Variable | Overrides | Example |
|---------------------|-----------|---------|
| `LOCAL_AI_LLM_ENDPOINT` | llm.endpoint | `http://localhost:8080` |
| `LOCAL_AI_LLM_MODEL` | llm.model_name | `llama2:7b` |
| `LOCAL_AI_LLM_TEMPERATURE` | llm.temperature | `0.5` |
| `LOCAL_AI_LLM_MAX_TOKENS` | llm.max_tokens | `8000` |
| `LOCAL_AI_LLM_CONTEXT_LENGTH` | llm.context_length | `32000` |
| `LOCAL_AI_LLM_BACKEND` | llm.backend_type | `llamacpp` |
| `LOCAL_AI_PROJECT_ROOT` | project_root | `/path/to/project` |
| `LOCAL_AI_LOG_LEVEL` | log_level | `debug` |
| `LOCAL_AI_WEB_RESEARCH` | web_research_enabled | `true` or `false` |
| `LOCAL_AI_SELF_IMPROVEMENT` | self_improvement_enabled | `true` or `false` |
| `LOCAL_AI_NETWORK_DISABLED` | Disables all network | `true` or `false` |

### Example Usage

```bash
# Use a different model
export LOCAL_AI_LLM_MODEL="llama2:13b"

# Enable debug logging
export LOCAL_AI_LOG_LEVEL="debug"

# Disable network access (offline mode)
export LOCAL_AI_NETWORK_DISABLED="true"

# Run the application
python src/main.py
```

## Usage in Code

### Loading Configuration

```python
from src.core.config import load_config, ConfigManager

# Simple usage - loads from default locations
config = load_config()

# Load from specific file
config = load_config("/path/to/config.yaml")

# Using ConfigManager for more control
manager = ConfigManager("config.yaml")
config = manager.load_config()
```

### Accessing Configuration

```python
# Access LLM configuration
print(f"Using model: {config.llm.model_name}")
print(f"Endpoint: {config.llm.endpoint}")

# Access system configuration
print(f"Project root: {config.project_root}")
print(f"Log level: {config.log_level}")

# Check feature flags
if config.web_research_enabled:
    print("Web research is enabled")
```

### Reloading Configuration

```python
# Reload configuration without restarting application
manager = ConfigManager("config.yaml")
config = manager.load_config()

# ... application runs ...

# Reload after configuration file changes
updated_config = manager.reload_config()
```

### Saving Configuration

```python
from src.core.models import SystemConfig, LLMConfig

# Create configuration programmatically
llm_config = LLMConfig(
    endpoint="http://localhost:11434",
    model_name="codellama:13b"
)
config = SystemConfig(
    llm=llm_config,
    project_root="/path/to/project"
)

# Save as YAML
manager = ConfigManager()
manager.save_config(config, "output.yaml", format="yaml")

# Save as JSON
manager.save_config(config, "output.json", format="json")
```

### Validation

Configuration is automatically validated when loaded, but you can also validate manually:

```python
from src.core.config import ConfigManager, ConfigurationError

manager = ConfigManager()

try:
    manager.validate_config(config)
    print("Configuration is valid")
except ConfigurationError as e:
    print(f"Configuration error: {e}")
```

## Error Handling

The configuration system raises `ConfigurationError` for various issues:

- Configuration file not found
- Invalid YAML/JSON syntax
- Invalid configuration values (e.g., negative temperature)
- Missing required fields
- Invalid project root path
- Invalid backend type

Example error handling:

```python
from src.core.config import load_config, ConfigurationError

try:
    config = load_config("config.yaml")
except ConfigurationError as e:
    print(f"Failed to load configuration: {e}")
    # Use defaults or exit
```

## Privacy and Security

### Network Access Control

The `LOCAL_AI_NETWORK_DISABLED` environment variable provides a kill switch for all network access:

```bash
# Disable all network access
export LOCAL_AI_NETWORK_DISABLED="true"
```

When enabled, this sets `web_research_enabled=false`, ensuring the system operates in offline mode.

### Sensitive Configuration

For sensitive values (API keys, credentials), prefer environment variables over configuration files:

```bash
# Set sensitive values via environment
export LOCAL_AI_LLM_ENDPOINT="https://private-server:8080"

# Configuration file contains non-sensitive values
# config.yaml doesn't include endpoint
```

### Local-Only Operation

The system is designed to run entirely locally. Configuration requirements:

1. **LLM endpoint** must point to local server (default: `localhost:11434`)
2. **Project root** must be local directory
3. **Web research** can be disabled for complete offline operation

## Troubleshooting

### Configuration not found

If no configuration file is found, the system uses built-in defaults. To confirm which configuration is being used, enable debug logging:

```bash
export LOCAL_AI_LOG_LEVEL="debug"
python src/main.py
```

### Invalid configuration values

Validation errors include specific guidance. Common issues:

- **Temperature out of range**: Must be 0.0 to 2.0
- **Context length too small**: Must be >= max_tokens
- **Invalid backend**: Must be ollama, llamacpp, or openai-compatible
- **Project root doesn't exist**: Ensure directory exists before starting

### Environment variables not working

Ensure environment variables are exported before running the application:

```bash
# Wrong - variable only set for echo command
LOCAL_AI_LOG_LEVEL="debug"
python src/main.py

# Right - variable exported for all subsequent commands
export LOCAL_AI_LOG_LEVEL="debug"
python src/main.py
```
