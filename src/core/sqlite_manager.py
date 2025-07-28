"""
SQLiteデータベース管理クラス
ファイルの読み込みとデータベースへの書き込みを行う
"""

import sqlite3
import pandas as pd
import numpy as np
import csv
import chardet
from pathlib import Path
import re
from typing import Optional, Dict, Any, Union, List, Tuple

from ..utils.logger import Logger
from ..utils.error_handler import ErrorHandler
from ..utils.string_utils import StringUtils


class SQLiteManager:
    """SQLiteデータベース管理クラス"""
    
    def __init__(self):
        self.logger = Logger.get_logger(__name__)
        self.error_handler = ErrorHandler()
        
    def process_file(self, file_path: Path, db_path: str, **kwargs) -> bool:
        """ファイルを処理してSQLiteに保存"""
        try:
            self.logger.info(f"ファイル処理開始: {file_path}")
            
            # 設定パラメータの取得
            encoding = kwargs.get('encoding', 'auto')
            separator = kwargs.get('separator', 'auto')
            header_row = kwargs.get('header_row', 0)
            table_name = kwargs.get('table_name', None)
            if_exists = kwargs.get('if_exists', 'replace')
            
            # ファイルを読み込み
            df = self._read_file(file_path, encoding, separator, header_row)
            
            if df is None or df.empty:
                self.logger.error(f"ファイルの読み込みに失敗: {file_path}")
                return False
                
            # テーブル名が指定されていない場合はファイル名から生成
            if not table_name:
                table_name = StringUtils.sanitize_table_name(file_path.stem)
                
            # データ型の最適化
            df = self._optimize_dtypes(df)
            
            # SQLiteに保存
            self._save_to_sqlite(df, db_path, table_name, if_exists)
            
            self.logger.info(f"ファイル処理完了: {file_path} -> {table_name}")
            return True
            
        except Exception as e:
            self.error_handler.handle_error(e, f"ファイル処理エラー: {file_path}")
            return False
            
    def _read_file(self, file_path: Path, encoding: str = 'auto', separator: str = 'auto', 
                  header: int = 0, nrows: Optional[int] = None) -> Optional[pd.DataFrame]:
        """ファイルを読み込む"""
        try:
            # ファイル拡張子に基づいて処理
            suffix = file_path.suffix.lower()
            
            if suffix in ['.csv', '.txt']:
                # エンコーディング検出
                if encoding == 'auto':
                    encoding = self._detect_encoding(file_path)
                    
                # 区切り文字検出
                if separator == 'auto':
                    separator = self._detect_separator(file_path, encoding)
                    
                # 特殊ファイル処理
                if file_path.name.lower() == 'zm37.txt':
                    return self._read_special_zm37(file_path, encoding, separator)
                    
                # CSVファイル読み込み
                try:
                    kwargs = {}
                    if nrows is not None:
                        kwargs['nrows'] = nrows
                        
                    df = pd.read_csv(
                        file_path,
                        encoding=encoding,
                        sep=separator,
                        header=header,
                        dtype=str,  # すべての列を文字列として読み込み
                        **kwargs
                    )
                    return df
                except Exception as e:
                    self.logger.error(f"CSV読み込みエラー: {e}")
                    
                    # エラーが発生した場合はPythonエンジンで再試行
                    return pd.read_csv(
                        file_path,
                        encoding=encoding,
                        sep=separator,
                        header=header,
                        dtype=str,
                        engine='python',
                        on_bad_lines='skip',
                        **kwargs
                    )
                    
            elif suffix in ['.xlsx', '.xls']:
                # 特殊Excelファイル処理
                if file_path.name.lower() == 'pp_summary_ztbp080_kojozisseki_d_0.xlsx':
                    header = 7  # ヘッダーが8行目
                    
                # Excelファイル読み込み
                kwargs = {}
                if nrows is not None:
                    kwargs['nrows'] = nrows
                    
                return pd.read_excel(
                    file_path,
                    sheet_name=0,
                    header=header,
                    engine='openpyxl',
                    dtype=str,  # すべての列を文字列として読み込み
                    **kwargs
                )
                
            else:
                self.logger.error(f"サポートされていないファイル形式: {suffix}")
                return None
                
        except Exception as e:
            self.error_handler.handle_error(e, f"ファイル読み込みエラー: {file_path}")
            return None
            
    def _detect_encoding(self, file_path: Path) -> str:
        """ファイルのエンコーディングを検出"""
        try:
            # 特定のファイルは強制的にcp932を使用
            special_files = ['zm37.txt', 'zs58month.csv', 'zs61kday.csv', 'zf26.csv']
            if file_path.name.lower() in special_files:
                self.logger.info(f"特殊ファイル {file_path.name} にcp932エンコーディングを適用")
                return 'cp932'
            
            # ファイルの先頭部分を読み込み
            with open(file_path, 'rb') as f:
                raw_data = f.read(10000)  # 最初の10000バイトを読み込み
                
            # chardetでエンコーディングを検出
            result = chardet.detect(raw_data)
            encoding = result['encoding']
            
            # 日本語環境の場合はcp932を優先
            if encoding and encoding.lower() in ['shift_jis', 'shift-jis', 'sjis']:
                encoding = 'cp932'
                
            # 検出できない場合はcp932をデフォルトとする
            if not encoding:
                encoding = 'cp932'
                
            self.logger.info(f"検出されたエンコーディング: {encoding} (信頼度: {result['confidence']:.2f})")
            return encoding
            
        except Exception as e:
            self.logger.error(f"エンコーディング検出エラー: {e}")
            return 'cp932'  # デフォルトはcp932
            
    def _detect_separator(self, file_path: Path, encoding: str) -> str:
        """ファイルの区切り文字を検出"""
        try:
            # 特定のファイルは強制的にタブ区切りを使用
            tab_separated_files = ['zs58month.csv', 'zs61kday.csv', 'zf26.csv']
            if file_path.name.lower() in tab_separated_files:
                self.logger.info(f"特殊ファイル {file_path.name} にタブ区切りを適用")
                return '\t'
            
            # ファイルの先頭数行を読み込み
            lines = []
            with open(file_path, 'r', encoding=encoding, errors='replace') as f:
                for _ in range(5):  # 最初の5行を読み込み
                    line = f.readline()
                    if not line:
                        break
                    lines.append(line)
                    
            if not lines:
                return ','  # デフォルトはカンマ
                
            # 一般的な区切り文字の出現回数をカウント
            separators = {',': 0, '\t': 0, '|': 0, ';': 0}
            
            for line in lines:
                for sep, count in separators.items():
                    separators[sep] += line.count(sep)
                    
            # 最も出現回数の多い区切り文字を選択
            max_sep = max(separators.items(), key=lambda x: x[1])
            
            # 出現回数が0の場合はカンマをデフォルトとする
            if max_sep[1] == 0:
                return ','
                
            self.logger.info(f"検出された区切り文字: '{max_sep[0]}'")
            return max_sep[0]
            
        except Exception as e:
            self.logger.error(f"区切り文字検出エラー: {e}")
            return ','  # デフォルトはカンマ
            
    def _read_special_zm37(self, file_path: Path, encoding: str, separator: str) -> pd.DataFrame:
        """特殊ファイルzm37.txtの読み込み"""
        self.logger.info(f"特殊ファイル処理: {file_path.name}")
        
        try:
            # 特殊な設定でzm37.txtを読み込む
            df = pd.read_csv(
                file_path,
                encoding=encoding,
                sep=separator,
                quoting=csv.QUOTE_NONE,  # クォーテーションを無視
                engine='python',  # より柔軟な解析のためpythonエンジンを使用
                on_bad_lines='skip',  # 問題のある行をスキップ
                escapechar='\\',  # エスケープ文字を指定
                dtype=str  # すべての列を文字列として読み込む
            )
            return df
            
        except Exception as e:
            self.error_handler.handle_error(e, f"zm37.txt読み込みエラー: {file_path}")
            raise
            
    def _optimize_dtypes(self, df: pd.DataFrame) -> pd.DataFrame:
        """データ型の最適化"""
        # 日付列の名前パターン
        date_column_patterns = [
            'date', '日付', 'day', '年月日', '登録日', '有効開始日', '有効終了日',
            '作成日', '更新日', '開始日', '終了日', '期限', '期日'
        ]
        
        for col in df.columns:
            # 列名を小文字に変換して比較
            col_lower = col.lower() if isinstance(col, str) else ""
            
            # 空の列はスキップ
            if df[col].empty:
                continue
                
            # 列名に基づく日付型の検出と変換
            is_date_column = any(pattern in col_lower for pattern in date_column_patterns)
            
            if is_date_column:
                try:
                    # まず標準的な日付形式で変換を試みる
                    df[col] = pd.to_datetime(df[col], errors='coerce')
                    
                    # 変換に失敗した値（NaT）がある場合、8桁数値形式（YYYYMMDD）で再試行
                    if df[col].isna().any():
                        # 元の値を保持
                        original_values = df[col].copy()
                        
                        # 8桁数値形式で変換を試みる
                        mask = df[col].isna()
                        str_values = df.loc[mask, col].astype(str)
                        date_values = pd.to_datetime(str_values, format='%Y%m%d', errors='coerce')
                        df.loc[mask, col] = date_values
                        
                        # 特殊な値（99991231など）を処理
                        special_mask = df[col].isna() & original_values.astype(str).str.contains('9999')
                        if special_mask.any():
                            df.loc[special_mask, col] = pd.Timestamp.max
                except Exception as e:
                    pass
                    
            # 8桁数値・文字の処理
            elif df[col].dtype == 'object':
                # サンプルデータを取得（最大100行）
                sample = df[col].dropna().head(100)
                
                # 8桁数値パターンの検出（日付の可能性）
                if all(isinstance(x, str) and len(x) == 8 and x.isdigit() for x in sample if pd.notna(x) and x):
                    try:
                        # 日付として解釈できるか試す
                        test_dates = pd.to_datetime(sample, format='%Y%m%d', errors='coerce')
                        valid_dates = ~test_dates.isna()
                        
                        # 50%以上が有効な日付の場合、日付型として変換
                        if valid_dates.mean() >= 0.5:
                            df[col] = pd.to_datetime(df[col], format='%Y%m%d', errors='coerce')
                            
                            # 特殊な値（99991231など）を処理
                            special_mask = df[col].isna() & df[col].astype(str).str.contains('9999')
                            if special_mask.any():
                                df.loc[special_mask, col] = pd.Timestamp.max
                        else:
                            # 数値として保持
                            df[col] = pd.to_numeric(df[col], errors='ignore')
                    except Exception as e:
                        # 数値として変換
                        df[col] = pd.to_numeric(df[col], errors='ignore')
                
                # コード列の処理（数値として読み込まれた場合も文字列に変換）
                elif 'code' in col_lower or 'コード' in col_lower:
                    # 数値型の場合は整数部分のみを取得して文字列に変換
                    if df[col].dtype in ['float64', 'int64']:
                        df[col] = df[col].fillna(0).astype(int).astype(str)
                    else:
                        df[col] = df[col].astype(str)
                
                # 数値列だが固定長コードの可能性がある列の処理
                elif df[col].dtype in ['float64', 'int64']:
                    # サンプルデータで固定長コードかチェック
                    sample = df[col].dropna().head(100)
                    if len(sample) > 0:
                        # 整数値で固定長の場合はコードとして扱う
                        str_sample = sample.astype(int).astype(str)
                        lengths = str_sample.str.len()
                        if len(lengths.unique()) <= 2 and lengths.mean() >= 4:  # 固定長で4桁以上
                            self.logger.info(f"固定長コードとして検出: {col}")
                            df[col] = df[col].fillna(0).astype(int).astype(str)
                    
        return df
        
    def _save_to_sqlite(self, df: pd.DataFrame, db_path: str, table_name: str, if_exists: str = 'replace'):
        """DataFrameをSQLiteに保存"""
        try:
            # データベース接続
            conn = sqlite3.connect(db_path)
            
            # パフォーマンス設定
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("PRAGMA synchronous = NORMAL")
            conn.execute("PRAGMA cache_size = 10000")
            
            # データをSQLiteに書き込み
            df.to_sql(table_name, conn, if_exists=if_exists, index=False)
            
            # インデックスの作成
            self._create_indexes(conn, table_name, df)
            
            conn.close()
            
            self.logger.info(f"テーブル {table_name} に {len(df)} 行保存")
            
        except Exception as e:
            self.error_handler.handle_error(e, f"SQLite保存エラー: {table_name}")
            raise
            
    def _create_indexes(self, conn: sqlite3.Connection, table_name: str, df: pd.DataFrame):
        """インデックスを作成"""
        try:
            cursor = conn.cursor()
            
            # 主キーとなる可能性のあるカラムパターン
            key_patterns = ['id', 'code', 'key', 'no', 'num', 'コード', '番号']
            
            # インデックス候補を検索
            index_candidates = []
            
            for col in df.columns:
                col_lower = str(col).lower()
                
                # 主キー候補のカラム
                if any(pattern in col_lower for pattern in key_patterns):
                    # ユニーク値の割合を確認
                    unique_ratio = df[col].nunique() / len(df) if len(df) > 0 else 0
                    
                    # ユニーク値の割合が高い場合はインデックス候補
                    if unique_ratio > 0.5:
                        index_candidates.append(col)
                        
                # 日付カラム
                elif df[col].dtype == 'datetime64[ns]':
                    index_candidates.append(col)
                    
            # インデックスを作成
            for col in index_candidates:
                index_name = f"idx_{table_name}_{col}"
                
                # 既存のインデックスを確認
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='index' AND name=?",
                    (index_name,)
                )
                
                if not cursor.fetchone():
                    # インデックスを作成
                    cursor.execute(f"CREATE INDEX {index_name} ON {table_name}(`{col}`)")
                    self.logger.info(f"インデックス作成: {index_name}")
                    
            conn.commit()
            
        except Exception as e:
            self.logger.error(f"インデックス作成エラー: {e}")
            # インデックス作成エラーは無視して処理を続行
    
    def finalize_database(self, db_path: str = None):
        """データベースの最終化処理（主キー・インデックス設定）"""
        if not db_path:
            self.logger.warning("データベースパスが指定されていません")
            return
            
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            self.logger.info("データベース最終化処理を開始...")
            
            # 全テーブル一覧を取得
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
            tables = cursor.fetchall()
            
            processed_tables = 0
            created_indexes = 0
            
            for table_tuple in tables:
                table_name = table_tuple[0]
                
                try:
                    # テーブル情報を取得
                    cursor.execute(f"PRAGMA table_info(`{table_name}`)")
                    columns = cursor.fetchall()
                    
                    # 主キー候補を探す
                    primary_key_candidates = []
                    index_candidates = []
                    
                    for col_info in columns:
                        col_name = col_info[1]
                        col_type = col_info[2]
                        is_pk = col_info[5]  # PRIMARY KEY フラグ
                        
                        # 既に主キーが設定されている場合はスキップ
                        if is_pk:
                            continue
                            
                        col_lower = col_name.lower()
                        
                        # 主キー候補のパターン
                        pk_patterns = ['id', '_id', 'key', '_key', 'no', '_no', 'code', '_code', 
                                     'コード', '番号', 'キー']
                        
                        if any(pattern in col_lower for pattern in pk_patterns):
                            primary_key_candidates.append(col_name)
                            
                        # インデックス候補のパターン
                        idx_patterns = ['date', '日付', 'time', '時刻', 'created', 'updated', 
                                      '作成', '更新', '登録', 'status', '状態']
                        
                        if any(pattern in col_lower for pattern in idx_patterns):
                            index_candidates.append(col_name)
                    
                    # 主キーを設定（_rowid_を追加）
                    if not any(col[5] for col in columns):  # 主キーが設定されていない場合
                        try:
                            # _rowid_カラムを追加
                            cursor.execute(f"ALTER TABLE `{table_name}` ADD COLUMN _rowid_ INTEGER PRIMARY KEY AUTOINCREMENT")
                            self.logger.info(f"主キー追加: {table_name}._rowid_")
                        except sqlite3.OperationalError as e:
                            if "duplicate column name" not in str(e).lower():
                                self.logger.warning(f"主キー追加失敗: {table_name} - {e}")
                    
                    # インデックスを作成
                    for col_name in primary_key_candidates + index_candidates:
                        index_name = f"idx_{table_name}_{col_name}".replace(' ', '_').replace('-', '_')
                        
                        try:
                            # 既存インデックスをチェック
                            cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name=?", (index_name,))
                            if not cursor.fetchone():
                                cursor.execute(f"CREATE INDEX `{index_name}` ON `{table_name}`(`{col_name}`)")
                                created_indexes += 1
                                self.logger.info(f"インデックス作成: {index_name}")
                        except Exception as e:
                            self.logger.warning(f"インデックス作成失敗: {index_name} - {e}")
                    
                    processed_tables += 1
                    
                except Exception as e:
                    self.logger.error(f"テーブル {table_name} の処理エラー: {e}")
            
            # データベース最適化
            cursor.execute("PRAGMA optimize")
            conn.commit()
            conn.close()
            
            self.logger.info(f"データベース最終化完了: {processed_tables}テーブル処理, {created_indexes}インデックス作成")
            
        except Exception as e:
            self.logger.error(f"データベース最終化エラー: {e}")
            raise