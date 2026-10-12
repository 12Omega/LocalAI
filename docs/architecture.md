# Architecture Documentation

## System Overview

The Local AI Development Environment is an autonomous, locally-executing AI system designed to write, edit, and improve code without relying on cloud services. The system uses a modular architecture with clear separation between reasoning (LLM), execution (tools), and orchestration (task management).

## Core Architectural Principles

### 1. Local-First Design
All core functionality operates without internet connectivity using local resources:
- Local LLM for reasoning and planning
- Local file system for all operations
- Local command execution for builds and tests
- Optional web research that can be disabled

### 2. Agent Loop Pattern
The system follows a continuous agent loop:
```
Plan → Execute → Observe → Reflect → Iterate
```

This pattern enables autonomous operation where the AI:
- Plans steps to accomplish a task
- Executes those steps using available tools
- Observes the results of its actions
- Reflects on progress and decides next actions
- Iterates until task completion

### 3. Tool-Based Interface
The LLM interacts with the system through well-defined tools:
- **File Operations**: Create, read, update, delete, move files
- **Code Search**: Search by text, filename, or symbol
- **Command Execution**: Run shell commands and capture output
- **Context Analysis**: Understand project structure and dependencies
- **Web Research**: (Optional) Search and fetch web content

### 4. Context-Aware Operation
All code generation and editing is informed by:
- Project structure and technology stack
- Dependency relationships between files
- Existing code style and conventions
- Relevant code context for the task

### 5. Modular Component Design
Components are loosely coupled with clear interfaces:
- Each component has a single, well-defined responsibility
- Components communicate through data models
- Components can be tested independently
- Components can be replaced or upgraded independently

## System Architecture

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                          User                                │
│                     (CLI Interface)                          │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │   Task Executor        │
              │  (Agent Loop Control)  │
              └─────┬──────────────────┘
                    │
        ┌───────────┼───────────┬────────────┐
        │           │           │            │
        ▼           ▼           ▼            ▼
┌───────────┐ ┌──────────┐ ┌────────┐ ┌──────────────┐
│   Code    │ │ Context  │ │  Web   │ │     Self     │
│   Agent   │ │ Manager  │ │Research│ │ Improvement  │
└─────┬─────┘ └────┬─────┘ └───┬────┘ └──────┬───────┘
      │            │            │              │
      │            │            │              │
      └────────────┴────────────┴──────────────┘
                   │
                   ▼
          ┌────────────────┐
          │  Local LLM     │
          │  Interface     │
          └────────────────┘
                   │
                   ▼
          ┌────────────────┐
          │  Local LLM     │
          │   (Ollama,     │
          │  llama.cpp,    │
          │  etc.)         │
          └────────────────┘
```

## Component Detailed Architecture

### Task Executor

**Responsibility**: Orchestrates the entire agent loop and coordinates all system components.

**Architecture**:
```
TaskExecutor
├── State Management
│   ├── Execution history
│   ├── Modified files tracker
│   ├── Test results cache
│   └── Context window manager
├── Planning Engine
│   └── LLM-based task decomposition
├── Step Execution Router
│   ├── Code operations → Code Agent
│   ├── Context queries → Context Manager
│   ├── Web research → Web Research Module
│   └── Self-improvement → Self-Improvement Engine
├── Result Observer
│   └── Collect and structure operation results
└── Reflection Engine
    └── LLM-based progress assessment
```

**Key Algorithms**:

1. **Context Window Management**:
   ```
   When context approaches limit:
   1. Summarize old execution steps
   2. Retain recent steps in full detail
   3. Keep critical context (file paths, errors)
   4. Calculate remaining token budget
   ```

2. **Task Completion Detection**:
   ```
   Task complete when:
   1. All planned steps executed successfully
   2. Tests pass (if tests were written)
   3. LLM confirms no more work needed
   OR
   1. Max iterations reached
   2. Unrecoverable error encountered
   ```

### Local LLM Interface

**Responsibility**: Abstracts communication with different local LLM backends.

**Architecture**:
```
LocalLLMInterface
├── Backend Adapters
│   ├── OllamaAdapter (REST API)
│   ├── LlamaCppAdapter (OpenAI-compatible)
│   └── GenericOpenAIAdapter
├── Request Formatter
│   ├── Prompt construction
│   ├── Tool definition translation
│   └── Context management
├── Response Parser
│   ├── Text extraction
│   ├── Tool call parsing
│   └── Error detection
└── Error Handler
    ├── Retry logic (exponential backoff)
    ├── Timeout handling
    └── Model unavailable detection
