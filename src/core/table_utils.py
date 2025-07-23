"""
テーブル操作ユーティリティモジュール

テーブル構造の取得やテーブル名の変換などの機能を提供します。
"""

import re
import time
from typing import Dict, List, Optional, Tuple, Any

from src.core.db_connection import DatabaseConnection
from src.utils.string_utils import StringUtils
from src.utils.logger import Logger
from src.utils.error_handler import ErrorHandler


class TableInfo:
    """テーブル情報を格納するクラス"""
    
    def __init__(self, name: str, row_count: int = 0, column_count: int = 0):
        self.name = name
        self.row_count = row_count
        self.column_count = column_count
        self.columns: List[ColumnInfo] = []
        self.indexes: List[IndexInfo] = []
        self.create_sql: Optional[str] = None


class ColumnInfo:
    """カラム情報を格納するクラス"""
    
    def __init__(
        self, 
        cid: int, 
        name: str, 
        type_: str, 
        not_null: bool = False, 
        default_value: Optional[str] = None, 
        primary_key: bool = False
    ):
        self.cid = cid
        self.name = name
        self.type = type_
        self.not_null = not_null
        self.default_value = default_value
        self.primary_key = primary_key


class IndexInfo:
    """インデックス情報を格納するクラス"""
    
    def __init__(self, name: str, unique: bool = False, columns: List[str] = None):
        self.name = name
        self.unique = unique
        self.columns = columns or []


