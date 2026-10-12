# Documentation Index

Welcome to the Local AI Development Environment documentation. This index helps you find the information you need.

## Getting Started

- **[Main README](../README.md)** - Start here for installation, configuration, and basic usage
- **[Configuration Guide](configuration.md)** - Detailed configuration options and environment variables
- **[Common Workflows](workflows.md)** - Practical workflows and best practices for daily use

## For Developers

- **[Developer Guide](developer_guide.md)** - Complete guide for contributors
  - Architecture overview
  - Component interactions
  - API documentation
  - Contributing guidelines
  - Testing strategy
  
- **[Architecture Documentation](architecture.md)** - Deep dive into system design
  - Core architectural principles
  - Component detailed architecture
  - Data flow diagrams
  - Concurrency and state management
  - Security architecture
  - Extensibility points

- **[Contributing Guide](../CONTRIBUTING.md)** - How to contribute to the project
  - Code of conduct
  - Development workflow
  - Coding standards
  - Pull request process
  - Issue reporting

## Specialized Topics

- **[Self-Improvement Implementation](self_improvement_implementation.md)** - Details on the self-improvement engine
  - How it works
  - Safety mechanisms
  - Usage guidelines

## Examples

- **[Example Projects](../examples/projects/)** - Multi-language example projects
  - [Python Flask API](../examples/projects/python-flask-api/) - RESTful API example
  - [JavaScript React App](../examples/projects/javascript-react-app/) - Frontend application
  - [Java Spring API](../examples/projects/java-spring-api/) - Enterprise Java application
  - [Go CLI Tool](../examples/projects/go-cli-tool/) - Command-line tool

- **[Code Examples](../examples/)** - Standalone code examples
  - Task executor examples
  - File operations demo
  - Context manager demo
  - Self-improvement demo

## Quick Reference

### Installation

```bash
# Clone and setup
cd local-ai-dev-environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure
cp config.example.yaml config.yaml
# Edit config.yaml with your LLM settings

# Verify
pytest tests/unit/
```

### Basic Usage

```bash
# Execute a task
python src/main.py "Create a Python calculator module with tests"

# With specific configuration
python src/main.py --config my-config.yaml "Add validation to user input"

# Debug mode
python src/main.py --log-level debug "Fix the bug in authentication"
```

### Common Commands

```bash
# Run all tests
pytest

# Run specific test category
pytest tests/unit/          # Unit tests
pytest tests/properties/    # Property-based tests
pytest tests/integration/   # Integration tests

# Check code coverage
pytest --cov=src --cov-report=html

# Lint code
pylint src/
mypy src/

# Format code
black src/
isort src/
```

## Documentation by Role

### I'm a New User

Start with:
1. [Main README](../README.md) - Installation and first steps
2. [Configuration Guide](configuration.md) - Set up your environment
3. [Common Workflows](workflows.md) - Learn practical usage patterns

### I'm a Developer/Contributor

Read:
1. [Developer Guide](developer_guide.md) - Understand the architecture
2. [Architecture Documentation](architecture.md) - Deep dive into design
3. [Contributing Guide](../CONTRIBUTING.md) - How to contribute

### I'm Integrating This System

Review:
1. [Architecture Documentation](architecture.md) - Understand components
2. [API Documentation](developer_guide.md#api-documentation) - Component interfaces
3. [Configuration Guide](configuration.md) - Integration options

### I'm Troubleshooting

Check:
1. [Troubleshooting Section](../README.md#troubleshooting) - Common issues
2. [Common Workflows](workflows.md#troubleshooting-common-issues) - Workflow-specific issues
3. [Developer Guide](developer_guide.md#testing-strategy) - Testing and debugging

## Documentation Standards

All documentation follows these standards:

- **Markdown Format**: All docs use GitHub-flavored Markdown
- **Code Examples**: All code examples are tested and working
- **Internal Links**: Use relative paths for internal documentation links
- **External Links**: Include full URLs for external references
- **Versioning**: Documentation version matches code version
- **Language**: Written in English with clear, concise language

## Contributing to Documentation

Found an issue or want to improve documentation?

1. **Small fixes**: Submit a PR with the change
2. **New sections**: Open an issue to discuss first
3. **Clarifications**: Add them and submit a PR

See [Contributing Guide](../CONTRIBUTING.md) for details.

## Feedback

Have suggestions for improving documentation? Please:
- Open an issue on GitHub
- Tag with "documentation" label
- Describe what's unclear or missing

## Version Information

**Documentation Version**: 1.0.0
**Last Updated**: 2026-09-06
**Covers System Version**: 1.0.0

---

**Need help?** Start with the [Main README](../README.md) or check the [Common Workflows](workflows.md) guide.