```

**Request Flow**:
```
1. Receive request (prompt + tools)
2. Format for backend:
   - Add system prompt
   - Format tool definitions
   - Calculate token budget
3. Send to LLM endpoint
4. Parse response:
   - Extract text response
   - Parse tool calls (if any)
   - Detect errors
5. Return structured response
```

**Error Handling**:
```
Error Type         | Strategy
-------------------|------------------------------------------
Timeout            | Retry with exponential backoff (3 times)
Connection Failed  | Report model unavailable, fail fast
Invalid Response   | Log response, attempt partial parsing
Rate Limit         | Wait and retry with backoff
```

### Code Agent

**Responsibility**: Handles all code-related operations including generation, editing, and execution.

**Architecture**:
```
CodeAgent
├── File Operations Manager
│   ├── FileOperations (CRUD)
│   └── Reference Updater (for moves)
├── Code Generation Engine
│   ├── Style Analyzer
│   ├── Convention Detector
│   └── LLM-based Generator
├── Code Editing Engine
│   ├── Precise Edit Calculator
│   └── LLM-based Editor
├── Code Search Engine
│   ├── Text Search (regex)
│   ├── File Search (glob)
│   └── Symbol Search (AST-based)
└── Command Executor
    ├── Synchronous execution
    └── Asynchronous execution
```

**Code Generation Strategy**:
```
1. Analyze existing code:
   - Detect indentation (spaces vs tabs, width)
   - Identify naming conventions (snake_case, camelCase)
   - Extract import patterns
   - Identify framework conventions

2. Gather context:
   - Related files from Context Manager
   - Dependency information
   - Project structure

3. Generate code:
   - Use LLM with context
   - Apply detected style rules
   - Follow conventions
   - Include comments

4. Validate:
   - Check syntax (language-specific parser)
   - Verify formatting
   - Log generation details
```

**Code Editing Strategy**:
```
1. Read existing file
2. Identify edit locations:
   - Line ranges to modify
   - Preserve surrounding code
3. Generate edits:
   - Precise replacements
   - Maintain formatting
   - Update dependent sections
4. Apply edits:
   - Validate before write
   - Log changes
5. Verify:
   - Check syntax
   - Run tests if available
```

### Context Manager

**Responsibility**: Builds and maintains understanding of project structure and dependencies.

**Architecture**:
```
ContextManager
├── Project Scanner
│   ├── File tree builder
│   ├── Language detector
│   └── Framework identifier
├── AST Parser (Tree-sitter)
│   ├── Multi-language support
│   ├── Symbol extractor
│   └── Import analyzer
├── Dependency Graph Builder
│   ├── Import tracking
│   ├── Reference mapping
│   └── Graph visualization
├── Relevance Analyzer
│   ├── File relevance scorer
│   └── Context extractor
└── Cache Manager
    ├── Analysis result caching
    └── Incremental updates
```

**Project Scanning Algorithm**:
```
1. Walk directory tree:
   - Skip excluded directories
   - Identify file types
   - Build file tree structure

2. Detect languages:
   - Count files by extension
   - Identify primary language
   - List all languages present

3. Detect frameworks:
   - Look for marker files:
     • package.json → Node.js
     • requirements.txt → Python
     • go.mod → Go
     • Cargo.toml → Rust
   - Identify framework patterns

4. Build dependency graph:
   - Parse imports in each file
   - Create edges between files
   - Identify entry points

5. Index symbols:
   - Extract functions, classes
   - Build symbol table
   - Enable fast lookup

6. Cache results:
   - Store analysis
   - Track file modification times
   - Enable incremental updates
```

**Relevance Scoring Algorithm**:
```
Given task description, score files by:
1. Direct name match (weight: 10)
2. Symbol name match (weight: 8)
3. Dependency relationship (weight: 5)
4. Same directory (weight: 3)
5. Same language (weight: 2)
6. Keyword match in content (weight: 1)

