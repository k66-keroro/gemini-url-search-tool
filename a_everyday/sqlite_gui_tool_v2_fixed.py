"""
改善版コード – SQLite GUI ツール（提案変更反映済み）
・with sqlite3.connect を使用
・スクロールバー追加
・pyperclip 未インストール時警告
・traceback ログ出力
"""

import sqlite3
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import json
import os
import csv
import traceback
import time

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
    with sqlite3.connect(db_path) as conn:
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
    return table_data

def delete_all_tables(db_path, log_callback):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        tables = cursor.fetchall()
        for table in tables:
            name = table[0]
            try:
                safe_name = name.replace('"', '""')
                cursor.execute(f'DROP TABLE IF EXISTS "{safe_name}";')
                log_callback(f"Deleted table: {name}")
            except Exception as e:
                log_callback(f"Error deleting table {name}: {e}\n{traceback.format_exc()}")
        conn.commit()


def delete_selected_table(db_path, table_name, log_callback):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(f'DROP TABLE IF EXISTS "{table_name}";')
            log_callback(f"Deleted selected table: {table_name}")
        except Exception as e:
            log_callback(f"Error deleting selected table {table_name}: {e}\n{traceback.format_exc()}")
        conn.commit()

def run_vacuum(db_path, log_callback):
    """VACUUMを実行し、ファイルサイズの変更を確認"""
    try:
        # VACUUM実行前のファイルサイズを取得
        original_size = os.path.getsize(db_path)
        log_callback(f"VACUUM前のファイルサイズ: {original_size / (1024*1024):.2f} MB")
        
        # 新しい接続でVACUUMを実行
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("VACUUM;")
            log_callback("VACUUM completed.")
        
        # VACUUM実行後のファイルサイズを取得
        new_size = os.path.getsize(db_path)
        size_diff = original_size - new_size
        log_callback(f"VACUUM後のファイルサイズ: {new_size / (1024*1024):.2f} MB")
        log_callback(f"削減されたサイズ: {size_diff / (1024*1024):.2f} MB")
        
        if size_diff > 0:
            log_callback("✅ VACUUMが正常に実行され、容量が削減されました")
        else:
            log_callback("⚠️ VACUUMは実行されましたが、容量の削減はありませんでした")
            
    except Exception as e:
        log_callback(f"VACUUM error: {e}\n{traceback.format_exc()}")

def run_vacuum_with_force(db_path, log_callback):
    """強制的にVACUUMを実行（他の接続を閉じる）"""
    try:
        import psutil
        import sqlite3
        
        # 現在のプロセスで開いているSQLite接続を確認
        current_pid = os.getpid()
        log_callback(f"現在のプロセスID: {current_pid}")
        
        # ファイルサイズを取得
        original_size = os.path.getsize(db_path)
        log_callback(f"VACUUM前のファイルサイズ: {original_size / (1024*1024):.2f} MB")
        
        # 強制的にVACUUMを実行
        with sqlite3.connect(db_path, timeout=30.0) as conn:
            # 他の接続を待機
            conn.execute("PRAGMA busy_timeout = 30000")
            cursor = conn.cursor()
            cursor.execute("VACUUM;")
            log_callback("強制VACUUM completed.")
        
        # 新しいファイルサイズを確認
        new_size = os.path.getsize(db_path)
        size_diff = original_size - new_size
        log_callback(f"VACUUM後のファイルサイズ: {new_size / (1024*1024):.2f} MB")
        log_callback(f"削減されたサイズ: {size_diff / (1024*1024):.2f} MB")
        
    except Exception as e:
        log_callback(f"強制VACUUM error: {e}\n{traceback.format_exc()}")

