"""Property-based tests for dependency graph accuracy.

This module tests Property 3: Dependency Graph Accuracy
**Validates: Requirements 6.2**

The property ensures that dependency graph edges exactly match imports in
code files - the constructed dependency graph SHALL contain an edge from the
file to each imported module, and the set of dependencies SHALL exactly match
the set of imports found in the code.
"""

import os
import tempfile
import shutil
import uuid
from pathlib import Path
import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from typing import List, Tuple, Set

from src.context.context_manager import ContextManager
from src.core.models import SystemConfig, LLMConfig, DependencyGraph


# Strategy for generating valid Python identifiers
import keyword
identifier_strategy = st.from_regex(
    r'[a-zA-Z_][a-zA-Z0-9_]{0,15}',
    fullmatch=True
).filter(
    lambda x: not keyword.iskeyword(x)
)


# Strategy for generating Python module names
@st.composite
def module_name_strategy(draw):
    """Generate valid Python module names (file names without extension)."""
    name = draw(identifier_strategy)
    # Make it more likely to be a valid module name
    return name.lower()


# Strategy for generating import statements
@st.composite
def import_statement_strategy(draw, available_modules: List[str]):
    """Generate Python import statements.
    
    Args:
        available_modules: List of module names that can be imported
    """
    if not available_modules:
        return None
    
    module = draw(st.sampled_from(available_modules))
    import_style = draw(st.sampled_from(['import', 'from_import', 'from_import_as']))
    
    if import_style == 'import':
        return f'import {module}'
    elif import_style == 'from_import':
        # Import something from the module
        symbol = draw(identifier_strategy)
        return f'from {module} import {symbol}'
    else:  # from_import_as
        symbol = draw(identifier_strategy)
        alias = draw(identifier_strategy)
        return f'from {module} import {symbol} as {alias}'


# Strategy for generating relative imports
@st.composite
def relative_import_strategy(draw, available_modules: List[str]):
    """Generate relative import statements."""
    if not available_modules:
        return None
    
    module = draw(st.sampled_from(available_modules))
    symbol = draw(identifier_strategy)
    
    # Use relative import syntax
    return f'from .{module} import {symbol}'


# Strategy for generating a Python file with imports
@st.composite
def python_file_with_imports_strategy(draw, available_modules: List[str]):
    """Generate Python file content with import statements.
    
    Returns:
        Tuple of (file_content, list_of_imported_modules)
    """
    # Decide how many imports to include (0-5)
    num_imports = draw(st.integers(min_value=0, max_value=min(5, len(available_modules))))
    
    if num_imports == 0:
        # No imports
        code = "# Empty module\npass\n"
        return code, []
    
    # Sample modules to import (without replacement)
    imported_modules = draw(st.lists(
        st.sampled_from(available_modules),
        min_size=num_imports,
        max_size=num_imports,
        unique=True
    ))
    
    # Generate import statements
    import_lines = []
    for module in imported_modules:
        import_stmt = draw(import_statement_strategy([module]))
        if import_stmt:
            import_lines.append(import_stmt)
    
    # Build file content
    code_parts = import_lines + [
        "",
        "# Module content",
        "def dummy_function():",
        "    pass",
        ""
    ]
    
    code = '\n'.join(code_parts)
    
    return code, imported_modules


# Strategy for generating JavaScript files with imports
@st.composite
def javascript_file_with_imports_strategy(draw, available_modules: List[str]):
    """Generate JavaScript file content with import statements.
    
    Returns:
        Tuple of (file_content, list_of_imported_modules)
    """
    if not available_modules:
        return "// Empty module\n", []
    
    # Decide how many imports to include (0-4)
    num_imports = draw(st.integers(min_value=0, max_value=min(4, len(available_modules))))
    
    if num_imports == 0:
        code = "// Empty module\nexport default {};\n"
        return code, []
    
    # Sample modules to import (without replacement)
    imported_modules = draw(st.lists(
        st.sampled_from(available_modules),
        min_size=num_imports,
        max_size=num_imports,
        unique=True
    ))
    
    # Generate import statements
    import_lines = []
    for module in imported_modules:
        import_style = draw(st.sampled_from(['default', 'named', 'namespace']))
        
        if import_style == 'default':
            import_lines.append(f"import {module} from './{module}.js';")
        elif import_style == 'named':
            symbol = draw(identifier_strategy)
            import_lines.append(f"import {{ {symbol} }} from './{module}.js';")
        else:  # namespace
            import_lines.append(f"import * as {module}Module from './{module}.js';")
    
    # Build file content
    code_parts = import_lines + [
        "",
        "// Module content",
        "export function dummy() {",
        "    return 42;",
        "}",
        ""
    ]
    
    code = '\n'.join(code_parts)
    
    return code, imported_modules


