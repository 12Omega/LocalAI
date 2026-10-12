"""Integration tests for platform paths with GUI modules.

Verifies that gui_config_manager, gui_history_manager, and crash_logger
work correctly with the new platform_paths module.
"""

import tempfile
from pathlib import Path
import pytest

from .platform_paths import PlatformPaths
from .gui_config_manager import GUIConfigManager
from .gui_history_manager import GUIHistoryManager, HistoryEntry
from .crash_logger import CrashLogger
from datetime import datetime


class TestGUIConfigManagerIntegration:
    """Test gui_config_manager integration with platform_paths."""
    
    def test_encryption_key_uses_platform_path(self):
        """Test that encryption key is stored in platform-appropriate location."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / 'config.yaml'
            config_file.write_text('llm:\n  endpoint: http://localhost:11434\n')
            
            manager = GUIConfigManager(str(config_file))
            
            # Verify encryption key path is platform-appropriate
            key_path = PlatformPaths.get_encryption_key_path()
            assert key_path.exists()
            assert key_path.name == 'encryption.key'
            
            if PlatformPaths.is_windows():
                assert 'AppData' in str(key_path)
            elif PlatformPaths.is_macos():
                assert 'Library' in str(key_path)
            else:
                assert '.config' in str(key_path) or 'XDG_CONFIG_HOME' in str(key_path)


class TestGUIHistoryManagerIntegration:
    """Test gui_history_manager integration with platform_paths."""
    
    def test_default_db_path_is_platform_appropriate(self):
        """Test that default database path follows platform conventions."""
        manager = GUIHistoryManager()
        
        db_path = Path(manager.db_path)
        assert db_path.name == 'history.db'
        assert 'local-ai-dev' in str(db_path)
        
        if PlatformPaths.is_windows():
            assert 'AppData' in str(db_path)
        elif PlatformPaths.is_macos():
            assert 'Library' in str(db_path)
        else:
            assert '.local' in str(db_path) or 'XDG_DATA_HOME' in str(db_path)
    
    def test_custom_db_path_works(self):
        """Test that custom database path still works."""
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_db = str(Path(tmpdir) / 'custom.db')
            manager = GUIHistoryManager(db_path=custom_db)
            
            # Add an entry
            entry = HistoryEntry(
                entry_id='test-123',
                task_description='Test task',
                timestamp=datetime.now(),
                duration_seconds=1.5,
                status='success',
                output='Test output'
            )
            
            entry_id = manager.add_entry(entry)
            assert entry_id == 'test-123'
            
            # Retrieve entry
            retrieved = manager.get_entry_by_id('test-123')
            assert retrieved is not None
            assert retrieved.task_description == 'Test task'


class TestCrashLoggerIntegration:
    """Test crash_logger integration with platform_paths."""
    
    def test_default_log_dir_is_platform_appropriate(self):
        """Test that default log directory follows platform conventions."""
        logger = CrashLogger()
        
        log_dir = logger.log_dir
        assert 'local-ai-dev' in str(log_dir)
        
        if PlatformPaths.is_windows():
            assert 'AppData' in str(log_dir)
            assert 'logs' in str(log_dir).lower()
        elif PlatformPaths.is_macos():
            assert 'Library' in str(log_dir)
            assert 'Logs' in str(log_dir)
        else:
            assert '.local' in str(log_dir) or 'XDG_DATA_HOME' in str(log_dir)
            assert 'logs' in str(log_dir).lower()
    
    def test_custom_log_dir_works(self):
        """Test that custom log directory still works."""
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_log_dir = Path(tmpdir) / 'custom_logs'
            logger = CrashLogger(log_dir=custom_log_dir)
            
            assert logger.log_dir == custom_log_dir
            assert custom_log_dir.exists()
            assert (custom_log_dir / 'crash.log').exists()


class TestPathNormalization:
    """Test path normalization across modules."""
    
    def test_normalize_mixed_separators(self):
        """Test normalizing paths with mixed separators."""
        test_cases = [
            'path/to/file.txt',
            'path\\to\\file.txt',
            'path/to\\mixed/separators.txt',
        ]
        
        for test_path in test_cases:
            normalized = PlatformPaths.normalize_path(test_path)
            
            # Should be a valid string
            assert isinstance(normalized, str)
            
            # Should be convertible to Path
            path_obj = Path(normalized)
            assert path_obj.parts[-1] in ['file.txt', 'separators.txt']
    
    def test_join_path_compatibility(self):
        """Test that join_path produces compatible paths."""
        parts = ['root', 'middle', 'file.txt']
        joined = PlatformPaths.join_path(*parts)
        
        # Should be compatible with Path operations
        path_obj = Path(joined)
        assert 'file.txt' in str(path_obj)
        assert len(path_obj.parts) == 3


class TestRequirementsCompliance:
    """Test compliance with specific requirements."""
    
    def test_requirement_15_4_cross_platform_separators(self):
        """Requirement 15.4: Platform-appropriate file path separators."""
        sep = PlatformPaths.get_path_separator()
        
        # Verify correct separator for platform
        if PlatformPaths.is_windows():
            assert sep == '\\\\'
        else:
            assert sep == '/'
        
        # Verify normalization uses correct separator
        test_path = 'a/b/c'
        normalized = PlatformPaths.normalize_path(test_path)
        path_obj = Path(normalized)
        
        # Path object should handle it correctly
        assert path_obj.parts[-1] == 'c'
    
    def test_requirement_15_7_platform_directories(self):
        """Requirement 15.7: Platform-appropriate configuration directories."""
        config_dir = PlatformPaths.get_config_dir(create=False)
        data_dir = PlatformPaths.get_data_dir(create=False)
        cache_dir = PlatformPaths.get_cache_dir(create=False)
        log_dir = PlatformPaths.get_log_dir(create=False)
        
        # All should exist as Path objects
        assert isinstance(config_dir, Path)
        assert isinstance(data_dir, Path)
        assert isinstance(cache_dir, Path)
        assert isinstance(log_dir, Path)
        
        # All should contain app name
        for dir_path in [config_dir, data_dir, cache_dir, log_dir]:
            assert 'local-ai-dev' in str(dir_path)
        
        # Platform-specific checks
        if PlatformPaths.is_windows():
            # Windows: AppData directories
            assert 'AppData' in str(config_dir)
            assert 'AppData' in str(data_dir)
        elif PlatformPaths.is_macos():
            # macOS: Library directories
            assert 'Library' in str(config_dir)
            assert 'Application Support' in str(config_dir)
            assert 'Library' in str(cache_dir)
            assert 'Caches' in str(cache_dir)
            assert 'Library' in str(log_dir)
            assert 'Logs' in str(log_dir)
        else:
            # Linux: XDG directories
            config_str = str(config_dir)
            data_str = str(data_dir)
            cache_str = str(cache_dir)
            
            assert '.config' in config_str or 'XDG_CONFIG_HOME' in config_str
            assert '.local' in data_str or 'XDG_DATA_HOME' in data_str
            assert '.cache' in cache_str or 'XDG_CACHE_HOME' in cache_str


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
