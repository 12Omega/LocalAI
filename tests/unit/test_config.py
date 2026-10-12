"""Unit tests for configuration management.

Tests configuration loading from files (YAML/JSON), validation,
environment variable overrides, and error handling.

Requirements tested:
- 1.3: Initialize all components using local resources only
- 1.4: Store all configuration on local file system
- 12.1: Support configuration of Local_LLM endpoint
- 12.4: Allow configuration of model parameters
- 12.5: Apply new configuration without restart
- 13.5: Provide configuration option to disable all network access
"""

import pytest
import os
import json
import yaml
import tempfile
from pathlib import Path

from src.core.config import ConfigManager, ConfigurationError, load_config
from src.core.models import SystemConfig, LLMConfig


class TestConfigManager:
    """Test ConfigManager class."""
    
    def test_load_default_config_no_file(self, tmp_path, monkeypatch):
        """Test loading default configuration when no file exists."""
        # Change to temp directory where no config file exists
        monkeypatch.chdir(tmp_path)
        
        manager = ConfigManager()
        config = manager.load_config()
        
        # Verify default values
        assert config.llm.endpoint == "http://localhost:11434"
        assert config.llm.model_name == "codellama:13b"
        assert config.llm.temperature == 0.2
        assert config.llm.max_tokens == 4096
        assert config.llm.context_length == 16384
        assert config.llm.backend_type == "ollama"
        assert config.log_level == "info"
        assert config.web_research_enabled is True
        assert config.self_improvement_enabled is False
        assert "node_modules" in config.excluded_directories
    
    def test_load_config_from_yaml(self, tmp_path):
        """Test loading configuration from YAML file."""
        config_file = tmp_path / "config.yaml"
        config_data = {
            "llm": {
                "endpoint": "http://localhost:8080",
                "model_name": "llama2:7b",
                "temperature": 0.5,
                "max_tokens": 2048,
                "context_length": 8192,
                "backend_type": "llamacpp"
            },
            "project_root": str(tmp_path),
            "log_level": "debug",
            "web_research_enabled": False,
            "self_improvement_enabled": True,
            "excluded_directories": [".git", "build"]
        }
        
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        manager = ConfigManager(str(config_file))
        config = manager.load_config()
        
        assert config.llm.endpoint == "http://localhost:8080"
        assert config.llm.model_name == "llama2:7b"
        assert config.llm.temperature == 0.5
        assert config.llm.max_tokens == 2048
        assert config.llm.context_length == 8192
        assert config.llm.backend_type == "llamacpp"
        assert config.project_root == str(tmp_path)
        assert config.log_level == "debug"
        assert config.web_research_enabled is False
        assert config.self_improvement_enabled is True
        assert config.excluded_directories == [".git", "build"]
    
    def test_load_config_from_json(self, tmp_path):
        """Test loading configuration from JSON file."""
        config_file = tmp_path / "config.json"
        config_data = {
            "llm": {
                "endpoint": "http://localhost:9090",
                "model_name": "mistral:7b",
                "temperature": 0.3,
                "max_tokens": 3000,
                "context_length": 12000,
                "backend_type": "openai-compatible"
            },
            "project_root": str(tmp_path),
            "log_level": "warning",
            "web_research_enabled": True,
            "self_improvement_enabled": False,
            "excluded_directories": ["venv"]
        }
        
        with open(config_file, 'w') as f:
            json.dump(config_data, f)
        
        manager = ConfigManager(str(config_file))
        config = manager.load_config()
        
        assert config.llm.endpoint == "http://localhost:9090"
        assert config.llm.model_name == "mistral:7b"
        assert config.llm.temperature == 0.3
        assert config.log_level == "warning"
    
    def test_env_override_llm_endpoint(self, tmp_path, monkeypatch):
        """Test environment variable override for LLM endpoint."""
        monkeypatch.setenv("LOCAL_AI_LLM_ENDPOINT", "http://custom:5000")
        monkeypatch.chdir(tmp_path)
        
        manager = ConfigManager()
        config = manager.load_config()
        
        assert config.llm.endpoint == "http://custom:5000"
    
    def test_env_override_llm_model(self, tmp_path, monkeypatch):
        """Test environment variable override for LLM model."""
        monkeypatch.setenv("LOCAL_AI_LLM_MODEL", "custom-model:latest")
        monkeypatch.chdir(tmp_path)
        
        manager = ConfigManager()
        config = manager.load_config()
        
        assert config.llm.model_name == "custom-model:latest"
    
    def test_env_override_temperature(self, tmp_path, monkeypatch):
        """Test environment variable override for temperature."""
        monkeypatch.setenv("LOCAL_AI_LLM_TEMPERATURE", "0.8")
        monkeypatch.chdir(tmp_path)
        
        manager = ConfigManager()
        config = manager.load_config()
        
        assert config.llm.temperature == 0.8
    
    def test_env_override_max_tokens(self, tmp_path, monkeypatch):
        """Test environment variable override for max tokens."""
        monkeypatch.setenv("LOCAL_AI_LLM_MAX_TOKENS", "8000")
        monkeypatch.chdir(tmp_path)
        
        manager = ConfigManager()
        config = manager.load_config()
        
        assert config.llm.max_tokens == 8000
    
    def test_env_override_context_length(self, tmp_path, monkeypatch):
        """Test environment variable override for context length."""
        monkeypatch.setenv("LOCAL_AI_LLM_CONTEXT_LENGTH", "32000")
        monkeypatch.chdir(tmp_path)
        
        manager = ConfigManager()
        config = manager.load_config()
        
        assert config.llm.context_length == 32000
    
    def test_env_override_backend_type(self, tmp_path, monkeypatch):
        """Test environment variable override for backend type."""
        monkeypatch.setenv("LOCAL_AI_LLM_BACKEND", "llamacpp")
        monkeypatch.chdir(tmp_path)
        
        manager = ConfigManager()
        config = manager.load_config()
        
        assert config.llm.backend_type == "llamacpp"
    
    def test_env_override_project_root(self, tmp_path, monkeypatch):
        """Test environment variable override for project root."""
        custom_root = tmp_path / "custom"
        custom_root.mkdir()
        monkeypatch.setenv("LOCAL_AI_PROJECT_ROOT", str(custom_root))
        
        manager = ConfigManager()
        config = manager.load_config()
        
        assert config.project_root == str(custom_root)
    
    def test_env_override_log_level(self, tmp_path, monkeypatch):
        """Test environment variable override for log level."""
        monkeypatch.setenv("LOCAL_AI_LOG_LEVEL", "error")
        monkeypatch.chdir(tmp_path)
        
        manager = ConfigManager()
        config = manager.load_config()
        
        assert config.log_level == "error"
    
    def test_env_override_web_research(self, tmp_path, monkeypatch):
        """Test environment variable override for web research."""
        monkeypatch.setenv("LOCAL_AI_WEB_RESEARCH", "false")
        monkeypatch.chdir(tmp_path)
        
        manager = ConfigManager()
        config = manager.load_config()
        
        assert config.web_research_enabled is False
    
    def test_env_override_self_improvement(self, tmp_path, monkeypatch):
        """Test environment variable override for self improvement."""
        monkeypatch.setenv("LOCAL_AI_SELF_IMPROVEMENT", "true")
        monkeypatch.chdir(tmp_path)
        
        manager = ConfigManager()
        config = manager.load_config()
        
        assert config.self_improvement_enabled is True
    
    def test_env_network_disabled_overrides_web_research(self, tmp_path, monkeypatch):
        """Test that LOCAL_AI_NETWORK_DISABLED disables web research.
        
        Requirement 13.5: Provide configuration option to disable all network access.
        """
        monkeypatch.setenv("LOCAL_AI_NETWORK_DISABLED", "true")
        monkeypatch.chdir(tmp_path)
        
        manager = ConfigManager()
        config = manager.load_config()
        
        assert config.web_research_enabled is False
    
    def test_env_override_combines_with_file_config(self, tmp_path, monkeypatch):
        """Test that environment variables override file configuration."""
        config_file = tmp_path / "config.yaml"
        config_data = {
            "llm": {
                "endpoint": "http://localhost:11434",
                "model_name": "codellama:13b",
                "temperature": 0.2
            },
            "project_root": str(tmp_path),
            "log_level": "info"
        }
        
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        # Override endpoint via environment
        monkeypatch.setenv("LOCAL_AI_LLM_ENDPOINT", "http://override:8080")
        
        manager = ConfigManager(str(config_file))
        config = manager.load_config()
        
        # Environment override should take precedence
        assert config.llm.endpoint == "http://override:8080"
        # Other values from file should remain
        assert config.llm.model_name == "codellama:13b"
        assert config.llm.temperature == 0.2
    
    def test_get_config_before_load_raises_error(self):
        """Test that get_config() raises error before load_config()."""
        manager = ConfigManager()
        
        with pytest.raises(ConfigurationError, match="Configuration not loaded"):
            manager.get_config()
    
    def test_get_config_after_load(self, tmp_path, monkeypatch):
        """Test that get_config() returns config after load_config()."""
        monkeypatch.chdir(tmp_path)
        
        manager = ConfigManager()
        loaded_config = manager.load_config()
        retrieved_config = manager.get_config()
        
        assert retrieved_config == loaded_config
    
    def test_reload_config(self, tmp_path, monkeypatch):
        """Test reloading configuration.
        
        Requirement 12.5: Apply new configuration without restart.
        """
        config_file = tmp_path / "config.yaml"
        config_data = {
            "llm": {"endpoint": "http://localhost:11434", "model_name": "model1"},
            "project_root": str(tmp_path),
            "log_level": "info"
        }
        
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        manager = ConfigManager(str(config_file))
        config1 = manager.load_config()
        assert config1.llm.model_name == "model1"
        
        # Modify config file
        config_data["llm"]["model_name"] = "model2"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        # Reload config
        config2 = manager.reload_config()
        assert config2.llm.model_name == "model2"
    
    def test_save_config_yaml(self, tmp_path):
        """Test saving configuration to YAML file."""
        llm_config = LLMConfig(
            endpoint="http://localhost:11434",
            model_name="test-model",
            temperature=0.5,
            max_tokens=2048,
            context_length=8192,
            backend_type="ollama"
        )
        config = SystemConfig(
            llm=llm_config,
            project_root=str(tmp_path),
            log_level="debug",
            web_research_enabled=False,
            self_improvement_enabled=True,
            excluded_directories=[".git"]
        )
        
        output_file = tmp_path / "output.yaml"
        manager = ConfigManager()
        manager.save_config(config, str(output_file), format="yaml")
        
        # Verify file was created and can be loaded
        assert output_file.exists()
        
        with open(output_file, 'r') as f:
            loaded = yaml.safe_load(f)
        
        assert loaded["llm"]["endpoint"] == "http://localhost:11434"
        assert loaded["llm"]["model_name"] == "test-model"
        assert loaded["log_level"] == "debug"
        assert loaded["web_research_enabled"] is False
    
    def test_save_config_json(self, tmp_path):
        """Test saving configuration to JSON file."""
        llm_config = LLMConfig(
            endpoint="http://localhost:11434",
            model_name="test-model"
        )
        config = SystemConfig(
            llm=llm_config,
            project_root=str(tmp_path)
        )
        
        output_file = tmp_path / "output.json"
        manager = ConfigManager()
        manager.save_config(config, str(output_file), format="json")
        
        # Verify file was created and can be loaded
        assert output_file.exists()
        
        with open(output_file, 'r') as f:
            loaded = json.load(f)
        
        assert loaded["llm"]["endpoint"] == "http://localhost:11434"
        assert loaded["llm"]["model_name"] == "test-model"
    
    def test_save_config_invalid_format(self, tmp_path):
        """Test that save_config raises error for invalid format."""
        llm_config = LLMConfig(endpoint="http://localhost:11434", model_name="test")
        config = SystemConfig(llm=llm_config, project_root=str(tmp_path))
        
        manager = ConfigManager()
        
        with pytest.raises(ConfigurationError, match="Invalid format"):
            manager.save_config(config, str(tmp_path / "output.txt"), format="txt")