Return top N files by score
```

### Web Research Module

**Responsibility**: Searches web and fetches documentation (when enabled).

**Architecture**:
```
WebResearchModule
├── Search Engine
│   ├── Query formatter
│   ├── Result ranker (prioritize official docs)
│   └── Result deduplicator
├── Web Fetcher
│   ├── HTTP client
│   ├── Redirect handler
│   └── Error handler
├── Content Extractor
│   ├── HTML parser (BeautifulSoup)
│   ├── Main content detector
│   ├── Code block extractor
│   └── Navigation/ad filter
└── Privacy Logger
    └── Request audit trail
```

**Search and Prioritization**:
```
1. Execute search query
2. Collect results
3. Rank by priority:
   - Official docs domains (e.g., python.org, docs.*)
   - Version-specific docs
   - GitHub repositories
   - Stack Overflow
   - Blog posts
4. Return top results
```

**Content Extraction**:
```
1. Fetch HTML content
2. Parse DOM structure
3. Identify main content:
   - Remove navigation
   - Remove advertisements
   - Remove footers/sidebars
4. Extract text and code:
   - Plain text paragraphs
   - Code blocks with language tags
   - Preserve formatting
5. Return structured content
```

### Self-Improvement Engine

**Responsibility**: Analyzes and improves the system's own code.

**Architecture**:
```
SelfImprovementEngine
├── System Analyzer
│   ├── Code quality scanner
│   ├── Performance profiler
│   └── Capability gap detector
├── Improvement Proposer
│   └── LLM-based proposal generator
├── Implementation Engine
│   ├── Backup creator
│   └── Code modifier
├── Test Runner
│   ├── Unit test executor
│   ├── Property test executor
│   └── Integration test executor
├── Metrics Collector
│   ├── Success rate tracker
│   ├── Error rate tracker
│   └── Performance tracker
└── Rollback Manager
    ├── Change reverter
    └── Audit logger
```

**Self-Improvement Workflow**:
```
1. Analyze system code:
   - Identify improvement opportunities
   - Categorize: quality, capability, performance, reliability

2. Propose improvement:
   - Use LLM to generate specific changes
   - Estimate impact and risk

3. Create backup:
   - Copy affected files
   - Record current metrics

4. Implement changes:
   - Apply code modifications
   - Update documentation if needed

5. Test improvements:
   - Run full test suite
   - Measure new metrics

6. Evaluate:
   IF metrics improved or maintained:
     - Keep changes
     - Log success in audit trail
   ELSE:
     - Rollback changes
     - Log failure and reason
```

## Data Flow Diagrams

### Task Execution Data Flow

```
User Input (task description)
    │
    ▼
TaskExecutor.execute_task()
    │
    ├─> LLM: Plan task → ExecutionPlan
    │   (steps: [step1, step2, ...])
    │
    ├─> For each ExecutionStep:
    │   │
    │   ├─> TaskExecutor.execute_step(step)
    │   │   │
    │   │   ├─> Route to component:
    │   │   │   - CodeAgent.create_code()
    │   │   │   - CodeAgent.edit_code()
    │   │   │   - CodeAgent.execute_command()
    │   │   │   - ContextManager.get_relevant_files()
    │   │   │   - WebResearch.search()
    │   │   │
    │   │   └─> OperationResult
    │   │
    │   ├─> Observe results
    │   │
    │   └─> LLM: Reflect on progress → Continue/Complete
    │
    └─> TaskResult
        (success, files_modified, tests_passed, logs)
```

### Code Generation Data Flow

```
Task: "Create module X with functionality Y"
    │
    ▼
CodeAgent.create_code()
    │
    ├─> ContextManager.get_relevant_files()
    │   └─> [relevant_file_paths]
    │
    ├─> ContextManager.analyze_code(existing_files)
    │   └─> CodeAnalysis (style, conventions, patterns)
    │
    ├─> Build context for LLM:
    │   - Task description
    │   - Relevant code snippets
    │   - Detected conventions
    │   - Project structure
    │
    ├─> LLM.generate(context)
    │   └─> Generated code
    │
    ├─> FileOperations.create_file(path, code)
    │   └─> OperationResult
    │
    └─> Return result to TaskExecutor
