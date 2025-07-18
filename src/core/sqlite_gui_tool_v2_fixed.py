import re
import time
import csv
import json
from tkinter import filedialog, ttk, messagebox
import tkinter as tk
import sqlite3
import sys
import os
from pathlib import Path
import traceback

# GUIツール自身のファイルパスを基準にプロジェクトルートを特定
GUI_TOOL_DIR = Path(os.path.abspath(os.path.dirname(__file__)))
GUI_PROJECT_ROOT = GUI_TOOL_DIR.parents[1]  # src/core の2つ上の階層

# プロジェクトルートをsys.pathに追加
if str(GUI_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(GUI_PROJECT_ROOT))

try:
    # SQLiteManagerをインポート
    from src.core.sqlite_manager import SQLiteManager
    from config.constants import Paths
    # PathsクラスのPROJECT_ROOTをGUI_PROJECT_ROOTで上書き
    _original_paths_init = Paths.__init__

    def _new_paths_init(self, *args, **kwargs):
        _original_paths_init(self, *args, **kwargs)
        self.PROJECT_ROOT = GUI_PROJECT_ROOT
        self.LOGS = self.PROJECT_ROOT / 'logs'
        self.RAW_DATA = self.PROJECT_ROOT / 'data' / 'raw'
    Paths.__init__ = _new_paths_init

except ImportError as e:
    SQLiteManager = None

    class Paths:
        def __init__(self):
            self.PROJECT_ROOT = GUI_PROJECT_ROOT
            self.LOGS = self.PROJECT_ROOT / 'logs'
            self.RAW_DATA = self.PROJECT_ROOT / 'data' / 'raw'
    print(f"警告: SQLiteManagerまたはPathsのインポートに失敗しました。一部機能が制限されます。エラー: {e}")
    print(traceback.format_exc())

"""
改善版コード – SQLite GUI ツール（提案変更反映済み）
・with sqlite3.connect を使用
・スクロールバー追加
・pyperclip 未インストール時警告
・traceback ログ出力
・エラー再処理機能追加
"""


try:
    import pyperclip
except ImportError:
    pyperclip = None

CONFIG_FILE = "db_config.json"


def sanitize_table_name(table_name: str) -> str:
    """
    テーブル名を適切に変換（日本語や特殊文字を避ける）

    Args:
        table_name: 元のテーブル名

    Returns:
        変換後のテーブル名
    """
    import re

    # 日本語文字を含むかチェック
    has_japanese = re.search(r'[ぁ-んァ-ン一-龥]', table_name)

    # 日本語文字を含む場合は、ローマ字に変換するか、プレフィックスを付ける
    if has_japanese:
        # 簡易的な変換: 日本語テーブル名にはt_を付ける
        sanitized = f"t_{hash(table_name) % 10000:04d}"
    else:
        # 英数字以外の文字を_に置換
        sanitized = re.sub(r'[^a-zA-Z0-9]', '_', table_name)

        # 連続する_を単一の_に置換
        sanitized = re.sub(r'_+', '_', sanitized)

        # 先頭が数字の場合、t_を付ける
        if sanitized and sanitized[0].isdigit():
            sanitized = f"t_{sanitized}"

        # 先頭と末尾の_を削除
        sanitized = sanitized.strip('_')

    return sanitized


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
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        tables = cursor.fetchall()
        table_data = []
        for table in tables:
            # クォートを除去して返す
            name = table[0].strip('"').strip("'")
            try:
                cursor.execute(f"SELECT COUNT(*) FROM '{name}'")
                row_count = cursor.fetchone()[0]
                cursor.execute(f"PRAGMA table_info('{name}')")
                column_count = len(cursor.fetchall())
                estimated_size_bytes = row_count * column_count * 50
                estimated_size_mb = estimated_size_bytes / (1024 * 1024)
                table_data.append(
                    (name, row_count, column_count, f"{estimated_size_mb:.2f} MB"))
            except Exception as e:
                table_data.append((name, "Error", "Error", "Error"))
    return table_data


