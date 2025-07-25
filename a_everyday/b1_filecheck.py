import os
import tkinter as tk
from tkinter import Scrollbar, Text
from datetime import datetime

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

def get_space_padding(file_name, total_length=25):
    """ファイル名に基づいてスペースを計算する関数"""
    full_width_count = sum(1 for char in file_name if len(char.encode('utf-8')) > 1)
    half_width_count = len(file_name) - full_width_count
    padding_length = total_length - (full_width_count * 2 + half_width_count)
    return ' ' * padding_length

def on_button_click():
    """ボタンがクリックされたときの処理"""
    text_box.delete(1.0, tk.END)  # テキストボックスの内容をクリア
    file1 = r"\\fsdes02\Public\課共有\業務課\000_access_data\0_データ更新\よしあつ.accdb"
    file2 = r"\\fsshi01\電源機器製造本部共有\39　部材管理課⇒他部署共有\26　アクセスデータ\在庫でーた.accdb"
    file3 = r"\\fssha01\全社共有\SSS購買課\shingo\pc_工程表.accdb"
    
    date1 = get_file_datetime(file1)
    date2 = get_file_datetime(file2)
    date3 = get_file_datetime(file3)

    space_padding1 = get_space_padding("よしあつ.accdb")
    space_padding2 = get_space_padding("在庫でーた.accdb")
    space_padding3 = get_space_padding("pc_工程表.accdb")

    text1 = f"よしあつ.accdb{space_padding1}： {date1}\n"
    text2 = f"在庫でーた.accdb{space_padding2}： {date2}\n"
    text3 = f"pc_工程表.accdb{space_padding2}： {date3}\n"
    
    text_box.insert(tk.END, text1 + text2+ text3)

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
