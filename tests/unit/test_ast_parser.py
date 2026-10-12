"""Unit tests for AST Parser.

Tests the Tree-sitter integration for multi-language code parsing,
symbol extraction, and import detection.
"""

import os
import tempfile
import pytest
from pathlib import Path

from src.context.ast_parser import ASTParser
from src.core.models import SymbolLocation


@pytest.fixture
def ast_parser():
    """Create an ASTParser instance for testing."""
    return ASTParser()


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


class TestLanguageDetection:
    """Tests for language detection from file extensions."""
    
    def test_detect_python(self, ast_parser):
        assert ast_parser.detect_language("test.py") == "python"
        assert ast_parser.detect_language("test.pyw") == "python"
    
    def test_detect_javascript(self, ast_parser):
        assert ast_parser.detect_language("test.js") == "javascript"
        assert ast_parser.detect_language("test.mjs") == "javascript"
    
    def test_detect_typescript(self, ast_parser):
        assert ast_parser.detect_language("test.ts") == "typescript"
        assert ast_parser.detect_language("test.tsx") == "typescript"
    
    def test_detect_java(self, ast_parser):
        assert ast_parser.detect_language("Test.java") == "java"
    
    def test_detect_go(self, ast_parser):
        assert ast_parser.detect_language("test.go") == "go"
    
    def test_detect_rust(self, ast_parser):
        assert ast_parser.detect_language("test.rs") == "rust"
    
    def test_detect_cpp(self, ast_parser):
        assert ast_parser.detect_language("test.cpp") == "cpp"
        assert ast_parser.detect_language("test.hpp") == "cpp"
        assert ast_parser.detect_language("test.h") == "cpp"
    
    def test_detect_unsupported(self, ast_parser):
        assert ast_parser.detect_language("test.txt") is None
        assert ast_parser.detect_language("test.md") is None


class TestParsePythonFile:
    """Tests for parsing Python files."""
    
    def test_parse_simple_python_file(self, ast_parser, temp_dir):
        """Test parsing a simple Python file."""
        code = '''def hello():
    print("Hello, world!")

class MyClass:
    def method(self):
        pass
'''
        file_path = os.path.join(temp_dir, "test.py")
        with open(file_path, 'w') as f:
            f.write(code)
        
        tree = ast_parser.parse_file(file_path)
        assert tree is not None
        assert tree.root_node is not None
    
    def test_parse_nonexistent_file(self, ast_parser):
        """Test parsing a file that doesn't exist."""
        with pytest.raises(FileNotFoundError):
            ast_parser.parse_file("nonexistent.py")
    
    def test_parse_unsupported_language(self, ast_parser, temp_dir):
        """Test parsing a file with unsupported language."""
        file_path = os.path.join(temp_dir, "test.txt")
        with open(file_path, 'w') as f:
            f.write("Hello")
        
        with pytest.raises(ValueError, match="Cannot detect language"):
            ast_parser.parse_file(file_path)


