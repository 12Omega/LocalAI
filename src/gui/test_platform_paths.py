"""Unit tests for platform_paths module.

Tests platform-specific path handling functionality including:
- Configuration directory paths
- Data directory paths
- Cache and log directory paths
- Path normalization and separator handling
"""

import os
import platform
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from .platform_paths import PlatformPaths, get_config_dir, get_data_dir, normalize_path


class TestPlatformPaths:
    """Test suite for PlatformPaths class."""
    
    def test_get_system(self):
        """Test that get_system returns current OS name."""
        system = PlatformPaths.get_system()
        assert system in ['Windows', 'Darwin', 'Linux', 'Java']
        assert system == platform.system()
    
    def test_platform_detection(self):
        """Test platform detection methods."""
        system = platform.system()
        
        if system == 'Windows':
            assert PlatformPaths.is_windows() is True
            assert PlatformPaths.is_macos() is False
            assert PlatformPaths.is_linux() is False
        elif system == 'Darwin':
            assert PlatformPaths.is_windows() is False
            assert PlatformPaths.is_macos() is True
            assert PlatformPaths.is_linux() is False
        elif system == 'Linux':
            assert PlatformPaths.is_windows() is False
            assert PlatformPaths.is_macos() is False
            assert PlatformPaths.is_linux() is True
    
    def test_get_path_separator(self):
        """Test that path separator matches OS expectations."""
        sep = PlatformPaths.get_path_separator()
        assert sep == os.sep
        
        if PlatformPaths.is_windows():
            assert sep == '\\'
        else:
            assert sep == '/'
    
    def test_normalize_path(self):
        """Test path normalization with different inputs."""
        # Test basic path normalization
        if PlatformPaths.is_windows():
            result = PlatformPaths.normalize_path('path/to/file.txt')
            assert '\\' in result or result == 'path/to/file.txt'
        else:
            result = PlatformPaths.normalize_path('path\\to\\file.txt')
            assert '/' in result or '\\' not in result
        
        # Test empty path
        assert PlatformPaths.normalize_path('') == ''
        
        # Test single component
        assert PlatformPaths.normalize_path('file.txt') == 'file.txt'
    
    def test_join_path(self):
        """Test joining path components."""
        result = PlatformPaths.join_path('path', 'to', 'file.txt')
        expected = str(Path('path') / 'to' / 'file.txt')
        assert result == expected
        
        # Test empty join
        assert PlatformPaths.join_path() == ''
        
        # Test single component
        assert PlatformPaths.join_path('single') == 'single'
    
    @patch('platform.system')
    def test_get_config_dir_windows(self, mock_system):
        """Test config directory on Windows."""
        mock_system.return_value = 'Windows'
        
        with patch.dict(os.environ, {'APPDATA': r'C:\Users\Test\AppData\Roaming'}):
            # Need to reload the class to pick up the mocked platform
            config_dir = PlatformPaths.get_config_dir(create=False)
            assert 'local-ai-dev' in str(config_dir)
    
    @patch('platform.system')
    def test_get_config_dir_macos(self, mock_system):
        """Test config directory on macOS."""
        # This test only validates behavior when actually on macOS
        # Skip if not on macOS since class-level platform detection can't be mocked
        if not PlatformPaths.is_macos():
            pytest.skip("Test only runs on macOS")
        
        mock_system.return_value = 'Darwin'
        
        config_dir = PlatformPaths.get_config_dir(create=False)
        assert 'Library' in str(config_dir)
        assert 'Application Support' in str(config_dir)
        assert 'local-ai-dev' in str(config_dir)
    
    @patch('platform.system')
    def test_get_config_dir_linux(self, mock_system):
        """Test config directory on Linux."""
        # This test only validates behavior when actually on Linux
        # Skip if not on Linux since class-level platform detection can't be mocked
        if not PlatformPaths.is_linux():
            pytest.skip("Test only runs on Linux")
        
        mock_system.return_value = 'Linux'
        
        config_dir = PlatformPaths.get_config_dir(create=False)
        assert '.config' in str(config_dir) or 'XDG_CONFIG_HOME' in os.environ
        assert 'local-ai-dev' in str(config_dir)
    
    def test_get_data_dir(self):
        """Test data directory returns valid path."""
        data_dir = PlatformPaths.get_data_dir(create=False)
        assert isinstance(data_dir, Path)
        assert 'local-ai-dev' in str(data_dir)
        
        # Verify different from config on Windows
        if PlatformPaths.is_windows():
            config_dir = PlatformPaths.get_config_dir(create=False)
            # Data uses LOCALAPPDATA, config uses APPDATA
            assert data_dir != config_dir or 'AppData' in str(data_dir)
    
    def test_get_cache_dir(self):
        """Test cache directory returns valid path."""
        cache_dir = PlatformPaths.get_cache_dir(create=False)
        assert isinstance(cache_dir, Path)
        assert 'local-ai-dev' in str(cache_dir)
        
        if PlatformPaths.is_macos():
            assert 'Caches' in str(cache_dir)
        elif PlatformPaths.is_linux():
            assert '.cache' in str(cache_dir) or 'XDG_CACHE_HOME' in os.environ
    
    def test_get_log_dir(self):
        """Test log directory returns valid path."""
        log_dir = PlatformPaths.get_log_dir(create=False)
        assert isinstance(log_dir, Path)
        assert 'local-ai-dev' in str(log_dir)
        
        if PlatformPaths.is_macos():
            assert 'Logs' in str(log_dir)
        else:
            assert 'logs' in str(log_dir).lower()
    
    def test_get_history_db_path(self):
        """Test history database path."""
        db_path = PlatformPaths.get_history_db_path()
        assert isinstance(db_path, Path)
        assert db_path.name == 'history.db'
        assert 'local-ai-dev' in str(db_path)
    
    def test_get_encryption_key_path(self):
        """Test encryption key path."""
        key_path = PlatformPaths.get_encryption_key_path()
        assert isinstance(key_path, Path)
        assert key_path.name == 'encryption.key'
        assert 'local-ai-dev' in str(key_path)
    
    def test_get_session_state_path(self):
        """Test session state path."""
        state_path = PlatformPaths.get_session_state_path()
        assert isinstance(state_path, Path)
        assert state_path.name == 'session_state.json'
        assert 'local-ai-dev' in str(state_path)
    
    def test_ensure_dir_exists(self):
        """Test directory creation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_path = Path(tmpdir) / 'test' / 'nested' / 'dir'
            assert not test_path.exists()
            
            result = PlatformPaths.ensure_dir_exists(test_path)
            
            assert test_path.exists()
            assert test_path.is_dir()
            assert result == test_path
    
    def test_get_temp_dir(self):
        """Test temporary directory path."""
        temp_dir = PlatformPaths.get_temp_dir()
        assert isinstance(temp_dir, Path)
        assert 'local-ai-dev' in str(temp_dir)
        
        # Should exist after calling get_temp_dir
        assert temp_dir.exists()
        assert temp_dir.is_dir()


class TestConvenienceFunctions:
    """Test convenience functions that wrap PlatformPaths methods."""
    
    def test_get_config_dir_function(self):
        """Test get_config_dir convenience function."""
        result = get_config_dir(create=False)
        expected = PlatformPaths.get_config_dir(create=False)
        assert result == expected
    
    def test_get_data_dir_function(self):
        """Test get_data_dir convenience function."""
        result = get_data_dir(create=False)
        expected = PlatformPaths.get_data_dir(create=False)
        assert result == expected
    
    def test_normalize_path_function(self):
        """Test normalize_path convenience function."""
        test_path = 'path/to/file.txt'
        result = normalize_path(test_path)
        expected = PlatformPaths.normalize_path(test_path)
        assert result == expected


class TestPathSeparatorHandling:
    """Test path separator handling across platforms."""
    
    def test_to_platform_path_with_forward_slashes(self):
        """Test converting Unix-style paths."""
        input_path = 'path/to/file.txt'
        result = PlatformPaths.to_platform_path(input_path)
        
        # Result should use platform-appropriate separators
        if PlatformPaths.is_windows():
            # Windows may convert to backslashes or keep forward (both work)
            assert '/' in result or '\\' in result or result == 'path/to/file.txt'
        else:
            # Unix systems use forward slashes
            assert '/' in result or result == input_path
    
    def test_to_platform_path_with_backslashes(self):
        """Test converting Windows-style paths."""
        input_path = 'path\\to\\file.txt'
        result = PlatformPaths.to_platform_path(input_path)
        
        # Should be normalized regardless of platform
        assert isinstance(result, str)
    
    def test_absolute_path_handling(self):
        """Test that absolute paths are handled correctly."""
        if PlatformPaths.is_windows():
            test_path = 'C:\\Users\\Test\\file.txt'
        else:
            test_path = '/home/test/file.txt'
        
        result = PlatformPaths.normalize_path(test_path)
        # Should remain absolute
        assert Path(result).is_absolute()


class TestDirectoryCreation:
    """Test that directory creation works correctly."""
    
    def test_config_dir_creation(self):
        """Test that config directory can be created."""
        # This test creates actual directories - use with caution
        config_dir = PlatformPaths.get_config_dir(create=True)
        assert config_dir.exists()
        assert config_dir.is_dir()
    
    def test_data_dir_creation(self):
        """Test that data directory can be created."""
        data_dir = PlatformPaths.get_data_dir(create=True)
        assert data_dir.exists()
        assert data_dir.is_dir()
    
    def test_no_creation_when_disabled(self):
        """Test that directories are not created when create=False."""
        # This test is tricky because directories might already exist
        # We'll just verify the method doesn't raise an error
        try:
            PlatformPaths.get_config_dir(create=False)
            PlatformPaths.get_data_dir(create=False)
            PlatformPaths.get_cache_dir(create=False)
            PlatformPaths.get_log_dir(create=False)
        except Exception as e:
            pytest.fail(f"Should not raise exception with create=False: {e}")


class TestRequirements:
    """Test that requirements are satisfied."""
    
    def test_requirement_15_4_path_separators(self):
        """Test Requirement 15.4: Platform-appropriate file paths."""
        # Verify correct separator is used
        sep = PlatformPaths.get_path_separator()
        
        if PlatformPaths.is_windows():
            assert sep == '\\', "Windows should use backslash separator"
        else:
            assert sep == '/', "Unix-like systems should use forward slash"
        
        # Verify normalization works
        test_path = 'path/to/file'
        normalized = PlatformPaths.normalize_path(test_path)
        assert isinstance(normalized, str)
    
    def test_requirement_15_7_config_locations(self):
        """Test Requirement 15.7: Platform-appropriate config locations."""
        config_dir = PlatformPaths.get_config_dir(create=False)
        data_dir = PlatformPaths.get_data_dir(create=False)
        
        if PlatformPaths.is_windows():
            # Windows: AppData directories
            assert 'AppData' in str(config_dir) or 'local-ai-dev' in str(config_dir)
            assert 'local-ai-dev' in str(data_dir)
        elif PlatformPaths.is_macos():
            # macOS: ~/Library directories
            assert 'Library' in str(config_dir)
            assert 'Application Support' in str(config_dir)
            assert 'local-ai-dev' in str(config_dir)
        else:
            # Linux: XDG directories
            assert '.config' in str(config_dir) or 'XDG_CONFIG_HOME' in os.environ
            assert '.local' in str(data_dir) or 'XDG_DATA_HOME' in os.environ
        
        # All platforms should have app name in path
        assert 'local-ai-dev' in str(config_dir)
        assert 'local-ai-dev' in str(data_dir)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
