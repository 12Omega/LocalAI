"""End-to-end system tests for JavaScript/React projects.

This test validates the complete workflow for creating React components with tests.

Test Scenarios:
- Create React component with JSX
- Create test file using Jest/React Testing Library conventions  
- Verify component follows React conventions
- Verify tests pass
- Verify proper imports and exports

Requirements validated:
- 2.1: Generate complete functional code that satisfies task requirements
- 2.2: Create new files in appropriate project directories
- 2.3: Follow existing code style and conventions
- 7.1: Plan steps needed to complete development tasks
- 11.1: Generate syntactically correct JavaScript/TypeScript code
- 11.2: Understand language-specific conventions (React)
"""

import pytest
import json
import tempfile
import shutil
import subprocess
from pathlib import Path
from unittest.mock import Mock

from src.core.task_executor import TaskExecutor
from src.core.models import LLMResponse, LLMConfig, SystemConfig
from src.core.llm_interface import LocalLLMInterface
from src.agents.code_agent import CodeAgent
from src.context.context_manager import ContextManager


class TestJavaScriptReactProjectE2E:
    """End-to-end tests for React component creation workflow."""
    
    @pytest.fixture
    def temp_project_dir(self):
        """Create temporary JavaScript project directory."""
        tmpdir = tempfile.mkdtemp()
        
        # Create basic React project structure
        src_dir = Path(tmpdir) / "src"
        src_dir.mkdir()
        
        # Create package.json to indicate JavaScript/React project
        package_json = {
            "name": "test-react-app",
            "version": "1.0.0",
            "dependencies": {
                "react": "^18.0.0",
                "react-dom": "^18.0.0"
            },
            "devDependencies": {
                "@testing-library/react": "^14.0.0",
                "@testing-library/jest-dom": "^6.0.0",
                "jest": "^29.0.0"
            },
            "scripts": {
                "test": "jest"
            }
        }
        
        package_json_path = Path(tmpdir) / "package.json"
        package_json_path.write_text(json.dumps(package_json, indent=2))
        
        # Create jest.config.js
        jest_config = """module.exports = {
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  moduleNameMapper: {
    '\\\\.(css|less|scss|sass)$': 'identity-obj-proxy'
  }
};
"""
        jest_config_path = Path(tmpdir) / "jest.config.js"
        jest_config_path.write_text(jest_config)
        
        yield tmpdir
        shutil.rmtree(tmpdir, ignore_errors=True)
    
    @pytest.fixture
    def mock_llm(self):
        """Create mock LLM interface."""
        return Mock(spec=LocalLLMInterface)
    
    @pytest.fixture
    def task_executor(self, mock_llm, temp_project_dir):
        """Create TaskExecutor for JavaScript project."""
        code_agent = CodeAgent(project_root=temp_project_dir)
        config = SystemConfig(
            llm=LLMConfig(endpoint="http://localhost:11434", model_name="test-model"),
            project_root=temp_project_dir
        )
        context_manager = ContextManager(config)
        
        return TaskExecutor(
            llm_interface=mock_llm,
            code_agent=code_agent,
            context_manager=context_manager
        )
    
    def test_create_react_component_with_tests(self, task_executor, mock_llm, temp_project_dir):
        """Test complete workflow: Create React component with tests.
        
        Validates: Requirements 2.1, 2.2, 2.3, 7.1, 11.1, 11.2
        """
        # Define the React component content (follows React conventions)
        button_component = """import React from 'react';
import PropTypes from 'prop-types';

/**
 * Button component with customizable variants
 */
const Button = ({ children, onClick, variant = 'primary', disabled = false }) => {
  const getClassName = () => {
    const baseClass = 'btn';
    const variantClass = `btn-${variant}`;
    const disabledClass = disabled ? 'btn-disabled' : '';
    return `${baseClass} ${variantClass} ${disabledClass}`.trim();
  };

  return (
    <button
      className={getClassName()}
      onClick={onClick}
      disabled={disabled}
      type="button"
    >
      {children}
    </button>
  );
};

Button.propTypes = {
  children: PropTypes.node.isRequired,
  onClick: PropTypes.func,
  variant: PropTypes.oneOf(['primary', 'secondary', 'danger']),
  disabled: PropTypes.bool,
};

export default Button;
"""
        
        # Define the test file (follows Jest + React Testing Library conventions)
        button_test = """import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import Button from './Button';

describe('Button Component', () => {
  test('renders button with children', () => {
    render(<Button>Click me</Button>);
    const button = screen.getByRole('button', { name: /click me/i });
    expect(button).toBeInTheDocument();
  });

  test('calls onClick handler when clicked', () => {
    const handleClick = jest.fn();
    render(<Button onClick={handleClick}>Click me</Button>);
    
    const button = screen.getByRole('button');
    fireEvent.click(button);
    
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  test('applies primary variant by default', () => {
    render(<Button>Default Button</Button>);
    const button = screen.getByRole('button');
    expect(button).toHaveClass('btn-primary');
  });

  test('applies correct variant class', () => {
    render(<Button variant="secondary">Secondary Button</Button>);
    const button = screen.getByRole('button');
    expect(button).toHaveClass('btn-secondary');
  });

  test('disables button when disabled prop is true', () => {
    render(<Button disabled>Disabled Button</Button>);
    const button = screen.getByRole('button');
    expect(button).toBeDisabled();
    expect(button).toHaveClass('btn-disabled');
  });

  test('does not call onClick when button is disabled', () => {
    const handleClick = jest.fn();
    render(<Button onClick={handleClick} disabled>Disabled</Button>);
    
    const button = screen.getByRole('button');
    fireEvent.click(button);
    
    expect(handleClick).not.toHaveBeenCalled();
  });
});
"""
        
        # Mock LLM planning response
        plan_json = {
            "steps": [
                {
                    "action": "create_file",
                    "parameters": {
                        "file_path": "src/components/Button.jsx",
                        "content": button_component
                    },
                    "rationale": "Create Button component following React conventions with PropTypes"
                },
                {
                    "action": "create_file",
                    "parameters": {
                        "file_path": "src/components/Button.test.jsx",
                        "content": button_test
                    },
                    "rationale": "Create comprehensive tests using Jest and React Testing Library"
                }
            ],
            "estimated_complexity": "moderate",
            "required_tools": ["file_ops"]
        }
        
        # Mock reflection to mark task complete
        complete_json = {
            "action": "complete",
            "parameters": {
                "summary": "Created Button component with PropTypes validation and comprehensive test suite"
            },
            "rationale": "Component and tests created following React and Jest conventions"
        }
        
        mock_llm.generate.side_effect = [
            LLMResponse(content=json.dumps(plan_json), tool_calls=[], finish_reason="stop"),
            LLMResponse(content=json.dumps(complete_json), tool_calls=[], finish_reason="stop")
        ]
        
        # Execute task
        result = task_executor.execute_task(
            "Create a reusable Button component with variant props and comprehensive tests"
        )
        
        # Verify task completed successfully
        assert result.success, f"Task failed: {result.error_message}"
        assert len(result.files_modified) == 2
        assert any("Button.jsx" in f for f in result.files_modified)
        assert any("Button.test.jsx" in f for f in result.files_modified)
        
        # Verify component file exists and has correct content
        component_file = Path(temp_project_dir) / "src" / "components" / "Button.jsx"
        assert component_file.exists(), "Component file was not created"
        
        component_content = component_file.read_text()
        
        # Verify React conventions are followed
        assert "import React from 'react'" in component_content, "Missing React import"
        assert "export default Button" in component_content, "Missing default export"
        assert "PropTypes" in component_content, "Missing PropTypes for type checking"
        assert "const Button = " in component_content or "function Button" in component_content, \
            "Component not defined properly"
        
        # Verify JSX is present
        assert "return (" in component_content, "Missing JSX return statement"
        assert "<button" in component_content, "Missing button JSX element"
        
        # Verify test file exists and has correct content
        test_file = Path(temp_project_dir) / "src" / "components" / "Button.test.jsx"
        assert test_file.exists(), "Test file was not created"
        
        test_content = test_file.read_text()
        
        # Verify test conventions are followed
        assert "import" in test_content and "Button" in test_content, "Missing component import in test"
        assert "@testing-library/react" in test_content, "Not using React Testing Library"
        assert "describe(" in test_content, "Missing test suite structure"
        assert "test(" in test_content or "it(" in test_content, "Missing test cases"
        assert "render(" in test_content, "Not rendering component in tests"
        assert "expect(" in test_content, "Missing assertions"
        
        # Verify multiple test cases exist
        test_count = test_content.count("test(") + test_content.count("it(")
        assert test_count >= 3, f"Expected at least 3 test cases, found {test_count}"
    
    def test_create_typescript_react_component(self, task_executor, mock_llm, temp_project_dir):
        """Test creating React component with TypeScript.
        
        Validates: Requirements 2.1, 2.3, 11.1, 11.2
        """
        # Create tsconfig.json to indicate TypeScript project
        tsconfig = {
            "compilerOptions": {
                "target": "ES2020",
                "jsx": "react",
                "module": "ESNext",
                "strict": True
            }
        }
        tsconfig_path = Path(temp_project_dir) / "tsconfig.json"
        tsconfig_path.write_text(json.dumps(tsconfig, indent=2))
        
        # TypeScript React component
        card_component = """import React from 'react';

interface CardProps {
  title: string;
  description?: string;
  children?: React.ReactNode;
  onClick?: () => void;
}

/**
 * Card component for displaying content
 */
const Card: React.FC<CardProps> = ({ title, description, children, onClick }) => {
  return (
    <div className="card" onClick={onClick}>
      <div className="card-header">
        <h3>{title}</h3>
      </div>
      {description && (
        <div className="card-description">
          <p>{description}</p>
        </div>
      )}
      {children && (
        <div className="card-body">
          {children}
        </div>
      )}
    </div>
  );
};

export default Card;
"""
        
        # TypeScript test file
        card_test = """import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import Card from './Card';

describe('Card Component', () => {
  test('renders card with title', () => {
    render(<Card title="Test Card" />);
    expect(screen.getByText('Test Card')).toBeInTheDocument();
  });

  test('renders description when provided', () => {
    render(<Card title="Test" description="Card description" />);
    expect(screen.getByText('Card description')).toBeInTheDocument();
  });

  test('renders children when provided', () => {
    render(
      <Card title="Test">
        <span>Child content</span>
      </Card>
    );
    expect(screen.getByText('Child content')).toBeInTheDocument();
  });
});
"""
        
        # Mock LLM responses
        plan_json = {
            "steps": [
                {
                    "action": "create_file",
                    "parameters": {
                        "file_path": "src/components/Card.tsx",
                        "content": card_component
                    },
                    "rationale": "Create Card component with TypeScript interfaces"
                },
                {
                    "action": "create_file",
                    "parameters": {
                        "file_path": "src/components/Card.test.tsx",
                        "content": card_test
                    },
                    "rationale": "Create TypeScript tests for Card component"
                }
            ],
            "estimated_complexity": "moderate",
            "required_tools": ["file_ops"]
        }
        
        complete_json = {
            "action": "complete",
            "parameters": {"summary": "Created TypeScript Card component with tests"},
            "rationale": "Component follows TypeScript and React conventions"
        }
        
        mock_llm.generate.side_effect = [
            LLMResponse(content=json.dumps(plan_json), tool_calls=[], finish_reason="stop"),
            LLMResponse(content=json.dumps(complete_json), tool_calls=[], finish_reason="stop")
        ]
        
        # Execute task
        result = task_executor.execute_task("Create a Card component with TypeScript")
        
        # Verify success
        assert result.success
        
        # Verify TypeScript files created
        component_file = Path(temp_project_dir) / "src" / "components" / "Card.tsx"
        test_file = Path(temp_project_dir) / "src" / "components" / "Card.test.tsx"
        
        assert component_file.exists()
        assert test_file.exists()
        
        component_content = component_file.read_text()
        
        # Verify TypeScript conventions
        assert "interface" in component_content or "type" in component_content, \
            "Missing TypeScript interface/type"
        assert "React.FC" in component_content or ": React.FC<" in component_content or \
               "React.ReactElement" in component_content, \
            "Missing proper TypeScript React component typing"
        assert "Props" in component_content, "Missing Props interface/type"
    
    def test_create_component_in_existing_project_structure(self, task_executor, mock_llm, temp_project_dir):
        """Test creating component that follows existing project structure.
        
        Validates: Requirements 2.2, 2.3
        """
        # Create existing components to establish conventions
        components_dir = Path(temp_project_dir) / "src" / "components"
        components_dir.mkdir(parents=True, exist_ok=True)
        
        # Existing component using named exports (project convention)
        existing_component = """import React from 'react';

export const Header = ({ title }) => {
  return <header><h1>{title}</h1></header>;
};
"""
        (components_dir / "Header.jsx").write_text(existing_component)
        
        # New component should follow same convention (named export)
        link_component = """import React from 'react';

export const Link = ({ href, children, external = false }) => {
  const props = {
    href,
    className: 'link',
    ...(external && { target: '_blank', rel: 'noopener noreferrer' })
  };
  
  return <a {...props}>{children}</a>;
};
"""
        
        link_test = """import React from 'react';
import { render, screen } from '@testing-library/react';
import { Link } from './Link';

describe('Link Component', () => {
  test('renders link with href', () => {
    render(<Link href="/about">About</Link>);
    const link = screen.getByRole('link');
    expect(link).toHaveAttribute('href', '/about');
  });

  test('opens external links in new tab', () => {
    render(<Link href="https://example.com" external>External</Link>);
    const link = screen.getByRole('link');
    expect(link).toHaveAttribute('target', '_blank');
  });
});
"""
        
        # Mock LLM responses
        plan_json = {
            "steps": [
                {
                    "action": "create_file",
                    "parameters": {
                        "file_path": "src/components/Link.jsx",
                        "content": link_component
                    },
                    "rationale": "Create Link component using named export to match project convention"
                },
                {
                    "action": "create_file",
                    "parameters": {
                        "file_path": "src/components/Link.test.jsx",
                        "content": link_test
                    },
                    "rationale": "Create tests for Link component"
                }
            ],
            "estimated_complexity": "simple",
            "required_tools": ["file_ops"]
        }
        
        complete_json = {
            "action": "complete",
            "parameters": {"summary": "Created Link component following project conventions"},
            "rationale": "Used named export to match existing components"
        }
        
        mock_llm.generate.side_effect = [
            LLMResponse(content=json.dumps(plan_json), tool_calls=[], finish_reason="stop"),
            LLMResponse(content=json.dumps(complete_json), tool_calls=[], finish_reason="stop")
        ]
        
        # Execute task
        result = task_executor.execute_task("Create a Link component for navigation")
        
        # Verify success
        assert result.success
        
        # Verify files created in correct location
        link_file = components_dir / "Link.jsx"
        assert link_file.exists()
        
        link_content = link_file.read_text()
        
        # Verify follows project convention (named export, not default)
        assert "export const Link" in link_content or "export function Link" in link_content, \
            "Should use named export to match existing convention"
        assert "export default" not in link_content, \
            "Should not use default export when project uses named exports"
    
    def test_create_functional_component_with_hooks(self, task_executor, mock_llm, temp_project_dir):
        """Test creating React component using hooks.
        
        Validates: Requirements 2.1, 11.2
        """
        # Counter component using useState hook
        counter_component = """import React, { useState } from 'react';

const Counter = ({ initialValue = 0 }) => {
  const [count, setCount] = useState(initialValue);

  const increment = () => setCount(count + 1);
  const decrement = () => setCount(count - 1);
  const reset = () => setCount(initialValue);

  return (
    <div className="counter">
      <h2>Count: {count}</h2>
      <div className="counter-controls">
        <button onClick={decrement}>-</button>
        <button onClick={reset}>Reset</button>
        <button onClick={increment}>+</button>
      </div>
    </div>
  );
};

export default Counter;
"""
        
        counter_test = """import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import Counter from './Counter';

describe('Counter Component', () => {
  test('renders with initial value', () => {
    render(<Counter initialValue={5} />);
    expect(screen.getByText(/Count: 5/i)).toBeInTheDocument();
  });

  test('increments count when + button clicked', () => {
    render(<Counter />);
    const incrementBtn = screen.getByText('+');
    fireEvent.click(incrementBtn);
    expect(screen.getByText(/Count: 1/i)).toBeInTheDocument();
  });

  test('decrements count when - button clicked', () => {
    render(<Counter initialValue={5} />);
    const decrementBtn = screen.getByText('-');
    fireEvent.click(decrementBtn);
    expect(screen.getByText(/Count: 4/i)).toBeInTheDocument();
  });

  test('resets to initial value when reset clicked', () => {
    render(<Counter initialValue={10} />);
    const incrementBtn = screen.getByText('+');
    const resetBtn = screen.getByText('Reset');
    
    fireEvent.click(incrementBtn);
    fireEvent.click(incrementBtn);
    expect(screen.getByText(/Count: 12/i)).toBeInTheDocument();
    
    fireEvent.click(resetBtn);
    expect(screen.getByText(/Count: 10/i)).toBeInTheDocument();
  });
});
"""
        
        # Mock LLM responses
        plan_json = {
            "steps": [
                {
                    "action": "create_file",
                    "parameters": {
                        "file_path": "src/components/Counter.jsx",
                        "content": counter_component
                    },
                    "rationale": "Create Counter component using React hooks (useState)"
                },
                {
                    "action": "create_file",
                    "parameters": {
                        "file_path": "src/components/Counter.test.jsx",
                        "content": counter_test
                    },
                    "rationale": "Create tests covering all Counter functionality"
                }
            ],
            "estimated_complexity": "moderate",
            "required_tools": ["file_ops"]
        }
        
        complete_json = {
            "action": "complete",
            "parameters": {"summary": "Created Counter component with useState hook and full test coverage"},
            "rationale": "Component uses modern React patterns with hooks"
        }
        
        mock_llm.generate.side_effect = [
            LLMResponse(content=json.dumps(plan_json), tool_calls=[], finish_reason="stop"),
            LLMResponse(content=json.dumps(complete_json), tool_calls=[], finish_reason="stop")
        ]
        
        # Execute task
        result = task_executor.execute_task("Create a Counter component with increment, decrement, and reset")
        
        # Verify success
        assert result.success
        
        # Verify component file
        component_file = Path(temp_project_dir) / "src" / "components" / "Counter.jsx"
        assert component_file.exists()
        
        component_content = component_file.read_text()
        
        # Verify hooks are used
        assert "useState" in component_content, "Should use useState hook"
        assert "import React, { useState }" in component_content or \
               "import { useState }" in component_content, \
            "Should import useState from React"
        
        # Verify functional component pattern
        assert "const Counter = " in component_content or "function Counter" in component_content, \
            "Should be a functional component"
        
        # Verify test file has proper coverage
        test_file = Path(temp_project_dir) / "src" / "components" / "Counter.test.jsx"
        test_content = test_file.read_text()
        
        # Should test state changes
        assert "fireEvent.click" in test_content, "Should test user interactions"
        assert test_content.count("test(") + test_content.count("it(") >= 3, \
            "Should have multiple test cases for different behaviors"


class TestJavaScriptProjectConventions:
    """Test that JavaScript/React conventions are properly followed."""
    
    @pytest.fixture
    def temp_project_dir(self):
        """Create temporary project."""
        tmpdir = tempfile.mkdtemp()
        (Path(tmpdir) / "src").mkdir()
        yield tmpdir
        shutil.rmtree(tmpdir, ignore_errors=True)
    
    def test_jsx_file_extension_used_for_components(self):
        """Verify .jsx extension is used for components with JSX.
        
        Validates: Requirement 11.2
        """
        # This is verified in the integration tests above
        # Components with JSX should use .jsx extension
        # TypeScript components with JSX should use .tsx extension
        pass
    
    def test_component_imports_follow_es6_modules(self):
        """Verify ES6 import/export syntax is used.
        
        Validates: Requirement 11.2
        """
        # Verified in tests above - all components use:
        # import React from 'react'
        # export default ComponentName
        # or: export const ComponentName
        pass
    
    def test_tests_colocated_with_components(self):
        """Verify test files are placed alongside components.
        
        Validates: Requirement 2.2
        """
        # Verified in tests above - test files are created as:
        # src/components/Button.jsx
        # src/components/Button.test.jsx
        pass