class TestConfigValidation:
    """Test configuration validation."""
    
    def test_validate_valid_config(self, tmp_path):
        """Test validation of valid configuration."""
        llm_config = LLMConfig(
            endpoint="http://localhost:11434",
            model_name="codellama:13b",
            temperature=0.2,
            max_tokens=4096,
            context_length=16384,
            backend_type="ollama"
        )
        config = SystemConfig(
            llm=llm_config,
            project_root=str(tmp_path),
            log_level="info"
        )
        
        manager = ConfigManager()
        assert manager.validate_config(config) is True
    
    def test_validate_empty_llm_endpoint(self, tmp_path):
        """Test validation fails for empty LLM endpoint."""
        llm_config = LLMConfig(
            endpoint="",
            model_name="codellama:13b"
        )
        config = SystemConfig(llm=llm_config, project_root=str(tmp_path))
        
        manager = ConfigManager()
        
        with pytest.raises(ConfigurationError, match="endpoint must be specified"):
            manager.validate_config(config)
    
    def test_validate_invalid_llm_endpoint_protocol(self, tmp_path):
        """Test validation fails for invalid LLM endpoint protocol."""
        llm_config = LLMConfig(
            endpoint="ftp://localhost:11434",
            model_name="codellama:13b"
        )
        config = SystemConfig(llm=llm_config, project_root=str(tmp_path))
        
        manager = ConfigManager()
        
        with pytest.raises(ConfigurationError, match="must start with http"):
            manager.validate_config(config)
    
    def test_validate_empty_model_name(self, tmp_path):
        """Test validation fails for empty model name."""
        llm_config = LLMConfig(
            endpoint="http://localhost:11434",
            model_name=""
        )
        config = SystemConfig(llm=llm_config, project_root=str(tmp_path))
        
        manager = ConfigManager()
        
        with pytest.raises(ConfigurationError, match="model_name must be specified"):
            manager.validate_config(config)
    
    def test_validate_temperature_out_of_range_low(self, tmp_path):
        """Test validation fails for temperature below 0.0."""
        llm_config = LLMConfig(
            endpoint="http://localhost:11434",
            model_name="codellama:13b",
            temperature=-0.1
        )
        config = SystemConfig(llm=llm_config, project_root=str(tmp_path))
        
        manager = ConfigManager()
        
        with pytest.raises(ConfigurationError, match="temperature must be between"):
            manager.validate_config(config)
    
    def test_validate_temperature_out_of_range_high(self, tmp_path):
        """Test validation fails for temperature above 2.0."""
        llm_config = LLMConfig(
            endpoint="http://localhost:11434",
            model_name="codellama:13b",
            temperature=2.5
        )
        config = SystemConfig(llm=llm_config, project_root=str(tmp_path))
        
        manager = ConfigManager()
        
        with pytest.raises(ConfigurationError, match="temperature must be between"):
            manager.validate_config(config)
    
    def test_validate_negative_max_tokens(self, tmp_path):
        """Test validation fails for negative max_tokens."""
        llm_config = LLMConfig(
            endpoint="http://localhost:11434",
            model_name="codellama:13b",
            max_tokens=-100
        )
        config = SystemConfig(llm=llm_config, project_root=str(tmp_path))
        
        manager = ConfigManager()
        
        with pytest.raises(ConfigurationError, match="max_tokens must be positive"):
            manager.validate_config(config)
    
    def test_validate_negative_context_length(self, tmp_path):
        """Test validation fails for negative context_length."""
        llm_config = LLMConfig(
            endpoint="http://localhost:11434",
            model_name="codellama:13b",
            context_length=-1000
        )
        config = SystemConfig(llm=llm_config, project_root=str(tmp_path))
        
        manager = ConfigManager()
        
        with pytest.raises(ConfigurationError, match="context_length must be positive"):
            manager.validate_config(config)
    
    def test_validate_context_length_less_than_max_tokens(self, tmp_path):
        """Test validation fails when context_length < max_tokens."""
        llm_config = LLMConfig(
            endpoint="http://localhost:11434",
            model_name="codellama:13b",
            max_tokens=8000,
            context_length=4000
        )
        config = SystemConfig(llm=llm_config, project_root=str(tmp_path))
        
        manager = ConfigManager()
        
        with pytest.raises(ConfigurationError, match="context_length.*must be >= max_tokens"):
            manager.validate_config(config)
    
    def test_validate_invalid_backend_type(self, tmp_path):
        """Test validation fails for invalid backend type."""
        llm_config = LLMConfig(
            endpoint="http://localhost:11434",
            model_name="codellama:13b",
            backend_type="invalid-backend"
        )
        config = SystemConfig(llm=llm_config, project_root=str(tmp_path))
        
        manager = ConfigManager()
        
        with pytest.raises(ConfigurationError, match="Invalid LLM backend_type"):
            manager.validate_config(config)
    
    def test_validate_empty_project_root(self):
        """Test validation fails for empty project root."""
        llm_config = LLMConfig(
            endpoint="http://localhost:11434",
            model_name="codellama:13b"
        )
        config = SystemConfig(llm=llm_config, project_root="")
        
        manager = ConfigManager()
        
        with pytest.raises(ConfigurationError, match="project_root must be specified"):
            manager.validate_config(config)
    
    def test_validate_nonexistent_project_root(self):
        """Test validation fails for nonexistent project root."""
        llm_config = LLMConfig(
            endpoint="http://localhost:11434",
            model_name="codellama:13b"
        )
        config = SystemConfig(llm=llm_config, project_root="/nonexistent/path/xyz")
        
        manager = ConfigManager()
        
        with pytest.raises(ConfigurationError, match="does not exist"):
            manager.validate_config(config)
    
    def test_validate_project_root_is_file(self, tmp_path):
        """Test validation fails when project root is a file, not directory."""
        test_file = tmp_path / "file.txt"
        test_file.write_text("test")
        
        llm_config = LLMConfig(
            endpoint="http://localhost:11434",
            model_name="codellama:13b"
        )
        config = SystemConfig(llm=llm_config, project_root=str(test_file))
        
        manager = ConfigManager()
        
        with pytest.raises(ConfigurationError, match="not a directory"):
            manager.validate_config(config)
    
    def test_validate_invalid_log_level(self, tmp_path):
        """Test validation fails for invalid log level."""
        llm_config = LLMConfig(
            endpoint="http://localhost:11434",
            model_name="codellama:13b"
        )
        config = SystemConfig(
            llm=llm_config,
            project_root=str(tmp_path),
            log_level="invalid"
        )
        
        manager = ConfigManager()
        
        with pytest.raises(ConfigurationError, match="Invalid log_level"):
            manager.validate_config(config)
    
    def test_validate_all_log_levels(self, tmp_path):
        """Test validation passes for all valid log levels."""
        llm_config = LLMConfig(
            endpoint="http://localhost:11434",
            model_name="codellama:13b"
        )
        
        manager = ConfigManager()
        
        for level in ["debug", "info", "warning", "error", "DEBUG", "INFO", "WARNING", "ERROR"]:
            config = SystemConfig(
                llm=llm_config,
                project_root=str(tmp_path),
                log_level=level
            )
            assert manager.validate_config(config) is True


