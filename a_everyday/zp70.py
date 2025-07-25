import pandas as pd
import pyodbc
import numpy as np
from decimal import Decimal

# ファイルパスとデータベースの設定
txt_file_path = r'C:\Projects_workspace\02_access\テキスト\zp70.txt'
access_db_path = r'C:\Projects_workspace\02_access\Database1.accdb'
table_name = 'ZP70'

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
    # フィールド名のクレンジング
    df.columns = df.columns.str.strip()

    # データのクレンジング
    df = df.where(pd.notnull(df), None)
    df = df.replace(r'^\s*|\s*$|nan|NaN|NA|None', '', regex=True)
    # 数値型の列を0に、文字列型の列を空文字に
    numeric_columns = ['入庫/所要量', '例外グループ', '例外','安全在庫']
    #string_columns = ['購買伝票', 'Ｇ／Ｌ勘定', '原価センタ', '購買情報番号', '購買発注削除', '勘定設定カテゴリ', '追跡番号', '購買情報テキスト', 'プラント固有St', '棚番']

    df[numeric_columns] = df[numeric_columns].fillna(0)
    #df[string_columns] = df[string_columns].fillna('')    
    # 保管場所を文字列型に変換
    df['保管場所'] = df['保管場所'].apply(lambda x: None if pd.isnull(x) or str(x).strip() == '' else int(float(str(x).strip())))
    # 保管場所のデータ型を整数型に設定
    df['保管場所'] = df['保管場所'].astype('Int64')  # pandasのnullable integer type

    # 日付フィールドの変換処理
    date_fields = ['MRP 日付','所要日付','再計画日付']

    for field in date_fields:
        df[field] = df[field].astype(str).str.strip()
        df[field] = df[field].apply(lambda x: x if x.isdigit() and len(x) == 8 else None)

    for field in date_fields:
        df[field] = pd.to_datetime(df[field], format='%Y%m%d', errors='coerce')

    for field in date_fields:
        df[field] = df[field].apply(lambda x: None if pd.isnull(x) else x)

    df = df.replace({pd.NaT: None, np.nan: None})

    # NaNやNoneを明示的に処理
    df = df.where(pd.notnull(df), None)

    # 0をNoneに変換
    df[numeric_columns] = df[numeric_columns].replace(0, None)
    
    
    fields_to_convert = ['指図番号','伝票番号',]# '着手フラグ', '立会予定','エンドユーザコード','受注伝票番号','受注明細番号']

    for field in fields_to_convert:
        # 欠損値を保持しつつ整数型に変換
        df[field] = df[field].apply(lambda x: int(x) if pd.notna(x) else pd.NA)  
        df[field] = df[field].astype(str)  # 文字列型に変換

        # <NA>をNoneに置き換える
        df[field] = df[field].replace({"<NA>": None})
        #df_filtered = df[df['プラント'] == "P100"]
        #df = df[df['プラント'] == "P100"]



    # テーブル構造を定義
    table_columns = {
        'MRP 日付':'DATETIME','プラント':'TEXT','MRP管理者':'TEXT','購買グループ':'TEXT','品目コード':'TEXT',
        '略称':'TEXT','伝票番号':'TEXT','指図番号':'TEXT','所要日付':'DATETIME','再計画日付':'DATETIME',
        '入庫/所要量':'DOUBLE','保管場所':'TEXT','例外グループ':'DOUBLE','例外':'DOUBLE','例外メッセージ':'TEXT',
        '品目テキスト':'TEXT','Type':'TEXT','安全在庫':'DOUBLE','単位':'TEXT',
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
