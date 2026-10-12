"""GUI Configuration Manager for Desktop GUI Application.

This module provides GUI-specific configuration management with validation,
encryption of sensitive values, atomic file writes, and external change detection.

Requirements:
- 4.2: Display current configuration values when opened
- 4.3: Validate input before accepting
- 4.4: Display error message and prevent saving invalid input
- 4.10: Prompt for API key if required
- 4.11: Mask sensitive values like API keys
- 12.1: Validate Configuration_Store structure
- 12.2: Preserve unknown fields when saving
- 12.3: Detect external changes within 5 seconds
- 12.4: Prompt user to reload or keep current settings
- 12.5: Create backup of previous Configuration_Store
- 12.6: Restore backup if saving fails
- 12.7: Use atomic file operations
- 12.8: Validate configuration values before writing
- 14.2: Encrypt sensitive configuration values (API keys)
"""

import os
import re
import shutil
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlparse
from cryptography.fernet import Fernet
import yaml

from ..core.config import ConfigManager, ConfigurationError
from .platform_paths import PlatformPaths


class FileWatcher:
    """Watches a file for external modifications.
    
    Uses simple mtime-based checking for reliability and simplicity.
    Can be used with watchdog for real-time notifications if needed.
    """
    
    def __init__(self, file_path: str):
        """Initialize file watcher.
        
        Args:
            file_path: Path to file to watch
        """
        self.file_path = Path(file_path)
        self._last_mtime: Optional[float] = None
        self._last_check_time: float = 0.0
        self._update_mtime()
    
    def _update_mtime(self) -> None:
        """Update stored modification time."""
        if self.file_path.exists():
            self._last_mtime = self.file_path.stat().st_mtime
        else:
            self._last_mtime = None
        self._last_check_time = time.time()
    
    def has_changed(self) -> bool:
        """Check if file has been modified externally.
        
        Returns:
            True if file was modified since last check, False otherwise
        
        Requirements: 12.3
        """
        # Rate limit checks to avoid excessive filesystem operations
        current_time = time.time()
        if current_time - self._last_check_time < 1.0:
            # Don't check more than once per second
            return False
        
        self._last_check_time = current_time
        
        if not self.file_path.exists():
            # File was deleted
            if self._last_mtime is not None:
                return True
            return False
        
        current_mtime = self.file_path.stat().st_mtime
        if self._last_mtime is None:
            # File was created
            return True
        
        # Check if modified (with small tolerance for filesystem precision)
        return abs(current_mtime - self._last_mtime) > 0.001
    
    def acknowledge_change(self) -> None:
        """Acknowledge external change and update stored mtime."""
        self._update_mtime()


