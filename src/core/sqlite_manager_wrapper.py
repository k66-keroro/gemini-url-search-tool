"""
SQLiteManager Wrapper

This module provides a wrapper for the SQLiteManager class that works with the modular GUI tool.
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any, Union, List, Tuple

# Create a simple logger for the GUI tool
class SimpleLogger:
    @staticmethod
    def get_logger(name):
        logger = logging.getLogger(name)
        if not logger.handlers:
            # Create console handler
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

# Simple error handler
class SimpleErrorHandler:
    def handle_error(self, error, message):
        logger = SimpleLogger.get_logger(__name__)
        logger.error(f"{message}: {error}")
        import traceback
        logger.error(traceback.format_exc())

# Simple string utils
class SimpleStringUtils:
    @staticmethod
    def sanitize_table_name(table_name: str) -> str:
        """
        テーブル名を適切に変換（日本語や特殊文字を避ける）

        Args:
            table_name: 元のテーブル名

        Returns:
            変換後のテーブル名
        """
        import re

        # 日本語文字を含むかチェック
        has_japanese = re.search(r'[ぁ-んァ-ン一-龥]', table_name)

        # 日本語文字を含む場合は、プレフィックスを付ける
        if has_japanese:
            sanitized = f"t_{hash(table_name) % 10000:04d}"
        else:
            # 英数字以外の文字を_に置換
            sanitized = re.sub(r'[^a-zA-Z0-9]', '_', table_name)

            # 連続する_を単一の_に置換
            sanitized = re.sub(r'_+', '_', sanitized)

            # 先頭が数字の場合、t_を付ける
            if sanitized and sanitized[0].isdigit():
                sanitized = f"t_{sanitized}"

            # 先頭と末尾の_を削除
            sanitized = sanitized.strip('_')

        return sanitized

# Try to import the real SQLiteManager
try:
    import sys
    import os
    from pathlib import Path
    
    # Get the project root
    wrapper_dir = Path(os.path.abspath(os.path.dirname(__file__)))
    project_root = wrapper_dir.parents[1]  # src/core の1つ上
    
    # Add project root to sys.path if not already there
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    # Import the real SQLiteManager
    try:
        from src.core.sqlite_manager import SQLiteManager as RealSQLiteManager
        REAL_MANAGER_AVAILABLE = True
    except ImportError as import_error:
        REAL_MANAGER_AVAILABLE = False
        import_error_msg = str(import_error)
    
    class SQLiteManager:
        """SQLiteデータベース管理クラス（ラッパー）"""
        
        def __init__(self, db_path: str = None):
            self.logger = SimpleLogger.get_logger(__name__)
            self.error_handler = SimpleErrorHandler()
            
            # プロジェクトルートを設定
            self.project_root = project_root
            
            # デフォルトのデータベースパス
            if db_path is None:
                db_path = str(project_root / 'data' / 'sqlite' / 'main.db')
            
            # 実際のSQLiteManagerを初期化
            try:
                if REAL_MANAGER_AVAILABLE:
                    self.real_manager = RealSQLiteManager()  # 引数なしで初期化
                    self.logger.info(f"SQLiteManager初期化完了: {db_path}")
                else:
                    self.logger.warning(f"実際のSQLiteManagerが利用できません: {import_error_msg}")
                    self.real_manager = None
            except Exception as e:
                self.logger.error(f"SQLiteManager初期化エラー: {e}")
                self.real_manager = None
                
        def process_file(self, file_path: Path, db_path: str = None) -> bool:
            """ファイルを処理してSQLiteに保存"""
            if not self.real_manager:
                self.logger.error("SQLiteManagerが初期化されていません")
                return False
                
            try:
                self.logger.info(f"ファイル処理開始: {file_path}")
                
                # デフォルトのdb_pathを使用
                if db_path is None:
                    db_path = str(self.project_root / 'data' / 'sqlite' / 'main.db')
                
                # 実際のSQLiteManagerでファイルを処理
                success = self.real_manager.process_file(file_path, db_path)
                
                if success:
                    self.logger.info(f"ファイル処理完了: {file_path}")
                else:
                    self.logger.error(f"ファイル処理失敗: {file_path}")
                
                return success
                
            except Exception as e:
                self.error_handler.handle_error(e, f"ファイル処理エラー: {file_path}")
                return False
                
        def get_table_name_for_file(self, file_path: Path) -> str:
            """ファイルに対応するテーブル名を取得"""
            if not self.real_manager:
                # フォールバック: ファイル名からテーブル名を生成
                table_name = file_path.stem
                return self.sanitize_table_name(table_name)
            
            try:
                # 実際のSQLiteManagerから取得
                return self.real_manager.get_table_name_for_file(file_path)
            except Exception as e:
                self.logger.error(f"テーブル名取得エラー: {e}")
                # フォールバック
                table_name = file_path.stem
                return self.sanitize_table_name(table_name)
                
        def finalize_database(self):
            """データベースの最終化処理（インデックス作成など）"""
            if not self.real_manager:
                self.logger.warning("SQLiteManagerが初期化されていません")
                return
                
            try:
                self.real_manager.finalize_database()
                self.logger.info("データベース最終化完了")
            except Exception as e:
                self.error_handler.handle_error(e, "データベース最終化エラー")
                
        def sanitize_table_name(self, table_name: str) -> str:
            """テーブル名を適切に変換"""
            if self.real_manager and hasattr(self.real_manager, 'sanitize_table_name'):
                return self.real_manager.sanitize_table_name(table_name)
            else:
                return SimpleStringUtils.sanitize_table_name(table_name)

except ImportError as e:
    # Fallback to simplified implementation
    class SQLiteManager:
        """SQLiteデータベース管理クラス（簡易版）"""
        
        def __init__(self, db_path: str = None):
            self.logger = SimpleLogger.get_logger(__name__)
            self.error_handler = SimpleErrorHandler()
            self.logger.warning("実際のSQLiteManagerをインポートできませんでした。簡易版を使用します。")
            
        def process_file(self, file_path: Path, db_path: str = None) -> bool:
            """ファイルを処理してSQLiteに保存（簡易版）"""
            try:
                self.logger.info(f"ファイル処理開始（簡易版）: {file_path}")
                # 簡易実装: 実際の処理は行わない
                self.logger.warning(f"簡易版のため実際の処理は行われません: {file_path}")
                return False
            except Exception as e:
                self.error_handler.handle_error(e, f"ファイル処理エラー: {file_path}")
                return False
                
        def get_table_name_for_file(self, file_path: Path) -> str:
            """ファイルに対応するテーブル名を取得（簡易版）"""
            table_name = file_path.stem
            return self.sanitize_table_name(table_name)
                
        def finalize_database(self):
            """データベースの最終化処理（簡易版）"""
            self.logger.warning("簡易版のため最終化処理は行われません")
                
        def sanitize_table_name(self, table_name: str) -> str:
            """テーブル名を適切に変換"""
            return SimpleStringUtils.sanitize_table_name(table_name)