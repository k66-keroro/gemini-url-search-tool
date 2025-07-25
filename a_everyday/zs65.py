import pandas as pd
import pyodbc

# ファイルパスとデータベースの設定
txt_file_path1 = r'C:\Projects_workspace\02_access\テキスト\zs65_sss.txt'
txt_file_path2 = r'C:\Projects_workspace\02_access\テキスト\zs65.txt'
access_db_path = r'C:\Projects_workspace\02_access\Database1.accdb'
table_name = 'zs65'

def import_data_to_access():
    # テキストファイルの読み込みと統合
    column_names = ['品目コード', 'プラント', '品目テキスト', '保管場所', '特殊在庫区分', '特殊在庫番号', '利用可能評価在庫', '利用可能値', '棚番', '滞留日数', '品目タイプ']

    # 1つ目のファイルを読み込む
    df1 = pd.read_csv(txt_file_path1, sep='\t', encoding='SHIFT_JIS', na_values=["", "NA", " "], on_bad_lines='skip')
    # 2つ目のファイルを読み込む
    df2 = pd.read_csv(txt_file_path2, sep='\t', encoding='CP932', na_values=["", "NA", " "], on_bad_lines='skip')

    # 2つのデータフレームを統合
    df = pd.concat([df1, df2], ignore_index=True)

    # フィールド名のクレンジング
    df.columns = df.columns.str.strip()

    # データのクレンジング
    df = df.where(pd.notnull(df), None)
    df = df.replace(r'^\s*|\s*$|nan|NaN|NA|None', '', regex=True)

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

    # テーブル作成
    table_columns = {
        '品目コード':'TEXT',
        'プラント':'TEXT',
        '品目テキスト':'TEXT',
        '保管場所':'TEXT',
        '特殊在庫区分':'TEXT',
        '特殊在庫番号':'TEXT',
        '利用可能評価在庫':'DOUBLE',
        '利用可能値':'DOUBLE',
        '棚番':'TEXT',
        '滞留日数':'INTEGER',
        '品目タイプ':'TEXT',
    }

    if not df.empty:
        create_table_query = f'CREATE TABLE {table_name} ({", ".join([f"[{col}] {dtype} NULL" for col, dtype in table_columns.items()])})'
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
                print(f"データ型: {[type(v) for v in row_data]}")
        conn.commit()

    conn.close()
# メインブロックを追加
if __name__ == "__main__":
    import_data_to_access()