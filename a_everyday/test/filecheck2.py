import os
import tkinter as tk
from tkinter import Scrollbar, Text
from datetime import datetime
import pyodbc  # pyodbcを使ってAccessに接続

def get_file_datetime(file_path):
    """指定されたファイルの最終更新日時を取得する関数"""
    try:
        if os.path.exists(file_path):
            timestamp = os.path.getmtime(file_path)
            return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
        else:
            return "ファイルが存在しません"
    except Exception as e:
        return f"エラー: {e}"

def get_table_update_time(db_path, table_name):
    """指定されたテーブルの最終更新日時を取得する関数"""
    try:
        conn_str = r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=' + db_path
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        # テーブルの最終レコードの更新日時を取得するクエリ
        cursor.execute(f"SELECT TOP 1 * FROM {table_name} ORDER BY LastUpdated DESC")
        row = cursor.fetchone()
        
        conn.close()
        
        if row and 'LastUpdated' in [column[0] for column in cursor.description]:
            last_updated = row.LastUpdated  # ここで正しいフィールド名を指定
            return last_updated.strftime('%Y-%m-%d %H:%M:%S')
        else:
            return "更新日時が取得できません"
    except Exception as e:
        return f"エラー: {e}"


def get_space_padding(file_name, total_length=25):
    """ファイル名に基づいてスペースを計算する関数"""
    full_width_count = sum(1 for char in file_name if len(char.encode('utf-8')) > 1)
    half_width_count = len(file_name) - full_width_count
    padding_length = total_length - (full_width_count * 2 + half_width_count)
    return ' ' * padding_length

def on_button_click():
    """ボタンがクリックされたときの処理"""
    text_box.delete(1.0, tk.END)  # テキストボックスの内容をクリア
    db_path = r"\\fsshi01\電源機器製造本部共有\39　部材管理課⇒他部署共有\26　アクセスデータ\在庫でーた.accdb"
    table_name = "t_zp138引当"
    
    date1 = get_file_datetime(db_path)
    table_update_time = get_table_update_time(db_path, table_name)

    space_padding = get_space_padding(table_name)

    text1 = f"在庫でーた.accdb        ： {date1}\n"
    text2 = f"{table_name}{space_padding}： {table_update_time}\n"
    
    text_box.insert(tk.END, text1 + text2)

# tkinterのウィンドウを作成
root = tk.Tk()
root.title("ファイル更新日時取得")

# スクロールバーの作成
scrollbar = Scrollbar(root)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

# テキストボックスの作成
text_box = Text(root, width=60, height=10, yscrollcommand=scrollbar.set)
text_box.pack(padx=10, pady=10)

# スクロールバーとテキストボックスを接続
scrollbar.config(command=text_box.yview)

# ボタンの作成
button = tk.Button(root, text="更新日時取得", command=on_button_click)
button.pack(pady=10)

# メインループを開始
root.mainloop()
