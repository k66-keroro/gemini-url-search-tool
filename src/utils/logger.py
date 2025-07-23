"""
ロギングモジュール

SQLite GUI Toolのログ機能を提供します。
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional


class Logger:
    """ロギングクラス"""
    
    _instance: Optional['Logger'] = None
    _logger: Optional[logging.Logger] = None
    
    def __new__(cls) -> 'Logger':
        """シングルトンパターンでインスタンスを作成"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初期化"""
        if self._logger is None:
            self._setup_logger()
    
    def _setup_logger(self) -> None:
        """ロガーの設定"""
        # ログディレクトリの作成
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # ログファイル名（日付付き）
        log_filename = f"sqlite_gui_tool_{datetime.now().strftime('%Y%m%d')}.log"
        log_path = log_dir / log_filename
        
        # ロガーの作成
        self._logger = logging.getLogger("SQLiteGUITool")
        self._logger.setLevel(logging.DEBUG)
        
        # 既存のハンドラーをクリア
        self._logger.handlers.clear()
        
        # ファイルハンドラーの作成
        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # コンソールハンドラーの作成
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # フォーマッターの作成
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # ハンドラーをロガーに追加
        self._logger.addHandler(file_handler)
        self._logger.addHandler(console_handler)
    
    @classmethod
    def debug(cls, message: str) -> None:
        """デバッグレベルのログを出力"""
        logger = cls()
        logger._logger.debug(message)
    
    @classmethod
    def info(cls, message: str) -> None:
        """情報レベルのログを出力"""
        logger = cls()
        logger._logger.info(message)
    
    @classmethod
    def warning(cls, message: str) -> None:
        """警告レベルのログを出力"""
        logger = cls()
        logger._logger.warning(message)
    
    @classmethod
    def error(cls, message: str) -> None:
        """エラーレベルのログを出力"""
        logger = cls()
        logger._logger.error(message)
    
    @classmethod
    def critical(cls, message: str) -> None:
        """重大エラーレベルのログを出力"""
        logger = cls()
        logger._logger.critical(message)
    
    @classmethod
    def log_function_call(cls, func_name: str, args: tuple = (), kwargs: dict = None) -> None:
        """関数呼び出しをログに記録"""
        kwargs = kwargs or {}
        args_str = ", ".join([str(arg) for arg in args])
        kwargs_str = ", ".join([f"{k}={v}" for k, v in kwargs.items()])
        
        params = []
        if args_str:
            params.append(args_str)
        if kwargs_str:
            params.append(kwargs_str)
        
        params_str = ", ".join(params)
        cls.debug(f"関数呼び出し: {func_name}({params_str})")
    
    @classmethod
    def log_performance(cls, func_name: str, execution_time: float) -> None:
        """パフォーマンス情報をログに記録"""
        cls.info(f"パフォーマンス: {func_name} - {execution_time:.3f}秒")


def log_function_calls(func):
    """関数呼び出しをログに記録するデコレータ"""
    def wrapper(*args, **kwargs):
        Logger.log_function_call(func.__name__, args, kwargs)
        return func(*args, **kwargs)
    return wrapper


def log_performance(func):
    """関数のパフォーマンスをログに記録するデコレータ"""
    import time
    
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time = time.time() - start_time
        Logger.log_performance(func.__name__, execution_time)
        return result
    return wrapper