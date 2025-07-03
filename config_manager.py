"""
Configuration Manager for Claude Orchestrator
Provides centralized configuration management with validation and property access
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ConfigValidationResult:
    """Result of configuration validation"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]


class ConfigProperty:
    """Descriptor for configuration properties with dot notation support"""
    
    def __init__(self, path: str, default: Any = None):
        self.path = path
        self.default = default
        
    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return obj.get_config_value(self.path, self.default)
    
    def __set__(self, obj, value):
        obj.set_config_value(self.path, value)


class EnhancedConfig:
    """Enhanced configuration class with property access"""
    
    # Define configuration properties
    manager_model = ConfigProperty("models.manager.model", "opus")
    worker_model = ConfigProperty("models.worker.model", "sonnet")
    max_workers = ConfigProperty("execution.max_workers", 3)
    worker_timeout = ConfigProperty("execution.worker_timeout", 7200)
    manager_timeout = ConfigProperty("execution.manager_timeout", 7200)
    enable_opus_review = ConfigProperty("monitoring.enable_opus_review", True)
    slack_webhook_url = ConfigProperty("notifications.slack_webhook_url", None)
    locale_language = ConfigProperty("locale.language", "en")
    
    def __init__(self, config_data: Dict[str, Any]):
        self._config = config_data
        
    def get_config_value(self, path: str, default: Any = None) -> Any:
        """Get configuration value using dot notation"""
        keys = path.split('.')
        value = self._config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
                
        return value
    
    def set_config_value(self, path: str, value: Any):
        """Set configuration value using dot notation"""
        keys = path.split('.')
        config = self._config
        
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
            
        config[keys[-1]] = value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return self._config.copy()


class ConfigurationManager:
    """Manages configuration loading, validation, and access"""
    
    DEFAULT_CONFIG = {
        "models": {
            "manager": {
                "model": "opus",
                "description": "Opus model for planning and task management"
            },
            "worker": {
                "model": "sonnet",
                "description": "Sonnet model for code implementation"
            }
        },
        "execution": {
            "max_workers": 3,
            "worker_timeout": 7200,
            "manager_timeout": 7200,
            "task_queue_timeout": 1.0,
            "max_retries": 3,
            "retry_base_delay": 1.0,
            "retry_max_delay": 60.0
        },
        "monitoring": {
            "progress_interval": 10,
            "verbose_logging": False,
            "show_progress_bar": True,
            "enable_opus_review": True
        },
        "notifications": {
            "slack_webhook_url": None,
            "notify_on_task_complete": True,
            "notify_on_task_failed": True,
            "notify_on_all_complete": True
        },
        "locale": {
            "language": "en",
            "description": "Language for commit messages and outputs"
        }
    }
    
    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        self.config_path = Path(config_path) if config_path else self._find_config()
        self.config_data = self._load_config()
        self.config = EnhancedConfig(self.config_data)
        
    def _find_config(self) -> Path:
        """Find configuration file in current or parent directories"""
        current = Path.cwd()
        
        # Check current directory and up to 3 parent directories
        for _ in range(4):
            config_file = current / "orchestrator_config.json"
            if config_file.exists():
                return config_file
            current = current.parent
            
        # Default to current directory
        return Path.cwd() / "orchestrator_config.json"
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    return self._merge_configs(self.DEFAULT_CONFIG, config)
            except Exception as e:
                logger.error(f"Error loading config: {e}")
                return self.DEFAULT_CONFIG.copy()
        else:
            # Create default config file
            self._save_config(self.DEFAULT_CONFIG)
            return self.DEFAULT_CONFIG.copy()
    
    def _merge_configs(self, default: Dict, custom: Dict) -> Dict:
        """Recursively merge custom config with defaults"""
        result = default.copy()
        
        for key, value in custom.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
                
        return result
    
    def _save_config(self, config_data: Dict[str, Any]):
        """Save configuration to file"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved configuration to {self.config_path}")
        except Exception as e:
            logger.error(f"Error saving config: {e}")
    
    def validate(self) -> ConfigValidationResult:
        """Validate configuration"""
        errors = []
        warnings = []
        
        # Check required fields
        if not self.config.manager_model:
            errors.append("Manager model not specified")
        if not self.config.worker_model:
            errors.append("Worker model not specified")
            
        # Check value ranges
        if self.config.max_workers < 1:
            errors.append("max_workers must be at least 1")
        elif self.config.max_workers > 10:
            warnings.append("max_workers > 10 may cause rate limiting")
            
        # Check timeouts
        if self.config.worker_timeout < 60:
            warnings.append("worker_timeout < 60 seconds may be too short")
            
        # Check language setting
        valid_languages = ["en", "ko", "ja", "zh"]
        if self.config.locale_language not in valid_languages:
            warnings.append(f"Unknown language: {self.config.locale_language}")
            
        return ConfigValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value with dot notation"""
        return self.config.get_config_value(key, default)
    
    def set(self, key: str, value: Any):
        """Set configuration value and save"""
        self.config.set_config_value(key, value)
        self.config_data = self.config.to_dict()
        self._save_config(self.config_data)
    
    def reload(self):
        """Reload configuration from file"""
        self.config_data = self._load_config()
        self.config = EnhancedConfig(self.config_data)
        logger.info("Configuration reloaded")
        
    def export_env(self) -> Dict[str, str]:
        """Export configuration as environment variables"""
        env_vars = {}
        
        def flatten_dict(d: Dict, prefix: str = "ORCHESTRATOR"):
            for key, value in d.items():
                env_key = f"{prefix}_{key.upper()}"
                if isinstance(value, dict):
                    flatten_dict(value, env_key)
                else:
                    env_vars[env_key] = str(value)
                    
        flatten_dict(self.config_data)
        return env_vars


# Legacy compatibility
def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Legacy function for loading config"""
    manager = ConfigurationManager(config_path)
    return manager.config_data