"""Unit tests for core data models."""

import pytest
from src.core.models import (
    ExecutionPlan,
    ExecutionStep,
    TaskResult,
    SearchResult,
    SymbolLocation,
    CodeAnalysis,
    SystemConfig,
    LLMConfig,
    FileTree,
    DependencyGraph,
    LanguageStack,
    ProjectContext,
    Tool,
    ToolCall,
    LLMResponse,
)


class TestExecutionModels:
    """Tests for task execution data models."""

    def test_execution_step_creation(self):
        """Test creating an ExecutionStep instance."""
        step = ExecutionStep(
            action="create_file",
            parameters={"path": "test.py", "content": "print('hello')"},
            rationale="Create a test file"
        )
        assert step.action == "create_file"
        assert step.parameters["path"] == "test.py"
        assert step.rationale == "Create a test file"

    def test_execution_plan_creation(self):
        """Test creating an ExecutionPlan instance."""
        steps = [
            ExecutionStep("create_file", {"path": "test.py"}, "Create file"),
            ExecutionStep("run_command", {"cmd": "pytest"}, "Run tests")
        ]
        plan = ExecutionPlan(
            steps=steps,
            estimated_complexity="simple",
            required_tools=["file_ops", "command_executor"]
        )
        assert len(plan.steps) == 2
        assert plan.estimated_complexity == "simple"
        assert "file_ops" in plan.required_tools

    def test_task_result_creation(self):
        """Test creating a TaskResult instance."""
        result = TaskResult(
            success=True,
            actions_taken=[],
            files_modified=["test.py"],
            tests_passed=True,
            error_message=None,
            execution_log=["Created test.py", "Ran tests"]
        )
        assert result.success is True
        assert result.tests_passed is True
        assert "test.py" in result.files_modified


class TestCodeModels:
    """Tests for code analysis data models."""

    def test_search_result_creation(self):
        """Test creating a SearchResult instance."""
        result = SearchResult(
            file_path="src/main.py",
            line_number=42,
            match_text="def hello():",
            context_before=["", "# Greeting function"],
            context_after=["    print('hello')", ""]
        )
        assert result.file_path == "src/main.py"
        assert result.line_number == 42
        assert "def hello" in result.match_text

    def test_symbol_location_creation(self):
        """Test creating a SymbolLocation instance."""
        symbol = SymbolLocation(
            file_path="src/utils.py",
            line_number=10,
            symbol_name="calculate",
            symbol_type="function"
        )
        assert symbol.file_path == "src/utils.py"
        assert symbol.symbol_name == "calculate"
        assert symbol.symbol_type == "function"

    def test_code_analysis_creation(self):
        """Test creating a CodeAnalysis instance."""
        analysis = CodeAnalysis(
            language="python",
            imports=["os", "sys", "typing"],
            symbols=[
                SymbolLocation("test.py", 1, "main", "function"),
                SymbolLocation("test.py", 10, "Helper", "class")
            ],
            dependencies=["utils.py", "config.py"],
            structure="Module with 1 function and 1 class"
        )
        assert analysis.language == "python"
        assert len(analysis.imports) == 3
        assert len(analysis.symbols) == 2
        assert "os" in analysis.imports


class TestConfigModels:
    """Tests for configuration data models."""

    def test_llm_config_creation(self):
        """Test creating an LLMConfig instance."""
        config = LLMConfig(
            endpoint="http://localhost:11434",
            model_name="codellama:13b",
            temperature=0.2,
            max_tokens=4096,
            context_length=16384,
            backend_type="ollama"
        )
        assert config.endpoint == "http://localhost:11434"
        assert config.model_name == "codellama:13b"
        assert config.temperature == 0.2
        assert config.backend_type == "ollama"

    def test_llm_config_defaults(self):
        """Test LLMConfig default values."""
        config = LLMConfig(
            endpoint="http://localhost:11434",
            model_name="codellama:13b"
        )
        assert config.temperature == 0.2
        assert config.max_tokens == 4096
        assert config.context_length == 16384
        assert config.backend_type == "ollama"

    def test_system_config_creation(self):
        """Test creating a SystemConfig instance."""
        llm_config = LLMConfig(
            endpoint="http://localhost:11434",
            model_name="codellama:13b"
        )
        config = SystemConfig(
            llm=llm_config,
            project_root="/home/user/project",
            log_level="debug",
            web_research_enabled=True,
            self_improvement_enabled=False
        )
        assert config.project_root == "/home/user/project"
        assert config.log_level == "debug"
        assert config.web_research_enabled is True
        assert config.self_improvement_enabled is False

    def test_system_config_default_excluded_dirs(self):
        """Test SystemConfig has default excluded directories."""
        llm_config = LLMConfig(
            endpoint="http://localhost:11434",
            model_name="codellama:13b"
        )
        config = SystemConfig(
            llm=llm_config,
            project_root="/home/user/project"
        )
        assert "node_modules" in config.excluded_directories
        assert ".git" in config.excluded_directories
        assert "__pycache__" in config.excluded_directories
        assert len(config.excluded_directories) > 0


