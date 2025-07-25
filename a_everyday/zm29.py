import pandas as pd
import pyodbc
import numpy as np

# ファイルパスとデータベースの設定
txt_file_path = r'C:\Projects_workspace\02_access\テキスト\ZM29.txt'
access_db_path = r'C:\Projects_workspace\02_access\Database1.accdb'
table_name = 'zm29'


def import_data_to_access():
    # Accessデータベースへの接続
    conn_str = f'DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={access_db_path};'
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    # 既存のテーブルがあれば削除
    try:
        cursor.execute(f'DROP TABLE {table_name}')
        conn.commit()
    except Exception as e:
        print(f"テーブル削除中にエラー: {e}")

    # TXTファイルの読み込み
    df = pd.read_csv(txt_file_path, delimiter='\t', encoding='SHIFT_JIS', na_values=["", "NA", " "])#',''cp932', error_bad_lines=False
    df.columns = df.columns.str.strip()

    print(f"データフレームの行数: {len(df)}")

    # Rename the 21st column (index 20) explicitly
    #df.columns.values[20] = "出荷指示_1"

    # データのクレンジング
    df = df.where(pd.notna(df), None)
    df = df.replace(r'^\s*|\s*$|nan|NaN|NA|None', '', regex=True)
    # データ型を文字列に変換
    df['ネットワーク・指図番号'] = df['ネットワーク・指図番号'].astype(str)

    # 指図フィールドの値から先頭の「000000」と「0000」を削除
    df['ネットワーク・指図番号'] = df['ネットワーク・指図番号'].str.replace(r'^000000', '', regex=True)
    df['ネットワーク・指図番号'] = df['ネットワーク・指図番号'].str.replace(r'^0000', '', regex=True)

    # 'None' 文字列を None に変換
    #df['指図'] = df['指図'].replace('None', None)



    # 数値型の列を0に、文字列型の列を空文字に
    numeric_columns = ['金額', '製品金額合計', '単価', '最低販売単価or製品単価']#, '安全在庫']
    string_columns = ['保管場所', '入出庫伝票']#, '原価センタ', '購買情報番号', '購買発注削除', '勘定設定カテゴリ', '追跡番号', '購買情報テキスト', 'プラント固有St', '棚番']

    df[numeric_columns] = df[numeric_columns].apply(pd.to_numeric, errors='coerce')
    df[numeric_columns] = df[numeric_columns].fillna(0)
    df[string_columns] = df[string_columns].astype(str)
    df[string_columns] = df[string_columns].fillna('')

    # 購買伝票を明示的に文字列型に変換
    #df['購買伝票'] = df['購買伝票'].astype(str)

    # 日付フィールドの変換処理
    date_fields = ['転記日付'] #, '発注の入庫日付', '納入期日', '入庫日付', '再計画日付'

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
    #df[numeric_columns] = df[numeric_columns].replace(0, None)

    #df = df.iloc[:500]
    print("修正後のカラム名:", df.columns.tolist())

    # テーブル構造を定義
    table_columns = {
        'MRP管理者':'TEXT',
        '転記日付':'DATETIME',
        'WBS番号':'TEXT',
        'ネットワーク・指図番号':'TEXT',
        '受領者':'TEXT',
        '品目コード':'TEXT',
        '品目テキスト':'TEXT',
        '計画数':'INTEGER',
        '完成数':'DOUBLE',
        '単位（完成数）':'TEXT',
        'プラント':'TEXT',
        '保管場所':'TEXT',
        'ﾈｯﾄﾜｰｸ完了':'TEXT',
        '指図完了':'TEXT',
        '入出庫伝票':'TEXT',
        '明細':'INTEGER',
        '移動タイプ':'INTEGER',
        '移動区分':'TEXT',
        'D/C':'TEXT',
        '単価':'DOUBLE',
        '金額':'DOUBLE',
        '最低販売単価or製品単価':'DOUBLE',
        '製品金額合計':'DOUBLE',
    }


    # フィールド名のクレンジング
    df.columns = df.columns.str.strip()

    if df.empty:
        print("データフレームが空です。データを確認してください。")
    else:
        create_table_query = f'CREATE TABLE {table_name} ({", ".join([f"[{col}] {dtype} NULL" for col, dtype in table_columns.items()])})'
        print("作成クエリ:", create_table_query)
        cursor.execute(create_table_query)
        conn.commit()

        df = df[list(table_columns.keys())]

        for index, row in df.iterrows():
            placeholders = ', '.join(['?'] * len(row))
            insert_query = f'INSERT INTO {table_name} VALUES ({placeholders})'
            row_data = tuple(row)

            try:
                cursor.execute(insert_query, row_data)
            except Exception as e:
                print(f"挿入エラーの詳細: {e}")
                print(f"行データ: {row_data}")

        conn.commit()

    # 接続を閉じる
    cursor.close()
    conn.close()
    print("データのインポートが完了しました。")

# メインブロックを追加
if __name__ == "__main__":
    import_data_to_access()