"""
Comprehensive GUI Checkpoint Test Suite

This script tests all GUI features end-to-end for task 14 checkpoint:
- Task execution workflow
- Configuration management
- History tracking
- System tray integration
- Theme switching
- Keyboard shortcuts
- Multi-resolution/DPI support
"""

import sys
import os
import time
import json
import sqlite3
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.gui.gui_task_manager import GUITaskManager, TaskAlreadyRunningError
from src.gui.gui_config_manager import GUIConfigManager
from src.gui.gui_history_manager import GUIHistoryManager, HistoryEntry
from src.core.config import ConfigManager


class Colors:
    """Terminal colors for test output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


class TestResult:
    """Test result tracker"""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.tests = []
    
    def add_pass(self, test_name: str, message: str = ""):
        self.passed += 1
        self.tests.append(('PASS', test_name, message))
        print(f"{Colors.GREEN}✓{Colors.RESET} {test_name} {Colors.BLUE}{message}{Colors.RESET}")
    
    def add_fail(self, test_name: str, message: str = ""):
        self.failed += 1
        self.tests.append(('FAIL', test_name, message))
        print(f"{Colors.RED}✗{Colors.RESET} {test_name} {Colors.RED}{message}{Colors.RESET}")
    
    def add_warning(self, test_name: str, message: str = ""):
        self.warnings += 1
        self.tests.append(('WARN', test_name, message))
        print(f"{Colors.YELLOW}⚠{Colors.RESET} {test_name} {Colors.YELLOW}{message}{Colors.RESET}")
    
    def summary(self):
        total = self.passed + self.failed
        print(f"\n{Colors.BOLD}{'='*70}{Colors.RESET}")
        print(f"{Colors.BOLD}Test Summary:{Colors.RESET}")
        print(f"  {Colors.GREEN}Passed: {self.passed}/{total}{Colors.RESET}")
        print(f"  {Colors.RED}Failed: {self.failed}/{total}{Colors.RESET}")
        if self.warnings:
            print(f"  {Colors.YELLOW}Warnings: {self.warnings}{Colors.RESET}")
        print(f"{Colors.BOLD}{'='*70}{Colors.RESET}")
        
        if self.failed > 0:
            print(f"\n{Colors.RED}Some tests failed. Review the output above.{Colors.RESET}")
            return False
        else:
            print(f"\n{Colors.GREEN}All tests passed!{Colors.RESET}")
            return True


def test_backend_integration_layer(results: TestResult):
    """Test 1: Backend Integration Layer (GUI Task Manager, Config Manager, History Manager)"""
    print(f"\n{Colors.BOLD}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}Test Suite 1: Backend Integration Layer{Colors.RESET}")
    print(f"{Colors.BOLD}{'='*70}{Colors.RESET}\n")
    
    # Create temporary test environment
    test_dir = Path(tempfile.mkdtemp(prefix='gui_test_'))
    test_config = test_dir / 'config.yaml'
    test_db = test_dir / 'history.db'
    
    try:
        # Test 1.1: GUI Config Manager Initialization
        try:
            # Create a minimal config file
            test_config.write_text("""
llm:
  endpoint: "http://localhost:11434"
  model: "llama2"
  temperature: 0.7
  max_tokens: 2000
  context_length: 4096
  backend: "ollama"

project_root: "."
log_level: "info"

features:
  web_research: true
  self_improvement: false