class TestConfigLoadingErrors:
    """Test error handling during configuration loading."""
    
    def test_load_nonexistent_file(self):
        """Test loading nonexistent configuration file."""
        manager = ConfigManager("/nonexistent/config.yaml")
        
        with pytest.raises(ConfigurationError, match="not found"):
            manager.load_config()
    
    def test_load_invalid_yaml(self, tmp_path):
        """Test loading invalid YAML file."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("invalid: yaml: content: [unclosed")
        
        manager = ConfigManager(str(config_file))
        
        with pytest.raises(ConfigurationError, match="Failed to load"):
            manager.load_config()
    
    def test_load_invalid_json(self, tmp_path):
        """Test loading invalid JSON file."""
        config_file = tmp_path / "config.json"
        config_file.write_text('{"invalid": json content}')
        
        manager = ConfigManager(str(config_file))
        
        with pytest.raises(ConfigurationError, match="Failed to load"):
            manager.load_config()
    
    def test_load_config_with_invalid_values(self, tmp_path):
        """Test loading configuration with invalid values triggers validation error."""
        config_file = tmp_path / "config.yaml"
        config_data = {
            "llm": {
                "endpoint": "ftp://invalid",  # Invalid protocol
                "model_name": "test"
            },
            "project_root": str(tmp_path)
        }
        
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        manager = ConfigManager(str(config_file))
        
        with pytest.raises(ConfigurationError, match="must start with http"):
            manager.load_config()


class TestConvenienceFunction:
    """Test the convenience load_config() function."""
    
    def test_load_config_function(self, tmp_path, monkeypatch):
        """Test the convenience load_config() function."""
        monkeypatch.chdir(tmp_path)
        
        config = load_config()
        
        assert isinstance(config, SystemConfig)
        assert config.llm.endpoint == "http://localhost:11434"
    
    def test_load_config_function_with_path(self, tmp_path):
        """Test load_config() function with explicit path."""
        config_file = tmp_path / "config.yaml"
        config_data = {
            "llm": {"endpoint": "http://custom:8080", "model_name": "custom-model"},
            "project_root": str(tmp_path)
        }
        
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        config = load_config(str(config_file))
        
        assert config.llm.endpoint == "http://custom:8080"
        assert config.llm.model_name == "custom-model"
