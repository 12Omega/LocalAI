"""
Tests for Task Input Panel HTML Structure (Task 5.2)

Validates that the Task Input Panel contains all required elements:
- Multi-line textarea with 5000 character limit
- Character counter display
- Run and Stop buttons
- Status indicator element
"""

import os
import re
from pathlib import Path


def test_task_input_panel_structure():
    """Test that Task Input Panel HTML has all required elements"""
    
    # Read the HTML file
    html_path = Path(__file__).parent.parent / "src" / "web" / "index.html"
    assert html_path.exists(), f"HTML file not found at {html_path}"
    
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Requirement 2.1: Multi-line textarea with 5000 character limit
    assert 'id="task-description"' in html_content, "Task description textarea not found"
    assert 'maxlength="5000"' in html_content, "Textarea does not have 5000 character limit"
    assert '<textarea' in html_content, "Textarea element not found"
    
    # Requirement 2.2: Character counter display
    assert 'id="char-count"' in html_content, "Character counter span not found"
    assert '/ 5000' in html_content, "Character limit display not found"
    assert 'character-counter' in html_content, "Character counter container not found"
    
    # Requirement 2.3: Run button
    assert 'id="run-task-btn"' in html_content, "Run task button not found"
    assert 'Run Task' in html_content, "Run button text not found"
    
    # Requirement 2.4 & 2.8: Stop button
    assert 'id="stop-task-btn"' in html_content, "Stop task button not found"
    assert 'Stop Task' in html_content, "Stop button text not found"
    
    # Requirement 2.4: Status indicator
    assert 'id="task-status"' in html_content, "Task status indicator not found"
    assert 'aria-live="polite"' in html_content, "Status indicator missing aria-live attribute"
    
    print("✓ All Task Input Panel HTML elements verified successfully")


def test_task_input_panel_accessibility():
    """Test that Task Input Panel has proper accessibility attributes"""
    
    html_path = Path(__file__).parent.parent / "src" / "web" / "index.html"
    
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Check aria-label attributes
    assert 'aria-label="Task description"' in html_content, "Textarea missing aria-label"
    assert 'aria-label="Run task"' in html_content, "Run button missing aria-label"
    assert 'aria-label="Stop task"' in html_content, "Stop button missing aria-label"
    
    # Check aria-describedby for character counter
    assert 'aria-describedby="char-count"' in html_content, "Textarea missing aria-describedby"
    
    # Check aria-live for status updates
    assert 'aria-live="polite"' in html_content, "Status indicator missing aria-live"
    assert 'aria-atomic="true"' in html_content, "Status indicator missing aria-atomic"
    
    print("✓ Task Input Panel accessibility attributes verified successfully")


def test_task_input_panel_structure_layout():
    """Test that Task Input Panel has proper semantic structure"""
    
    html_path = Path(__file__).parent.parent / "src" / "web" / "index.html"
    
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Check panel structure
    assert 'class="task-input-panel panel"' in html_content, "Task input panel container not found"
    assert 'class="panel-header"' in html_content, "Panel header not found"
    assert 'class="panel-content"' in html_content, "Panel content not found"
    assert 'class="task-actions"' in html_content, "Task actions container not found"
    
    # Check that elements are in correct order within the HTML
    textarea_pos = html_content.find('id="task-description"')
    run_btn_pos = html_content.find('id="run-task-btn"')
    stop_btn_pos = html_content.find('id="stop-task-btn"')
    status_pos = html_content.find('id="task-status"')
    
    assert textarea_pos > 0, "Textarea not found in HTML"
    assert run_btn_pos > textarea_pos, "Run button should come after textarea"
    assert stop_btn_pos > run_btn_pos, "Stop button should come after run button"
    assert status_pos > stop_btn_pos, "Status indicator should come after stop button"
    
    print("✓ Task Input Panel structure and layout verified successfully")


if __name__ == "__main__":
    test_task_input_panel_structure()
    test_task_input_panel_accessibility()
    test_task_input_panel_structure_layout()
    print("\n✅ All Task Input Panel HTML tests passed!")