```

### Context Building Data Flow

```
Project Root
    │
    ▼
ContextManager.scan_project()
    │
    ├─> ProjectScanner.walk_directory()
    │   └─> FileTree
    │
    ├─> For each source file:
    │   │
    │   ├─> ASTParser.parse_file()
    │   │   └─> AST
    │   │
    │   ├─> Extract symbols:
    │   │   └─> [functions, classes, methods]
    │   │
    │   └─> Extract imports:
    │       └─> [dependencies]
    │
    ├─> Build dependency graph:
    │   └─> DependencyGraph
    │
    ├─> Detect languages:
    │   └─> LanguageStack
    │
    ├─> Detect frameworks:
    │   └─> [framework_list]
    │
    ├─> Cache results
    │
    └─> Return ProjectContext
```

## Concurrency and State Management

### Thread Safety

The system is primarily single-threaded for the agent loop:
- One task executes at a time
- State is managed sequentially
- No concurrent modifications

For async command execution:
- Uses separate processes for commands
- Captures output in thread-safe buffers
- Main thread polls for completion

### State Management

**Task Executor State**:
```python
{
  "current_iteration": int,
  "execution_history": [ExecutionStep],
  "modified_files": Set[str],
  "test_results": Dict[str, bool],
  "context_summary": str
}
```

**Context Manager State**:
```python
{
  "project_context": ProjectContext,
  "file_analysis_cache": Dict[str, CodeAnalysis],
  "dependency_graph": DependencyGraph,
  "last_scan_time": datetime
}
```

State is not persisted between runs; each session starts fresh.

## Error Handling Architecture

### Error Categories and Strategies

```
Error Category     | Detection              | Recovery Strategy
-------------------|------------------------|----------------------------------
LLM Timeout        | Request timeout        | Retry with exponential backoff
LLM Unavailable    | Connection error       | Report to user, fail task
File Not Found     | OS error               | Report to user, fail step
Permission Denied  | OS error               | Report with details, fail step
Command Failed     | Non-zero exit          | Report stderr, allow LLM to retry
Syntax Error       | Parser error           | Report to LLM, regenerate code
Test Failure       | Test runner exit code  | Report to LLM, debug and fix
Network Error      | HTTP error             | Retry, try alt source, or skip
Parse Error        | AST parse failure      | Report to user, skip file
```

### Error Propagation

```
Component Error
    │
    ├─> Wrap in OperationResult(success=False, error_message=...)
    │
    ▼
TaskExecutor receives result
    │
    ├─> Log error with context
    │
    ├─> Present to LLM for reflection
    │   │
    │   ├─> LLM decides:
    │   │   - Retry with different approach
    │   │   - Skip and continue
    │   │   - Fail task
    │   │
    │   └─> Generate next action
    │
    └─> Continue or fail based on decision
