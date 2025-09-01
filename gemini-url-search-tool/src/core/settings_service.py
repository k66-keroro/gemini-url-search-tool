"""
Settings management service for the Gemini URL Search Tool.

This module provides comprehensive settings management including:
- Configuration loading and saving
- Settings validation
- Default value management
- Settings reset functionality
"""

import json
import os
import logging
from typing import Dict, Any, Optional, Union
from pathlib import Path
from dataclasses import dataclass, asdict
from copy import deepcopy

from .storage_service import StorageService

logger = logging.getLogger(__name__)


@dataclass
class APISettings:
    """API configuration settings."""
    api_key: str = ""
    models: list = None
    max_retries: int = 3
    timeout: int = 30
    rate_limit_delay: float = 1.0
    
    def __post_init__(self):
        if self.models is None:
            self.models = ["gemini-2.0-flash-exp", "gemini-1.5-flash"]


@dataclass
class SearchSettings:
    """Search configuration settings."""
    max_results: int = 10
    default_search_type: str = "general"
    enable_caching: bool = True
    cache_duration_hours: int = 24
    enable_result_ranking: bool = True
    prioritize_official_sources: bool = True


@dataclass
class ContentSettings:
    """Content processing settings."""
    max_content_size: int = 1048576  # 1MB
    chunk_size: int = 4096
    summary_max_length: int = 1000
    extraction_timeout: int = 60
    enable_content_filtering: bool = True
    auto_detect_language: bool = True


@dataclass
class UISettings:
    """User interface settings."""
    page_title: str = "Gemini URL Search Tool"
    page_icon: str = "🔍"
    layout: str = "wide"
    sidebar_state: str = "expanded"
    theme: str = "auto"
    results_per_page: int = 10
    show_advanced_options: bool = False


@dataclass
class DatabaseSettings:
    """Database configuration settings."""
    path: str = "data/search_results.db"
    backup_enabled: bool = True
    cleanup_days: int = 30
    auto_vacuum: bool = True


@dataclass
class LoggingSettings:
    """Logging configuration settings."""
    level: str = "INFO"
    file: str = "logs/app.log"
    max_size_mb: int = 10
    backup_count: int = 5
    console_output: bool = True