class TableUtils:
    """テーブル操作ユーティリティクラス"""
    
    def __init__(self, db_connection: DatabaseConnection):
        """
        初期化
        
        Args:
            db_connection: データベース接続オブジェクト
        """
        self.db_connection = db_connection
        self.logger = Logger.get_logger(__name__)
        self.error_handler = ErrorHandler()
    
    def get_table_structure(self, table_name: str) -> Optional[TableInfo]:
        """
        テーブル構造を取得
        
        Args:
            table_name: テーブル名
            
        Returns:
            テーブル情報、エラーの場合はNone
        """
        try:
            # テーブル情報を作成
            table_info = TableInfo(table_name)
            
            # 行数を取得
            table_info.row_count = self.db_connection.get_table_row_count(table_name)
            
            # カラム情報を取得
            columns_data = self.db_connection.get_table_info(table_name)
            if columns_data:
                table_info.column_count = len(columns_data)
                for col_data in columns_data:
                    column = ColumnInfo(
                        cid=col_data[0],
                        name=col_data[1],
                        type_=col_data[2],
                        not_null=bool(col_data[3]),
                        default_value=col_data[4],
                        primary_key=bool(col_data[5])
                    )
                    table_info.columns.append(column)
            
            # インデックス情報を取得
            indexes_data = self.db_connection.get_index_list(table_name)
            if indexes_data:
                for idx_data in indexes_data:
                    index_name = idx_data[1]
                    is_unique = bool(idx_data[2])
                    
                    # インデックスのカラム情報を取得
                    index_columns_data = self.db_connection.get_index_info(index_name)
                    column_names = []
                    
                    if index_columns_data:
                        # カラムインデックスからカラム名を取得
                        for idx_col_data in index_columns_data:
                            col_idx = idx_col_data[1]
                            if col_idx < len(table_info.columns):
                                column_names.append(table_info.columns[col_idx].name)
                    
                    index = IndexInfo(
                        name=index_name,
                        unique=is_unique,
                        columns=column_names
                    )
                    table_info.indexes.append(index)
            
            # CREATE文を取得
            table_info.create_sql = self.db_connection.get_create_sql(table_name)
            
            return table_info
            
        except Exception as e:
            self.error_handler = ErrorHandler()
            self.error_handler.handle_error(
                e, 
                f"テーブル構造取得: {table_name}"
            )
            return None
    
    def get_all_tables_info(self) -> List[TableInfo]:
        """
        全テーブルの情報を取得
        
        Returns:
            テーブル情報のリスト
        """
        tables_info = []
        
        try:
            table_names = self.db_connection.get_table_list()
            
            for table_name in table_names:
                table_info = self.get_table_structure(table_name)
                if table_info:
                    tables_info.append(table_info)
            
            self.logger.info(f"{len(tables_info)}個のテーブル情報を取得しました")
            
        except Exception as e:
            self.error_handler = ErrorHandler()
            self.error_handler.handle_error(
                e, 
                "全テーブル情報取得"
            )
        
        return tables_info
    
    def get_table_sample_data(
        self, 
        table_name: str, 
        limit: int = 100
    ) -> Tuple[List[str], List[Tuple]]:
        """
        テーブルのサンプルデータを取得
        
        Args:
            table_name: テーブル名
            limit: 取得する行数の上限
            
        Returns:
            tuple: (列名のリスト, データのリスト)
        """
        try:
            success, results, error = self.db_connection.execute_query(
                f"SELECT * FROM {table_name} LIMIT {limit}"
            )
            
            if success and results is not None:
                column_names = self.db_connection.get_column_names() or []
                return column_names, results
            else:
                self.logger.error(f"サンプルデータ取得エラー: {error}")
                return [], []
                
        except Exception as e:
            self.error_handler = ErrorHandler()
            self.error_handler.handle_error(
                e, 
                f"サンプルデータ取得: {table_name}"
            )
            return [], []
    
    def analyze_column_data_type(self, table_name: str, column_name: str) -> Dict[str, Any]:
        """
        カラムのデータ型を分析
        
        Args:
            table_name: テーブル名
            column_name: カラム名
            
        Returns:
            分析結果の辞書
        """
        try:
            # カラムの基本情報を取得
            table_info = self.get_table_structure(table_name)
            if not table_info:
                return {}
            
            column_info = None
            for col in table_info.columns:
                if col.name == column_name:
                    column_info = col
                    break
            
            if not column_info:
                return {}
            
            # サンプルデータを取得
            success, results, error = self.db_connection.execute_query(
                f"SELECT {column_name} FROM {table_name} WHERE {column_name} IS NOT NULL LIMIT 1000"
            )
            
            if not success or not results:
                return {
                    "column_name": column_name,
                    "declared_type": column_info.type,
                    "sample_count": 0
                }
            
            # データ型を分析
            sample_values = [row[0] for row in results]
            analysis = {
                "column_name": column_name,
                "declared_type": column_info.type,
                "sample_count": len(sample_values),
                "sample_values": sample_values[:10],  # 最初の10個のサンプル
                "has_leading_zeros": False,
                "has_trailing_minus": False,
                "all_numeric": True,
                "all_integer": True
            }
            
            # サンプル値を分析
            for value in sample_values:
                str_value = str(value)
                
                # 先頭に0があるかチェック
                if str_value.startswith('0') and len(str_value) > 1 and str_value.isdigit():
                    analysis["has_leading_zeros"] = True
                
                # 末尾にマイナスがあるかチェック
                if str_value.endswith('-'):
                    analysis["has_trailing_minus"] = True
                
                # 数値かどうかチェック
                try:
                    float(str_value.replace('-', ''))
                except ValueError:
                    analysis["all_numeric"] = False
                
                # 整数かどうかチェック
                try:
                    int(str_value.replace('-', ''))
                except ValueError:
                    analysis["all_integer"] = False
            
            return analysis
            
        except Exception as e:
            self.error_handler = ErrorHandler()
            self.error_handler.handle_error(
                e, 
                f"カラムデータ型分析: {table_name}.{column_name}"
            )
            return {}
    
    def find_code_fields(self) -> List[Dict[str, Any]]:
        """
        コードフィールドを検出
        
        Returns:
            コードフィールド情報のリスト
        """
        code_fields = []
        
        try:
            tables_info = self.get_all_tables_info()
            
            for table_info in tables_info:
                for column in table_info.columns:
                    # カラム名でコードフィールドを判定
                    column_name_lower = column.name.lower()
                    is_code_field = (
                        'code' in column_name_lower or
                        'コード' in column_name_lower or
                        column_name_lower.endswith('id') or
                        '番号' in column_name_lower or
                        column_name_lower.endswith('no')
                    )
                    
                    # 数値型でコードフィールドの可能性がある場合
                    if is_code_field and column.type.upper() in ['INTEGER', 'REAL', 'NUMERIC']:
                        analysis = self.analyze_column_data_type(table_info.name, column.name)
                        
                        # 変換が必要な理由を判定
                        reasons = []
                        if analysis.get("has_leading_zeros"):
                            reasons.append("先頭に0を含む値が存在")
                        if analysis.get("has_trailing_minus"):
                            reasons.append("末尾にマイナス記号を含む値が存在")
                        if column.type.upper() in ['INTEGER', 'REAL']:
                            reasons.append("数値型で保存されたコードフィールド")
                        
                        if reasons:
                            code_fields.append({
                                "table": table_info.name,
                                "column": column.name,
                                "current_type": column.type,
                                "reason": ", ".join(reasons),
                                "sample_values": analysis.get("sample_values", [])
                            })
            
            self.logger.info(f"{len(code_fields)}個のコードフィールドを検出しました")
            
        except Exception as e:
            self.error_handler = ErrorHandler()
            self.error_handler.handle_error(
                e, 
                "コードフィールド検出"
            )
        
        return code_fields
    
    def convert_column_to_text(self, table_name: str, column_name: str) -> Tuple[bool, Optional[str]]:
        """
        カラムを文字列型に変換
        
        Args:
            table_name: テーブル名
            column_name: カラム名
            
        Returns:
            tuple: (成功フラグ, エラーメッセージ)
        """
        try:
            # トランザクション開始
            if not self.db_connection.begin_transaction():
                return False, "トランザクションの開始に失敗しました"
            
            # 一時テーブル名を生成
            temp_table_name = f"{table_name}_temp_{int(time.time())}"
            
            # 元のテーブル構造を取得
            table_info = self.get_table_structure(table_name)
            if not table_info:
                self.db_connection.rollback_transaction()
                return False, "テーブル構造の取得に失敗しました"
            
            # 新しいテーブル構造を作成（対象カラムをTEXT型に変更）
            new_columns = []
            for col in table_info.columns:
                if col.name == column_name:
                    # 対象カラムをTEXT型に変更
                    col_def = f"{col.name} TEXT"
                    if col.not_null:
                        col_def += " NOT NULL"
                    if col.default_value:
                        col_def += f" DEFAULT {col.default_value}"
                else:
                    # その他のカラムはそのまま
                    col_def = f"{col.name} {col.type}"
                    if col.not_null:
                        col_def += " NOT NULL"
                    if col.default_value:
                        col_def += f" DEFAULT {col.default_value}"
                    if col.primary_key:
                        col_def += " PRIMARY KEY"
                
                new_columns.append(col_def)
            
            # 一時テーブルを作成
            create_temp_sql = f"CREATE TABLE {temp_table_name} ({', '.join(new_columns)})"
            success, _, error = self.db_connection.execute_query(create_temp_sql, fetch_results=False)
            if not success:
                self.db_connection.rollback_transaction()
                return False, f"一時テーブルの作成に失敗しました: {error}"
            
            # データを一時テーブルにコピー
            column_names = [col.name for col in table_info.columns]
            copy_sql = f"INSERT INTO {temp_table_name} SELECT {', '.join(column_names)} FROM {table_name}"
            success, _, error = self.db_connection.execute_query(copy_sql, fetch_results=False)
            if not success:
                self.db_connection.rollback_transaction()
                return False, f"データのコピーに失敗しました: {error}"
            
            # 元のテーブルを削除
            drop_sql = f"DROP TABLE {table_name}"
            success, _, error = self.db_connection.execute_query(drop_sql, fetch_results=False)
            if not success:
                self.db_connection.rollback_transaction()
                return False, f"元のテーブルの削除に失敗しました: {error}"
            
            # 一時テーブルを元の名前にリネーム
            rename_sql = f"ALTER TABLE {temp_table_name} RENAME TO {table_name}"
            success, _, error = self.db_connection.execute_query(rename_sql, fetch_results=False)
            if not success:
                self.db_connection.rollback_transaction()
                return False, f"テーブルのリネームに失敗しました: {error}"
            
            # トランザクションをコミット
            if not self.db_connection.commit_transaction():
                return False, "トランザクションのコミットに失敗しました"
            
            self.logger.info(f"カラムを文字列型に変換しました: {table_name}.{column_name}")
            return True, None
            
        except Exception as e:
            self.db_connection.rollback_transaction()
            error_msg = f"カラム変換エラー: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg


def get_sanitized_table_name(original_name: str) -> str:
    """
    テーブル名を適切に変換
    
    Args:
        original_name: 元のテーブル名
        
    Returns:
        変換後のテーブル名
    """
    return StringUtils.sanitize_table_name(original_name)