def delete_all_tables(db_path, log_callback):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        tables = cursor.fetchall()
        for table in tables:
            name = table[0]
            try:
                # テーブル名からクォートを除去してからエスケープ
                clean_name = name.strip('"').strip("'")
                safe_name = clean_name.replace('"', '""')
                cursor.execute(f'DROP TABLE IF EXISTS "{safe_name}";')
                log_callback(f"Deleted table: {name}")
            except Exception as e:
                log_callback(
                    f"Error deleting table {name}: {e}\n{traceback.format_exc()}")
        conn.commit()


def delete_selected_table(db_path, table_name, log_callback):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        try:
            # テーブル名からクォートを除去してからエスケープ
            clean_name = table_name.strip('"').strip("'")
            safe_name = clean_name.replace('"', '""')
            cursor.execute(f'DROP TABLE IF EXISTS "{safe_name}";')
            log_callback(f"Deleted selected table: {table_name}")
        except Exception as e:
            log_callback(
                f"Error deleting selected table {table_name}: {e}\n{traceback.format_exc()}")
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

        # Windows環境でのsqlite3コマンドの検出
        sqlite3_cmd = None

        # 1. PATHからsqlite3を検索
        try:
            result = subprocess.run(
                ['sqlite3', '--version'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                sqlite3_cmd = 'sqlite3'
                log_callback(f"sqlite3コマンドを検出: {result.stdout.strip()}")
        except FileNotFoundError:
            pass

        # 2. 一般的なWindowsのsqlite3パスを試行
        if not sqlite3_cmd:
            possible_paths = [
                r"C:\Program Files\SQLite\sqlite3.exe",
                r"C:\Program Files (x86)\SQLite\sqlite3.exe",
                r"C:\sqlite\sqlite3.exe",
                r"C:\Windows\System32\sqlite3.exe"
            ]

            for path in possible_paths:
                if os.path.exists(path):
                    sqlite3_cmd = path
                    log_callback(f"sqlite3コマンドを検出: {path}")
                    break

        if not sqlite3_cmd:
            log_callback("❌ sqlite3コマンドが見つかりません。以下のいずれかをインストールしてください:")
            log_callback("  1. SQLite公式サイトからsqlite3.exeをダウンロード")
            log_callback("  2. Chocolatey: choco install sqlite")
            log_callback("  3. 手動でPATHに追加")
            return

        # 外部プロセスでVACUUMを実行
        sql_script = f"""
        VACUUM;
        """

        # 一時的なSQLファイルを作成
        temp_sql = f"temp_vacuum_{int(time.time())}.sql"
        with open(temp_sql, 'w') as f:
            f.write(sql_script)

        try:
            # sqlite3コマンドで実行
            cmd = [sqlite3_cmd, db_path, '.read ' + temp_sql]
            log_callback(f"実行コマンド: {' '.join(cmd)}")

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=60)

            if result.returncode == 0:
                log_callback("✅ 外部VACUUM completed.")
            else:
                log_callback(f"❌ 外部VACUUM error: {result.stderr}")
                log_callback(f"stdout: {result.stdout}")

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
                                             filetypes=[
                                                 ("CSV files", "*.csv")],
                                             title="Save CSV File")
    if file_path:
        try:
            with open(file_path, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                headers = [tree.heading(col)["text"]
                           for col in tree["columns"]]
                writer.writerow(headers)
                for row_id in tree.get_children():
                    row = tree.item(row_id)["values"]
                    writer.writerow(row)
            messagebox.showinfo(
                "Success", f"Data exported successfully to {file_path}")
        except Exception as e:
            messagebox.showerror(
                "Error", f"Failed to export CSV: {e}\n{traceback.format_exc()}")


def parse_error_log(log_file_path: Path) -> list:
    errors = []
    if not log_file_path.exists():
        return errors

    with open(log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            match_file_fail = re.search(r"❌ ファイル処理失敗: (.*?) - (.*)", line)
            match_structure_fail = re.search(r"❌ 構造最終化失敗: (.*?) - (.*)", line)

            if match_file_fail:
                file_name = match_file_fail.group(1).strip()
                error_message = match_file_fail.group(2).strip()
                errors.append(
                    {'file_name': file_name, 'error_message': error_message})
            elif match_structure_fail:
                table_name = match_structure_fail.group(1).strip()
                error_message = match_structure_fail.group(2).strip()
                # 構造最終化失敗の場合、ファイル名が不明なためテーブル名をファイル名として扱う
                errors.append({'file_name': table_name,
                              'error_message': error_message})
    return errors


def load_and_display_errors(error_tree, log_callback):
    """エラーログからエラー情報を読み込み、表示する"""
    try:
        app_paths = Paths()
        log_file_path = app_paths.LOGS / "main.log"

        if not log_file_path.exists():
            log_callback(f"⚠️ ログファイルが見つかりません: {log_file_path}")
            return

        # エラーツリーをクリア
        for row in error_tree.get_children():
            error_tree.delete(row)

        # エラーログを解析
        errors = parse_error_log(log_file_path)

        if not errors:
            log_callback("✅ エラーログにエラーは見つかりませんでした。")
            return

        # エラー情報をツリーに追加
        for error in errors:
            error_tree.insert("", "end", values=(
                error['file_name'], error['error_message']))

        log_callback(f"📋 エラーログから {len(errors)} 件のエラーを読み込みました。")

    except Exception as e:
        log_callback(f"❌ エラーログの読み込み中にエラーが発生しました: {e}")
        log_callback(f"  トレースバック:\n{traceback.format_exc()}")


def create_gui():
    def import_files_to_db():
        if not db_path.get():
            messagebox.showwarning("No DB", "先にDBファイルを選択してください。")
            return
        if SQLiteManager is None:
            messagebox.showerror("Error", "SQLiteManagerのインポートに失敗しました。")
            return
        file_paths = filedialog.askopenfilenames(
            title="インポートするファイルを選択",
            filetypes=[("データファイル", "*.csv *.txt *.xlsx *.xls")]
        )
        if not file_paths:
            return

        manager = SQLiteManager(db_path=db_path.get())
        for file_path_str in file_paths:
            file_path = Path(file_path_str)
            file_name = file_path.name
            table_name_orig = file_path.stem.lower()

            # テーブル名を適切に変換（日本語や特殊文字を避ける）
            table_name = sanitize_table_name(table_name_orig)

            try:
                # 統一インターフェースでファイル処理
                config = manager.get_file_processing_config(file_name)
                log_message(
                    f"--- インポート開始: {file_name} → {table_name} (encoding={config['encoding']}, quoting={config['quoting']}) ---")

                # 元のテーブル名と変換後のテーブル名が異なる場合はログに記録
                if table_name != table_name_orig:
                    log_message(
                        f"テーブル名を変換しました: {table_name_orig} → {table_name}")

                # 主キー設定オプションを確認
                finalize_structure = finalize_structure_var.get()

                # データベース接続を確立
                with sqlite3.connect(db_path.get()) as conn:
                    success, err = manager.bulk_insert_from_file(
                        conn=conn,  # 接続オブジェクトを渡す
                        file_path=file_path,
                        table_name=table_name,
                        encoding=config['encoding'],
                        quoting=config['quoting']
                    )

                    if success and finalize_structure:
                        # 主キーとインデックスを設定
                        success2, err2 = manager.finalize_table_structure(
                            conn=conn,
                            table_name=table_name,
                            primary_key_columns=None,  # _rowid_を使用
                            index_columns=[]  # GUIではインデックスは空で
                        )
                        if not success2:
                            log_message(f"❌ 主キー設定失敗: {table_name}")
                            if err2:
                                log_message(f"  エラー内容: {err2}")

                if success:
                    log_message(f"✅ インポート成功: {file_name}")
                    if finalize_structure:
                        log_message(f"  🔑 主キー(_rowid_)を追加しました")
                else:
                    log_message(f"❌ インポート失敗: {file_name}")
                    if err:
                        log_message(f"  エラー内容: {err}")
            except Exception as e:
                log_message(f"❌ インポート中に予期せぬエラーが発生しました: {file_name}")
                log_message(f"  エラー内容: {e}")
                log_message(f"  トレースバック:\n{traceback.format_exc()}")
        update_table_view(tree, db_path.get())

    def reprocess_error_file():
        selected_item = error_tree.selection()
        if not selected_item:
            messagebox.showwarning("選択なし", "再処理するエラーファイルを選択してください。")
            return

        item_values = error_tree.item(selected_item[0], 'values')
        file_name = item_values[0]
        original_error = item_values[1]

        # GUIからエンコーディングとクォーティングを取得
        encoding = error_encoding_var.get()
        quoting = error_quoting_var.get()
        if quoting == 'None':
            quoting = None
        elif quoting == 'none':
            quoting = 'none'

        # ファイルパスを構築
        app_paths = Paths()
        raw_data_path = app_paths.RAW_DATA
        file_path = raw_data_path / file_name
        table_name_orig = Path(file_name).stem.lower()

        # テーブル名を適切に変換（日本語や特殊文字を避ける）
        table_name = sanitize_table_name(table_name_orig)

        # 元のテーブル名と変換後のテーブル名が異なる場合はログに記録
        if table_name != table_name_orig:
            log_message(f"テーブル名を変換しました: {table_name_orig} → {table_name}")

        if not file_path.exists():
            messagebox.showerror(
                "ファイルなし", f"ファイルが見つかりません: {file_path}\nraw_dataディレクトリのパスを確認してください。")
            return

        if SQLiteManager is None:
            messagebox.showerror("エラー", "SQLiteManagerのインポートに失敗しました。")
            return

        try:
            manager = SQLiteManager(db_path=db_path.get())
            log_message(
                f"--- 再処理開始: {file_name} → {table_name} (encoding={encoding}, quoting={quoting}) ---")

            # 主キー設定オプションを確認
            finalize_structure = finalize_structure_var.get()

            # データベース接続を確立
            with sqlite3.connect(db_path.get()) as conn:
                # ファイルをインポート
                success, err = manager.bulk_insert_from_file(
                    conn=conn,
                    file_path=file_path,
                    table_name=table_name,
                    encoding=encoding,
                    quoting=quoting
                )

                if success and finalize_structure:
                    # 主キーとインデックスを設定
                    success2, err2 = manager.finalize_table_structure(
                        conn=conn,
                        table_name=table_name,
                        primary_key_columns=None,  # _rowid_を使用
                        index_columns=[]  # GUIではインデックスは空で
                    )
                    if not success2:
                        log_message(f"❌ 主キー設定失敗: {table_name}")
                        if err2:
                            log_message(f"  エラー内容: {err2}")

            if success:
                log_message(f"✅ 再処理成功: {file_name}")
                if finalize_structure:
                    log_message(f"  🔑 主キー(_rowid_)を追加しました")
                # 成功したらエラーリストから削除
                error_tree.delete(selected_item)
                update_table_view(tree, db_path.get())
            else:
                log_message(f"❌ 再処理失敗: {file_name}")
                if err:
                    log_message(f"  エラー内容: {err}")
                # エラーメッセージを更新
                error_tree.item(selected_item[0], values=(file_name, err))
        except Exception as e:
            log_message(f"❌ 再処理中に予期せぬエラーが発生しました: {file_name}")
            log_message(f"  エラー内容: {e}")
            log_message(f"  トレースバック:\n{traceback.format_exc()}")

    def show_all_tables():
        """データベース内の全テーブル一覧を表示"""
        try:
            with sqlite3.connect(db_path.get()) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")
                tables = cursor.fetchall()

                if not tables:
                    log_message("📋 データベース内にテーブルがありません")
                    return

                log_message(f"📋 データベース内のテーブル一覧 ({len(tables)}件):")
                for i, table in enumerate(tables, 1):
                    table_name = table[0]
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM '{table_name}'")
                        row_count = cursor.fetchone()[0]
                        log_message(f"  {i}. {table_name} ({row_count:,} 行)")
                    except Exception as e:
                        log_message(f"  {i}. {table_name} (エラー: {e})")

        except Exception as e:
            log_message(f"❌ テーブル一覧取得中にエラーが発生しました: {e}")
            log_message(f"  トレースバック:\n{traceback.format_exc()}")

    def debug_table_selection():
        """選択されたテーブルの詳細情報をデバッグ表示"""
        selected = tree.selection()
        if not selected:
            log_message("⚠️ テーブルが選択されていません")
            return

        item_values = tree.item(selected[0], "values")
        log_message(f"🔍 選択されたアイテムの詳細:")
        log_message(f"  全値: {item_values}")
        log_message(f"  テーブル名: '{item_values[0]}'")
        log_message(f"  行数: {item_values[1]}")
        log_message(f"  カラム数: {item_values[2]}")
        log_message(f"  サイズ: {item_values[3]}")

        # テーブル名の処理
        table_name = item_values[0]
        cleaned_name = table_name.strip('"').strip("'")
        log_message(f"  クリーンアップ後のテーブル名: '{cleaned_name}'")

    def add_primary_key_to_selected_table():
        """選択されたテーブルに主キーを追加"""
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("選択なし", "主キーを追加するテーブルを選択してください。")
            return

        # テーブル名を取得（get_table_infoでクォートなしで返される）
        table_name = tree.item(selected[0], "values")[0]

        log_message(f"🔍 選択されたテーブル: '{table_name}'")

        try:
            manager = SQLiteManager(db_path=db_path.get())

            with sqlite3.connect(db_path.get()) as conn:
                cursor = conn.cursor()

                # テーブルの存在確認（クリーンアップした名前で確認）
                clean_table_name = table_name.strip('"').strip("'")
                # デバッグ: DB内の全テーブル名を出力
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
                all_tables = [row[0] for row in cursor.fetchall()]
                log_message(f"DB内テーブル一覧: {all_tables}")
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (clean_table_name,))
                table_exists = cursor.fetchone()

                if not table_exists:
                    log_message(f"❌ テーブル '{clean_table_name}' が存在しません")
                    return

                log_message(f"✅ テーブル '{clean_table_name}' を確認しました")

                # 現在のテーブル構造を確認
                clean_table_name = table_name.strip('"').strip("'")
                safe_table_name = clean_table_name.replace('"', '""')
                cursor.execute(f'PRAGMA table_info("{safe_table_name}")')
                columns = cursor.fetchall()
                log_message(f"📋 現在のカラム数: {len(columns)}")

                # 主キーが既に存在するかチェック
                has_primary_key = any(col[5] for col in columns)  # pkフラグをチェック
                if has_primary_key:
                    log_message(f"⚠️ テーブル '{table_name}' には既に主キーが設定されています")
                    return

                # 主キー追加（テーブル名はクォート付きで渡す）
                success, error = manager.finalize_table_structure(
                    conn, clean_table_name, None, [])
                if success:
                    log_message(f"✅ テーブル '{table_name}' に主キー(_rowid_)を追加しました")
                    update_table_view(tree, db_path.get())
                else:
                    log_message(f"❌ 主キー追加失敗: {table_name} - {error}")

        except Exception as e:
            log_message(f"❌ 主キー追加中にエラーが発生しました: {e}")
            log_message(f"  トレースバック:\n{traceback.format_exc()}")

    def show_table_structure():
        """選択されたテーブルの構造を表示"""
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("選択なし", "構造を確認するテーブルを選択してください。")
            return

        # テーブル名を取得（get_table_infoでクォートなしで返される）
        table_name = tree.item(selected[0], "values")[0]

        log_message(f"🔍 構造確認対象テーブル: '{table_name}'")

        try:
            with sqlite3.connect(db_path.get()) as conn:
                cursor = conn.cursor()

                # テーブルの存在確認（クリーンアップした名前で確認）
                clean_table_name = table_name.strip('"').strip("'")
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (clean_table_name,))
                table_exists = cursor.fetchone()

                if not table_exists:
                    log_message(f"❌ テーブル '{clean_table_name}' が存在しません")
                    return

                log_message(f"✅ テーブル '{clean_table_name}' を確認しました")

                # テーブル構造を取得
                safe_table_name = clean_table_name.replace('"', '""')
                cursor.execute(f'PRAGMA table_info("{safe_table_name}")')
                columns = cursor.fetchall()

                # インデックス情報も取得
                cursor.execute(
                    f"SELECT name FROM sqlite_master WHERE type='index' AND tbl_name=?", (clean_table_name,))
                indexes = cursor.fetchall()

                structure_info = f"=== テーブル構造: {table_name} ===\n"
                structure_info += f"カラム数: {len(columns)}\n\n"

                for col in columns:
                    col_id, name, dtype, not_null, default_val, pk = col
                    pk_info = " (PRIMARY KEY)" if pk else ""
                    structure_info += f"{name}: {dtype}{pk_info}\n"

                if indexes:
                    structure_info += f"\nインデックス:\n"
                    for idx in indexes:
                        structure_info += f"  - {idx[0]}\n"
                else:
                    structure_info += f"\nインデックス: なし\n"

                # データ件数も表示
                cursor.execute(f'SELECT COUNT(*) FROM "{safe_table_name}"')
                row_count = cursor.fetchone()[0]
                structure_info += f"\nデータ件数: {row_count:,} 件\n"

                # 新しいウィンドウで表示
                structure_window = tk.Toplevel()
                structure_window.title(f"テーブル構造: {table_name}")
                structure_window.geometry("600x400")

                text_widget = tk.Text(structure_window, wrap=tk.WORD)
                text_widget.pack(fill="both", expand=True, padx=10, pady=10)
                text_widget.insert("1.0", structure_info)
                text_widget.config(state=tk.DISABLED)

                log_message(f"✅ テーブル構造を表示しました: {table_name}")

        except Exception as e:
            log_message(f"❌ テーブル構造取得中にエラーが発生しました: {e}")
            log_message(f"  トレースバック:\n{traceback.format_exc()}")

    root = tk.Tk()
    root.title("SQLite検証GUIツール")
    root.geometry("1000x700")  # ウィンドウサイズを拡大
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
            # get_table_infoでクォートなしで返されるので、そのまま使用
            delete_selected_table(db_path.get(), table_name, log_message)
            update_table_view(tree, db_path.get())
            # 選択状態をクリア
            tree.selection_clear()
            # 削除後に本当に消えたか確認
            tables = [row[0] for row in get_table_info(db_path.get())]
            if table_name in tables:
                log_message(f"⚠️ テーブル {table_name} はまだ存在しています（削除失敗またはロック中）")
            else:
                log_message(f"✅ テーブル {table_name} の削除を確認しました")

    def copy_row():
        copy_selected_row(tree)

    # Notebook (タブ) の作成
    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True, padx=10, pady=5)

    # テーブル管理タブ
    tab_table_management = ttk.Frame(notebook)
    notebook.add(tab_table_management, text="テーブル管理")

    # エラー再処理タブ
    tab_error_reprocessing = ttk.Frame(notebook)
    notebook.add(tab_error_reprocessing, text="エラー再処理")

    # --- テーブル管理タブのUI ---
    frame_top = tk.Frame(tab_table_management)
    frame_top.pack(fill="x", padx=10, pady=5)

    tk.Label(frame_top, text="DB Path:").pack(side="left")
    tk.Entry(frame_top, textvariable=db_path,
             width=60).pack(side="left", padx=5)
    tk.Button(frame_top, text="Browse", command=browse_db).pack(side="left")

    # 主キー設定オプション
    frame_options = tk.Frame(tab_table_management)
    frame_options.pack(fill="x", padx=10, pady=2)
    finalize_structure_var = tk.BooleanVar(value=False)
    tk.Checkbutton(frame_options, text="主キー(_rowid_)を追加",
                   variable=finalize_structure_var).pack(side="left", padx=5)

    frame_tree = tk.Frame(tab_table_management)
    frame_tree.pack(fill="both", expand=True, padx=10, pady=5)

    tree = ttk.Treeview(frame_tree, columns=(
        "Table", "Rows", "Columns", "Size"), show="headings")
    for col in ("Table", "Rows", "Columns", "Size"):
        tree.heading(col, text=col)
        tree.column(col, width=150)
    tree.pack(side="left", fill="both", expand=True)

    tree_scroll = ttk.Scrollbar(
        frame_tree, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=tree_scroll.set)
    tree_scroll.pack(side="right", fill="y")

    frame_buttons1 = tk.Frame(tab_table_management)
    frame_buttons1.pack(fill="x", padx=10, pady=2)
    frame_buttons2 = tk.Frame(tab_table_management)
    frame_buttons2.pack(fill="x", padx=10, pady=2)
    frame_buttons3 = tk.Frame(tab_table_management)
    frame_buttons3.pack(fill="x", padx=10, pady=2)

    tk.Button(frame_buttons1, text="ファイルからテーブル作成",
              command=import_files_to_db).pack(side="left", padx=5)
    tk.Button(frame_buttons1, text="Delete All Tables", command=lambda: [delete_all_tables(
        db_path.get(), log_message), update_table_view(tree, db_path.get())]).pack(side="left", padx=5)
    tk.Button(frame_buttons1, text="Delete Selected Table",
              command=delete_selected).pack(side="left", padx=5)
    tk.Button(frame_buttons1, text="Run VACUUM", command=lambda: run_vacuum(
        db_path.get(), log_message)).pack(side="left", padx=5)
    tk.Button(frame_buttons1, text="Force VACUUM", command=lambda: run_vacuum_with_force(
        db_path.get(), log_message)).pack(side="left", padx=5)

    tk.Button(frame_buttons2, text="External VACUUM", command=lambda: run_vacuum_external(
        db_path.get(), log_message)).pack(side="left", padx=5)
    tk.Button(frame_buttons2, text="Copy Selected Row",
              command=copy_row).pack(side="left", padx=5)
    tk.Button(frame_buttons2, text="Refresh", command=lambda: update_table_view(
        tree, db_path.get())).pack(side="left", padx=5)
    tk.Button(frame_buttons2, text="Export CSV",
              command=lambda: export_csv(tree)).pack(side="left", padx=5)

    # 新しいボタン: 主キー追加とテーブル構造表示
    tk.Button(frame_buttons3, text="選択テーブルに主キー追加",
              command=add_primary_key_to_selected_table).pack(side="left", padx=5)
    tk.Button(frame_buttons3, text="テーブル構造表示",
              command=show_table_structure).pack(side="left", padx=5)
    tk.Button(frame_buttons3, text="全テーブル一覧表示",
              command=show_all_tables).pack(side="left", padx=5)
    tk.Button(frame_buttons3, text="デバッグ: 選択テーブル詳細",
              command=debug_table_selection).pack(side="left", padx=5)

    # --- エラー再処理タブのUI ---
    frame_error_controls = tk.Frame(tab_error_reprocessing)
    frame_error_controls.pack(fill="x", padx=10, pady=5)

    tk.Label(frame_error_controls, text="エンコーディング:").pack(side="left")
    error_encoding_var = tk.StringVar(value="auto")
    ttk.Combobox(frame_error_controls, textvariable=error_encoding_var,
                 values=["auto", "utf-8", "shift_jis", "cp932"]).pack(side="left", padx=5)

    tk.Label(frame_error_controls, text="クォーティング:").pack(
        side="left", padx=(10, 0))
    error_quoting_var = tk.StringVar(value="None")
    ttk.Combobox(frame_error_controls, textvariable=error_quoting_var,
                 values=["None", "0", "1", "2", "none"]).pack(side="left", padx=5)  # 0,1,2はcsv.QUOTE_*

    tk.Button(frame_error_controls, text="エラーログを再読み込み", command=lambda: load_and_display_errors(
        error_tree, log_message)).pack(side="left", padx=10)
    tk.Button(frame_error_controls, text="選択したエラーを再処理",
              command=reprocess_error_file).pack(side="left", padx=5)

    frame_error_tree = tk.Frame(tab_error_reprocessing)
    frame_error_tree.pack(fill="both", expand=True, padx=10, pady=5)

    error_tree = ttk.Treeview(frame_error_tree, columns=(
        "File", "Error"), show="headings")
    error_tree.heading("File", text="ファイル名")
    error_tree.heading("Error", text="エラー内容")
    error_tree.column("File", width=200)
    error_tree.column("Error", width=600)
    error_tree.pack(side="left", fill="both", expand=True)

    error_tree_scroll = ttk.Scrollbar(
        frame_error_tree, orient="vertical", command=error_tree.yview)
    error_tree.configure(yscrollcommand=error_tree_scroll.set)
    error_tree_scroll.pack(side="right", fill="y")

    # ログ表示エリア
    frame_log = tk.Frame(root)
    frame_log.pack(fill="both", expand=True, padx=10, pady=5)

    log_text = tk.Text(frame_log, wrap=tk.WORD, height=10)
    log_text.pack(side="left", fill="both", expand=True)

    log_scroll = ttk.Scrollbar(
        frame_log, orient="vertical", command=log_text.yview)
    log_text.configure(yscrollcommand=log_scroll.set)
    log_scroll.pack(side="right", fill="y")

    # 初期化
    if db_path.get():
        update_table_view(tree, db_path.get())
        log_message(f"データベースを読み込みました: {db_path.get()}")
    else:
        log_message("データベースを選択してください。")

    # エラーログの初期読み込み
    load_and_display_errors(error_tree, log_message)

    return root


if __name__ == "__main__":
    root = create_gui()
    root.mainloop()
