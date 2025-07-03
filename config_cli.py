#!/usr/bin/env python3
"""
Configuration CLI Tool for Claude Orchestrator
Provides command-line interface for managing configuration
"""

import argparse
import sys
import os
import json
from typing import Dict, Any
from config_manager import ConfigurationManager, EnhancedConfig
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def cmd_init(args):
    """Initialize configuration with template"""
    config_manager = ConfigurationManager()
    
    output_path = args.output or "orchestrator_config.json"
    
    if os.path.exists(output_path) and not args.force:
        print(f"❌ Configuration file already exists at {output_path}")
        print("Use --force to overwrite or specify a different --output path")
        return 1
    
    try:
        config_manager.create_config_template(output_path)
        print(f"✅ Configuration template created at: {output_path}")
        print("\n📝 Next steps:")
        print(f"   1. Edit {output_path} to customize your settings")
        print(f"   2. Validate with: python config_cli.py validate {output_path}")
        print(f"   3. View summary with: python config_cli.py show {output_path}")
        return 0
    except Exception as e:
        print(f"❌ Failed to create configuration template: {e}")
        return 1


def cmd_validate(args):
    """Validate configuration file"""
    config_path = args.config_path
    
    if not os.path.exists(config_path):
        print(f"❌ Configuration file not found: {config_path}")
        return 1
    
    try:
        config_manager = ConfigurationManager([config_path])
        config_manager.load_configuration()
        validation_result = config_manager.get_validation_result()
        
        if validation_result.is_valid:
            print(f"✅ Configuration is valid: {config_path}")
            
            if validation_result.warnings:
                print("\n⚠️ Warnings:")
                for warning in validation_result.warnings:
                    print(f"   - {warning}")
        else:
            print(f"❌ Configuration validation failed: {config_path}")
            print("\n🔍 Errors:")
            for error in validation_result.errors:
                print(f"   - {error}")
            
            if validation_result.warnings:
                print("\n⚠️ Warnings:")
                for warning in validation_result.warnings:
                    print(f"   - {warning}")
            
            return 1
        
        return 0
    except Exception as e:
        print(f"❌ Error validating configuration: {e}")
        return 1


def cmd_show(args):
    """Show configuration summary"""
    config_path = args.config_path
    
    if not os.path.exists(config_path):
        print(f"❌ Configuration file not found: {config_path}")
        return 1
    
    try:
        config_manager = ConfigurationManager([config_path])
        config_manager.load_configuration()
        
        print(f"📋 Configuration Summary for: {config_path}")
        print("=" * 50)
        print(config_manager.get_config_summary())
        
        if args.verbose:
            print("\n📄 Full Configuration:")
            print("=" * 50)
            config = config_manager.get_config()
            print(json.dumps(config, indent=2))
        
        return 0
    except Exception as e:
        print(f"❌ Error reading configuration: {e}")
        return 1


def cmd_set(args):
    """Set configuration value"""
    config_path = args.config_path
    key = args.key
    value = args.value
    
    if not os.path.exists(config_path):
        print(f"❌ Configuration file not found: {config_path}")
        return 1
    
    try:
        config_manager = ConfigurationManager([config_path])
        config = config_manager.load_configuration()
        
        # Convert value to appropriate type
        converted_value = _convert_value(value)
        
        # Set nested value
        _set_nested_value(config, key, converted_value)
        
        # Save updated configuration
        config_manager.save_config(config_path, config)
        
        print(f"✅ Updated {key} = {converted_value}")
        print(f"💾 Configuration saved to: {config_path}")
        
        return 0
    except Exception as e:
        print(f"❌ Error setting configuration: {e}")
        return 1


def cmd_get(args):
    """Get configuration value"""
    config_path = args.config_path
    key = args.key
    
    if not os.path.exists(config_path):
        print(f"❌ Configuration file not found: {config_path}")
        return 1
    
    try:
        config_manager = ConfigurationManager([config_path])
        config = config_manager.load_configuration()
        
        # Get nested value
        value = _get_nested_value(config, key)
        
        if value is not None:
            if args.json:
                print(json.dumps(value, indent=2))
            else:
                print(f"{key} = {value}")
        else:
            print(f"❌ Configuration key not found: {key}")
            return 1
        
        return 0
    except Exception as e:
        print(f"❌ Error getting configuration: {e}")
        return 1


def cmd_list_keys(args):
    """List all configuration keys"""
    config_path = args.config_path
    
    if not os.path.exists(config_path):
        print(f"❌ Configuration file not found: {config_path}")
        return 1
    
    try:
        config_manager = ConfigurationManager([config_path])
        config = config_manager.load_configuration()
        
        print(f"🔑 Configuration Keys in: {config_path}")
        print("=" * 50)
        
        keys = _get_all_keys(config)
        for key in sorted(keys):
            value = _get_nested_value(config, key)
            value_type = type(value).__name__
            
            if args.verbose:
                print(f"  {key:<40} ({value_type}): {value}")
            else:
                print(f"  {key}")
        
        return 0
    except Exception as e:
        print(f"❌ Error listing keys: {e}")
        return 1


