import hashlib
import sys
import sqlite3
import pandas as pd
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

# config.constantsのインポートを試みるが、失敗しても続行
try:
    from config.constants import Paths
except ImportError:
    class Paths:
        def __init__(self):
            self.PROJECT_ROOT = Path(__file__).resolve().parents[2]
            self.LOGS = self.PROJECT_ROOT / 'logs'
            self.LOGS.mkdir(exist_ok=True)

class SQLiteManager:
    """SQLite統一管理クラス V5 修正版 (主キー・インデックス設定機能強化)"""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.logger = self._setup_logger()
        self._init_database()

    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger(self.__class__.__name__)
        if not logger.handlers:
            log_path = Paths().LOGS / f"{self.__class__.__name__}.log"
            handler = logging.FileHandler(log_path, encoding='utf-8')
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

    def _init_database(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("PRAGMA synchronous = NORMAL")

    def _close_all_connections(self):
        """すべてのSQLite接続を確実に閉じる"""
        try:
            import gc
            gc.collect()
            self.logger.info("SQLite接続のクリーンアップを実行しました")
        except Exception as e:
            self.logger.warning(f"接続クリーンアップ中にエラーが発生しました: {e}")

    def _optimize_dtypes(self, df: pd.DataFrame) -> pd.DataFrame:
        self.logger.info("データ型最適化中...")
        for col in df.columns:
            if df[col].dtype == 'object':
                try:
                    df[col] = pd.to_numeric(df[col], errors='ignore')
                except:
                    pass
        return df

    def bulk_insert_from_file(self, conn: sqlite3.Connection, file_path: Path, table_name: str, encoding: str = 'utf-8', quoting=None) -> tuple:
        self.logger.info(f"開始: {table_name} <- {file_path.name}")
        try:
            # conn.execute(f'DROP TABLE IF EXISTS "{table_name}"') # main.pyで削除するためコメントアウト
            total_rows = 0

            if file_path.suffix.lower() in ['.csv', '.txt']:
                detected_encoding = self._detect_encoding(file_path) if encoding == 'auto' else encoding
                encodings_to_try = list(dict.fromkeys([detected_encoding, 'utf-8', 'shift_jis', 'cp932']))

                successful_read = False
                import csv as _csv
                # csv.field_size_limit(sys.maxsize) # OverflowError対策のためコメントアウト
                for current_encoding in encodings_to_try:
                    if not current_encoding: continue
                    try:
                        sep = ','
                        with open(file_path, 'r', encoding=current_encoding) as f:
                            first_line = f.readline()
                            if '\t' in first_line: sep = '\t'
                            elif '|' in first_line: sep = '|'
                            elif file_path.suffix.lower() == '.txt' and '  ' in first_line: sep = r'\s+'

                        engine = 'python' if sep == r'\s+' else 'c'
                        self.logger.info(f"エンコーディング '{current_encoding}', 区切り文字 '{sep}' で処理試行")

                        read_csv_kwargs = dict(
                            chunksize=50000,
                            encoding=current_encoding,
                            sep=sep,
                            engine=engine,
                            on_bad_lines='skip',
                            low_memory=(engine=='c')
                        )
                        if quoting is not None:
                            if isinstance(quoting, str) and quoting == 'none':
                                read_csv_kwargs['quoting'] = _csv.QUOTE_NONE
                                read_csv_kwargs['escapechar'] = ''
                                read_csv_kwargs['engine'] = 'python'
                            elif isinstance(quoting, int):
                                read_csv_kwargs['quoting'] = quoting

                        i = -1 # Initialize i for cases where enumerate might not yield any chunks
                        for i, chunk in enumerate(pd.read_csv(file_path, **read_csv_kwargs)):
                            chunk = self._optimize_dtypes(chunk)
                            # テーブル名はクォートなしで渡す
                            chunk.to_sql(table_name, conn, if_exists=('replace' if i == 0 else 'append'), index=False)
                            total_rows += len(chunk)
                        successful_read = True
                        break # 成功したらループを抜ける
                    except Exception as e:
                        self.logger.warning(f"読み込み失敗({current_encoding}): {e}")
                        # traceback.format_exc() は冗長なため、ここでは出力しない
                        continue # 次のエンコーディングを試す
                if not successful_read:
                    return False, f"全てのエンコーディング試行に失敗しました: {file_path.name}"

            elif file_path.suffix.lower() in ['.xls', '.xlsx']:
                # Excelファイルの場合の処理
                try:
                    # openpyxlエンジンを明示的に指定して試行
                    df = pd.read_excel(file_path, sheet_name=0, engine='openpyxl')
                except Exception as e:
                    self.logger.error(f"Excel処理失敗: {file_path.name} - {e}")
                    return False, f"Excel処理失敗: {file_path.name} - {e}"
                
                df = self._optimize_dtypes(df)
                # Excelの場合も同様
                df.to_sql(table_name, conn, if_exists='replace', index=False)
                total_rows = len(df)
            else:
                return False, f"未対応ファイル形式: {file_path.name}"

            self.logger.info(f"完了: {table_name} ({total_rows:,} rows)")
            return True, None

        except Exception as e:
            import traceback
            self.logger.error(f"""エラー: {table_name} - {str(e)}
{traceback.format_exc()}""")
            return False, str(e)

    def finalize_table_structure(self, conn: sqlite3.Connection, table_name: str, 
                                primary_key_columns: Optional[List[str]] = None, 
                                index_columns: Optional[List[str]] = None) -> Tuple[bool, Optional[str]]:
        """
        テーブル構造を最終化し、主キーとインデックスを追加する。
        既存のテーブルをリネームし、新しいスキーマでデータを移行する。
        
        Args:
            conn: SQLite接続オブジェクト
            table_name: 対象テーブル名
            primary_key_columns: 主キーに設定するカラムのリスト（指定がない場合は_rowid_を使用）
            index_columns: インデックスを作成するカラムのリスト
            
        Returns:
            (成功したかどうか, エラーメッセージ)
        """
        self.logger.info(f"開始: {table_name} の構造を最終化します。")
        
        # テーブル名からクォートを削除
        clean_table_name = table_name.strip('"').strip("'")
        temp_table_name = f"temp_final_{clean_table_name}"

        try:
            cursor = conn.cursor()
            
            # === ステップ1: 既存テーブルの構造確認 ===
            cursor.execute(f'PRAGMA table_info("{clean_table_name}")')
            columns_info = cursor.fetchall()
            if not columns_info:
                return False, f"テーブル {table_name} が存在しません。"
            
            # 主キーが既に存在するかチェック
            has_primary_key = any(col[5] for col in columns_info)
            if has_primary_key:
                self.logger.info(f"テーブル {table_name} には既に主キーが設定されています")
                
                # インデックスのみ作成する場合
                if index_columns:
                    return self._create_indexes(conn, clean_table_name, index_columns)
                return True, None
            
            # データ件数を確認（移行前）
            cursor.execute(f'SELECT COUNT(*) FROM "{clean_table_name}"')
            row_count_before = cursor.fetchone()[0]
            self.logger.info(f"移行前のデータ件数: {row_count_before} 件")

            # === ステップ2: トランザクション開始 ===
            cursor.execute("BEGIN TRANSACTION;")
            
            try:
                # カラム情報を取得
                column_defs = []
                column_names = []
                
                for col in columns_info:
                    name, dtype = col[1], col[2]
                    if name.lower() == '_rowid_':
                        continue
                    column_defs.append(f'"{name}" {dtype}')
                    column_names.append(f'"{name}"')

                # 元のテーブルをリネーム
                cursor.execute(f'ALTER TABLE "{clean_table_name}" RENAME TO "{temp_table_name}";')
                self.logger.info(f"テーブルをリネーム: {table_name} → {temp_table_name}")

                # 新しいテーブルを作成
                if primary_key_columns and len(primary_key_columns) > 0:
                    # 指定された主キーを使用
                    pk_columns = ', '.join([f'"{col}"' for col in primary_key_columns])
                    create_table_sql = f'CREATE TABLE "{clean_table_name}" ({", ".join(column_defs)}, PRIMARY KEY ({pk_columns}));'
                else:
                    # _rowid_ を主キーとして追加
                    create_table_sql = f'CREATE TABLE "{clean_table_name}" ("_rowid_" INTEGER PRIMARY KEY AUTOINCREMENT, {", ".join(column_defs)});'
                
                self.logger.info(f"実行SQL: {create_table_sql}")
                cursor.execute(create_table_sql)

                # データを新しいテーブルにコピー
                column_names_str = ', '.join(column_names)
                insert_sql = f'INSERT INTO "{clean_table_name}" ({column_names_str}) SELECT {column_names_str} FROM "{temp_table_name}";'
                self.logger.info(f"実行SQL: {insert_sql}")
                cursor.execute(insert_sql)

                # データ件数を確認（移行後）
                cursor.execute(f'SELECT COUNT(*) FROM "{clean_table_name}"')
                row_count_after = cursor.fetchone()[0]
                self.logger.info(f"移行後のデータ件数: {row_count_after} 件")
                
                if row_count_before != row_count_after:
                    self.logger.warning(f"データ件数が変更されました: {row_count_before} → {row_count_after}")
                    if abs(row_count_before - row_count_after) > row_count_before * 0.01:  # 1%以上の差がある場合
                        raise Exception(f"データ移行中に大幅な件数不一致が発生しました: 移行前 {row_count_before} 件, 移行後 {row_count_after} 件")

                # 一時テーブルを削除
                cursor.execute(f'DROP TABLE "{temp_table_name}";')
                self.logger.info(f"一時テーブルを削除: {temp_table_name}")
                
                # トランザクションをコミット
                conn.commit()
                
                if primary_key_columns and len(primary_key_columns) > 0:
                    self.logger.info(f"完了: {table_name} に主キー ({', '.join(primary_key_columns)}) を追加しました。")
                else:
                    self.logger.info(f"完了: {table_name} に _rowid_ 主キーを追加しました。")

            except Exception as e:
                # エラー発生時はロールバック
                conn.rollback()
                self.logger.error(f"テーブル再作成エラー ({table_name}): {e}")
                try:
                    # エラー時の復元処理
                    cursor.execute(f'DROP TABLE IF EXISTS "{clean_table_name}";')
                    cursor.execute(f'ALTER TABLE "{temp_table_name}" RENAME TO "{clean_table_name}";')
                    conn.commit()
                    self.logger.info(f"テーブル {table_name} を元の状態に復元しました")
                except Exception as revert_e:
                     self.logger.error(f"テーブル復元エラー ({table_name}): {revert_e}")
                return False, str(e)

            # === ステップ3: インデックスを作成 ===
            if index_columns:
                return self._create_indexes(conn, clean_table_name, index_columns)
            
            return True, None

        except Exception as e:
            import traceback
            self.logger.error(f"構造最終化エラー: {table_name} - {str(e)}\n{traceback.format_exc()}")
            return False, str(e)

    def _create_indexes(self, conn: sqlite3.Connection, table_name: str, index_columns: List[str]) -> Tuple[bool, Optional[str]]:
        """インデックスを作成する内部メソッド"""
        try:
            cursor = conn.cursor()
            
            # テーブルのカラム一覧を取得
            cursor.execute(f'PRAGMA table_info("{table_name}")')
            existing_columns = [info[1] for info in cursor.fetchall()]
            
            for col in index_columns:
                if not col or col == "#N/A":
                    continue
                    
                # 複合インデックスの場合（スラッシュ区切り）
                if '/' in col:
                    cols = [c.strip() for c in col.split('/')]
                    valid_cols = [c for c in cols if c in existing_columns]
                    if not valid_cols:
                        self.logger.warning(f"インデックス対象カラム {cols} が {table_name} に存在しないため、スキップします。")
                        continue
                        
                    # インデックス名を生成（特殊文字を置換）
                    index_name = f"idx_{table_name}_{'_'.join(valid_cols)}".lower()
                    index_name = self._sanitize_name(index_name)
                    
                    # インデックスSQL生成
                    indexed_columns_str = ', '.join([f'"{c}"' for c in valid_cols])
                    index_sql = f'CREATE INDEX IF NOT EXISTS "{index_name}" ON "{table_name}" ({indexed_columns_str});'
                    
                else:
                    # 単一カラムのインデックス
                    if col not in existing_columns:
                        self.logger.warning(f"インデックス対象カラム {col} が {table_name} に存在しないため、スキップします。")
                        continue
                        
                    index_name = f"idx_{table_name}_{col}".lower()
                    index_name = self._sanitize_name(index_name)
                    index_sql = f'CREATE INDEX IF NOT EXISTS "{index_name}" ON "{table_name}" ("{col}");'
                
                # インデックス作成
                cursor.execute(index_sql)
                self.logger.info(f"完了: {table_name} にインデックス {index_name} を作成しました。")
            
            return True, None
            
        except Exception as e:
            self.logger.error(f"インデックス作成エラー: {table_name} - {str(e)}")
            return False, str(e)

    def _sanitize_name(self, name: str) -> str:
        """SQLiteで使用可能な識別子に変換する"""
        return (name.replace(' ', '_')
                   .replace('-', '_')
                   .replace('.', '_')
                   .replace('(', '')
                   .replace(')', '')
                   .replace('/', '_')
                   .replace('（', '')
                   .replace('）', '')
                   .replace('★', '')
                   .replace(':', '')
                   .replace('／', '_')
                   .replace('・', '_')
                   .replace('?', '')
                   .replace('!', '')
                   .replace('　', '_')
                   .replace('+', '_')
                   .replace('=', '_')
                   .replace('%', '_')
                   .replace('&', '_')
                   .replace('#', '_')
                   .replace('@', '_')
                   .replace('*', '_')
                   .replace('~', '_')
                   .replace('`', '_')
                   .replace("'", '_')
                   .replace('"', '_')
                   .replace(';', '_')
                   .replace('>', '_')
                   .replace('<', '_')
                   .replace(',', '_')
                   .replace('{', '_')
                   .replace('}', '_')
                   .replace('[', '_')
                   .replace(']', '_')
                   .replace('^', '_')
                   .replace('|', '_'))

    def get_file_processing_config(self, file_name: str) -> dict:
        """
        ファイル名に基づいて処理設定を取得
        """
        file_name_lower = file_name.lower()
        
        if file_name_lower == 'zm37.txt':
            return {
                'encoding': 'cp932',
                'quoting': 'none'
            }
        else:
            return {
                'encoding': 'auto',
                'quoting': None
            }

    def _detect_encoding(self, file_path: Path) -> str:
        import chardet
        with open(file_path, 'rb') as f:
            raw_data = f.read(100000)
            result = chardet.detect(raw_data)
        encoding = result.get('encoding')
        if encoding: self.logger.info(f"エンコーディング判定: {encoding} (信頼度: {result.get('confidence', 0):.2f})")
        return encoding if result.get('confidence', 0) > 0.7 else 'shift_jis'

    def load_primary_key_definitions(self, file_path: Path) -> Dict[str, List[str]]:
        """
        主キー定義ファイルを読み込む
        
        Args:
            file_path: 主キー定義ファイルのパス
            
        Returns:
            テーブル名をキー、主キーカラムのリストを値とする辞書
        """
        self.logger.info(f"主キー定義ファイルを読み込み: {file_path}")
        primary_keys = {}
        
        try:
            # タブ区切りテキストファイルを読み込む
            df = pd.read_csv(file_path, sep='\t', encoding='utf-8')
            
            # 必要なカラムがあるか確認
            required_columns = ['Table Name', 'Field Name', 'Field Name2']
            if not all(col in df.columns for col in required_columns):
                self.logger.error(f"主キー定義ファイルに必要なカラムがありません: {required_columns}")
                return primary_keys
                
            # 各行を処理
            for _, row in df.iterrows():
                table_name = row['Table Name']
                if pd.isna(table_name) or table_name == "#N/A":
                    continue
                    
                # 主キーカラムを取得
                pk_columns = []
                if not pd.isna(row['Field Name']) and row['Field Name'] != "#N/A":
                    pk_columns.append(row['Field Name'])
                    
                if not pd.isna(row['Field Name2']) and row['Field Name2'] != "#N/A":
                    pk_columns.append(row['Field Name2'])
                    
                if pk_columns:
                    primary_keys[table_name] = pk_columns
                    
            self.logger.info(f"主キー定義を {len(primary_keys)} テーブル分読み込みました")
            return primary_keys
            
        except Exception as e:
            self.logger.error(f"主キー定義ファイル読み込みエラー: {e}")
            return primary_keys

    def load_index_definitions(self, file_path: Path) -> Dict[str, List[str]]:
        """
        インデックス定義ファイルを読み込む
        
        Args:
            file_path: インデックス定義ファイルのパス
            
        Returns:
            テーブル名をキー、インデックスカラムのリストを値とする辞書
        """
        self.logger.info(f"インデックス定義ファイルを読み込み: {file_path}")
        index_defs = {}
        
        try:
            # タブ区切りテキストファイルを読み込む
            df = pd.read_csv(file_path, sep='\t', encoding='utf-8')
            
            # 必要なカラムがあるか確認
            required_columns = ['Table Name', 'Field Name', 'Field Name2']
            if not all(col in df.columns for col in required_columns):
                self.logger.error(f"インデックス定義ファイルに必要なカラムがありません: {required_columns}")
                return index_defs
                
            # 各行を処理
            for _, row in df.iterrows():
                table_name = row['Table Name']
                if pd.isna(table_name) or table_name == "#N/A":
                    continue
                    
                # インデックスカラムを取得
                idx_columns = []
                
                # 単一カラムのインデックス
                if not pd.isna(row['Field Name']) and row['Field Name'] != "#N/A":
                    idx_columns.append(row['Field Name'])
                    
                # 複合インデックス（Field Name2がある場合）
                if not pd.isna(row['Field Name2']) and row['Field Name2'] != "#N/A":
                    # 複合インデックスとして追加
                    composite_idx = f"{row['Field Name']}/{row['Field Name2']}"
                    idx_columns.append(composite_idx)
                    
                if idx_columns:
                    if table_name in index_defs:
                        index_defs[table_name].extend(idx_columns)
                    else:
                        index_defs[table_name] = idx_columns
                    
            self.logger.info(f"インデックス定義を {len(index_defs)} テーブル分読み込みました")
            return index_defs
            
        except Exception as e:
            self.logger.error(f"インデックス定義ファイル読み込みエラー: {e}")
            return index_defs

    def apply_table_optimizations(self, primary_key_file: Path, index_file: Path) -> Tuple[int, int, List[str]]:
        """
        すべてのテーブルに主キーとインデックスを適用する
        
        Args:
            primary_key_file: 主キー定義ファイルのパス
            index_file: インデックス定義ファイルのパス
            
        Returns:
            (成功したテーブル数, 失敗したテーブル数, エラーメッセージのリスト)
        """
        # 定義ファイルを読み込む
        pk_defs = self.load_primary_key_definitions(primary_key_file)
        idx_defs = self.load_index_definitions(index_file)
        
        success_count = 0
        error_count = 0
        error_messages = []
        
        # データベースに接続
        with sqlite3.connect(self.db_path) as conn:
            # テーブル一覧を取得
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
            tables = [row[0] for row in cursor.fetchall()]
            
            self.logger.info(f"データベース内の {len(tables)} テーブルに最適化を適用します")
            
            # 各テーブルを処理
            for table_name in tables:
                try:
                    # 主キーとインデックスの定義を取得
                    pk_columns = pk_defs.get(table_name, [])
                    idx_columns = idx_defs.get(table_name, [])
                    
                    if not pk_columns and not idx_columns:
                        self.logger.info(f"テーブル {table_name} には主キー・インデックス定義がないためスキップします")
                        continue
                    
                    # テーブル構造を最終化
                    success, error = self.finalize_table_structure(conn, table_name, pk_columns, idx_columns)
                    
                    if success:
                        success_count += 1
                    else:
                        error_count += 1
                        error_messages.append(f"テーブル {table_name}: {error}")
                        
                except Exception as e:
                    error_count += 1
                    error_messages.append(f"テーブル {table_name} 処理エラー: {str(e)}")
                    self.logger.error(f"テーブル {table_name} 処理中にエラーが発生: {e}")
            
        self.logger.info(f"テーブル最適化完了: 成功={success_count}, 失敗={error_count}")
        return success_count, error_count, error_messages

# ==============================
# 変更:
# - finalize_table_structure メソッドを統合・改善
# - 主キー定義ファイル読み込み機能を追加
# - インデックス定義ファイル読み込み機能を追加
# - 一括最適化適用機能を追加
# ==============================