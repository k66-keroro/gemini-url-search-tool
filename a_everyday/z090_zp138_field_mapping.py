import win32com.client

# 元のAccessデータベースファイルのパス
source_access_db_path = r'C:\\Projects_workspace\\02_access\\Database1.accdb'

# エクスポート先のAccessデータベースファイルのパス
destination_access_db_path = r'\\fsshi01\電源機器製造本部共有\39　部材管理課⇒他部署共有\26　アクセスデータ\在庫でーた.accdb'



# フィールド名のマッピング
field_mapping = {
    #"MRP エリア": "mrpエリア",
    "所要日付": "所要日",
    #"MRP 要素": "mrp要素",
    #"MRP 要素データ": "mrp要素データ",
    "入庫_所要量": "数量",
    "利用可能数量": "在庫",
    "例外Msg": "例外msg",
    "Itm": "itm"
}

# テーブル名
table_name = "t_zp138引当"

# Accessアプリケーションを起動
access_app = win32com.client.Dispatch("Access.Application")
access_app.OpenCurrentDatabase(source_access_db_path)

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

# エクスポート先のデータベースを開く
access_app.OpenCurrentDatabase(destination_access_db_path)

try:
    # テーブルが存在するか確認
    table_exists = False
    for tbl in db.TableDefs:
        if tbl.Name == table_name:
            table_exists = True
            break

    if table_exists:
        access_app.DoCmd.DeleteObject(0, table_name)
        print(f"既存のテーブル {table_name} を削除しました。")
    else:
        print(f"テーブル {table_name} は存在しません。")
except Exception as e:
    print(f"削除エラー: {e}")

try:
    # テーブルをエクスポートする処理
    access_app.DoCmd.TransferDatabase(0, "Microsoft Access", source_access_db_path, 0, table_name, table_name)
    print(f"データを {destination_access_db_path} のテーブル {table_name} にエクスポートしました。")
except Exception as e:
    print(f"エクスポートエラー: {e}")

# エクスポート後にデータベースを閉じる
access_app.CloseCurrentDatabase()
access_app.Quit()

