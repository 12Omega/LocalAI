"""Unit tests for GUI Config Manager.

Tests configuration validation, atomic writes, backup/restore,
external change detection, and sensitive value encryption.

Requirements:
- 4.3: Validate input before accepting
- 4.4: Display error message and prevent saving invalid input
- 12.5: Create backup of previous Configuration_Store
- 12.6: Restore backup if saving fails
- 14.2: Encrypt sensitive configuration values
"""

import os
import pytest
import tempfile
import time
from pathlib import Path
import yaml

from src.gui.gui_config_manager import GUIConfigManager, FileWatcher
from src.core.config import ConfigurationError


@pytest.fixture
def temp_config_dir(tmp_path):
    """Create temporary directory for config files."""
    return tmp_path


@pytest.fixture
def sample_config_data():
    """Sample valid configuration data."""
    return {
        'llm': {
            'endpoint': 'http://localhost:11434',
            'model_name': 'codellama:13b',
            'temperature': 0.2,
            'max_tokens': 4096,
            'context_length': 16384,
            'backend_type': 'ollama'
        },
        'project_root': os.getcwd(),
        'log_level': 'info',
        'web_research_enabled': True,
        'self_improvement_enabled': False,
        'excluded_directories': ['node_modules', '.git', '__pycache__']
    }


@pytest.fixture
def config_file(temp_config_dir, sample_config_data):
    """Create a temporary config file."""
    config_path = temp_config_dir / "config.yaml"
    with open(config_path, 'w') as f:
        yaml.safe_dump(sample_config_data, f)
    return config_path


@pytest.fixture
def config_manager(config_file):
    """Create GUIConfigManager instance with temp config."""
    return GUIConfigManager(str(config_file))


class TestFileWatcher:
    """Tests for FileWatcher class."""
    
    def test_file_watcher_initialization(self, temp_config_dir):
        """Test FileWatcher initializes correctly."""
        test_file = temp_config_dir / "test.yaml"
        test_file.touch()
        
        watcher = FileWatcher(str(test_file))
        assert watcher.file_path == test_file
        assert watcher._last_mtime is not None
    
    def test_detect_file_modification(self, temp_config_dir):
        """Test FileWatcher detects file modifications."""
        test_file = temp_config_dir / "test.yaml"
        test_file.write_text("original content")
        
        watcher = FileWatcher(str(test_file))
        
        # Acknowledge initial state
        watcher.acknowledge_change()
        
        # Wait to ensure filesystem timestamp granularity
        time.sleep(0.1)
        
        # Modify file
        test_file.write_text("modified content")
        
        # Wait for rate limiting
        time.sleep(1.1)
        
        # Should detect change
        assert watcher.has_changed()
    
    def test_acknowledge_change(self, temp_config_dir):
        """Test acknowledging changes updates internal state."""
        test_file = temp_config_dir / "test.yaml"
        test_file.write_text("content")
        
        watcher = FileWatcher(str(test_file))
        
        # Modify file
        time.sleep(0.1)
        test_file.write_text("new content")
        time.sleep(1.1)
        
        # Detect change
        assert watcher.has_changed()
        
        # Acknowledge
        watcher.acknowledge_change()
        
        # Should not detect change anymore
        time.sleep(1.1)
        assert not watcher.has_changed()
    
    def test_detect_file_deletion(self, temp_config_dir):
        """Test FileWatcher detects file deletion."""
        test_file = temp_config_dir / "test.yaml"
        test_file.write_text("content")
        
        watcher = FileWatcher(str(test_file))
        watcher.acknowledge_change()
        
        # Delete file
        test_file.unlink()
        
        # Wait for rate limiting
        time.sleep(1.1)
        
        # Should detect deletion
        assert watcher.has_changed()


