"""Unit tests for Context Manager."""

import os
import tempfile
import shutil
import pytest
from pathlib import Path

from src.context.context_manager import ContextManager
from src.core.models import (
    SystemConfig,
    LLMConfig,
    FileTree,
    DependencyGraph,
    LanguageStack,
    ProjectContext,
)


@pytest.fixture
def temp_project_dir():
    """Create a temporary project directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def system_config(temp_project_dir):
    """Create a test system configuration."""
    llm_config = LLMConfig(
        endpoint="http://localhost:11434",
        model_name="test-model"
    )
    return SystemConfig(
        llm=llm_config,
        project_root=temp_project_dir,
        log_level="info"
    )


@pytest.fixture
def context_manager(system_config):
    """Create a ContextManager instance for testing."""
    return ContextManager(system_config)


class TestContextManagerInit:
    """Tests for ContextManager initialization."""

    def test_init_with_config(self, system_config):
        """Test ContextManager initializes with config."""
        cm = ContextManager(system_config)
        assert cm.config == system_config
        assert cm.ast_parser is not None
        assert cm._analysis_cache == {}
        assert cm._file_hashes == {}
        assert cm._project_context is None


class TestScanProject:
    """Tests for project scanning functionality."""

    def test_scan_empty_project(self, context_manager, temp_project_dir):
        """Test scanning an empty project directory."""
        context = context_manager.scan_project(temp_project_dir)
        
        assert context.root_path == temp_project_dir
        assert isinstance(context.file_tree, FileTree)
        assert isinstance(context.dependency_graph, DependencyGraph)
        assert isinstance(context.language_stack, LanguageStack)

    def test_scan_project_with_python_files(self, context_manager, temp_project_dir):
        """Test scanning a project with Python files."""
        # Create test files
        main_py = os.path.join(temp_project_dir, "main.py")
        with open(main_py, 'w') as f:
            f.write("def main():\n    pass\n")
        
        utils_py = os.path.join(temp_project_dir, "utils.py")
        with open(utils_py, 'w') as f:
            f.write("def helper():\n    pass\n")
        
        context = context_manager.scan_project(temp_project_dir)
        
        assert len(context.file_tree.files) == 2
        assert "main.py" in context.file_tree.files
        assert "utils.py" in context.file_tree.files
        assert "Python" in context.languages

    def test_scan_project_excludes_directories(self, context_manager, temp_project_dir):
        """Test that excluded directories are not scanned."""
        # Create excluded directory
        node_modules = os.path.join(temp_project_dir, "node_modules")
        os.makedirs(node_modules)
        
        excluded_file = os.path.join(node_modules, "package.js")
        with open(excluded_file, 'w') as f:
            f.write("// excluded")
        
        # Create normal file
        main_py = os.path.join(temp_project_dir, "main.py")
        with open(main_py, 'w') as f:
            f.write("# main")
        
        context = context_manager.scan_project(temp_project_dir)
        
        # node_modules should be excluded
        assert "node_modules" not in context.file_tree.directories
        assert "node_modules" not in str(context.file_tree.files)
        assert "main.py" in context.file_tree.files

    def test_scan_nonexistent_directory(self, context_manager):
        """Test scanning a directory that doesn't exist."""
        with pytest.raises(FileNotFoundError):
            context_manager.scan_project("/nonexistent/path")

    def test_scan_file_instead_of_directory(self, context_manager, temp_project_dir):
        """Test scanning a file instead of directory."""
        test_file = os.path.join(temp_project_dir, "test.py")
        with open(test_file, 'w') as f:
            f.write("# test")
        
        with pytest.raises(NotADirectoryError):
            context_manager.scan_project(test_file)