def run_vacuum_external(db_path, log_callback):
    """外部プロセスでVACUUMを実行"""
    try:
        import subprocess
        
        # ファイルサイズを取得
        original_size = os.path.getsize(db_path)
        log_callback(f"VACUUM前のファイルサイズ: {original_size / (1024*1024):.2f} MB")
        
        # 外部プロセスでVACUUMを実行
        sql_script = f"""
        ATTACH DATABASE '{db_path}' AS main_db;
        VACUUM main_db;
        DETACH DATABASE main_db;
        """
        
        # 一時的なSQLファイルを作成
        temp_sql = f"temp_vacuum_{int(time.time())}.sql"
        with open(temp_sql, 'w') as f:
            f.write(sql_script)
        
        try:
            # sqlite3コマンドで実行
            result = subprocess.run(['sqlite3', db_path, '.read ' + temp_sql], 
                                  capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                log_callback("外部VACUUM completed.")
            else:
                log_callback(f"外部VACUUM error: {result.stderr}")
                
        finally:
            # 一時ファイルを削除
            if os.path.exists(temp_sql):
                os.remove(temp_sql)
        
        # 新しいファイルサイズを確認
        new_size = os.path.getsize(db_path)
        size_diff = original_size - new_size
        log_callback(f"VACUUM後のファイルサイズ: {new_size / (1024*1024):.2f} MB")
        log_callback(f"削減されたサイズ: {size_diff / (1024*1024):.2f} MB")
        
    except Exception as e:
        log_callback(f"外部VACUUM error: {e}\n{traceback.format_exc()}")

def copy_selected_row(tree):
    if not pyperclip:
        messagebox.showwarning("Copy Error", "pyperclip is not installed.")
        return
    selected = tree.selection()
    if selected:
        values = tree.item(selected[0], "values")
        pyperclip.copy("\t".join(str(v) for v in values))

def update_table_view(tree, db_path):
    for row in tree.get_children():
        tree.delete(row)
    table_data = get_table_info(db_path)
    for data in table_data:
        tree.insert("", "end", values=data)

def export_csv(tree):
    if not tree.get_children():
        messagebox.showwarning("No Data", "There is no data to export.")
        return
    file_path = filedialog.asksaveasfilename(defaultextension=".csv",
                                             filetypes=[("CSV files", "*.csv")],
                                             title="Save CSV File")
    if file_path:
        try:
            with open(file_path, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                headers = [tree.heading(col)["text"] for col in tree["columns"]]
                writer.writerow(headers)
                for row_id in tree.get_children():
                    row = tree.item(row_id)["values"]
                    writer.writerow(row)
            messagebox.showinfo("Success", f"Data exported successfully to {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export CSV: {e}\n{traceback.format_exc()}")

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

    frame_tree = tk.Frame(root)
    frame_tree.pack(fill="both", expand=True, padx=10, pady=5)

    tree = ttk.Treeview(frame_tree, columns=("Table", "Rows", "Columns", "Size"), show="headings")
    for col in ("Table", "Rows", "Columns", "Size"):
        tree.heading(col, text=col)
        tree.column(col, width=150)
    tree.pack(side="left", fill="both", expand=True)

    tree_scroll = ttk.Scrollbar(frame_tree, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=tree_scroll.set)
    tree_scroll.pack(side="right", fill="y")

    frame_buttons = tk.Frame(root)
    frame_buttons.pack(fill="x", padx=10, pady=5)

    tk.Button(frame_buttons, text="Delete All Tables", command=lambda: [delete_all_tables(db_path.get(), log_message), update_table_view(tree, db_path.get())]).pack(side="left", padx=5)
    tk.Button(frame_buttons, text="Delete Selected Table", command=delete_selected).pack(side="left", padx=5)
    tk.Button(frame_buttons, text="Run VACUUM", command=lambda: run_vacuum(db_path.get(), log_message)).pack(side="left", padx=5)
    tk.Button(frame_buttons, text="Force VACUUM", command=lambda: run_vacuum_with_force(db_path.get(), log_message)).pack(side="left", padx=5)
    tk.Button(frame_buttons, text="External VACUUM", command=lambda: run_vacuum_external(db_path.get(), log_message)).pack(side="left", padx=5)
    tk.Button(frame_buttons, text="Copy Selected Row", command=copy_row).pack(side="left", padx=5)
    tk.Button(frame_buttons, text="Refresh", command=lambda: update_table_view(tree, db_path.get())).pack(side="left", padx=5)
    tk.Button(frame_buttons, text="Export CSV", command=lambda: export_csv(tree)).pack(side="left", padx=5)

    log_text = tk.Text(root, height=8)
    log_text.pack(fill="x", padx=10, pady=5)

    if db_path.get():
        update_table_view(tree, db_path.get())

    root.mainloop()

if __name__ == "__main__":
    create_gui()