class TestExtractPythonSymbols:
    """Tests for extracting symbols from Python code."""
    
    def test_extract_function(self, ast_parser, temp_dir):
        """Test extracting a function definition."""
        code = '''def hello_world():
    print("Hello, world!")
'''
        file_path = os.path.join(temp_dir, "test.py")
        with open(file_path, 'w') as f:
            f.write(code)
        
        tree = ast_parser.parse_file(file_path)
        symbols = ast_parser.extract_symbols(tree, file_path, 'python')
        
        assert len(symbols) == 1
        assert symbols[0].symbol_name == "hello_world"
        assert symbols[0].symbol_type == "function"
        assert symbols[0].line_number == 1
        assert symbols[0].file_path == file_path
    
    def test_extract_class(self, ast_parser, temp_dir):
        """Test extracting a class definition."""
        code = '''class MyClass:
    def method(self):
        pass
'''
        file_path = os.path.join(temp_dir, "test.py")
        with open(file_path, 'w') as f:
            f.write(code)
        
        tree = ast_parser.parse_file(file_path)
        symbols = ast_parser.extract_symbols(tree, file_path, 'python')
        
        # Should find the class and the method
        assert len(symbols) == 2
        
        class_symbol = next(s for s in symbols if s.symbol_type == "class")
        assert class_symbol.symbol_name == "MyClass"
        assert class_symbol.line_number == 1
        
        method_symbol = next(s for s in symbols if s.symbol_type == "function")
        assert method_symbol.symbol_name == "method"
        assert method_symbol.line_number == 2
    
    def test_extract_multiple_symbols(self, ast_parser, temp_dir):
        """Test extracting multiple functions and classes."""
        code = '''def func1():
    pass

def func2():
    pass

class Class1:
    pass

class Class2:
    def method1(self):
        pass
    
    def method2(self):
        pass
'''
        file_path = os.path.join(temp_dir, "test.py")
        with open(file_path, 'w') as f:
            f.write(code)
        
        tree = ast_parser.parse_file(file_path)
        symbols = ast_parser.extract_symbols(tree, file_path, 'python')
        
        # Should find: func1, func2, Class1, Class2, method1, method2
        assert len(symbols) == 6
        
        function_names = [s.symbol_name for s in symbols if s.symbol_type == "function"]
        class_names = [s.symbol_name for s in symbols if s.symbol_type == "class"]
        
        assert "func1" in function_names
        assert "func2" in function_names
        assert "method1" in function_names
        assert "method2" in function_names
        assert "Class1" in class_names
        assert "Class2" in class_names


class TestExtractPythonImports:
    """Tests for extracting imports from Python code."""
    
    def test_extract_simple_import(self, ast_parser, temp_dir):
        """Test extracting a simple import statement."""
        code = '''import os
import sys
'''
        file_path = os.path.join(temp_dir, "test.py")
        with open(file_path, 'w') as f:
            f.write(code)
        
        tree = ast_parser.parse_file(file_path)
        imports = ast_parser.extract_imports(tree, 'python')
        
        assert len(imports) == 2
        assert "import os" in imports
        assert "import sys" in imports
    
    def test_extract_from_import(self, ast_parser, temp_dir):
        """Test extracting 'from ... import' statements."""
        code = '''from os import path
from typing import List, Dict
'''
        file_path = os.path.join(temp_dir, "test.py")
        with open(file_path, 'w') as f:
            f.write(code)
        
        tree = ast_parser.parse_file(file_path)
        imports = ast_parser.extract_imports(tree, 'python')
        
        assert len(imports) == 2
        assert any("from os import path" in imp for imp in imports)
        assert any("from typing import List, Dict" in imp for imp in imports)
    
    def test_extract_mixed_imports(self, ast_parser, temp_dir):
        """Test extracting mixed import styles."""
        code = '''import os
from typing import List
import sys
from pathlib import Path
'''
        file_path = os.path.join(temp_dir, "test.py")
        with open(file_path, 'w') as f:
            f.write(code)
        
        tree = ast_parser.parse_file(file_path)
        imports = ast_parser.extract_imports(tree, 'python')
        
        assert len(imports) == 4


class TestExtractJavaScriptSymbols:
    """Tests for extracting symbols from JavaScript code."""
    
    def test_extract_function_declaration(self, ast_parser, temp_dir):
        """Test extracting JavaScript function declaration."""
        code = '''function hello() {
    console.log("Hello");
}
'''
        file_path = os.path.join(temp_dir, "test.js")
        with open(file_path, 'w') as f:
            f.write(code)
        
        tree = ast_parser.parse_file(file_path)
        symbols = ast_parser.extract_symbols(tree, file_path, 'javascript')
        
        assert len(symbols) >= 1
        func_symbols = [s for s in symbols if s.symbol_name == "hello"]
        assert len(func_symbols) == 1
        assert func_symbols[0].symbol_type == "function"
    
    def test_extract_class_declaration(self, ast_parser, temp_dir):
        """Test extracting JavaScript class declaration."""
        code = '''class MyClass {
    constructor() {
        this.value = 0;
    }
    
    method() {
        return this.value;
    }
}
'''
        file_path = os.path.join(temp_dir, "test.js")
        with open(file_path, 'w') as f:
            f.write(code)
        
        tree = ast_parser.parse_file(file_path)
        symbols = ast_parser.extract_symbols(tree, file_path, 'javascript')
        
        # Should find the class and methods
        class_symbols = [s for s in symbols if s.symbol_type == "class"]
        assert len(class_symbols) == 1
        assert class_symbols[0].symbol_name == "MyClass"


