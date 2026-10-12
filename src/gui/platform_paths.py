"""Platform-specific file path handling utilities.

This module provides cross-platform path handling utilities for the Desktop GUI
Application, ensuring proper path separators and configuration directories are
used for each operating system.

Requirements:
- 15.4: Use platform-appropriate file paths (backslash on Windows, forward slash on Unix)
- 15.7: Store configuration and data files in platform-appropriate locations
        (AppData on Windows, ~/Library on macOS, ~/.config on Linux)
"""

import os
import platform
from pathlib import Path
from typing import Optional


class PlatformPaths:
    """Platform-specific path utilities for cross-platform compatibility.
    
    This class provides methods to get platform-appropriate directories for
    configuration, data storage, cache, and logs.
    
    Paths follow platform conventions:
    - Windows: Uses AppData directories (Roaming for config, Local for cache/data)
    - macOS: Uses ~/Library directories (Application Support, Caches, Logs)
    - Linux: Uses XDG directories (~/.config, ~/.local/share, ~/.cache)
    
    Requirements: 15.4, 15.7
    """
    
    # Application name used for directory creation
    APP_NAME = 'local-ai-dev'
    
    # Detect OS once at class level
    _system = platform.system()
    _is_windows = _system == 'Windows'
    _is_macos = _system == 'Darwin'
    _is_linux = _system == 'Linux'
    
    @classmethod
    def get_system(cls) -> str:
        """Get the current operating system name.
        
        Returns:
            'Windows', 'Darwin' (macOS), 'Linux', or other platform name
        """
        return cls._system
    
    @classmethod
    def is_windows(cls) -> bool:
        """Check if running on Windows.
        
        Returns:
            True if Windows, False otherwise
        
        Requirements: 15.4
        """
        return cls._is_windows
    
    @classmethod
    def is_macos(cls) -> bool:
        """Check if running on macOS.
        
        Returns:
            True if macOS, False otherwise
        
        Requirements: 15.4
        """
        return cls._is_macos
    
    @classmethod
    def is_linux(cls) -> bool:
        """Check if running on Linux.
        
        Returns:
            True if Linux, False otherwise
        
        Requirements: 15.4
        """
        return cls._is_linux
    
    @classmethod
    def get_config_dir(cls, create: bool = True) -> Path:
        """Get platform-appropriate configuration directory.
        
        Directory locations:
        - Windows: %APPDATA%/local-ai-dev (e.g., C:\\Users\\User\\AppData\\Roaming\\local-ai-dev)
        - macOS: ~/Library/Application Support/local-ai-dev
        - Linux: ~/.config/local-ai-dev
        
        Args:
            create: If True, create the directory if it doesn't exist
        
        Returns:
            Path object for configuration directory
        
        Requirements: 15.7
        """
        if cls._is_windows:
            # Windows: Use AppData\Roaming for configuration
            base_dir = Path(os.environ.get('APPDATA', Path.home() / 'AppData' / 'Roaming'))
        elif cls._is_macos:
            # macOS: Use ~/Library/Application Support
            base_dir = Path.home() / 'Library' / 'Application Support'
        else:
            # Linux and others: Use ~/.config (XDG Base Directory)
            base_dir = Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config'))
        
        config_dir = base_dir / cls.APP_NAME
        
        if create:
            config_dir.mkdir(parents=True, exist_ok=True)
        
        return config_dir
    
    @classmethod
    def get_data_dir(cls, create: bool = True) -> Path:
        """Get platform-appropriate data directory.
        
        Directory locations:
        - Windows: %LOCALAPPDATA%/local-ai-dev (e.g., C:\\Users\\User\\AppData\\Local\\local-ai-dev)
        - macOS: ~/Library/Application Support/local-ai-dev
        - Linux: ~/.local/share/local-ai-dev
        
        Args:
            create: If True, create the directory if it doesn't exist
        
        Returns:
            Path object for data directory
        
        Requirements: 15.7
        """
        if cls._is_windows:
            # Windows: Use AppData\Local for data
            base_dir = Path(os.environ.get('LOCALAPPDATA', Path.home() / 'AppData' / 'Local'))
        elif cls._is_macos:
            # macOS: Use ~/Library/Application Support (same as config)
            base_dir = Path.home() / 'Library' / 'Application Support'
        else:
            # Linux and others: Use ~/.local/share (XDG Base Directory)
            base_dir = Path(os.environ.get('XDG_DATA_HOME', Path.home() / '.local' / 'share'))
        
        data_dir = base_dir / cls.APP_NAME
        
        if create:
            data_dir.mkdir(parents=True, exist_ok=True)
        
        return data_dir
    
    @classmethod
    def get_cache_dir(cls, create: bool = True) -> Path:
        """Get platform-appropriate cache directory.
        
        Directory locations:
        - Windows: %LOCALAPPDATA%/local-ai-dev/cache
        - macOS: ~/Library/Caches/local-ai-dev
        - Linux: ~/.cache/local-ai-dev
        
        Args:
            create: If True, create the directory if it doesn't exist
        
        Returns:
            Path object for cache directory
        
        Requirements: 15.7
        """
        if cls._is_windows:
            # Windows: Use AppData\Local\local-ai-dev\cache
            base_dir = Path(os.environ.get('LOCALAPPDATA', Path.home() / 'AppData' / 'Local'))
            cache_dir = base_dir / cls.APP_NAME / 'cache'
        elif cls._is_macos:
            # macOS: Use ~/Library/Caches
            base_dir = Path.home() / 'Library' / 'Caches'
            cache_dir = base_dir / cls.APP_NAME
        else:
            # Linux and others: Use ~/.cache (XDG Base Directory)
            base_dir = Path(os.environ.get('XDG_CACHE_HOME', Path.home() / '.cache'))
            cache_dir = base_dir / cls.APP_NAME
        
        if create:
            cache_dir.mkdir(parents=True, exist_ok=True)
        
        return cache_dir
    
    @classmethod
    def get_log_dir(cls, create: bool = True) -> Path:
        """Get platform-appropriate log directory.
        
        Directory locations:
        - Windows: %LOCALAPPDATA%/local-ai-dev/logs
        - macOS: ~/Library/Logs/local-ai-dev
        - Linux: ~/.local/share/local-ai-dev/logs
        
        Args:
            create: If True, create the directory if it doesn't exist
        
        Returns:
            Path object for log directory
        
        Requirements: 15.7
        """
        if cls._is_windows:
            # Windows: Use AppData\Local\local-ai-dev\logs
            base_dir = Path(os.environ.get('LOCALAPPDATA', Path.home() / 'AppData' / 'Local'))
            log_dir = base_dir / cls.APP_NAME / 'logs'
        elif cls._is_macos:
            # macOS: Use ~/Library/Logs
            base_dir = Path.home() / 'Library' / 'Logs'
            log_dir = base_dir / cls.APP_NAME
        else:
            # Linux and others: Use ~/.local/share/local-ai-dev/logs
            base_dir = Path(os.environ.get('XDG_DATA_HOME', Path.home() / '.local' / 'share'))
            log_dir = base_dir / cls.APP_NAME / 'logs'
        
        if create:
            log_dir.mkdir(parents=True, exist_ok=True)
        
        return log_dir
    
    @classmethod
    def get_history_db_path(cls) -> Path:
        """Get platform-appropriate history database path.
        
        Returns:
            Path object for history.db file
        
        Requirements: 15.7
        """
        return cls.get_data_dir() / 'history.db'
    
    @classmethod
    def get_encryption_key_path(cls) -> Path:
        """Get platform-appropriate encryption key path.
        
        Returns:
            Path object for encryption.key file
        
        Requirements: 15.7
        """
        return cls.get_config_dir() / 'encryption.key'
    
    @classmethod
    def get_session_state_path(cls) -> Path:
        """Get platform-appropriate session state path.
        
        Returns:
            Path object for session_state.json file
        
        Requirements: 15.7
        """
        return cls.get_data_dir() / 'session_state.json'
    
    @classmethod
    def normalize_path(cls, path: str) -> str:
        """Normalize path to use platform-appropriate separators.
        
        This method converts path separators to the correct format for the
        current platform while preserving absolute/relative path semantics.
        
        Args:
            path: Path string to normalize
        
        Returns:
            Normalized path string with correct separators
        
        Requirements: 15.4
        """
        if not path:
            return path
        
        # Convert to Path object and back to string to normalize separators
        return str(Path(path))
    
    @classmethod
    def to_platform_path(cls, path: str) -> str:
        """Convert path to platform-specific format.
        
        This is an alias for normalize_path() for clearer intent in some contexts.
        
        Args:
            path: Path string to convert
        
        Returns:
            Platform-specific path string
        
        Requirements: 15.4
        """
        return cls.normalize_path(path)
    
    @classmethod
    def join_path(cls, *parts: str) -> str:
        """Join path parts using platform-appropriate separator.
        
        This is a convenience wrapper around Path() / Path() that returns a string.
        
        Args:
            *parts: Path components to join
        
        Returns:
            Joined path string with correct separators
        
        Requirements: 15.4
        """
        if not parts:
            return ''
        
        result = Path(parts[0])
        for part in parts[1:]:
            result = result / part
        
        return str(result)
    
    @classmethod
    def get_path_separator(cls) -> str:
        """Get the path separator for the current platform.
        
        Returns:
            Path separator ('\\' on Windows, '/' on Unix-like systems)
        
        Requirements: 15.4
        """
        return os.sep
    
    @classmethod
    def ensure_dir_exists(cls, path: Path) -> Path:
        """Ensure a directory exists, creating it if necessary.
        
        Args:
            path: Path object for directory
        
        Returns:
            The same Path object
        """
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    @classmethod
    def get_temp_dir(cls) -> Path:
        """Get platform-appropriate temporary directory for the application.
        
        Returns:
            Path object for temporary directory
        """
        if cls._is_windows:
            # Windows: Use TEMP environment variable
            temp_base = Path(os.environ.get('TEMP', Path.home() / 'AppData' / 'Local' / 'Temp'))
        elif cls._is_macos:
            # macOS: Use system temp directory
            temp_base = Path('/tmp')
        else:
            # Linux: Use /tmp or XDG_RUNTIME_DIR
            temp_base = Path(os.environ.get('XDG_RUNTIME_DIR', '/tmp'))
        
        temp_dir = temp_base / cls.APP_NAME
        temp_dir.mkdir(parents=True, exist_ok=True)
        return temp_dir


