import pandas as pd
import pyodbc
import numpy as np
from decimal import Decimal

# ファイルパスとデータベースの設定
txt_file_path = r'C:\Projects_workspace\02_access\テキスト\ZS58MONTH.csv'
access_db_path = r'C:\Projects_workspace\02_access\Database1.accdb'
table_name = 'ZS58'

def import_data_to_access():
    # Accessデータベースへの接続
    conn_str = f'DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={access_db_path};'
    #conn = pyodbc.connect(conn_str)
    conn = pyodbc.connect(conn_str, autocommit=True)
    cursor = conn.cursor()

    # 既存のテーブルがあれば削除
    try:
        cursor.execute(f'DROP TABLE {table_name}')
        conn.commit()
    except Exception as e:
        print(f"テーブル削除中にエラー: {e}")
    
    # TXTファイルの読み込み
    df = pd.read_csv(txt_file_path, delimiter='\t', encoding='cp932', na_values=["", "NA", " "])
    # 欠損値をNoneに変換
    df = df.where(pd.notnull(df), None)


    # 日付フィールドをリストにする
    date_fields = [
             '受注日','請求転記日','出庫転記日'
    ]
    for field in date_fields:
        df[field] = df[field].apply(lambda x: None if pd.isnull(x) else x)
    # もしNaTが残っている場合は、Noneに置き換える
    for field in date_fields:
        df[field] = df[field].where(pd.notnull(df[field]), None)
    
    
    fields_to_convert = ['ネットワーク／指図番号',]# '着手フラグ', '立会予定','エンドユーザコード','受注伝票番号','受注明細番号']

    for field in fields_to_convert:
        # 欠損値を保持しつつ整数型に変換
        df[field] = df[field].apply(lambda x: int(x) if pd.notna(x) else pd.NA)  
        df[field] = df[field].astype(str)  # 文字列型に変換

        # <NA>をNoneに置き換える
        df[field] = df[field].replace({"<NA>": None})
        #df_filtered = df[df['プラント'] == "P100"]
        df = df[df['プラント'] == "P100"]



    # テーブル構造を定義
    table_columns = {
        'プラント':'TEXT','受注伝票番号':'INTEGER','受注明細番号':'INTEGER','請求伝票番号':'INTEGER',
        '請求明細番号':'INTEGER','伝票タイプ':'TEXT','受注先コード':'INTEGER','受注先名':'TEXT',
        '品目コード':'TEXT','品目名':'TEXT','受注日':'DATETIME','受注数':'DOUBLE','営業員':'INTEGER',
        '品目階層':'TEXT','請求済数':'DOUBLE','請求転記日':'DATETIME','標準原価':'DOUBLE','材料費単価':'DOUBLE',
        'JPY契約換算金額':'INTEGER','得意先発注番号':'TEXT','件名':'TEXT','入庫番号':'TEXT','CM記号':'TEXT',
        'ネットワーク／指図番号':'TEXT','WBS番号':'TEXT','品目タイプ':'TEXT','JPY製品換算単価':'DOUBLE',
        'JPY見積製造換算原価':'DOUBLE','材料費（設計予算：単価）':'DOUBLE','加工費（設計予算：単価）':'DOUBLE',
        '見積材費':'DOUBLE','見積材費 社内レート':'DOUBLE','見積材費 単位':'TEXT','JPY見積換算材費':'DOUBLE',
        'JPY税換算金額':'INTEGER','特裁番号':'TEXT','出庫転記日':'DATETIME','特記事項':'TEXT','間接費キー':'TEXT',
    }


    # データフレームが空でないことを確認
    if df.empty:
        print("データフレームが空です。データを確認してください。")
    else:
        # テーブル作成クエリの生成
        create_table_query = f'CREATE TABLE {table_name} ({", ".join([f"[{col}] {dtype} NULL" for col, dtype in table_columns.items()])})'
        cursor.execute(create_table_query)
        conn.commit()

        # データフレームをテーブルに一致させる
        df = df[list(table_columns.keys())]

        # データをAccessに挿入
        for index, row in df.iterrows():
        #for row in df.itertuples(index=False, name=None):            
            placeholders = ', '.join(['?'] * len(row))
            insert_query = f'INSERT INTO {table_name} VALUES ({placeholders})'

            # 行データの型確認
            row_data = tuple(row)
            
            try:
                cursor.execute(insert_query, row_data)
            except Exception as e:
                print(f"挿入エラーの詳細: {e}")
                print(f"行データ: {row_data}")
                print(f"データ型: {[type(v) for v in row_data]}")
                
        conn.commit()
    #print(df[['受注伝票番号', '受注伝票明細', '完成']])

    # 接続を閉じる
    cursor.close()
    conn.close()
    print("データのインポートが完了しました。")

# メインブロックを追加
if __name__ == "__main__":
    import_data_to_access()
