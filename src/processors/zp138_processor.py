import pandas as pd
import sqlite3
from decimal import Decimal, InvalidOperation, getcontext
import time
from datetime import datetime
import logging
import os
from pathlib import Path

from .base_processor import DataProcessor

# 小数点以下の桁数を設定
getcontext().prec = 10

class ZP138Processor(DataProcessor):
    """ZP138データ処理クラス
    
    ZP138.txtファイルを読み込み、引当計算を行い、SQLiteに保存します。
    """
    
    def __init__(self, config=None):
        """初期化
        
        Args:
            config (dict, optional): 設定パラメータ。Defaults to None.
        """
        super().__init__(config)
        
        # デフォルト設定
        self.input_file = self.config.get('input_file', r'\\fssha01\common\HOST\ZP138\ZP138.txt')
        self.table_name = self.config.get('table_name', 't_zp138引当')
        
        # ローカルファイルパスを設定
        self.local_input_file = os.path.join(self.raw_data_dir, 'ZP138.txt')
        
        # カラム名のマッピング
        self.column_mapping = {
            '連続行番号': '連続行番号',
            '品目': '品目',
            '名称': '名称',
            'MRP エリア': 'MRPエリア',
            'プラント': 'プラント',
            '所要日付': '所要日付',
            'MRP 要素': 'MRP要素',
            'MRP 要素データ': 'MRP要素データ',
            '再日程計画日付': '再日程計画日付',
            '例外Msg': '例外Msg',
            '入庫/所要量': '入庫_所要量',
            '利用可能数量': '利用可能数量',
            '保管場所': '保管場所',
            '入出庫予定': '入出庫予定',
            'Itm': 'Itm',
            '引当': '引当',
            '過不足': '過不足'
        }
        
    def read_data(self):
        """ZP138.txtファイルを読み込む
        
        Returns:
            pd.DataFrame: 読み込んだデータ
        """
        try:
            # 元ファイルをローカルにコピー（オプション）
            if self.config.get('copy_to_local', False):
                self._copy_file_to_local()
                input_path = self.local_input_file
            else:
                input_path = self.input_file
                
            self.logger.info(f"ファイル読み込み開始: {input_path}")
            data = pd.read_csv(input_path, delimiter='\t', encoding='cp932', header=0)
            self.logger.info(f"ファイル読み込み完了: {len(data)}行")
            
            # カラム名を変更
            data = data.rename(columns=self.column_mapping)
            
            return data
        except FileNotFoundError:
            self.logger.error(f"エラー: ファイルが見つかりません: {input_path}")
            raise
        except Exception as e:
            self.logger.error(f"ファイルの読み込み中にエラーが発生しました: {e}")
            raise
            
    def transform_data(self, data):
        """引当計算などの変換処理
        
        Args:
            data (pd.DataFrame): 変換するデータ
            
        Returns:
            pd.DataFrame: 変換後のデータ
        """
        # 「引当」と「過不足」カラムを追加 (初期値はNone)
        data['引当'] = None
        data['過不足'] = None

        # 日付列処理
        data['所要日付'] = pd.to_datetime(data['所要日付'], format='%Y%m%d', errors='coerce')
        data['所要日付'] = data['所要日付'].where(pd.notna(data['所要日付']), None)

        data['再日程計画日付'] = pd.to_datetime(data['再日程計画日付'], format='%Y%m%d', errors='coerce')
        data['再日程計画日付'] = data['再日程計画日付'].where(pd.notna(data['再日程計画日付']), None)

        # 数値列処理
        data['入庫_所要量'] = data['入庫_所要量'].apply(self._safe_decimal_conversion)
        data['利用可能数量'] = data['利用可能数量'].apply(self._safe_decimal_conversion)

        # 保管場所整形
        data['保管場所'] = data['保管場所'].fillna('').apply(
            lambda x: str(int(x)) if isinstance(x, (int, float)) else str(x)
        ).str.replace(r',.*$', '', regex=True)

        # 過不足計算
        self.logger.info("在庫計算処理開始")
        final_df = self._calculate_inventory(data)
        self.logger.info("在庫計算処理完了")

        # データ変換とNoneへの統一
        for col in final_df.select_dtypes(exclude=['datetime64[ns]']):  # datetime64[ns]型は除外
            if pd.api.types.is_numeric_dtype(final_df[col]):
                continue  # 数値型はスキップ
            else:  # 文字列型の場合
                final_df[col] = final_df[col].apply(self._clean_text)
                final_df[col] = final_df[col].fillna('NULL')

        # MRP要素データのNULLをpd.NAに変換
        final_df['MRP要素データ'] = final_df['MRP要素データ'].apply(
            lambda x: pd.NA if x == 'NULL' or pd.isna(x) else x
        )
        # Noneをpd.NAに変換
        final_df['MRP要素データ'] = final_df['MRP要素データ'].fillna(pd.NA)
        final_df['例外Msg'] = final_df['例外Msg'].fillna(pd.NA)

        return final_df
        
    def save_to_db(self, df):
        """データをSQLiteに保存
        
        Args:
            df (pd.DataFrame): 保存するデータ
        """
        # SQLiteデータベースに接続
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # 既存テーブル削除
            cursor.execute(f"DROP TABLE IF EXISTS {self.table_name}")
            conn.commit()
            self.logger.info(f"SQLiteテーブル削除: {self.table_name}")

            # テーブル作成
            columns = []
            for col_name_txt, col_name_db in self.column_mapping.items():
                if col_name_db == '連続行番号':
                    columns.append(f"連続行番号 INTEGER")
                elif col_name_db in ['入庫_所要量', '利用可能数量', '引当', '過不足']:
                    columns.append(f"{col_name_db} REAL")
                elif col_name_db in ['所要日付', '再日程計画日付']:
                    columns.append(f"{col_name_db} TEXT")
                else:
                    columns.append(f"{col_name_db} TEXT")

            create_table_sql = f"""
                CREATE TABLE {self.table_name} (
                    {", ".join(columns)}
                )
            """
            cursor.execute(create_table_sql)
            conn.commit()
            self.logger.info(f"SQLiteテーブル作成: {self.table_name}")

            # データをSQLiteに挿入
            batch_size = 1000  # バッチサイズ
            total_rows = len(df)
            
            for i in range(0, total_rows, batch_size):
                batch_df = df.iloc[i:i+batch_size]
                
                for _, row in batch_df.iterrows():
                    values = []
                    cols = []
                    placeholders = []

                    for col_name_db in df.columns:
                        value = row[col_name_db]

                        if col_name_db == '連続行番号':
                            if pd.notnull(value):
                                try:
                                    values.append(int(value))
                                except ValueError:
                                    self.logger.warning(f"Warning: Could not convert '{value}' to integer.")
                                    values.append(None)
                            else:
                                values.append(None)
                        elif col_name_db in ['入庫_所要量', '利用可能数量', '引当', '過不足']:
                            if pd.notnull(value) and isinstance(value, (int, float, Decimal)):
                                values.append(float(value))
                            else:
                                values.append(None)
                        elif col_name_db in ['所要日付', '再日程計画日付']:
                            if pd.isna(value) or value is None:
                                values.append(None)
                            elif isinstance(value, datetime):
                                try:
                                    values.append(value.strftime('%Y-%m-%d %H:%M:%S'))
                                except (ValueError, AttributeError):
                                    values.append(None)
                            else:
                                self.logger.warning(f"Warning: Value for {col_name_db} is not a datetime object: {value}, type: {type(value)}")
                                values.append(None)
                        elif pd.isna(value):
                            values.append(None)
                        else:
                            values.append(str(value))
                        cols.append(col_name_db)
                        placeholders.append("?")

                    cols_str = ", ".join(cols)
                    placeholders_str = ", ".join(placeholders)
                    
                    sql = f"""
                        INSERT INTO {self.table_name} ({cols_str})
                        VALUES ({placeholders_str})
                    """
                    cursor.execute(sql, values)
                
                conn.commit()
                self.logger.info(f"SQLiteにデータ挿入: {i+len(batch_df)}/{total_rows}行")

            # インデックス作成（オプション）
            if self.config.get('create_indexes', True):
                self._create_indexes(conn)

            self.logger.info(f"SQLiteにデータ挿入完了: {total_rows}行")
            
        except sqlite3.Error as e:
            self.logger.error(f"SQLiteエラーが発生しました: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
            
    def _copy_file_to_local(self):
        """元ファイルをローカルにコピー"""
        import shutil
        
        # ディレクトリが存在しない場合は作成
        os.makedirs(self.raw_data_dir, exist_ok=True)
        
        self.logger.info(f"ファイルをローカルにコピー: {self.input_file} -> {self.local_input_file}")
        shutil.copy2(self.input_file, self.local_input_file)
        
    def _create_indexes(self, conn):
        """インデックスを作成
        
        Args:
            conn (sqlite3.Connection): データベース接続
        """
        cursor = conn.cursor()
        
        # 品目のインデックス
        cursor.execute(f"CREATE INDEX idx_{self.table_name}_品目 ON {self.table_name}(品目)")
        
        # 所要日付のインデックス
        cursor.execute(f"CREATE INDEX idx_{self.table_name}_所要日付 ON {self.table_name}(所要日付)")
        
        # MRP要素のインデックス
        cursor.execute(f"CREATE INDEX idx_{self.table_name}_MRP要素 ON {self.table_name}(MRP要素)")
        
        conn.commit()
        self.logger.info(f"インデックス作成完了: {self.table_name}")
            
    # SAP後ろマイナス対応
    def _process_trailing_minus(self, value):
        """SAPの後ろマイナス表記を処理する"""
        if isinstance(value, str) and value.endswith('-'):
            return f"-{value[:-1]}"
        return value

    # Decimal変換（エラー処理強化）
    def _safe_decimal_conversion(self, value):
        """安全にDecimal型に変換する"""
        value = self._process_trailing_minus(value)
        try:
            if value in [None, '', '']:
                return Decimal(0)
            return Decimal(value).quantize(Decimal('0.001'))
        except (InvalidOperation, ValueError, TypeError):
            return Decimal(0)

    # 特殊文字削除
    def _clean_text(self, value):
        """特殊文字を削除する"""
        if isinstance(value, str):
            return ''.join(c for c in value if c.isprintable()).strip()
        return value

    # 在庫計算
    def _calculate_inventory(self, df_batch):
        """在庫計算を行う"""
        df_result = df_batch.copy()  # copyを作成
        grouped = df_result.sort_values(by=['品目', '連続行番号']).groupby('品目')

        for item, group in grouped:
            actual_stock = Decimal(0).quantize(Decimal('0.001'))
            shortage = Decimal(0).quantize(Decimal('0.001'))
            group_indices = group.index  # indexを取得

            for index, row in group.iterrows():
                row_quantity = Decimal(row['入庫_所要量']).quantize(Decimal('0.001'))

                if row['MRP要素'] == '在庫':
                    actual_stock = row_quantity
                    shortage = Decimal(0)
                    allocation = Decimal(0)
                    excess_shortage = actual_stock
                    df_result.loc[index, '引当'] = float(allocation)
                    df_result.loc[index, '過不足'] = excess_shortage
                elif row['MRP要素'] in ['外注依', '受注', '従所要', '入出予', '出荷']:
                    required_qty = abs(row_quantity)

                    if actual_stock >= required_qty:
                        allocation = required_qty
                        actual_stock -= allocation
                    else:
                        allocation = actual_stock
                        shortage += (required_qty - actual_stock)
                        actual_stock = Decimal(0)

                    excess_shortage = actual_stock - shortage
                    if excess_shortage is not None:
                        excess_shortage = Decimal(excess_shortage).quantize(Decimal('0.001'))
                    df_result.loc[index, '引当'] = float(allocation)
                    df_result.loc[index, '過不足'] = excess_shortage
                else:
                    allocation = Decimal(0)
                    excess_shortage = None
                    df_result.loc[index, '引当'] = float(allocation)
                    df_result.loc[index, '過不足'] = excess_shortage

        df_batch.update(df_result)  # 元のdfに反映
        return df_batch


# スクリプトとして実行された場合
if __name__ == "__main__":
    # ロギング設定
    logging.basicConfig(
        filename='logs/zp138_processor.log',
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # ログディレクトリが存在しない場合は作成
    os.makedirs('logs', exist_ok=True)
    
    # コンソールにもログを出力
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)
    
    # 設定ファイルの読み込み（オプション）
    config_file = 'config/processors/zp138_config.json'
    config = {}
    
    if os.path.exists(config_file):
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
    
    # プロセッサの実行
    processor = ZP138Processor(config)
    processor.process()