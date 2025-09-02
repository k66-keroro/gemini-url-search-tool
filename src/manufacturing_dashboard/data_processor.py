"""
データ処理クラス - 既存SQLiteManagerを拡張した製造ダッシュボード用データ処理
"""

import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta
import json

from ..utils.logger import Logger
from ..utils.error_handler import ErrorHandler


class DataProcessor:
    """製造ダッシュボード用データ処理クラス"""
    
    def __init__(self, db_path: str = "data/sqlite/manufacturing.db"):
        self.db_path = db_path
        self.logger = Logger()
        self.error_handler = ErrorHandler()
        
    def process_night_batch_files(self, file_path: str) -> Dict[str, Any]:
        """夜間処理テキストファイルを処理"""
        try:
            Logger.info(f"夜間処理ファイル処理開始: {file_path}")
            
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                raise FileNotFoundError(f"ファイルが見つかりません: {file_path}")
            
            # ファイルを処理してSQLiteに保存
            success = self._process_file_basic(file_path_obj)
            
            if success:
                # 処理結果の統計情報を取得
                stats = self._get_processing_stats(file_path_obj.stem)
                
                result = {
                    "status": "success",
                    "file_path": file_path,
                    "table_name": stats.get("table_name"),
                    "rows_processed": stats.get("row_count", 0),
                    "processing_time": stats.get("processing_time"),
                    "timestamp": datetime.now().isoformat()
                }
                
                Logger.info(f"夜間処理ファイル処理完了: {file_path}")
                return result
            else:
                raise Exception("ファイル処理に失敗しました")
                
        except Exception as e:
            self.error_handler.handle_error(e, f"夜間処理ファイル処理エラー: {file_path}")
            return {
                "status": "error",
                "file_path": file_path,
                "error_message": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def process_hourly_data(self, file_path: str) -> Dict[str, Any]:
        """1時間ごと実績データを処理"""
        try:
            Logger.info(f"1時間ごと実績データ処理開始: {file_path}")
            
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                raise FileNotFoundError(f"ファイルが見つかりません: {file_path}")
            
            # ファイルを読み込み
            df = self._read_file_basic(file_path_obj)
            
            if df is None or df.empty:
                raise Exception("データの読み込みに失敗しました")
            
            # 時間ごとデータ用のテーブル名を生成
            table_name = f"hourly_data_{datetime.now().strftime('%Y%m%d_%H')}"
            
            # タイムスタンプを追加
            df['processed_at'] = datetime.now()
            
            # SQLiteに保存
            self._save_to_sqlite_basic(df, table_name)
            
            result = {
                "status": "success",
                "file_path": file_path,
                "table_name": table_name,
                "rows_processed": len(df),
                "timestamp": datetime.now().isoformat()
            }
            
            Logger.info(f"1時間ごと実績データ処理完了: {file_path}")
            return result
            
        except Exception as e:
            self.error_handler.handle_error(e, f"1時間ごと実績データ処理エラー: {file_path}")
            return {
                "status": "error",
                "file_path": file_path,
                "error_message": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def export_report(self, report_type: str, format: str = "excel", 
                     output_path: Optional[str] = None) -> str:
        """レポートをエクスポート"""
        try:
            Logger.info(f"レポートエクスポート開始: {report_type} ({format})")
            
            # レポートデータを取得
            data = self._get_report_data(report_type)
            
            if data is None or data.empty:
                raise Exception(f"レポートデータが見つかりません: {report_type}")
            
            # 出力パスを生成
            if output_path is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_path = f"reports/{report_type}_{timestamp}.{format}"
            
            # フォーマットに応じてエクスポート
            output_path_obj = Path(output_path)
            output_path_obj.parent.mkdir(parents=True, exist_ok=True)
            
            if format.lower() == "excel":
                data.to_excel(output_path_obj, index=False)
            elif format.lower() == "csv":
                data.to_csv(output_path_obj, index=False, encoding='utf-8-sig')
            else:
                raise ValueError(f"サポートされていないフォーマット: {format}")
            
            Logger.info(f"レポートエクスポート完了: {output_path}")
            return str(output_path_obj.absolute())
            
        except Exception as e:
            self.error_handler.handle_error(e, f"レポートエクスポートエラー: {report_type}")
            raise
    
    def get_database_info(self) -> Dict[str, Any]:
        """データベース情報を取得"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # テーブル一覧を取得
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            # 各テーブルの行数を取得
            table_info = {}
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM `{table}`")
                row_count = cursor.fetchone()[0]
                table_info[table] = {"row_count": row_count}
            
            conn.close()
            
            return {
                "database_path": self.db_path,
                "table_count": len(tables),
                "tables": table_info,
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.error_handler.handle_error(e, "データベース情報取得エラー")
            return {}
    
    def _get_processing_stats(self, table_name: str) -> Dict[str, Any]:
        """処理統計情報を取得"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # テーブルの行数を取得
            cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
            row_count = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                "table_name": table_name,
                "row_count": row_count,
                "processing_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            Logger.error(f"処理統計情報取得エラー: {e}")
            return {}
    
    def _get_report_data(self, report_type: str) -> Optional[pd.DataFrame]:
        """レポートデータを取得"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # レポートタイプに応じてクエリを実行
            if report_type == "production_summary":
                query = """
                SELECT * FROM production_data 
                WHERE date >= date('now', '-7 days')
                ORDER BY date DESC
                """
            elif report_type == "error_summary":
                query = """
                SELECT * FROM error_log 
                WHERE created_at >= datetime('now', '-24 hours')
                ORDER BY created_at DESC
                """
            elif report_type == "inventory_summary":
                query = """
                SELECT * FROM inventory_data 
                WHERE last_updated >= date('now', '-1 day')
                ORDER BY item_code
                """
            else:
                raise ValueError(f"未知のレポートタイプ: {report_type}")
            
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            return df
            
        except Exception as e:
            Logger.error(f"レポートデータ取得エラー: {e}")
            return None
    
    def validate_data_integrity(self) -> List[Dict[str, Any]]:
        """データ整合性をチェック"""
        try:
            Logger.info("データ整合性チェック開始")
            
            issues = []
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # テーブル一覧を取得
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            for table in tables:
                # 各テーブルの基本チェック
                try:
                    # NULL値の多いカラムをチェック
                    cursor.execute(f"PRAGMA table_info(`{table}`)")
                    columns = [col[1] for col in cursor.fetchall()]
                    
                    for column in columns:
                        cursor.execute(f"SELECT COUNT(*) FROM `{table}` WHERE `{column}` IS NULL")
                        null_count = cursor.fetchone()[0]
                        
                        cursor.execute(f"SELECT COUNT(*) FROM `{table}`")
                        total_count = cursor.fetchone()[0]
                        
                        if total_count > 0 and null_count / total_count > 0.5:
                            issues.append({
                                "type": "high_null_ratio",
                                "table": table,
                                "column": column,
                                "null_ratio": null_count / total_count,
                                "description": f"カラム {column} のNULL値の割合が高い ({null_count}/{total_count})"
                            })
                
                except Exception as e:
                    issues.append({
                        "type": "table_check_error",
                        "table": table,
                        "error": str(e),
                        "description": f"テーブル {table} のチェック中にエラーが発生"
                    })
            
            conn.close()
            
            Logger.info(f"データ整合性チェック完了: {len(issues)}件の問題を検出")
            return issues
            
        except Exception as e:
            self.error_handler.handle_error(e, "データ整合性チェックエラー")
            return []
    
    def _process_file_basic(self, file_path: Path) -> bool:
        """基本的なファイル処理"""
        try:
            # ファイルを読み込み
            df = self._read_file_basic(file_path)
            if df is None or df.empty:
                return False
            
            # テーブル名を生成
            table_name = file_path.stem.lower().replace(' ', '_').replace('-', '_')
            
            # SQLiteに保存
            self._save_to_sqlite_basic(df, table_name)
            return True
            
        except Exception as e:
            Logger.error(f"ファイル処理エラー: {e}")
            return False
    
    def _read_file_basic(self, file_path: Path) -> Optional[pd.DataFrame]:
        """基本的なファイル読み込み"""
        try:
            suffix = file_path.suffix.lower()
            
            if suffix == '.csv':
                return pd.read_csv(file_path, encoding='utf-8')
            elif suffix == '.txt':
                return pd.read_csv(file_path, sep='\t', encoding='utf-8')
            elif suffix in ['.xlsx', '.xls']:
                return pd.read_excel(file_path)
            else:
                Logger.warning(f"サポートされていないファイル形式: {suffix}")
                return None
                
        except Exception as e:
            Logger.error(f"ファイル読み込みエラー: {e}")
            return None
    
    def _save_to_sqlite_basic(self, df: pd.DataFrame, table_name: str):
        """基本的なSQLite保存"""
        try:
            # データベースディレクトリを作成
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            
            conn = sqlite3.connect(self.db_path)
            df.to_sql(table_name, conn, if_exists='replace', index=False)
            conn.close()
            
            Logger.info(f"テーブル {table_name} に {len(df)} 行保存")
            
        except Exception as e:
            Logger.error(f"SQLite保存エラー: {e}")
            raise