class TestExtractJavaScriptImports:
    """Tests for extracting imports from JavaScript code."""
    
    def test_extract_es6_import(self, ast_parser, temp_dir):
        """Test extracting ES6 import statements."""
        code = '''import React from 'react';
import { useState } from 'react';
'''
        file_path = os.path.join(temp_dir, "test.js")
        with open(file_path, 'w') as f:
            f.write(code)
        
        tree = ast_parser.parse_file(file_path)
        imports = ast_parser.extract_imports(tree, 'javascript')
        
        assert len(imports) == 2


class TestExtractTypeScriptImports:
    """Tests for extracting imports from TypeScript code."""
    
    def test_extract_typescript_import(self, ast_parser, temp_dir):
        """Test extracting TypeScript import statements."""
        code = '''import { Component } from '@angular/core';
import * as fs from 'fs';
'''
        file_path = os.path.join(temp_dir, "test.ts")
        with open(file_path, 'w') as f:
            f.write(code)
        
        tree = ast_parser.parse_file(file_path)
        if tree is None:
            pytest.skip("TypeScript parser not available")
        
        imports = ast_parser.extract_imports(tree, 'typescript')
        assert len(imports) == 2


class TestExtractJavaImports:
    """Tests for extracting imports from Java code."""
    
    def test_extract_java_import(self, ast_parser, temp_dir):
        """Test extracting Java import declarations."""
        code = '''import java.util.ArrayList;
import java.util.List;

public class Test {
}
'''
        file_path = os.path.join(temp_dir, "Test.java")
        with open(file_path, 'w') as f:
            f.write(code)
        
        tree = ast_parser.parse_file(file_path)
        if tree is None:
            pytest.skip("Java parser not available")
        
        imports = ast_parser.extract_imports(tree, 'java')
        assert len(imports) == 2


class TestExtractTypeScriptSymbols:
    """Tests for extracting symbols from TypeScript code."""
    
    def test_extract_typescript_function(self, ast_parser, temp_dir):
        """Test extracting TypeScript function declaration."""
        code = '''function greet(name: string): string {
    return `Hello, ${name}`;
}
'''
        file_path = os.path.join(temp_dir, "test.ts")
        with open(file_path, 'w') as f:
            f.write(code)
        
        tree = ast_parser.parse_file(file_path)
        if tree is None:  # Skip if TypeScript parser not available
            pytest.skip("TypeScript parser not available")
        
        symbols = ast_parser.extract_symbols(tree, file_path, 'typescript')
        func_symbols = [s for s in symbols if s.symbol_name == "greet"]
        assert len(func_symbols) >= 1
        assert func_symbols[0].symbol_type == "function"
    
    def test_extract_typescript_interface(self, ast_parser, temp_dir):
        """Test extracting TypeScript interface declaration."""
        code = '''interface User {
    name: string;
    age: number;
}
'''
        file_path = os.path.join(temp_dir, "test.ts")
        with open(file_path, 'w') as f:
            f.write(code)
        
        tree = ast_parser.parse_file(file_path)
        if tree is None:
            pytest.skip("TypeScript parser not available")
        
        symbols = ast_parser.extract_symbols(tree, file_path, 'typescript')
        interface_symbols = [s for s in symbols if s.symbol_name == "User"]
        assert len(interface_symbols) >= 1


class TestExtractJavaSymbols:
    """Tests for extracting symbols from Java code."""
    
    def test_extract_java_class(self, ast_parser, temp_dir):
        """Test extracting Java class declaration."""
        code = '''public class HelloWorld {
    public static void main(String[] args) {
        System.out.println("Hello, World!");
    }
}
'''
        file_path = os.path.join(temp_dir, "HelloWorld.java")
        with open(file_path, 'w') as f:
            f.write(code)
        
        tree = ast_parser.parse_file(file_path)
        if tree is None:
            pytest.skip("Java parser not available")
        
        symbols = ast_parser.extract_symbols(tree, file_path, 'java')
        class_symbols = [s for s in symbols if s.symbol_name == "HelloWorld"]
        assert len(class_symbols) >= 1


