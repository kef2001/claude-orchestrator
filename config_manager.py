#!/usr/bin/env python3
"""
Configuration Management System for Claude Orchestrator
Provides centralized configuration loading, validation, and management
"""

import json
import os
import logging
from typing import Dict, Any, Optional, Union, List
from dataclasses import dataclass, field
from pathlib import Path
from jsonschema import validate, ValidationError
import yaml
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class ConfigValidationResult:
    """Result of configuration validation"""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def add_error(self, error: str):
        """Add an error to the validation result"""
        self.errors.append(error)
        self.is_valid = False
        
    def add_warning(self, warning: str):
        """Add a warning to the validation result"""
        self.warnings.append(warning)


class ConfigurationManager:
    """
    Enhanced configuration management system with validation, 
    environment variable support, and hierarchical configuration
    """
    
    CONFIG_SCHEMA = {
        "type": "object",
        "properties": {
            "models": {
                "type": "object",
                "properties": {
                    "manager": {
                        "type": "object",
                        "properties": {
                            "model": {"type": "string"},
                            "description": {"type": "string"}
                        },
                        "required": ["model"]
                    },
                    "worker": {
                        "type": "object",
                        "properties": {
                            "model": {"type": "string"},
                            "description": {"type": "string"}
                        },
                        "required": ["model"]
                    }
                },
                "required": ["manager", "worker"]
            },
            "execution": {
                "type": "object",
                "properties": {
                    "max_workers": {"type": "integer", "minimum": 1, "maximum": 20},
                    "worker_timeout": {"type": "integer", "minimum": 10},
                    "manager_timeout": {"type": "integer", "minimum": 10},
                    "task_queue_timeout": {"type": "number", "minimum": 0.1},
                    "max_turns": {"type": ["integer", "null"], "minimum": 1},
                    "bash_default_timeout_ms": {"type": "integer", "minimum": 1000},
                    "bash_max_timeout_ms": {"type": "integer", "minimum": 1000},
                    "bash_max_output_length": {"type": "integer", "minimum": 1000},
                    "default_working_dir": {"type": ["string", "null"]}
                },
                "required": ["max_workers", "worker_timeout", "manager_timeout"]
            },
            "monitoring": {
                "type": "object",
                "properties": {
                    "progress_interval": {"type": "integer", "minimum": 1},
                    "verbose_logging": {"type": "boolean"},
                    "enable_opus_review": {"type": "boolean"},
                    "show_progress_bar": {"type": "boolean"},
                    "usage_warning_threshold": {"type": "integer", "minimum": 0, "maximum": 100},
                    "check_usage_before_start": {"type": "boolean"}
                }
            },
            "notifications": {
                "type": "object",
                "properties": {
                    "slack_webhook_url": {"type": "string"},
                    "notify_on_task_complete": {"type": "boolean"},
                    "notify_on_task_failed": {"type": "boolean"},
                    "notify_on_all_complete": {"type": "boolean"}
                }
            },
            "claude_cli": {
                "type": "object",
                "properties": {
                    "command": {"type": "string"},
                    "flags": {"type": "object"},
                    "settings": {"type": "object"},
                    "environment": {"type": "object"}
                },
                "required": ["command"]
            }
        },
        "required": ["models", "execution"]
    }
    
    def __init__(self, config_paths: Optional[List[str]] = None, 
                 environment_prefix: str = "CLAUDE_ORCHESTRATOR"):
        """
        Initialize configuration manager
        
        Args:
            config_paths: List of configuration file paths to load in order
            environment_prefix: Prefix for environment variables
        """
        self.config_paths = config_paths or [
            "orchestrator_config.json",
            "orchestrator_config.yaml",
            "orchestrator_config.yml",
            os.path.expanduser("~/.claude_orchestrator/config.json"),
            os.path.expanduser("~/.claude_orchestrator/config.yaml"),
            "/etc/claude_orchestrator/config.json"
        ]
        self.environment_prefix = environment_prefix
        self.config = {}
        self.loaded_files = []
        self.validation_result = ConfigValidationResult(is_valid=True)
        
    def load_configuration(self) -> Dict[str, Any]:
        """Load configuration from multiple sources in order of precedence"""
        # Start with default configuration
        self.config = self._get_default_config()
        
        # Load from config files
        for config_path in self.config_paths:
            if os.path.exists(config_path):
                try:
                    file_config = self._load_config_file(config_path)
                    self.config = self._merge_configs(self.config, file_config)
                    self.loaded_files.append(config_path)
                    logger.info(f"Loaded configuration from: {config_path}")
                except Exception as e:
                    logger.error(f"Failed to load config from {config_path}: {e}")
                    self.validation_result.add_error(f"Failed to load {config_path}: {e}")
        
        # Override with environment variables
        env_overrides = self._load_environment_variables()
        if env_overrides:
            self.config = self._merge_configs(self.config, env_overrides)
            logger.info("Applied environment variable overrides")
        
        # Validate final configuration
        self._validate_configuration()
        
        return self.config
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "models": {
                "manager": {
                    "model": "claude-3-opus-20240229",
                    "description": "Opus model for planning and task management"
                },
                "worker": {
                    "model": "claude-3-5-sonnet-20241022",
                    "description": "Sonnet model for code implementation"
                }
            },
            "execution": {
                "max_workers": 3,
                "worker_timeout": 300,
                "manager_timeout": 180,
                "task_queue_timeout": 1.0,
                "max_turns": None,
                "bash_default_timeout_ms": 120000,
                "bash_max_timeout_ms": 600000,
                "bash_max_output_length": 30000,
                "default_working_dir": None
            },
            "monitoring": {
                "progress_interval": 10,
                "verbose_logging": False,
                "enable_opus_review": True,
                "show_progress_bar": True,
                "usage_warning_threshold": 80,
                "check_usage_before_start": True
            },
            "notifications": {
                "slack_webhook_url": "",
                "notify_on_task_complete": True,
                "notify_on_task_failed": True,
                "notify_on_all_complete": True
            },
            "claude_cli": {
                "command": "claude",
                "flags": {
                    "verbose": False,
                    "dangerously_skip_permissions": False,
                    "add_dir": [],
                    "allowed_tools": [],
                    "disallowed_tools": [],
                    "output_format": "text",
                    "input_format": "text",
                    "permission_mode": None,
                    "permission_prompt_tool": None
                },
                "settings": {
                    "api_key_helper": None,
                    "cleanup_period_days": 30,
                    "include_co_authored_by": True,
                    "permissions": {
                        "allow": [],
                        "deny": [],
                        "additional_directories": [],
                        "default_mode": None,
                        "disable_bypass_permissions_mode": None,
                        "force_login_method": None
                    }
                },
                "environment": {
                    "ANTHROPIC_API_KEY": None,
                    "ANTHROPIC_AUTH_TOKEN": None,
                    "ANTHROPIC_CUSTOM_HEADERS": None,
                    "ANTHROPIC_MODEL": None,
                    "ANTHROPIC_SMALL_FAST_MODEL": None,
                    "CLAUDE_BASH_MAINTAIN_PROJECT_WORKING_DIR": None,
                    "CLAUDE_CODE_API_KEY_HELPER_TTL_MS": None,
                    "CLAUDE_CODE_MAX_OUTPUT_TOKENS": None,
                    "CLAUDE_CODE_USE_BEDROCK": None,
                    "CLAUDE_CODE_USE_VERTEX": None,
                    "CLAUDE_CODE_SKIP_BEDROCK_AUTH": None,
                    "CLAUDE_CODE_SKIP_VERTEX_AUTH": None,
                    "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": None,
                    "DISABLE_AUTOUPDATER": None,
                    "DISABLE_BUG_COMMAND": None,
                    "DISABLE_COST_WARNINGS": None,
                    "DISABLE_ERROR_REPORTING": None,
                    "DISABLE_NON_ESSENTIAL_MODEL_CALLS": None,
                    "DISABLE_TELEMETRY": None,
                    "HTTP_PROXY": None,
                    "HTTPS_PROXY": None,
                    "MAX_THINKING_TOKENS": None,
                    "MCP_TIMEOUT": None,
                    "MCP_TOOL_TIMEOUT": None,
                    "MAX_MCP_OUTPUT_TOKENS": None
                }
            }
        }
    
    def _load_config_file(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from a single file"""
        path = Path(config_path)
        
        with open(path, 'r', encoding='utf-8') as f:
            if path.suffix.lower() in ['.yaml', '.yml']:
                return yaml.safe_load(f)
            else:
                return json.load(f)
    
    def _load_environment_variables(self) -> Dict[str, Any]:
        """Load configuration overrides from environment variables"""
        env_config = {}
        
        # Define environment variable mappings
        env_mappings = {
            f"{self.environment_prefix}_MAX_WORKERS": "execution.max_workers",
            f"{self.environment_prefix}_WORKER_TIMEOUT": "execution.worker_timeout",
            f"{self.environment_prefix}_MANAGER_TIMEOUT": "execution.manager_timeout",
            f"{self.environment_prefix}_VERBOSE": "monitoring.verbose_logging",
            f"{self.environment_prefix}_PROGRESS_BAR": "monitoring.show_progress_bar",
            f"{self.environment_prefix}_OPUS_REVIEW": "monitoring.enable_opus_review",
            f"{self.environment_prefix}_SLACK_WEBHOOK": "notifications.slack_webhook_url",
            f"{self.environment_prefix}_WORKING_DIR": "execution.default_working_dir",
            f"{self.environment_prefix}_MANAGER_MODEL": "models.manager.model",
            f"{self.environment_prefix}_WORKER_MODEL": "models.worker.model"
        }
        
        for env_var, config_path in env_mappings.items():
            value = os.environ.get(env_var)
            if value is not None:
                # Convert string values to appropriate types
                converted_value = self._convert_env_value(value)
                self._set_nested_value(env_config, config_path, converted_value)
        
        return env_config
    
    def _convert_env_value(self, value: str) -> Union[str, int, float, bool]:
        """Convert environment variable string to appropriate type"""
        # Boolean conversion
        if value.lower() in ['true', 'false']:
            return value.lower() == 'true'
        
        # Integer conversion
        try:
            return int(value)
        except ValueError:
            pass
        
        # Float conversion
        try:
            return float(value)
        except ValueError:
            pass
        
        # Return as string
        return value
    
    def _set_nested_value(self, config: Dict[str, Any], path: str, value: Any):
        """Set a nested configuration value using dot notation"""
        keys = path.split('.')
        current = config
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
    
    def _merge_configs(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merge configuration dictionaries"""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _validate_configuration(self) -> ConfigValidationResult:
        """Validate configuration against schema"""
        try:
            validate(instance=self.config, schema=self.CONFIG_SCHEMA)
            logger.info("Configuration validation passed")
        except ValidationError as e:
            error_msg = f"Configuration validation failed: {e.message}"
            logger.error(error_msg)
            self.validation_result.add_error(error_msg)
        
        # Additional custom validations
        self._validate_timeouts()
        self._validate_paths()
        self._validate_model_names()
        
        return self.validation_result
    
    def _validate_timeouts(self):
        """Validate timeout configurations"""
        execution = self.config.get("execution", {})
        
        # Check bash timeouts
        bash_default = execution.get("bash_default_timeout_ms", 0)
        bash_max = execution.get("bash_max_timeout_ms", 0)
        
        if bash_default > bash_max:
            self.validation_result.add_error(
                "bash_default_timeout_ms cannot be greater than bash_max_timeout_ms"
            )
        
        # Check if worker timeout is reasonable
        worker_timeout = execution.get("worker_timeout", 0)
        if worker_timeout > 3600:  # 1 hour
            self.validation_result.add_warning(
                "worker_timeout is very high (>1 hour), consider reducing it"
            )
    
    def _validate_paths(self):
        """Validate path configurations"""
        execution = self.config.get("execution", {})
        working_dir = execution.get("default_working_dir")
        
        if working_dir and not os.path.exists(working_dir):
            self.validation_result.add_warning(
                f"default_working_dir does not exist: {working_dir}"
            )
    
    def _validate_model_names(self):
        """Validate model name configurations"""
        models = self.config.get("models", {})
        
        # Check if model names are valid
        valid_models = [
            "claude-3-opus-20240229",
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022",
            "opus",
            "sonnet",
            "haiku"
        ]
        
        manager_model = models.get("manager", {}).get("model", "")
        worker_model = models.get("worker", {}).get("model", "")
        
        if manager_model and manager_model not in valid_models:
            self.validation_result.add_warning(
                f"Unknown manager model: {manager_model}"
            )
        
        if worker_model and worker_model not in valid_models:
            self.validation_result.add_warning(
                f"Unknown worker model: {worker_model}"
            )
    
    def get_config(self) -> Dict[str, Any]:
        """Get the loaded configuration"""
        return self.config
    
    def get_validation_result(self) -> ConfigValidationResult:
        """Get the validation result"""
        return self.validation_result
    
    def save_config(self, config_path: str, config: Optional[Dict[str, Any]] = None):
        """Save configuration to file"""
        config_to_save = config or self.config
        
        path = Path(config_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            if path.suffix.lower() in ['.yaml', '.yml']:
                yaml.dump(config_to_save, f, default_flow_style=False, indent=2)
            else:
                json.dump(config_to_save, f, indent=2)
        
        logger.info(f"Configuration saved to: {config_path}")
    
    def create_config_template(self, output_path: str = "orchestrator_config_template.json"):
        """Create a configuration template with all available options"""
        template = self._get_default_config()
        
        # Add comments as special keys (will be removed in actual use)
        template["_comments"] = {
            "models": "Configure AI models for manager and worker roles",
            "execution": "Execution parameters for parallel processing",
            "monitoring": "Monitoring and logging configuration",
            "notifications": "Notification settings (Slack, etc.)",
            "claude_cli": "Claude CLI configuration and flags"
        }
        
        self.save_config(output_path, template)
        logger.info(f"Configuration template created at: {output_path}")
    
    def get_config_summary(self) -> str:
        """Get a summary of the current configuration"""
        summary = []
        summary.append("Configuration Summary:")
        summary.append(f"  Loaded files: {', '.join(self.loaded_files) if self.loaded_files else 'None'}")
        summary.append(f"  Manager model: {self.config.get('models', {}).get('manager', {}).get('model', 'Unknown')}")
        summary.append(f"  Worker model: {self.config.get('models', {}).get('worker', {}).get('model', 'Unknown')}")
        summary.append(f"  Max workers: {self.config.get('execution', {}).get('max_workers', 'Unknown')}")
        summary.append(f"  Worker timeout: {self.config.get('execution', {}).get('worker_timeout', 'Unknown')}s")
        summary.append(f"  Progress bar: {self.config.get('monitoring', {}).get('show_progress_bar', 'Unknown')}")
        summary.append(f"  Opus review: {self.config.get('monitoring', {}).get('enable_opus_review', 'Unknown')}")
        
        if self.validation_result.errors:
            summary.append("  Validation errors:")
            for error in self.validation_result.errors:
                summary.append(f"    - {error}")
        
        if self.validation_result.warnings:
            summary.append("  Validation warnings:")
            for warning in self.validation_result.warnings:
                summary.append(f"    - {warning}")
        
        return "\n".join(summary)


class ConfigProperty:
    """Property descriptor for configuration values with validation"""
    
    def __init__(self, config_path: str, default_value: Any = None, 
                 validator: Optional[callable] = None):
        self.config_path = config_path
        self.default_value = default_value
        self.validator = validator
    
    def __get__(self, instance, owner):
        if instance is None:
            return self
        
        keys = self.config_path.split('.')
        value = instance.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return self.default_value
        
        if self.validator:
            try:
                value = self.validator(value)
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid value for {self.config_path}: {e}")
                return self.default_value
        
        return value


class EnhancedConfig:
    """Enhanced configuration class with property-based access"""
    
    def __init__(self, config_manager: ConfigurationManager):
        self.config_manager = config_manager
        self.config = config_manager.get_config()
    
    # Model configurations
    manager_model = ConfigProperty("models.manager.model", "claude-3-opus-20240229")
    worker_model = ConfigProperty("models.worker.model", "claude-3-5-sonnet-20241022")
    
    # Execution configurations
    max_workers = ConfigProperty("execution.max_workers", 3, lambda x: max(1, min(20, int(x))))
    worker_timeout = ConfigProperty("execution.worker_timeout", 300, lambda x: max(10, int(x)))
    manager_timeout = ConfigProperty("execution.manager_timeout", 180, lambda x: max(10, int(x)))
    task_queue_timeout = ConfigProperty("execution.task_queue_timeout", 1.0, lambda x: max(0.1, float(x)))
    max_turns = ConfigProperty("execution.max_turns", None)
    bash_default_timeout_ms = ConfigProperty("execution.bash_default_timeout_ms", 120000)
    bash_max_timeout_ms = ConfigProperty("execution.bash_max_timeout_ms", 600000)
    bash_max_output_length = ConfigProperty("execution.bash_max_output_length", 30000)
    default_working_dir = ConfigProperty("execution.default_working_dir", None)
    
    # Monitoring configurations
    progress_interval = ConfigProperty("monitoring.progress_interval", 10)
    verbose_logging = ConfigProperty("monitoring.verbose_logging", False)
    enable_opus_review = ConfigProperty("monitoring.enable_opus_review", True)
    show_progress_bar = ConfigProperty("monitoring.show_progress_bar", True)
    usage_warning_threshold = ConfigProperty("monitoring.usage_warning_threshold", 80)
    check_usage_before_start = ConfigProperty("monitoring.check_usage_before_start", True)
    
    # Notification configurations
    slack_webhook_url = ConfigProperty("notifications.slack_webhook_url", "")
    notify_on_task_complete = ConfigProperty("notifications.notify_on_task_complete", True)
    notify_on_task_failed = ConfigProperty("notifications.notify_on_task_failed", True)
    notify_on_all_complete = ConfigProperty("notifications.notify_on_all_complete", True)
    
    # Claude CLI configurations
    claude_command = ConfigProperty("claude_cli.command", "claude")
    claude_flags = ConfigProperty("claude_cli.flags", {})
    claude_settings = ConfigProperty("claude_cli.settings", {})
    claude_environment = ConfigProperty("claude_cli.environment", {})
    
    def refresh(self):
        """Refresh configuration from sources"""
        self.config = self.config_manager.load_configuration()
    
    def get_raw_config(self) -> Dict[str, Any]:
        """Get the raw configuration dictionary"""
        return self.config
    
    def get_validation_result(self) -> ConfigValidationResult:
        """Get configuration validation result"""
        return self.config_manager.get_validation_result()
    
    def is_valid(self) -> bool:
        """Check if configuration is valid"""
        return self.config_manager.get_validation_result().is_valid