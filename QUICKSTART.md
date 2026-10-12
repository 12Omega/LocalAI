# Quick Start Guide

Get up and running with the Local AI Development Environment in 5 minutes.

## Prerequisites

- Python 3.8 or higher
- A local LLM (we'll use Ollama in this guide)

## Step 1: Install Ollama

**macOS/Linux**:
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

**Windows**:
Download from [https://ollama.ai/download](https://ollama.ai/download)

## Step 2: Pull a Model

```bash
# Pull a code-focused model (this may take a few minutes)
ollama pull codellama:13b

# Verify it works
ollama run codellama:13b "Write a hello world in Python"
```

## Step 3: Set Up the Development Environment

```bash
# Clone/navigate to the project
cd local-ai-dev-environment

# Create virtual environment
python -m venv venv

# Activate it
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Step 4: Configure

```bash
# Copy example configuration
cp config.example.yaml config.yaml

# The defaults work with Ollama, but you can customize:
# - model_name: The model to use (default: codellama:13b)
# - project_root: Where to work (default: current directory)
# - log_level: Verbosity (default: info)
```

**Minimal config.yaml**:
```yaml
llm:
  endpoint: "http://localhost:11434"
  model_name: "codellama:13b"
  backend_type: "ollama"

project_root: "."
log_level: "info"
```

## Step 5: Test the Setup

```bash
# Test LLM connection
python src/main.py --test-llm

# Expected output:
# ✓ Connected to LLM successfully
# ✓ Model: codellama:13b
# ✓ Backend: ollama
```

## Step 6: Try Your First Task

Create a simple project:

```bash
# Create a test directory
mkdir my-first-ai-project
cd my-first-ai-project

# Ask AI to create a calculator module
python ../src/main.py "Create a Python module called calculator.py with functions for add, subtract, multiply, and divide. Include type hints and unit tests."
```

**What happens**:
1. AI analyzes the task
2. Creates `calculator.py` with the functions
3. Creates `test_calculator.py` with unit tests
4. Runs the tests to verify correctness

**Check the results**:
```bash
# See what was created
ls -la

# Look at the code
cat calculator.py
cat test_calculator.py

# Run the tests manually
pytest test_calculator.py -v
```

## Common Tasks

### Task 1: Create a Web API

```bash
python src/main.py "Create a Flask REST API with:
- GET /api/users - list users
- POST /api/users - create user
- Include validation and tests"
```

### Task 2: Add Features

```bash
python src/main.py "Add input validation to the calculator.py module:
- Check for valid number inputs
- Handle division by zero
- Return descriptive error messages
- Update tests"
```

### Task 3: Debug Issues

```bash
python src/main.py "The test_divide_by_zero test is failing. 
Debug and fix the issue in calculator.py"
```

### Task 4: Refactor Code

```bash
python src/main.py "Refactor calculator.py to use a Calculator class
instead of standalone functions. Update tests accordingly."
```

## Tips for Success

### ✅ DO:
- **Be specific**: "Create a User class with name, email, and validation"
- **Request tests**: "Include unit tests with >90% coverage"
- **Specify format**: "Use Python type hints and Google-style docstrings"
- **Mention conventions**: "Follow PEP 8 style guidelines"
- **Iterate**: Start simple, then refine

### ❌ DON'T:
- **Be vague**: "Make it better"
- **Skip review**: Always review generated code
- **Expect perfection**: First attempt may need refinement
- **Forget tests**: Always ask for tests explicitly
- **Overcomplicate**: Break complex tasks into steps

## Example Task Descriptions

### Good Examples

**Creating a module**:
```
Create a UserValidator class in src/validators/user.py with methods:
- validate_email(email) -> bool: Check valid email format
- validate_password(password) -> bool: Min 8 chars, 1 uppercase, 1 number
- validate_username(username) -> bool: 3-20 alphanumeric chars

Include:
- Type hints for all methods
- Docstrings explaining validation rules
- Unit tests with pytest covering valid and invalid inputs
- Use regex for email validation
```

**Fixing a bug**:
```
Fix the bug in src/auth.py line 45 where login fails for users with 
email addresses containing '+' character. The error is:
  ValueError: invalid email format

Update the email validation regex to allow '+' character.
Ensure tests cover this case.
```

**Adding a feature**:
```
Add rate limiting to the /api/login endpoint in src/api/routes.py:
- Limit to 5 attempts per minute per IP address
- Return 429 Too Many Requests when exceeded
- Use Flask-Limiter library
- Add configuration for rate limit values
- Include integration tests
```

## Configuration Options

### Common Settings

```yaml
# Use a different model
llm:
  model_name: "codellama:7b"  # Faster, less accurate

# Enable debug logging
log_level: "debug"

# Disable web research (offline mode)
web_research_enabled: false

# Change project location
project_root: "/path/to/my/project"
```

### Environment Variables

```bash
# Quick overrides without editing config file
export LOCAL_AI_LLM_MODEL="llama2:13b"
export LOCAL_AI_LOG_LEVEL="debug"
export LOCAL_AI_PROJECT_ROOT="/my/project"

python src/main.py "your task here"
```

## Troubleshooting

### "Could not connect to LLM"

**Problem**: Can't reach Ollama

**Fix**:
```bash
# Check if Ollama is running
ollama list

# If not, start it
ollama serve

# Test connection
curl http://localhost:11434/api/tags
```

### "Model not found"

**Problem**: Model hasn't been pulled

**Fix**:
```bash
# List available models
ollama list

# Pull the model you need
ollama pull codellama:13b
```

### Slow Performance

**Problem**: Tasks take too long

**Fix**:
```bash
# Use a smaller model
ollama pull codellama:7b

# Update config.yaml
llm:
  model_name: "codellama:7b"
```

### Tests Failing

**Problem**: Generated tests don't pass

**Fix**:
```bash
# Run tests to see errors
pytest -v

# Ask AI to fix
python src/main.py "Fix the failing tests. The errors are:
[paste test output here]"
```

## Next Steps

Now that you're up and running:

1. **Try the examples**: Explore [examples/projects/](examples/projects/) for multi-language samples
2. **Read workflows**: Check [docs/workflows.md](docs/workflows.md) for common patterns
3. **Understand architecture**: Review [docs/architecture.md](docs/architecture.md) for design details
4. **Contribute**: See [CONTRIBUTING.md](CONTRIBUTING.md) to contribute improvements

## Getting Help

- **Documentation**: Check [docs/README.md](docs/README.md) for full documentation index
- **Issues**: Search [existing issues](https://github.com/your-repo/issues) for solutions
- **Questions**: Open a discussion on GitHub

## Quick Reference Card

```bash
# Execute task
python src/main.py "task description"

# Debug mode
python src/main.py --log-level debug "task"

# Test LLM
python src/main.py --test-llm

# Run tests
pytest                    # All tests
pytest tests/unit/        # Unit tests only
pytest --cov=src         # With coverage

# Lint
pylint src/              # Check code quality
black src/               # Auto-format
mypy src/                # Type checking
```

## Success! 🎉

You're now ready to use the Local AI Development Environment. Start with simple tasks and gradually tackle more complex projects.

**Remember**: The AI is a powerful assistant, but always review the generated code before using it in production.

Happy coding! 🚀
