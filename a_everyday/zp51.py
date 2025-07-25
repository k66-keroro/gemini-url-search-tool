import pandas as pd
import pyodbc
import numpy as np
from decimal import Decimal

# ファイルパスとデータベースの設定
txt_file_path = r'C:\Projects_workspace\02_access\テキスト\ZP51N.TXT'
access_db_path = r'C:\Projects_workspace\02_access\Database1.accdb'
table_name = 'ZP51'

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
    numeric_columns = ['連番1','連番2','連番3','出庫数量','所要残数','在庫数','在庫引当','所要引当残数','計画数量',
                       '計画引当','計画引当残数','C','A','C,A以外','作業0020時間(分)','作業0030時間(分)',
                       '作業0040時間(分)','作業0050時間(分)','作業0060時間(分)','標準原価']
    #string_columns = ['購買伝票', 'Ｇ／Ｌ勘定', '原価センタ', '購買情報番号', '購買発注削除', '勘定設定カテゴリ', '追跡番号', '購買情報テキスト', 'プラント固有St', '棚番']

    df[numeric_columns] = df[numeric_columns].fillna(0)
    #df[string_columns] = df[string_columns].fillna('')    
    # 入庫保管場所を文字列型に変換
    df['入庫保管場所'] = df['入庫保管場所'].apply(lambda x: None if pd.isnull(x) or str(x).strip() == '' else int(float(str(x).strip())))
    # 入庫保管場所のデータ型を整数型に設定
    df['入庫保管場所'] = df['入庫保管場所'].astype('Int64')  # pandasのnullable integer type

    # 日付フィールドの変換処理
    date_fields = ['親指図計画開始日','親指図計画終了日','所要日','子指図計画開始日','子指図計画終了日']

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
    
    
    fields_to_convert = ['親指図番号', '子指図番号']

    def convert_to_int(x):
        if pd.notna(x):
            # 数字部分を抽出し、整数に変換
            num_str = ''.join(filter(str.isdigit, str(x)))
            return int(num_str) if num_str else pd.NA
        return pd.NA

    for field in fields_to_convert:
        df[field] = df[field].apply(convert_to_int)
        df[field] = df[field].astype(str)  # 文字列型に変換

        # <NA>をNoneに置き換える
        df[field] = df[field].replace({"<NA>": None})
        #df_filtered = df[df['プラント'] == "P100"]
        #df = df[df['プラント'] == "P100"]



    # テーブル構造を定義
    table_columns = {
        '連番1':'DOUBLE','連番2':'DOUBLE','連番3':'DOUBLE','所要区分':'TEXT','親指図番号':'TEXT','割当(WBS)':'TEXT',
        '受注伝票':'TEXT','入出庫番号':'TEXT','入庫保管場所':'TEXT','親品目コード':'TEXT','親品目テキスト':'TEXT',
        '原価センタテキスト':'TEXT','出荷伝票':'TEXT','出庫数量':'DOUBLE','親MRP管理者':'TEXT','親指図計画開始日':'DATETIME',
        '親指図計画終了日':'DATETIME','BOM明細番号':'TEXT','子指図番号':'TEXT','子品目コード':'TEXT','子品目テキスト':'TEXT',
        '所要日':'DATETIME','所要残数':'DOUBLE','在庫数':'DOUBLE','在庫引当':'DOUBLE','所要引当残数':'DOUBLE',
        '子MRP管理者':'TEXT','購買発注番号':'TEXT','子指図計画開始日':'DATETIME','子指図計画終了日':'DATETIME',
        '計画数量':'DOUBLE','計画引当':'DOUBLE','計画引当残数':'DOUBLE','作業区４':'TEXT','作業区５':'TEXT','払出完了':'TEXT',
        '進捗':'TEXT','工程(子)':'TEXT','C':'DOUBLE','A':'DOUBLE','C,A以外':'DOUBLE','作業0020時間(分)':'DOUBLE',
        '作業0030時間(分)':'DOUBLE','作業0040時間(分)':'DOUBLE','作業0050時間(分)':'DOUBLE','作業0060時間(分)':'DOUBLE',
        '検査':'TEXT','標準原価':'DOUBLE','指図テキスト':'TEXT',

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
