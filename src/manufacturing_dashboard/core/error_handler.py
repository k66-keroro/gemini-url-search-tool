"""
製造ダッシュボード用エラーハンドラー
"""

import logging
import traceback
from typing import Optional, Dict, Any
from datetime import datetime
from pathlib import Path

from ..config.settings import get_config


class ManufacturingErrorHandler:
    """製造ダッシュボード用エラーハンドラー"""
    
    def __init__(self):
        self.logger = self._setup_logger()
        self.error_log = []
        
    def _setup_logger(self) -> logging.Logger:
        """ロガーをセットアップ"""
        logger = logging.getLogger("manufacturing_dashboard")
        
        if not logger.handlers:
            # 設定を取得
            log_config = get_config("logging")
            
            # ログレベルを設定
            logger.setLevel(getattr(logging, log_config.get("level", "INFO")))
            
            # フォーマッターを作成
            formatter = logging.Formatter(log_config.get("format"))
            
            # ファイルハンドラーを追加
            if log_config.get("file_handler", {}).get("enabled", True):
                log_file = Path(log_config["file_handler"]["filename"])
                log_file.parent.mkdir(parents=True, exist_ok=True)
                
                file_handler = logging.FileHandler(log_file, encoding='utf-8')
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)
            
            # コンソールハンドラーを追加
            if log_config.get("console_handler", {}).get("enabled", True):
                console_handler = logging.StreamHandler()
                console_handler.setFormatter(formatter)
                logger.addHandler(console_handler)
        
        return logger
    
    def handle_error(self, error: Exception, context: str = "", 
                    severity: str = "error") -> Dict[str, Any]:
        """エラーを処理"""
        error_info = {
            "timestamp": datetime.now().isoformat(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context,
            "severity": severity,
            "traceback": traceback.format_exc()
        }
        
        # ログに記録
        log_message = f"{context}: {error_info['error_type']} - {error_info['error_message']}"
        
        if severity == "critical":
            self.logger.critical(log_message)
        elif severity == "error":
            self.logger.error(log_message)
        elif severity == "warning":
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)
        
        # エラーログに追加
        self.error_log.append(error_info)
        
        # エラーログのサイズを制限（最新の100件のみ保持）
        if len(self.error_log) > 100:
            self.error_log = self.error_log[-100:]
        
        return error_info
    
    def log_info(self, message: str, context: str = ""):
        """情報ログを記録"""
        log_message = f"{context}: {message}" if context else message
        self.logger.info(log_message)
    
    def log_warning(self, message: str, context: str = ""):
        """警告ログを記録"""
        log_message = f"{context}: {message}" if context else message
        self.logger.warning(log_message)
    
    def get_recent_errors(self, count: int = 10) -> list:
        """最近のエラーを取得"""
        return self.error_log[-count:] if self.error_log else []
    
    def clear_error_log(self):
        """エラーログをクリア"""
        self.error_log.clear()
        self.logger.info("エラーログをクリアしました")
    
    def get_error_summary(self) -> Dict[str, Any]:
        """エラーサマリーを取得"""
        if not self.error_log:
            return {
                "total_errors": 0,
                "by_severity": {},
                "by_type": {},
                "recent_errors": []
            }
        
        # 重要度別の集計
        by_severity = {}
        by_type = {}
        
        for error in self.error_log:
            severity = error.get("severity", "unknown")
            error_type = error.get("error_type", "unknown")
            
            by_severity[severity] = by_severity.get(severity, 0) + 1
            by_type[error_type] = by_type.get(error_type, 0) + 1
        
        return {
            "total_errors": len(self.error_log),
            "by_severity": by_severity,
            "by_type": by_type,
            "recent_errors": self.get_recent_errors(5)
        }


# グローバルエラーハンドラーインスタンス
error_handler = ManufacturingErrorHandler()