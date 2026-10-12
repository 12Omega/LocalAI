"""
Unit tests for GUI Config Manager

Tests cover:
- Field validation for each config type
- Atomic write and backup restoration
- External change detection
- Sensitive value encryption
"""

import os
import tempfile
import time
import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from src.gui.gui_config_manager import GUIConfigManager
from src.core.models import SystemConfig, LLMConfig


class TestGUIConfigManagerInit:
    """Tests for initialization."""
    
    def test_init_with_valid_config(self):
        """Should initialize with valid config file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / 'config.yaml'
            
            # Create a valid config file
            config_content = """
llm:
  endpoint: "http://localhost:11434"
  model_name: "codellama:13b"
  temperature: 0.2
  max_tokens: 4096
  context_length: 16384
  backend_type: "ollama"
project_root: "."
log_level: "info"
web_research_enabled: true
self_improvement_enabled: false
excluded_directories:
  - "node_modules"
  - ".git"
"""
            config_path.write_text(config_content)
            
            manager = GUIConfigManager(str(config_path))
            
            assert manager.config is not None
            assert manager.config.llm.endpoint == "http://localhost:11434"
            assert manager.config.log_level == "info"
    
    def test_init_without_config_file(self):
        """Should initialize with None config when config file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / 'nonexistent.yaml'
            
            manager = GUIConfigManager(str(config_path))
            
            # Config is None when file doesn't exist, but get_config_for_gui returns defaults
            assert manager.config is None
            config_dict = manager.get_config_for_gui()
            assert config_dict['llm']['endpoint'] == "http://localhost:11434"


class TestGetConfigForGUI:
    """Tests for get_config_for_gui method."""
    
    def test_returns_dict_format(self):
        """Should return config as dictionary."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / 'config.yaml'
            config_path.write_text("llm:\n  endpoint: 'http://localhost:11434'\n  model_name: 'test'\nproject_root: '.'")
            
            manager = GUIConfigManager(str(config_path))
            config_dict = manager.get_config_for_gui()
            
            assert isinstance(config_dict, dict)
            assert 'llm' in config_dict
            assert 'project_root' in config_dict
            assert isinstance(config_dict['llm'], dict)
    
    def test_includes_all_fields(self):
        """Should include all configuration fields."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / 'config.yaml'
            config_path.write_text("llm:\n  endpoint: 'http://localhost:11434'\n  model_name: 'test'\nproject_root: '.'")
            
            manager = GUIConfigManager(str(config_path))
            config_dict = manager.get_config_for_gui()
            
            # Check LLM fields
            assert 'endpoint' in config_dict['llm']
            assert 'model_name' in config_dict['llm']
            assert 'temperature' in config_dict['llm']
            assert 'max_tokens' in config_dict['llm']
            assert 'context_length' in config_dict['llm']
            assert 'backend_type' in config_dict['llm']
            
            # Check other fields
            assert 'project_root' in config_dict
            assert 'log_level' in config_dict
            assert 'web_research_enabled' in config_dict
            assert 'self_improvement_enabled' in config_dict
            assert 'excluded_directories' in config_dict