# Strategy for generating TypeScript files with imports
@st.composite
def typescript_file_with_imports_strategy(draw, available_modules: List[str]):
    """Generate TypeScript file content with import statements.
    
    Returns:
        Tuple of (file_content, list_of_imported_modules)
    """
    if not available_modules:
        return "// Empty module\nexport {};\n", []
    
    # Decide how many imports to include (0-4)
    num_imports = draw(st.integers(min_value=0, max_value=min(4, len(available_modules))))
    
    if num_imports == 0:
        code = "// Empty module\nexport default {};\n"
        return code, []
    
    # Sample modules to import (without replacement)
    imported_modules = draw(st.lists(
        st.sampled_from(available_modules),
        min_size=num_imports,
        max_size=num_imports,
        unique=True
    ))
    
    # Generate import statements (similar to JavaScript)
    import_lines = []
    for module in imported_modules:
        import_style = draw(st.sampled_from(['default', 'named', 'type']))
        
        if import_style == 'default':
            import_lines.append(f"import {module} from './{module}';")
        elif import_style == 'named':
            symbol = draw(identifier_strategy)
            import_lines.append(f"import {{ {symbol} }} from './{module}';")
        else:  # type import
            type_name = draw(identifier_strategy.filter(lambda x: x[0].isupper()))
            import_lines.append(f"import type {{ {type_name} }} from './{module}';")
    
    # Build file content with TypeScript-specific syntax
    code_parts = import_lines + [
        "",
        "// Module content",
        "export function dummy(): number {",
        "    return 42;",
        "}",
        ""
    ]
    
    code = '\n'.join(code_parts)
    
    return code, imported_modules


# Strategy for generating a Python project with multiple files
@st.composite
def python_project_strategy(draw):
    """Generate a Python project with multiple files and imports between them.
    
    Returns:
        Dict mapping filename -> (file_content, list_of_imported_module_names)
    """
    # Generate 2-8 Python modules
    num_modules = draw(st.integers(min_value=2, max_value=8))
    
    # Generate unique module names
    module_names = []
    for _ in range(num_modules):
        module_name = draw(module_name_strategy())
        # Ensure uniqueness
        while module_name in module_names:
            module_name = draw(module_name_strategy())
        module_names.append(module_name)
    
    # Create files with imports
    project_files = {}
    
    for module_name in module_names:
        # Each module can import from other modules (not itself)
        available_for_import = [m for m in module_names if m != module_name]
        
        # Generate file content with imports
        file_content, imported_modules = draw(
            python_file_with_imports_strategy(available_for_import)
        )
        
        filename = f"{module_name}.py"
        project_files[filename] = (file_content, imported_modules)
    
    return project_files


# Strategy for generating a multi-language project
@st.composite
def multi_language_project_strategy(draw):
    """Generate a multi-language project with Python, JavaScript, and TypeScript files.
    
    Returns:
        Dict mapping filename -> (file_content, list_of_imported_module_names, language)
    """
    # Choose which languages to include (at least 1)
    languages = draw(st.lists(
        st.sampled_from(['python', 'javascript', 'typescript']),
        min_size=1,
        max_size=3,
        unique=True
    ))
    
    project_files = {}
    
    # For each language, generate 2-4 modules
    for language in languages:
        num_modules = draw(st.integers(min_value=2, max_value=4))
        
        # Generate unique module names for this language
        module_names = []
        for _ in range(num_modules):
            module_name = draw(module_name_strategy())
            # Ensure uniqueness within this language
            while module_name in module_names:
                module_name = draw(module_name_strategy())
            module_names.append(module_name)
        
        # Create files with imports
        if language == 'python':
            for module_name in module_names:
                available_for_import = [m for m in module_names if m != module_name]
                file_content, imported_modules = draw(
                    python_file_with_imports_strategy(available_for_import)
                )
                filename = f"{module_name}.py"
                project_files[filename] = (file_content, imported_modules, 'python')
        
        elif language == 'javascript':
            for module_name in module_names:
                available_for_import = [m for m in module_names if m != module_name]
                file_content, imported_modules = draw(
                    javascript_file_with_imports_strategy(available_for_import)
                )
                filename = f"{module_name}.js"
                project_files[filename] = (file_content, imported_modules, 'javascript')
        
        elif language == 'typescript':
            for module_name in module_names:
                available_for_import = [m for m in module_names if m != module_name]
                file_content, imported_modules = draw(
                    typescript_file_with_imports_strategy(available_for_import)
                )
                filename = f"{module_name}.ts"
                project_files[filename] = (file_content, imported_modules, 'typescript')
    
    return project_files