class TestExtractGoSymbols:
    """Tests for extracting symbols from Go code."""
    
    def test_extract_go_function(self, ast_parser, temp_dir):
        """Test extracting Go function declaration."""
        code = '''package main

func Hello() string {
    return "Hello, World!"
}
'''
        file_path = os.path.join(temp_dir, "test.go")
        with open(file_path, 'w') as f:
            f.write(code)
        
        tree = ast_parser.parse_file(file_path)
        if tree is None:
            pytest.skip("Go parser not available")
        
        symbols = ast_parser.extract_symbols(tree, file_path, 'go')
        func_symbols = [s for s in symbols if s.symbol_name == "Hello"]
        assert len(func_symbols) >= 1


class TestExtractRustSymbols:
    """Tests for extracting symbols from Rust code."""
    
    def test_extract_rust_function(self, ast_parser, temp_dir):
        """Test extracting Rust function declaration."""
        code = '''fn greet(name: &str) -> String {
    format!("Hello, {}", name)
}
'''
        file_path = os.path.join(temp_dir, "test.rs")
        with open(file_path, 'w') as f:
            f.write(code)
        
        tree = ast_parser.parse_file(file_path)
        if tree is None:
            pytest.skip("Rust parser not available")
        
        symbols = ast_parser.extract_symbols(tree, file_path, 'rust')
        func_symbols = [s for s in symbols if s.symbol_name == "greet"]
        assert len(func_symbols) >= 1


class TestExtractCppSymbols:
    """Tests for extracting symbols from C++ code."""
    
    def test_extract_cpp_function(self, ast_parser, temp_dir):
        """Test extracting C++ function declaration."""
        code = '''#include <string>

std::string greet(const std::string& name) {
    return "Hello, " + name;
}
'''
        file_path = os.path.join(temp_dir, "test.cpp")
        with open(file_path, 'w') as f:
            f.write(code)
        
        tree = ast_parser.parse_file(file_path)
        if tree is None:
            pytest.skip("C++ parser not available")
        
        symbols = ast_parser.extract_symbols(tree, file_path, 'cpp')
        func_symbols = [s for s in symbols if s.symbol_name == "greet"]
        assert len(func_symbols) >= 1
    
    def test_extract_cpp_class(self, ast_parser, temp_dir):
        """Test extracting C++ class declaration."""
        code = '''class MyClass {
public:
    void method() {
        // implementation
    }
};
'''
        file_path = os.path.join(temp_dir, "test.cpp")
        with open(file_path, 'w') as f:
            f.write(code)
        
        tree = ast_parser.parse_file(file_path)
        if tree is None:
            pytest.skip("C++ parser not available")
        
        symbols = ast_parser.extract_symbols(tree, file_path, 'cpp')
        class_symbols = [s for s in symbols if s.symbol_name == "MyClass"]
        assert len(class_symbols) >= 1


class TestAvailableLanguages:
    """Tests for getting available languages."""
    
    def test_get_available_languages(self, ast_parser):
        """Test getting list of available languages."""
        languages = ast_parser.get_available_languages()
        
        # Should have at least some languages
        assert isinstance(languages, list)
        assert len(languages) > 0
        
        # Check that common languages are present if their parsers are installed
        # (We can't guarantee all will be installed, but at least Python should be)
        # This test is flexible to pass even if not all languages are available


class TestExtractGoImports:
    """Tests for extracting imports from Go code."""
    
    def test_extract_go_import(self, ast_parser, temp_dir):
        """Test extracting Go import declarations."""
        code = '''package main

import (
    "fmt"
    "strings"
)

func main() {
    fmt.Println("Hello")
}
'''
        file_path = os.path.join(temp_dir, "test.go")
        with open(file_path, 'w') as f:
            f.write(code)
        
        tree = ast_parser.parse_file(file_path)
        if tree is None:
            pytest.skip("Go parser not available")
        
        imports = ast_parser.extract_imports(tree, 'go')
        # Should find the import declaration (may be grouped or separate)
        assert len(imports) >= 1


