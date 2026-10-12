"""Configuration management for Local AI Development Environment.

This module handles loading, validating, and managing system configuration
from files (YAML/JSON) and environment variables.

Requirements:
- 1.3: Initialize all components using local resources only
- 1.4: Store all configuration on local file system
- 12.1: Support configuration of Local_LLM endpoint
- 12.4: Allow configuration of model parameters
- 12.5: Apply new configuration without restart
- 13.5: Provide configuration option to disable all network access
"""

import os
import json
import yaml
from pathlib import Path
from typing import Optional, Dict, Any, Union
from dataclasses import asdict

from .models import SystemConfig, LLMConfig


class ConfigurationError(Exception):
    """Raised when configuration is invalid or cannot be loaded."""
    pass


class ConfigManager:
    """Manages system configuration with support for file loading and validation."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration manager.
        
        Args:
            config_path: Optional path to configuration file. If not provided,
                        will look for config in default locations.
        """
        self._config_path = config_path
        self._config: Optional[SystemConfig] = None
    
    def load_config(self, config_path: Optional[str] = None) -> SystemConfig:
        """Load configuration from file with environment variable overrides.
        
        Args:
            config_path: Path to configuration file (YAML or JSON).
                        If None, uses path provided during initialization.
        
        Returns:
            SystemConfig instance with loaded and validated configuration.
        
        Raises:
            ConfigurationError: If configuration file is invalid or cannot be loaded.
        
        Requirements: 1.3, 1.4, 12.1, 12.4, 12.5
        """
        path = config_path or self._config_path
        
        if path is None:
            # Try default locations
            path = self._find_default_config()
        
        if path is None:
            # No config file found, use defaults with environment overrides
            config_dict = self._get_default_config_dict()
        else:
            # Load config from file
            config_dict = self._load_config_file(path)
        
        # Apply environment variable overrides
        config_dict = self._apply_env_overrides(config_dict)
        
        # Validate and create SystemConfig
        self._config = self._create_system_config(config_dict)
        
        return self._config
    
    def get_config(self) -> SystemConfig:
        """Get current configuration.
        
        Returns:
            Current SystemConfig instance.
        
        Raises:
            ConfigurationError: If configuration has not been loaded yet.
        """
        if self._config is None:
            raise ConfigurationError("Configuration not loaded. Call load_config() first.")
        return self._config
    
    def reload_config(self) -> SystemConfig:
        """Reload configuration from file and environment.
        
        Returns:
            Updated SystemConfig instance.
        
        Requirements: 12.5 - Apply new configuration without restart
        """
        return self.load_config(self._config_path)
    
    def validate_config(self, config: SystemConfig) -> bool:
        """Validate configuration values.
        
        Args:
            config: SystemConfig instance to validate.
        
        Returns:
            True if configuration is valid.
        
        Raises:
            ConfigurationError: If configuration is invalid with specific error message.
        
        Requirements: 12.1, 12.4
        """
        # Validate LLM configuration
        self._validate_llm_config(config.llm)
        
        # Validate project root
        if not config.project_root:
            raise ConfigurationError("project_root must be specified")
        
        project_path = Path(config.project_root)
        if not project_path.exists():
            raise ConfigurationError(f"project_root does not exist: {config.project_root}")
        if not project_path.is_dir():
            raise ConfigurationError(f"project_root is not a directory: {config.project_root}")
        
        # Validate log level
        valid_log_levels = ["debug", "info", "warning", "error"]
        if config.log_level.lower() not in valid_log_levels:
            raise ConfigurationError(
                f"Invalid log_level '{config.log_level}'. Must be one of: {', '.join(valid_log_levels)}"
            )
        
        # Validate excluded directories (must be non-empty list)
        if not isinstance(config.excluded_directories, list):
            raise ConfigurationError("excluded_directories must be a list")
        
        return True
    
    def save_config(self, config: SystemConfig, output_path: str, format: str = "yaml") -> None:
        """Save configuration to file.
        
        Args:
            config: SystemConfig instance to save.
            output_path: Path where configuration file will be written.
            format: Output format, either "yaml" or "json".
        
        Raises:
            ConfigurationError: If format is invalid or file cannot be written.
        
        Requirements: 1.4 - Store all configuration on local file system
        """
        if format not in ["yaml", "json"]:
            raise ConfigurationError(f"Invalid format '{format}'. Must be 'yaml' or 'json'.")
        
        # Convert config to dictionary
        config_dict = {
            "llm": asdict(config.llm),
            "project_root": config.project_root,
            "log_level": config.log_level,
            "web_research_enabled": config.web_research_enabled,
            "self_improvement_enabled": config.self_improvement_enabled,
            "excluded_directories": config.excluded_directories
        }
        
        try:
            with open(output_path, 'w') as f:
                if format == "yaml":
                    yaml.safe_dump(config_dict, f, default_flow_style=False, sort_keys=False)
                else:  # json
                    json.dump(config_dict, f, indent=2)
        except Exception as e:
            raise ConfigurationError(f"Failed to save configuration to {output_path}: {e}")
    
    # Private helper methods
    
    def _find_default_config(self) -> Optional[str]:
        """Search for configuration file in default locations.
        
        Returns:
            Path to configuration file if found, None otherwise.
        """
        # Check current directory
        for filename in ["config.yaml", "config.yml", "config.json"]:
            if Path(filename).exists():
                return filename
        
        # Check ~/.local_ai_dev/
        home_config_dir = Path.home() / ".local_ai_dev"
        if home_config_dir.exists():
            for filename in ["config.yaml", "config.yml", "config.json"]:
                config_file = home_config_dir / filename
                if config_file.exists():
                    return str(config_file)
        
        return None
    
    def _load_config_file(self, path: str) -> Dict[str, Any]:
        """Load configuration from YAML or JSON file.
        
        Args:
            path: Path to configuration file.
        
        Returns:
            Dictionary with configuration values.
        
        Raises:
            ConfigurationError: If file cannot be loaded or parsed.
        """
        file_path = Path(path)
        
        if not file_path.exists():
            raise ConfigurationError(f"Configuration file not found: {path}")
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                
                # Determine format from extension
                if file_path.suffix.lower() in ['.yaml', '.yml']:
                    return yaml.safe_load(content) or {}
                elif file_path.suffix.lower() == '.json':
                    return json.loads(content)
                else:
                    # Try to detect format
                    try:
                        return json.loads(content)
                    except json.JSONDecodeError:
                        try:
                            return yaml.safe_load(content) or {}
                        except yaml.YAMLError:
                            raise ConfigurationError(
                                f"Cannot determine format of configuration file: {path}. "
                                "Must be valid YAML or JSON."
                            )
        except ConfigurationError:
            raise
        except Exception as e:
            raise ConfigurationError(f"Failed to load configuration from {path}: {e}")
    
    def _get_default_config_dict(self) -> Dict[str, Any]:
        """Get default configuration values.
        
        Returns:
            Dictionary with default configuration.
        """
        return {
            "llm": {
                "endpoint": "http://localhost:11434",
                "model_name": "codellama:13b",
                "temperature": 0.2,
                "max_tokens": 4096,
                "context_length": 16384,
                "backend_type": "ollama"
            },
            "project_root": os.getcwd(),
            "log_level": "info",
            "web_research_enabled": True,
            "self_improvement_enabled": False,
            "excluded_directories": [
                "node_modules", ".git", "__pycache__", ".pytest_cache",
                "venv", ".venv", "build", "dist", ".hypothesis"
            ]
        }
    
    def _apply_env_overrides(self, config_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Apply environment variable overrides to configuration.
        
        Environment variables:
            LOCAL_AI_LLM_ENDPOINT: Override LLM endpoint
            LOCAL_AI_LLM_MODEL: Override LLM model name
            LOCAL_AI_LLM_TEMPERATURE: Override LLM temperature
            LOCAL_AI_LLM_MAX_TOKENS: Override max tokens
            LOCAL_AI_LLM_CONTEXT_LENGTH: Override context length
            LOCAL_AI_LLM_BACKEND: Override backend type
            LOCAL_AI_PROJECT_ROOT: Override project root
            LOCAL_AI_LOG_LEVEL: Override log level
            LOCAL_AI_WEB_RESEARCH: Enable/disable web research (true/false)
            LOCAL_AI_SELF_IMPROVEMENT: Enable/disable self-improvement (true/false)
            LOCAL_AI_NETWORK_DISABLED: Disable all network access (true/false)
        
        Args:
            config_dict: Base configuration dictionary.
        
        Returns:
            Configuration dictionary with environment overrides applied.
        
        Requirements: 12.4, 13.5
        """
        # Ensure llm section exists
        if "llm" not in config_dict:
            config_dict["llm"] = {}
        
        # LLM configuration overrides
        if os.getenv("LOCAL_AI_LLM_ENDPOINT"):
            config_dict["llm"]["endpoint"] = os.getenv("LOCAL_AI_LLM_ENDPOINT")
        
        if os.getenv("LOCAL_AI_LLM_MODEL"):
            config_dict["llm"]["model_name"] = os.getenv("LOCAL_AI_LLM_MODEL")
        
        if os.getenv("LOCAL_AI_LLM_TEMPERATURE"):
            try:
                config_dict["llm"]["temperature"] = float(os.getenv("LOCAL_AI_LLM_TEMPERATURE"))
            except ValueError:
                pass  # Ignore invalid values
        
        if os.getenv("LOCAL_AI_LLM_MAX_TOKENS"):
            try:
                config_dict["llm"]["max_tokens"] = int(os.getenv("LOCAL_AI_LLM_MAX_TOKENS"))
            except ValueError:
                pass
        
        if os.getenv("LOCAL_AI_LLM_CONTEXT_LENGTH"):
            try:
                config_dict["llm"]["context_length"] = int(os.getenv("LOCAL_AI_LLM_CONTEXT_LENGTH"))
            except ValueError:
                pass
        
        if os.getenv("LOCAL_AI_LLM_BACKEND"):
            config_dict["llm"]["backend_type"] = os.getenv("LOCAL_AI_LLM_BACKEND")
        
        # System configuration overrides
        if os.getenv("LOCAL_AI_PROJECT_ROOT"):
            config_dict["project_root"] = os.getenv("LOCAL_AI_PROJECT_ROOT")
        
        if os.getenv("LOCAL_AI_LOG_LEVEL"):
            config_dict["log_level"] = os.getenv("LOCAL_AI_LOG_LEVEL")
        
        if os.getenv("LOCAL_AI_WEB_RESEARCH"):
            config_dict["web_research_enabled"] = os.getenv("LOCAL_AI_WEB_RESEARCH").lower() in ["true", "1", "yes"]
        
        if os.getenv("LOCAL_AI_SELF_IMPROVEMENT"):
            config_dict["self_improvement_enabled"] = os.getenv("LOCAL_AI_SELF_IMPROVEMENT").lower() in ["true", "1", "yes"]
        
        # Network disabled override (Requirement 13.5)
        if os.getenv("LOCAL_AI_NETWORK_DISABLED"):
            if os.getenv("LOCAL_AI_NETWORK_DISABLED").lower() in ["true", "1", "yes"]:
                config_dict["web_research_enabled"] = False
        
        return config_dict
    
    def _create_system_config(self, config_dict: Dict[str, Any]) -> SystemConfig:
        """Create and validate SystemConfig from dictionary.
        
        Args:
            config_dict: Configuration dictionary.
        
        Returns:
            Validated SystemConfig instance.
        
        Raises:
            ConfigurationError: If configuration is invalid.
        """
        try:
            # Extract LLM config
            llm_dict = config_dict.get("llm", {})
            llm_config = LLMConfig(
                endpoint=llm_dict.get("endpoint", "http://localhost:11434"),
                model_name=llm_dict.get("model_name", "codellama:13b"),
                temperature=float(llm_dict.get("temperature", 0.2)),
                max_tokens=int(llm_dict.get("max_tokens", 4096)),
                context_length=int(llm_dict.get("context_length", 16384)),
                backend_type=llm_dict.get("backend_type", "ollama")
            )
            
            # Create system config
            system_config = SystemConfig(
                llm=llm_config,
                project_root=config_dict.get("project_root", os.getcwd()),
                log_level=config_dict.get("log_level", "info"),
                web_research_enabled=config_dict.get("web_research_enabled", True),
                self_improvement_enabled=config_dict.get("self_improvement_enabled", False),
                excluded_directories=config_dict.get("excluded_directories", [
                    "node_modules", ".git", "__pycache__", ".pytest_cache",
                    "venv", ".venv", "build", "dist", ".hypothesis"
                ])
            )
            
            # Validate configuration
            self.validate_config(system_config)
            
            return system_config
            
        except (TypeError, ValueError) as e:
            raise ConfigurationError(f"Invalid configuration values: {e}")
    
    def _validate_llm_config(self, llm_config: LLMConfig) -> None:
        """Validate LLM configuration.
        
        Args:
            llm_config: LLMConfig instance to validate.
        
        Raises:
            ConfigurationError: If LLM configuration is invalid.
        
        Requirements: 12.1, 12.4
        """
        # Validate endpoint
        if not llm_config.endpoint:
            raise ConfigurationError("LLM endpoint must be specified")
        
        if not llm_config.endpoint.startswith(("http://", "https://")):
            raise ConfigurationError(
                f"LLM endpoint must start with http:// or https://: {llm_config.endpoint}"
            )
        
        # Validate model name
        if not llm_config.model_name:
            raise ConfigurationError("LLM model_name must be specified")
        
        # Validate temperature (0.0 to 2.0 is typical range)
        if not (0.0 <= llm_config.temperature <= 2.0):
            raise ConfigurationError(
                f"LLM temperature must be between 0.0 and 2.0, got: {llm_config.temperature}"
            )
        
        # Validate max_tokens (must be positive)
        if llm_config.max_tokens <= 0:
            raise ConfigurationError(
                f"LLM max_tokens must be positive, got: {llm_config.max_tokens}"
            )
        
        # Validate context_length (must be positive and >= max_tokens)
        if llm_config.context_length <= 0:
            raise ConfigurationError(
                f"LLM context_length must be positive, got: {llm_config.context_length}"
            )
        
        if llm_config.context_length < llm_config.max_tokens:
            raise ConfigurationError(
                f"LLM context_length ({llm_config.context_length}) must be >= "
                f"max_tokens ({llm_config.max_tokens})"
            )
        
        # Validate backend type
        valid_backends = ["ollama", "llamacpp", "openai-compatible"]
        if llm_config.backend_type not in valid_backends:
            raise ConfigurationError(
                f"Invalid LLM backend_type '{llm_config.backend_type}'. "
                f"Must be one of: {', '.join(valid_backends)}"
            )


def load_config(config_path: Optional[str] = None) -> SystemConfig:
    """Convenience function to load configuration.
    
    Args:
        config_path: Optional path to configuration file.
    
    Returns:
        SystemConfig instance with loaded and validated configuration.
    
    Raises:
        ConfigurationError: If configuration is invalid or cannot be loaded.
    """
    manager = ConfigManager(config_path)
    return manager.load_config()
