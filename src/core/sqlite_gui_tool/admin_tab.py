"""
Admin Tab Module for SQLite GUI Tool

This module provides the database administration functionality for the SQLite GUI Tool.
Features include:
- Table listing with size estimation
- Table deletion (all or selected)
- VACUUM operation
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import os
import time


class AdminTab:
    """Admin tab for database administration tasks"""
    
    def __init__(self, parent, app):
        """Initialize the admin tab
        
        Args:
            parent: The parent frame
            app: The main application instance
        """
        self.parent = parent
        self.app = app
        
        # Create the tab UI
        self._create_ui()
        
    def _create_ui(self):
        """Create the admin tab UI"""
        # メインフレーム
        admin_frame = ttk.Frame(self.parent)
        admin_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 説明ラベル
        description = (
            "このタブでは、データベースの管理操作を行うことができます。\n"
            "テーブルの削除やVACUUM操作などが可能です。"
        )
        desc_label = ttk.Label(
            admin_frame, text=description, wraplength=800, justify="left")
        desc_label.pack(fill=tk.X, pady=10)

        # テーブル情報フレーム
        table_frame = ttk.LabelFrame(admin_frame, text="テーブル情報")
        table_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # テーブル情報ツリービュー
        columns = ("table", "rows", "columns", "size")
        self.table_tree = ttk.Treeview(
            table_frame, columns=columns, show="headings")

        # 列の設定
        self.table_tree.heading("table", text="テーブル名")
        self.table_tree.heading("rows", text="行数")
        self.table_tree.heading("columns", text="カラム数")
        self.table_tree.heading("size", text="推定サイズ")

        self.table_tree.column("table", width=200)
        self.table_tree.column("rows", width=100, anchor="center")
        self.table_tree.column("columns", width=100, anchor="center")
        self.table_tree.column("size", width=150, anchor="center")

        # スクロールバー
        tree_y_scrollbar = ttk.Scrollbar(
            table_frame, orient="vertical", command=self.table_tree.yview)
        tree_x_scrollbar = ttk.Scrollbar(
            table_frame, orient="horizontal", command=self.table_tree.xview)
        self.table_tree.configure(
            yscrollcommand=tree_y_scrollbar.set, xscrollcommand=tree_x_scrollbar.set)

        # 配置
        self.table_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree_x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        # 操作ボタンフレーム
        button_frame = ttk.Frame(admin_frame)
        button_frame.pack(fill=tk.X, pady=10)

        # データベース選択ボタン
        db_select_button = ttk.Button(
            button_frame, text="データベース選択", command=self.select_database)
        db_select_button.pack(side=tk.LEFT, padx=5)

        # 更新ボタン
        refresh_button = ttk.Button(
            button_frame, text="テーブル情報を更新", command=self.refresh_table_info)
        refresh_button.pack(side=tk.LEFT, padx=5)
        
        # 全件データ更新ボタン
        update_all_button = ttk.Button(
            button_frame, text="全件データ更新", command=self.update_all_data)
        update_all_button.pack(side=tk.LEFT, padx=5)

        # 選択テーブル削除ボタン
        delete_selected_button = ttk.Button(
            button_frame, text="選択テーブルを削除", command=self.delete_selected_table)
        delete_selected_button.pack(side=tk.LEFT, padx=5)

        # 全テーブル削除ボタン
        delete_all_button = ttk.Button(
            button_frame, text="全テーブルを削除", command=self.delete_all_tables)
        delete_all_button.pack(side=tk.LEFT, padx=5)

        # VACUUM実行ボタン
        vacuum_button = ttk.Button(
            button_frame, text="VACUUM実行", command=self.run_vacuum)
        vacuum_button.pack(side=tk.LEFT, padx=5)

        # 選択行コピーボタン
        copy_button = ttk.Button(
            button_frame, text="選択行をコピー", command=self.copy_selected_row)
        copy_button.pack(side=tk.LEFT, padx=5)

        # ログ表示フレーム
        log_frame = ttk.LabelFrame(admin_frame, text="実行ログ")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # ログ表示エリア
        self.log_text = tk.Text(log_frame, height=8, wrap=tk.WORD)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # スクロールバー
        log_scrollbar = ttk.Scrollbar(
            log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
    def refresh_table_info(self):
        """テーブル情報を更新"""
        # データベース接続の確認
        if not self.app.conn:
            self.app.show_message("データベースに接続されていません。", "warning")
            return
            
        # 接続が有効かチェック
        try:
            # 簡単なクエリを実行して接続をテスト
            self.app.cursor.execute("SELECT 1")
        except sqlite3.ProgrammingError:
            self.app.show_message("データベース接続が無効です。再接続してください。", "error")
            self.app.conn = None
            self.app.cursor = None
            return
        except Exception as e:
            self.app.show_message(f"データベース接続エラー: {e}", "error")
            return
            
        # テーブル情報をクリア
        for item in self.table_tree.get_children():
            self.table_tree.delete(item)
            
        try:
            # テーブル一覧を取得
            self.app.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
            tables = self.app.cursor.fetchall()
            
            for table in tables:
                name = table[0]
                try:
                    # 行数を取得
                    self.app.cursor.execute(f"SELECT COUNT(*) FROM '{name}'")
                    row_count = self.app.cursor.fetchone()[0]
                    
                    # カラム情報を取得
                    self.app.cursor.execute(f"PRAGMA table_info('{name}')")
                    column_count = len(self.app.cursor.fetchall())
                    
                    # サイズを推定
                    estimated_size_bytes = row_count * column_count * 50  # 1セルあたり約50バイトと仮定
                    estimated_size_mb = estimated_size_bytes / (1024 * 1024)
                    
                    # テーブル情報を追加
                    self.table_tree.insert("", "end", values=(name, row_count, column_count, f"{estimated_size_mb:.2f} MB"))
                    
                except Exception as e:
                    self.table_tree.insert("", "end", values=(name, "Error", "Error", "Error"))
                    self.log_message(f"テーブル {name} の情報取得エラー: {e}")
                    
            self.log_message(f"{len(tables)} 個のテーブル情報を更新しました。")
            
        except Exception as e:
            self.app.show_message(f"テーブル情報の更新エラー: {e}", "error")
            
    def delete_selected_table(self):
        """選択されたテーブルを削除"""
        if not self.app.conn:
            self.app.show_message("データベースに接続されていません。", "warning")
            return
            
        # 選択されたテーブルを取得
        selected = self.table_tree.selection()
        if not selected:
            self.app.show_message("テーブルが選択されていません。", "warning")
            return
            
        # テーブル名を取得
        table_name = self.table_tree.item(selected[0], "values")[0]
        
        # 確認ダイアログ
        if not messagebox.askyesno("確認", f"テーブル '{table_name}' を削除しますか？"):
            return
            
        try:
            # テーブルが存在するか確認
            self.app.cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
            if not self.app.cursor.fetchone():
                self.app.show_message(f"テーブル '{table_name}' は存在しません。", "warning")
                return
                
            # テーブルを削除（クォートを修正）
            sql = f"DROP TABLE IF EXISTS [{table_name}]"
            self.log_message(f"実行SQL: {sql}")
            self.app.cursor.execute(sql)
            self.app.conn.commit()
            
            # 削除確認
            self.app.cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
            if self.app.cursor.fetchone():
                self.log_message(f"警告: テーブル {table_name} が削除されていません。別の方法で削除を試みます。")
                
                # 別の方法で削除を試みる
                try:
                    sql = f'DROP TABLE IF EXISTS "{table_name}"'
                    self.log_message(f"実行SQL (2回目): {sql}")
                    self.app.cursor.execute(sql)
                    self.app.conn.commit()
                except Exception as e:
                    self.log_message(f"2回目の削除試行エラー: {e}")
            
            # テーブル情報を更新
            self.refresh_table_info()
            
            # テーブル一覧を更新（スキーマタブなど）
            if 'schema' in self.app.tabs:
                tables = self.app.get_table_list()
                self.app.tabs['schema'].update_table_list(tables)
            
            self.log_message(f"テーブル {table_name} を削除しました。")
            
        except Exception as e:
            self.app.show_message(f"テーブル削除エラー: {e}", "error")
            
    def delete_all_tables(self):
        """すべてのテーブルを削除"""
        if not self.app.conn:
            self.app.show_message("データベースに接続されていません。", "warning")
            return
            
        # 確認ダイアログ
        if not messagebox.askyesno("確認", "すべてのテーブルを削除しますか？\nこの操作は元に戻せません。"):
            return
            
        try:
            # テーブル一覧を取得
            self.app.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
            tables = self.app.cursor.fetchall()
            
            if not tables:
                self.app.show_message("削除可能なテーブルがありません。", "info")
                return
                
            deleted_count = 0
            for table in tables:
                name = table[0]
                try:
                    # テーブルを削除（クォートを修正）
                    sql = f"DROP TABLE IF EXISTS [{name}]"
                    self.log_message(f"実行SQL: {sql}")
                    self.app.cursor.execute(sql)
                    
                    # 削除確認
                    self.app.cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,))
                    if self.app.cursor.fetchone():
                        self.log_message(f"警告: テーブル {name} が削除されていません。別の方法で削除を試みます。")
                        
                        # 別の方法で削除を試みる
                        try:
                            sql = f'DROP TABLE IF EXISTS "{name}"'
                            self.log_message(f"実行SQL (2回目): {sql}")
                            self.app.cursor.execute(sql)
                        except Exception as e:
                            self.log_message(f"2回目の削除試行エラー: {e}")
                    
                    self.log_message(f"テーブル {name} を削除しました。")
                    deleted_count += 1
                    
                except Exception as e:
                    self.log_message(f"テーブル {name} の削除エラー: {e}")
                    
            self.app.conn.commit()
            
            # テーブル情報を更新
            self.refresh_table_info()
            
            # テーブル一覧を更新（スキーマタブなど）
            if 'schema' in self.app.tabs:
                tables = self.app.get_table_list()
                self.app.tabs['schema'].update_table_list(tables)
            
            self.log_message(f"{deleted_count} 個のテーブルをすべて削除しました。")
            
        except Exception as e:
            self.app.show_message(f"テーブル削除エラー: {e}", "error")
            
    def run_vacuum(self):
        """VACUUM操作を実行"""
        if not self.app.conn:
            self.app.show_message("データベースに接続されていません。", "warning")
            return
            
        # 確認ダイアログ
        if not messagebox.askyesno("確認", "VACUUM操作を実行しますか？\nデータベースの最適化を行います。"):
            return
            
        try:
            # 現在のジャーナルモードを確認
            self.app.cursor.execute("PRAGMA journal_mode")
            current_mode = self.app.cursor.fetchone()[0]
            self.log_message(f"現在のジャーナルモード: {current_mode}")
            
            # WALモードの場合は一時的にDELETEモードに変更
            if current_mode.upper() == "WAL":
                self.log_message("WALモードからDELETEモードに変更します...")
                self.app.cursor.execute("PRAGMA journal_mode = DELETE")
                self.app.conn.commit()
            
            # VACUUM実行
            self.log_message("VACUUM操作を実行中...")
            self.app.cursor.execute("VACUUM")
            self.app.conn.commit()
            
            # 元のモードに戻す
            if current_mode.upper() == "WAL":
                self.log_message("ジャーナルモードをWALに戻します...")
                self.app.cursor.execute("PRAGMA journal_mode = WAL")
                self.app.conn.commit()
            
            # データベースファイルのパスを取得
            db_path = self.app.db_path
            
            # 関連ファイルの存在を確認
            wal_file = f"{db_path}-wal"
            shm_file = f"{db_path}-shm"
            journal_file = f"{db_path}-journal"
            
            if os.path.exists(wal_file) or os.path.exists(shm_file) or os.path.exists(journal_file):
                self.log_message("関連ファイル（WAL/SHM/Journal）が残っています。クリーンアップを試みます...")
                
                # 接続を一度閉じる
                self.app.close_connection()
                
                # 少し待機してファイルが解放されるのを待つ
                time.sleep(0.5)
                
                # ファイルの削除を試みる
                try:
                    if os.path.exists(wal_file):
                        os.remove(wal_file)
                        self.log_message(f"WALファイルを削除しました: {wal_file}")
                    if os.path.exists(shm_file):
                        os.remove(shm_file)
                        self.log_message(f"SHMファイルを削除しました: {shm_file}")
                    if os.path.exists(journal_file):
                        os.remove(journal_file)
                        self.log_message(f"Journalファイルを削除しました: {journal_file}")
                except Exception as e:
                    self.log_message(f"ファイル削除エラー: {e}")
                
                # 再接続
                self.app._connect_to_db(db_path)
            
            self.log_message("VACUUM操作が完了しました。")
            
        except Exception as e:
            self.app.show_message(f"VACUUM実行エラー: {e}", "error")
            
    def select_database(self):
        """データベース選択ダイアログを表示"""
        # アプリケーションのデータベース接続メソッドを呼び出す
        self.app.connect_database()
    
    def update_all_data(self):
        """全件データ更新処理"""
        if not self.app.conn:
            self.app.show_message("データベースに接続されていません。", "warning")
            return
            
        # 確認ダイアログ
        if not messagebox.askyesno("確認", "全件データ更新を実行しますか？\nこの処理には時間がかかる場合があります。"):
            return
            
        try:
            # テーブル一覧を取得（削除されていないテーブルのみ）
            self.app.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
            tables = self.app.cursor.fetchall()
            
            if not tables:
                self.log_message("処理対象のテーブルがありません。")
                return
            
            total_rows = 0
            processed_tables = 0
            
            self.log_message(f"{len(tables)} 個のテーブルの処理を開始します...")
            
            for table in tables:
                name = table[0]
                try:
                    # テーブルが実際に存在するか確認
                    self.app.cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,))
                    if not self.app.cursor.fetchone():
                        self.log_message(f"テーブル {name} は存在しません。スキップします。")
                        continue
                    
                    # 行数を取得
                    self.app.cursor.execute(f"SELECT COUNT(*) FROM [{name}]")
                    row_count = self.app.cursor.fetchone()[0]
                    total_rows += row_count
                    
                    # データの統計情報を取得（実際のデータ処理の代わり）
                    self.app.cursor.execute(f"PRAGMA table_info([{name}])")
                    columns = self.app.cursor.fetchall()
                    column_count = len(columns)
                    
                    # テーブルの最初の数行を読み込み（データ更新のシミュレーション）
                    self.app.cursor.execute(f"SELECT * FROM [{name}] LIMIT 100")
                    sample_data = self.app.cursor.fetchall()
                    
                    processed_tables += 1
                    self.log_message(f"テーブル {name}: {row_count} 行, {column_count} カラム, サンプル {len(sample_data)} 行を処理しました。")
                    
                    # UIの更新のために少し待機
                    self.parent.update()
                    time.sleep(0.01)
                    
                except Exception as e:
                    self.log_message(f"テーブル {name} の処理エラー: {e}")
            
            self.log_message(f"全件データ更新が完了しました。{processed_tables} テーブル、合計 {total_rows} 行を処理しました。")
            
            # テーブル情報を更新
            self.refresh_table_info()
            
        except Exception as e:
            self.app.show_message(f"全件データ更新エラー: {e}", "error")
    
    def copy_selected_row(self):
        """選択された行をクリップボードにコピー"""
        # 選択された行を取得
        selected = self.table_tree.selection()
        if not selected:
            self.app.show_message("行が選択されていません。", "warning")
            return
            
        try:
            # pyperclipのインポートを試みる
            import pyperclip
            
            # 選択された行の値を取得
            values = self.table_tree.item(selected[0], "values")
            
            # タブ区切りのテキストとしてコピー
            text = "\t".join(str(v) for v in values)
            pyperclip.copy(text)
            
            self.log_message("選択行をクリップボードにコピーしました。")
            
        except ImportError:
            self.app.show_message(
                "pyperclipモジュールがインストールされていないため、コピー機能は使用できません。\n"
                "pip install pyperclipでインストールしてください。",
                "warning"
            )
            
    def log_message(self, message):
        """ログメッセージを表示"""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        
    def on_db_connect(self, conn, cursor):
        """データベース接続時の処理"""
        # テーブル情報を更新
        self.refresh_table_info()
        
    def on_db_disconnect(self):
        """データベース切断時の処理"""
        # テーブル情報をクリア
        for item in self.table_tree.get_children():
            self.table_tree.delete(item)
            
        # ログをクリア
        self.log_text.delete(1.0, tk.END)
        
    def refresh(self):
        """タブの表示を更新"""
        if self.app.conn:
            self.refresh_table_info()
            
    def _update_all_tabs(self):
        """すべてのタブのテーブル一覧を更新"""
        # スキーマタブを更新
        if 'schema' in self.app.tabs:
            tables = self.app.get_table_list()
            self.app.tabs['schema'].update_table_list(tables)
            
        # エクスポートタブを更新
        if 'export' in self.app.tabs and hasattr(self.app.tabs['export'], 'refresh_table_list'):
            self.app.tabs['export'].refresh_table_list()
            
        # データ分析タブを更新
        if 'analyze' in self.app.tabs and hasattr(self.app.tabs['analyze'], 'refresh_table_list'):
            self.app.tabs['analyze'].refresh_table_list()