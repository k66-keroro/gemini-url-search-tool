"""
設定管理モジュール

SQLite GUI Toolの設定を管理します。
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional
from src.utils.logger import Logger
from src.utils.error_handler import ErrorHandler


class Settings:
    """設定管理クラス"""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        初期化
        
        Args:
            config_file: 設定ファイルのパス（省略時はデフォルトパス）
        """
        if config_file is None:
            config_file = Path.cwd() / "config" / "app_config.json"
        
        self.config_file = Path(config_file)
        self.config: Dict[str, Any] = {}
        self._load_config()
    
    def _load_config(self) -> None:
        """設定を読み込む"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                Logger.info(f"設定ファイルを読み込みました: {self.config_file}")
            else:
                # デフォルト設定を作成
                self.config = self._get_default_config()
                self._save_config()
                Logger.info(f"デフォルト設定ファイルを作成しました: {self.config_file}")
                
        except Exception as e:
            ErrorHandler.handle_exception(
                e, 
                context="設定ファイルの読み込み",
                show_message=False
            )
            self.config = self._get_default_config()
    
    def _save_config(self) -> None:
        """設定を保存"""
        try:
            # 設定ディレクトリを作成
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            
            Logger.debug(f"設定ファイルを保存しました: {self.config_file}")
            
        except Exception as e:
            ErrorHandler.handle_exception(
                e, 
                context="設定ファイルの保存",
                show_message=False
            )
    
    def _get_default_config(self) -> Dict[str, Any]:
        """デフォルト設定を取得"""
        return {
            "database": {
                "last_db_path": "",
                "auto_connect": False,
                "connection_timeout": 30
            },
            "ui": {
                "window_width": 1200,
                "window_height": 800,
                "theme": "default",
                "font_size": 10
            },
            "query": {
                "max_result_rows": 1000,
                "query_timeout": 60,
                "auto_format": True,
                "history_size": 100
            },
            "import": {
                "default_encoding": "utf-8",
                "preview_rows": 10,
                "batch_size": 1000
            },
            "export": {
                "default_format": "CSV",
                "default_encoding": "utf-8-sig",
                "include_headers": True
            },
            "analysis": {
                "sample_size": 10000,
                "max_unique_values": 100
            },
            "logging": {
                "level": "INFO",
                "max_log_files": 10,
                "max_log_size_mb": 10
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        設定値を取得
        
        Args:
            key: 設定キー（ドット記法対応、例: "database.last_db_path"）
            default: デフォルト値
            
        Returns:
            設定値
        """
        keys = key.split('.')
        value = self.config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any) -> None:
        """
        設定値を設定
        
        Args:
            key: 設定キー（ドット記法対応）
            value: 設定値
        """
        keys = key.split('.')
        config = self.config
        
        # 最後のキー以外は辞書を作成
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # 最後のキーに値を設定
        config[keys[-1]] = value
        
        # 設定を保存
        self._save_config()
        
        Logger.debug(f"設定を更新しました: {key} = {value}")
    
    def get_database_config(self) -> Dict[str, Any]:
        """データベース設定を取得"""
        return self.get("database", {})
    
    def get_ui_config(self) -> Dict[str, Any]:
        """UI設定を取得"""
        return self.get("ui", {})
    
    def get_query_config(self) -> Dict[str, Any]:
        """クエリ設定を取得"""
        return self.get("query", {})
    
    def get_import_config(self) -> Dict[str, Any]:
        """インポート設定を取得"""
        return self.get("import", {})
    
    def get_export_config(self) -> Dict[str, Any]:
        """エクスポート設定を取得"""
        return self.get("export", {})
    
    def get_analysis_config(self) -> Dict[str, Any]:
        """分析設定を取得"""
        return self.get("analysis", {})
    
    def set_last_database_path(self, path: str) -> None:
        """最後に接続したデータベースパスを設定"""
        self.set("database.last_db_path", path)
    
    def get_last_database_path(self) -> str:
        """最後に接続したデータベースパスを取得"""
        return self.get("database.last_db_path", "")
    
    def set_window_geometry(self, width: int, height: int) -> None:
        """ウィンドウサイズを設定"""
        self.set("ui.window_width", width)
        self.set("ui.window_height", height)
    
    def get_window_geometry(self) -> tuple[int, int]:
        """ウィンドウサイズを取得"""
        width = self.get("ui.window_width", 1200)
        height = self.get("ui.window_height", 800)
        return width, height
    
    def reset_to_defaults(self) -> None:
        """設定をデフォルトにリセット"""
        self.config = self._get_default_config()
        self._save_config()
        Logger.info("設定をデフォルトにリセットしました")
    
    def export_config(self, export_path: str) -> bool:
        """
        設定をファイルにエクスポート
        
        Args:
            export_path: エクスポート先のパス
            
        Returns:
            成功した場合True
        """
        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            Logger.info(f"設定をエクスポートしました: {export_path}")
            return True
        except Exception as e:
            ErrorHandler.handle_exception(e, context="設定のエクスポート")
            return False
    
    def import_config(self, import_path: str) -> bool:
        """
        設定をファイルからインポート
        
        Args:
            import_path: インポート元のパス
            
        Returns:
            成功した場合True
        """
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                imported_config = json.load(f)
            
            # 設定を更新
            self.config.update(imported_config)
            self._save_config()
            
            Logger.info(f"設定をインポートしました: {import_path}")
            return True
        except Exception as e:
            ErrorHandler.handle_exception(e, context="設定のインポート")
            return False


# グローバル設定インスタンス
_settings_instance: Optional[Settings] = None


def get_settings() -> Settings:
    """グローバル設定インスタンスを取得"""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
    return _settings_instance