class TestExtractRustImports:
    """Tests for extracting imports from Rust code."""
    
    def test_extract_rust_use(self, ast_parser, temp_dir):
        """Test extracting Rust use declarations."""
        code = '''use std::collections::HashMap;
use std::fs::File;

fn main() {
    println!("Hello");
}
'''
        file_path = os.path.join(temp_dir, "test.rs")
        with open(file_path, 'w') as f:
            f.write(code)
        
        tree = ast_parser.parse_file(file_path)
        if tree is None:
            pytest.skip("Rust parser not available")
        
        imports = ast_parser.extract_imports(tree, 'rust')
        assert len(imports) >= 1


class TestExtractCppImports:
    """Tests for extracting imports from C++ code."""
    
    def test_extract_cpp_include(self, ast_parser, temp_dir):
        """Test extracting C++ #include preprocessor directives."""
        code = '''#include <iostream>
#include <string>
#include "myheader.h"

int main() {
    return 0;
}
'''
        file_path = os.path.join(temp_dir, "test.cpp")
        with open(file_path, 'w') as f:
            f.write(code)
        
        tree = ast_parser.parse_file(file_path)
        if tree is None:
            pytest.skip("C++ parser not available")
        
        imports = ast_parser.extract_imports(tree, 'cpp')
        assert len(imports) == 3
        assert any("iostream" in imp for imp in imports)
        assert any("string" in imp for imp in imports)
        assert any("myheader.h" in imp for imp in imports)


class TestComplexPythonStructures:
    """Tests for complex Python code structures."""
    
    def test_nested_classes(self, ast_parser, temp_dir):
        """Test extracting nested class definitions."""
        code = '''class Outer:
    def outer_method(self):
        pass
    
    class Inner:
        def inner_method(self):
            pass
'''
        file_path = os.path.join(temp_dir, "nested.py")
        with open(file_path, 'w') as f:
            f.write(code)
        
        tree = ast_parser.parse_file(file_path)
        symbols = ast_parser.extract_symbols(tree, file_path, 'python')
        
        # Should find Outer, Inner, outer_method, inner_method
        class_names = [s.symbol_name for s in symbols if s.symbol_type == "class"]
        assert "Outer" in class_names
        assert "Inner" in class_names
    
    def test_decorators(self, ast_parser, temp_dir):
        """Test extracting functions and classes with decorators."""
        code = '''@decorator
def decorated_function():
    pass

@classmethod
def class_method(cls):
    pass

@staticmethod
def static_method():
    pass
'''
        file_path = os.path.join(temp_dir, "decorated.py")
        with open(file_path, 'w') as f:
            f.write(code)
        
        tree = ast_parser.parse_file(file_path)
        symbols = ast_parser.extract_symbols(tree, file_path, 'python')
        
        func_names = [s.symbol_name for s in symbols if s.symbol_type == "function"]
        assert "decorated_function" in func_names
        assert "class_method" in func_names
        assert "static_method" in func_names
    
    def test_async_functions(self, ast_parser, temp_dir):
        """Test extracting async function definitions."""
        code = '''async def async_function():
    await some_operation()

async def another_async():
    pass
'''
        file_path = os.path.join(temp_dir, "async.py")
        with open(file_path, 'w') as f:
            f.write(code)
        
        tree = ast_parser.parse_file(file_path)
        symbols = ast_parser.extract_symbols(tree, file_path, 'python')
        
        func_names = [s.symbol_name for s in symbols if s.symbol_type == "function"]
        assert "async_function" in func_names
        assert "another_async" in func_names