def cmd_test(args):
    """Test configuration with orchestrator"""
    config_path = args.config_path
    
    if not os.path.exists(config_path):
        print(f"❌ Configuration file not found: {config_path}")
        return 1
    
    try:
        print(f"🧪 Testing configuration: {config_path}")
        
        # Load and validate configuration
        config_manager = ConfigurationManager([config_path])
        config_manager.load_configuration()
        enhanced_config = EnhancedConfig(config_manager)
        
        validation_result = enhanced_config.get_validation_result()
        
        if not validation_result.is_valid:
            print("❌ Configuration validation failed:")
            for error in validation_result.errors:
                print(f"   - {error}")
            return 1
        
        print("✅ Configuration validation passed")
        
        # Test property access
        print("\n🔍 Testing property access:")
        print(f"   Manager model: {enhanced_config.manager_model}")
        print(f"   Worker model: {enhanced_config.worker_model}")
        print(f"   Max workers: {enhanced_config.max_workers}")
        print(f"   Worker timeout: {enhanced_config.worker_timeout}s")
        print(f"   Progress bar: {enhanced_config.show_progress_bar}")
        
        # Test environment variable loading
        print("\n🌍 Environment variable support:")
        print("   Set CLAUDE_ORCHESTRATOR_MAX_WORKERS=5 to override max_workers")
        print("   Set CLAUDE_ORCHESTRATOR_VERBOSE=true to enable verbose logging")
        print("   Set CLAUDE_ORCHESTRATOR_SLACK_WEBHOOK=<url> to configure Slack")
        
        print("\n✅ Configuration test completed successfully")
        return 0
        
    except Exception as e:
        print(f"❌ Error testing configuration: {e}")
        return 1


def _convert_value(value: str):
    """Convert string value to appropriate type"""
    # Boolean conversion
    if value.lower() in ['true', 'false']:
        return value.lower() == 'true'
    
    # None/null conversion
    if value.lower() in ['none', 'null']:
        return None
    
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
    
    # JSON conversion (for arrays/objects)
    try:
        return json.loads(value)
    except (json.JSONDecodeError, ValueError):
        pass
    
    # Return as string
    return value


def _set_nested_value(config: Dict[str, Any], path: str, value: Any):
    """Set a nested configuration value using dot notation"""
    keys = path.split('.')
    current = config
    
    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]
    
    current[keys[-1]] = value


def _get_nested_value(config: Dict[str, Any], path: str):
    """Get a nested configuration value using dot notation"""
    keys = path.split('.')
    current = config
    
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return None
    
    return current


def _get_all_keys(config: Dict[str, Any], prefix: str = "") -> list:
    """Get all configuration keys with dot notation"""
    keys = []
    
    for key, value in config.items():
        if key.startswith('_'):  # Skip private keys like _comments
            continue
            
        full_key = f"{prefix}.{key}" if prefix else key
        
        if isinstance(value, dict):
            keys.extend(_get_all_keys(value, full_key))
        else:
            keys.append(full_key)
    
    return keys


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Claude Orchestrator Configuration Manager",
        epilog="""
Examples:
  # Create a new configuration template
  python config_cli.py init

  # Validate configuration
  python config_cli.py validate orchestrator_config.json

  # Show configuration summary
  python config_cli.py show orchestrator_config.json

  # Set a configuration value
  python config_cli.py set orchestrator_config.json execution.max_workers 5

  # Get a configuration value
  python config_cli.py get orchestrator_config.json models.manager.model

  # List all configuration keys
  python config_cli.py list-keys orchestrator_config.json

  # Test configuration
  python config_cli.py test orchestrator_config.json
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Init command
    init_parser = subparsers.add_parser('init', help='Create configuration template')
    init_parser.add_argument('--output', '-o', help='Output file path (default: orchestrator_config.json)')
    init_parser.add_argument('--force', '-f', action='store_true', help='Overwrite existing file')
    init_parser.set_defaults(func=cmd_init)
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate configuration')
    validate_parser.add_argument('config_path', help='Path to configuration file')
    validate_parser.set_defaults(func=cmd_validate)
    
    # Show command
    show_parser = subparsers.add_parser('show', help='Show configuration summary')
    show_parser.add_argument('config_path', help='Path to configuration file')
    show_parser.add_argument('--verbose', '-v', action='store_true', help='Show full configuration')
    show_parser.set_defaults(func=cmd_show)
    
    # Set command
    set_parser = subparsers.add_parser('set', help='Set configuration value')
    set_parser.add_argument('config_path', help='Path to configuration file')
    set_parser.add_argument('key', help='Configuration key (dot notation, e.g., execution.max_workers)')
    set_parser.add_argument('value', help='Configuration value')
    set_parser.set_defaults(func=cmd_set)
    
    # Get command
    get_parser = subparsers.add_parser('get', help='Get configuration value')
    get_parser.add_argument('config_path', help='Path to configuration file')
    get_parser.add_argument('key', help='Configuration key (dot notation)')
    get_parser.add_argument('--json', action='store_true', help='Output as JSON')
    get_parser.set_defaults(func=cmd_get)
    
    # List keys command
    list_parser = subparsers.add_parser('list-keys', help='List all configuration keys')
    list_parser.add_argument('config_path', help='Path to configuration file')
    list_parser.add_argument('--verbose', '-v', action='store_true', help='Show values and types')
    list_parser.set_defaults(func=cmd_list_keys)
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Test configuration')
    test_parser.add_argument('config_path', help='Path to configuration file')
    test_parser.set_defaults(func=cmd_test)
    
    args = parser.parse_args()
    
    if hasattr(args, 'func'):
        return args.func(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())