class SettingsService:
    """
    Comprehensive settings management service.
    
    Handles loading, saving, validation, and management of all application settings.
    """
    
    def __init__(self, config_path: str = "config.json", storage_service: Optional[StorageService] = None):
        """
        Initialize the settings service.
        
        Args:
            config_path: Path to the configuration file
            storage_service: Optional storage service for database settings
        """
        self.config_path = Path(config_path)
        self.storage_service = storage_service
        
        # Default settings
        self._default_settings = {
            "api": asdict(APISettings()),
            "search": asdict(SearchSettings()),
            "content": asdict(ContentSettings()),
            "ui": asdict(UISettings()),
            "database": asdict(DatabaseSettings()),
            "logging": asdict(LoggingSettings())
        }
        
        # Current settings
        self._current_settings = deepcopy(self._default_settings)
        
        # Load settings on initialization
        self.load_settings()
    
    def load_settings(self) -> Dict[str, Any]:
        """
        Load settings from configuration file and database.
        
        Returns:
            Dictionary containing all loaded settings
        """
        try:
            # Load from config file
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    file_settings = json.load(f)
                
                # Merge with defaults
                self._merge_settings(self._current_settings, file_settings)
                logger.info(f"Loaded settings from {self.config_path}")
            
            # Load user preferences from database
            if self.storage_service:
                db_settings = self.storage_service.get_all_settings()
                if db_settings:
                    self._apply_user_preferences(db_settings)
                    logger.info("Loaded user preferences from database")
            
            # Validate settings
            self._validate_settings()
            
            return self._current_settings
            
        except Exception as e:
            logger.error(f"Failed to load settings: {e}")
            logger.info("Using default settings")
            self._current_settings = deepcopy(self._default_settings)
            return self._current_settings
    
    def save_settings(self, settings: Optional[Dict[str, Any]] = None) -> bool:
        """
        Save settings to configuration file.
        
        Args:
            settings: Optional settings dictionary to save. If None, saves current settings.
            
        Returns:
            True if successful, False otherwise
        """
        try:
            settings_to_save = settings or self._current_settings
            
            # Ensure directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save to file
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(settings_to_save, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Settings saved to {self.config_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
            return False
    
    def get_setting(self, key_path: str, default: Any = None) -> Any:
        """
        Get a specific setting value using dot notation.
        
        Args:
            key_path: Dot-separated path to the setting (e.g., "api.max_retries")
            default: Default value if setting not found
            
        Returns:
            Setting value or default
        """
        try:
            keys = key_path.split('.')
            value = self._current_settings
            
            for key in keys:
                value = value[key]
            
            return value
            
        except (KeyError, TypeError):
            return default
    
    def set_setting(self, key_path: str, value: Any, save_to_db: bool = True) -> bool:
        """
        Set a specific setting value using dot notation.
        
        Args:
            key_path: Dot-separated path to the setting
            value: Value to set
            save_to_db: Whether to save user preference to database
            
        Returns:
            True if successful, False otherwise
        """
        try:
            keys = key_path.split('.')
            current = self._current_settings
            
            # Navigate to the parent of the target key
            for key in keys[:-1]:
                if key not in current:
                    current[key] = {}
                current = current[key]
            
            # Set the value
            current[keys[-1]] = value
            
            # Save user preference to database
            if save_to_db and self.storage_service:
                self.storage_service.save_setting(key_path, str(value))
            
            logger.info(f"Setting {key_path} updated to {value}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to set setting {key_path}: {e}")
            return False
    
    def reset_settings(self, category: Optional[str] = None) -> bool:
        """
        Reset settings to defaults.
        
        Args:
            category: Optional category to reset (e.g., "api", "search"). If None, resets all.
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if category:
                if category in self._default_settings:
                    self._current_settings[category] = deepcopy(self._default_settings[category])
                    logger.info(f"Reset {category} settings to defaults")
                else:
                    logger.warning(f"Unknown settings category: {category}")
                    return False
            else:
                self._current_settings = deepcopy(self._default_settings)
                logger.info("Reset all settings to defaults")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to reset settings: {e}")
            return False
    
    def get_api_settings(self) -> APISettings:
        """Get API settings as a structured object."""
        api_dict = self._current_settings.get("api", {})
        return APISettings(**api_dict)
    
    def get_search_settings(self) -> SearchSettings:
        """Get search settings as a structured object."""
        search_dict = self._current_settings.get("search", {})
        return SearchSettings(**search_dict)
    
    def get_content_settings(self) -> ContentSettings:
        """Get content settings as a structured object."""
        content_dict = self._current_settings.get("content", {})
        return ContentSettings(**content_dict)
    
    def get_ui_settings(self) -> UISettings:
        """Get UI settings as a structured object."""
        ui_dict = self._current_settings.get("ui", {})
        return UISettings(**ui_dict)
    
    def get_database_settings(self) -> DatabaseSettings:
        """Get database settings as a structured object."""
        db_dict = self._current_settings.get("database", {})
        return DatabaseSettings(**db_dict)
    
    def get_logging_settings(self) -> LoggingSettings:
        """Get logging settings as a structured object."""
        logging_dict = self._current_settings.get("logging", {})
        return LoggingSettings(**logging_dict)
    
    def get_all_settings(self) -> Dict[str, Any]:
        """Get all current settings."""
        return deepcopy(self._current_settings)
    
    def update_api_key(self, api_key: str) -> bool:
        """
        Update API key and save to environment.
        
        Args:
            api_key: New API key
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Update in current settings
            self.set_setting("api.api_key", api_key, save_to_db=True)
            
            # Update environment variable
            os.environ["GEMINI_API_KEY"] = api_key
            
            # Update .env file if it exists
            env_path = Path(".env")
            if env_path.exists():
                self._update_env_file(env_path, "GEMINI_API_KEY", api_key)
            
            logger.info("API key updated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update API key: {e}")
            return False
    
    def validate_api_key(self, api_key: str) -> bool:
        """
        Validate API key format.
        
        Args:
            api_key: API key to validate
            
        Returns:
            True if valid format, False otherwise
        """
        if not api_key or not isinstance(api_key, str):
            return False
        
        # Basic validation - Gemini API keys typically start with specific patterns
        if len(api_key) < 20:
            return False
        
        return True
    
    def export_settings(self, file_path: str) -> bool:
        """
        Export current settings to a file.
        
        Args:
            file_path: Path to export file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            export_path = Path(file_path)
            export_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(self._current_settings, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Settings exported to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export settings: {e}")
            return False
    
    def import_settings(self, file_path: str) -> bool:
        """
        Import settings from a file.
        
        Args:
            file_path: Path to import file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            import_path = Path(file_path)
            if not import_path.exists():
                logger.error(f"Import file not found: {file_path}")
                return False
            
            with open(import_path, 'r', encoding='utf-8') as f:
                imported_settings = json.load(f)
            
            # Validate imported settings
            if self._validate_imported_settings(imported_settings):
                self._current_settings = imported_settings
                self._validate_settings()
                logger.info(f"Settings imported from {file_path}")
                return True
            else:
                logger.error("Invalid settings format in import file")
                return False
            
        except Exception as e:
            logger.error(f"Failed to import settings: {e}")
            return False
    
    def _merge_settings(self, target: Dict[str, Any], source: Dict[str, Any]) -> None:
        """Recursively merge settings dictionaries."""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._merge_settings(target[key], value)
            else:
                target[key] = value
    
    def _apply_user_preferences(self, db_settings: Dict[str, str]) -> None:
        """Apply user preferences from database."""
        for key_path, value in db_settings.items():
            try:
                # Convert string values to appropriate types
                converted_value = self._convert_setting_value(value)
                self.set_setting(key_path, converted_value, save_to_db=False)
            except Exception as e:
                logger.warning(f"Failed to apply user preference {key_path}: {e}")
    
    def _convert_setting_value(self, value: str) -> Any:
        """Convert string setting value to appropriate type."""
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        
        try:
            # Try integer
            return int(value)
        except ValueError:
            pass
        
        try:
            # Try float
            return float(value)
        except ValueError:
            pass
        
        try:
            # Try JSON (for lists, dicts)
            return json.loads(value)
        except (json.JSONDecodeError, ValueError):
            pass
        
        # Return as string
        return value
    
    def _validate_settings(self) -> None:
        """Validate current settings and fix invalid values."""
        try:
            # Validate API settings
            api_settings = self._current_settings.get("api", {})
            if api_settings.get("max_retries", 0) < 1:
                api_settings["max_retries"] = 3
            if api_settings.get("timeout", 0) < 5:
                api_settings["timeout"] = 30
            
            # Validate search settings
            search_settings = self._current_settings.get("search", {})
            if search_settings.get("max_results", 0) < 1:
                search_settings["max_results"] = 10
            if search_settings.get("cache_duration_hours", 0) < 1:
                search_settings["cache_duration_hours"] = 24
            
            # Validate content settings
            content_settings = self._current_settings.get("content", {})
            if content_settings.get("max_content_size", 0) < 1024:
                content_settings["max_content_size"] = 1048576
            if content_settings.get("chunk_size", 0) < 512:
                content_settings["chunk_size"] = 4096
            
            logger.debug("Settings validation completed")
            
        except Exception as e:
            logger.error(f"Settings validation failed: {e}")
    
    def _validate_imported_settings(self, settings: Dict[str, Any]) -> bool:
        """Validate imported settings structure."""
        required_categories = ["api", "search", "content", "ui", "database", "logging"]
        
        if not isinstance(settings, dict):
            return False
        
        # Check if at least some required categories exist
        found_categories = sum(1 for cat in required_categories if cat in settings)
        return found_categories >= len(required_categories) // 2
    
    def _update_env_file(self, env_path: Path, key: str, value: str) -> None:
        """Update a key-value pair in .env file."""
        try:
            lines = []
            key_found = False
            
            if env_path.exists():
                with open(env_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
            
            # Update existing key or add new one
            for i, line in enumerate(lines):
                if line.strip().startswith(f"{key}="):
                    lines[i] = f"{key}={value}\n"
                    key_found = True
                    break
            
            if not key_found:
                lines.append(f"{key}={value}\n")
            
            with open(env_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
                
        except Exception as e:
            logger.warning(f"Failed to update .env file: {e}")