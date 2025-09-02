"""
製造ダッシュボード設定
"""

import os
from pathlib import Path
from typing import Dict, Any

# プロジェクトルートディレクトリ
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent

# データベース設定
DATABASE_CONFIG = {
    "default_db_path": str(PROJECT_ROOT / "data" / "sqlite" / "manufacturing.db"),
    "backup_db_path": str(PROJECT_ROOT / "data" / "sqlite" / "manufacturing_backup.db"),
    "test_db_path": str(PROJECT_ROOT / "data" / "sqlite" / "manufacturing_test.db")
}

# ファイル処理設定
FILE_PROCESSING_CONFIG = {
    "input_directory": str(PROJECT_ROOT / "data" / "raw"),
    "output_directory": str(PROJECT_ROOT / "data" / "processed"),
    "reports_directory": str(PROJECT_ROOT / "reports"),
    "logs_directory": str(PROJECT_ROOT / "logs"),
    "supported_formats": [".csv", ".txt", ".xlsx", ".xls"],
    "encoding_detection": True,
    "auto_separator_detection": True
}

# ダッシュボード設定
DASHBOARD_CONFIG = {
    "title": "PC製造部門ダッシュボード",
    "port": 8501,
    "host": "localhost",
    "theme": "light",
    "page_config": {
        "page_title": "製造ダッシュボード",
        "page_icon": "🏭",
        "layout": "wide",
        "initial_sidebar_state": "expanded"
    }
}

# 分析設定
ANALYTICS_CONFIG = {
    "production": {
        "default_date_range": 7,  # 日
        "update_interval": 3600,  # 秒（1時間）
        "alert_thresholds": {
            "low_efficiency": 0.8,
            "high_error_rate": 0.05
        }
    },
    "inventory": {
        "stagnation_threshold": 30,  # 日
        "alert_threshold": 60,  # 日
        "analysis_period": 90  # 日
    },
    "error_detection": {
        "severity_levels": ["low", "medium", "high", "critical"],
        "auto_categorization": True,
        "notification_enabled": True
    }
}

# ログ設定
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file_handler": {
        "enabled": True,
        "filename": str(PROJECT_ROOT / "logs" / "manufacturing_dashboard.log"),
        "max_bytes": 10 * 1024 * 1024,  # 10MB
        "backup_count": 5
    },
    "console_handler": {
        "enabled": True
    }
}

# パフォーマンス設定
PERFORMANCE_CONFIG = {
    "cache_enabled": True,
    "cache_ttl": 300,  # 秒（5分）
    "max_memory_usage": "1GB",
    "chunk_size": 10000,
    "parallel_processing": True,
    "max_workers": 4
}

# セキュリティ設定
SECURITY_CONFIG = {
    "authentication_enabled": False,
    "session_timeout": 3600,  # 秒（1時間）
    "allowed_file_types": [".csv", ".txt", ".xlsx", ".xls"],
    "max_file_size": 100 * 1024 * 1024,  # 100MB
}

def get_config(section: str = None) -> Dict[str, Any]:
    """設定を取得"""
    config = {
        "database": DATABASE_CONFIG,
        "file_processing": FILE_PROCESSING_CONFIG,
        "dashboard": DASHBOARD_CONFIG,
        "analytics": ANALYTICS_CONFIG,
        "logging": LOGGING_CONFIG,
        "performance": PERFORMANCE_CONFIG,
        "security": SECURITY_CONFIG
    }
    
    if section:
        return config.get(section, {})
    
    return config

def update_config(section: str, key: str, value: Any) -> bool:
    """設定を更新"""
    try:
        config = get_config()
        if section in config and key in config[section]:
            config[section][key] = value
            return True
        return False
    except Exception:
        return False

def ensure_directories():
    """必要なディレクトリを作成"""
    directories = [
        Path(DATABASE_CONFIG["default_db_path"]).parent,
        Path(FILE_PROCESSING_CONFIG["input_directory"]),
        Path(FILE_PROCESSING_CONFIG["output_directory"]),
        Path(FILE_PROCESSING_CONFIG["reports_directory"]),
        Path(FILE_PROCESSING_CONFIG["logs_directory"])
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

# 初期化時にディレクトリを作成
ensure_directories()