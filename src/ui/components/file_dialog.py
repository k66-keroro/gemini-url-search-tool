"""
ファイル選択ダイアログコンポーネント

ファイル選択、保存、ディレクトリ選択のダイアログ機能を提供します。
"""

import os
from pathlib import Path
from tkinter import filedialog
from typing import List, Optional, Tuple

from src.config.constants import FileFormats
from src.utils.logger import Logger
from src.utils.error_handler import ErrorHandler


class FileDialog:
    """ファイル選択ダイアログクラス"""
    
    @staticmethod
    def open_file(
        title: str = "ファイルを選択",
        filetypes: Optional[List[Tuple[str, str]]] = None,
        initial_dir: Optional[str] = None,
        multiple: bool = False
    ) -> Optional[str | List[str]]:
        """
        ファイル選択ダイアログを表示
        
        Args:
            title: ダイアログのタイトル
            filetypes: ファイルタイプのリスト [(表示名, 拡張子), ...]
            initial_dir: 初期ディレクトリ
            multiple: 複数選択を許可するかどうか
            
        Returns:
            選択されたファイルパス（複数選択時はリスト）、キャンセル時はNone
        """
        try:
            # デフォルトのファイルタイプ
            if filetypes is None:
                filetypes = [("すべてのファイル", "*.*")]
            
            # 初期ディレクトリの設定
            if initial_dir is None:
                initial_dir = str(Path.cwd())
            
            if multiple:
                # 複数選択
                file_paths = filedialog.askopenfilenames(
                    title=title,
                    filetypes=filetypes,
                    initialdir=initial_dir
                )
                result = list(file_paths) if file_paths else None
            else:
                # 単一選択
                result = filedialog.askopenfilename(
                    title=title,
                    filetypes=filetypes,
                    initialdir=initial_dir
                )
                result = result if result else None
            
            if result:
                Logger.debug(f"ファイルが選択されました: {result}")
            
            return result
            
        except Exception as e:
            ErrorHandler.handle_exception(e, context="ファイル選択ダイアログ")
            return None
    
    @staticmethod
    def save_file(
        title: str = "ファイルを保存",
        filetypes: Optional[List[Tuple[str, str]]] = None,
        initial_dir: Optional[str] = None,
        default_extension: str = "",
        initial_file: str = ""
    ) -> Optional[str]:
        """
        ファイル保存ダイアログを表示
        
        Args:
            title: ダイアログのタイトル
            filetypes: ファイルタイプのリスト
            initial_dir: 初期ディレクトリ
            default_extension: デフォルト拡張子
            initial_file: 初期ファイル名
            
        Returns:
            保存先ファイルパス、キャンセル時はNone
        """
        try:
            # デフォルトのファイルタイプ
            if filetypes is None:
                filetypes = [("すべてのファイル", "*.*")]
            
            # 初期ディレクトリの設定
            if initial_dir is None:
                initial_dir = str(Path.cwd())
            
            result = filedialog.asksaveasfilename(
                title=title,
                filetypes=filetypes,
                initialdir=initial_dir,
                defaultextension=default_extension,
                initialfile=initial_file
            )
            
            result = result if result else None
            
            if result:
                Logger.debug(f"保存先が選択されました: {result}")
            
            return result
            
        except Exception as e:
            ErrorHandler.handle_exception(e, context="ファイル保存ダイアログ")
            return None
    
    @staticmethod
    def select_directory(
        title: str = "フォルダを選択",
        initial_dir: Optional[str] = None
    ) -> Optional[str]:
        """
        ディレクトリ選択ダイアログを表示
        
        Args:
            title: ダイアログのタイトル
            initial_dir: 初期ディレクトリ
            
        Returns:
            選択されたディレクトリパス、キャンセル時はNone
        """
        try:
            # 初期ディレクトリの設定
            if initial_dir is None:
                initial_dir = str(Path.cwd())
            
            result = filedialog.askdirectory(
                title=title,
                initialdir=initial_dir
            )
            
            result = result if result else None
            
            if result:
                Logger.debug(f"ディレクトリが選択されました: {result}")
            
            return result
            
        except Exception as e:
            ErrorHandler.handle_exception(e, context="ディレクトリ選択ダイアログ")
            return None
    
    @staticmethod
    def open_database_file(initial_dir: Optional[str] = None) -> Optional[str]:
        """
        データベースファイル選択ダイアログを表示
        
        Args:
            initial_dir: 初期ディレクトリ
            
        Returns:
            選択されたデータベースファイルパス、キャンセル時はNone
        """
        filetypes = [
            ("SQLiteデータベース", "*.db *.sqlite *.sqlite3"),
            ("すべてのファイル", "*.*")
        ]
        
        return FileDialog.open_file(
            title="SQLiteデータベースを選択",
            filetypes=filetypes,
            initial_dir=initial_dir
        )
    
    @staticmethod
    def open_import_file(initial_dir: Optional[str] = None) -> Optional[str]:
        """
        インポートファイル選択ダイアログを表示
        
        Args:
            initial_dir: 初期ディレクトリ
            
        Returns:
            選択されたファイルパス、キャンセル時はNone
        """
        filetypes = [
            ("すべてのサポートされるファイル", "*.csv *.tsv *.txt *.xlsx *.xls"),
            ("CSVファイル", "*.csv"),
            ("TSVファイル", "*.tsv *.txt"),
            ("Excelファイル", "*.xlsx *.xls"),
            ("すべてのファイル", "*.*")
        ]
        
        return FileDialog.open_file(
            title="インポートするファイルを選択",
            filetypes=filetypes,
            initial_dir=initial_dir
        )
    
    @staticmethod
    def save_export_file(
        format_type: str = FileFormats.CSV,
        initial_dir: Optional[str] = None,
        initial_file: str = "export"
    ) -> Optional[str]:
        """
        エクスポートファイル保存ダイアログを表示
        
        Args:
            format_type: ファイル形式（CSV, Excel）
            initial_dir: 初期ディレクトリ
            initial_file: 初期ファイル名
            
        Returns:
            保存先ファイルパス、キャンセル時はNone
        """
        if format_type == FileFormats.CSV:
            filetypes = [("CSVファイル", "*.csv"), ("すべてのファイル", "*.*")]
            default_extension = ".csv"
            if not initial_file.endswith('.csv'):
                initial_file += ".csv"
        elif format_type == FileFormats.EXCEL:
            filetypes = [("Excelファイル", "*.xlsx"), ("すべてのファイル", "*.*")]
            default_extension = ".xlsx"
            if not initial_file.endswith('.xlsx'):
                initial_file += ".xlsx"
        else:
            filetypes = [("すべてのファイル", "*.*")]
            default_extension = ""
        
        return FileDialog.save_file(
            title="エクスポート先を選択",
            filetypes=filetypes,
            initial_dir=initial_dir,
            default_extension=default_extension,
            initial_file=initial_file
        )
    
    @staticmethod
    def validate_file_path(file_path: str) -> Tuple[bool, str]:
        """
        ファイルパスを検証
        
        Args:
            file_path: 検証するファイルパス
            
        Returns:
            tuple: (有効フラグ, エラーメッセージ)
        """
        try:
            path = Path(file_path)
            
            # ファイルの存在確認
            if not path.exists():
                return False, "ファイルが存在しません"
            
            # ファイルかどうか確認
            if not path.is_file():
                return False, "指定されたパスはファイルではありません"
            
            # 読み取り権限の確認
            if not os.access(file_path, os.R_OK):
                return False, "ファイルの読み取り権限がありません"
            
            return True, ""
            
        except Exception as e:
            return False, f"ファイルパスの検証エラー: {str(e)}"
    
    @staticmethod
    def validate_save_path(file_path: str) -> Tuple[bool, str]:
        """
        保存先パスを検証
        
        Args:
            file_path: 検証する保存先パス
            
        Returns:
            tuple: (有効フラグ, エラーメッセージ)
        """
        try:
            path = Path(file_path)
            
            # 親ディレクトリの存在確認
            if not path.parent.exists():
                return False, "保存先ディレクトリが存在しません"
            
            # 親ディレクトリの書き込み権限確認
            if not os.access(path.parent, os.W_OK):
                return False, "保存先ディレクトリの書き込み権限がありません"
            
            # ファイルが既に存在する場合の書き込み権限確認
            if path.exists() and not os.access(file_path, os.W_OK):
                return False, "ファイルの書き込み権限がありません"
            
            return True, ""
            
        except Exception as e:
            return False, f"保存先パスの検証エラー: {str(e)}"
    
    @staticmethod
    def get_file_info(file_path: str) -> dict:
        """
        ファイル情報を取得
        
        Args:
            file_path: ファイルパス
            
        Returns:
            ファイル情報の辞書
        """
        try:
            path = Path(file_path)
            
            if not path.exists():
                return {}
            
            stat = path.stat()
            
            return {
                "name": path.name,
                "size": stat.st_size,
                "modified": stat.st_mtime,
                "extension": path.suffix.lower(),
                "is_file": path.is_file(),
                "is_dir": path.is_dir()
            }
            
        except Exception as e:
            Logger.error(f"ファイル情報取得エラー: {str(e)}")
            return {}
    
    @staticmethod
    def get_recent_directory() -> str:
        """
        最近使用したディレクトリを取得
        
        Returns:
            最近使用したディレクトリパス
        """
        try:
            from src.config.settings import get_settings
            settings = get_settings()
            
            # 最後に接続したデータベースのディレクトリを取得
            last_db_path = settings.get_last_database_path()
            if last_db_path:
                return str(Path(last_db_path).parent)
            
            # デフォルトはカレントディレクトリ
            return str(Path.cwd())
            
        except Exception as e:
            Logger.error(f"最近使用したディレクトリの取得エラー: {str(e)}")
            return str(Path.cwd())