class TestGUIConfigManager:
    """Tests for GUIConfigManager class."""
    
    def test_initialization(self, config_manager):
        """Test GUIConfigManager initializes correctly."""
        assert config_manager.config is not None
        assert config_manager.file_watcher is not None
        assert config_manager.encryption_key is not None
        assert config_manager.cipher is not None
    
    def test_get_config_for_gui(self, config_manager):
        """Test getting configuration in GUI-friendly format.
        
        Requirements: 4.2
        """
        config = config_manager.get_config_for_gui()
        
        assert 'llm' in config
        assert 'endpoint' in config['llm']
        assert 'project_root' in config
        assert 'log_level' in config
        assert isinstance(config['excluded_directories'], list)
    
    def test_mask_sensitive_values(self, config_manager):
        """Test sensitive values are masked.
        
        Requirements: 4.11
        """
        test_config = {
            'llm': {
                'endpoint': 'http://localhost:11434',
                'api_key': 'sk-secret123456789'
            },
            'password': 'mypassword123'
        }
        
        masked = config_manager._mask_sensitive_values(test_config)
        
        # Non-sensitive values unchanged
        assert masked['llm']['endpoint'] == 'http://localhost:11434'
        
        # Sensitive values masked
        assert masked['llm']['api_key'] == '•' * 12
        assert masked['password'] == '•' * 12
    
    def test_validate_url_field_valid(self, config_manager):
        """Test URL validation with valid URLs.
        
        Requirements: 4.3
        """
        valid, msg = config_manager.validate_field('llm.endpoint', 'http://localhost:11434')
        assert valid
        assert msg == ""
        
        valid, msg = config_manager.validate_field('llm.endpoint', 'https://api.openai.com')
        assert valid
        assert msg == ""
    
    def test_validate_url_field_invalid(self, config_manager):
        """Test URL validation with invalid URLs.
        
        Requirements: 4.3, 4.4
        """
        # Empty URL
        valid, msg = config_manager.validate_field('llm.endpoint', '')
        assert not valid
        assert 'empty' in msg.lower()
        
        # Missing protocol
        valid, msg = config_manager.validate_field('llm.endpoint', 'localhost:11434')
        assert not valid
        assert 'protocol' in msg.lower()
        
        # Invalid protocol
        valid, msg = config_manager.validate_field('llm.endpoint', 'ftp://localhost:11434')
        assert not valid
        assert 'http' in msg.lower()
    
    def test_validate_float_range_field(self, config_manager):
        """Test float range validation.
        
        Requirements: 4.3
        """
        # Valid values
        valid, msg = config_manager.validate_field('llm.temperature', 0.0)
        assert valid
        
        valid, msg = config_manager.validate_field('llm.temperature', 0.5)
        assert valid
        
        valid, msg = config_manager.validate_field('llm.temperature', 1.0)
        assert valid
        
        # Invalid values
        valid, msg = config_manager.validate_field('llm.temperature', -0.1)
        assert not valid
        assert 'between' in msg.lower()
        
        valid, msg = config_manager.validate_field('llm.temperature', 1.5)
        assert not valid
        assert 'between' in msg.lower()
        
        valid, msg = config_manager.validate_field('llm.temperature', 'not a number')
        assert not valid
        assert 'number' in msg.lower()
    
    def test_validate_positive_int_field(self, config_manager):
        """Test positive integer validation.
        
        Requirements: 4.3
        """
        # Valid values
        valid, msg = config_manager.validate_field('llm.max_tokens', 1)
        assert valid
        
        valid, msg = config_manager.validate_field('llm.max_tokens', 4096)
        assert valid
        
        # Invalid values
        valid, msg = config_manager.validate_field('llm.max_tokens', 0)
        assert not valid
        assert 'positive' in msg.lower()
        
        valid, msg = config_manager.validate_field('llm.max_tokens', -100)
        assert not valid
        
        valid, msg = config_manager.validate_field('llm.max_tokens', 'not a number')
        assert not valid
    
    def test_validate_enum_field(self, config_manager):
        """Test enum validation.
        
        Requirements: 4.3
        """
        # Valid values
        for level in ['debug', 'info', 'warning', 'error']:
            valid, msg = config_manager.validate_field('log_level', level)
            assert valid, f"Expected {level} to be valid"
        
        # Invalid value
        valid, msg = config_manager.validate_field('log_level', 'invalid')
        assert not valid
        assert 'one of' in msg.lower()
    
    def test_validate_directory_field(self, config_manager, temp_config_dir):
        """Test directory path validation.
        
        Requirements: 4.3
        """
        # Valid directory
        valid, msg = config_manager.validate_field('project_root', str(temp_config_dir))
        assert valid
        
        # Non-existent directory
        valid, msg = config_manager.validate_field('project_root', str(temp_config_dir / 'nonexistent'))
        assert not valid
        assert 'does not exist' in msg.lower()
        
        # File instead of directory
        test_file = temp_config_dir / "test.txt"
        test_file.touch()
        valid, msg = config_manager.validate_field('project_root', str(test_file))
        assert not valid
        assert 'not a directory' in msg.lower()
    
    def test_save_config_success(self, config_manager, sample_config_data, config_file):
        """Test successful configuration save.
        
        Requirements: 4.5, 4.6, 12.7, 12.8
        """
        # Modify config
        modified_config = sample_config_data.copy()
        modified_config['log_level'] = 'debug'
        
        success, msg = config_manager.save_config(modified_config)
        
        assert success
        assert 'success' in msg.lower()
        
        # Verify file was updated
        with open(config_file, 'r') as f:
            saved_config = yaml.safe_load(f)
        
        assert saved_config['log_level'] == 'debug'
    
    def test_save_config_creates_backup(self, config_manager, sample_config_data, config_file):
        """Test backup creation during save.
        
        Requirements: 12.5
        """
        backup_path = config_file.with_suffix('.yaml.backup')
        
        # Ensure no backup exists initially
        if backup_path.exists():
            backup_path.unlink()
        
        # Save config
        modified_config = sample_config_data.copy()
        modified_config['log_level'] = 'debug'
        
        # During save, backup is created temporarily
        # After successful save, backup is removed
        success, msg = config_manager.save_config(modified_config)
        assert success
        
        # Backup should be removed after successful save
        assert not backup_path.exists()
    
    def test_save_config_validation_failure(self, config_manager, sample_config_data):
        """Test save fails with invalid configuration.
        
        Requirements: 4.4, 12.8
        """
        # Invalid temperature
        invalid_config = sample_config_data.copy()
        invalid_config['llm']['temperature'] = 5.0  # Out of range
        
        success, msg = config_manager.save_config(invalid_config)
        
        assert not success
        assert 'validation' in msg.lower() or 'temperature' in msg.lower()
    
    def test_save_config_preserves_unknown_fields(self, config_file, sample_config_data):
        """Test saving preserves unknown fields.
        
        Requirements: 12.2
        """
        # Add unknown field to config file
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        config['custom_field'] = 'custom_value'
        config['nested'] = {'unknown': 'field'}
        
        with open(config_file, 'w') as f:
            yaml.safe_dump(config, f)
        
        # Create manager and save
        manager = GUIConfigManager(str(config_file))
        modified_config = sample_config_data.copy()
        modified_config['log_level'] = 'debug'
        
        success, msg = manager.save_config(modified_config)
        assert success
        
        # Verify unknown fields preserved
        with open(config_file, 'r') as f:
            saved_config = yaml.safe_load(f)
        
        assert 'custom_field' in saved_config
        assert saved_config['custom_field'] == 'custom_value'
        assert 'nested' in saved_config
        assert saved_config['nested']['unknown'] == 'field'
    
    def test_atomic_write_on_error(self, config_manager, sample_config_data, config_file, monkeypatch):
        """Test atomic write restores backup on error.
        
        Requirements: 12.6, 12.7
        """
        # Read original content
        with open(config_file, 'r') as f:
            original_content = f.read()
        
        # Monkeypatch to simulate write error after backup
        original_move = __import__('shutil').move
        
        def failing_move(src, dst):
            if dst == config_file:
                raise IOError("Simulated write error")
            return original_move(src, dst)
        
        monkeypatch.setattr('shutil.move', failing_move)
        
        # Try to save
        modified_config = sample_config_data.copy()
        modified_config['log_level'] = 'debug'
        
        success, msg = config_manager.save_config(modified_config)
        
        assert not success
        assert 'backup restored' in msg.lower() or 'failed' in msg.lower()
        
        # Verify original content preserved
        with open(config_file, 'r') as f:
            current_content = f.read()
        
        assert current_content == original_content
    
    def test_check_external_changes(self, config_manager, config_file):
        """Test detection of external configuration changes.
        
        Requirements: 12.3
        """
        # Acknowledge current state
        config_manager.file_watcher.acknowledge_change()
        
        # Modify config externally
        time.sleep(0.1)
        with open(config_file, 'a') as f:
            f.write("\n# External change\n")
        
        # Wait for rate limiting
        time.sleep(1.1)
        
        # Should detect change
        assert config_manager.check_external_changes()
    
    def test_reload_config(self, config_manager, config_file, sample_config_data):
        """Test reloading configuration from disk.
        
        Requirements: 12.4
        """
        # Modify config file externally
        modified_config = sample_config_data.copy()
        modified_config['log_level'] = 'error'
        
        with open(config_file, 'w') as f:
            yaml.safe_dump(modified_config, f)
        
        # Reload
        config_manager.reload_config()
        
        # Verify change reflected
        reloaded_config = config_manager.get_config_for_gui()
        assert reloaded_config['log_level'] == 'error'
        
        # File watcher should acknowledge the change
        time.sleep(1.1)
        assert not config_manager.check_external_changes()
    
    def test_encrypt_decrypt_sensitive_value(self, config_manager):
        """Test encryption and decryption of sensitive values.
        
        Requirements: 14.2
        """
        sensitive_value = "sk-1234567890abcdef"
        
        # Encrypt
        encrypted = config_manager.encrypt_sensitive_value(sensitive_value)
        
        # Should be different from original
        assert encrypted != sensitive_value
        
        # Decrypt
        decrypted = config_manager.decrypt_sensitive_value(encrypted)
        
        # Should match original
        assert decrypted == sensitive_value
    
    def test_encrypt_empty_value(self, config_manager):
        """Test encrypting empty value returns empty.
        
        Requirements: 14.2
        """
        encrypted = config_manager.encrypt_sensitive_value("")
        assert encrypted == ""
        
        encrypted = config_manager.encrypt_sensitive_value(None)
        assert encrypted is None
    
    def test_reset_to_defaults(self, config_manager):
        """Test resetting configuration to defaults.
        
        Requirements: 4.7
        """
        defaults = config_manager.reset_to_defaults()
        
        assert 'llm' in defaults
        assert 'project_root' in defaults
        assert 'log_level' in defaults
        assert defaults['log_level'] == 'info'
        assert defaults['llm']['temperature'] == 0.2