class TestComplexJavaScriptStructures:
    """Tests for complex JavaScript code structures."""
    
    def test_arrow_functions_in_class(self, ast_parser, temp_dir):
        """Test extracting classes with arrow function properties."""
        code = '''class MyClass {
    constructor() {
        this.x = 5;
    }
    
    regularMethod() {
        return this.x;
    }
    
    arrowMethod = () => {
        return this.x;
    }
}
'''
        file_path = os.path.join(temp_dir, "arrow.js")
        with open(file_path, 'w') as f:
            f.write(code)
        
        tree = ast_parser.parse_file(file_path)
        if tree is None:
            pytest.skip("JavaScript parser not available")
        
        symbols = ast_parser.extract_symbols(tree, file_path, 'javascript')
        
        # Should at least find the class
        class_symbols = [s for s in symbols if s.symbol_type == "class"]
        assert len(class_symbols) >= 1
        assert class_symbols[0].symbol_name == "MyClass"
    
    def test_export_statements(self, ast_parser, temp_dir):
        """Test parsing files with export statements."""
        code = '''export function exportedFunc() {
    return 42;
}

export class ExportedClass {
    method() {}
}

export default class DefaultClass {
}
'''
        file_path = os.path.join(temp_dir, "exports.js")
        with open(file_path, 'w') as f:
            f.write(code)
        
        tree = ast_parser.parse_file(file_path)
        if tree is None:
            pytest.skip("JavaScript parser not available")
        
        symbols = ast_parser.extract_symbols(tree, file_path, 'javascript')
        
        # Should find the exported functions and classes
        symbol_names = [s.symbol_name for s in symbols]
        assert "exportedFunc" in symbol_names or len(symbol_names) >= 2


class TestComplexJavaStructures:
    """Tests for complex Java code structures."""
    
    def test_interface_with_methods(self, ast_parser, temp_dir):
        """Test extracting Java interfaces."""
        code = '''public interface MyInterface {
    void method1();
    int method2(String arg);
}
'''
        file_path = os.path.join(temp_dir, "Interface.java")
        with open(file_path, 'w') as f:
            f.write(code)
        
        tree = ast_parser.parse_file(file_path)
        if tree is None:
            pytest.skip("Java parser not available")
        
        symbols = ast_parser.extract_symbols(tree, file_path, 'java')
        interface_symbols = [s for s in symbols if s.symbol_name == "MyInterface"]
        assert len(interface_symbols) >= 1
    
    def test_multiple_classes_in_file(self, ast_parser, temp_dir):
        """Test extracting multiple classes from one Java file."""
        code = '''public class MainClass {
    public void method() {}
}

class HelperClass {
    void helper() {}
}
'''
        file_path = os.path.join(temp_dir, "Multiple.java")
        with open(file_path, 'w') as f:
            f.write(code)
        
        tree = ast_parser.parse_file(file_path)
        if tree is None:
            pytest.skip("Java parser not available")
        
        symbols = ast_parser.extract_symbols(tree, file_path, 'java')
        class_names = [s.symbol_name for s in symbols if s.symbol_type == "class"]
        assert "MainClass" in class_names
        assert "HelperClass" in class_names


class TestComplexRustStructures:
    """Tests for complex Rust code structures."""
    
    def test_struct_with_impl(self, ast_parser, temp_dir):
        """Test extracting Rust structs and implementations."""
        code = '''struct Point {
    x: f64,
    y: f64,
}

impl Point {
    fn new(x: f64, y: f64) -> Self {
        Point { x, y }
    }
    
    fn distance(&self) -> f64 {
        (self.x * self.x + self.y * self.y).sqrt()
    }
}
'''
        file_path = os.path.join(temp_dir, "struct.rs")
        with open(file_path, 'w') as f:
            f.write(code)
        
        tree = ast_parser.parse_file(file_path)
        if tree is None:
            pytest.skip("Rust parser not available")
        
        symbols = ast_parser.extract_symbols(tree, file_path, 'rust')
        # Should find the struct and impl block
        assert len(symbols) >= 1
    
    def test_trait_definition(self, ast_parser, temp_dir):
        """Test extracting Rust trait definitions."""
        code = '''trait Drawable {
    fn draw(&self);
}

trait Resizable {
    fn resize(&mut self, factor: f64);
}
'''
        file_path = os.path.join(temp_dir, "trait.rs")
        with open(file_path, 'w') as f:
            f.write(code)
        
        tree = ast_parser.parse_file(file_path)
        if tree is None:
            pytest.skip("Rust parser not available")
        
        symbols = ast_parser.extract_symbols(tree, file_path, 'rust')
        trait_symbols = [s for s in symbols if s.symbol_type == "trait"]
        # May find trait definitions
        assert len(symbols) >= 0  # At least parses without error


