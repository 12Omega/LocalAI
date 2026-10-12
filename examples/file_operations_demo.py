"""Demonstration of FileOperations class capabilities.

This script demonstrates the usage of the FileOperations class for creating,
reading, updating, deleting, and moving files with error handling.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.file_operations import FileOperations


def main():
    """Run FileOperations demonstrations."""
    
    # Initialize FileOperations with current directory
    file_ops = FileOperations()
    
    print("=== FileOperations Demonstration ===\n")
    
    # 1. Create a file
    print("1. Creating a new file...")
    result = file_ops.create_file("demo_file.txt", "Hello, World!\nThis is a demo file.")
    print(f"   Result: {result.message}\n")
    
    # 2. Read the file
    print("2. Reading the file...")
    content, result = file_ops.read_file("demo_file.txt")
    if result.success:
        print(f"   Content: {content}")
        print(f"   Result: {result.message}\n")
    
    # 3. Update the file
    print("3. Updating the file...")
    result = file_ops.update_file("demo_file.txt", "Updated content!\nThe file has been modified.")
    print(f"   Result: {result.message}\n")
    
    # 4. Read updated content
    print("4. Reading updated content...")
    content, result = file_ops.read_file("demo_file.txt")
    if result.success:
        print(f"   Content: {content}")
        print(f"   Result: {result.message}\n")
    
    # 5. Move the file
    print("5. Moving the file...")
    result = file_ops.move_file("demo_file.txt", "moved_demo.txt")
    print(f"   Result: {result.message}\n")
    
    # 6. Delete the file
    print("6. Deleting the file...")
    result = file_ops.delete_file("moved_demo.txt")
    print(f"   Result: {result.message}\n")
    
    # 7. Demonstrate error handling - try to read non-existent file
    print("7. Error handling - reading non-existent file...")
    content, result = file_ops.read_file("nonexistent.txt")
    print(f"   Result: {result.message}")
    print(f"   Error Type: {result.error_type}\n")
    
    print("=== Demo Complete ===")


if __name__ == "__main__":
    main()
