import pyodbc

# データベースファイルのパス
db_path = r"\\fsshi01\電源機器製造本部共有\39　部材管理課⇒他部署共有\26　アクセスデータ\在庫でーた.accdb"

# 接続文字列の作成
conn_str = (
    r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
    f'DBQ={db_path};'
)

# データベースへの接続
conn = pyodbc.connect(conn_str)

# テーブル情報の取得
tables = conn.cursor().tables(tableType='TABLE').fetchall()

# テーブル名の表示
for table in tables:
    print(f"テーブル名: {table.table_name}")