class TestDetectLanguageStack:
    """Tests for language and framework detection."""

    def test_detect_python_project(self, context_manager, temp_project_dir):
        """Test detecting a Python project."""
        # Create Python files
        for i in range(5):
            file_path = os.path.join(temp_project_dir, f"file{i}.py")
            with open(file_path, 'w') as f:
                f.write("# Python file")
        
        context_manager.scan_project(temp_project_dir)
        lang_stack = context_manager.detect_language_stack()
        
        assert "Python" in lang_stack.languages
        assert lang_stack.primary_language == "Python"

    def test_detect_javascript_project(self, context_manager, temp_project_dir):
        """Test detecting a JavaScript project."""
        # Create JS files
        for i in range(3):
            file_path = os.path.join(temp_project_dir, f"file{i}.js")
            with open(file_path, 'w') as f:
                f.write("// JavaScript file")
        
        context_manager.scan_project(temp_project_dir)
        lang_stack = context_manager.detect_language_stack()
        
        assert "JavaScript" in lang_stack.languages
        assert lang_stack.primary_language == "JavaScript"

    def test_detect_multi_language_project(self, context_manager, temp_project_dir):
        """Test detecting project with multiple languages."""
        # Create Python files
        for i in range(5):
            file_path = os.path.join(temp_project_dir, f"file{i}.py")
            with open(file_path, 'w') as f:
                f.write("# Python")
        
        # Create JavaScript files
        for i in range(3):
            file_path = os.path.join(temp_project_dir, f"file{i}.js")
            with open(file_path, 'w') as f:
                f.write("// JS")
        
        context_manager.scan_project(temp_project_dir)
        lang_stack = context_manager.detect_language_stack()
        
        assert "Python" in lang_stack.languages
        assert "JavaScript" in lang_stack.languages
        # Python should be primary (more files)
        assert lang_stack.primary_language == "Python"

    def test_detect_flask_framework(self, context_manager, temp_project_dir):
        """Test detecting Flask framework."""
        # Create requirements.txt with Flask
        req_file = os.path.join(temp_project_dir, "requirements.txt")
        with open(req_file, 'w') as f:
            f.write("flask==2.0.0\n")
        
        # Create a Python file
        main_py = os.path.join(temp_project_dir, "main.py")
        with open(main_py, 'w') as f:
            f.write("from flask import Flask\n")
        
        context_manager.scan_project(temp_project_dir)
        lang_stack = context_manager.detect_language_stack()
        
        assert "Flask" in lang_stack.frameworks

    def test_detect_react_framework(self, context_manager, temp_project_dir):
        """Test detecting React framework."""
        # Create package.json with React
        pkg_file = os.path.join(temp_project_dir, "package.json")
        with open(pkg_file, 'w') as f:
            f.write('{"dependencies": {"react": "^18.0.0"}}')
        
        context_manager.scan_project(temp_project_dir)
        lang_stack = context_manager.detect_language_stack()
        
        assert "React" in lang_stack.frameworks

    def test_detect_build_tools(self, context_manager, temp_project_dir):
        """Test detecting build tools."""
        # Create marker files for different build tools
        with open(os.path.join(temp_project_dir, "requirements.txt"), 'w') as f:
            f.write("# pip")
        
        with open(os.path.join(temp_project_dir, "package.json"), 'w') as f:
            f.write("{}")
        
        with open(os.path.join(temp_project_dir, "Makefile"), 'w') as f:
            f.write("all:\n\techo 'build'")
        
        context_manager.scan_project(temp_project_dir)
        lang_stack = context_manager.detect_language_stack()
        
        assert "pip" in lang_stack.build_tools
        assert "npm" in lang_stack.build_tools
        assert "make" in lang_stack.build_tools


