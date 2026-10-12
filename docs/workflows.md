# Common Workflows and Best Practices

This document provides practical workflows and best practices for using the Local AI Development Environment effectively.

## Table of Contents

- [Getting Started Workflows](#getting-started-workflows)
- [Development Workflows](#development-workflows)
- [Testing Workflows](#testing-workflows)
- [Debugging Workflows](#debugging-workflows)
- [Best Practices](#best-practices)
- [Troubleshooting Common Issues](#troubleshooting-common-issues)

## Getting Started Workflows

### First-Time Setup

**Workflow**: Set up the system for the first time

1. **Install prerequisites**:
   ```bash
   # Install Python 3.8+
   python --version
   
   # Install local LLM (Ollama recommended)
   # Visit https://ollama.ai for installation
   ```

2. **Set up the project**:
   ```bash
   cd local-ai-dev-environment
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure the system**:
   ```bash
   # Copy example configuration
   cp config.example.yaml config.yaml
   
   # Edit config.yaml:
   # - Set your LLM endpoint
   # - Set your model name
   # - Set project root
   ```

4. **Verify setup**:
   ```bash
   # Test LLM connection
   python src/main.py --test-llm
   
   # Run tests
   pytest tests/unit/
   ```

### Starting a New Project

**Workflow**: Use the system to bootstrap a new project

```bash
# 1. Create project directory
mkdir my-new-project
cd my-new-project

# 2. Initialize git
git init

# 3. Configure the AI for this project
export LOCAL_AI_PROJECT_ROOT="$(pwd)"

# 4. Ask AI to create project structure
python /path/to/local-ai-dev/src/main.py "Create a Python project structure with:
- src/ directory for source code
- tests/ directory for tests
- requirements.txt
- README.md
- .gitignore
- Setup.py for package installation
Follow Python best practices and include example modules."

# 5. Review generated files
ls -la

# 6. Commit initial structure
git add .
git commit -m "Initial project structure"
```

## Development Workflows

### Feature Development

**Workflow**: Implement a new feature from description to tested code

1. **Define the feature**:
   ```bash
   # Create a clear task description
   TASK="Create a UserAuthentication module with:
   - Login function that accepts username and password
   - Logout function
   - Password validation (min 8 chars, 1 uppercase, 1 number)
   - Session token generation
   - Include unit tests with >90% coverage
   - Follow existing project conventions"
   ```

2. **Execute the task**:
   ```bash
   python src/main.py "$TASK"
   ```

3. **Review the results**:
   ```bash
   # Check generated files
   git status
   git diff
   
   # Review code quality
   pylint src/
   
   # Check test coverage
   pytest --cov=src tests/
   ```

4. **Iterate if needed**:
   ```bash
   # If changes needed, provide feedback
   python src/main.py "Update UserAuthentication to also support OAuth2 login"
   ```

5. **Commit the feature**:
   ```bash
   git add src/auth/ tests/test_auth.py
   git commit -m "feat: Add user authentication module"
   ```

### Code Refactoring

**Workflow**: Refactor existing code while maintaining functionality

1. **Identify refactoring needs**:
   ```bash
   # Analyze code
   pylint src/legacy_module.py
   radon cc src/legacy_module.py  # Cyclomatic complexity
   ```

2. **Execute refactoring**:
   ```bash
   python src/main.py "Refactor src/legacy_module.py to:
   - Break down large functions into smaller ones (max 15 lines)
   - Extract duplicated code into helper functions
   - Add type hints
   - Improve variable naming
   - Maintain all existing functionality
   - Ensure all tests still pass"
   ```

3. **Verify refactoring**:
   ```bash
   # Run tests to ensure behavior unchanged
   pytest tests/test_legacy_module.py -v
   
   # Check improvements
   radon cc src/legacy_module.py
   pylint src/legacy_module.py
   ```

4. **Commit refactoring**:
   ```bash
   git add src/legacy_module.py
   git commit -m "refactor: Improve legacy module code quality"
   ```

### Adding Tests

**Workflow**: Add comprehensive tests to existing code

1. **Identify coverage gaps**:
   ```bash
   pytest --cov=src --cov-report=html
   open htmlcov/index.html  # Review uncovered code
   ```

2. **Generate tests**:
   ```bash
   python src/main.py "Add unit tests for src/utils/helpers.py covering:
   - All public functions
   - Edge cases (empty input, None, invalid types)
   - Error conditions
   - Use pytest fixtures for setup
   - Achieve >95% coverage"
   ```

3. **Run new tests**:
   ```bash
   pytest tests/test_helpers.py -v
   ```

4. **Add property-based tests** (for critical logic):
   ```bash
   python src/main.py "Add property-based tests for src/utils/validators.py using Hypothesis:
   - Email validation property
   - Phone number validation property
   - Date parsing property
   Run 100+ examples per test"
   ```

### Code Review Preparation

**Workflow**: Prepare code for review with AI assistance

1. **Self-review checklist**:
   ```bash
   python src/main.py "Review the changes in src/payment/ and:
   - Check for potential bugs
   - Identify security issues
   - Suggest performance improvements
   - Verify error handling is comprehensive
   - Ensure logging is adequate
   - Check for code duplication
   Generate a summary report"
   ```

2. **Address issues**:
   ```bash
   # Apply suggested fixes
   python src/main.py "Fix the security issue in src/payment/processor.py:
   Sanitize user input before SQL query construction"
   ```

3. **Generate documentation**:
   ```bash
   python src/main.py "Add docstrings to all public functions in src/payment/ 
   following Google style format"
   ```

## Testing Workflows

### Test-Driven Development (TDD)

**Workflow**: Write tests first, then implementation

1. **Write tests**:
   ```bash
   python src/main.py "Create unit tests for a Calculator class with methods:
   - add(a, b)
   - subtract(a, b)
   - multiply(a, b)
   - divide(a, b) with divide-by-zero error
   Use pytest and test all edge cases.
   Do NOT implement the Calculator class yet."
   ```

2. **Verify tests fail**:
   ```bash
   pytest tests/test_calculator.py  # Should fail (no implementation)
   ```

3. **Implement code**:
   ```bash
   python src/main.py "Implement the Calculator class in src/calculator.py 
   to make all tests in tests/test_calculator.py pass"
   ```

4. **Verify tests pass**:
   ```bash
   pytest tests/test_calculator.py -v  # Should pass now
   ```

### Integration Testing

**Workflow**: Test component interactions

1. **Set up test environment**:
   ```bash
   python src/main.py "Create integration test setup for the API module:
   - Test database (SQLite in-memory)
   - Mock external API calls
   - Test fixtures for common data
   - Cleanup after each test"
   ```

2. **Write integration tests**:
   ```bash
   python src/main.py "Add integration tests for user registration flow:
   - Test POST /api/register endpoint
   - Verify user stored in database
   - Check email sent (mocked)
   - Verify authentication works
   - Test error cases (duplicate email, invalid data)"
   ```

3. **Run integration tests**:
   ```bash
   pytest tests/integration/ -v
   ```

### Property-Based Testing

**Workflow**: Use Hypothesis for property-based tests

1. **Identify properties**:
   ```bash
   python src/main.py "Identify universal properties for the sorting algorithm in src/algorithms/sort.py:
   - Output length equals input length
   - Output contains same elements as input
   - Output is in ascending order
   - Sorting twice gives same result (idempotent)"
   ```

2. **Implement property tests**:
   ```bash
   python src/main.py "Create property-based tests for src/algorithms/sort.py:
   - Use Hypothesis library
   - Test properties across 100+ random inputs
   - Include edge cases (empty list, single element, duplicates)
   - Tag as Feature: sorting, Property: correctness"
   ```

3. **Run property tests**:
   ```bash
   pytest tests/properties/test_sort_properties.py -v
   ```

## Debugging Workflows

### Debugging Failing Tests

**Workflow**: Fix failing tests with AI assistance

1. **Run tests to identify failure**:
   ```bash
   pytest tests/test_user_service.py -v
   # FAILED tests/test_user_service.py::test_user_creation
   ```

2. **Get detailed failure information**:
   ```bash
   pytest tests/test_user_service.py::test_user_creation -vv
   ```

3. **Ask AI to debug**:
   ```bash
   python src/main.py "The test test_user_creation in tests/test_user_service.py is failing with:
   AssertionError: Expected user.email to be 'test@example.com', got 'test@example.co'
   
   Debug and fix the issue in src/services/user_service.py"
   ```

4. **Verify fix**:
   ```bash
   pytest tests/test_user_service.py::test_user_creation -v
   ```

### Debugging Runtime Errors

**Workflow**: Fix errors found during execution

1. **Capture error**:
   ```bash
   python src/main.py
   # Traceback showing error in src/api/routes.py line 45
   ```

2. **Provide context to AI**:
   ```bash
   python src/main.py "Fix the KeyError at src/api/routes.py:45:
   Error: KeyError: 'user_id'
   The error occurs when POST /api/users is called without user_id in the request.
   Add proper validation and return 400 Bad Request with error message."
   ```

3. **Test the fix**:
   ```bash
   # Test manually or with curl
   curl -X POST http://localhost:5000/api/users -d '{}'
   # Should return 400 with error message
   ```

### Performance Debugging

**Workflow**: Identify and fix performance issues

1. **Profile the code**:
   ```bash
   python -m cProfile -o profile.out src/main.py
   python -m pstats profile.out
   ```

2. **Identify bottleneck**:
   ```
   # pstats output shows slow_function() takes 80% of time
   ```

3. **Ask AI to optimize**:
   ```bash
   python src/main.py "Optimize slow_function() in src/processing/data.py:
   - Currently takes 5 seconds for 10k records
   - Target <1 second
   - Consider caching, vectorization, or algorithm change
   - Maintain correctness (all tests must pass)
   - Add performance benchmark test"
   ```

4. **Verify improvement**:
   ```bash
   pytest tests/benchmark/test_performance.py -v
   # Should show significant improvement
   ```

## Best Practices

### Writing Effective Task Descriptions

**Good task descriptions**:
- Are specific and concrete
- Include acceptance criteria
- Specify constraints
- Request tests explicitly
- Mention conventions to follow

**Example - Vague** ❌:
```
"Add user management"
```

**Example - Clear** ✅:
```
"Create a UserManager class in src/users/manager.py with methods:
- create_user(username, email, password) -> User
  - Validate email format
  - Hash password with bcrypt
  - Store in database
  - Return User object
- get_user(user_id) -> User
  - Raise UserNotFoundError if not exists
- update_user(user_id, **kwargs) -> User
- delete_user(user_id) -> bool

Include:
- Type hints for all methods
- Docstrings in Google format
- Error handling for all methods
- Unit tests with >90% coverage
- Use existing database connection from src/db.py"
```

### Iterative Development

**Approach**: Break large tasks into smaller iterations

Instead of:
```bash
python src/main.py "Build a complete e-commerce platform with user auth, product catalog, shopping cart, payment processing, and admin dashboard"
```

Do:
```bash
# Iteration 1: Foundation
python src/main.py "Create project structure for e-commerce platform with:
- User authentication module
- Database models for User, Product, Order
- Basic API endpoints structure"

# Iteration 2: User features
python src/main.py "Implement user registration and login:
- POST /api/register
- POST /api/login
- JWT token generation
- Password hashing
- Include tests"

# Iteration 3: Products
python src/main.py "Implement product catalog:
- GET /api/products - list all
- GET /api/products/{id} - get one
- POST /api/products - create (admin only)
- Include pagination, search, filtering"

# Continue iteratively...
```

### Maintaining Code Quality

**Workflow**: Ensure quality throughout development

1. **Run linters regularly**:
   ```bash
   # After each change
   pylint src/
   flake8 src/
   mypy src/
   ```

2. **Maintain test coverage**:
   ```bash
   # Check coverage after adding code
   pytest --cov=src --cov-report=term-missing
   
   # If coverage drops, add tests
   python src/main.py "Add tests for new functions in src/new_module.py"
   ```

3. **Review generated code**:
   - Always review AI-generated code before committing
   - Check for security issues
   - Verify edge cases are handled
   - Ensure documentation is adequate

4. **Use version control**:
   ```bash
   # Commit frequently
   git add src/module.py tests/test_module.py
   git commit -m "feat: Add module with tests"
   
   # Can easily revert if needed
   git revert HEAD
   ```

### Handling AI Limitations

**When AI gets stuck or produces incorrect code**:

1. **Provide more context**:
   ```bash
   # Instead of: "Fix the bug"
   # Provide: "Fix the bug in line 45 where user_id is None causing TypeError.
   # This happens when users login with OAuth. Add check for None and handle gracefully."
   ```

2. **Break down the task**:
   ```bash
   # If complex task fails, break into steps
   # Step 1: "Create the data model"
   # Step 2: "Create the repository"
   # Step 3: "Create the service"
   # Step 4: "Create the API endpoint"
   ```

3. **Provide examples**:
   ```bash
   python src/main.py "Create a similar function to parse_json() in src/utils.py 
   but for parsing XML. Follow the same error handling pattern and return structure."
   ```

4. **Manual intervention**:
   - Sometimes manual fixes are faster
   - Edit the code yourself, then ask AI to add tests
   - Use AI for boilerplate, write complex logic manually

## Troubleshooting Common Issues

### LLM Not Responding

**Problem**: LLM requests timeout or hang

**Solutions**:
1. Check LLM is running: `ollama list` or check your LLM server
2. Test connection: `curl http://localhost:11434/api/tags`
3. Check logs: `--log-level debug`
4. Reduce context size: Use shorter task descriptions
5. Try smaller model: Switch from 34B to 13B model

### Code Quality Issues

**Problem**: Generated code doesn't follow conventions

**Solutions**:
1. Be explicit about conventions:
   ```bash
   python src/main.py "Create module following these conventions:
   - 4 spaces indentation
   - Type hints on all functions
   - Google-style docstrings
   - Max line length 100
   - Use dataclasses for data structures"
   ```

2. Provide example:
   ```bash
   python src/main.py "Create a new module similar to src/existing_module.py 
   following the same style and patterns"
   ```

3. Post-process with linters:
   ```bash
   black src/  # Auto-format
   isort src/  # Sort imports
   ```

### Tests Failing

**Problem**: Generated tests don't pass

**Solutions**:
1. Run tests and provide output:
   ```bash
   pytest tests/ -v > test_output.txt
   python src/main.py "Fix failing tests. Test output:
   $(cat test_output.txt)"
   ```

2. Ask for specific fixes:
   ```bash
   python src/main.py "The test test_user_creation fails because:
   - Expected user.name to be 'John', got 'john'
   Fix the normalization in create_user() to preserve case"
   ```

3. Simplify tests:
   - Complex mocking can confuse AI
   - Prefer integration tests over heavily mocked unit tests
   - Use fixtures instead of inline setup

### Import/Dependency Issues

**Problem**: Generated code has missing imports

**Solutions**:
1. Specify dependencies:
   ```bash
   python src/main.py "Create API client using 'requests' library.
   Add to requirements.txt if not present."
   ```

2. Fix imports manually and ask for review:
   ```bash
   # Fix imports yourself
   python src/main.py "Review src/api_client.py for any other issues"
   ```

### Performance Issues

**Problem**: System is slow

**Solutions**:
1. **Reduce model size**: Use 7B instead of 13B model
2. **Simplify tasks**: Break into smaller pieces
3. **Disable web research**: `export LOCAL_AI_WEB_RESEARCH=false`
4. **Use GPU**: Configure LLM backend to use GPU
5. **Reduce context**: Keep task descriptions concise

## Advanced Workflows

### Multi-Language Projects

**Workflow**: Working with projects using multiple languages

```bash
# Frontend + Backend example
python src/main.py "In the frontend/ directory:
Create React component UserProfile.tsx"

python src/main.py "In the backend/ directory:
Create Python Flask endpoint GET /api/user/{id}"

# AI will detect language per directory
```

### Database Migrations

**Workflow**: Managing database schema changes

```bash
# Create migration
python src/main.py "Create Alembic migration to add 'phone' column to users table:
- Column type: String(20)
- Nullable: True
- Add index on phone
Include up and down migrations"

# Apply migration
alembic upgrade head

# Verify
python src/main.py "Update User model in src/models/user.py to include phone field"
```

### API Documentation

**Workflow**: Generate API documentation

```bash
python src/main.py "Add OpenAPI/Swagger documentation to all endpoints in src/api/:
- Include request/response schemas
- Add example requests
- Document error codes
- Add authentication requirements
Configure Swagger UI at /api/docs"
```

### CI/CD Integration

**Workflow**: Use AI in CI/CD pipeline

```bash
#!/bin/bash
# .github/workflows/ai-review.sh

# Use AI to review PR changes
python local-ai-dev/src/main.py "Review the changes in this PR:
$(git diff main...HEAD)

Check for:
- Security issues
- Performance concerns
- Missing tests
- Code quality issues
Generate a review summary"
```

## Tips for Success

1. **Start Simple**: Begin with small, clear tasks to understand AI capabilities
2. **Iterate**: Don't expect perfection on first try; refine iteratively
3. **Be Specific**: More detail in task description = better results
4. **Review Always**: Never commit AI code without review
5. **Learn Patterns**: Observe what works and refine your prompts
6. **Use Version Control**: Easy rollback if AI makes mistakes
7. **Provide Feedback**: Guide AI with corrections and refinements
8. **Know Limitations**: AI is a tool, not a replacement for understanding
9. **Maintain Context**: Keep related changes together in one task
10. **Document Decisions**: Capture why certain approaches were chosen
