import pandas as pd
import pyodbc
import numpy as np

# ファイルパスとデータベースの設定
txt_file_path = r'C:\Projects_workspace\02_access\テキスト\zp58.txt'
access_db_path = r'C:\Projects_workspace\02_access\Database1.accdb'
table_name = 'zp58'

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
    try:
        df = pd.read_csv(txt_file_path, delimiter='\t', encoding='cp932', na_values=["", "NA", " "], on_bad_lines='skip', low_memory=False)
        df.columns = df.columns.str.strip()
    except pd.errors.ParserError as e:
        print(f"データ読み込み中にエラーが発生しました: {e}")
        return

    print(f"データフレームの行数: {len(df)}")

    # Rename the 21st column (index 20) explicitly
    #df.columns.values[20] = "出荷指示_1"

    # データのクレンジング
    df = df.where(pd.notna(df), None)
    df = df.replace(r'^\s*|\s*$|nan|NaN|NA|None', '', regex=True)
    # データ型を文字列に変換
    df['指図／ネットワーク'] = df['指図／ネットワーク'].astype(str)

    # '指図／ネットワーク'フィールドの値から先頭の「000000」と「0000」を削除
    #df['指図／ネットワーク'] = df['指図／ネットワーク'].str.replace(r'^000000', '', regex=True)
    df['指図／ネットワーク'] = df['指図／ネットワーク'].str.replace(r'^0000', '', regex=True)

    # 'None' 文字列を None に変換
    df['指図／ネットワーク'] = df['指図／ネットワーク'].replace('None', None)

    # 数値型の列を0に、文字列型の列を空文字に
    numeric_columns = ['活動番号','指図明細数量',  '完成数量',  '所要量',  '引落数量',  '差異数量',  '購買発注数量',  '入庫数量',  '標準原価（単価）',  '構成品目／外注工程']
    string_columns = ['保管場所', '入出庫予定',  '構成品目保管場所',  '購買依頼', '購買伝票']

    # 重複を除く
    string_columns = list(dict.fromkeys(string_columns))  # または list(set(string_columns))

    df[numeric_columns] = df[numeric_columns].fillna(0)

    # string_columns の列が存在するか確認し、存在しない場合は追加
    for col in string_columns:
        if col not in df.columns:
            print(f"列 '{col}' が存在しないため、デフォルト値 '' で追加します。")
            df[col] = ''

    # 存在する列だけを抽出して fillna
    existing_string_columns = [col for col in string_columns if col in df.columns]
    df[existing_string_columns] = df[existing_string_columns].fillna('')


    # デバッグ用の出力
    print("データフレームの列名:", df.columns.tolist())
    print("データフレームの列数:", len(df.columns))
    print("string_columns の内容:", string_columns)

    # 欠損値を埋める処理
    try:
        df[string_columns] = df[string_columns].fillna('')
    except ValueError as e:
        print("エラー: string_columns の列数が一致しません。")
        print("データフレームの列名:", df.columns.tolist())
        print("string_columns:", string_columns)
        raise e

    # 購買伝票を明示的に文字列型に変換
    df['購買伝票'] = df['購買伝票'].astype(str)

    # 日付フィールドの変換処理
    date_fields = ['計画開始', '計画終了', '所要日付']

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

    #df = df.iloc[:500]
    print("修正後のカラム名:", df.columns.tolist())

    # テーブル構造を定義
    table_columns = {
        '指図／ネットワーク':'TEXT',
        '活動番号':'INTEGER',
        '計画開始':'DATETIME',
        '計画終了':'DATETIME',
        '品目':'TEXT',
        '品目テキスト':'TEXT',
        '指図明細数量':'DOUBLE',
        '指図明細単位':'TEXT',
        '完成数量':'DOUBLE',
        'プラント':'TEXT',
        '指図タイプ':'TEXT',
        '保管場所':'TEXT',
        '入出庫予定':'TEXT',
        '入出庫明細':'TEXT',
        '構成品目':'TEXT',
        '構成品目テキスト':'TEXT',
        '構成品目保管場所':'TEXT',
        '所要日付':'DATETIME',
        '所要量':'DOUBLE',
        '数量単位':'TEXT',
        '引落数量':'DOUBLE',
        '差異数量':'DOUBLE',
        '購買発注数量':'DOUBLE',
        '購買発注単位':'TEXT',
        '入庫数量':'DOUBLE',
        '常備／購入区分':'TEXT',
        'MRP管理者':'TEXT',
        'MRPタイプ':'TEXT',
        '標準原価（単価）':'DOUBLE',
        '指図完了フラグ':'TEXT',
        'WBS要素':'TEXT',
        '購買依頼':'TEXT',
        '購買伝票':'TEXT',
        'BOM明細':'TEXT',
        'TECO':'TEXT',
        'DLV':'TEXT',
        '入出庫明細削除':'TEXT',
        '納入完了':'TEXT',
        '構成品目／外注工程':'INTEGER',
        '購買発注削除':'TEXT'
    }


    # フィールド名のクレンジング
    df.columns = df.columns.str.strip()

    # 列名の存在確認
    if '指図／ネットワーク' not in df.columns:
        print("エラー: '指図／ネットワーク' 列がデータフレームに存在しません。")
        print("現在の列名:", df.columns.tolist())
        return

    # デバッグ用の出力
    print("データフレームの列名:", df.columns.tolist())
    print("データフレームの列数:", len(df.columns))
    print("定義されたキーの数:", len(table_columns.keys()))

    # 列数とキーの数が一致するか確認
    if len(df.columns) != len(table_columns.keys()):
        print("エラー: 列数とキーの数が一致しません。")
        print("列名:", df.columns.tolist())
        print("キー:", list(table_columns.keys()))
        return

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