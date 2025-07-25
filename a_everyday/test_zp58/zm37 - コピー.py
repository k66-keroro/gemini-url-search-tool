import pandas as pd
import pyodbc
import numpy as np

# ファイルパスとデータベースの設定
txt_file_path = r'C:\Projects_workspace\02_access\テキスト\zm37.txt'
access_db_path = r'C:\Projects_workspace\02_access\Database1.accdb'
table_name = 'zm37'

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
        import csv
        df = pd.read_csv(txt_file_path, delimiter='\t', encoding='cp932', na_values=["", "NA", " "], quoting=csv.QUOTE_NONE, on_bad_lines='skip', low_memory=False)
        df.columns = df.columns.str.strip()
    except pd.errors.ParserError as e:
        print(f"データ読み込み中にエラーが発生しました: {e}")
        with open(txt_file_path, 'r', encoding='cp932') as file:
            for i, line in enumerate(file):
                if i > 183240 and i < 183250:  # 問題の行付近を確認
                    print(line)
        return

    print(f"データフレームの行数: {len(df)}")

    # Rename the 21st column (index 20) explicitly
    #df.columns.values[20] = "出荷指示_1"

    # データのクレンジング
    df = df.where(pd.notna(df), None)
    df = df.replace(r'^\s*|\s*$|nan|NaN|NA|None', '', regex=True)
    # データ型を文字列に変換
    #df['指図／ネットワーク'] = df['指図／ネットワーク'].astype(str)

    # '指図／ネットワーク'フィールドの値から先頭の「000000」と「0000」を削除
    #df['指図／ネットワーク'] = df['指図／ネットワーク'].str.replace(r'^000000', '', regex=True)
    #df['指図／ネットワーク'] = df['指図／ネットワーク'].str.replace(r'^0000', '', regex=True)

    # 'None' 文字列を None に変換
    #df['指図／ネットワーク'] = df['指図／ネットワーク'].replace('None', None)

    # 数値型の列を0に、文字列型の列を空文字に
    numeric_columns = ['単価','納入予定日数','輸入諸掛率','材料単価','加工単価','過剰納入許容範囲','不足納入許容範囲',]
    string_columns = ['購買情報', '購買グループ']

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
    #df['購買伝票'] = df['購買伝票'].astype(str)

    # 日付フィールドの変換処理
    date_fields = ['納入予定日数', '登録日', '有効開始日', '有効終了日']

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
    #print("修正後のカラム名:", df.columns.tolist())

    # テーブル構造を定義
    table_columns = {
        '購買情報':'TEXT',
        '仕入先勘定GRP':'TEXT',
        'プラント':'TEXT',
        '仕入先コード':'TEXT',
        '仕入先名称':'TEXT',
        '品目コード':'TEXT',
        '品目テキスト':'TEXT',
        '工程外注品目コード':'TEXT',
        '品目グループ':'TEXT',
        'テキスト (短)':'TEXT',
        'ソートキー':'TEXT',
        '購買グループ':'TEXT',
        '単価':'DOUBLE',
        '通貨':'TEXT',
        '納入予定日数':'INTEGER',
        '税':'TEXT',
        'ERS不可':'TEXT',
        '削除':'TEXT',
        '登録日':'INTEGER',
        '輸入諸掛率':'DOUBLE',
        '単位':'TEXT',
        '供給元一覧':'TEXT',
        'Fix':'TEXT',
        'MRP区分':'TEXT',
        '有効開始日':'INTEGER',
        '材料単価':'DOUBLE',
        '加工単価':'DOUBLE',
        '過剰納入無制限':'TEXT',
        '過剰納入許容範囲':'DOUBLE',
        '不足納入許容範囲':'DOUBLE',
        '有効終了日':'INTEGER',
        '発注単位':'TEXT',
    }




    # フィールド名のクレンジング
    df.columns = df.columns.str.strip()



    # デバッグ用の出力
    #print("データフレームの列名:", df.columns.tolist())
    #print("データフレームの列数:", len(df.columns))
    #print("定義されたキーの数:", len(table_columns.keys()))

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