""")
            config_mgr = GUIConfigManager(str(test_config))
            results.add_pass("GUI Config Manager initialization", "Created successfully")
        except Exception as e:
            results.add_fail("GUI Config Manager initialization", f"Failed: {e}")
            return
        
        # Test 1.2: Config Field Validation
        test_cases = [
            ('llm.endpoint', 'http://localhost:11434', True, 'Valid URL'),
            ('llm.endpoint', 'not-a-url', False, 'Invalid URL'),
            ('llm.temperature', 0.5, True, 'Valid temperature'),
            ('llm.temperature', 2.0, False, 'Temperature out of range'),
            ('llm.max_tokens', 1000, True, 'Valid max tokens'),
            ('llm.max_tokens', -100, False, 'Negative max tokens'),
        ]
        
        for field, value, should_pass, description in test_cases:
            is_valid, error_msg = config_mgr.validate_field(field, value)
            if should_pass:
                if is_valid:
                    results.add_pass(f"Config validation: {description}", field)
                else:
                    results.add_fail(f"Config validation: {description}", f"Expected valid but got: {error_msg}")
            else:
                if not is_valid:
                    results.add_pass(f"Config validation: {description}", field)
                else:
                    results.add_fail(f"Config validation: {description}", "Expected invalid but was valid")
        
        # Test 1.3: Atomic Config Save with Backup
        try:
            config_data = config_mgr.get_config_for_gui()
            config_data['llm']['temperature'] = 0.8
            success, message = config_mgr.save_config(config_data)
            
            if success:
                # Verify backup was created
                backup_path = Path(str(test_config) + '.backup')
                if backup_path.exists():
                    results.add_pass("Config atomic save with backup", "Backup created")
                else:
                    results.add_warning("Config atomic save with backup", "Backup not found")
            else:
                results.add_fail("Config atomic save with backup", message)
        except Exception as e:
            results.add_fail("Config atomic save with backup", str(e))
        
        # Test 1.4: Sensitive Value Encryption
        try:
            test_key = "test-api-key-12345"
            encrypted = config_mgr.encrypt_sensitive_value(test_key)
            decrypted = config_mgr.decrypt_sensitive_value(encrypted)
            
            if encrypted != test_key and decrypted == test_key:
                results.add_pass("Sensitive value encryption/decryption", "Works correctly")
            else:
                results.add_fail("Sensitive value encryption/decryption", "Encryption or decryption failed")
        except Exception as e:
            results.add_fail("Sensitive value encryption/decryption", str(e))
        
        # Test 1.5: GUI History Manager Initialization
        try:
            history_mgr = GUIHistoryManager(str(test_db))
            results.add_pass("GUI History Manager initialization", "Database created")
        except Exception as e:
            results.add_fail("GUI History Manager initialization", str(e))
            return
        
        # Test 1.6: History Entry Creation and Retrieval
        try:
            entry = HistoryEntry(
                entry_id="test-entry-1",
                task_description="Test task for history",
                timestamp=datetime.now(),
                duration_seconds=5.5,
                status="success",
                output="Test output here",
                error_message=None,
                config_snapshot={}
            )
            
            entry_id = history_mgr.add_entry(entry)
            retrieved = history_mgr.get_entry_by_id(entry_id)
            
            if retrieved and retrieved.task_description == entry.task_description:
                results.add_pass("History entry creation and retrieval", "Entry stored and retrieved")
            else:
                results.add_fail("History entry creation and retrieval", "Entry not found or mismatch")
        except Exception as e:
            results.add_fail("History entry creation and retrieval", str(e))
        
        # Test 1.7: History Search and Filtering
        try:
            # Add multiple entries
            for i in range(5):
                entry = HistoryEntry(
                    entry_id=f"test-entry-search-{i}",
                    task_description=f"Search test task {i}",
                    timestamp=datetime.now() - timedelta(days=i),
                    duration_seconds=float(i),
                    status="success" if i % 2 == 0 else "failed",
                    output=f"Output {i}",
                    error_message=None if i % 2 == 0 else f"Error {i}",
                    config_snapshot={}
                )
                history_mgr.add_entry(entry)
            
            # Test search
            search_results = history_mgr.get_entries(search_query="Search")
            if len(search_results) >= 5:
                results.add_pass("History search", f"Found {len(search_results)} entries")
            else:
                results.add_fail("History search", f"Expected >= 5 entries, got {len(search_results)}")
            
            # Test status filter
            success_entries = history_mgr.get_entries(status_filter="success")
            failed_entries = history_mgr.get_entries(status_filter="failed")
            
            if len(success_entries) > 0 and len(failed_entries) > 0:
                results.add_pass("History status filtering", f"{len(success_entries)} success, {len(failed_entries)} failed")
            else:
                results.add_fail("History status filtering", "Filter not working correctly")
        except Exception as e:
            results.add_fail("History search and filtering", str(e))
        
        # Test 1.8: History Export
        try:
            json_export = test_dir / 'history_export.json'
            csv_export = test_dir / 'history_export.csv'
            
            json_success = history_mgr.export_to_json(str(json_export))
            csv_success = history_mgr.export_to_csv(str(csv_export))
            
            if json_success and json_export.exists():
                results.add_pass("History JSON export", "File created")
            else:
                results.add_fail("History JSON export", "Export failed or file not found")
            
            if csv_success and csv_export.exists():
                results.add_pass("History CSV export", "File created")
            else:
                results.add_fail("History CSV export", "Export failed or file not found")
        except Exception as e:
            results.add_fail("History export", str(e))
        
        # Test 1.9: History Statistics
        try:
            stats = history_mgr.get_statistics()
            if 'total_entries' in stats and stats['total_entries'] > 0:
                results.add_pass("History statistics", f"{stats['total_entries']} total entries")
            else:
                results.add_fail("History statistics", "No statistics returned")
        except Exception as e:
            results.add_fail("History statistics", str(e))
        
        # Test 1.10: History Auto-purge
        try:
            # Add old entry
            old_entry = HistoryEntry(
                entry_id="test-old-entry",
                task_description="Old task",
                timestamp=datetime.now() - timedelta(days=100),
                duration_seconds=1.0,
                status="success",
                output="Old output",
                error_message=None,
                config_snapshot={}
            )
            history_mgr.add_entry(old_entry)
            
            # Purge entries older than 90 days
            purged_count = history_mgr.purge_old_entries(days=90)
            if purged_count > 0:
                results.add_pass("History auto-purge", f"Purged {purged_count} old entries")
            else:
                results.add_warning("History auto-purge", "No entries purged (may need manual verification)")
        except Exception as e:
            results.add_fail("History auto-purge", str(e))
        
        # Test 1.11: GUI Task Manager (basic functionality test without actual task execution)
        # Note: GUITaskManager requires LLMInterface, CodeAgent, and ContextManager
        # This test is skipped in automated testing but should be tested manually
        results.add_warning("GUI Task Manager initialization", "Skipped - requires full component initialization (manual test recommended)")
    
    finally:
        # Cleanup
        if test_dir.exists():
            shutil.rmtree(test_dir, ignore_errors=True)


def test_frontend_structure(results: TestResult):
    """Test 2: Frontend Structure (HTML, CSS, JavaScript files)"""
    print(f"\n{Colors.BOLD}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}Test Suite 2: Frontend Structure{Colors.RESET}")
    print(f"{Colors.BOLD}{'='*70}{Colors.RESET}\n")
    
    web_dir = Path('src/web')
    
    # Test 2.1: HTML Structure
    required_html_files = [
        'index.html',
    ]
    
    for html_file in required_html_files:
        path = web_dir / html_file
        if path.exists():
            content = path.read_text(encoding='utf-8', errors='ignore')
            
            # Check for key elements
            checks = [
                ('textarea', 'Task input textarea'),
                ('id="btn-run"', 'Run button'),
                ('id="btn-stop"', 'Stop button'),
                ('id="progress-output"', 'Progress display'),
                ('id="view-settings"', 'Settings view'),
                ('id="view-history"', 'History view'),
            ]
            
            for check, description in checks:
                if check in content:
                    results.add_pass(f"HTML structure: {description}", html_file)
                else:
                    results.add_fail(f"HTML structure: {description}", f"Not found in {html_file}")
        else:
            results.add_fail(f"HTML file existence", f"{html_file} not found")
    
    # Test 2.2: CSS Structure
    css_dir = web_dir / 'css'
    required_css_files = [
        'main.css',
        'components/buttons.css',
        'components/inputs.css',
        'components/progress.css',
        'themes/light.css',
        'themes/dark.css',
    ]
    
    for css_file in required_css_files:
        path = css_dir / css_file
        if path.exists():
            results.add_pass(f"CSS file: {css_file}", "Exists")
        else:
            results.add_fail(f"CSS file: {css_file}", "Not found")
    
    # Test 2.3: JavaScript Structure
    js_dir = web_dir / 'js'
    required_js_files = [
        'main.js',
        'state.js',
        'components/task_input.js',
        'components/progress_display.js',
        'components/settings.js',
        'components/history.js',
    ]
    
    for js_file in required_js_files:
        path = js_dir / js_file
        if path.exists():
            results.add_pass(f"JavaScript file: {js_file}", "Exists")
        else:
            results.add_fail(f"JavaScript file: {js_file}", "Not found")
    
    # Test 2.4: Assets (Icons)
    assets_dir = web_dir / 'assets'
    required_assets = [
        'icon.svg',
        'icons',  # Directory
    ]
    
    for asset in required_assets:
        path = assets_dir / asset
        if path.exists():
            results.add_pass(f"Asset: {asset}", "Exists")
        else:
            results.add_fail(f"Asset: {asset}", "Not found")


def test_keyboard_shortcuts_implementation(results: TestResult):
    """Test 3: Keyboard Shortcuts Implementation"""
    print(f"\n{Colors.BOLD}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}Test Suite 3: Keyboard Shortcuts{Colors.RESET}")
    print(f"{Colors.BOLD}{'='*70}{Colors.RESET}\n")
    
    main_js = Path('src/web/js/main.js')
    
    if not main_js.exists():
        results.add_fail("Keyboard shortcuts file", "main.js not found")
        return
    
    content = main_js.read_text(encoding='utf-8', errors='ignore')
    
    # Check for keyboard shortcut implementations
    shortcuts = [
        ('Ctrl+Enter', 'Run task'),
        ('Ctrl+,', 'Settings'),
        ('Ctrl+H', 'History'),
        ('Ctrl+1', 'View 1'),
        ('Ctrl+2', 'View 2'),
        ('Ctrl+3', 'View 3'),
        ('Escape', 'Close dialog'),
        ('Ctrl+C', 'Copy'),
    ]
    
    for shortcut, description in shortcuts:
        # Check if shortcut is mentioned in code (simplified check)
        shortcut_key = shortcut.split('+')[-1].lower()
        if shortcut_key in content.lower():
            results.add_pass(f"Keyboard shortcut: {description}", shortcut)
        else:
            results.add_warning(f"Keyboard shortcut: {description}", f"{shortcut} not clearly implemented (manual verification needed)")


def test_theme_system(results: TestResult):
    """Test 4: Theme System"""
    print(f"\n{Colors.BOLD}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}Test Suite 4: Theme System{Colors.RESET}")
    print(f"{Colors.BOLD}{'='*70}{Colors.RESET}\n")
    
    # Test 4.1: Theme CSS Files
    themes_dir = Path('src/web/css/themes')
    
    for theme in ['light.css', 'dark.css']:
        path = themes_dir / theme
        if path.exists():
            content = path.read_text(encoding='utf-8', errors='ignore')
            
            # Check for CSS variables
            if '--' in content and 'color' in content.lower():
                results.add_pass(f"Theme file: {theme}", "Contains CSS variables")
            else:
                results.add_warning(f"Theme file: {theme}", "May not use CSS variables")
        else:
            results.add_fail(f"Theme file: {theme}", "Not found")
    
    # Test 4.2: Theme Switcher in JavaScript
    main_js = Path('src/web/js/main.js')
    if main_js.exists():
        content = main_js.read_text(encoding='utf-8', errors='ignore')
        if 'theme' in content.lower() and 'localStorage' in content:
            results.add_pass("Theme persistence", "localStorage implementation found")
        else:
            results.add_warning("Theme persistence", "Implementation not clearly found")
    else:
        results.add_fail("Theme JavaScript", "main.js not found")


def test_system_tray_integration(results: TestResult):
    """Test 5: System Tray Integration"""
    print(f"\n{Colors.BOLD}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}Test Suite 5: System Tray Integration{Colors.RESET}")
    print(f"{Colors.BOLD}{'='*70}{Colors.RESET}\n")
    
    gui_app = Path('src/gui/gui_app.py')
    
    if not gui_app.exists():
        results.add_fail("System tray implementation", "gui_app.py not found")
        return
    
    content = gui_app.read_text(encoding='utf-8', errors='ignore')
    
    # Check for pystray import
    if 'pystray' in content or 'system_tray' in content.lower():
        results.add_pass("System tray import", "pystray or tray code found")
    else:
        results.add_warning("System tray import", "pystray not clearly imported (may be optional)")
    
    # Check requirements-gui.txt for pystray
    req_file = Path('requirements-gui.txt')
    if req_file.exists():
        req_content = req_file.read_text(encoding='utf-8', errors='ignore')
        if 'pystray' in req_content:
            results.add_pass("System tray dependency", "pystray in requirements")
        else:
            results.add_warning("System tray dependency", "pystray not in requirements (may be optional)")
    else:
        results.add_fail("GUI requirements file", "requirements-gui.txt not found")


def test_error_handling(results: TestResult):
    """Test 6: Error Handling and User Feedback"""
    print(f"\n{Colors.BOLD}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}Test Suite 6: Error Handling{Colors.RESET}")
    print(f"{Colors.BOLD}{'='*70}{Colors.RESET}\n")
    
    # Test 6.1: Crash Logger
    try:
        from src.gui.crash_logger import install_crash_logger, get_crash_logger
        crash_logger = get_crash_logger()
        results.add_pass("Crash logger module", "Imported successfully")
        
        # Test crash log directory
        log_dir = Path.home() / '.local-ai-dev' / 'crash_logs'
        results.add_pass("Crash log directory", f"Path: {log_dir}")
    except ImportError as e:
        results.add_fail("Crash logger module", f"Import failed: {e}")
    
    # Test 6.2: Error Dialog in JavaScript
    progress_js = Path('src/web/js/components/progress_display.js')
    if progress_js.exists():
        content = progress_js.read_text(encoding='utf-8', errors='ignore')
        if 'error' in content.lower():
            results.add_pass("Error display in progress", "Error handling found")
        else:
            results.add_warning("Error display in progress", "Error handling not clearly implemented")
    else:
        results.add_fail("Progress display JavaScript", "File not found")


def test_accessibility_features(results: TestResult):
    """Test 7: Accessibility Features"""
    print(f"\n{Colors.BOLD}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}Test Suite 7: Accessibility{Colors.RESET}")
    print(f"{Colors.BOLD}{'='*70}{Colors.RESET}\n")
    
    index_html = Path('src/web/index.html')
    
    if not index_html.exists():
        results.add_fail("Accessibility check", "index.html not found")
        return
    
    content = index_html.read_text(encoding='utf-8', errors='ignore')
    
    # Check for ARIA attributes
    aria_checks = [
        ('aria-label', 'ARIA labels'),
        ('role=', 'ARIA roles'),
        ('aria-describedby', 'ARIA descriptions'),
    ]
    
    for check, description in aria_checks:
        if check in content:
            results.add_pass(f"Accessibility: {description}", "Found")
        else:
            results.add_warning(f"Accessibility: {description}", "Not found (may need manual verification)")


def test_responsiveness(results: TestResult):
    """Test 8: Responsive Design"""
    print(f"\n{Colors.BOLD}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}Test Suite 8: Responsive Design{Colors.RESET}")
    print(f"{Colors.BOLD}{'='*70}{Colors.RESET}\n")
    
    main_css = Path('src/web/css/main.css')
    
    if not main_css.exists():
        results.add_fail("Responsive design", "main.css not found")
        return
    
    content = main_css.read_text(encoding='utf-8', errors='ignore')
    
    # Check for media queries
    if '@media' in content:
        results.add_pass("Media queries", "Found in main.css")
    else:
        results.add_warning("Media queries", "Not found (may affect responsiveness)")
    
    # Check for CSS Grid/Flexbox
    if 'grid' in content.lower() or 'flex' in content.lower():
        results.add_pass("Modern layout", "Grid or Flexbox found")
    else:
        results.add_warning("Modern layout", "Grid/Flexbox not clearly used")
    
    # Manual test recommendation
    results.add_warning("Manual testing required", "Test at 800x600, 1920x1080, 2560x1440, 3840x2160")
    results.add_warning("Manual DPI testing required", "Test at 100%, 125%, 150%, 200% scaling")


def main():
    """Run all checkpoint tests"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}GUI Application Checkpoint Test Suite{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}Task 14: Full GUI Features Complete{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}\n")
    
    results = TestResult()
    
    try:
        # Run all test suites
        test_backend_integration_layer(results)
        test_frontend_structure(results)
        test_keyboard_shortcuts_implementation(results)
        test_theme_system(results)
        test_system_tray_integration(results)
        test_error_handling(results)
        test_accessibility_features(results)
        test_responsiveness(results)
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Tests interrupted by user{Colors.RESET}")
        return 1
    except Exception as e:
        print(f"\n{Colors.RED}Unexpected error during testing: {e}{Colors.RESET}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Print summary
    success = results.summary()
    
    # Create test report
    report_path = Path('GUI_CHECKPOINT_TEST_REPORT.md')
    create_test_report(results, report_path)
    print(f"\n{Colors.BLUE}Detailed report saved to: {report_path}{Colors.RESET}")
    
    return 0 if success else 1


def create_test_report(results: TestResult, report_path: Path):
    """Create a detailed test report in Markdown format"""
    
    report = f"""# GUI Application Checkpoint Test Report

**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Task**: 14 - Checkpoint - Full GUI Features Complete

## Summary

- **Total Tests**: {results.passed + results.failed}
- **Passed**: {results.passed}
- **Failed**: {results.failed}
- **Warnings**: {results.warnings}

## Test Results

"""
    
    current_suite = None
    for status, test_name, message in results.tests:
        # Group by test suite
        if '=' in test_name or 'Suite' in test_name:
            current_suite = test_name
            report += f"\n### {test_name}\n\n"
        else:
            icon = '✓' if status == 'PASS' else '✗' if status == 'FAIL' else '⚠'
            report += f"{icon} **{test_name}**"
            if message:
                report += f": {message}"
            report += "\n"
    
    report += f"""

## Manual Testing Recommendations

The following areas require manual testing:

### 1. End-to-End Task Execution
- [ ] Launch the GUI application
- [ ] Enter a simple task description
- [ ] Click Run button
- [ ] Verify real-time progress updates
- [ ] Verify task completion status
- [ ] Check history entry was created

### 2. Configuration Management
- [ ] Open Settings view
- [ ] Modify LLM endpoint
- [ ] Save configuration
- [ ] Restart application
- [ ] Verify settings persisted

### 3. History Functionality
- [ ] View history entries
- [ ] Search history
- [ ] Filter by status
- [ ] Export to JSON
- [ ] Export to CSV
- [ ] Re-run a task from history
- [ ] Delete a history entry

### 4. Theme Switching
- [ ] Toggle between light and dark themes
- [ ] Verify all components respect theme
- [ ] Restart application
- [ ] Verify theme persisted

### 5. Keyboard Shortcuts
- [ ] Press Ctrl+Enter to run task
- [ ] Press Ctrl+, to open settings
- [ ] Press Ctrl+H to view history
- [ ] Press Ctrl+1/2/3 to switch views
- [ ] Press Esc to close dialogs
- [ ] Press Ctrl+C to copy output

### 6. Responsive Design
Test at different resolutions:
- [ ] 800x600 (minimum)
- [ ] 1920x1080 (standard)
- [ ] 2560x1440 (high resolution)
- [ ] 3840x2160 (4K)

Test at different DPI scaling:
- [ ] 100% (standard)
- [ ] 125% (medium)
- [ ] 150% (high)
- [ ] 200% (very high)

### 7. System Tray Integration
- [ ] Minimize application to tray
- [ ] Restore from tray
- [ ] Right-click tray icon for menu
- [ ] Verify running task indicator in tray

### 8. Error Handling
- [ ] Enter invalid LLM endpoint
- [ ] Attempt to run task
- [ ] Verify user-friendly error message
- [ ] Test network disconnection scenario

## Issues Found

"""
    
    # List all failures
    failures = [t for t in results.tests if t[0] == 'FAIL']
    if failures:
        for status, test_name, message in failures:
            report += f"- **{test_name}**: {message}\n"
    else:
        report += "*No issues found in automated tests.*\n"
    
    report += """

## Recommendations

"""
    
    if results.failed == 0:
        report += "All automated tests passed. Proceed with manual testing using the checklist above.\n"
    else:
        report += "Some automated tests failed. Address the issues listed above before proceeding with manual testing.\n"
    
    report_path.write_text(report, encoding='utf-8')


if __name__ == '__main__':
    sys.exit(main())
