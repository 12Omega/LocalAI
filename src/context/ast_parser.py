"""AST Parser for multi-language code analysis using Tree-sitter.

This module provides Tree-sitter integration for parsing source code across
multiple programming languages and extracting symbols (functions, classes, methods)
and imports/dependencies.

Supported Languages:
- Python
- JavaScript
- TypeScript
- Java
- Go
- Rust
- C++
"""

import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

try:
    import tree_sitter
    from tree_sitter import Language, Parser, Node, Tree
except ImportError:
    raise ImportError(
        "tree-sitter is not installed. Please install it with: pip install tree-sitter"
    )

from src.core.models import SymbolLocation


class ASTParser:
    """Multi-language AST parser using Tree-sitter."""
    
    # Language to file extension mapping
    LANGUAGE_EXTENSIONS = {
        'python': ['.py', '.pyw'],
        'javascript': ['.js', '.mjs', '.cjs'],
        'typescript': ['.ts', '.tsx'],
        'java': ['.java'],
        'go': ['.go'],
        'rust': ['.rs'],
        'cpp': ['.cpp', '.cc', '.cxx', '.hpp', '.h', '.hxx'],
    }
    
    # Extension to language mapping (reverse of above)
    EXTENSION_TO_LANGUAGE = {}
    for lang, exts in LANGUAGE_EXTENSIONS.items():
        for ext in exts:
            EXTENSION_TO_LANGUAGE[ext] = lang
    
    def __init__(self):
        """Initialize the AST parser with Tree-sitter language parsers."""
        self.parsers: Dict[str, Parser] = {}
        self.languages: Dict[str, Language] = {}
        self._initialize_parsers()
    
    def _initialize_parsers(self):
        """Initialize Tree-sitter parsers for all supported languages."""
        # Direct language function imports
        language_loaders = {
            'python': lambda: __import__('tree_sitter_python').language(),
            'javascript': lambda: __import__('tree_sitter_javascript').language(),
            'typescript': lambda: __import__('tree_sitter_typescript').language_typescript(),
            'java': lambda: __import__('tree_sitter_java').language(),
            'go': lambda: __import__('tree_sitter_go').language(),
            'rust': lambda: __import__('tree_sitter_rust').language(),
            'cpp': lambda: __import__('tree_sitter_cpp').language(),
        }
        
        for lang_name, loader in language_loaders.items():
            try:
                # Get the language capsule and wrap it in a Language object
                language_capsule = loader()
                language = Language(language_capsule)
                
                # Create parser with language
                parser = Parser(language)
                
                self.parsers[lang_name] = parser
                self.languages[lang_name] = language
                
            except (ImportError, AttributeError, Exception) as e:
                # Language not available - skip it
                # This allows partial functionality if not all languages are installed
                pass
    
    def detect_language(self, file_path: str) -> Optional[str]:
        """Detect programming language from file extension.
        
        Args:
            file_path: Path to the source code file
            
        Returns:
            Language name (e.g., 'python', 'javascript') or None if unsupported
        """
        ext = Path(file_path).suffix.lower()
        return self.EXTENSION_TO_LANGUAGE.get(ext)
    
    def parse_file(self, file_path: str, language: Optional[str] = None) -> Optional[Tree]:
        """Parse a source code file and return its AST.
        
        Args:
            file_path: Path to the source code file
            language: Programming language (auto-detected if not provided)
            
        Returns:
            Tree-sitter Tree object or None if parsing fails
            
        Raises:
            FileNotFoundError: If the file does not exist
            ValueError: If the language is unsupported
        """
        # Check if file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Detect language if not provided
        if language is None:
            language = self.detect_language(file_path)
            if language is None:
                raise ValueError(f"Cannot detect language for file: {file_path}")
        
        # Check if language is supported
        if language not in self.parsers:
            raise ValueError(
                f"Unsupported language: {language}. "
                f"Supported languages: {list(self.parsers.keys())}"
            )
        
        # Read file content
        try:
            with open(file_path, 'rb') as f:
                source_code = f.read()
        except Exception as e:
            raise IOError(f"Error reading file {file_path}: {e}")
        
        # Parse the source code
        parser = self.parsers[language]
        tree = parser.parse(source_code)
        
        return tree
    
    def extract_symbols(self, tree: Tree, file_path: str, language: str) -> List[SymbolLocation]:
        """Extract symbols (functions, classes, methods) from an AST.
        
        Args:
            tree: Tree-sitter Tree object
            file_path: Path to the source file (for the SymbolLocation)
            language: Programming language
            
        Returns:
            List of SymbolLocation objects representing all symbols found
        """
        if tree is None or tree.root_node is None:
            return []
        
        symbols = []
        
        # Language-specific node types for symbols
        symbol_node_types = {
            'python': ['function_definition', 'class_definition'],
            'javascript': ['function_declaration', 'class_declaration', 'method_definition'],
            'typescript': ['function_declaration', 'class_declaration', 'method_definition', 'interface_declaration'],
            'java': ['class_declaration', 'method_declaration', 'interface_declaration'],
            'go': ['function_declaration', 'method_declaration', 'type_declaration'],
            'rust': ['function_item', 'impl_item', 'struct_item', 'enum_item', 'trait_item'],
            'cpp': ['function_definition', 'class_specifier', 'struct_specifier', 'namespace_definition'],
        }
        
        target_types = symbol_node_types.get(language, [])
        if not target_types:
            return symbols
        
        # Traverse the AST and collect symbols
        self._traverse_and_extract(tree.root_node, file_path, language, target_types, symbols)
        
        return symbols
    
    def _traverse_and_extract(
        self, 
        node: Node, 
        file_path: str, 
        language: str,
        target_types: List[str], 
        symbols: List[SymbolLocation]
    ):
        """Recursively traverse AST nodes and extract symbols.
        
        Args:
            node: Current Tree-sitter Node
            file_path: Path to source file
            language: Programming language
            target_types: List of node types to extract
            symbols: List to append found symbols to
        """
        if node.type in target_types:
            symbol_name = self._extract_symbol_name(node, language)
            symbol_type = self._get_symbol_type(node.type, language)
            
            if symbol_name:
                symbols.append(SymbolLocation(
                    file_path=file_path,
                    line_number=node.start_point[0] + 1,  # Convert to 1-indexed
                    symbol_name=symbol_name,
                    symbol_type=symbol_type
                ))
        
        # Recursively traverse children
        for child in node.children:
            self._traverse_and_extract(child, file_path, language, target_types, symbols)
    
    def _extract_symbol_name(self, node: Node, language: str) -> Optional[str]:
        """Extract the name of a symbol from its AST node.
        
        Args:
            node: Tree-sitter Node representing a symbol
            language: Programming language
            
        Returns:
            Symbol name or None if not found
        """
        # Language-specific name extraction strategies
        if language in ['python', 'javascript']:
            # Look for 'name' or 'identifier' child
            for child in node.children:
                if child.type in ['identifier', 'name']:
                    return child.text.decode('utf8')
        
        elif language == 'typescript':
            # TypeScript uses 'identifier' and 'type_identifier' (for interfaces)
            for child in node.children:
                if child.type in ['identifier', 'name', 'type_identifier']:
                    return child.text.decode('utf8')
        
        elif language == 'java':
            # Java uses 'identifier' for names
            for child in node.children:
                if child.type == 'identifier':
                    return child.text.decode('utf8')
        
        elif language == 'go':
            # Go uses 'identifier' for names
            for child in node.children:
                if child.type == 'identifier':
                    return child.text.decode('utf8')
        
        elif language == 'rust':
            # Rust uses 'identifier' for names
            for child in node.children:
                if child.type == 'identifier':
                    return child.text.decode('utf8')
        
        elif language == 'cpp':
            # C++ uses various identifiers, may be nested
            # For functions, name is in function_declarator child
            # For classes, name is direct identifier child
            for child in node.children:
                if child.type in ['identifier', 'field_identifier', 'type_identifier']:
                    return child.text.decode('utf8')
                elif child.type == 'function_declarator':
                    # Function name is the first identifier in function_declarator
                    for subchild in child.children:
                        if subchild.type == 'identifier':
                            return subchild.text.decode('utf8')
                elif child.type == 'qualified_identifier':
                    # Recursively search qualified_identifier for the actual identifier
                    for subchild in child.children:
                        if subchild.type == 'identifier':
                            return subchild.text.decode('utf8')
        
        return None
    
    def _get_symbol_type(self, node_type: str, language: str) -> str:
        """Map Tree-sitter node type to symbol type.
        
        Args:
            node_type: Tree-sitter node type string
            language: Programming language
            
        Returns:
            Symbol type string ('function', 'class', 'method', etc.)
        """
        # Mapping of node types to symbol types
        type_mapping = {
            'function_definition': 'function',
            'function_declaration': 'function',
            'function_item': 'function',
            'class_definition': 'class',
            'class_declaration': 'class',
            'class_specifier': 'class',
            'method_definition': 'method',
            'method_declaration': 'method',
            'interface_declaration': 'interface',
            'impl_item': 'implementation',
            'struct_item': 'struct',
            'struct_specifier': 'struct',
            'enum_item': 'enum',
            'trait_item': 'trait',
            'type_declaration': 'type',
            'namespace_definition': 'namespace',
        }
        
        return type_mapping.get(node_type, 'unknown')
    
    def extract_imports(self, tree: Tree, language: str) -> List[str]:
        """Extract import/dependency statements from an AST.
        
        Args:
            tree: Tree-sitter Tree object
            language: Programming language
            
        Returns:
            List of import strings
        """
        if tree is None or tree.root_node is None:
            return []
        
        imports = []
        
        # Language-specific import node types
        import_node_types = {
            'python': ['import_statement', 'import_from_statement'],
            'javascript': ['import_statement'],
            'typescript': ['import_statement'],
            'java': ['import_declaration'],
            'go': ['import_declaration', 'import_spec'],
            'rust': ['use_declaration'],
            'cpp': ['preproc_include'],
        }
        
        target_types = import_node_types.get(language, [])
        if not target_types:
            return imports
        
        # Traverse and extract imports
        self._traverse_and_extract_imports(tree.root_node, language, target_types, imports)
        
        return imports
    
    def _traverse_and_extract_imports(
        self,
        node: Node,
        language: str,
        target_types: List[str],
        imports: List[str]
    ):
        """Recursively traverse AST nodes and extract imports.
        
        Args:
            node: Current Tree-sitter Node
            language: Programming language
            target_types: List of import node types
            imports: List to append found imports to
        """
        if node.type in target_types:
            import_text = self._extract_import_text(node, language)
            if import_text and import_text not in imports:
                imports.append(import_text)
        
        # Recursively traverse children
        for child in node.children:
            self._traverse_and_extract_imports(child, language, target_types, imports)
    
    def _extract_import_text(self, node: Node, language: str) -> Optional[str]:
        """Extract import statement text from an AST node.
        
        Args:
            node: Tree-sitter Node representing an import
            language: Programming language
            
        Returns:
            Import statement as string or None
        """
        # For most languages, we can use the node text directly
        # Strip whitespace and newlines for cleaner output
        import_text = node.text.decode('utf8').strip()
        return import_text if import_text else None
    
    def get_available_languages(self) -> List[str]:
        """Get list of languages that have successfully initialized parsers.
        
        Returns:
            List of language names
        """
        return list(self.parsers.keys())
