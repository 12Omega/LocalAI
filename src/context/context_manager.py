"""Context Manager for project understanding and code context extraction.

This module provides the ContextManager class which builds and maintains
understanding of project structure, dependencies, and relevant context for
development tasks.

Key capabilities:
- Scan project structure and build file tree
- Detect languages and frameworks in use
- Build dependency graphs between code files
- Extract relevant files for specific tasks
- Analyze code files to extract symbols and structure
- Cache analysis results for performance
"""

import os
from pathlib import Path
from typing import List, Dict, Optional, Set
from dataclasses import dataclass, field
import json
import hashlib

from src.core.models import (
    ProjectContext,
    DependencyGraph,
    LanguageStack,
    FileTree,
    CodeAnalysis,
    SystemConfig
)
from src.context.ast_parser import ASTParser


class ContextManager:
    """Manages project context and code understanding.
    
    The ContextManager builds and maintains an understanding of project
    structure, including:
    - File organization and tree structure
    - Programming languages and frameworks in use
    - Dependencies between code files
    - Symbols (functions, classes) defined in each file
    - Relevant context for specific development tasks
    
    Analysis results are cached to improve performance on repeated operations.
    The cache is automatically updated when files change.
    """
    
    # Framework detection markers
    FRAMEWORK_MARKERS = {
        'Flask': ['flask'],  # Check for Flask in requirements or imports
        'Django': ['django', 'manage.py'],
        'FastAPI': ['fastapi'],
        'React': ['react', 'package.json'],
        'Vue': ['vue', 'package.json'],
        'Angular': ['@angular/core', 'angular.json'],
        'Express': ['express', 'package.json'],
        'Spring': ['pom.xml', 'spring'],
        'Gin': ['gin-gonic/gin'],
        'Actix': ['actix-web'],
    }
    
    # Build tool markers
    BUILD_TOOL_MARKERS = {
        'npm': 'package.json',
        'yarn': 'yarn.lock',
        'pip': 'requirements.txt',
        'pipenv': 'Pipfile',
        'poetry': 'pyproject.toml',
        'maven': 'pom.xml',
        'gradle': 'build.gradle',
        'cargo': 'Cargo.toml',
        'go mod': 'go.mod',
        'make': 'Makefile',
    }
    
    # Key file patterns
    KEY_FILE_PATTERNS = {
        'main_entry': ['main.py', 'index.js', 'index.ts', 'main.go', 'main.rs', 'Main.java', 'main.cpp'],
        'config': ['config.py', 'config.js', 'config.json', 'settings.py', 'appsettings.json'],
        'readme': ['README.md', 'README.txt', 'README'],
        'tests': ['test_*.py', '*_test.py', '*.test.js', '*.test.ts', '*_test.go', '*_test.rs'],
    }
    
    def __init__(self, config: SystemConfig):
        """Initialize the Context Manager.
        
        Args:
            config: System configuration including project root and exclusions
        """
        self.config = config
        self.ast_parser = ASTParser()
        
        # Cache for analysis results
        self._analysis_cache: Dict[str, CodeAnalysis] = {}
        self._file_hashes: Dict[str, str] = {}  # Track file changes
        
        # Project context (built during scan)
        self._project_context: Optional[ProjectContext] = None
    
    def scan_project(self, root_path: str) -> ProjectContext:
        """Scan project directory to build complete understanding.
        
        This performs an initial comprehensive scan of the project:
        1. Build file tree structure
        2. Detect languages and frameworks
        3. Build dependency graph
        4. Identify key files (entry points, config, etc.)
        
        Args:
            root_path: Root directory of the project to scan
            
        Returns:
            ProjectContext containing complete project understanding
            
        Raises:
            FileNotFoundError: If root_path does not exist
            PermissionError: If root_path is not accessible
        """
        if not os.path.exists(root_path):
            raise FileNotFoundError(f"Project root not found: {root_path}")
        
        if not os.path.isdir(root_path):
            raise NotADirectoryError(f"Project root is not a directory: {root_path}")
        
        # Build file tree
        file_tree = self._build_file_tree(root_path)
        
        # Detect language stack
        language_stack = self.detect_language_stack(root_path, file_tree)
        
        # Create a temporary minimal project context for dependency resolution
        # This allows analyze_code to resolve imports during the dependency graph build
        self._project_context = ProjectContext(
            root_path=root_path,
            languages=language_stack.languages,
            frameworks=language_stack.frameworks,
            file_tree=file_tree,
            dependency_graph=DependencyGraph(nodes=[], edges={}),  # Empty for now
            key_files={},
            language_stack=language_stack
        )
        
        # Build dependency graph (now with project_context available)
        dependency_graph = self._build_dependency_graph(root_path, file_tree)
        
        # Identify key files
        key_files = self._identify_key_files(root_path, file_tree)
        
        # Update project context with complete information
        self._project_context = ProjectContext(
            root_path=root_path,
            languages=language_stack.languages,
            frameworks=language_stack.frameworks,
            file_tree=file_tree,
            dependency_graph=dependency_graph,
            key_files=key_files,
            language_stack=language_stack
        )
        
        return self._project_context
    
    def get_relevant_files(self, task_description: str) -> List[str]:
        """Identify files relevant to a specific task.
        
        This analyzes the task description to determine which files are
        likely relevant for completing the task. Uses heuristics based on:
        - Keywords in task description matching file/symbol names
        - File types relevant to the task
        - Dependencies between files
        
        Args:
            task_description: Natural language description of the task
            
        Returns:
            List of file paths (absolute) that are relevant to the task
        """
        if not self._project_context:
            raise RuntimeError("Project not scanned. Call scan_project() first.")
        
        relevant_files = []
        task_lower = task_description.lower()
        
        # Extract potential file/symbol names from task description
        # (Simple keyword matching - can be enhanced with NLP)
        keywords = set(word.strip('.,!?()[]{}') for word in task_lower.split())
        
        # Check all files in project
        for file_path in self._project_context.file_tree.files:
            full_path = os.path.join(self._project_context.root_path, file_path)
            
            # Check if file name matches keywords
            file_name = os.path.basename(file_path).lower()
            file_name_no_ext = os.path.splitext(file_name)[0]
            
            if any(keyword in file_name_no_ext for keyword in keywords):
                relevant_files.append(full_path)
                continue
            
            # Check if file contains symbols matching keywords
            analysis = self.analyze_code(full_path)
            if analysis:
                for symbol in analysis.symbols:
                    if any(keyword in symbol.symbol_name.lower() for keyword in keywords):
                        relevant_files.append(full_path)
                        break
        
        return relevant_files
    
    def get_dependencies(self, file_path: str) -> DependencyGraph:
        """Get dependency graph for a specific file.
        
        Returns both direct and transitive dependencies of the file.
        
        Args:
            file_path: Path to the file (absolute or relative to project root)
            
        Returns:
            DependencyGraph containing the file and its dependencies
        """
        if not self._project_context:
            raise RuntimeError("Project not scanned. Call scan_project() first.")
        
        # Normalize path
        if not os.path.isabs(file_path):
            file_path = os.path.join(self._project_context.root_path, file_path)
        
        # Create a subgraph containing just this file's dependencies
        subgraph = DependencyGraph(nodes=[file_path], edges={})
        
        # Get all dependencies (direct and transitive)
        all_deps = self._project_context.dependency_graph.get_all_dependencies(file_path)
        
        # Add nodes and edges to subgraph
        for dep in all_deps:
            if dep not in subgraph.nodes:
                subgraph.nodes.append(dep)
        
        # Copy relevant edges
        for node in subgraph.nodes:
            deps = self._project_context.dependency_graph.get_dependencies(node)
            if deps:
                subgraph.edges[node] = [d for d in deps if d in subgraph.nodes]
        
        return subgraph
    
    def analyze_code(self, file_path: str) -> Optional[CodeAnalysis]:
        """Analyze a code file to extract symbols, imports, and structure.
        
        This uses AST parsing to extract:
        - Programming language
        - Import statements
        - Function and class definitions (symbols)
        - Dependencies on other files
        - High-level file structure
        
        Results are cached and reused if the file hasn't changed.
        
        Args:
            file_path: Path to the code file (absolute or relative to project root)
            
        Returns:
            CodeAnalysis object with extracted information, or None if file
            cannot be parsed (unsupported language, syntax errors, etc.)
        """
        # Normalize path
        if not os.path.isabs(file_path):
            if self._project_context:
                file_path = os.path.join(self._project_context.root_path, file_path)
        
        # Check if file exists
        if not os.path.exists(file_path):
            return None
        
        # Check cache
        file_hash = self._get_file_hash(file_path)
        if file_path in self._analysis_cache and self._file_hashes.get(file_path) == file_hash:
            return self._analysis_cache[file_path]
        
        # Detect language
        language = self.ast_parser.detect_language(file_path)
        if not language:
            return None  # Unsupported file type
        
        # Parse file
        try:
            tree = self.ast_parser.parse_file(file_path, language)
            if not tree:
                return None
            
            # Extract symbols
            symbols = self.ast_parser.extract_symbols(tree, file_path, language)
            
            # Extract imports
            imports = self.ast_parser.extract_imports(tree, language)
            
            # Build dependencies (resolve imports to file paths)
            dependencies = self._resolve_imports_to_files(file_path, imports, language)
            
            # Generate structure outline
            structure = self._generate_structure_outline(symbols)
            
            # Create analysis
            analysis = CodeAnalysis(
                language=language,
                imports=imports,
                symbols=symbols,
                dependencies=dependencies,
                structure=structure
            )
            
            # Update cache
            self._analysis_cache[file_path] = analysis
            self._file_hashes[file_path] = file_hash
            
            return analysis
            
        except Exception as e:
            # Log error and return None
            # (In production, should use proper logging)
            print(f"Error analyzing {file_path}: {e}")
            return None
    
    def detect_language_stack(self, root_path: Optional[str] = None, file_tree: Optional[FileTree] = None) -> LanguageStack:
        """Detect languages and frameworks used in the project.
        
        This analyzes the project to identify:
        - Programming languages (based on file extensions)
        - Frameworks (based on marker files and dependencies)
        - Build tools (based on marker files)
        - Primary language (most common)
        
        Args:
            root_path: Project root directory (uses cached context if not provided)
            file_tree: File tree to analyze (builds it if not provided)
            
        Returns:
            LanguageStack with detected languages, frameworks, and tools
        """
        # Use cached context if available
        if root_path is None and self._project_context:
            root_path = self._project_context.root_path
            file_tree = self._project_context.file_tree
        
        if root_path is None:
            raise ValueError("root_path required when project not scanned")
        
        # Build file tree if not provided
        if file_tree is None:
            file_tree = self._build_file_tree(root_path)
        
        # Count files by language
        language_counts: Dict[str, int] = {}
        
        for file_path in file_tree.files:
            ext = Path(file_path).suffix.lower()
            language = self.ast_parser.EXTENSION_TO_LANGUAGE.get(ext)
            
            if language:
                # Capitalize language name
                lang_name = language.capitalize()
                if lang_name == 'Javascript':
                    lang_name = 'JavaScript'
                elif lang_name == 'Typescript':
                    lang_name = 'TypeScript'
                elif lang_name == 'Cpp':
                    lang_name = 'C++'
                
                language_counts[lang_name] = language_counts.get(lang_name, 0) + 1
        
        # Get languages sorted by frequency
        languages = sorted(language_counts.keys(), key=lambda x: language_counts[x], reverse=True)
        primary_language = languages[0] if languages else None
        
        # Detect frameworks
        frameworks = self._detect_frameworks(root_path, file_tree)
        
        # Detect build tools
        build_tools = self._detect_build_tools(root_path, file_tree)
        
        return LanguageStack(
            languages=languages,
            frameworks=frameworks,
            build_tools=build_tools,
            primary_language=primary_language
        )
    
    def invalidate_cache(self, file_path: Optional[str] = None):
        """Invalidate analysis cache for a file or all files.
        
        Call this when files are modified externally to force re-analysis.
        
        Args:
            file_path: Specific file to invalidate, or None to clear all cache
        """
        if file_path:
            self._analysis_cache.pop(file_path, None)
            self._file_hashes.pop(file_path, None)
        else:
            self._analysis_cache.clear()
            self._file_hashes.clear()
    
    # Private helper methods
    
    def _build_file_tree(self, root_path: str) -> FileTree:
        """Build file tree structure by walking directory.
        
        Args:
            root_path: Root directory to scan
            
        Returns:
            FileTree with all files and directories
        """
        files = []
        directories = []
        
        # Normalize the root path to ensure consistent path handling
        root_path = os.path.abspath(root_path)
        
        for dirpath, dirnames, filenames in os.walk(root_path):
            # Ensure we're still within the root path
            # This prevents traversal to parent directories
            abs_dirpath = os.path.abspath(dirpath)
            if not abs_dirpath.startswith(root_path):
                continue
            
            # Filter excluded directories
            dirnames[:] = [d for d in dirnames if d not in self.config.excluded_directories]
            
            # Get relative path
            rel_dir = os.path.relpath(dirpath, root_path)
            
            # Add directory (skip root itself)
            if rel_dir != '.':
                directories.append(rel_dir)
            
            # Add files
            for filename in filenames:
                rel_file = os.path.join(rel_dir, filename) if rel_dir != '.' else filename
                files.append(rel_file)
        
        return FileTree(root=root_path, files=files, directories=directories)
    
    def _build_dependency_graph(self, root_path: str, file_tree: FileTree) -> DependencyGraph:
        """Build dependency graph by analyzing imports.
        
        Args:
            root_path: Project root directory
            file_tree: File tree to analyze
            
        Returns:
            DependencyGraph with all dependencies
        """
        graph = DependencyGraph(nodes=[], edges={})
        
        # Analyze each code file
        for file_path in file_tree.files:
            full_path = os.path.join(root_path, file_path)
            
            # Only analyze code files
            language = self.ast_parser.detect_language(full_path)
            if not language:
                continue
            
            # Add node
            if full_path not in graph.nodes:
                graph.nodes.append(full_path)
            
            # Analyze and add dependencies
            analysis = self.analyze_code(full_path)
            if analysis:
                for dep in analysis.dependencies:
                    graph.add_dependency(full_path, dep)
                    if dep not in graph.nodes:
                        graph.nodes.append(dep)
        
        return graph
    
    def _detect_frameworks(self, root_path: str, file_tree: FileTree) -> List[str]:
        """Detect frameworks by looking for marker files and imports.
        
        Args:
            root_path: Project root directory
            file_tree: File tree to analyze
            
        Returns:
            List of detected framework names
        """
        frameworks = []
        
        # Helper to find files by basename
        def find_file_by_name(filename: str) -> str:
            """Find first file with matching basename."""
            for file_path in file_tree.files:
                if os.path.basename(file_path) == filename:
                    return file_path
            return None
        
        for framework, markers in self.FRAMEWORK_MARKERS.items():
            detected = False
            
            for marker in markers:
                # Skip generic marker files that need content checking
                if marker in ['package.json', 'requirements.txt', 'pom.xml']:
                    continue
                
                # Check for specific marker files (like manage.py, angular.json, etc.)
                if any(marker in file_path or marker == os.path.basename(file_path) for file_path in file_tree.files):
                    detected = True
                    break
            
            # If not detected by specific markers, check file contents
            if not detected:
                # For Python frameworks, check requirements.txt
                req_file = find_file_by_name('requirements.txt')
                if req_file:
                    req_path = os.path.join(root_path, req_file)
                    try:
                        with open(req_path, 'r') as f:
                            content = f.read().lower()
                            # Check if any non-generic marker appears in requirements
                            for marker in markers:
                                if marker not in ['package.json', 'requirements.txt', 'pom.xml']:
                                    if marker.lower() in content:
                                        detected = True
                                        break
                    except:
                        pass
                
                # For Node frameworks, check package.json
                pkg_file = find_file_by_name('package.json')
                if not detected and pkg_file:
                    pkg_path = os.path.join(root_path, pkg_file)
                    try:
                        with open(pkg_path, 'r') as f:
                            content = f.read().lower()
                            # Check if any non-generic marker appears in package.json
                            for marker in markers:
                                if marker not in ['package.json', 'requirements.txt', 'pom.xml']:
                                    if marker.lower() in content:
                                        detected = True
                                        break
                    except:
                        pass
                
                # For Spring, check pom.xml content
                pom_file = find_file_by_name('pom.xml')
                if not detected and pom_file:
                    pom_path = os.path.join(root_path, pom_file)
                    try:
                        with open(pom_path, 'r') as f:
                            content = f.read().lower()
                            # Check if any non-generic marker appears in pom.xml
                            for marker in markers:
                                if marker not in ['package.json', 'requirements.txt', 'pom.xml']:
                                    if marker.lower() in content:
                                        detected = True
                                        break
                    except:
                        pass
                
                # For Go frameworks (Gin), check go.mod content
                go_mod_file = find_file_by_name('go.mod')
                if not detected and go_mod_file:
                    go_mod_path = os.path.join(root_path, go_mod_file)
                    try:
                        with open(go_mod_path, 'r') as f:
                            content = f.read().lower()
                            # Check if any non-generic marker appears in go.mod
                            for marker in markers:
                                if marker not in ['package.json', 'requirements.txt', 'pom.xml']:
                                    if marker.lower() in content:
                                        detected = True
                                        break
                    except:
                        pass
                
                # For Rust frameworks (Actix), check Cargo.toml content
                cargo_file = find_file_by_name('Cargo.toml')
                if not detected and cargo_file:
                    cargo_path = os.path.join(root_path, cargo_file)
                    try:
                        with open(cargo_path, 'r') as f:
                            content = f.read().lower()
                            # Check if any non-generic marker appears in Cargo.toml
                            for marker in markers:
                                if marker not in ['package.json', 'requirements.txt', 'pom.xml']:
                                    if marker.lower() in content:
                                        detected = True
                                        break
                    except:
                        pass
            
            if detected:
                frameworks.append(framework)
        
        return frameworks
    
    def _detect_build_tools(self, root_path: str, file_tree: FileTree) -> List[str]:
        """Detect build tools by looking for marker files.
        
        Args:
            root_path: Project root directory
            file_tree: File tree to analyze
            
        Returns:
            List of detected build tool names
        """
        build_tools = []
        
        for tool, marker in self.BUILD_TOOL_MARKERS.items():
            # Check if any file matches the marker (handle both exact match and paths)
            for file_path in file_tree.files:
                if os.path.basename(file_path) == marker:
                    build_tools.append(tool)
                    break
        
        return build_tools
    
    def _identify_key_files(self, root_path: str, file_tree: FileTree) -> Dict[str, str]:
        """Identify key project files (entry points, config, etc.).
        
        Args:
            root_path: Project root directory
            file_tree: File tree to analyze
            
        Returns:
            Dictionary mapping key file types to their paths
        """
        key_files = {}
        
        for key, patterns in self.KEY_FILE_PATTERNS.items():
            for pattern in patterns:
                # Simple pattern matching (can be enhanced with glob)
                for file_path in file_tree.files:
                    file_name = os.path.basename(file_path)
                    
                    if '*' in pattern:
                        # Wildcard pattern
                        pattern_parts = pattern.split('*')
                        if all(part in file_name for part in pattern_parts):
                            key_files[key] = file_path
                            break
                    else:
                        # Exact match
                        if file_name == pattern:
                            key_files[key] = file_path
                            break
                
                if key in key_files:
                    break
        
        return key_files
    
    def _resolve_imports_to_files(self, file_path: str, imports: List[str], language: str) -> List[str]:
        """Resolve import statements to actual file paths.
        
        This is a simplified implementation that handles common cases.
        Full implementation would need language-specific module resolution logic.
        
        Args:
            file_path: Path to the file containing imports
            imports: List of import statements
            language: Programming language
            
        Returns:
            List of file paths that are imported
        """
        dependencies = []
        
        if not self._project_context:
            return dependencies
        
        project_root = self._project_context.root_path
        file_dir = os.path.dirname(file_path)
        
        for import_stmt in imports:
            # Extract module name from import statement
            module = self._extract_module_name(import_stmt, language)
            if not module:
                continue
            
            # Try to resolve to file path
            resolved = self._resolve_module_to_file(module, file_dir, project_root, language)
            if resolved and resolved != file_path:  # Don't include self
                dependencies.append(resolved)
        
        return dependencies
    
    def _extract_module_name(self, import_stmt: str, language: str) -> Optional[str]:
        """Extract module name from import statement.
        
        Args:
            import_stmt: Import statement text
            language: Programming language
            
        Returns:
            Module name or None
        """
        import keyword
        
        import_stmt = import_stmt.strip()
        
        if language == 'python':
            # Handle: import module, from module import x
            module_name = None
            if import_stmt.startswith('import '):
                module_name = import_stmt.split()[1].split('.')[0]
            elif import_stmt.startswith('from '):
                parts = import_stmt.split()
                if len(parts) >= 2:
                    module_name = parts[1].split('.')[0]
            
            # Filter out Python keywords - they cannot be module names
            if module_name and keyword.iskeyword(module_name):
                return None
            
            return module_name
        
        elif language in ['javascript', 'typescript']:
            # Handle: import x from 'module'
            if "from '" in import_stmt or 'from "' in import_stmt:
                parts = import_stmt.split('from ')
                if len(parts) >= 2:
                    module = parts[1].strip().strip('";\'')
                    return module
        
        return None
    
    def _resolve_module_to_file(self, module: str, file_dir: str, project_root: str, language: str) -> Optional[str]:
        """Resolve module name to file path.
        
        Args:
            module: Module name to resolve
            file_dir: Directory of the importing file
            project_root: Project root directory
            language: Programming language
            
        Returns:
            Resolved file path or None
        """
        # Skip standard library and external modules
        if not module.startswith('.') and not module.startswith('/'):
            # Check if it's a project-relative module
            if language == 'python':
                # Try to find in project
                candidate = os.path.join(project_root, module.replace('.', os.sep) + '.py')
                if os.path.exists(candidate):
                    return candidate
                # Try __init__.py
                candidate = os.path.join(project_root, module.replace('.', os.sep), '__init__.py')
                if os.path.exists(candidate):
                    return candidate
            return None  # External module
        
        # Relative import
        if module.startswith('.'):
            # Resolve relative to file directory
            # Remove leading './' or '../' but keep the relative path structure
            if module.startswith('./'):
                rel_path = module[2:]  # Remove './'
            elif module.startswith('../'):
                # Handle parent directory imports
                rel_path = module
                # For now, just strip '../' and search in parent
                # More sophisticated resolution would handle multiple '../'
                rel_path = module[3:]
                file_dir = os.path.dirname(file_dir)
            else:
                rel_path = module.lstrip('.')  # Remove all leading dots
            
            if language == 'python':
                candidate = os.path.join(file_dir, rel_path.replace('.', os.sep) + '.py')
            elif language in ['javascript', 'typescript']:
                # Handle .js, .ts extensions
                candidate = os.path.join(file_dir, rel_path)
                if not os.path.exists(candidate):
                    # Try without extension if it already has one
                    if candidate.endswith('.js') or candidate.endswith('.ts'):
                        pass  # Already has extension
                    else:
                        candidate += '.js'
                if not os.path.exists(candidate):
                    candidate = candidate.replace('.js', '.ts') if candidate.endswith('.js') else candidate + '.ts'
            else:
                return None
            
            if os.path.exists(candidate):
                return candidate
        
        return None
    
    def _generate_structure_outline(self, symbols: List) -> str:
        """Generate high-level outline of file structure.
        
        Args:
            symbols: List of SymbolLocation objects
            
        Returns:
            String outline of the file structure
        """
        if not symbols:
            return "Empty file or no symbols found"
        
        lines = []
        current_class = None
        
        for symbol in symbols:
            if symbol.symbol_type == 'class':
                current_class = symbol.symbol_name
                lines.append(f"class {symbol.symbol_name}")
            elif symbol.symbol_type == 'function':
                lines.append(f"  function {symbol.symbol_name}()" if current_class else f"function {symbol.symbol_name}()")
            elif symbol.symbol_type == 'method':
                lines.append(f"  method {symbol.symbol_name}()")
        
        return '\n'.join(lines)
    
    def _get_file_hash(self, file_path: str) -> str:
        """Calculate hash of file content for cache invalidation.
        
        Args:
            file_path: Path to file
            
        Returns:
            MD5 hash of file content
        """
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except:
            return ""
