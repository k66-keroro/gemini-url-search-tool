"""
データベース接続管理モジュール

SQLiteデータベースへの接続と操作を管理します。
"""

import sqlite3
import time
from pathlib import Path
from typing import Any, List, Optional, Tuple, Union

from src.config.constants import Database
from src.config.settings import Settings
from src.utils.error_handler import ErrorHandler
from src.utils.logger import Logger


class DatabaseConnection:
    """データベース接続クラス"""
    
    def __init__(self):
        """初期化"""
        self.conn: Optional[sqlite3.Connection] = None
        self.cursor: Optional[sqlite3.Cursor] = None
        self.db_path: Optional[str] = None
        self.is_connected = False
        self.settings = Settings()
        self.logger = Logger.get_logger(__name__)
        self.error_handler = ErrorHandler()
    
    def connect(self, db_path: Union[str, Path]) -> bool:
        """
        データベースに接続
        
        Args:
            db_path: データベースファイルのパス
            
        Returns:
            接続成功の場合True、失敗の場合False
        """
        try:
            # 既存の接続を閉じる
            if self.is_connected:
                self.close()
            
            # パスを文字列に変換
            db_path_str = str(db_path)
            
            # ファイルの存在確認
            if not Path(db_path_str).exists():
                raise Exception(f"データベースファイルが見つかりません: {db_path_str}")
            
            # データベースに接続
            timeout = self.settings.get("database_connection_timeout", Database.DEFAULT_TIMEOUT)
            self.conn = sqlite3.connect(db_path_str, timeout=timeout)
            self.cursor = self.conn.cursor()
            self.db_path = db_path_str
            self.is_connected = True
            
            # PRAGMA設定を適用
            self._apply_pragma_settings()
            
            # 接続テスト
            self._test_connection()
            
            # 設定に最後の接続パスを保存
            self.settings.set('last_database_path', db_path_str)
            self.settings.save()
            
            self.logger.info(f"データベースに接続しました: {db_path_str}")
            return True
            
        except Exception as e:
            error_msg = f"データベース接続エラー: {str(e)}"
            self.logger.error(error_msg)
            self.error_handler.handle_error(e, error_msg)
            return False
    
    def close(self) -> None:
        """接続を閉じる"""
        try:
            if self.conn:
                self.conn.close()
                self.logger.info(f"データベース接続を閉じました: {self.db_path}")
            
            self.conn = None
            self.cursor = None
            self.db_path = None
            self.is_connected = False
            
        except Exception as e:
            self.logger.error(f"データベース接続の切断エラー: {str(e)}")
    
    def _apply_pragma_settings(self) -> None:
        """PRAGMA設定を適用"""
        try:
            for pragma, value in Database.PRAGMA_SETTINGS.items():
                self.cursor.execute(f"PRAGMA {pragma} = {value}")
            self.logger.debug("PRAGMA設定を適用しました")
        except Exception as e:
            self.logger.warning(f"PRAGMA設定の適用に失敗しました: {str(e)}")
    
    def _test_connection(self) -> None:
        """接続テスト"""
        try:
            self.cursor.execute("SELECT sqlite_version()")
            version = self.cursor.fetchone()[0]
            self.logger.debug(f"SQLiteバージョン: {version}")
        except Exception as e:
            raise Exception(f"接続テストに失敗しました: {str(e)}")
    
    def execute_query(
        self, 
        query: str, 
        params: Optional[Tuple] = None,
        fetch_results: bool = True
    ) -> Tuple[bool, Optional[List[Tuple]], Optional[str]]:
        """
        クエリを実行
        
        Args:
            query: 実行するSQLクエリ
            params: クエリパラメータ（オプション）
            fetch_results: 結果を取得するかどうか
            
        Returns:
            tuple: (成功フラグ, 結果, エラーメッセージ)
        """
        if not self.is_connected:
            return False, None, "データベースに接続されていません"
        
        try:
            start_time = time.time()
            
            # クエリを実行
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            
            # 結果を取得
            results = None
            if fetch_results:
                results = self.cursor.fetchall()
            
            execution_time = time.time() - start_time
            self.logger.debug(f"クエリ実行時間: {execution_time:.3f}秒")
            
            return True, results, None
            
        except sqlite3.Error as e:
            error_msg = f"SQLエラー: {str(e)}"
            self.logger.error(error_msg)
            return False, None, error_msg
        except Exception as e:
            error_msg = f"クエリ実行エラー: {str(e)}"
            self.logger.error(error_msg)
            return False, None, error_msg
    
    def get_column_names(self) -> Optional[List[str]]:
        """
        最後に実行したクエリの列名を取得
        
        Returns:
            列名のリスト、エラーの場合はNone
        """
        try:
            if self.cursor and self.cursor.description:
                return [description[0] for description in self.cursor.description]
            return None
        except Exception as e:
            self.logger.error(f"列名取得エラー: {str(e)}")
            return None
    
    def get_table_list(self) -> List[str]:
        """
        テーブル一覧を取得
        
        Returns:
            テーブル名のリスト
        """
        try:
            success, results, error = self.execute_query(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
            
            if success and results:
                return [row[0] for row in results]
            else:
                self.logger.error(f"テーブル一覧取得エラー: {error}")
                return []
                
        except Exception as e:
            self.logger.error(f"テーブル一覧取得エラー: {str(e)}")
            return []
    
    def get_table_info(self, table_name: str) -> Optional[List[Tuple]]:
        """
        テーブル情報を取得
        
        Args:
            table_name: テーブル名
            
        Returns:
            テーブル情報のリスト、エラーの場合はNone
        """
        try:
            success, results, error = self.execute_query(
                f"PRAGMA table_info({table_name})"
            )
            
            if success:
                return results
            else:
                self.logger.error(f"テーブル情報取得エラー: {error}")
                return None
                
        except Exception as e:
            self.logger.error(f"テーブル情報取得エラー: {str(e)}")
            return None
    
    def get_table_row_count(self, table_name: str) -> int:
        """
        テーブルの行数を取得
        
        Args:
            table_name: テーブル名
            
        Returns:
            行数、エラーの場合は0
        """
        try:
            success, results, error = self.execute_query(
                f"SELECT COUNT(*) FROM {table_name}"
            )
            
            if success and results:
                return results[0][0]
            else:
                self.logger.error(f"行数取得エラー: {error}")
                return 0
                
        except Exception as e:
            self.logger.error(f"行数取得エラー: {str(e)}")
            return 0
    
    def get_index_list(self, table_name: str) -> List[Tuple]:
        """
        テーブルのインデックス一覧を取得
        
        Args:
            table_name: テーブル名
            
        Returns:
            インデックス情報のリスト
        """
        try:
            success, results, error = self.execute_query(
                f"PRAGMA index_list({table_name})"
            )
            
            if success and results:
                return results
            else:
                self.logger.error(f"インデックス一覧取得エラー: {error}")
                return []
                
        except Exception as e:
            self.logger.error(f"インデックス一覧取得エラー: {str(e)}")
            return []
    
    def get_index_info(self, index_name: str) -> List[Tuple]:
        """
        インデックス情報を取得
        
        Args:
            index_name: インデックス名
            
        Returns:
            インデックス詳細情報のリスト
        """
        try:
            success, results, error = self.execute_query(
                f"PRAGMA index_info({index_name})"
            )
            
            if success and results:
                return results
            else:
                self.logger.error(f"インデックス情報取得エラー: {error}")
                return []
                
        except Exception as e:
            self.logger.error(f"インデックス情報取得エラー: {str(e)}")
            return []
    
    def get_create_sql(self, table_name: str) -> Optional[str]:
        """
        テーブルのCREATE文を取得
        
        Args:
            table_name: テーブル名
            
        Returns:
            CREATE文、エラーの場合はNone
        """
        try:
            success, results, error = self.execute_query(
                "SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
                (table_name,)
            )
            
            if success and results:
                return results[0][0]
            else:
                self.logger.error(f"CREATE文取得エラー: {error}")
                return None
                
        except Exception as e:
            self.logger.error(f"CREATE文取得エラー: {str(e)}")
            return None
    
    def begin_transaction(self) -> bool:
        """
        トランザクションを開始
        
        Returns:
            成功した場合True
        """
        try:
            success, _, error = self.execute_query("BEGIN TRANSACTION", fetch_results=False)
            if not success:
                self.logger.error(f"トランザクション開始エラー: {error}")
            return success
        except Exception as e:
            self.logger.error(f"トランザクション開始エラー: {str(e)}")
            return False
    
    def commit_transaction(self) -> bool:
        """
        トランザクションをコミット
        
        Returns:
            成功した場合True
        """
        try:
            if self.conn:
                self.conn.commit()
                self.logger.debug("トランザクションをコミットしました")
                return True
            return False
        except Exception as e:
            Logger.error(f"トランザクションコミットエラー: {str(e)}")
            return False
    
    def rollback_transaction(self) -> bool:
        """
        トランザクションをロールバック
        
        Returns:
            成功した場合True
        """
        try:
            if self.conn:
                self.conn.rollback()
                Logger.debug("トランザクションをロールバックしました")
                return True
            return False
        except Exception as e:
            Logger.error(f"トランザクションロールバックエラー: {str(e)}")
            return False
    
    def vacuum(self) -> bool:
        """
        データベースをVACUUM
        
        Returns:
            成功した場合True
        """
        try:
            success, _, error = self.execute_query("VACUUM", fetch_results=False)
            if success:
                Logger.info("データベースをVACUUMしました")
            else:
                Logger.error(f"VACUUMエラー: {error}")
            return success
        except Exception as e:
            Logger.error(f"VACUUMエラー: {str(e)}")
            return False
    
    def analyze(self) -> bool:
        """
        データベースをANALYZE
        
        Returns:
            成功した場合True
        """
        try:
            success, _, error = self.execute_query("ANALYZE", fetch_results=False)
            if success:
                Logger.info("データベースをANALYZEしました")
            else:
                Logger.error(f"ANALYZEエラー: {error}")
            return success
        except Exception as e:
            Logger.error(f"ANALYZEエラー: {str(e)}")
            return False
    
    def __enter__(self):
        """コンテキストマネージャーのエントリー"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキストマネージャーの終了"""
        self.close()