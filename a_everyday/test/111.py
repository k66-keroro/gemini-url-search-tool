import sqlite3
import pyodbc
from datetime import datetime  # 修正: datetime クラスを直接インポート

def migrate_sqlite_to_access(sqlite_db_path, access_db_path, sqlite_table, access_table, column_mapping):
    """
    SQLite から Access にデータを移行する関数
    """
    # SQLite に接続
    sqlite_conn = sqlite3.connect(sqlite_db_path)
    sqlite_cursor = sqlite_conn.cursor()

    # Access に接続
    access_conn_str = f"DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={access_db_path};"
    access_conn = pyodbc.connect(access_conn_str)
    access_cursor = access_conn.cursor()

    # SQLite テーブルのデータ確認
    sqlite_cursor.execute(f"SELECT COUNT(*) FROM {sqlite_table}")
    row_count = sqlite_cursor.fetchone()[0]
    print(f"SQLite テーブル '{sqlite_table}' の行数: {row_count}")

    if row_count == 0:
        print(f"SQLite テーブル '{sqlite_table}' にデータが存在しません。処理を中止します。")
        return

    # Access テーブルを削除
    try:
        print(f"実行するクエリ: DROP TABLE {access_table}")
        access_cursor.execute(f"DROP TABLE {access_table}")
        access_conn.commit()
        print(f"Access テーブル '{access_table}' を削除しました。")
    except Exception as e:
        print(f"Access テーブル削除中にエラー: {e}")

    # Access テーブルを作成
    create_table_query = f"CREATE TABLE {access_table} ({', '.join([f'{col} {dtype}' for col, dtype in column_mapping.items()])})"
    try:
        print(f"実行するクエリ: {create_table_query}")
        access_cursor.execute(create_table_query)
        access_conn.commit()
        print(f"Access テーブル '{access_table}' を作成しました。")
    except Exception as e:
        print(f"Access テーブル作成中にエラー: {e}")

    # INSERT クエリを定義
    placeholders = ', '.join(['?' for _ in column_mapping.keys()])
    insert_query = f"INSERT INTO {access_table} ({', '.join(column_mapping.keys())}) VALUES ({placeholders})"
    print(f"実行するクエリ: {insert_query}")

    # データ型を変換する関数
    def convert_row(row, column_mapping):
        converted_row = []
        for value, (col, dtype) in zip(row, column_mapping.items()):
            if dtype in ['INTEGER', 'DOUBLE']:
                # 数値型に変換
                try:
                    converted_row.append(float(value) if dtype == 'DOUBLE' else int(value))
                except (ValueError, TypeError):
                    converted_row.append(None)  # 変換できない場合は NULL にする
            elif dtype == 'DATETIME':
                # 日付型に変換
                try:
                    converted_row.append(datetime.strptime(value, '%Y-%m-%d %H:%M:%S') if value else None)
                except (ValueError, TypeError):
                    converted_row.append(None)  # 不正な日付は NULL にする
            else:
                # 文字列型に変換
                converted_row.append(str(value) if value is not None else None)
        return converted_row

    # SQLite データをストリーミングで取得
    sqlite_cursor.execute(f"SELECT * FROM {sqlite_table}")
    batch_size = 5000  # バッチサイズを設定
    batch = []

    access_conn.autocommit = False  # トランザクションを手動管理

    try:
        for i, row in enumerate(iter(sqlite_cursor.fetchone, None), start=1):
            batch.append(convert_row(row, column_mapping))
            if i % batch_size == 0:
                access_cursor.executemany(insert_query, batch)
                access_conn.commit()
                print(f"{i} 行を挿入しました。")
                batch = []

        # 残りのデータを挿入
        if batch:
            access_cursor.executemany(insert_query, batch)
            access_conn.commit()
            print(f"{i} 行を挿入しました。")
    except Exception as e:
        access_conn.rollback()  # エラー時にロールバック
        print(f"データ挿入中にエラー: {e}")
    finally:
        access_conn.autocommit = True  # 自動コミットを再有効化

    # 接続を閉じる
    sqlite_conn.close()
    access_cursor.close()
    access_conn.close()
    print("SQLite と Access の接続を閉じました。")


