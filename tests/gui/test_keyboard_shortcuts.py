"""
Unit tests for keyboard shortcut handling

Tests verify that keyboard shortcuts are properly defined and functional.
This test file validates the JavaScript implementation indirectly by
checking the expected behavior patterns.
"""

import pytest


class TestKeyboardShortcuts:
    """Test keyboard shortcut definitions and behavior"""
    
    def test_keyboard_shortcuts_are_documented(self):
        """Verify that keyboard shortcuts are documented in main.js"""
        import os
        from pathlib import Path
        
        main_js_path = Path('src/web/js/main.js')
        assert main_js_path.exists(), "main.js file should exist"
        
        with open(main_js_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check that setupKeyboardShortcuts function exists
        assert 'function setupKeyboardShortcuts()' in content or \
               'const setupKeyboardShortcuts = ' in content, \
               "setupKeyboardShortcuts function should be defined"
        
        # Check that key shortcuts are registered
        shortcuts_to_check = [
            ('Ctrl+Enter', 'Enter'),  # Run task
            ('Ctrl+1', "'1'"),  # View switching
            ('Ctrl+2', "'2'"),
            ('Ctrl+3', "'3'"),
            ('Ctrl+H', "'h'"),  # History view (case insensitive)
            ('Ctrl+,', "','"),  # Settings
            ('Ctrl+C', "'c'"),  # Copy output (case insensitive)
            ('Esc', 'Escape'),  # Close dialog
        ]
        
        for shortcut_name, key_code in shortcuts_to_check:
            # Check if the key is referenced in the keyboard handler
            assert key_code in content or key_code.upper() in content or key_code.lower() in content, \
                f"Keyboard shortcut {shortcut_name} should be implemented (key: {key_code})"
    
    def test_platform_detection_for_modifiers(self):
        """Verify that both Ctrl and Cmd modifiers are checked"""
        from pathlib import Path
        
        main_js_path = Path('src/web/js/main.js')
        
        with open(main_js_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Should check both ctrlKey and metaKey for cross-platform support
        assert 'e.ctrlKey' in content, "Should check e.ctrlKey for Windows/Linux"
        assert 'e.metaKey' in content, "Should check e.metaKey for macOS"
        
        # Should use OR logic to support both platforms
        assert 'ctrlKey || e.metaKey' in content or \
               'metaKey || e.ctrlKey' in content, \
               "Should check both Ctrl and Cmd keys with OR logic"
    
    def test_input_field_detection(self):
        """Verify that shortcuts don't interfere with text input"""
        from pathlib import Path
        
        main_js_path = Path('src/web/js/main.js')
        
        with open(main_js_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Should check if target is an input field
        assert 'INPUT' in content or 'input' in content, \
               "Should check if target is an input element"
        assert 'TEXTAREA' in content or 'textarea' in content, \
               "Should check if target is a textarea element"
    
    def test_escape_key_handling(self):
        """Verify Escape key closes dialogs and stops tasks"""
        from pathlib import Path
        
        main_js_path = Path('src/web/js/main.js')
        
        with open(main_js_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Should handle Escape key
        assert 'Escape' in content, "Should handle Escape key"
        
        # Should close dialogs or stop task
        assert 'closeDialog' in content, "Should call closeDialog function"
    
    def test_keyboard_shortcuts_help_function(self):
        """Verify that help function for keyboard shortcuts exists"""
        from pathlib import Path
        
        main_js_path = Path('src/web/js/main.js')
        
        with open(main_js_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Should have a help function
        assert 'showKeyboardShortcutsHelp' in content, \
               "Should have showKeyboardShortcutsHelp function"
        
        # Help function should list shortcuts
        shortcuts_in_help = [
            'Ctrl/Cmd + Enter',
            'Ctrl/Cmd + 1',
            'Ctrl/Cmd + H',
            'Ctrl/Cmd + ,',
            'Ctrl/Cmd + C',
            'Esc'
        ]
        
        for shortcut in shortcuts_in_help:
            assert shortcut in content, \
                f"Shortcut {shortcut} should be documented in help"
    
    def test_all_required_shortcuts_implemented(self):
        """Verify all required shortcuts from task 10.1 are implemented"""
        from pathlib import Path
        
        main_js_path = Path('src/web/js/main.js')
        
        with open(main_js_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Required shortcuts from task 10.1:
        # 1. Ctrl+Enter / Cmd+Enter for run task
        assert 'Enter' in content and 'btn-run' in content, \
               "Ctrl+Enter should run task"
        
        # 2. Ctrl+, / Cmd+, for settings
        assert "','" in content and "settings" in content, \
               "Ctrl+, should open settings"
        
        # 3. Ctrl+H / Cmd+H for history view
        assert ("'h'" in content or "'H'" in content) and "history" in content, \
               "Ctrl+H should open history"
        
        # 4. Ctrl+1/2/3 for view switching
        assert "'1'" in content and "'2'" in content and "'3'" in content, \
               "Ctrl+1/2/3 should switch views"
        
        # 5. Esc for dialog close
        assert 'Escape' in content, \
               "Esc should close dialogs"
        
        # 6. Ctrl+C for copy output
        assert ("'c'" in content or "'C'" in content) and 'copy' in content, \
               "Ctrl+C should copy output"


class TestKeyboardShortcutIntegration:
    """Integration tests for keyboard shortcuts with UI components"""
    
    def test_run_button_exists(self):
        """Verify run button element exists in HTML"""
        from pathlib import Path
        
        html_path = Path('src/web/index.html')
        assert html_path.exists(), "index.html should exist"
        
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert 'id="btn-run"' in content or 'id="run-button"' in content, \
               "Run button should exist in HTML"
    
    def test_stop_button_exists(self):
        """Verify stop button element exists in HTML"""
        from pathlib import Path
        
        html_path = Path('src/web/index.html')
        
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert 'id="btn-stop"' in content or 'id="stop-button"' in content, \
               "Stop button should exist in HTML"
    
    def test_copy_output_button_exists(self):
        """Verify copy output button element exists in HTML"""
        from pathlib import Path
        
        html_path = Path('src/web/index.html')
        
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert 'copy-output' in content or 'btn-copy-output' in content, \
               "Copy output button should exist in HTML"
    
    def test_navigation_tabs_exist(self):
        """Verify navigation tabs exist for view switching"""
        from pathlib import Path
        
        html_path = Path('src/web/index.html')
        
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for task, history, and settings tabs
        assert 'data-view="task"' in content, "Task tab should exist"
        assert 'data-view="history"' in content, "History tab should exist"
        assert 'data-view="settings"' in content, "Settings tab should exist"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