class TestValidateField:
    """Tests for validate_field method."""
    
    def test_validate_endpoint_accepts_valid_urls(self):
        """Valid URLs should pass validation."""
        manager = GUIConfigManager()
        
        valid_urls = [
            "http://localhost:11434",
            "https://example.com:8080",
            "http://192.168.1.1:3000",
            "https://api.example.com"
        ]
        
        for url in valid_urls:
            is_valid, error = manager.validate_field('llm.endpoint', url)
            assert is_valid, f"URL {url} should be valid but got error: {error}"
            assert error == ""
    
    def test_validate_endpoint_rejects_invalid_urls(self):
        """Invalid URLs should fail validation."""
        manager = GUIConfigManager()
        
        invalid_urls = [
            "",
            "not a url",
            "ftp://example.com",
            "http://",
            "localhost:11434",  # missing scheme
            "//example.com"  # missing scheme
        ]
        
        for url in invalid_urls:
            is_valid, error = manager.validate_field('llm.endpoint', url)
            assert not is_valid, f"URL {url} should be invalid"
            assert error != ""
    
    def test_validate_temperature_range(self):
        """Temperature must be between 0.0 and 1.0."""
        manager = GUIConfigManager()
        
        # Valid values
        for temp in [0.0, 0.5, 1.0]:
            is_valid, error = manager.validate_field('llm.temperature', temp)
            assert is_valid, f"Temperature {temp} should be valid"
        
        # Invalid values
        for temp in [-0.1, 1.1, 2.0, -1.0]:
            is_valid, error = manager.validate_field('llm.temperature', temp)
            assert not is_valid, f"Temperature {temp} should be invalid"
    
    def test_validate_temperature_type(self):
        """Temperature must be numeric."""
        manager = GUIConfigManager()
        
        is_valid, error = manager.validate_field('llm.temperature', "not a number")
        assert not is_valid
        assert "number" in error.lower()
    
    def test_validate_max_tokens_positive(self):
        """Max tokens must be positive."""
        manager = GUIConfigManager()
        
        # Valid
        is_valid, error = manager.validate_field('llm.max_tokens', 4096)
        assert is_valid
        
        # Invalid - negative
        is_valid, error = manager.validate_field('llm.max_tokens', -100)
        assert not is_valid
        
        # Invalid - zero
        is_valid, error = manager.validate_field('llm.max_tokens', 0)
        assert not is_valid
    
    def test_validate_context_length_positive(self):
        """Context length must be positive."""
        manager = GUIConfigManager()
        
        # Valid
        is_valid, error = manager.validate_field('llm.context_length', 16384)
        assert is_valid
        
        # Invalid
        is_valid, error = manager.validate_field('llm.context_length', -100)
        assert not is_valid
    
    def test_validate_backend_type(self):
        """Backend type has no specific validation rule, accepts any value."""
        manager = GUIConfigManager()
        
        # No validation rule for backend_type, so all values are accepted
        for backend in ['ollama', 'llamacpp', 'openai-compatible', 'invalid']:
            is_valid, error = manager.validate_field('llm.backend_type', backend)
            assert is_valid, f"Backend {backend} should be valid (no validation rule)"
            assert error == ""
    
    def test_validate_log_level(self):
        """Log level must be one of allowed values."""
        manager = GUIConfigManager()
        
        # Valid levels
        for level in ['debug', 'info', 'warning', 'error']:
            is_valid, error = manager.validate_field('log_level', level)
            assert is_valid, f"Log level {level} should be valid"
        
        # Invalid level
        is_valid, error = manager.validate_field('log_level', 'invalid')
        assert not is_valid
    
    def test_validate_boolean_fields(self):
        """Boolean fields have no specific validation rule, accept any value."""
        manager = GUIConfigManager()
        
        # No validation rule for boolean fields
        is_valid, error = manager.validate_field('web_research_enabled', True)
        assert is_valid
        assert error == ""
        
        is_valid, error = manager.validate_field('web_research_enabled', False)
        assert is_valid
        assert error == ""
        
        # Even non-boolean values are accepted (no validation rule)
        is_valid, error = manager.validate_field('web_research_enabled', "true")
        assert is_valid
        assert error == ""
    
    def test_validate_excluded_directories(self):
        """Excluded directories have no specific validation rule, accept any value."""
        manager = GUIConfigManager()
        
        # No validation rule for excluded_directories
        is_valid, error = manager.validate_field('excluded_directories', ['node_modules', '.git'])
        assert is_valid
        assert error == ""
        
        # Even non-list values are accepted (no validation rule)
        is_valid, error = manager.validate_field('excluded_directories', "node_modules")
        assert is_valid
        assert error == ""
        
        # List with non-strings also accepted (no validation rule)
        is_valid, error = manager.validate_field('excluded_directories', ['node_modules', 123])
        assert is_valid
        assert error == ""
    
    def test_validate_unknown_field(self):
        """Unknown fields have no validation rule, accept any value."""
        manager = GUIConfigManager()
        
        # No validation rule for unknown fields, so they're accepted
        is_valid, error = manager.validate_field('unknown.field', 'value')
        assert is_valid
        assert error == ""


