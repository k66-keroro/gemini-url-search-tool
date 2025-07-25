import os
import time

# 削除対象のフォルダパス
folder_path = r"C:\Users\sem3171\AppData\Local\Microsoft\Office\16.0\OfficeFileCache"

# 削除する関数
def delete_unwanted_files():
    while True:
        try:
            for filename in os.listdir(folder_path):
                # accdb と laccdb 以外のファイルを削除
                if not (filename.endswith('.accdb') or filename.endswith('.laccdb')):
                    file_path = os.path.join(folder_path, filename)
                    os.remove(file_path)
                    print(f"削除しました: {file_path}")
            break  # すべてのファイルを処理したらループを終了
        except PermissionError:
            print("ファイルが使用中です。再試行します...")
            time.sleep(5)  # 5秒待機して再試行

# 関数を実行
delete_unwanted_files()
