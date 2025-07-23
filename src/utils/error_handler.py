"""
エラーハンドリングモジュール

SQLite GUI Toolで発生する例外の統一的な処理を提供します。
"""

import traceback
from typing import Optional, Tuple, Any
from tkinter import messagebox


class ErrorHandler:
    """エラーハンドリングクラス"""
    
    @staticmethod
    def handle_exception(
        exception: Exception,
        context: str = "",
        show_message: bool = True,
        log_error: bool = True
    ) -> Tuple[bool, str]:
        """
        例外を統一的に処理する
        
        Args:
            exception: 発生した例外
            context: エラーが発生したコンテキスト
            show_message: エラーメッセージを表示するかどうか
            log_error: エラーをログに記録するかどうか
            
        Returns:
            tuple: (処理成功フラグ, エラーメッセージ)
        """
        error_message = str(exception)
        full_context = f"{context}: {error_message}" if context else error_message
        
        # ログに記録
        if log_error:
            ErrorHandler._log_error(full_context, exception)
        
        # メッセージボックスを表示
        if show_message:
            ErrorHandler._show_error_message(full_context)
        
        return False, error_message
    
    @staticmethod
    def _log_error(message: str, exception: Exception) -> None:
        """
        エラーをログに記録する
        
        Args:
            message: エラーメッセージ
            exception: 発生した例外
        """
        print(f"エラー: {message}")
        print(traceback.format_exc())
    
    @staticmethod
    def _show_error_message(message: str) -> None:
        """
        エラーメッセージを表示する
        
        Args:
            message: 表示するメッセージ
        """
        messagebox.showerror("エラー", message)
    
    @staticmethod
    def safe_execute(
        func,
        *args,
        context: str = "",
        default_return: Any = None,
        show_message: bool = True,
        **kwargs
    ) -> Tuple[bool, Any]:
        """
        関数を安全に実行する
        
        Args:
            func: 実行する関数
            *args: 関数の引数
            context: エラーが発生したコンテキスト
            default_return: エラー時のデフォルト戻り値
            show_message: エラーメッセージを表示するかどうか
            **kwargs: 関数のキーワード引数
            
        Returns:
            tuple: (成功フラグ, 戻り値またはエラーメッセージ)
        """
        try:
            result = func(*args, **kwargs)
            return True, result
        except Exception as e:
            ErrorHandler.handle_exception(
                e, 
                context=context or f"{func.__name__}の実行",
                show_message=show_message
            )
            return False, default_return


class DatabaseError(Exception):
    """データベース関連のエラー"""
    pass


class FileProcessingError(Exception):
    """ファイル処理関連のエラー"""
    pass


class UIError(Exception):
    """UI関連のエラー"""
    pass


class ValidationError(Exception):
    """バリデーション関連のエラー"""
    pass