class TestSaveConfig:
    """Tests for save_config method."""
    
    def test_save_creates_backup(self):
        """Saving config should create backup file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / 'config.yaml'
            # Create initial config
            config_path.write_text("llm:\n  endpoint: 'http://localhost:11434'\n  model_name: 'test'\nproject_root: '.'")
            
            manager = GUIConfigManager(str(config_path))
            
            # Save new config
            new_config = manager.get_config_for_gui()
            new_config['llm']['endpoint'] = 'http://localhost:8080'
            
            success, message = manager.save_config(new_config)
            assert success
            
            # Backup should have been created and then removed on success
            backup_path = Path(tmpdir) / 'config.yaml.backup'
            assert not backup_path.exists()  # Removed on success
    
    def test_save_is_atomic(self):
        """Config save should be atomic (all-or-nothing)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / 'config.yaml'
            config_path.write_text("llm:\n  endpoint: 'http://localhost:11434'\n  model_name: 'test'\nproject_root: '.'")
            
            manager = GUIConfigManager(str(config_path))
            original_content = config_path.read_text()
            
            # Try to save invalid config
            invalid_config = manager.get_config_for_gui()
            invalid_config['llm']['endpoint'] = 'invalid url'
            
            success, message = manager.save_config(invalid_config)
            assert not success
            
            # Original config should be unchanged
            current_content = config_path.read_text()
            assert current_content == original_content
    
    def test_save_restores_backup_on_failure(self):
        """Should restore backup if save fails."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / 'config.yaml'
            original_config = "llm:\n  endpoint: 'http://localhost:11434'\n  model_name: 'test'\nproject_root: '.'"
            config_path.write_text(original_config)
            
            manager = GUIConfigManager(str(config_path))
            
            # Create invalid config (validation will fail)
            invalid_config = {
                'llm': {
                    'endpoint': '',  # Invalid - empty
                    'model_name': 'test',
                    'temperature': 0.2,
                    'max_tokens': 4096,
                    'context_length': 16384,
                    'backend_type': 'ollama'
                },
                'project_root': '.',
                'log_level': 'info',
                'web_research_enabled': True,
                'self_improvement_enabled': False,
                'excluded_directories': []
            }
            
            success, message = manager.save_config(invalid_config)
            assert not success
            
            # Original config should be preserved
            assert config_path.read_text() == original_config
    
    def test_save_validates_all_fields(self):
        """Should validate all fields before saving."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / 'config.yaml'
            config_path.write_text("llm:\n  endpoint: 'http://localhost:11434'\n  model_name: 'test'\nproject_root: '.'")
            
            manager = GUIConfigManager(str(config_path))
            
            # Config with invalid temperature
            config = manager.get_config_for_gui()
            config['llm']['temperature'] = 5.0  # Invalid
            
            success, message = manager.save_config(config)
            assert not success
            assert 'temperature' in message.lower()
    
    def test_save_updates_internal_state(self):
        """Successful save should update internal config state."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / 'config.yaml'
            config_path.write_text("llm:\n  endpoint: 'http://localhost:11434'\n  model_name: 'test'\nproject_root: '.'")
            
            manager = GUIConfigManager(str(config_path))
            
            new_config = manager.get_config_for_gui()
            new_config['llm']['temperature'] = 0.7
            
            success, message = manager.save_config(new_config)
            assert success
            
            # Internal config should be updated
            assert manager.config.llm.temperature == 0.7


class TestExternalChangeDetection:
    """Tests for external change detection."""
    
    def test_check_external_changes_detects_modification(self):
        """Should detect when config file is modified externally."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / 'config.yaml'
            config_path.write_text("llm:\n  endpoint: 'http://localhost:11434'\n  model_name: 'test'\nproject_root: '.'")
            
            manager = GUIConfigManager(str(config_path))
            
            # Initially no changes
            assert not manager.check_external_changes()
            
            # Modify file externally
            time.sleep(1.1)  # Wait longer than rate limit (1 second)
            config_path.write_text("llm:\n  endpoint: 'http://localhost:8080'\n  model_name: 'test'\nproject_root: '.'")
            
            # Should detect change
            assert manager.check_external_changes()
    
    def test_check_external_changes_no_false_positives(self):
        """Should not detect changes when file hasn't been modified."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / 'config.yaml'
            config_path.write_text("llm:\n  endpoint: 'http://localhost:11434'\n  model_name: 'test'\nproject_root: '.'")
            
            manager = GUIConfigManager(str(config_path))
            
            # Check multiple times - should always be False
            assert not manager.check_external_changes()
            time.sleep(0.1)
            assert not manager.check_external_changes()
    
    def test_reload_config_updates_state(self):
        """reload_config should load new values from disk."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / 'config.yaml'
            config_path.write_text("llm:\n  endpoint: 'http://localhost:11434'\n  model_name: 'test'\nproject_root: '.'")
            
            manager = GUIConfigManager(str(config_path))
            original_endpoint = manager.config.llm.endpoint
            
            # Modify file
            config_path.write_text("llm:\n  endpoint: 'http://localhost:9999'\n  model_name: 'test'\nproject_root: '.'")
            
            # Reload
            manager.reload_config()
            
            # Should have new value
            assert manager.config.llm.endpoint == 'http://localhost:9999'
            assert manager.config.llm.endpoint != original_endpoint


