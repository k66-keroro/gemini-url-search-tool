"""
メッセージボックスコンポーネント

統一されたメッセージ表示機能を提供します。
"""

from tkinter import messagebox
from typing import Optional, Any
from enum import Enum

from src.utils.logger import Logger
from src.utils.error_handler import ErrorHandler


class MessageType(Enum):
    """メッセージタイプの列挙"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    QUESTION = "question"


class MessageBox:
    """メッセージボックスクラス"""
    
    @staticmethod
    def show_info(
        title: str,
        message: str,
        detail: Optional[str] = None
    ) -> None:
        """
        情報メッセージを表示
        
        Args:
            title: タイトル
            message: メッセージ
            detail: 詳細メッセージ（オプション）
        """
        try:
            full_message = message
            if detail:
                full_message += f"\n\n詳細:\n{detail}"
            
            messagebox.showinfo(title, full_message)
            Logger.info(f"情報メッセージを表示: {title} - {message}")
            
        except Exception as e:
            Logger.error(f"情報メッセージ表示エラー: {str(e)}")
    
    @staticmethod
    def show_warning(
        title: str,
        message: str,
        detail: Optional[str] = None
    ) -> None:
        """
        警告メッセージを表示
        
        Args:
            title: タイトル
            message: メッセージ
            detail: 詳細メッセージ（オプション）
        """
        try:
            full_message = message
            if detail:
                full_message += f"\n\n詳細:\n{detail}"
            
            messagebox.showwarning(title, full_message)
            Logger.warning(f"警告メッセージを表示: {title} - {message}")
            
        except Exception as e:
            Logger.error(f"警告メッセージ表示エラー: {str(e)}")
    
    @staticmethod
    def show_error(
        title: str,
        message: str,
        detail: Optional[str] = None
    ) -> None:
        """
        エラーメッセージを表示
        
        Args:
            title: タイトル
            message: メッセージ
            detail: 詳細メッセージ（オプション）
        """
        try:
            full_message = message
            if detail:
                full_message += f"\n\n詳細:\n{detail}"
            
            messagebox.showerror(title, full_message)
            Logger.error(f"エラーメッセージを表示: {title} - {message}")
            
        except Exception as e:
            Logger.error(f"エラーメッセージ表示エラー: {str(e)}")
    
    @staticmethod
    def ask_yes_no(
        title: str,
        message: str,
        detail: Optional[str] = None
    ) -> bool:
        """
        はい/いいえの確認ダイアログを表示
        
        Args:
            title: タイトル
            message: メッセージ
            detail: 詳細メッセージ（オプション）
            
        Returns:
            「はい」が選択された場合True、「いいえ」の場合False
        """
        try:
            full_message = message
            if detail:
                full_message += f"\n\n詳細:\n{detail}"
            
            result = messagebox.askyesno(title, full_message)
            Logger.info(f"確認ダイアログの結果: {title} - {result}")
            return result
            
        except Exception as e:
            Logger.error(f"確認ダイアログ表示エラー: {str(e)}")
            return False
    
    @staticmethod
    def ask_ok_cancel(
        title: str,
        message: str,
        detail: Optional[str] = None
    ) -> bool:
        """
        OK/キャンセルの確認ダイアログを表示
        
        Args:
            title: タイトル
            message: メッセージ
            detail: 詳細メッセージ（オプション）
            
        Returns:
            「OK」が選択された場合True、「キャンセル」の場合False
        """
        try:
            full_message = message
            if detail:
                full_message += f"\n\n詳細:\n{detail}"
            
            result = messagebox.askokcancel(title, full_message)
            Logger.info(f"OK/キャンセルダイアログの結果: {title} - {result}")
            return result
            
        except Exception as e:
            Logger.error(f"OK/キャンセルダイアログ表示エラー: {str(e)}")
            return False
    
    @staticmethod
    def ask_retry_cancel(
        title: str,
        message: str,
        detail: Optional[str] = None
    ) -> bool:
        """
        再試行/キャンセルの確認ダイアログを表示
        
        Args:
            title: タイトル
            message: メッセージ
            detail: 詳細メッセージ（オプション）
            
        Returns:
            「再試行」が選択された場合True、「キャンセル」の場合False
        """
        try:
            full_message = message
            if detail:
                full_message += f"\n\n詳細:\n{detail}"
            
            result = messagebox.askretrycancel(title, full_message)
            Logger.info(f"再試行/キャンセルダイアログの結果: {title} - {result}")
            return result
            
        except Exception as e:
            Logger.error(f"再試行/キャンセルダイアログ表示エラー: {str(e)}")
            return False
    
    @staticmethod
    def ask_yes_no_cancel(
        title: str,
        message: str,
        detail: Optional[str] = None
    ) -> Optional[bool]:
        """
        はい/いいえ/キャンセルの確認ダイアログを表示
        
        Args:
            title: タイトル
            message: メッセージ
            detail: 詳細メッセージ（オプション）
            
        Returns:
            「はい」の場合True、「いいえ」の場合False、「キャンセル」の場合None
        """
        try:
            full_message = message
            if detail:
                full_message += f"\n\n詳細:\n{detail}"
            
            result = messagebox.askyesnocancel(title, full_message)
            Logger.info(f"はい/いいえ/キャンセルダイアログの結果: {title} - {result}")
            return result
            
        except Exception as e:
            Logger.error(f"はい/いいえ/キャンセルダイアログ表示エラー: {str(e)}")
            return None
    
    @staticmethod
    def show_database_connection_success(db_path: str, table_count: int) -> None:
        """
        データベース接続成功メッセージを表示
        
        Args:
            db_path: データベースファイルパス
            table_count: テーブル数
        """
        import os
        db_name = os.path.basename(db_path)
        MessageBox.show_info(
            "接続成功",
            f"データベース '{db_name}' に接続しました。",
            f"テーブル数: {table_count}"
        )
    
    @staticmethod
    def show_database_connection_error(error_message: str) -> None:
        """
        データベース接続エラーメッセージを表示
        
        Args:
            error_message: エラーメッセージ
        """
        MessageBox.show_error(
            "接続エラー",
            "データベースへの接続中にエラーが発生しました。",
            error_message
        )
    
    @staticmethod
    def show_query_success(row_count: int, execution_time: float) -> None:
        """
        クエリ実行成功メッセージを表示
        
        Args:
            row_count: 結果行数
            execution_time: 実行時間（秒）
        """
        MessageBox.show_info(
            "クエリ実行完了",
            f"クエリが正常に実行されました。",
            f"結果: {row_count:,}行 ({execution_time:.3f}秒)"
        )
    
    @staticmethod
    def show_query_error(error_message: str) -> None:
        """
        クエリ実行エラーメッセージを表示
        
        Args:
            error_message: エラーメッセージ
        """
        MessageBox.show_error(
            "クエリエラー",
            "クエリの実行中にエラーが発生しました。",
            error_message
        )
    
    @staticmethod
    def show_import_success(file_path: str, row_count: int, table_name: str) -> None:
        """
        インポート成功メッセージを表示
        
        Args:
            file_path: インポートファイルパス
            row_count: インポート行数
            table_name: テーブル名
        """
        import os
        file_name = os.path.basename(file_path)
        MessageBox.show_info(
            "インポート完了",
            f"データのインポートが完了しました。",
            f"ファイル: {file_name}\nテーブル: {table_name}\n行数: {row_count:,}行"
        )
    
    @staticmethod
    def show_import_error(file_path: str, error_message: str) -> None:
        """
        インポートエラーメッセージを表示
        
        Args:
            file_path: インポートファイルパス
            error_message: エラーメッセージ
        """
        import os
        file_name = os.path.basename(file_path)
        MessageBox.show_error(
            "インポートエラー",
            f"ファイル '{file_name}' のインポート中にエラーが発生しました。",
            error_message
        )
    
    @staticmethod
    def show_export_success(file_path: str, row_count: int) -> None:
        """
        エクスポート成功メッセージを表示
        
        Args:
            file_path: エクスポートファイルパス
            row_count: エクスポート行数
        """
        import os
        file_name = os.path.basename(file_path)
        MessageBox.show_info(
            "エクスポート完了",
            f"データのエクスポートが完了しました。",
            f"ファイル: {file_name}\n行数: {row_count:,}行"
        )
    
    @staticmethod
    def show_export_error(file_path: str, error_message: str) -> None:
        """
        エクスポートエラーメッセージを表示
        
        Args:
            file_path: エクスポートファイルパス
            error_message: エラーメッセージ
        """
        import os
        file_name = os.path.basename(file_path)
        MessageBox.show_error(
            "エクスポートエラー",
            f"ファイル '{file_name}' へのエクスポート中にエラーが発生しました。",
            error_message
        )
    
    @staticmethod
    def confirm_field_conversion(field_count: int) -> bool:
        """
        フィールド変換の確認ダイアログを表示
        
        Args:
            field_count: 変換対象フィールド数
            
        Returns:
            変換を実行する場合True
        """
        return MessageBox.ask_yes_no(
            "フィールド変換の確認",
            f"選択された {field_count} 個のフィールドを文字列型に変換します。",
            "この操作は元に戻せません。続行しますか？"
        )
    
    @staticmethod
    def show_field_conversion_success(success_count: int, total_count: int) -> None:
        """
        フィールド変換成功メッセージを表示
        
        Args:
            success_count: 成功した変換数
            total_count: 総変換数
        """
        MessageBox.show_info(
            "フィールド変換完了",
            f"フィールドの変換が完了しました。",
            f"成功: {success_count}/{total_count} 個のフィールド"
        )
    
    @staticmethod
    def show_field_conversion_error(error_message: str) -> None:
        """
        フィールド変換エラーメッセージを表示
        
        Args:
            error_message: エラーメッセージ
        """
        MessageBox.show_error(
            "フィールド変換エラー",
            "フィールドの変換中にエラーが発生しました。",
            error_message
        )
    
    @staticmethod
    def show_no_data_message(context: str = "データ") -> None:
        """
        データなしメッセージを表示
        
        Args:
            context: コンテキスト（データの種類）
        """
        MessageBox.show_info(
            "情報",
            f"{context}がありません。"
        )
    
    @staticmethod
    def show_large_data_warning(row_count: int, limit: int) -> bool:
        """
        大量データの警告メッセージを表示
        
        Args:
            row_count: データ行数
            limit: 表示制限数
            
        Returns:
            続行する場合True
        """
        return MessageBox.ask_yes_no(
            "大量データの警告",
            f"結果の行数が多いため、最初の {limit:,} 行のみ表示されます。",
            f"総行数: {row_count:,} 行\n続行しますか？"
        )
    
    @staticmethod
    def show_unsaved_changes_warning() -> Optional[bool]:
        """
        未保存変更の警告メッセージを表示
        
        Returns:
            保存する場合True、保存しない場合False、キャンセルの場合None
        """
        return MessageBox.ask_yes_no_cancel(
            "未保存の変更",
            "保存されていない変更があります。",
            "変更を保存しますか？"
        )