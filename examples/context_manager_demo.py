"""Demo script for ContextManager capabilities.

This script demonstrates all the key features of the ContextManager:
- scan_project: Build project understanding
- detect_language_stack: Identify languages and frameworks
- analyze_code: Extract symbols and structure
- get_relevant_files: Find files for specific tasks
- get_dependencies: Build dependency graphs
- Caching: Efficient re-analysis
"""

import os
from src.context.context_manager import ContextManager
from src.core.models import SystemConfig, LLMConfig


def main():
    """Run ContextManager demonstration."""
    
    # Setup configuration
    llm_config = LLMConfig(
        endpoint="http://localhost:11434",
        model_name="codellama:13b"
    )
    
    config = SystemConfig(
        llm=llm_config,
        project_root=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        log_level="info"
    )
    
    # Create ContextManager
    cm = ContextManager(config)
    
    print("=" * 60)
    print("ContextManager Demo")
    print("=" * 60)
    
    # 1. Scan project
    print("\n1. Scanning project...")
    context = cm.scan_project(config.project_root)
    print(f"   Root: {context.root_path}")
    print(f"   Files found: {len(context.file_tree.files)}")
    print(f"   Directories: {len(context.file_tree.directories)}")
    
    # 2. Detect language stack
    print("\n2. Language Stack:")
    print(f"   Languages: {', '.join(context.language_stack.languages)}")
    print(f"   Primary: {context.language_stack.primary_language}")
    print(f"   Frameworks: {', '.join(context.language_stack.frameworks) if context.language_stack.frameworks else 'None detected'}")
    print(f"   Build tools: {', '.join(context.language_stack.build_tools)}")
    
    # 3. Analyze specific file
    print("\n3. Analyzing a code file...")
    test_file = os.path.join(config.project_root, "src", "context", "context_manager.py")
    if os.path.exists(test_file):
        analysis = cm.analyze_code(test_file)
        if analysis:
            print(f"   File: context_manager.py")
            print(f"   Language: {analysis.language}")
            print(f"   Imports: {len(analysis.imports)}")
            print(f"   Symbols: {len(analysis.symbols)}")
            print(f"   First 3 symbols:")
            for symbol in analysis.symbols[:3]:
                print(f"      - {symbol.symbol_type}: {symbol.symbol_name} (line {symbol.line_number})")
    
    # 4. Get relevant files for a task
    print("\n4. Finding relevant files for task:")
    task = "update the context manager implementation"
    relevant = cm.get_relevant_files(task)
    print(f"   Task: '{task}'")
    print(f"   Relevant files found: {len(relevant)}")
    for file in relevant[:3]:
        print(f"      - {os.path.basename(file)}")
    
    # 5. Get dependencies
    print("\n5. Dependency graph:")
    if os.path.exists(test_file):
        dep_graph = cm.get_dependencies(test_file)
        print(f"   File: context_manager.py")
        print(f"   Nodes in graph: {len(dep_graph.nodes)}")
        print(f"   Direct dependencies: {len(dep_graph.get_dependencies(test_file))}")
    
    # 6. Key files
    print("\n6. Key project files:")
    for key, path in context.key_files.items():
        print(f"   {key}: {path}")
    
    print("\n" + "=" * 60)
    print("Demo completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