class GUIConfigManager:
    """GUI-specific configuration manager with validation and encryption.
    
    Provides configuration management tailored for GUI usage, including:
    - Field-level validation with user-friendly error messages
    - Atomic file writes with backup/restore
    - External change detection via file watching
    - Encryption/decryption of sensitive values (API keys)
    """
    
    # Sensitive fields that should be masked in GUI
    SENSITIVE_FIELDS = {'api_key', 'password', 'token', 'secret'}
    
    # Validation rules for specific field types
    VALIDATION_RULES = {
        'llm.endpoint': 'url',
        'llm.temperature': ('float', 0.0, 1.0),
        'llm.max_tokens': ('positive_int',),
        'llm.context_length': ('positive_int',),
        'project_root': 'directory',
        'log_level': ('enum', ['debug', 'info', 'warning', 'error']),
    }
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize GUI config manager.
        
        Args:
            config_path: Path to configuration file
        
        Requirements: 12.1, 12.3, 14.2
        """
        self.config_path = Path(config_path)
        self.config_manager = ConfigManager(str(config_path))
        
        # Load or create configuration
        try:
            self.config = self.config_manager.load_config()
        except ConfigurationError:
            # Config doesn't exist or is invalid, will be created on first save
            self.config = None
        
        # Initialize file watcher for external change detection
        self.file_watcher = FileWatcher(str(self.config_path))
        
        # Load or create encryption key for sensitive values
        self.encryption_key = self._load_or_create_key()
        self.cipher = Fernet(self.encryption_key)
        
        # Store original config dict to preserve unknown fields
        self._original_config_dict: Dict[str, Any] = {}
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    self._original_config_dict = yaml.safe_load(f) or {}
            except Exception:
                self._original_config_dict = {}
    
    def _load_or_create_key(self) -> bytes:
        """Load or create encryption key for sensitive values.
        
        Key is stored in platform-appropriate location:
        - Windows: %APPDATA%/local-ai-dev/encryption.key
        - macOS: ~/Library/Application Support/local-ai-dev/encryption.key
        - Linux: ~/.config/local-ai-dev/encryption.key
        
        Returns:
            Encryption key bytes
        
        Requirements: 14.2, 15.7
        """
        # Use platform-appropriate path from PlatformPaths utility
        key_path = PlatformPaths.get_encryption_key_path()
        
        if key_path.exists():
            # Load existing key
            with open(key_path, 'rb') as f:
                return f.read()
        else:
            # Generate and save new key
            key = Fernet.generate_key()
            with open(key_path, 'wb') as f:
                f.write(key)
            # Set restrictive permissions (owner only) - only on Unix-like systems
            if not PlatformPaths.is_windows():
                key_path.chmod(0o600)
            return key
    
    def get_config_for_gui(self) -> Dict[str, Any]:
        """Get configuration in GUI-friendly format.
        
        Converts configuration to dictionary with sensitive values masked.
        
        Returns:
            Dictionary with all config values, sensitive values shown as masked
        
        Requirements: 4.2, 4.11
        """
        if self.config is None:
            # Return default configuration
            return self.config_manager._get_default_config_dict()
        
        # Convert config to dictionary
        config_dict = {
            'llm': {
                'endpoint': self.config.llm.endpoint,
                'model_name': self.config.llm.model_name,
                'temperature': self.config.llm.temperature,
                'max_tokens': self.config.llm.max_tokens,
                'context_length': self.config.llm.context_length,
                'backend_type': self.config.llm.backend_type,
            },
            'project_root': self.config.project_root,
            'log_level': self.config.log_level,
            'web_research_enabled': self.config.web_research_enabled,
            'self_improvement_enabled': self.config.self_improvement_enabled,
            'excluded_directories': self.config.excluded_directories.copy()
        }
        
        # Mask sensitive values
        config_dict = self._mask_sensitive_values(config_dict)
        
        return config_dict
    
    def _mask_sensitive_values(self, config_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Mask sensitive values in configuration dictionary.
        
        Args:
            config_dict: Configuration dictionary
        
        Returns:
            Configuration dictionary with sensitive values masked
        
        Requirements: 4.11
        """
        def mask_dict(d: Dict[str, Any]) -> Dict[str, Any]:
            result = {}
            for key, value in d.items():
                if isinstance(value, dict):
                    result[key] = mask_dict(value)
                elif any(sensitive in key.lower() for sensitive in self.SENSITIVE_FIELDS):
                    # Mask sensitive field
                    if value and isinstance(value, str):
                        result[key] = '•' * min(len(value), 12)
                    else:
                        result[key] = value
                else:
                    result[key] = value
            return result
        
        return mask_dict(config_dict)
    
    def validate_field(self, field_name: str, value: Any) -> Tuple[bool, str]:
        """Validate a single configuration field.
        
        Args:
            field_name: Dot-notation field name (e.g., 'llm.endpoint')
            value: Value to validate
        
        Returns:
            Tuple of (is_valid, error_message)
            If valid, error_message is empty string
        
        Requirements: 4.3, 4.4, 12.8
        """
        # Get validation rule for field
        if field_name not in self.VALIDATION_RULES:
            # No specific rule, accept any value
            return (True, "")
        
        rule = self.VALIDATION_RULES[field_name]
        
        # Handle different validation types
        if rule == 'url':
            return self._validate_url(value)
        elif rule == 'directory':
            return self._validate_directory(value)
        elif isinstance(rule, tuple):
            if rule[0] == 'float':
                return self._validate_float_range(value, rule[1], rule[2])
            elif rule[0] == 'positive_int':
                return self._validate_positive_int(value)
            elif rule[0] == 'enum':
                return self._validate_enum(value, rule[1])
        
        return (True, "")
    
    def _validate_url(self, value: Any) -> Tuple[bool, str]:
        """Validate URL field.
        
        Requirements: 4.3, 12.8
        """
        if not isinstance(value, str):
            return (False, "URL must be a string")
        
        if not value:
            return (False, "URL cannot be empty")
        
        try:
            result = urlparse(value)
            if not all([result.scheme, result.netloc]):
                return (False, "Invalid URL format. Must include protocol (http:// or https://) and host")
            if result.scheme not in ['http', 'https']:
                return (False, "URL must use http:// or https:// protocol")
            return (True, "")
        except Exception:
            return (False, "Invalid URL format")
    
    def _validate_directory(self, value: Any) -> Tuple[bool, str]:
        """Validate directory path field.
        
        Requirements: 4.3, 12.8
        """
        if not isinstance(value, str):
            return (False, "Directory path must be a string")
        
        if not value:
            return (False, "Directory path cannot be empty")
        
        path = Path(value)
        if not path.exists():
            return (False, f"Directory does not exist: {value}")
        
        if not path.is_dir():
            return (False, f"Path is not a directory: {value}")
        
        return (True, "")
    
    def _validate_float_range(self, value: Any, min_val: float, max_val: float) -> Tuple[bool, str]:
        """Validate float within range.
        
        Requirements: 4.3, 12.8
        """
        try:
            float_val = float(value)
            if not (min_val <= float_val <= max_val):
                return (False, f"Value must be between {min_val} and {max_val}")
            return (True, "")
        except (TypeError, ValueError):
            return (False, f"Must be a number between {min_val} and {max_val}")
    
    def _validate_positive_int(self, value: Any) -> Tuple[bool, str]:
        """Validate positive integer.
        
        Requirements: 4.3, 12.8
        """
        try:
            int_val = int(value)
            if int_val <= 0:
                return (False, "Value must be a positive integer")
            return (True, "")
        except (TypeError, ValueError):
            return (False, "Must be a positive integer")
    
    def _validate_enum(self, value: Any, allowed_values: list) -> Tuple[bool, str]:
        """Validate enum value.
        
        Requirements: 4.3, 12.8
        """
        if value not in allowed_values:
            return (False, f"Must be one of: {', '.join(str(v) for v in allowed_values)}")
        return (True, "")
    
    def save_config(self, config_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Save configuration with atomic write and backup.
        
        Process:
        1. Validate all configuration values
        2. Create backup of existing config
        3. Write to temporary file
        4. Atomic rename to actual config file
        5. If error occurs, restore from backup
        
        Args:
            config_data: Complete configuration dictionary
        
        Returns:
            Tuple of (success, message)
        
        Requirements: 4.5, 4.6, 12.2, 12.5, 12.6, 12.7, 12.8
        """
        try:
            # Merge with original config to preserve unknown fields (Req 12.2)
            merged_config = self._original_config_dict.copy()
            self._deep_merge(merged_config, config_data)
            
            # Validate configuration
            try:
                # Create temporary SystemConfig for validation
                temp_config = self.config_manager._create_system_config(merged_config)
            except ConfigurationError as e:
                return (False, f"Configuration validation failed: {str(e)}")
            
            # Create backup if config file exists (Req 12.5)
            backup_path = None
            if self.config_path.exists():
                backup_path = self.config_path.with_suffix('.yaml.backup')
                try:
                    shutil.copy2(self.config_path, backup_path)
                except Exception as e:
                    return (False, f"Failed to create backup: {str(e)}")
            
            # Write to temporary file (Req 12.7 - atomic operation)
            temp_fd, temp_path = tempfile.mkstemp(
                suffix='.yaml.tmp',
                dir=self.config_path.parent,
                text=True
            )
            
            try:
                with os.fdopen(temp_fd, 'w') as f:
                    yaml.safe_dump(merged_config, f, default_flow_style=False, sort_keys=False)
                
                # Atomic rename (Req 12.7)
                shutil.move(temp_path, self.config_path)
                
                # Update internal state
                self.config = temp_config
                self._original_config_dict = merged_config
                
                # Update file watcher
                self.file_watcher.acknowledge_change()
                
                # Remove backup on success
                if backup_path and backup_path.exists():
                    backup_path.unlink()
                
                return (True, "Configuration saved successfully")
                
            except Exception as e:
                # Clean up temp file if it still exists
                temp_path_obj = Path(temp_path)
                if temp_path_obj.exists():
                    temp_path_obj.unlink()
                
                # Restore from backup (Req 12.6)
                if backup_path and backup_path.exists():
                    try:
                        shutil.copy2(backup_path, self.config_path)
                        backup_path.unlink()
                        return (False, f"Configuration save failed, backup restored: {str(e)}")
                    except Exception as restore_error:
                        return (False, f"Configuration save failed and backup restoration failed: {str(e)}; {str(restore_error)}")
                
                return (False, f"Failed to save configuration: {str(e)}")
                
        except Exception as e:
            return (False, f"Unexpected error saving configuration: {str(e)}")
    
    def _deep_merge(self, base: Dict[str, Any], update: Dict[str, Any]) -> None:
        """Deep merge update dict into base dict.
        
        Modifies base dict in place.
        
        Args:
            base: Base dictionary to merge into
            update: Dictionary with updates
        
        Requirements: 12.2 - preserve unknown fields
        """
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def reset_to_defaults(self) -> Dict[str, Any]:
        """Reset configuration to default values.
        
        Returns:
            Default configuration dictionary
        
        Requirements: 4.7
        """
        return self.config_manager._get_default_config_dict()
    
    def check_external_changes(self) -> bool:
        """Check if config file was modified externally.
        
        Returns:
            True if changes detected, False otherwise
        
        Requirements: 12.3
        """
        return self.file_watcher.has_changed()
    
    def reload_config(self) -> None:
        """Reload configuration from disk.
        
        Updates internal state with current file contents.
        
        Requirements: 12.4
        """
        try:
            self.config = self.config_manager.reload_config()
            
            # Reload original config dict
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    self._original_config_dict = yaml.safe_load(f) or {}
            
            # Acknowledge the change
            self.file_watcher.acknowledge_change()
            
        except ConfigurationError as e:
            raise ConfigurationError(f"Failed to reload configuration: {str(e)}")
    
    def encrypt_sensitive_value(self, value: str) -> str:
        """Encrypt sensitive value (e.g., API key).
        
        Args:
            value: Plain text value to encrypt
        
        Returns:
            Encrypted value as string
        
        Requirements: 14.2
        """
        if not value:
            return value
        
        encrypted_bytes = self.cipher.encrypt(value.encode('utf-8'))
        return encrypted_bytes.decode('utf-8')
    
    def decrypt_sensitive_value(self, encrypted: str) -> str:
        """Decrypt sensitive value.
        
        Args:
            encrypted: Encrypted value as string
        
        Returns:
            Decrypted plain text value
        
        Requirements: 14.2
        """
        if not encrypted:
            return encrypted
        
        try:
            decrypted_bytes = self.cipher.decrypt(encrypted.encode('utf-8'))
            return decrypted_bytes.decode('utf-8')
        except Exception:
            # If decryption fails, return as-is (might not be encrypted)
            return encrypted
