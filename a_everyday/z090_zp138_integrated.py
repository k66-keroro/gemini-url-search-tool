import pandas as pd
import pyodbc
import sqlite3
from decimal import Decimal, InvalidOperation, getcontext
import time
from datetime import datetime
import logging
import win32com.client
import os

# ログ設定
logging.basicConfig(filename='inventory.log', level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# スクリプトの実行時間を測定
start_time = time.time()

# 小数点以下の桁数を設定
getcontext().prec = 10

# ファイルパスの設定
INPUT_FILE_PATH = r'\\fssha01\common\HOST\ZP138\ZP138.txt'
SQLITE_DB_PATH = r'C:\Projects_workspace\02_access\Database1.sqlite'
ACCESS_DB_PATH = r'C:\Projects_workspace\02_access\Database1.accdb'
DESTINATION_ACCESS_DB_PATH = r'\\fsshi01\電源機器製造本部共有\39　部材管理課⇒他部署共有\26　アクセスデータ\在庫でーた.accdb'
TABLE_NAME = 't_zp138引当'

# フィールド名のマッピング
FIELD_MAPPING = {
    "所要日付": "所要日",
    "入庫_所要量": "数量",
    "利用可能数量": "在庫",
    "例外Msg": "例外msg",
    "Itm": "itm"
}

# カラム名のマッピング
COLUMN_MAPPING = {
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

# SAP後ろマイナス対応
def process_trailing_minus(value):
    """SAPの後ろマイナス表記を処理する"""
    if isinstance(value, str) and value.endswith('-'):
        return f"-{value[:-1]}"
    return value

# 日付フォーマット
def format_date_for_db(date):
    """日付をデータベース用にフォーマットする"""
    if pd.isnull(date):
        return None
    return pyodbc.Date(date.year, date.month, date.day)

# Decimal変換（エラー処理強化）
def safe_decimal_conversion(value):
    """安全にDecimal型に変換する"""
    value = process_trailing_minus(value)
    try:
        if value in [None, '', '']:
            return Decimal(0)
        return Decimal(value).quantize(Decimal('0.001'))
    except (InvalidOperation, ValueError, TypeError):
        return Decimal(0)

# 在庫計算
def calculate_inventory(df_batch):
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

# 文字列の切り詰め関数
def truncate_text(text, max_length=255):
    """文字列を指定の長さに切り詰める"""
    if isinstance(text, str):
        return text[:max_length]
    return text

# 特殊文字削除
def clean_text(value):
    """特殊文字を削除する"""
    if isinstance(value, str):
        return ''.join(c for c in value if c.isprintable()).strip()
    return value

def read_and_process_data():
    """データを読み込み、処理する"""
    try:
        logger.info(f"ファイル読み込み開始: {INPUT_FILE_PATH}")
        data = pd.read_csv(INPUT_FILE_PATH, delimiter='\t', encoding='cp932', header=0)
        logger.info(f"ファイル読み込み完了: {len(data)}行")
    except FileNotFoundError:
        logger.error(f"エラー: ファイルが見つかりません: {INPUT_FILE_PATH}")
        print(f"エラー: ファイルが見つかりません: {INPUT_FILE_PATH}")
        return None
    except Exception as e:
        logger.error(f"ファイルの読み込み中にエラーが発生しました: {e}")
        print(f"ファイルの読み込み中にエラーが発生しました: {e}")
        return None

    # カラム名を変更
    data = data.rename(columns=COLUMN_MAPPING)

    # 「引当」と「過不足」カラムを追加 (初期値はNone)
    data['引当'] = None
    data['過不足'] = None

    # 日付列処理
    data['所要日付'] = pd.to_datetime(data['所要日付'], format='%Y%m%d', errors='coerce')
    data['所要日付'] = data['所要日付'].where(pd.notna(data['所要日付']), None)

    data['再日程計画日付'] = pd.to_datetime(data['再日程計画日付'], format='%Y%m%d', errors='coerce')
    data['再日程計画日付'] = data['再日程計画日付'].where(pd.notna(data['再日程計画日付']), None)

    # 数値列処理
    data['入庫_所要量'] = data['入庫_所要量'].apply(safe_decimal_conversion)
    data['利用可能数量'] = data['利用可能数量'].apply(safe_decimal_conversion)

    # 保管場所整形
    data['保管場所'] = data['保管場所'].fillna('').apply(
        lambda x: str(int(x)) if isinstance(x, (int, float)) else str(x)
    ).str.replace(r',.*$', '', regex=True)

    # 過不足計算
    logger.info("在庫計算処理開始")
    final_df = calculate_inventory(data)
    logger.info("在庫計算処理完了")

    # データ変換とNoneへの統一
    for col in final_df.select_dtypes(exclude=['datetime64[ns]']):  # datetime64[ns]型は除外
        if pd.api.types.is_numeric_dtype(final_df[col]):
            continue  # 数値型はスキップ
        else:  # 文字列型の場合
            final_df[col] = final_df[col].apply(clean_text)
            final_df[col] = final_df[col].fillna('NULL')

    # MRP要素データのNULLをpd.NAに変換
    final_df['MRP要素データ'] = final_df['MRP要素データ'].apply(
        lambda x: pd.NA if x == 'NULL' or pd.isna(x) else x
    )
    # Noneをpd.NAに変換
    final_df['MRP要素データ'] = final_df['MRP要素データ'].fillna(pd.NA)
    final_df['例外Msg'] = final_df['例外Msg'].fillna(pd.NA)

    return final_df

def save_to_sqlite(df):
    """データをSQLiteに保存する"""
    # SQLiteデータベースに接続
    sqlite_conn = sqlite3.connect(SQLITE_DB_PATH)
    sqlite_cursor = sqlite_conn.cursor()

    try:
        # 既存テーブル削除
        sqlite_cursor.execute(f"DROP TABLE IF EXISTS {TABLE_NAME}")
        sqlite_conn.commit()
        logger.info(f"SQLiteテーブル削除: {TABLE_NAME}")

        # テーブル作成
        columns = []
        for col_name_txt, col_name_db in COLUMN_MAPPING.items():
            if col_name_db == '連続行番号':
                columns.append(f"連続行番号 INTEGER")
            elif col_name_db in ['入庫_所要量', '利用可能数量', '引当', '過不足']:
                columns.append(f"{col_name_db} REAL")
            elif col_name_db in ['所要日付', '再日程計画日付']:
                columns.append(f"{col_name_db} TEXT")
            else:
                columns.append(f"{col_name_db} TEXT")

        create_table_sql = f"""
            CREATE TABLE {TABLE_NAME} (
                {", ".join(columns)}
            )
        """
        sqlite_cursor.execute(create_table_sql)
        sqlite_conn.commit()
        logger.info(f"SQLiteテーブル作成: {TABLE_NAME}")

        # データをSQLiteに挿入
        for _, row in df.iterrows():
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
                            logger.warning(f"Warning: Could not convert '{value}' to integer.")
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
                        logger.warning(f"Warning: Value for {col_name_db} is not a datetime object: {value}, type: {type(value)}")
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
                INSERT INTO {TABLE_NAME} ({cols_str})
                VALUES ({placeholders_str})
            """
            sqlite_cursor.execute(sql, values)

        sqlite_conn.commit()
        logger.info(f"SQLiteにデータ挿入完了: {len(df)}行")
        return True
    except sqlite3.Error as e:
        logger.error(f"SQLiteエラーが発生しました: {e}")
        print(f"SQLiteエラーが発生しました: {e}")
        sqlite_conn.rollback()
        return False
    finally:
        sqlite_conn.close()

def export_to_access():
    """SQLiteからAccessにデータをエクスポートし、フィールド名を変更する"""
    try:
        # SQLiteからデータを取得
        sqlite_conn = sqlite3.connect(SQLITE_DB_PATH)
        sqlite_cursor = sqlite_conn.cursor()
        
        # テーブル構造を取得
        sqlite_cursor.execute(f"PRAGMA table_info({TABLE_NAME})")
        columns_info = sqlite_cursor.fetchall()
        column_names = [col[1] for col in columns_info]
        
        # データを取得
        sqlite_cursor.execute(f"SELECT * FROM {TABLE_NAME}")
        rows = sqlite_cursor.fetchall()
        sqlite_conn.close()
        
        # Accessデータベースに接続
        connection_string = f'DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={ACCESS_DB_PATH};'
        with pyodbc.connect(connection_string) as access_conn:
            access_cursor = access_conn.cursor()
            
            # 既存テーブル削除
            try:
                access_cursor.execute(f"DROP TABLE {TABLE_NAME}")
                access_conn.commit()
                logger.info(f"Accessテーブル削除: {TABLE_NAME}")
            except pyodbc.Error:
                pass

            # テーブル作成
            columns = []
            for col_name_db in column_names:
                if col_name_db == '連続行番号':
                    columns.append(f"[連続行番号] LONG")
                elif col_name_db in ['入庫_所要量', '利用可能数量', '引当', '過不足']:
                    columns.append(f"[{col_name_db}] DOUBLE")
                elif col_name_db in ['所要日付', '再日程計画日付']:
                    columns.append(f"[{col_name_db}] DATETIME")
                else:
                    columns.append(f"[{col_name_db}] TEXT(255)")

            create_table_sql = f"""
                CREATE TABLE {TABLE_NAME} (
                    {", ".join(columns)}
                )
            """
            access_cursor.execute(create_table_sql)
            access_conn.commit()
            logger.info(f"Accessテーブル作成: {TABLE_NAME}")

            # データをAccessに挿入
            for row in rows:
                values = []
                cols = []
                placeholders = []

                for i, col_name_db in enumerate(column_names):
                    value = row[i]
                    if col_name_db in ['所要日付', '再日程計画日付'] and value:
                        try:
                            value = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
                        except (ValueError, TypeError):
                            value = None
                    values.append(value)
                    cols.append(f"[{col_name_db}]")
                    placeholders.append("?")

                cols_str = ", ".join(cols)
                placeholders_str = ", ".join(placeholders)
                
                sql = f"""
                    INSERT INTO {TABLE_NAME} ({cols_str})
                    VALUES ({placeholders_str})
                """
                access_cursor.execute(sql, values)

            access_conn.commit()
            logger.info(f"Accessにデータ挿入完了: {len(rows)}行")
        
        # フィールド名の変更とエクスポート処理
        access_app = win32com.client.Dispatch("Access.Application")
        access_app.OpenCurrentDatabase(ACCESS_DB_PATH)
        
        # フィールド名変更処理
        db = access_app.CurrentDb()
        table_def = db.TableDefs(TABLE_NAME)

        for old_name, new_name in FIELD_MAPPING.items():
            try:
                field = table_def.Fields(old_name)
                field.Name = new_name
                logger.info(f"フィールド名変更: {old_name} → {new_name}")
            except Exception as e:
                logger.error(f"フィールド名変更エラー: {old_name} → {new_name}, エラー: {e}")
                print(f"フィールド名変更エラー: {old_name} → {new_name}, エラー: {e}")

        # Accessデータベースを閉じる
        access_app.CloseCurrentDatabase()
        
        # エクスポート先のデータベースを開く
        # 先にエクスポート先フォルダが存在するか確認
        dest_dir = os.path.dirname(DESTINATION_ACCESS_DB_PATH)
        if not os.path.exists(dest_dir):
            logger.error(f"エクスポート先フォルダが存在しません: {dest_dir}")
            print(f"エクスポート先フォルダが存在しません: {dest_dir}")
            return False
            
        access_app.OpenCurrentDatabase(DESTINATION_ACCESS_DB_PATH)
        
        try:
            # テーブルが存在するか確認し、存在する場合は削除
            access_app.DoCmd.DeleteObject(0, TABLE_NAME)
            logger.info(f"既存のテーブル {TABLE_NAME} を削除しました。")
        except Exception as e:
            logger.info(f"テーブル {TABLE_NAME} は存在しないか、削除できませんでした: {e}")
            
        try:
            # テーブルをエクスポートする処理
            access_app.DoCmd.TransferDatabase(0, "Microsoft Access", ACCESS_DB_PATH, 0, TABLE_NAME, TABLE_NAME)
            logger.info(f"データを {DESTINATION_ACCESS_DB_PATH} のテーブル {TABLE_NAME} にエクスポートしました。")
            print(f"データを {DESTINATION_ACCESS_DB_PATH} のテーブル {TABLE_NAME} にエクスポートしました。")
        except Exception as e:
            logger.error(f"エクスポートエラー: {e}")
            print(f"エクスポートエラー: {e}")
            return False
        finally:
            # エクスポート後にデータベースを閉じる
            access_app.CloseCurrentDatabase()
            access_app.Quit()
            
        return True
    except Exception as e:
        logger.error(f"予期せぬエラーが発生しました: {e}")
        print(f"予期せぬエラーが発生しました: {e}")
        return False

def main():
    """メイン処理"""
    try:
        print("ZP138データ処理を開始します...")
        logger.info("ZP138データ処理を開始します")
        
        # データ読み込みと処理
        df = read_and_process_data()
        if df is None:
            return
            
        # SQLiteに保存
        if not save_to_sqlite(df):
            return
            
        # Accessにエクスポート
        if not export_to_access():
            return
            
        processing_time = time.time() - start_time
        logger.info(f"データ処理が完了しました。処理時間: {processing_time:.2f}秒")
        print(f"データ処理が完了しました。処理時間: {processing_time:.2f}秒")
        
    except Exception as e:
        logger.error(f"処理中にエラーが発生しました: {e}")
        print(f"処理中にエラーが発生しました: {e}")

if __name__ == "__main__":
    main()