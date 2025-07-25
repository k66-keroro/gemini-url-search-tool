import win32com.client

# Accessデータベースファイルのパス
access_db_path = r'C:\\Projects_workspace\\02_access\\Database1.accdb'

# フィールド名のマッピング
field_mapping = {
    "MRP エリア": "mrpエリア",
    "所要日付": "所要日",
    "MRP 要素": "mrp要素",
    "MRP 要素データ": "mrp要素データ",
    "入庫/所要量": "数量",
    "利用可能数量": "在庫",
    "例外Msg": "例外msg",
    "Itm": "itm"
}

# テーブル名
table_name = "t_zp138引当"

# Accessアプリケーションを起動
access_app = win32com.client.Dispatch("Access.Application")
access_app.OpenCurrentDatabase(access_db_path)

# フィールド名変更処理
db = access_app.CurrentDb()
table_def = db.TableDefs(table_name)

for old_name, new_name in field_mapping.items():
    try:
        field = table_def.Fields(old_name)
        field.Name = new_name
        print(f"フィールド名変更: {old_name} → {new_name}")
    except Exception as e:
        print(f"フィールド名変更エラー: {old_name} → {new_name}, エラー: {e}")

# Accessデータベースを閉じる
access_app.CloseCurrentDatabase()
access_app.Quit()