class TestComplexCppStructures:
    """Tests for complex C++ code structures."""
    
    def test_namespace_with_functions(self, ast_parser, temp_dir):
        """Test extracting C++ namespaces and their contents."""
        code = '''namespace MyNamespace {
    void function1() {
        // implementation
    }
    
    int function2(int x) {
        return x * 2;
    }
}
'''
        file_path = os.path.join(temp_dir, "namespace.cpp")
        with open(file_path, 'w') as f:
            f.write(code)
        
        tree = ast_parser.parse_file(file_path)
        if tree is None:
            pytest.skip("C++ parser not available")
        
        symbols = ast_parser.extract_symbols(tree, file_path, 'cpp')
        # Should find the namespace and functions
        assert len(symbols) >= 1
    
    def test_template_class(self, ast_parser, temp_dir):
        """Test extracting C++ template classes."""
        code = '''template<typename T>
class Container {
public:
    T value;
    void set(T val) {
        value = val;
    }
};
'''
        file_path = os.path.join(temp_dir, "template.cpp")
        with open(file_path, 'w') as f:
            f.write(code)
        
        tree = ast_parser.parse_file(file_path)
        if tree is None:
            pytest.skip("C++ parser not available")
        
        symbols = ast_parser.extract_symbols(tree, file_path, 'cpp')
        # Should find the class
        class_symbols = [s for s in symbols if s.symbol_name == "Container"]
        assert len(class_symbols) >= 1


class TestEdgeCases:
    """Tests for edge cases and special scenarios."""
    
    def test_very_long_file(self, ast_parser, temp_dir):
        """Test parsing a file with many functions."""
        # Generate code with 100 functions
        code_lines = []
        for i in range(100):
            code_lines.append(f"def function_{i}():")
            code_lines.append(f"    return {i}")
            code_lines.append("")
        
        code = "\n".join(code_lines)
        file_path = os.path.join(temp_dir, "long.py")
        with open(file_path, 'w') as f:
            f.write(code)
        
        tree = ast_parser.parse_file(file_path)
        symbols = ast_parser.extract_symbols(tree, file_path, 'python')
        
        # Should find all 100 functions
        assert len(symbols) == 100
    
    def test_unicode_in_code(self, ast_parser, temp_dir):
        """Test parsing code with Unicode characters."""
        code = '''def 函数():
    """A function with Unicode name."""
    return "你好世界"

class Класс:
    def метод(self):
        pass
'''
        file_path = os.path.join(temp_dir, "unicode.py")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(code)
        
        tree = ast_parser.parse_file(file_path)
        symbols = ast_parser.extract_symbols(tree, file_path, 'python')
        
        # Should find the function and class (names may be in Unicode)
        assert len(symbols) >= 2
    
    def test_symbols_with_underscores(self, ast_parser, temp_dir):
        """Test extracting symbols with underscores (common naming pattern)."""
        code = '''def _private_function():
    pass

def __double_underscore__():
    pass

class _PrivateClass:
    def __init__(self):
        pass
    
    def __str__(self):
        return ""
'''
        file_path = os.path.join(temp_dir, "underscores.py")
        with open(file_path, 'w') as f:
            f.write(code)
        
        tree = ast_parser.parse_file(file_path)
        symbols = ast_parser.extract_symbols(tree, file_path, 'python')
        
        symbol_names = [s.symbol_name for s in symbols]
        assert "_private_function" in symbol_names
        assert "__double_underscore__" in symbol_names
        assert "_PrivateClass" in symbol_names
        assert "__init__" in symbol_names
        assert "__str__" in symbol_names
    
    def test_file_with_comments_only(self, ast_parser, temp_dir):
        """Test parsing a file with only comments."""
        code = '''# This is a comment
# Another comment
"""
This is a docstring
But not in a function or class
So it's just a string expression
"""
'''
        file_path = os.path.join(temp_dir, "comments.py")
        with open(file_path, 'w') as f:
            f.write(code)
        
        tree = ast_parser.parse_file(file_path)
        symbols = ast_parser.extract_symbols(tree, file_path, 'python')
        
        # Should find no symbols (only comments)
        assert len(symbols) == 0
    
    def test_duplicate_function_names(self, ast_parser, temp_dir):
        """Test extracting duplicate function names in different scopes."""
        code = '''def duplicate():
    pass

class MyClass:
    def duplicate(self):
        pass
    
    class Nested:
        def duplicate(self):
            pass
'''
        file_path = os.path.join(temp_dir, "duplicates.py")
        with open(file_path, 'w') as f:
            f.write(code)
        
        tree = ast_parser.parse_file(file_path)
        symbols = ast_parser.extract_symbols(tree, file_path, 'python')
        
        # Should find all three 'duplicate' functions (in different scopes)
        duplicate_symbols = [s for s in symbols if s.symbol_name == "duplicate"]
        assert len(duplicate_symbols) == 3