if __name__ == "__main__":
    # SQLite と Access の設定
    sqlite_db_path = r"C:\Projects_workspace\02_access\Database1.sqlite"
    access_db_path = r"C:\Projects_workspace\02_access\Database1.accdb"
    sqlite_table = "MARA_DL"
    access_table = "MARA_DL"

    # SQLite と Access の列名とデータ型のマッピング
    column_mapping = {
        '品目': 'TEXT',
        '品目テキスト': 'TEXT',
        'プラント': 'TEXT',
        '品目タイプコード': 'TEXT',
        '標準原価': 'DOUBLE',
        '品目階層': 'TEXT',
        '納入予定日数': 'INTEGER',
        '入庫処理日数': 'INTEGER',
        'MRP_管理者': 'TEXT',
        'MRP_管理者名': 'TEXT',
        'メーカー名': 'TEXT',
        '安全重要部品': 'TEXT',
        'ROHSコード': 'TEXT',
        'ROHS日付': 'DATETIME',
        '材料費_設計予算_': 'DOUBLE',
        '加工費_設計予算_': 'DOUBLE',
        '工程': 'TEXT',
        'CMコード': 'TEXT',
        '評価クラス': 'TEXT',
        '品目グループ': 'TEXT',
        '品目grpテキスト': 'TEXT',
        '研究室_設計室': 'TEXT',
        '発注点': 'INTEGER',
        '安全在庫': 'DOUBLE',
        '最終入庫日': 'DATETIME',
        '最終出庫日': 'DATETIME',
        '利益センタ': 'TEXT',
        '調達タイプ': 'TEXT',
        '特殊調達タイプ': 'TEXT',
        '消費モード': 'TEXT',
        '逆消費期間': 'TEXT',
        '順消費期間': 'TEXT',
        '二重ＭＲＰ区分': 'TEXT',
        '販売ステータス': 'TEXT',
        'ＭＲＰタイプ': 'TEXT',
        'タイムフェンス': 'INTEGER',
        'ＭＲＰ出庫保管場所': 'TEXT',
        '棚番': 'TEXT',
        'BOM': 'TEXT',
        '作業手順': 'TEXT',
        'ロットサイズ': 'TEXT',
        '最小ロットサイズ': 'DOUBLE',
        '最大ロットサイズ': 'INTEGER',
        '丸め数量': 'DOUBLE',
        '現会計年度': 'INTEGER',
        '現期間': 'INTEGER',
        '格上げ区分': 'TEXT',
        '将来会計年度': 'INTEGER',
        '将来期間': 'INTEGER',
        '将来予定原価': 'DOUBLE',
        '現在予定原価': 'DOUBLE',
        '前回会計年度': 'INTEGER',
        '前回期間': 'INTEGER',
        '前回予定原価': 'DOUBLE',
        '間接費グループ': 'TEXT',
        '品目登録日': 'DATETIME',
        '日程計画余裕キー': 'INTEGER',
        'プラント固有ステータス': 'TEXT',
        '営業倉庫_最終入庫日': 'DATETIME',
        '営業倉庫_最終出庫日': 'DATETIME',
        '原価計算ロットサイズ': 'INTEGER',
        '設計担当者ID': 'TEXT',
        '設計担当者名': 'TEXT',
        'プラント固有st開始日': 'DATETIME',
        '自動購買発注': 'TEXT',
    }

    # データ移行を実行
    print("データ移行を開始します...")
    migrate_sqlite_to_access(sqlite_db_path, access_db_path, sqlite_table, access_table, column_mapping)
    print("データ移行が完了しました。")