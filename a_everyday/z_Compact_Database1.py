import win32com.client
import os
import datetime
import shutil

db_file_path = r"C:\Projects_workspace\02_access\Database1.accdb"
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
backup_file_path = db_file_path.replace(".accdb", f"_backup_{timestamp}.accdb")

access_app = None

try:
    access_app = win32com.client.Dispatch("Access.Application")

    try:
        if access_app.CurrentDb is not None:
            access_app.CloseCurrentDatabase()
    except Exception:
        pass

    print(f"データベース '{db_file_path}' の最適化と修復を開始します。")
    print(f"一時バックアップファイル: '{backup_file_path}'")

    success = access_app.CompactRepair(db_file_path, backup_file_path)
    print(f"CompactRepair 成功: {success}")

    if success and os.path.exists(backup_file_path):
        shutil.copy2(backup_file_path, db_file_path)
        print("バックアップファイルで元のデータベースを上書きしました。")

except Exception as e:
    print(f"エラーが発生しました: {e}")

finally:
    if access_app is not None:
        access_app.Quit()
        print("Accessアプリケーションを終了しました。")

    if 'e' not in locals() and os.path.exists(backup_file_path):
        try:
            os.remove(backup_file_path)
            print(f"一時バックアップファイル '{backup_file_path}' を削除しました。")
        except Exception as e:
            print(f"一時バックアップファイルの削除中にエラーが発生しました: {e}")
