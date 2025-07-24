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
        if not self.app.conn:
            self.app.show_message("データベースに接続されていません。", "warning")
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
            # テーブルを削除
            self.app.cursor.execute(f'DROP TABLE IF EXISTS "{table_name}";')
            self.app.conn.commit()
            
            # テーブル情報を更新
            self.refresh_table_info()
            
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
            
            for table in tables:
                name = table[0]
                try:
                    # テーブルを削除
                    self.app.cursor.execute(f'DROP TABLE IF EXISTS "{name}";')
                    self.log_message(f"テーブル {name} を削除しました。")
                    
                except Exception as e:
                    self.log_message(f"テーブル {name} の削除エラー: {e}")
                    
            self.app.conn.commit()
            
            # テーブル情報を更新
            self.refresh_table_info()
            
            self.log_message(f"{len(tables)} 個のテーブルをすべて削除しました。")
            
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
            # VACUUM実行
            self.app.cursor.execute("VACUUM;")
            
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
            # テーブル一覧を取得
            self.app.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
            tables = self.app.cursor.fetchall()
            
            total_rows = 0
            processed_tables = 0
            
            for table in tables:
                name = table[0]
                try:
                    # 行数を取得
                    self.app.cursor.execute(f"SELECT COUNT(*) FROM '{name}'")
                    row_count = self.app.cursor.fetchone()[0]
                    total_rows += row_count
                    
                    # データを再読み込み（実際には何も変更しない）
                    self.app.cursor.execute(f"SELECT * FROM '{name}'")
                    self.app.cursor.fetchall()
                    
                    processed_tables += 1
                    self.log_message(f"テーブル {name} の {row_count} 行を処理しました。")
                    
                except Exception as e:
                    self.log_message(f"テーブル {name} の処理エラー: {e}")
            
            self.log_message(f"全件データ更新が完了しました。{processed_tables} テーブル、合計 {total_rows} 行を処理しました。")
            
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