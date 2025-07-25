"""
SQLite検証GUIツール - SQLite Inspection GUI Tool

主な機能:
1. DBファイル選択: GUIからSQLiteファイルを選択可能
2. パス保持: 選択したDBパスをJSONファイルに保存し、次回起動時に復元
3. テーブル情報表示: テーブル名、行数、カラム数、概算サイズ（row_count × column_count × 50 bytes）を表示（MB単位）
4. テーブル削除: ユーザー定義テーブルを一括削除、または選択テーブルのみ削除
5. VACUUM実行: ファイルサイズを圧縮
6. ログ表示: 実行結果をGUI下部に表示
7. モダンUI: Segoe UIフォント、Treeviewによる表形式、余白と配置調整済み
8. 選択行コピー: Treeviewで選択した行をクリップボードにコピー可能

容量の概算方法:
estimated_size = row_count × column_count × 50  # 1セルあたり約50バイトと仮定し、MB単位に変換

SQLiteの拡張機能は不要です。
"""

import sqlite3
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import json
import os

try:
    import pyperclip
except ImportError:
    pyperclip = None

CONFIG_FILE = "db_config.json"

def save_db_path(path):
    with open(CONFIG_FILE, "w") as f:
        json.dump({"last_db_path": path}, f)

def load_db_path():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f).get("last_db_path", "")
    return ""

def get_table_info(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    tables = cursor.fetchall()
    table_data = []
    for table in tables:
        name = table[0]
        try:
            cursor.execute(f"SELECT COUNT(*) FROM '{name}'")
            row_count = cursor.fetchone()[0]
            cursor.execute(f"PRAGMA table_info('{name}')")
            column_count = len(cursor.fetchall())
            estimated_size_bytes = row_count * column_count * 50
            estimated_size_mb = estimated_size_bytes / (1024 * 1024)
            table_data.append((name, row_count, column_count, f"{estimated_size_mb:.2f} MB"))
        except Exception as e:
            table_data.append((name, "Error", "Error", "Error"))
    conn.close()
    return table_data

def delete_all_tables(db_path, log_callback):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    tables = cursor.fetchall()
    for table in tables:
        name = table[0]
        try:
            cursor.execute(f'DROP TABLE IF EXISTS "{name}";')
            log_callback(f"Deleted table: {name}")
        except Exception as e:
            log_callback(f"Error deleting table {name}: {e}")
    conn.commit()
    conn.close()

def delete_selected_table(db_path, table_name, log_callback):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute(f'DROP TABLE IF EXISTS "{table_name}";')
        log_callback(f"Deleted selected table: {table_name}")
    except Exception as e:
        log_callback(f"Error deleting selected table {table_name}: {e}")
    conn.commit()
    conn.close()

def run_vacuum(db_path, log_callback):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("VACUUM;")
        log_callback("VACUUM completed.")
    except Exception as e:
        log_callback(f"VACUUM error: {e}")
    conn.close()

def copy_selected_row(tree):
    selected = tree.selection()
    if selected and pyperclip:
        values = tree.item(selected[0], "values")
        pyperclip.copy("\t".join(str(v) for v in values))

def update_table_view(tree, db_path):
    for row in tree.get_children():
        tree.delete(row)
    table_data = get_table_info(db_path)
    for data in table_data:
        tree.insert("", "end", values=data)

def create_gui():
    root = tk.Tk()
    root.title("SQLite検証GUIツール")
    root.geometry("800x500")
    root.option_add("*Font", "SegoeUI 10")

    db_path = tk.StringVar(value=load_db_path())

    def log_message(msg):
        log_text.insert(tk.END, msg + "\n")
        log_text.see(tk.END)

    def browse_db():
        path = filedialog.askopenfilename(filetypes=[("SQLite DB", "*.db")])
        if path:
            db_path.set(path)
            save_db_path(path)
            update_table_view(tree, path)

    def delete_selected():
        selected = tree.selection()
        if selected:
            table_name = tree.item(selected[0], "values")[0]
            delete_selected_table(db_path.get(), table_name, log_message)
            update_table_view(tree, db_path.get())

    def copy_row():
        copy_selected_row(tree)

    frame_top = tk.Frame(root)
    frame_top.pack(fill="x", padx=10, pady=5)

    tk.Label(frame_top, text="DB Path:").pack(side="left")
    tk.Entry(frame_top, textvariable=db_path, width=60).pack(side="left", padx=5)
    tk.Button(frame_top, text="Browse", command=browse_db).pack(side="left")

    tree = ttk.Treeview(root, columns=("Table", "Rows", "Columns", "Size"), show="headings")
    for col in ("Table", "Rows", "Columns", "Size"):
        tree.heading(col, text=col)
        tree.column(col, width=150)
    tree.pack(fill="both", expand=True, padx=10, pady=5)

    frame_buttons = tk.Frame(root)
    frame_buttons.pack(fill="x", padx=10, pady=5)

    tk.Button(frame_buttons, text="Delete All Tables", command=lambda: [delete_all_tables(db_path.get(), log_message), update_table_view(tree, db_path.get())]).pack(side="left", padx=5)
    tk.Button(frame_buttons, text="Delete Selected Table", command=delete_selected).pack(side="left", padx=5)
    tk.Button(frame_buttons, text="Run VACUUM", command=lambda: run_vacuum(db_path.get(), log_message)).pack(side="left", padx=5)
    tk.Button(frame_buttons, text="Copy Selected Row", command=copy_row).pack(side="left", padx=5)
    tk.Button(frame_buttons, text="Refresh", command=lambda: update_table_view(tree, db_path.get())).pack(side="left", padx=5)

    log_text = tk.Text(root, height=8)
    log_text.pack(fill="x", padx=10, pady=5)

    if db_path.get():
        update_table_view(tree, db_path.get())

    root.mainloop()

if __name__ == "__main__":
    create_gui()
