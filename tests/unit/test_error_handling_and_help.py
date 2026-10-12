"""
Test Error Handling and User Feedback Features (Task 12)

Tests for Requirements 10.1-10.7, 4.9, 10.5
"""

import pytest
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import json

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class TestCrashLogger:
    """Test crash logging functionality (Requirement 10.6)"""
    
    def test_crash_logger_initialization(self, tmp_path):
        """Crash logger should initialize with log directory"""
        from src.gui.crash_logger import CrashLogger
        
        crash_logger = CrashLogger(log_dir=tmp_path)
        
        assert crash_logger.log_dir == tmp_path
        assert tmp_path.exists()
        assert crash_logger.crash_log_path.exists() or crash_logger.crash_log_path.parent.exists()
    
    def test_crash_logger_logs_exception(self, tmp_path):
        """Crash logger should log unhandled exceptions"""
        from src.gui.crash_logger import CrashLogger
        
        crash_logger = CrashLogger(log_dir=tmp_path)
        
        try:
            raise ValueError("Test crash")
        except Exception:
            exc_info = sys.exc_info()
            crash_logger.log_crash(*exc_info)
        
        # Check that crash log was created
        crash_files = list(tmp_path.glob('crash_*.log'))
        assert len(crash_files) > 0
        
        # Verify content
        crash_content = crash_files[0].read_text()
        assert "CRASH REPORT" in crash_content
        assert "ValueError" in crash_content
        assert "Test crash" in crash_content
        assert "Traceback:" in crash_content
    
    def test_crash_logger_install(self, tmp_path):
        """Crash logger should install as global exception hook"""
        from src.gui.crash_logger import install_crash_logger
        
        original_excepthook = sys.excepthook
        
        crash_logger = install_crash_logger(log_dir=tmp_path)
        
        assert sys.excepthook != original_excepthook
        assert crash_logger is not None
        
        # Restore original
        sys.excepthook = original_excepthook
    
    def test_get_recent_crashes(self, tmp_path):
        """Should retrieve recent crash logs"""
        from src.gui.crash_logger import CrashLogger
        
        crash_logger = CrashLogger(log_dir=tmp_path)
        
        # Create mock crash files
        for i in range(5):
            crash_file = tmp_path / f"crash_202401{i:02d}_120000.log"
            crash_file.write_text(f"Crash {i}")
        
        recent = crash_logger.get_recent_crashes(limit=3)
        assert len(recent) == 3
    
    def test_clear_old_crashes(self, tmp_path):
        """Should remove old crash logs"""
        from src.gui.crash_logger import CrashLogger
        import time
        
        crash_logger = CrashLogger(log_dir=tmp_path)
        
        # Create old crash file
        old_crash = tmp_path / "crash_20200101_000000.log"
        old_crash.write_text("Old crash")
        
        # Make it old
        old_time = time.time() - (40 * 24 * 60 * 60)  # 40 days ago
        os.utime(old_crash, (old_time, old_time))
        
        crash_logger.clear_old_crashes(keep_days=30)
        
        assert not old_crash.exists()


class TestOpenExternal:
    """Test open_external Eel function (Requirement 10.5)"""
    
    @patch('webbrowser.open')
    def test_open_external_url(self, mock_webbrowser):
        """Should open URLs in browser"""
        # Mock Eel environment
        import eel
        from src.gui import gui_app
        
        result = gui_app.open_external("https://github.com")
        
        assert result['success'] == True
        mock_webbrowser.assert_called_once_with("https://github.com")
    
    @patch('os.startfile')
    def test_open_external_local_file_windows(self, mock_startfile):
        """Should open local files on Windows"""
        from src.gui import gui_app
        import tempfile
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("test")
            temp_path = f.name
        
        try:
            with patch('platform.system', return_value='Windows'):
                result = gui_app.open_external(temp_path)
                
                if os.path.exists(temp_path):
                    assert result['success'] == True
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)


class TestErrorHandling:
    """Test error handling in GUI backend (Requirements 10.1-10.4)"""
    
    def test_task_error_user_friendly_message(self):
        """Errors should be converted to user-friendly messages (Req 10.1, 11.7)"""
        from src.gui import gui_app
        
        # Test network error suggestion
        suggestion = gui_app._get_error_suggestion("Connection refused")
        assert "LLM server" in suggestion or "endpoint" in suggestion
        
        # Test API key error suggestion
        suggestion = gui_app._get_error_suggestion("API key invalid")
        assert "API key" in suggestion
        
        # Test permission error suggestion
        suggestion = gui_app._get_error_suggestion("Permission denied")
        assert "permission" in suggestion.lower()
    
    def test_error_categories(self):
        """Error handler should categorize errors correctly"""
        # This would test the JavaScript error_handler.js
        # For Python, we test that errors are properly caught and handled
        from src.gui.gui_app import run_task
        
        with patch('src.gui.gui_app.task_manager') as mock_manager:
            mock_manager.run_task.side_effect = Exception("Test error")
            
            result = run_task("test task")
            
            assert result['success'] == False
            assert 'error' in result


class TestHelpSystem:
    """Test help and documentation features (Requirements 4.9, 10.5, 10.7)"""
    
    def test_help_system_initialization(self):
        """Help system should initialize without errors"""
        # Test that help_system.js is properly structured
        help_js_path = Path(__file__).parent.parent.parent / 'src' / 'web' / 'js' / 'help_system.js'
        assert help_js_path.exists()
        
        content = help_js_path.read_text()
        assert 'showHelpMenu' in content
        assert 'showAboutDialog' in content
        assert 'showBugReportDialog' in content
        assert 'showUserGuide' in content
    
    def test_error_handler_initialization(self):
        """Error handler should initialize without errors"""
        error_js_path = Path(__file__).parent.parent.parent / 'src' / 'web' / 'js' / 'error_handler.js'
        assert error_js_path.exists()
        
        content = error_js_path.read_text()
        assert 'handleNetworkError' in content
        assert 'handleLLMApiError' in content
        assert 'handleFileOperationError' in content
        assert 'ErrorCategory' in content


@pytest.mark.integration
class TestErrorHandlingIntegration:
    """Integration tests for error handling"""
    
    def test_html_includes_error_handler(self):
        """HTML should include error_handler.js (Req 12.1)"""
        html_path = Path(__file__).parent.parent.parent / 'src' / 'web' / 'index.html'
        html_content = html_path.read_text(encoding='utf-8')
        
        assert 'error_handler.js' in html_content
        assert 'help_system.js' in html_content
        assert 'dialog.css' in html_content
    
    def test_dialog_css_exists(self):
        """Dialog CSS should exist for error dialogs"""
        dialog_css_path = Path(__file__).parent.parent.parent / 'src' / 'web' / 'css' / 'components' / 'dialog.css'
        assert dialog_css_path.exists()
        
        content = dialog_css_path.read_text()
        assert '.dialog-overlay' in content
        assert '.error-message' in content


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