class TestContextModels:
    """Tests for context management data models."""

    def test_file_tree_creation(self):
        """Test creating a FileTree instance."""
        tree = FileTree(
            root="/home/user/project",
            files=["main.py", "utils.py", "src/helper.py"],
            directories=["src", "tests"]
        )
        assert tree.root == "/home/user/project"
        assert len(tree.files) == 3
        assert len(tree.directories) == 2
        assert "main.py" in tree.files

    def test_dependency_graph_creation(self):
        """Test creating a DependencyGraph instance."""
        graph = DependencyGraph(
            nodes=["main.py", "utils.py"],
            edges={"main.py": ["utils.py"]}
        )
        assert len(graph.nodes) == 2
        assert "main.py" in graph.nodes
        assert graph.edges["main.py"] == ["utils.py"]

    def test_dependency_graph_add_dependency(self):
        """Test adding dependencies to graph."""
        graph = DependencyGraph(nodes=[], edges={})
        graph.add_dependency("main.py", "utils.py")
        graph.add_dependency("main.py", "config.py")
        
        assert graph.edges["main.py"] == ["utils.py", "config.py"]

    def test_dependency_graph_get_dependencies(self):
        """Test getting direct dependencies."""
        graph = DependencyGraph(
            nodes=["main.py", "utils.py", "config.py"],
            edges={"main.py": ["utils.py", "config.py"]}
        )
        deps = graph.get_dependencies("main.py")
        assert len(deps) == 2
        assert "utils.py" in deps
        assert "config.py" in deps

    def test_dependency_graph_get_all_dependencies(self):
        """Test getting transitive dependencies."""
        graph = DependencyGraph(
            nodes=["main.py", "utils.py", "helper.py"],
            edges={
                "main.py": ["utils.py"],
                "utils.py": ["helper.py"]
            }
        )
        all_deps = graph.get_all_dependencies("main.py")
        assert len(all_deps) == 2
        assert "utils.py" in all_deps
        assert "helper.py" in all_deps

    def test_language_stack_creation(self):
        """Test creating a LanguageStack instance."""
        stack = LanguageStack(
            languages=["Python", "JavaScript"],
            frameworks=["Flask", "React"],
            build_tools=["pip", "npm"],
            primary_language="Python"
        )
        assert len(stack.languages) == 2
        assert "Python" in stack.languages
        assert "Flask" in stack.frameworks
        assert stack.primary_language == "Python"

    def test_project_context_creation(self):
        """Test creating a ProjectContext instance."""
        file_tree = FileTree(
            root="/home/user/project",
            files=["main.py"],
            directories=["src"]
        )
        dep_graph = DependencyGraph(nodes=["main.py"], edges={})
        lang_stack = LanguageStack(
            languages=["Python"],
            frameworks=["Flask"],
            build_tools=["pip"],
            primary_language="Python"
        )
        
        context = ProjectContext(
            root_path="/home/user/project",
            languages=["Python"],
            frameworks=["Flask"],
            file_tree=file_tree,
            dependency_graph=dep_graph,
            key_files={"main_entry": "main.py"},
            language_stack=lang_stack
        )
        
        assert context.root_path == "/home/user/project"
        assert "Python" in context.languages
        assert "Flask" in context.frameworks
        assert context.key_files["main_entry"] == "main.py"


class TestLLMInterfaceModels:
    """Tests for LLM interface data models."""

    def test_tool_creation(self):
        """Test creating a Tool instance."""
        tool = Tool(
            name="search_code",
            description="Search for code in the repository",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "file_pattern": {"type": "string"}
                },
                "required": ["query"]
            }
        )
        assert tool.name == "search_code"
        assert tool.description == "Search for code in the repository"
        assert "properties" in tool.parameters
        assert "query" in tool.parameters["properties"]

    def test_tool_call_creation(self):
        """Test creating a ToolCall instance."""
        tool_call = ToolCall(
            name="create_file",
            arguments={
                "path": "test.py",
                "content": "print('hello')"
            }
        )
        assert tool_call.name == "create_file"
        assert tool_call.arguments["path"] == "test.py"
        assert tool_call.arguments["content"] == "print('hello')"

    def test_llm_response_creation(self):
        """Test creating an LLMResponse instance."""
        response = LLMResponse(
            content="Here's the code you requested.",
            tool_calls=[
                ToolCall(name="create_file", arguments={"path": "test.py"})
            ],
            finish_reason="tool_calls",
            usage={
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "total_tokens": 150
            }
        )
        assert response.content == "Here's the code you requested."
        assert len(response.tool_calls) == 1
        assert response.tool_calls[0].name == "create_file"
        assert response.finish_reason == "tool_calls"
        assert response.usage["total_tokens"] == 150

    def test_llm_response_defaults(self):
        """Test LLMResponse default values."""
        response = LLMResponse(content="Simple response")
        assert response.content == "Simple response"
        assert response.tool_calls == []
        assert response.finish_reason is None
        assert response.usage is None

    def test_llm_response_no_tool_calls(self):
        """Test LLMResponse without tool calls."""
        response = LLMResponse(
            content="This is a text-only response.",
            finish_reason="stop"
        )
        assert response.content == "This is a text-only response."
        assert len(response.tool_calls) == 0
        assert response.finish_reason == "stop"