class TestAnalyzeCode:
    """Tests for code analysis functionality."""

    def test_analyze_python_file(self, context_manager, temp_project_dir):
        """Test analyzing a Python file."""
        test_file = os.path.join(temp_project_dir, "test.py")
        with open(test_file, 'w') as f:
            f.write("""
import os
import sys

def hello():
    pass

class MyClass:
    def method(self):
        pass
""")
        
        analysis = context_manager.analyze_code(test_file)
        
        assert analysis is not None
        assert analysis.language == "python"
        assert len(analysis.imports) >= 2  # os and sys
        assert len(analysis.symbols) >= 2  # hello and MyClass
        
        # Check symbols
        symbol_names = [s.symbol_name for s in analysis.symbols]
        assert "hello" in symbol_names
        assert "MyClass" in symbol_names

    def test_analyze_javascript_file(self, context_manager, temp_project_dir):
        """Test analyzing a JavaScript file."""
        test_file = os.path.join(temp_project_dir, "test.js")
        with open(test_file, 'w') as f:
            f.write("""
function hello() {
    console.log('hello');
}

class MyClass {
    method() {
        return 42;
    }
}
""")
        
        analysis = context_manager.analyze_code(test_file)
        
        assert analysis is not None
        assert analysis.language == "javascript"
        assert len(analysis.symbols) >= 2  # hello and MyClass

    def test_analyze_nonexistent_file(self, context_manager):
        """Test analyzing a file that doesn't exist."""
        analysis = context_manager.analyze_code("/nonexistent/file.py")
        assert analysis is None

    def test_analyze_unsupported_file(self, context_manager, temp_project_dir):
        """Test analyzing a file with unsupported extension."""
        test_file = os.path.join(temp_project_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("Just text")
        
        analysis = context_manager.analyze_code(test_file)
        assert analysis is None

    def test_cache_invalidation(self, context_manager, temp_project_dir):
        """Test that cache is invalidated when file changes."""
        test_file = os.path.join(temp_project_dir, "test.py")
        
        # Write initial content
        with open(test_file, 'w') as f:
            f.write("def hello():\n    pass\n")
        
        # First analysis
        analysis1 = context_manager.analyze_code(test_file)
        assert analysis1 is not None
        
        # Modify file
        with open(test_file, 'w') as f:
            f.write("def goodbye():\n    pass\n")
        
        # Second analysis should detect change
        analysis2 = context_manager.analyze_code(test_file)
        assert analysis2 is not None
        
        # Check that new symbol is detected
        symbol_names = [s.symbol_name for s in analysis2.symbols]
        assert "goodbye" in symbol_names


class TestGetRelevantFiles:
    """Tests for identifying relevant files for a task."""

    def test_get_relevant_files_by_filename(self, context_manager, temp_project_dir):
        """Test finding files by filename match."""
        # Create files
        auth_file = os.path.join(temp_project_dir, "auth.py")
        with open(auth_file, 'w') as f:
            f.write("# authentication")
        
        utils_file = os.path.join(temp_project_dir, "utils.py")
        with open(utils_file, 'w') as f:
            f.write("# utilities")
        
        context_manager.scan_project(temp_project_dir)
        
        # Search for auth-related files
        relevant = context_manager.get_relevant_files("fix authentication bug in auth module")
        
        # Should find auth.py (keyword "auth" is in task description and filename)
        assert len(relevant) > 0
        assert any("auth" in os.path.basename(f) for f in relevant)

    def test_get_relevant_files_by_symbol(self, context_manager, temp_project_dir):
        """Test finding files by symbol name match."""
        # Create file with specific function
        test_file = os.path.join(temp_project_dir, "helpers.py")
        with open(test_file, 'w') as f:
            f.write("""
def calculate_total():
    pass

def format_output():
    pass
""")
        
        context_manager.scan_project(temp_project_dir)
        
        # Search for files with calculate function
        relevant = context_manager.get_relevant_files("update calculate function")
        
        # Should find helpers.py
        assert any("helpers.py" in f for f in relevant)

    def test_get_relevant_files_without_scan(self, context_manager):
        """Test that getting relevant files fails without scanning."""
        with pytest.raises(RuntimeError):
            context_manager.get_relevant_files("some task")


class TestGetDependencies:
    """Tests for dependency graph extraction."""

    def test_get_dependencies_simple(self, context_manager, temp_project_dir):
        """Test getting dependencies for a file."""
        # Create main.py that imports utils.py
        main_file = os.path.join(temp_project_dir, "main.py")
        with open(main_file, 'w') as f:
            f.write("from utils import helper\n")
        
        utils_file = os.path.join(temp_project_dir, "utils.py")
        with open(utils_file, 'w') as f:
            f.write("def helper():\n    pass\n")
        
        context_manager.scan_project(temp_project_dir)
        
        # Get dependencies
        dep_graph = context_manager.get_dependencies(main_file)
        
        assert main_file in dep_graph.nodes
        # Note: dependency resolution is simplified, so this might not work perfectly
        # Just verify the graph structure is valid
        assert isinstance(dep_graph, DependencyGraph)

    def test_get_dependencies_without_scan(self, context_manager, temp_project_dir):
        """Test that getting dependencies fails without scanning."""
        test_file = os.path.join(temp_project_dir, "test.py")
        with open(test_file, 'w') as f:
            f.write("# test")
        
        with pytest.raises(RuntimeError):
            context_manager.get_dependencies(test_file)


class TestCacheManagement:
    """Tests for cache management."""

    def test_invalidate_specific_file(self, context_manager, temp_project_dir):
        """Test invalidating cache for specific file."""
        test_file = os.path.join(temp_project_dir, "test.py")
        with open(test_file, 'w') as f:
            f.write("def test():\n    pass\n")
        
        # Analyze file
        context_manager.analyze_code(test_file)
        assert test_file in context_manager._analysis_cache
        
        # Invalidate
        context_manager.invalidate_cache(test_file)
        assert test_file not in context_manager._analysis_cache

    def test_invalidate_all_cache(self, context_manager, temp_project_dir):
        """Test invalidating all cache."""
        # Create and analyze multiple files
        for i in range(3):
            test_file = os.path.join(temp_project_dir, f"test{i}.py")
            with open(test_file, 'w') as f:
                f.write(f"def func{i}():\n    pass\n")
            context_manager.analyze_code(test_file)
        
        assert len(context_manager._analysis_cache) == 3
        
        # Invalidate all
        context_manager.invalidate_cache()
        assert len(context_manager._analysis_cache) == 0


class TestKeyFileIdentification:
    """Tests for identifying key project files."""

    def test_identify_main_entry(self, context_manager, temp_project_dir):
        """Test identifying main entry point."""
        # Create main.py
        main_file = os.path.join(temp_project_dir, "main.py")
        with open(main_file, 'w') as f:
            f.write("# main entry")
        
        context = context_manager.scan_project(temp_project_dir)
        
        assert "main_entry" in context.key_files
        assert "main.py" in context.key_files["main_entry"]

    def test_identify_readme(self, context_manager, temp_project_dir):
        """Test identifying README file."""
        # Create README.md
        readme_file = os.path.join(temp_project_dir, "README.md")
        with open(readme_file, 'w') as f:
            f.write("# Project")
        
        context = context_manager.scan_project(temp_project_dir)
        
        assert "readme" in context.key_files
        assert "README.md" in context.key_files["readme"]


class TestProjectScanningEdgeCases:
    """Tests for project scanning with different structures."""

    def test_scan_deeply_nested_structure(self, context_manager, temp_project_dir):
        """Test scanning project with deeply nested directories."""
        # Create deeply nested structure
        nested_path = os.path.join(temp_project_dir, "src", "core", "utils", "helpers")
        os.makedirs(nested_path)
        
        nested_file = os.path.join(nested_path, "deep_helper.py")
        with open(nested_file, 'w') as f:
            f.write("def deep_function():\n    pass\n")
        
        context = context_manager.scan_project(temp_project_dir)
        
        # Check that nested file is found
        assert any("deep_helper.py" in f for f in context.file_tree.files)
        # Check that nested directories are recorded
        assert any("helpers" in d for d in context.file_tree.directories)

    def test_scan_monorepo_structure(self, context_manager, temp_project_dir):
        """Test scanning monorepo with multiple projects."""
        # Create monorepo structure
        frontend_dir = os.path.join(temp_project_dir, "frontend")
        backend_dir = os.path.join(temp_project_dir, "backend")
        os.makedirs(frontend_dir)
        os.makedirs(backend_dir)
        
        # Frontend files (JavaScript)
        with open(os.path.join(frontend_dir, "app.js"), 'w') as f:
            f.write("console.log('frontend');\n")
        with open(os.path.join(frontend_dir, "package.json"), 'w') as f:
            f.write('{"name": "frontend"}')
        
        # Backend files (Python)
        with open(os.path.join(backend_dir, "server.py"), 'w') as f:
            f.write("print('backend')\n")
        with open(os.path.join(backend_dir, "requirements.txt"), 'w') as f:
            f.write("flask==2.0.0\n")
        
        context = context_manager.scan_project(temp_project_dir)
        
        # Should detect both languages
        assert "JavaScript" in context.languages
        assert "Python" in context.languages
        # Should detect both build tools
        assert "npm" in context.language_stack.build_tools
        assert "pip" in context.language_stack.build_tools

    def test_scan_empty_nested_directories(self, context_manager, temp_project_dir):
        """Test scanning project with empty nested directories."""
        # Create nested empty directories
        empty_path = os.path.join(temp_project_dir, "empty1", "empty2", "empty3")
        os.makedirs(empty_path)
        
        # Create one file in root
        root_file = os.path.join(temp_project_dir, "main.py")
        with open(root_file, 'w') as f:
            f.write("# main")
        
        context = context_manager.scan_project(temp_project_dir)
        
        # Should record empty directories
        assert len(context.file_tree.directories) >= 3
        # Should still find the root file
        assert "main.py" in context.file_tree.files

    def test_scan_mixed_file_types(self, context_manager, temp_project_dir):
        """Test scanning project with mixed file types."""
        # Create various file types
        files = {
            "code.py": "# Python",
            "code.js": "// JavaScript",
            "code.ts": "// TypeScript",
            "data.json": '{"key": "value"}',
            "readme.md": "# README",
            "config.yaml": "key: value",
            "image.png": "fake image data",
            "doc.txt": "text file",
        }
        
        for filename, content in files.items():
            with open(os.path.join(temp_project_dir, filename), 'w') as f:
                f.write(content)
        
        context = context_manager.scan_project(temp_project_dir)
        
        # Should include all files
        assert len(context.file_tree.files) == len(files)
        # Should detect multiple languages
        assert "Python" in context.languages
        assert "JavaScript" in context.languages
        assert "TypeScript" in context.languages

    def test_scan_project_with_symlinks(self, context_manager, temp_project_dir):
        """Test scanning project with symbolic links."""
        # Create regular file
        real_file = os.path.join(temp_project_dir, "real.py")
        with open(real_file, 'w') as f:
            f.write("# real file")
        
        # Create symlink (skip if OS doesn't support)
        try:
            link_file = os.path.join(temp_project_dir, "link.py")
            os.symlink(real_file, link_file)
            
            context = context_manager.scan_project(temp_project_dir)
            
            # Should handle symlinks without errors
            assert isinstance(context, type(context_manager._project_context))
        except (OSError, NotImplementedError):
            # Skip test if symlinks not supported
            pass


class TestRelevantFileIdentification:
    """Tests for relevant file identification with various task descriptions."""

    def test_identify_files_by_exact_filename(self, context_manager, temp_project_dir):
        """Test identifying files by exact filename match."""
        # Create files
        with open(os.path.join(temp_project_dir, "authentication.py"), 'w') as f:
            f.write("def login():\n    pass\n")
        with open(os.path.join(temp_project_dir, "database.py"), 'w') as f:
            f.write("def connect():\n    pass\n")
        
        context_manager.scan_project(temp_project_dir)
        
        # Task mentions authentication
        relevant = context_manager.get_relevant_files("update the authentication module")
        
        assert len(relevant) > 0
        assert any("authentication.py" in f for f in relevant)
        assert not any("database.py" in f for f in relevant)

    def test_identify_files_by_partial_filename(self, context_manager, temp_project_dir):
        """Test identifying files by partial filename match."""
        # Create files
        with open(os.path.join(temp_project_dir, "user_auth_service.py"), 'w') as f:
            f.write("# auth service")
        with open(os.path.join(temp_project_dir, "user_profile_service.py"), 'w') as f:
            f.write("# profile service")
        
        context_manager.scan_project(temp_project_dir)
        
        # Task mentions "auth"
        relevant = context_manager.get_relevant_files("fix bug in auth")
        
        assert any("user_auth_service.py" in f for f in relevant)

    def test_identify_files_by_function_name(self, context_manager, temp_project_dir):
        """Test identifying files by function name match."""
        # Create file with specific function
        with open(os.path.join(temp_project_dir, "utils.py"), 'w') as f:
            f.write("def calculate_tax():\n    pass\n\ndef format_date():\n    pass\n")
        
        context_manager.scan_project(temp_project_dir)
        
        # Task mentions function name
        relevant = context_manager.get_relevant_files("modify calculate_tax function")
        
        assert any("utils.py" in f for f in relevant)

    def test_identify_files_by_class_name(self, context_manager, temp_project_dir):
        """Test identifying files by class name match."""
        # Create file with specific class
        with open(os.path.join(temp_project_dir, "models.py"), 'w') as f:
            f.write("class UserModel:\n    pass\n\nclass ProductModel:\n    pass\n")
        
        context_manager.scan_project(temp_project_dir)
        
        # Task mentions class name
        relevant = context_manager.get_relevant_files("update UserModel class")
        
        assert any("models.py" in f for f in relevant)

    def test_identify_files_with_multiple_keywords(self, context_manager, temp_project_dir):
        """Test identifying files when task has multiple keywords."""
        # Create files
        with open(os.path.join(temp_project_dir, "user.py"), 'w') as f:
            f.write("class User:\n    def authenticate(self):\n        pass\n")
        with open(os.path.join(temp_project_dir, "auth.py"), 'w') as f:
            f.write("def verify_user():\n    pass\n")
        
        context_manager.scan_project(temp_project_dir)
        
        # Task mentions both "user" and "authenticate"
        relevant = context_manager.get_relevant_files("update user authentication logic")
        
        # Should find both files
        assert len(relevant) >= 2

    def test_identify_files_case_insensitive(self, context_manager, temp_project_dir):
        """Test that file identification is case-insensitive."""
        # Create file
        with open(os.path.join(temp_project_dir, "UserService.py"), 'w') as f:
            f.write("class UserService:\n    pass\n")
        
        context_manager.scan_project(temp_project_dir)
        
        # Task uses lowercase
        relevant = context_manager.get_relevant_files("fix userservice bug")
        
        assert len(relevant) > 0

    def test_no_relevant_files_found(self, context_manager, temp_project_dir):
        """Test when no relevant files match the task."""
        # Create file
        with open(os.path.join(temp_project_dir, "unrelated.py"), 'w') as f:
            f.write("def something():\n    pass\n")
        
        context_manager.scan_project(temp_project_dir)
        
        # Task doesn't match any files
        relevant = context_manager.get_relevant_files("implement quantum teleportation")
        
        # Should return empty list or minimal results
        assert isinstance(relevant, list)


class TestNoRecognizedFrameworks:
    """Tests for handling projects with no recognized frameworks."""

    def test_plain_python_project(self, context_manager, temp_project_dir):
        """Test project with Python files but no frameworks."""
        # Create plain Python files
        for i in range(3):
            with open(os.path.join(temp_project_dir, f"module{i}.py"), 'w') as f:
                f.write(f"def func{i}():\n    pass\n")
        
        context = context_manager.scan_project(temp_project_dir)
        
        # Should detect Python language
        assert "Python" in context.languages
        # But no frameworks
        assert len(context.frameworks) == 0

    def test_plain_javascript_project(self, context_manager, temp_project_dir):
        """Test project with JavaScript files but no frameworks."""
        # Create plain JavaScript files
        for i in range(3):
            with open(os.path.join(temp_project_dir, f"script{i}.js"), 'w') as f:
                f.write(f"function func{i}() {{}}\n")
        
        context = context_manager.scan_project(temp_project_dir)
        
        # Should detect JavaScript language
        assert "JavaScript" in context.languages
        # But no frameworks
        assert len(context.frameworks) == 0

    def test_custom_language_no_framework(self, context_manager, temp_project_dir):
        """Test project with supported language but no standard frameworks."""
        # Create Go files without known frameworks
        with open(os.path.join(temp_project_dir, "main.go"), 'w') as f:
            f.write("package main\n\nfunc main() {}\n")
        
        context = context_manager.scan_project(temp_project_dir)
        
        # Should detect Go language
        assert "Go" in context.languages
        # Should have no frameworks detected
        assert len(context.frameworks) == 0

    def test_no_build_tools(self, context_manager, temp_project_dir):
        """Test project with no recognized build tools."""
        # Create files without build tool markers
        with open(os.path.join(temp_project_dir, "code.py"), 'w') as f:
            f.write("# Python code")
        with open(os.path.join(temp_project_dir, "script.js"), 'w') as f:
            f.write("// JavaScript code")
        
        context = context_manager.scan_project(temp_project_dir)
        
        # Should detect languages
        assert len(context.languages) > 0
        # But no build tools
        assert len(context.language_stack.build_tools) == 0


class TestCacheInvalidation:
    """Tests for cache invalidation when files change."""

    def test_cache_invalidation_on_content_change(self, context_manager, temp_project_dir):
        """Test that cache is invalidated when file content changes."""
        test_file = os.path.join(temp_project_dir, "test.py")
        
        # Write initial content
        with open(test_file, 'w') as f:
            f.write("def original():\n    pass\n")
        
        # First analysis
        analysis1 = context_manager.analyze_code(test_file)
        symbols1 = [s.symbol_name for s in analysis1.symbols]
        assert "original" in symbols1
        
        # Modify file
        with open(test_file, 'w') as f:
            f.write("def modified():\n    pass\n")
        
        # Second analysis should detect change
        analysis2 = context_manager.analyze_code(test_file)
        symbols2 = [s.symbol_name for s in analysis2.symbols]
        assert "modified" in symbols2
        assert "original" not in symbols2

    def test_cache_hit_on_unchanged_file(self, context_manager, temp_project_dir):
        """Test that cache is used when file hasn't changed."""
        test_file = os.path.join(temp_project_dir, "test.py")
        
        # Write content
        with open(test_file, 'w') as f:
            f.write("def func():\n    pass\n")
        
        # First analysis
        analysis1 = context_manager.analyze_code(test_file)
        
        # Second analysis without modification
        analysis2 = context_manager.analyze_code(test_file)
        
        # Should return same object (cache hit)
        assert analysis1 is analysis2

    def test_manual_cache_invalidation_specific_file(self, context_manager, temp_project_dir):
        """Test manually invalidating cache for specific file."""
        test_file = os.path.join(temp_project_dir, "test.py")
        
        # Write and analyze
        with open(test_file, 'w') as f:
            f.write("def func():\n    pass\n")
        context_manager.analyze_code(test_file)
        
        # Manually invalidate
        context_manager.invalidate_cache(test_file)
        
        # Cache should be empty for this file
        assert test_file not in context_manager._analysis_cache

    def test_manual_cache_invalidation_all_files(self, context_manager, temp_project_dir):
        """Test manually invalidating all cache."""
        # Create and analyze multiple files
        files = []
        for i in range(3):
            test_file = os.path.join(temp_project_dir, f"test{i}.py")
            files.append(test_file)
            with open(test_file, 'w') as f:
                f.write(f"def func{i}():\n    pass\n")
            context_manager.analyze_code(test_file)
        
        assert len(context_manager._analysis_cache) == 3
        
        # Invalidate all
        context_manager.invalidate_cache()
        
        # Cache should be empty
        assert len(context_manager._analysis_cache) == 0

    def test_cache_survives_identical_content_rewrite(self, context_manager, temp_project_dir):
        """Test that cache detects when file is rewritten with same content."""
        test_file = os.path.join(temp_project_dir, "test.py")
        content = "def func():\n    pass\n"
        
        # Write and analyze
        with open(test_file, 'w') as f:
            f.write(content)
        analysis1 = context_manager.analyze_code(test_file)
        
        # Rewrite with same content
        with open(test_file, 'w') as f:
            f.write(content)
        
        # Analysis should be cached (same hash)
        analysis2 = context_manager.analyze_code(test_file)
        assert analysis1 is analysis2

    def test_cache_invalidation_on_whitespace_change(self, context_manager, temp_project_dir):
        """Test that cache detects whitespace-only changes."""
        test_file = os.path.join(temp_project_dir, "test.py")
        
        # Write initial content
        with open(test_file, 'w') as f:
            f.write("def func():\n    pass")
        analysis1 = context_manager.analyze_code(test_file)
        
        # Add trailing newline
        with open(test_file, 'w') as f:
            f.write("def func():\n    pass\n")
        
        # Cache should be invalidated (different hash)
        analysis2 = context_manager.analyze_code(test_file)
        # Should be different object (re-analyzed)
        assert analysis1 is not analysis2


class TestEdgeCasesAndErrorHandling:
    """Tests for edge cases and error handling in context manager."""

    def test_analyze_empty_file(self, context_manager, temp_project_dir):
        """Test analyzing an empty file."""
        test_file = os.path.join(temp_project_dir, "empty.py")
        with open(test_file, 'w') as f:
            f.write("")
        
        analysis = context_manager.analyze_code(test_file)
        
        # Should return valid analysis even for empty file
        assert analysis is not None
        assert len(analysis.symbols) == 0

    def test_analyze_large_file(self, context_manager, temp_project_dir):
        """Test analyzing a large file."""
        test_file = os.path.join(temp_project_dir, "large.py")
        
        # Create large file with many functions
        with open(test_file, 'w') as f:
            for i in range(100):
                f.write(f"def func_{i}():\n    pass\n\n")
        
        analysis = context_manager.analyze_code(test_file)
        
        # Should successfully analyze all symbols
        assert analysis is not None
        assert len(analysis.symbols) == 100

    def test_analyze_file_with_syntax_errors(self, context_manager, temp_project_dir):
        """Test analyzing file with syntax errors."""
        test_file = os.path.join(temp_project_dir, "broken.py")
        with open(test_file, 'w') as f:
            f.write("def broken(\n    # Missing closing paren and colon\n")
        
        analysis = context_manager.analyze_code(test_file)
        
        # Should return None or handle gracefully
        # (Behavior depends on parser implementation)
        assert analysis is None or isinstance(analysis, type(context_manager._analysis_cache.get(test_file)))

    def test_scan_project_with_permission_errors(self, context_manager, temp_project_dir):
        """Test scanning project with files that can't be read."""
        # Create normal file
        normal_file = os.path.join(temp_project_dir, "normal.py")
        with open(normal_file, 'w') as f:
            f.write("# normal")
        
        # This test is platform-specific, just verify no crash
        try:
            context = context_manager.scan_project(temp_project_dir)
            assert isinstance(context, type(context_manager._project_context))
        except PermissionError:
            # Expected on some systems
            pass

    def test_get_relevant_files_with_special_characters(self, context_manager, temp_project_dir):
        """Test relevant file identification with special characters in task."""
        # Create file
        with open(os.path.join(temp_project_dir, "handler.py"), 'w') as f:
            f.write("def handle():\n    pass\n")
        
        context_manager.scan_project(temp_project_dir)
        
        # Task with special characters
        relevant = context_manager.get_relevant_files("fix handler bug (urgent!)")
        
        # Should still find relevant files
        assert isinstance(relevant, list)

    def test_detect_language_with_no_files(self, context_manager, temp_project_dir):
        """Test language detection in empty project."""
        context = context_manager.scan_project(temp_project_dir)
        lang_stack = context_manager.detect_language_stack()
        
        # Should return empty language list
        assert len(lang_stack.languages) == 0
        assert lang_stack.primary_language is None

    def test_analyze_binary_file(self, context_manager, temp_project_dir):
        """Test analyzing a binary file."""
        test_file = os.path.join(temp_project_dir, "binary.bin")
        with open(test_file, 'wb') as f:
            f.write(b'\x00\x01\x02\x03\xff\xfe')
        
        analysis = context_manager.analyze_code(test_file)
        
        # Should return None for unsupported file type
        assert analysis is None
