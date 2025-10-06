"""
Agent Configuration System

This module provides configuration management utilities for agents,
including environment-specific settings, validation, and loading
from various sources.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, Union

import yaml
from pydantic import BaseModel, Field, ValidationError

from .agent import AgentCapability, AgentConfig


class EnvironmentConfig(BaseModel):
    """Environment-specific configuration."""
    name: str
    debug: bool = False
    log_level: str = "INFO"
    api_timeout: int = 300
    max_concurrent_agents: int = 10
    anthropic_api_key: Optional[str] = None
    storage_path: str = "storage"
    temp_path: str = "/tmp"


class AgentConfigLoader:
    """Utility class for loading and managing agent configurations."""

    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize the configuration loader.

        Args:
            config_dir: Directory containing configuration files
        """
        self.config_dir = config_dir or Path("system/config")
        self._environment_configs: Dict[str, EnvironmentConfig] = {}
        self._agent_configs: Dict[str, AgentConfig] = {}

    def load_environment_config(self, environment: str = "development") -> EnvironmentConfig:
        """
        Load environment-specific configuration.

        Args:
            environment: Environment name (development, production, etc.)

        Returns:
            EnvironmentConfig instance

        Raises:
            FileNotFoundError: If configuration file doesn't exist
            ValidationError: If configuration is invalid
        """
        if environment in self._environment_configs:
            return self._environment_configs[environment]

        config_file = self.config_dir / "environments" / f"{environment}.yml"

        if not config_file.exists():
            raise FileNotFoundError(f"Environment config not found: {config_file}")

        try:
            with open(config_file, 'r') as f:
                config_data = yaml.safe_load(f)

            # Merge with environment variables
            config_data = self._merge_env_vars(config_data)

            env_config = EnvironmentConfig(**config_data)
            self._environment_configs[environment] = env_config
            return env_config

        except yaml.YAMLError as e:
            raise ValidationError(f"Invalid YAML in {config_file}: {e}")
        except Exception as e:
            raise ValidationError(f"Failed to load environment config: {e}")

    def _merge_env_vars(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Merge environment variables into configuration data."""
        env_mappings = {
            "anthropic_api_key": "ANTHROPIC_API_KEY",
            "debug": "DEBUG",
            "log_level": "LOG_LEVEL",
            "storage_path": "STORAGE_PATH",
            "temp_path": "TEMP_PATH",
        }

        for config_key, env_var in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                # Convert string values to appropriate types
                if config_key == "debug":
                    config_data[config_key] = env_value.lower() in ("true", "1", "yes")
                else:
                    config_data[config_key] = env_value

        return config_data

    def create_agent_config(
        self,
        name: str,
        description: str,
        capabilities: List[AgentCapability],
        environment: str = "development",
        **kwargs
    ) -> AgentConfig:
        """
        Create an agent configuration with environment defaults.

        Args:
            name: Agent name
            description: Agent description
            capabilities: List of agent capabilities
            environment: Environment name
            **kwargs: Additional configuration parameters

        Returns:
            AgentConfig instance
        """
        env_config = self.load_environment_config(environment)

        # Set defaults from environment
        config_data = {
            "name": name,
            "description": description,
            "capabilities": capabilities,
            "environment": environment,
            "debug": env_config.debug,
            "timeout_seconds": env_config.api_timeout,
        }

        # Override with provided kwargs
        config_data.update(kwargs)

        return AgentConfig(**config_data)

    def save_agent_config(self, config: AgentConfig, filepath: Optional[Path] = None) -> Path:
        """
        Save agent configuration to file.

        Args:
            config: Agent configuration to save
            filepath: Optional file path (defaults to agent name)

        Returns:
            Path where configuration was saved
        """
        if filepath is None:
            filename = f"{config.name.lower().replace(' ', '_')}_config.yml"
            filepath = self.config_dir / "agents" / filename

        # Ensure directory exists
        filepath.parent.mkdir(parents=True, exist_ok=True)

        config_data = config.model_dump(exclude={"agent_id"})

        with open(filepath, 'w') as f:
            yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)

        return filepath

    def load_agent_config(self, filepath: Path) -> AgentConfig:
        """
        Load agent configuration from file.

        Args:
            filepath: Path to configuration file

        Returns:
            AgentConfig instance

        Raises:
            FileNotFoundError: If configuration file doesn't exist
            ValidationError: If configuration is invalid
        """
        if not filepath.exists():
            raise FileNotFoundError(f"Agent config not found: {filepath}")

        try:
            with open(filepath, 'r') as f:
                config_data = yaml.safe_load(f)

            return AgentConfig(**config_data)

        except yaml.YAMLError as e:
            raise ValidationError(f"Invalid YAML in {filepath}: {e}")
        except Exception as e:
            raise ValidationError(f"Failed to load agent config: {e}")

    def list_available_configs(self) -> List[Path]:
        """
        List all available agent configuration files.

        Returns:
            List of configuration file paths
        """
        config_dir = self.config_dir / "agents"
        if not config_dir.exists():
            return []

        return list(config_dir.glob("*_config.yml"))

    def validate_config(self, config: Union[AgentConfig, Dict[str, Any]]) -> bool:
        """
        Validate agent configuration.

        Args:
            config: Configuration to validate

        Returns:
            True if valid

        Raises:
            ValidationError: If configuration is invalid
        """
        if isinstance(config, dict):
            config = AgentConfig(**config)

        # Additional validation logic
        required_capabilities = {
            AgentCapability.TEXT_PROCESSING,  # All agents need basic text processing
        }

        if not any(cap in config.capabilities for cap in required_capabilities):
            raise ValidationError("Agent must have at least TEXT_PROCESSING capability")

        return True


class ConfigManager:
    """
    Singleton configuration manager for the entire agent system.
    """
    _instance: Optional["ConfigManager"] = None
    _loader: Optional[AgentConfigLoader] = None

    def __new__(cls) -> "ConfigManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._loader is None:
            self._loader = AgentConfigLoader()

    @property
    def loader(self) -> AgentConfigLoader:
        """Get the configuration loader instance."""
        return self._loader

    def get_environment_config(self, environment: str = "development") -> EnvironmentConfig:
        """Get environment configuration."""
        return self._loader.load_environment_config(environment)

    def create_agent_config(self, **kwargs) -> AgentConfig:
        """Create agent configuration with defaults."""
        return self._loader.create_agent_config(**kwargs)


# Global configuration manager instance
config_manager = ConfigManager()