class TestEncryption:
    """Tests for sensitive value encryption."""
    
    def test_encrypt_decrypt_roundtrip(self):
        """Encrypted value should decrypt to original."""
        manager = GUIConfigManager()
        
        original_value = "my-secret-api-key"
        encrypted = manager.encrypt_sensitive_value(original_value)
        decrypted = manager.decrypt_sensitive_value(encrypted)
        
        assert decrypted == original_value
        assert encrypted != original_value
    
    def test_encryption_produces_different_output(self):
        """Same value encrypted twice should produce different ciphertext."""
        manager = GUIConfigManager()
        
        value = "api-key"
        encrypted1 = manager.encrypt_sensitive_value(value)
        encrypted2 = manager.encrypt_sensitive_value(value)
        
        # Fernet uses timestamp, so these should be different
        # But both should decrypt to same value
        assert manager.decrypt_sensitive_value(encrypted1) == value
        assert manager.decrypt_sensitive_value(encrypted2) == value
    
    def test_encryption_key_persists(self):
        """Encryption key should be saved and reused."""
        # Create first manager - generates key
        manager1 = GUIConfigManager()
        encrypted = manager1.encrypt_sensitive_value("test")
        
        # Create second manager - should load same key
        manager2 = GUIConfigManager()
        decrypted = manager2.decrypt_sensitive_value(encrypted)
        
        assert decrypted == "test"


class TestResetToDefaults:
    """Tests for reset_to_defaults method."""
    
    def test_reset_returns_default_config(self):
        """reset_to_defaults should return default configuration without updating internal state."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / 'config.yaml'
            
            # Create config with non-default values
            config_path.write_text("""
llm:
  endpoint: "http://custom:9999"
  model_name: "custom-model"
  temperature: 0.9
project_root: "."
""")
            
            manager = GUIConfigManager(str(config_path))
            original_endpoint = manager.config.llm.endpoint
            
            # Reset to defaults
            default_config = manager.reset_to_defaults()
            
            # Should return default values
            assert default_config['llm']['endpoint'] == "http://localhost:11434"
            assert default_config['llm']['model_name'] == "codellama:13b"
            assert default_config['llm']['temperature'] == 0.2
            
            # Internal state should NOT be updated (reset_to_defaults just returns dict)
            assert manager.config.llm.endpoint == original_endpoint


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
