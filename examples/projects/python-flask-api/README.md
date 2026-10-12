# Python Flask API Example Project

This example demonstrates using the Local AI Development Environment to build a Python Flask REST API from scratch.

## Project Structure

```
python-flask-api/
├── app/
│   ├── __init__.py
│   ├── models.py
│   ├── routes.py
│   └── utils.py
├── tests/
│   ├── test_models.py
│   └── test_routes.py
├── requirements.txt
├── config.py
└── run.py
```

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the application:**
   ```bash
   python run.py
   ```

3. **Run tests:**
   ```bash
   pytest tests/
   ```

## Example Tasks for the AI

### Task 1: Create a new endpoint
```
Create a new GET endpoint /api/users that returns a list of all users from the database.
Include appropriate error handling and tests.
```

### Task 2: Add input validation
```
Add input validation to the POST /api/users endpoint to ensure:
- Email is valid format
- Username is at least 3 characters
- Password is at least 8 characters
Return 400 Bad Request with error details if validation fails.
```

### Task 3: Debug a failing test
```
The test_user_creation test is failing. Debug and fix the issue.
```

### Task 4: Refactor for better organization
```
Refactor the routes.py file to separate user routes and authentication routes
into separate modules: routes/users.py and routes/auth.py
```

## What the AI Will Do

1. **Analyze Context**: The AI will scan the project structure, identify it as a Flask application, and understand the existing code organization.

2. **Generate Code**: The AI will create new files or modify existing ones following Flask conventions and the project's coding style.

3. **Write Tests**: The AI will automatically create corresponding test files using pytest and Flask's test client.

4. **Verify Changes**: The AI will run the tests to ensure the implementation works correctly.

## Expected Behavior

- Code follows PEP 8 style guidelines
- Tests use pytest fixtures and Flask test client
- Error handling includes appropriate HTTP status codes
- Database operations use proper ORM patterns (SQLAlchemy)
- Logging is included for debugging