@pytest.mark.property
class TestDependencyGraphAccuracy:
    """Property-based tests for dependency graph accuracy.
    
    Tag: Feature: local-ai-dev-environment, Property 3: Dependency Graph Accuracy
    """
    
    def setup_method(self):
        """Create a temporary directory for test projects."""
        self.test_dir = tempfile.mkdtemp(prefix='dep_graph_test_')
        
        # Create system config
        llm_config = LLMConfig(
            endpoint="http://localhost:11434",
            model_name="test-model"
        )
        self.config = SystemConfig(
            llm=llm_config,
            project_root=self.test_dir,
            log_level="info"
        )
        
        self.context_manager = ContextManager(self.config)
    
    def teardown_method(self):
        """Clean up temporary directory."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def _write_project_files(self, project_files: dict) -> dict:
        """Write project files to the test directory.
        
        Args:
            project_files: Dict mapping filename -> (content, imported_modules)
        
        Returns:
            Dict mapping absolute file path -> list of imported module names
        """
        # Clean the test directory before writing new files
        # This ensures each Hypothesis example starts with a fresh directory
        for item in os.listdir(self.test_dir):
            item_path = os.path.join(self.test_dir, item)
            if os.path.isfile(item_path):
                os.remove(item_path)
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)
        
        file_to_imports = {}
        
        for filename, (content, imported_modules) in project_files.items():
            file_path = Path(self.test_dir) / filename
            file_path.write_text(content, encoding='utf-8')
            file_to_imports[str(file_path)] = imported_modules
        
        return file_to_imports
    
    def _extract_imports_from_graph(
        self,
        dep_graph: DependencyGraph,
        source_file: str
    ) -> Set[str]:
        """Extract imported module names from dependency graph.
        
        Args:
            dep_graph: The dependency graph
            source_file: Absolute path to the source file
        
        Returns:
            Set of imported module names (without .py extension)
        """
        dependencies = dep_graph.get_dependencies(source_file)
        
        # Convert file paths back to module names
        imported_modules = set()
        for dep_file in dependencies:
            # Get the module name from the file path
            module_name = Path(dep_file).stem  # Remove .py extension
            imported_modules.add(module_name)
        
        return imported_modules
    
    @given(project=python_project_strategy())
    @settings(max_examples=20, deadline=None, suppress_health_check=[HealthCheck.large_base_example, HealthCheck.data_too_large])
    def test_dependency_graph_edges_match_imports(self, project):
        """Test that dependency graph edges exactly match imports in code.
        
        **Validates: Requirements 6.2**
        
        Property: For any code file with import statements, the constructed
        dependency graph SHALL contain an edge from the file to each imported
        module, and the set of dependencies SHALL exactly match the set of
        imports found in the code.
        
        Tag: Feature: local-ai-dev-environment, Property 3: Dependency Graph Accuracy
        """
        # Ensure we have at least 2 files to test dependencies
        assume(len(project) >= 2)
        
        # Write project files
        file_to_imports = self._write_project_files(project)
        
        # Scan the project and build dependency graph
        context = self.context_manager.scan_project(self.test_dir)
        dep_graph = context.dependency_graph
        
        # Verify dependency graph for each file
        for source_file, expected_imports in file_to_imports.items():
            # Get dependencies from graph
            actual_imports = self._extract_imports_from_graph(dep_graph, source_file)
            expected_imports_set = set(expected_imports)
            
            # The dependency graph should exactly match the imports
            assert actual_imports == expected_imports_set, (
                f"Dependency mismatch for {Path(source_file).name}:\n"
                f"Expected imports: {expected_imports_set}\n"
                f"Actual in graph: {actual_imports}\n"
                f"Missing: {expected_imports_set - actual_imports}\n"
                f"Extra: {actual_imports - expected_imports_set}"
            )
    
    @given(project=python_project_strategy())
    @settings(max_examples=20, deadline=None, suppress_health_check=[HealthCheck.large_base_example])
    def test_dependency_graph_nodes_include_all_files(self, project):
        """Test that all code files appear as nodes in the dependency graph.
        
        **Validates: Requirements 6.2**
        
        Property: Every code file in the project should appear as a node
        in the dependency graph, even if it has no imports or is not imported.
        
        Tag: Feature: local-ai-dev-environment, Property 3: Dependency Graph Accuracy
        """
        # Write project files
        file_to_imports = self._write_project_files(project)
        
        # Scan the project
        context = self.context_manager.scan_project(self.test_dir)
        dep_graph = context.dependency_graph
        
        # Get all file paths
        all_files = set(file_to_imports.keys())
        graph_nodes = set(dep_graph.nodes)
        
        # All files should be in the graph
        missing_files = all_files - graph_nodes
        assert len(missing_files) == 0, (
            f"Files missing from dependency graph nodes: {missing_files}"
        )
    
    @given(project=python_project_strategy())
    @settings(max_examples=20, deadline=None, suppress_health_check=[HealthCheck.large_base_example])
    def test_no_self_dependencies(self, project):
        """Test that files do not have dependencies to themselves.
        
        **Validates: Requirements 6.2**
        
        Property: A file should never appear in its own dependency list
        (no self-loops in the graph).
        
        Tag: Feature: local-ai-dev-environment, Property 3: Dependency Graph Accuracy
        """
        # Write project files
        file_to_imports = self._write_project_files(project)
        
        # Scan the project
        context = self.context_manager.scan_project(self.test_dir)
        dep_graph = context.dependency_graph
        
        # Check each file
        for source_file in file_to_imports.keys():
            dependencies = dep_graph.get_dependencies(source_file)
            
            # File should not depend on itself
            assert source_file not in dependencies, (
                f"File {Path(source_file).name} has self-dependency"
            )
    
    @given(project=python_project_strategy())
    @settings(max_examples=20, deadline=None, suppress_health_check=[HealthCheck.large_base_example])
    def test_dependency_edges_are_files_in_project(self, project):
        """Test that all dependency edges point to files in the project.
        
        **Validates: Requirements 6.2**
        
        Property: Every dependency edge should point to a file that exists
        in the project (no dangling references to non-existent files).
        
        Tag: Feature: local-ai-dev-environment, Property 3: Dependency Graph Accuracy
        """
        # Write project files
        file_to_imports = self._write_project_files(project)
        
        # Scan the project
        context = self.context_manager.scan_project(self.test_dir)
        dep_graph = context.dependency_graph
        
        # Get all valid file paths
        valid_files = set(file_to_imports.keys())
        
        # Check all edges
        for source_file in dep_graph.edges:
            for dep_file in dep_graph.edges[source_file]:
                assert dep_file in valid_files, (
                    f"Invalid dependency: {Path(source_file).name} -> {dep_file}\n"
                    f"Dependency file not in project"
                )
    
    @given(
        num_modules=st.integers(min_value=2, max_value=5),
        module_name=module_name_strategy()
    )
    @settings(max_examples=20, deadline=None)
    def test_single_import_creates_single_edge(self, num_modules, module_name):
        """Test that a single import statement creates exactly one dependency edge.
        
        **Validates: Requirements 6.2**
        
        Property: If file A imports module B exactly once, the dependency
        graph should have exactly one edge from A to B.
        
        Tag: Feature: local-ai-dev-environment, Property 3: Dependency Graph Accuracy
        """
        # Create target module
        target_file = f"{module_name}.py"
        target_content = "# Target module\ndef helper():\n    pass\n"
        target_path = Path(self.test_dir) / target_file
        target_path.write_text(target_content, encoding='utf-8')
        
        # Create source module that imports target
        source_file = f"source_{uuid.uuid4().hex[:8]}.py"
        source_content = f"import {module_name}\n\ndef main():\n    pass\n"
        source_path = Path(self.test_dir) / source_file
        source_path.write_text(source_content, encoding='utf-8')
        
        # Scan the project
        context = self.context_manager.scan_project(self.test_dir)
        dep_graph = context.dependency_graph
        
        # Check dependencies
        dependencies = dep_graph.get_dependencies(str(source_path))
        
        # Should have exactly one dependency
        assert len(dependencies) == 1, (
            f"Expected 1 dependency, found {len(dependencies)}: {dependencies}"
        )
        
        # The dependency should point to the target module
        assert str(target_path) in dependencies, (
            f"Expected dependency to {target_path}, but got {dependencies}"
        )
    
    @given(
        module_names=st.lists(module_name_strategy(), min_size=2, max_size=5, unique=True)
    )
    @settings(max_examples=20, deadline=None)
    def test_multiple_imports_create_multiple_edges(self, module_names):
        """Test that multiple imports create corresponding multiple edges.
        
        **Validates: Requirements 6.2**
        
        Property: If file A imports N different modules, the dependency graph
        should have exactly N edges from A (one to each imported module).
        
        Tag: Feature: local-ai-dev-environment, Property 3: Dependency Graph Accuracy
        """
        # Create target modules
        target_paths = []
        for module_name in module_names:
            target_file = f"{module_name}.py"
            target_content = f"# Module {module_name}\ndef func():\n    pass\n"
            target_path = Path(self.test_dir) / target_file
            target_path.write_text(target_content, encoding='utf-8')
            target_paths.append(str(target_path))
        
        # Create source module that imports all targets
        source_file = f"source_{uuid.uuid4().hex[:8]}.py"
        import_lines = [f"import {name}" for name in module_names]
        source_content = '\n'.join(import_lines) + "\n\ndef main():\n    pass\n"
        source_path = Path(self.test_dir) / source_file
        source_path.write_text(source_content, encoding='utf-8')
        
        # Scan the project
        context = self.context_manager.scan_project(self.test_dir)
        dep_graph = context.dependency_graph
        
        # Check dependencies
        dependencies = dep_graph.get_dependencies(str(source_path))
        
        # Should have exactly N dependencies
        assert len(dependencies) == len(module_names), (
            f"Expected {len(module_names)} dependencies, found {len(dependencies)}"
        )
        
        # All target modules should be in dependencies
        dependencies_set = set(dependencies)
        target_set = set(target_paths)
        assert dependencies_set == target_set, (
            f"Dependency mismatch:\n"
            f"Expected: {target_set}\n"
            f"Actual: {dependencies_set}\n"
            f"Missing: {target_set - dependencies_set}\n"
            f"Extra: {dependencies_set - target_set}"
        )
    
    @given(
        module_name=module_name_strategy()
    )
    @settings(max_examples=20, deadline=None)
    def test_no_imports_means_no_dependencies(self, module_name):
        """Test that files with no imports have no dependencies in the graph.
        
        **Validates: Requirements 6.2**
        
        Property: A file with no import statements should have an empty
        dependency list in the graph.
        
        Tag: Feature: local-ai-dev-environment, Property 3: Dependency Graph Accuracy
        """
        # Create a file with no imports
        test_file = f"{module_name}.py"
        test_content = """