# Convenience functions for easier imports

def get_config_dir(create: bool = True) -> Path:
    """Get platform-appropriate configuration directory.
    
    Convenience function that delegates to PlatformPaths.get_config_dir().
    
    Args:
        create: If True, create the directory if it doesn't exist
    
    Returns:
        Path object for configuration directory
    """
    return PlatformPaths.get_config_dir(create=create)


def get_data_dir(create: bool = True) -> Path:
    """Get platform-appropriate data directory.
    
    Convenience function that delegates to PlatformPaths.get_data_dir().
    
    Args:
        create: If True, create the directory if it doesn't exist
    
    Returns:
        Path object for data directory
    """
    return PlatformPaths.get_data_dir(create=create)


def get_cache_dir(create: bool = True) -> Path:
    """Get platform-appropriate cache directory.
    
    Convenience function that delegates to PlatformPaths.get_cache_dir().
    
    Args:
        create: If True, create the directory if it doesn't exist
    
    Returns:
        Path object for cache directory
    """
    return PlatformPaths.get_cache_dir(create=create)


def get_log_dir(create: bool = True) -> Path:
    """Get platform-appropriate log directory.
    
    Convenience function that delegates to PlatformPaths.get_log_dir().
    
    Args:
        create: If True, create the directory if it doesn't exist
    
    Returns:
        Path object for log directory
    """
    return PlatformPaths.get_log_dir(create=create)


def normalize_path(path: str) -> str:
    """Normalize path to use platform-appropriate separators.
    
    Convenience function that delegates to PlatformPaths.normalize_path().
    
    Args:
        path: Path string to normalize
    
    Returns:
        Normalized path string with correct separators
    """
    return PlatformPaths.normalize_path(path)
