import time
import traceback
from decimal import Decimal, getcontext

import pandas as pd
import pyodbc
import sqlalchemy
import z900_database_config
from sqlalchemy import create_engine

# 小数点以下の桁数を設定（2桁に設定）
getcontext().prec = 10

# スクリプトの実行時間を測定
start_time = time.time()
def main():
    try:
        print("開始：PostgreSQL接続情報の設定", flush=True)
    
        # PostgreSQL接続情報
        pg_host = z900_database_config.pg_host
        pg_database = z900_database_config.pg_database
        pg_user = z900_database_config.pg_user
        pg_password = z900_database_config.pg_password

        postgresql_connection_str = f"postgresql+psycopg2://{pg_user}:{pg_password}@{pg_host}/{pg_database}"
        engine = create_engine(postgresql_connection_str)

        # Microsoft Accessの接続ファイルパスを設定
        access_file_path = r'C:\Projects_workspace\02_access\Database1.accdb'
        print("アクセスファイルのパス確認：", access_file_path, flush=True)

        # PostgreSQLからデータを取得するクエリ
        query = """
        SELECT
            連続行番号,
            品目,
            名称,
            mrpエリア,
            プラント,
            所要日付,
            mrp要素,
            mrp要素データ,
            CASE
                WHEN 再日程計画日付 = '0' THEN NULL
                ELSE TO_DATE(再日程計画日付::text, 'YYYYMMDD')
            END AS 再日程計画日付,
            例外msg,
            CASE WHEN CAST(数量 AS TEXT) LIKE '%-%' THEN -CAST(REPLACE(CAST(数量 AS TEXT), '-', '') AS FLOAT) ELSE CAST(数量 AS FLOAT) END AS 数量,
            CASE WHEN CAST(在庫 AS TEXT) LIKE '%-%' THEN -CAST(REPLACE(CAST(在庫 AS TEXT), '-', '') AS FLOAT) ELSE CAST(在庫 AS FLOAT) END AS 在庫,
            保管場所,
            入出庫予定,
            itm
        FROM zp138
        ORDER BY 連続行番号
        """
        print("データ取得開始", flush=True)

        with engine.connect() as connection:
            result = connection.execute(sqlalchemy.text(query))
            df = pd.DataFrame(result.fetchall(), columns=result.keys())
        print("データ取得完了：", len(df), "件", flush=True)

        # バッチサイズに分割するジェネレータ関数
        def batch_process(dataframe, batch_size):
            for start in range(0, len(dataframe), batch_size):
                yield dataframe[start:start + batch_size]

        # MRP要素フィールドごとの算出対象を定義
        allocation_mapping = {
            '外注依': 'a',
            '受注': 'a',
            '従所要': 'a',
            '入出予': 'a',
            '出荷': 'a',
            '在庫': '算出元'
        }

        # 在庫引当と過不足を計算する関数
        def calculate_inventory(df_batch, actual_stock=Decimal(0), shortage=Decimal(0), current_item=None):
            result = []
        
            # データを連続行番号でソート
            df_batch = df_batch.sort_values(by='連続行番号').reset_index(drop=True)

            for index, row in df_batch.iterrows():
                # 品目が切り替わったら在庫と不足分をリセット
                if current_item is None or current_item != row['品目']:
                    actual_stock = Decimal(0)
                    shortage = Decimal(0)
                    current_item = row['品目']
                    print(f"\n新しい品目の開始 - 品目: {current_item}")

                print(f"\n=== 行 {index + 1} ===")
                print(f"連続行番号: {row['連続行番号']}, 品目: {row['品目']}, mrp要素: {row['mrp要素']}, 数量: {row['数量']}")

                # Decimal型に変換
                row_quantity = Decimal(row['数量'])

                if row['mrp要素'] == '在庫':
                    # 「在庫」行の場合に在庫を設定し、不足分をリセット
                    actual_stock = row_quantity
                    shortage = Decimal(0)
                    引当 = Decimal(0)
                    過不足 = actual_stock
                    print(f"在庫設定 - actual_stock: {actual_stock}, 引当: {引当}, 過不足: {過不足}")

                elif allocation_mapping.get(row['mrp要素']) == 'a' and row_quantity < 0:
                    # 算出対象で数量がマイナスの所要量
                    required_qty = abs(row_quantity)
                    print(f"算出対象 - required_qty: {required_qty}, 現在の在庫: {actual_stock}, 不足分: {shortage}")

                    if actual_stock >= required_qty:
                        引当 = required_qty
                        actual_stock -= 引当
                    else:
                        引当 = actual_stock
                        shortage += required_qty - actual_stock
                        actual_stock = Decimal(0)

                    過不足 = actual_stock - shortage

                    # 丸め処理（小数点以下2桁）
                    引当 = 引当.quantize(Decimal('0.001'))
                    過不足 = 過不足.quantize(Decimal('0.001'))
                    print(f"計算結果 - 引当: {引当}, 過不足: {過不足}, 更新後の在庫: {actual_stock}, 累積不足分: {shortage}")

                else:
                    引当 = Decimal(0)
                    過不足 = None
                    print(f"対象外のmrp要素 - 引当: {引当}, 過不足: {過不足}")

                result.append({
                    '連続行番号': row['連続行番号'],
                    '品目': row['品目'],
                    '名称': row['名称'],
                    'mrpエリア': row['mrpエリア'],
                    'プラント': row['プラント'],
                    '所要日': pd.to_datetime(str(row['所要日付']), format='%Y%m%d', errors='coerce').date(),
                    'mrp要素': row['mrp要素'],
                    'mrp要素データ': row['mrp要素データ'],
                    '再日程計画日付': pd.to_datetime(str(row['再日程計画日付']), format='%Y%m%d', errors='coerce').date() if row['再日程計画日付'] != '0' else None,
                    '例外msg': row['例外msg'],
                    '数量': row['数量'],
                    '在庫': row['在庫'],
                    '保管場所': row['保管場所'],
                    '入出庫予定': row['入出庫予定'],
                    'itm': row['itm'],
                    '引当': float(引当),
                    '過不足': float(過不足) if 過不足 is not None else None
                })

            return pd.DataFrame(result), actual_stock, shortage, current_item

        # バッチサイズ
        batch_size = 1000
        final_df = pd.DataFrame()
        actual_stock = Decimal(0)
        shortage = Decimal(0)
        current_item = None

        print("データ処理開始", flush=True)
        for batch in batch_process(df, batch_size):
            batch_result, actual_stock, shortage, current_item = calculate_inventory(batch, actual_stock, shortage, current_item)
            final_df = pd.concat([final_df, batch_result], ignore_index=True)
        print("データ処理完了", flush=True)

        # データ型をネイティブなPython型に変換
        final_df = final_df.astype(object).where(pd.notnull(final_df), None)

        # データをリストのタプルに変換
        data_tuples = [tuple(x) for x in final_df.to_records(index=False)]

        # Access データベースへの接続文字列を定義
        access_connection_str = f"DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={access_file_path};"
        print("Access データベースに接続します。", flush=True)

        access_connection = pyodbc.connect(access_connection_str)
        cursor = access_connection.cursor()

        # Access テーブルの存在確認と作成
        print("Access テーブルの確認と作成開始", flush=True)
        create_table_query = """
        CREATE TABLE t_zp138引当 (
            連続行番号 LONG,
            品目 TEXT,
            名称 TEXT,
            mrpエリア TEXT,
            プラント TEXT,
            所要日 DATE,
            mrp要素 TEXT,
            mrp要素データ TEXT,
            再日程計画日付 DATE,
            例外msg TEXT,
            数量 DOUBLE,
            在庫 DOUBLE,
            保管場所 TEXT,
            入出庫予定 TEXT,
            itm TEXT,
            引当 DOUBLE,
            過不足 DOUBLE
        )
        """
        try:
            cursor.execute("DROP TABLE t_zp138引当;")
            access_connection.commit()
            print("既存のテーブルを削除しました。", flush=True)
        except pyodbc.Error as e:
            print("テーブルが存在しないか、削除エラー:", e, flush=True)
        
        try:
            cursor.execute(create_table_query)
            access_connection.commit()
            print("新しいテーブルを作成しました。", flush=True)
        except pyodbc.Error as e:
            print(f"テーブル作成エラー: {e}", flush=True)

        # データベースにデータを挿入
        print("データ挿入開始", flush=True)
        insert_query = """
            INSERT INTO t_zp138引当 (
                連続行番号, 品目, 名称, mrpエリア, プラント, 所要日, mrp要素, mrp要素データ, 再日程計画日付, 例外msg, 数量, 在庫, 保管場所, 入出庫予定, itm, 引当, 過不足
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        for i in range(0, len(data_tuples), batch_size):
            batch = data_tuples[i:i + batch_size]
            cursor.executemany(insert_query, batch)
        access_connection.commit()
        print("データ挿入完了", flush=True)

    except Exception as e:
        print("エラーが発生しました:", e, flush=True)
        print(traceback.format_exc(), flush=True)
    finally:
        if 'access_connection' in locals():
            access_connection.close()
        print(f"Script execution time: {time.time() - start_time:.2f} seconds", flush=True)

# z02_sap_file_dereat.py の例
if __name__ == '__main__':
    # メインの処理を書く
    main()