```

## Performance Considerations

### Context Window Optimization

**Problem**: LLM context windows are limited (16k-32k tokens).

**Solution**: Intelligent context management
```
Priority 1: Task description and current step
Priority 2: Recent execution results (last 3-5 steps)
Priority 3: Relevant code snippets
Priority 4: Project structure summary
Priority 5: Historical steps (summarized)
```

### Caching Strategy

**What is cached**:
- AST parse results (per file)
- Dependency graphs
- Project structure
- Symbol tables
- LLM tokenization

**Cache invalidation**:
- File modification time check
- Explicit invalidation on file write
- Cache expiry after project re-scan

### Performance Bottlenecks

1. **LLM Inference**: Slowest operation (1-30 seconds per request)
   - Mitigation: Minimize LLM calls, batch context

2. **AST Parsing**: Moderate (100-500ms for large files)
   - Mitigation: Cache results, parse only when needed

3. **File System Operations**: Fast (1-10ms)
   - No optimization needed

4. **Web Requests**: Variable (100ms-5s)
   - Mitigation: Cache fetched content, timeout limits

## Security Architecture

### Threat Model

**Out of Scope** (Trust Boundaries):
- User provides safe task descriptions
- Local LLM is trusted
- Local file system is trusted

**In Scope** (Protected Against):
- Unintended file modifications outside project root
- Accidental exposure of code to external services
- Command injection via unsanitized inputs
- Self-improvement damaging system code

### Security Measures

1. **Project Root Isolation**:
   ```
   All file operations:
   - Resolve paths to absolute
   - Verify path starts with project_root
   - Reject paths outside project
   ```

2. **Command Sanitization**:
   ```
   Before executing commands:
   - Use shell=False with argument lists
   - Escape special characters
   - Validate command structure
   ```

3. **Privacy Protection**:
   ```
   Web research:
   - Only send search queries
   - Never send code content
   - Log all outbound requests
   - Allow full disable via config
   ```

4. **Self-Improvement Safety**:
   ```
   Before modifying system code:
   - Create backup
   - Run full test suite
   - Measure metrics
   - Automatic rollback on degradation
   ```

## Extensibility Points

### Adding New Backends

To support a new LLM backend:

1. Create adapter class:
   ```python
   class NewBackendAdapter(LLMBackend):
       def generate(self, prompt, tools):
           # Implement for new backend
   ```

2. Register in LocalLLMInterface:
   ```python
   BACKENDS = {
       "ollama": OllamaAdapter,
       "llamacpp": LlamaCppAdapter,
       "newbackend": NewBackendAdapter
   }
   ```

### Adding New Tools

To add a new tool for the LLM:

1. Implement tool class:
   ```python
   class NewTool:
       def execute(self, parameters):
           # Tool implementation
   ```

2. Add execution handler in TaskExecutor:
   ```python
   def execute_step(self, step):
       if step.action == "new_tool":
           return self.new_tool.execute(step.parameters)
   ```

3. Define tool schema for LLM:
   ```python
   NEW_TOOL_SCHEMA = {
       "name": "new_tool",
       "description": "...",
       "parameters": {...}
   }
   ```

### Adding Language Support

To support a new programming language:

1. Add Tree-sitter grammar:
   ```python
   LANGUAGE_GRAMMARS["newlang"] = tree_sitter.Language(
       "path/to/newlang.so"
   )
   ```

2. Add file extension mapping:
   ```python
   LANGUAGE_EXTENSIONS["newlang"] = [".nl", ".newlang"]
   ```

3. Add language-specific parsing rules in ASTParser

### Adding Framework Detection

To detect a new framework:

1. Add marker file patterns:
   ```python
   FRAMEWORK_MARKERS["newframework"] = [
       "newframework.config",
       "package.json"  # with specific content
   ]
   ```

2. Add detection logic in ContextManager:
   ```python
   def detect_newframework(self, root_path):
       # Check for markers
       # Return True if detected
   ```

## Deployment Architecture

### Local Development

```
Developer Machine
├── Python 3.8+ Environment
├── Local LLM (Ollama/llama.cpp)
│   └── Code-focused model
├── Project Directory
│   └── Local AI Dev Environment
└── Target Project Directory
```

### Recommended Hardware

**Minimum**:
- 8 GB RAM
- 4-core CPU
- 10 GB storage
- No GPU required (CPU inference)

**Recommended**:
- 16-32 GB RAM
- 8-core CPU
- 50 GB storage (for models)
- NVIDIA GPU with 8+ GB VRAM

### Model Selection

| Model Size | RAM Needed | Speed | Quality | Use Case |
|------------|------------|-------|---------|----------|
| 7B params  | 8 GB       | Fast  | Good    | Quick iterations |
| 13B params | 16 GB      | Medium| Better  | Balanced (recommended) |
| 34B params | 32+ GB     | Slow  | Best    | Complex tasks |

## Future Architecture Considerations

### Potential Enhancements

1. **Multi-Agent Coordination**:
   - Specialized agents (frontend, backend, testing)
   - Agent collaboration on complex tasks

2. **Persistent Memory**:
   - Long-term learning from project history
   - Cross-project knowledge transfer

3. **Distributed Execution**:
   - Multiple LLM backends in parallel
   - Load balancing across models

4. **Advanced Context Management**:
   - Semantic code search
   - Intelligent context pruning
   - Dynamic context reconstruction

5. **Real-Time Collaboration**:
   - Watch file system for changes
   - Respond to developer modifications
   - Suggest improvements in real-time

6. **Plugin System**:
   - Community-contributed tools
   - Language-specific plugins
   - Framework-specific plugins
