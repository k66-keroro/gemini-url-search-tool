import pandas as pd
import pyodbc
import numpy as np
from decimal import Decimal
import tkinter as tk
from tkinter import ttk

class ProgressDialog:
    def __init__(self, parent):
        self.parent = parent
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Progress")
        self.dialog.geometry("300x100")

        self.label = ttk.Label(self.dialog, text="")
        self.label.grid(row=0, column=1, padx=5, pady=5, sticky="we")

        self.progress_bar = ttk.Progressbar(self.dialog, maximum=1)
        self.progress_bar.grid(row=1, column=1, padx=5, pady=5, sticky="we")

        self.dialog.transient(parent) 
        self.dialog.grab_set()

    def close(self):
        self.dialog.destroy()

    def update_pg(self, total, current):
        self.progress_bar.configure(value=(current / total))
        self.label.configure(text=f"処理中... {current}/{total}")
        self.dialog.update()

def run_zp02_with_progress():
    root = tk.Tk()
    progress_dialog = ProgressDialog(root)

    # ファイルパスとデータベースの設定
    txt_file_path = r'\\fssha01\common\HOST\ZP02\ZP02.TXT'
    access_db_path = r'C:\Projects_workspace\02_access\Database1.accdb'
    table_name = 'ZP02'

    # Accessデータベースへの接続
    conn_str = f'DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={access_db_path};'
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    # 既存のテーブルがあれば削除
    try:
        cursor.execute(f'DROP TABLE {table_name}')
        conn.commit()
    except Exception as e:
        print(f"テーブル削除中にエラー: {e}")

    # TXTファイルの読み込み
    df = pd.read_csv(txt_file_path, delimiter='\t', encoding='cp932', na_values=["", "NA", " "])

    # データフレームが空でないことを確認
    if df.empty:
        print("データフレームが空です。データを確認してください。")
        progress_dialog.close()
        return

    # プログレスバーの最大値を設定
    total_rows = len(df)
    progress_dialog.update_pg(total_rows, 0)

    # データをAccessに挿入
    for index, row in df.iterrows():
        placeholders = ', '.join(['?'] * len(row))
        insert_query = f'INSERT INTO {table_name} VALUES ({placeholders})'
        row_data = tuple(row)

        try:
            cursor.execute(insert_query, row_data)
        except Exception as e:
            print(f"挿入エラーの詳細: {e}, 行データ: {row_data}")
        
        # プログレスバーを更新
        progress_dialog.update_pg(total_rows, index + 1)

    conn.commit()
    cursor.close()
    conn.close()
    progress_dialog.close()
    print("データのインポートが完了しました。")

if __name__ == "__main__":
    run_zp02_with_progress()
