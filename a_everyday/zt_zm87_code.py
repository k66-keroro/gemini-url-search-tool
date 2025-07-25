import pandas as pd
import pyodbc
import datetime

# ファイルパスの定義
txt_file_path = r'C:\\Projects_workspace\\02_access\\テキスト\\zm87n.txt'
access_db_path = r'C:\\Projects_workspace\\02_access\\Database1.accdb'


def import_data_to_access():
    # テキストファイルをDataFrameに読み込む
    df = pd.read_csv(txt_file_path, delimiter=',', encoding='cp932')

    # 列名の前後に余分なスペースがないか確認し、トリムする
    df.columns = df.columns.str.strip()

    # 必要な列のみを使用
    required_columns = ['品目', '発注残数', '正味単価']
    if not all(col in df.columns for col in required_columns):
        raise ValueError(f"必要な列が不足しています: {set(required_columns) - set(df.columns)}")

    # 集計処理を実行
    summary_df = df.groupby('品目').agg(
        発注残=('発注残数', 'sum'),
        発注残金額=('発注残数', lambda x: sum(x * df.loc[x.index, '正味単価']))
    ).reset_index()

    # Accessデータベースの接続文字列を定義
    conn_str = (
        r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
        r'DBQ=' + access_db_path + ';'
    )

    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    table_name = 't_zm87n_集計'

    # テーブル削除を試みるが、存在しない場合のエラーを無視する
    try:
        cursor.execute(f"DROP TABLE {table_name}")
        conn.commit()
        print(f"テーブル '{table_name}' を削除しました。")
    except pyodbc.ProgrammingError as e:
        # テーブルが存在しない場合のエラーを無視
        if "does not exist" in str(e) or "存在しません" in str(e):
            print(f"テーブル '{table_name}' は存在しません。")
        else:
            raise

    # テーブルを作成
    try:
        create_table_query = f"""
        CREATE TABLE {table_name} (
            品目 TEXT(255),
            発注残 DOUBLE,
            発注残金額 DOUBLE
        )
        """
        cursor.execute(create_table_query)
        conn.commit()
        print(f"テーブル '{table_name}' を作成しました。")
    except pyodbc.ProgrammingError as e:
        print(f"テーブル作成中にエラー: {e}")
        conn.rollback()
        conn.close()
        raise

    # データを挿入
    try:
        for _, row in summary_df.iterrows():
            insert_query = f"""
            INSERT INTO {table_name} (品目, 発注残, 発注残金額)
            VALUES (?, ?, ?)
            """
            cursor.execute(insert_query, row['品目'], row['発注残'], row['発注残金額'])

        conn.commit()
        print(f"データが正常に挿入されました。")
    except Exception as e:
        print(f"データ挿入中にエラー: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

# メインブロックを追加
if __name__ == "__main__":
    import_data_to_access()