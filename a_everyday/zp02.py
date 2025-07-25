import pandas as pd
import pyodbc
import numpy as np
from decimal import Decimal

# ファイルパスとデータベースの設定
txt_file_path = r'C:\Projects_workspace\02_access\テキスト\ZP02.TXT'
access_db_path = r'C:\Projects_workspace\02_access\Database1.accdb'
table_name = 'ZP02'

# 値をクリーンアップして整数に変換する関数を追加
def clean_int(value):
    try:
        s = str(value).strip().replace(',', '')
        if '.' in s:
            return int(float(s))
        if s.isdigit():
            return int(s)
        import re
        m = re.match(r'\d+', s)
        return int(m.group()) if m else None
    except Exception:
        return None

def import_data_to_access():
    # Accessデータベースへの接続
    conn_str = f'DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={access_db_path};'
    try:
        conn = pyodbc.connect(conn_str, autocommit=True)
        cursor = conn.cursor()
    except pyodbc.Error as e:
        print(f"データベース接続エラー: {e}")
        return

    # 既存のテーブルがあれば削除
    try:
        cursor.execute(f"DROP TABLE {table_name}")
        conn.commit()
        print(f"既存のテーブル '{table_name}' を削除しました。")
    except pyodbc.Error as e:
        if "does not exist" in str(e) or "テーブル" in str(e):  # テーブルが存在しない場合のエラーを無視
            print(f"テーブル '{table_name}' は存在しません。")
        else:
            print(f"テーブル削除中にエラー: {e}")
            return

    # TXTファイルの読み込み
    try:
        df = pd.read_csv(txt_file_path, delimiter='\t', encoding='cp932', na_values=["", "NA", " "])
    except Exception as e:
        print(f"TXTファイル読み込みエラー: {e}")
        return

    # 欠損値をNoneに変換
    df = df.where(pd.notnull(df), None)

    # 必要なフィールドの追加
    if 'ＷＢＳ要素' in df.columns:
        df['親WBS'] = df['ＷＢＳ要素'].apply(
            lambda x: str(x)[:12].strip() if pd.notnull(x) and x.strip() != '' else None
        )

    # 日付フィールドをリストにする
    from datetime import datetime

    date_fields = [
        '登録日', '出図予定日', '出図実績日', '製造着手日',
        '先手配実績', '入検予定日', '立会予定日', '出庫日付',
        '要求日', '回答日', '実績開始日', '実績終了日',
        '計画終了', '計画開始', '発行日', 'CRTD日付',
        'REL日付', 'PCNF日付', 'CNF日付', 'DLV日付',
        'TECO日付'
    ]

    for field in date_fields:
        if (field in df.columns):
            df[field] = df[field].apply(
                lambda x: None if pd.isnull(x) else datetime.strptime(str(x), '%Y/%m/%d') if isinstance(x, str) else None
            )
    # MRP管理者フィールドを文字列に変換
    if 'MRP管理者' in df.columns:
        df['MRP管理者'] = df['MRP管理者'].astype(str)

    # 保管場所を文字列型に変換
    if '保管場所' in df.columns:
        df['保管場所'] = df['保管場所'].apply(
            lambda x: None if pd.isnull(x) or str(x).strip() == '' else clean_int(x)
        )


    if '金額' in df.columns:
        df['金額'] = df['金額'].apply(
            lambda x: None if pd.isnull(x) else float(x)
        )

    # 対象のフィールドをリストにする
    fields_to_convert = ['台数', '完成残数', '完成数']

    # 各フィールドに対して整数型に変換
    for field in fields_to_convert:
        if field in df.columns:
            # 値をクリーンアップして整数型に変換
            df[field] = df[field].apply(lambda x: clean_int(x))
            # NaNを含む場合にInt64型に変換
            df[field] = df[field].astype('Int64')

    # 新しい完成数フィールドを追加
    if '台数' in df.columns and '完成残数' in df.columns:
        df['完成'] = df['台数'] - df['完成残数']

    # NaNやNoneを明示的に処理
    df = df.replace({pd.NaT: None, np.nan: None})

    # テーブル構造を定義
    table_columns = {
        'MRP管理者': 'TEXT', 'MRP管理者グループ': 'TEXT', 'MRP管理者名': 'TEXT',
        '製造年': 'INTEGER', '製造月': 'INTEGER', '指図番号': 'TEXT',
        '指図タイ': 'TEXT', '登録日': 'DATETIME', '指図ステータス': 'TEXT',
        '受注伝票番号': 'TEXT', '受注伝票明細': 'TEXT', '品目コード': 'TEXT',
        '品目テキスト': 'TEXT', '台数': 'INTEGER', '製造区分': 'TEXT',
        '製造区分名称': 'TEXT', '件名': 'TEXT', 'ＷＢＳ要素': 'TEXT',
        '完成残数': 'INTEGER', '保管場所': 'TEXT', '担当': 'TEXT',
        'メモ': 'TEXT', '出図予定日': 'DATETIME', '出図実績日': 'DATETIME',
        '製造着手日': 'DATETIME', '先手配実績': 'DATETIME', '入検予定日': 'DATETIME',
        '立会予定日': 'TEXT', '出庫日付': 'DATETIME', '要求日': 'TEXT',
        '回答日': 'TEXT', '製造№': 'TEXT', '金額': 'CURRENCY',
        '計画終了': 'DATETIME', '計画開始': 'DATETIME', '発行日': 'DATETIME',
        'CRTD日付': 'DATETIME', 'REL日付': 'DATETIME', 'PCNF日付': 'DATETIME',
        'CNF日付': 'DATETIME', 'DLV日付': 'DATETIME', 'TECO日付': 'DATETIME',
        '完成数': 'INTEGER', '実績開始日': 'DATETIME', '実績終了日': 'DATETIME',
        '<生産管理へ>備考': 'TEXT', '品目タイプ': 'TEXT', '親WBS': 'TEXT'
    }

    # データフレームが空でないことを確認
    if df.empty:
        print("データフレームが空です。データを確認してください。")
        return

    # dfに存在する列だけを選択
    valid_columns = [col for col in table_columns.keys() if col in df.columns]
    df = df[valid_columns]

    # テーブル作成クエリの生成
    create_table_query = f'CREATE TABLE {table_name} ({", ".join([f"[{col}] {table_columns[col]} NULL" for col in valid_columns])})'
    cursor.execute(create_table_query)
    conn.commit()

    # データをAccessに挿入
    for index, row in df.iterrows():
        placeholders = ', '.join(['?'] * len(valid_columns))
        insert_query = f'INSERT INTO {table_name} ({", ".join([f"[{col}]" for col in valid_columns])}) VALUES ({placeholders})'

        row_data = tuple(row[col] for col in valid_columns)
        try:
            cursor.execute(insert_query, row_data)
        except Exception as e:
            print(f"挿入エラーの詳細: {e}")
            print(f"行データ: {row_data}")
            print(f"データ型: {[type(v) for v in row_data]}")

    conn.commit()  # ループ外でコミット
    print("データのインポートが完了しました。")

    # 接続を閉じる（ループ外）
    cursor.close()
    conn.close()

# メインブロックを追加
if __name__ == "__main__":
    import_data_to_access()