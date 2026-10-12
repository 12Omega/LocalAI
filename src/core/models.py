"""Core data models for Local AI Development Environment.

This module defines the fundamental data structures used throughout the system
for task execution, code analysis, configuration, and web research.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime


# Task and Execution Models

@dataclass
class ExecutionStep:
    """Single step in execution plan."""
    action: str  # create_file, edit_file, run_command, search_web, etc.
    parameters: Dict[str, Any]
    rationale: str


@dataclass
class ExecutionPlan:
    """Plan for executing a development task."""
    steps: List[ExecutionStep]
    estimated_complexity: str  # simple, moderate, complex
    required_tools: List[str]  # file_ops, web_research, etc.


@dataclass
class TaskResult:
    """Result of task execution."""
    success: bool
    actions_taken: List[ExecutionStep]
    files_modified: List[str]
    tests_passed: bool
    error_message: Optional[str]
    execution_log: List[str]


# Code Models

@dataclass
class SearchResult:
    """Result from code search."""
    file_path: str
    line_number: int
    match_text: str
    context_before: List[str]
    context_after: List[str]


@dataclass
class SymbolLocation:
    """Location of a code symbol."""
    file_path: str
    line_number: int
    symbol_name: str
    symbol_type: str  # function, class, method, variable


@dataclass
class CodeAnalysis:
    """Analysis of a code file."""
    language: str
    imports: List[str]
    symbols: List[SymbolLocation]
    dependencies: List[str]  # Other files this file depends on
    structure: str  # High-level outline of file contents


# Configuration Models

@dataclass
class LLMConfig:
    """Configuration for local language model."""
    endpoint: str  # e.g., "http://localhost:11434"
    model_name: str  # e.g., "codellama:13b"
    temperature: float = 0.2
    max_tokens: int = 4096
    context_length: int = 16384
    backend_type: str = "ollama"  # ollama, llamacpp, openai-compatible


@dataclass
class SystemConfig:
    """System-wide configuration."""
    llm: LLMConfig
    project_root: str
    log_level: str = "info"  # debug, info, warning, error
    web_research_enabled: bool = True
    self_improvement_enabled: bool = False
    excluded_directories: List[str] = field(default_factory=lambda: [
        "node_modules", ".git", "__pycache__", ".pytest_cache",
        "venv", ".venv", "build", "dist", ".hypothesis"
    ])


# Context Management Models

@dataclass
class FileTree:
    """Representation of project file structure."""
    root: str
    files: List[str]  # All file paths relative to root
    directories: List[str]  # All directory paths relative to root


@dataclass
class DependencyGraph:
    """Graph of dependencies between files."""
    nodes: List[str]  # File paths
    edges: Dict[str, List[str]]  # file_path -> [list of files it depends on]
    
    def add_dependency(self, from_file: str, to_file: str):
        """Add a dependency edge."""
        if from_file not in self.edges:
            self.edges[from_file] = []
        if to_file not in self.edges[from_file]:
            self.edges[from_file].append(to_file)
    
    def get_dependencies(self, file_path: str) -> List[str]:
        """Get all direct dependencies of a file."""
        return self.edges.get(file_path, [])
    
    def get_all_dependencies(self, file_path: str, visited: Optional[set] = None) -> List[str]:
        """Get all transitive dependencies of a file."""
        if visited is None:
            visited = set()
        
        if file_path in visited:
            return []
        
        visited.add(file_path)
        all_deps = []
        
        for dep in self.get_dependencies(file_path):
            all_deps.append(dep)
            all_deps.extend(self.get_all_dependencies(dep, visited))
        
        return all_deps


@dataclass
class LanguageStack:
    """Information about languages and frameworks in project."""
    languages: List[str]  # e.g., ["Python", "JavaScript"]
    frameworks: List[str]  # e.g., ["Flask", "React"]
    build_tools: List[str]  # e.g., ["npm", "pip", "maven"]
    primary_language: Optional[str] = None  # Most common language


@dataclass
class ProjectContext:
    """Complete understanding of project structure."""
    root_path: str
    languages: List[str]
    frameworks: List[str]
    file_tree: FileTree
    dependency_graph: DependencyGraph
    key_files: Dict[str, str]  # e.g., {"build_script": "build.sh", "main_entry": "main.py"}
    language_stack: LanguageStack


# LLM Interface Models

@dataclass
class Tool:
    """Definition of a tool that can be called by the LLM."""
    name: str
    description: str
    parameters: Dict[str, Any]  # JSON schema for parameters


@dataclass
class ToolCall:
    """A tool call requested by the LLM."""
    name: str
    arguments: Dict[str, Any]


@dataclass
class LLMResponse:
    """Response from the language model."""
    content: str  # Text response from LLM
    tool_calls: List[ToolCall] = field(default_factory=list)  # Any tool calls requested
    finish_reason: Optional[str] = None  # stop, tool_calls, length, etc.
    usage: Optional[Dict[str, int]] = None  # Token usage statistics


# Self-Improvement Models

@dataclass
class ImprovementOpportunity:
    """Identified opportunity for system improvement."""
    category: str  # code_quality, new_capability, performance, reliability
    description: str
    affected_files: List[str]
    severity: str  # low, medium, high
    potential_impact: str  # Description of expected improvement


@dataclass
class ImprovementProposal:
    """Specific proposal for system improvement."""
    opportunity: ImprovementOpportunity
    changes: Dict[str, str]  # file_path -> new_content
    rationale: str
    test_plan: str
    rollback_plan: str


@dataclass
class TestMetrics:
    """Metrics measuring system effectiveness."""
    total_tests: int
    tests_passed: int
    tests_failed: int
    success_rate: float  # Percentage of tests passed
    error_rate: float  # Percentage of tests failed
    execution_time: float  # Total time to run tests in seconds


@dataclass
class SelfModificationLog:
    """Audit log entry for self-modification."""
    timestamp: datetime
    category: str  # code_quality, new_capability, performance, reliability
    description: str
    files_modified: List[str]
    test_results_before: TestMetrics
    test_results_after: TestMetrics
    reverted: bool
    revert_reason: Optional[str] = None


@dataclass
class ImplementationResult:
    """Result of implementing an improvement."""
    success: bool
    files_modified: List[str]
    backup_path: Optional[str]
    error_message: Optional[str] = None