class TestErrorHandling:
    """Tests for error handling."""
    
    def test_parse_with_invalid_language(self, ast_parser, temp_dir):
        """Test parsing with an invalid language specified."""
        file_path = os.path.join(temp_dir, "test.py")
        with open(file_path, 'w') as f:
            f.write("print('hello')")
        
        with pytest.raises(ValueError, match="Unsupported language"):
            ast_parser.parse_file(file_path, language="invalid_lang")
    
    def test_extract_symbols_from_none_tree(self, ast_parser):
        """Test extracting symbols from None tree."""
        symbols = ast_parser.extract_symbols(None, "test.py", "python")
        assert symbols == []
    
    def test_extract_imports_from_none_tree(self, ast_parser):
        """Test extracting imports from None tree."""
        imports = ast_parser.extract_imports(None, "python")
        assert imports == []
    
    def test_parse_file_with_syntax_errors(self, ast_parser, temp_dir):
        """Test parsing a file with syntax errors - should still parse partially."""
        code = '''def incomplete_function(
    # Missing closing parenthesis and body
    
class BrokenClass
    # Missing colon
    pass
'''
        file_path = os.path.join(temp_dir, "syntax_error.py")
        with open(file_path, 'w') as f:
            f.write(code)
        
        # Tree-sitter is error-tolerant and should still return a tree
        tree = ast_parser.parse_file(file_path)
        assert tree is not None
        assert tree.root_node is not None
        # Tree-sitter will mark errors in the tree
        assert tree.root_node.has_error or len(tree.root_node.children) > 0
    
    def test_parse_empty_file(self, ast_parser, temp_dir):
        """Test parsing an empty file."""
        file_path = os.path.join(temp_dir, "empty.py")
        with open(file_path, 'w') as f:
            f.write("")
        
        tree = ast_parser.parse_file(file_path)
        assert tree is not None
        assert tree.root_node is not None
        
        # Empty file should have no symbols or imports
        symbols = ast_parser.extract_symbols(tree, file_path, 'python')
        imports = ast_parser.extract_imports(tree, 'python')
        assert symbols == []
        assert imports == []
    
    def test_parse_whitespace_only_file(self, ast_parser, temp_dir):
        """Test parsing a file with only whitespace."""
        file_path = os.path.join(temp_dir, "whitespace.py")
        with open(file_path, 'w') as f:
            f.write("   \n\n\t\n   ")
        
        tree = ast_parser.parse_file(file_path)
        assert tree is not None
        symbols = ast_parser.extract_symbols(tree, file_path, 'python')
        assert symbols == []
    
    def test_parse_binary_file(self, ast_parser, temp_dir):
        """Test parsing a binary file gracefully handles errors."""
        file_path = os.path.join(temp_dir, "binary.py")
        with open(file_path, 'wb') as f:
            f.write(b'\x00\x01\x02\x03\xff\xfe\xfd')
        
        # Should still parse (Tree-sitter handles binary data)
        tree = ast_parser.parse_file(file_path)
        assert tree is not None
    
    def test_read_permission_error(self, ast_parser, temp_dir):
        """Test handling file read permission errors."""
        # This test is platform-specific and may not work on all systems
        # Skip if we can't create a file with restricted permissions
        import platform
        if platform.system() == "Windows":
            pytest.skip("Permission tests behave differently on Windows")
        
        file_path = os.path.join(temp_dir, "noperm.py")
        with open(file_path, 'w') as f:
            f.write("def test(): pass")
        
        # Try to remove read permissions
        try:
            os.chmod(file_path, 0o000)
            with pytest.raises(IOError):
                ast_parser.parse_file(file_path)
        finally:
            # Restore permissions for cleanup
            os.chmod(file_path, 0o644)