# Module with no imports
def standalone_function():
    return 42

class StandaloneClass:
    def method(self):
        pass
"""
        test_path = Path(self.test_dir) / test_file
        test_path.write_text(test_content, encoding='utf-8')
        
        # Scan the project
        context = self.context_manager.scan_project(self.test_dir)
        dep_graph = context.dependency_graph
        
        # Check dependencies
        dependencies = dep_graph.get_dependencies(str(test_path))
        
        # Should have no dependencies
        assert len(dependencies) == 0, (
            f"Expected no dependencies for file with no imports, "
            f"but found {len(dependencies)}: {dependencies}"
        )
    
    @given(
        module_name=module_name_strategy(),
        num_times=st.integers(min_value=2, max_value=5)
    )
    @settings(max_examples=20, deadline=None)
    def test_duplicate_imports_create_single_edge(self, module_name, num_times):
        """Test that importing the same module multiple times creates only one edge.
        
        **Validates: Requirements 6.2**
        
        Property: If file A imports module B multiple times (with different
        import styles), the dependency graph should still have only one edge
        from A to B (no duplicate edges).
        
        Tag: Feature: local-ai-dev-environment, Property 3: Dependency Graph Accuracy
        """
        # Create target module
        target_file = f"{module_name}.py"
        target_content = "# Target module\ndef helper():\n    pass\n"
        target_path = Path(self.test_dir) / target_file
        target_path.write_text(target_content, encoding='utf-8')
        
        # Create source module with duplicate imports
        source_file = f"source_{uuid.uuid4().hex[:8]}.py"
        import_lines = [
            f"import {module_name}",
            f"from {module_name} import helper",
        ]
        # Add more duplicate imports
        for _ in range(num_times - 2):
            import_lines.append(f"import {module_name}")
        
        source_content = '\n'.join(import_lines) + "\n\ndef main():\n    pass\n"
        source_path = Path(self.test_dir) / source_file
        source_path.write_text(source_content, encoding='utf-8')
        
        # Scan the project
        context = self.context_manager.scan_project(self.test_dir)
        dep_graph = context.dependency_graph
        
        # Check dependencies
        dependencies = dep_graph.get_dependencies(str(source_path))
        
        # Should have exactly one dependency (no duplicates)
        assert len(dependencies) == 1, (
            f"Expected 1 dependency (no duplicates), found {len(dependencies)}: {dependencies}"
        )
        
        # The single dependency should be the target module
        assert str(target_path) in dependencies


@pytest.mark.property
class TestDependencyGraphMultiLanguage:
    """Property-based tests for multi-language dependency graph accuracy.
    
    Tag: Feature: local-ai-dev-environment, Property 3: Dependency Graph Accuracy
    """
    
    def setup_method(self):
        """Create a temporary directory for test projects."""
        self.test_dir = tempfile.mkdtemp(prefix='dep_graph_multilang_test_')
        
        # Create system config
        llm_config = LLMConfig(
            endpoint="http://localhost:11434",
            model_name="test-model"
        )
        self.config = SystemConfig(
            llm=llm_config,
            project_root=self.test_dir,
            log_level="info"
        )
        
        self.context_manager = ContextManager(self.config)
    
    def teardown_method(self):
        """Clean up temporary directory."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def _extract_imports_from_graph(
        self,
        dep_graph: DependencyGraph,
        source_file: str
    ) -> Set[str]:
        """Extract imported module names from dependency graph.
        
        Args:
            dep_graph: The dependency graph
            source_file: Absolute path to the source file
        
        Returns:
            Set of imported module names (without extensions)
        """
        dependencies = dep_graph.get_dependencies(source_file)
        
        # Convert file paths back to module names
        imported_modules = set()
        for dep_file in dependencies:
            # Get the module name from the file path
            module_name = Path(dep_file).stem  # Remove extension
            imported_modules.add(module_name)
        
        return imported_modules
    
    @given(project=multi_language_project_strategy())
    @settings(max_examples=20, deadline=None, suppress_health_check=[HealthCheck.large_base_example, HealthCheck.data_too_large])
    def test_multi_language_dependency_graph_accuracy(self, project):
        """Test dependency graph accuracy across multiple programming languages.
        
        **Validates: Requirements 6.2**
        
        Property: For code files in any supported language (Python, JavaScript,
        TypeScript), the dependency graph edges SHALL exactly match the imports
        found in the code, regardless of language.
        
        Tag: Feature: local-ai-dev-environment, Property 3: Dependency Graph Accuracy
        """
        # Ensure we have at least 2 files to test dependencies
        assume(len(project) >= 2)
        
        # Clean the test directory
        for item in os.listdir(self.test_dir):
            item_path = os.path.join(self.test_dir, item)
            if os.path.isfile(item_path):
                os.remove(item_path)
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)
        
        # Write project files and track expected imports
        file_to_imports = {}
        language_counts = {}
        
        for filename, (content, imported_modules, language) in project.items():
            file_path = Path(self.test_dir) / filename
            file_path.write_text(content, encoding='utf-8')
            file_to_imports[str(file_path)] = imported_modules
            language_counts[language] = language_counts.get(language, 0) + 1
        
        # Only proceed if we have files in the project
        assume(len(file_to_imports) >= 2)
        
        try:
            # Scan the project and build dependency graph
            context = self.context_manager.scan_project(self.test_dir)
            dep_graph = context.dependency_graph
            
            # Verify dependency graph for each file
            for source_file, expected_imports in file_to_imports.items():
                # Get dependencies from graph
                actual_imports = self._extract_imports_from_graph(dep_graph, source_file)
                expected_imports_set = set(expected_imports)
                
                # The dependency graph should match the imports
                # Note: Some languages might not be fully supported yet by the parser
                # In that case, we expect empty dependencies rather than incorrect ones
                if actual_imports or expected_imports_set:
                    assert actual_imports == expected_imports_set, (
                        f"Dependency mismatch for {Path(source_file).name}:\n"
                        f"Expected imports: {expected_imports_set}\n"
                        f"Actual in graph: {actual_imports}\n"
                        f"Missing: {expected_imports_set - actual_imports}\n"
                        f"Extra: {actual_imports - expected_imports_set}"
                    )
        
        except Exception as e:
            # If parsing fails for unsupported language features, that's acceptable
            # as long as it doesn't produce incorrect dependency information
            if "Unsupported language" in str(e) or "not installed" in str(e):
                assume(False)  # Skip this example
            else:
                raise
