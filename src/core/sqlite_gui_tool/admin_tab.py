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
        
        # ファイル名とテーブル名のマッピングを保存
        self.file_table_mapping = {}
        
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
        columns = ("table", "source_file", "rows", "columns", "size")
        self.table_tree = ttk.Treeview(
            table_frame, columns=columns, show="headings")

        # 列の設定
        self.table_tree.heading("table", text="テーブル名")
        self.table_tree.heading("source_file", text="元ファイル名")
        self.table_tree.heading("rows", text="行数")
        self.table_tree.heading("columns", text="カラム数")
        self.table_tree.heading("size", text="推定サイズ")

        self.table_tree.column("table", width=180)
        self.table_tree.column("source_file", width=200)
        self.table_tree.column("rows", width=80, anchor="center")
        self.table_tree.column("columns", width=80, anchor="center")
        self.table_tree.column("size", width=120, anchor="center")

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
        
        # ZP138個別処理ボタン
        zp138_button = ttk.Button(
            button_frame, text="ZP138個別処理", command=self.process_zp138_individual)
        zp138_button.pack(side=tk.LEFT, padx=5)
        
        # データベース診断ボタン
        diagnose_button = ttk.Button(
            button_frame, text="DB診断", command=self.diagnose_database)
        diagnose_button.pack(side=tk.LEFT, padx=5)

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
            # デバッグ情報を追加
            self.log_message("テーブル情報の更新を開始...")
            
            # テーブル一覧を取得
            self.app.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
            tables = self.app.cursor.fetchall()
            
            self.log_message(f"検出されたテーブル数: {len(tables)}")
            
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
                    
                    # 元ファイル名を取得
                    source_file = self.file_table_mapping.get(name, "不明")
                    
                    # テーブル情報を追加
                    self.table_tree.insert("", "end", values=(name, source_file, row_count, column_count, f"{estimated_size_mb:.2f} MB"))
                    
                except Exception as e:
                    source_file = self.file_table_mapping.get(name, "不明")
                    self.table_tree.insert("", "end", values=(name, source_file, "Error", "Error", "Error"))
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
        """全件データ更新処理（洗い替え）"""
        if not self.app.conn:
            self.app.show_message("データベースに接続されていません。", "warning")
            return
            
        # 確認ダイアログ
        if not messagebox.askyesno("確認", 
            "全件データ更新（洗い替え）を実行しますか？\n"
            "・すべてのテーブルが削除されます\n"
            "・data/rawフォルダのファイルから再作成されます\n"
            "・この処理には時間がかかる場合があります"):
            return
            
        try:
            # SQLiteManagerが利用可能かチェック
            if not self.app.sqlite_manager:
                self.app.show_message("SQLiteManagerが利用できません。", "error")
                return
            
            self.log_message("=== 全件データ更新（洗い替え）開始 ===")
            
            # 1. 既存テーブルをすべて削除
            self.log_message("既存テーブルの削除を開始...")
            self.app.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
            existing_tables = self.app.cursor.fetchall()
            
            deleted_count = 0
            for table in existing_tables:
                name = table[0]
                try:
                    self.app.cursor.execute(f"DROP TABLE IF EXISTS [{name}]")
                    self.log_message(f"テーブル {name} を削除しました")
                    deleted_count += 1
                except Exception as e:
                    self.log_message(f"テーブル {name} の削除エラー: {e}")
            
            self.app.conn.commit()
            self.log_message(f"{deleted_count} 個のテーブルを削除しました")
            
            # 2. data/rawフォルダのファイルを処理
            import sys
            import os
            from pathlib import Path
            
            # プロジェクトルートを取得
            gui_tool_dir = Path(os.path.abspath(os.path.dirname(__file__)))
            project_root = gui_tool_dir.parents[2]  # src/core/sqlite_gui_tool の2つ上
            raw_data_dir = project_root / 'data' / 'raw'
            
            self.log_message(f"データフォルダ: {raw_data_dir}")
            
            if not raw_data_dir.exists():
                self.log_message(f"データフォルダが見つかりません: {raw_data_dir}")
                self.app.show_message(f"データフォルダが見つかりません: {raw_data_dir}", "error")
                return
            
            # サポートされるファイル拡張子
            supported_extensions = {'.csv', '.txt', '.tsv', '.xlsx', '.xls'}
            
            # ファイル一覧を取得
            data_files = []
            for ext in supported_extensions:
                data_files.extend(raw_data_dir.glob(f'*{ext}'))
            
            self.log_message(f"処理対象ファイル数: {len(data_files)}")
            
            if not data_files:
                self.log_message("処理対象のファイルが見つかりません")
                self.app.show_message("data/rawフォルダに処理対象のファイルが見つかりません", "warning")
                return
            
            # 3. 各ファイルを処理
            processed_files = 0
            total_rows = 0
            
            for file_path in data_files:
                try:
                    self.log_message(f"ファイル処理開始: {file_path.name}")
                    
                    # ZP138.txtの特殊処理
                    if file_path.name.upper() == 'ZP138.TXT':
                        success, table_name, row_count = self._process_zp138_file(file_path)
                    else:
                        # 通常ファイル処理
                        success, table_name, row_count = self._process_single_file(file_path)
                    
                    if success:
                        processed_files += 1
                        total_rows += row_count
                        # ファイル名とテーブル名のマッピングを保存
                        self.file_table_mapping[table_name] = file_path.name
                        self.log_message(f"ファイル処理完了: {file_path.name} → テーブル {table_name}: {row_count:,} 行")
                    else:
                        self.log_message(f"ファイル処理失敗: {file_path.name}")
                    
                    # UIの更新
                    self.parent.update()
                    
                except Exception as e:
                    self.log_message(f"ファイル {file_path.name} の処理エラー: {e}")
                    import traceback
                    self.log_message(traceback.format_exc())
            
            # 4. インデックスとキーの設定
            self.log_message("インデックスとキーの設定を開始...")
            try:
                if self.app.sqlite_manager and hasattr(self.app.sqlite_manager, 'finalize_database'):
                    self.app.sqlite_manager.finalize_database()
                    self.log_message("インデックスとキーの設定が完了しました")
                else:
                    self.log_message("SQLiteManagerが利用できないため、インデックス設定をスキップします")
            except Exception as e:
                self.log_message(f"インデックス設定エラー: {e}")
            
            # 5. 完了処理
            self.log_message(f"=== 全件データ更新完了 ===")
            self.log_message(f"処理ファイル数: {processed_files}/{len(data_files)}")
            self.log_message(f"総行数: {total_rows:,} 行")
            
            # テーブル情報を更新
            self.refresh_table_info()
            
            # 他のタブも更新
            self._update_all_tabs()
            
            self.app.show_message(
                f"全件データ更新が完了しました。\n"
                f"処理ファイル数: {processed_files}/{len(data_files)}\n"
                f"総行数: {total_rows:,} 行", 
                "info"
            )
            
        except Exception as e:
            self.log_message(f"全件データ更新エラー: {e}")
            self.app.show_message(f"全件データ更新エラー: {e}", "error")
            import traceback
            self.log_message(traceback.format_exc())
    
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
            
    def _process_single_file(self, file_path):
        """単一ファイルを処理してSQLiteに保存"""
        try:
            import pandas as pd
            import chardet
            import re
            
            # ファイル拡張子を取得
            ext = file_path.suffix.lower()
            
            # テーブル名を生成
            table_name = self._sanitize_table_name(file_path.stem)
            
            # ファイルタイプに応じて読み込み
            if ext in ['.csv', '.txt', '.tsv']:
                # エンコーディング検出
                with open(file_path, 'rb') as f:
                    raw_data = f.read(10000)  # 最初の10KBを読み込み
                    encoding_result = chardet.detect(raw_data)
                    encoding = encoding_result['encoding'] or 'utf-8'
                
                # 区切り文字を推定
                delimiter = ','
                if ext == '.tsv' or '\t' in file_path.name.lower():
                    delimiter = '\t'
                elif ext == '.txt':
                    # ファイルの最初の数行を読んで区切り文字を推定
                    try:
                        with open(file_path, 'r', encoding=encoding) as f:
                            first_line = f.readline()
                            if '\t' in first_line:
                                delimiter = '\t'
                            elif '|' in first_line:
                                delimiter = '|'
                            elif ';' in first_line:
                                delimiter = ';'
                    except:
                        pass
                
                # 特殊ファイル処理
                if file_path.name.lower() == 'zm37.txt':
                    # zm37.txtの特殊処理
                    try:
                        df = pd.read_csv(
                            file_path, 
                            encoding='cp932',
                            sep=delimiter,
                            quoting=3,  # QUOTE_NONE
                            engine='python',
                            on_bad_lines='skip',
                            dtype=str
                        )
                    except:
                        df = pd.read_csv(file_path, encoding=encoding, sep=delimiter, dtype=str)
                else:
                    # 通常のCSV/TXT処理
                    try:
                        # 最初は文字列として読み込み、後でデータ型を最適化
                        df = pd.read_csv(file_path, encoding=encoding, sep=delimiter, dtype=str)
                    except UnicodeDecodeError:
                        # UTF-8で失敗した場合はCP932を試す
                        df = pd.read_csv(file_path, encoding='cp932', sep=delimiter, dtype=str)
                        
            elif ext in ['.xlsx', '.xls']:
                # Excel処理
                if file_path.name.lower() == 'pp_summary_ztbp080_kojozisseki_d_0.xlsx':
                    # 特殊なExcelファイル（ヘッダーが7行）
                    df = pd.read_excel(file_path, header=7, dtype=str)
                else:
                    # 通常のExcelファイル
                    df = pd.read_excel(file_path, header=0, dtype=str)
            else:
                self.log_message(f"サポートされていないファイル形式: {ext}")
                return False, None, 0
            
            # データが空の場合
            if df is None or df.empty:
                self.log_message(f"ファイルが空またはデータがありません: {file_path.name}")
                return False, None, 0
            
            # データ型の最適化
            df = self._optimize_dataframe_dtypes(df)
            
            # SQLiteに保存
            df.to_sql(table_name, self.app.conn, if_exists='replace', index=False)
            self.app.conn.commit()
            
            return True, table_name, len(df)
            
        except Exception as e:
            self.log_message(f"ファイル処理エラー: {e}")
            import traceback
            self.log_message(traceback.format_exc())
            return False, None, 0
    
    def _sanitize_table_name(self, table_name):
        """テーブル名を適切に変換"""
        import re
        
        # 日本語文字を含むかチェック
        has_japanese = re.search(r'[ぁ-んァ-ン一-龥]', table_name)
        
        if has_japanese:
            # 日本語を含む場合はハッシュ値を使用
            sanitized = f"t_{hash(table_name) % 10000:04d}"
        else:
            # 英数字以外の文字を_に置換
            sanitized = re.sub(r'[^a-zA-Z0-9]', '_', table_name)
            sanitized = re.sub(r'_+', '_', sanitized)
            
            # 先頭が数字の場合、t_を付ける
            if sanitized and sanitized[0].isdigit():
                sanitized = f"t_{sanitized}"
                
            # 先頭と末尾の_を削除
            sanitized = sanitized.strip('_')
            
        return sanitized
    
    def _optimize_dataframe_dtypes(self, df):
        """DataFrameのデータ型を最適化"""
        import pandas as pd
        import numpy as np
        
        self.log_message(f"データ型最適化開始: {len(df.columns)} カラム")
        
        # 日付列の名前パターン
        date_column_patterns = [
            'date', '日付', 'day', '年月日', '登録日', '有効開始日', '有効終了日', 
            '作成日', '更新日', '開始日', '終了日', '期限', '期日', '計画日', '実績日'
        ]
        
        # 数値列の名前パターン
        numeric_column_patterns = [
            '数量', '金額', '単価', '価格', '重量', '長さ', '幅', '高さ', '面積', '体積',
            '率', 'パーセント', '割合', '係数', 'レート', '倍率', '指数'
        ]
        
        # コード列の名前パターン
        code_column_patterns = [
            'code', 'コード', 'cd', 'id', '番号', '品目', '部品', '製品', 'no', 'num'
        ]
        
        for col in df.columns:
            col_lower = str(col).lower()
            
            # 空の列はスキップ
            if df[col].empty:
                continue
            
            # サンプルデータを取得（最大1000行）
            sample = df[col].dropna().head(1000)
            if len(sample) == 0:
                continue
            
            # 日付列の処理
            is_date_column = any(pattern in col_lower for pattern in date_column_patterns)
            
            if is_date_column:
                self.log_message(f"日付列として処理: {col}")
                try:
                    # 8桁数値形式（YYYYMMDD）をチェック
                    if all(isinstance(x, str) and len(x) == 8 and x.isdigit() for x in sample.head(10) if pd.notna(x)):
                        # 8桁数値形式として処理
                        df[col] = pd.to_datetime(df[col], format='%Y%m%d', errors='coerce')
                        
                        # 特殊な値（99991231など）を処理
                        special_mask = df[col].isna() & df[col].astype(str).str.contains('9999', na=False)
                        if special_mask.any():
                            df.loc[special_mask, col] = pd.Timestamp.max
                    else:
                        # 標準的な日付形式で変換
                        df[col] = pd.to_datetime(df[col], errors='coerce')
                except Exception as e:
                    self.log_message(f"日付変換エラー {col}: {e}")
                    pass
            
            # 数値列の処理
            elif any(pattern in col_lower for pattern in numeric_column_patterns):
                self.log_message(f"数値列として処理: {col}")
                try:
                    # 数値変換を試行
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                except Exception as e:
                    self.log_message(f"数値変換エラー {col}: {e}")
                    pass
            
            # コード列の処理
            elif any(pattern in col_lower for pattern in code_column_patterns):
                self.log_message(f"コード列として処理: {col}")
                # コード列は文字列として保持
                df[col] = df[col].astype(str)
            
            # その他の列の自動判定
            else:
                # 数値として解釈できるかチェック
                try:
                    # サンプルの90%以上が数値として変換可能な場合
                    numeric_sample = pd.to_numeric(sample, errors='coerce')
                    valid_numeric_ratio = (~numeric_sample.isna()).mean()
                    
                    if valid_numeric_ratio >= 0.9:
                        self.log_message(f"自動判定で数値列: {col} (有効率: {valid_numeric_ratio:.2f})")
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                        continue
                except:
                    pass
                
                # 8桁数値（日付の可能性）をチェック
                try:
                    eight_digit_count = sum(1 for x in sample.head(100) 
                                          if isinstance(x, str) and len(x) == 8 and x.isdigit())
                    if eight_digit_count > len(sample) * 0.5:  # 50%以上が8桁数値
                        # 日付として解釈できるかテスト
                        test_dates = pd.to_datetime(sample.head(10), format='%Y%m%d', errors='coerce')
                        valid_dates_ratio = (~test_dates.isna()).mean()
                        
                        if valid_dates_ratio >= 0.7:  # 70%以上が有効な日付
                            self.log_message(f"自動判定で8桁日付列: {col} (有効率: {valid_dates_ratio:.2f})")
                            df[col] = pd.to_datetime(df[col], format='%Y%m%d', errors='coerce')
                            
                            # 特殊な値（99991231など）を処理
                            special_mask = df[col].isna() & df[col].astype(str).str.contains('9999', na=False)
                            if special_mask.any():
                                df.loc[special_mask, col] = pd.Timestamp.max
                            continue
                except:
                    pass
                
                # タイムスタンプ形式をチェック
                try:
                    timestamp_sample = pd.to_datetime(sample.head(10), errors='coerce')
                    valid_timestamp_ratio = (~timestamp_sample.isna()).mean()
                    
                    if valid_timestamp_ratio >= 0.7:  # 70%以上が有効なタイムスタンプ
                        self.log_message(f"自動判定でタイムスタンプ列: {col} (有効率: {valid_timestamp_ratio:.2f})")
                        df[col] = pd.to_datetime(df[col], errors='coerce')
                        continue
                except:
                    pass
                
                # デフォルトは文字列として保持
                self.log_message(f"文字列列として保持: {col}")
        
        self.log_message("データ型最適化完了")
        return df
    
    def _process_zp138_file(self, file_path):
        """ZP138.txtファイルの特殊処理（引当計算付き）"""
        try:
            import pandas as pd
            from decimal import Decimal, InvalidOperation, getcontext
            
            # 小数点以下の桁数を設定
            getcontext().prec = 10
            
            self.log_message(f"ZP138特殊処理開始: {file_path.name}")
            
            # ファイル読み込み
            df = pd.read_csv(file_path, delimiter='\t', encoding='cp932', header=0, dtype=str)
            
            # カラム名のマッピング
            column_mapping = {
                '連続行番号': '連続行番号',
                '品目': '品目',
                '名称': '名称',
                'MRP エリア': 'MRPエリア',
                'プラント': 'プラント',
                '所要日付': '所要日付',
                'MRP 要素': 'MRP要素',
                'MRP 要素データ': 'MRP要素データ',
                '再日程計画日付': '再日程計画日付',
                '例外Msg': '例外Msg',
                '入庫/所要量': '入庫_所要量',
                '利用可能数量': '利用可能数量',
                '保管場所': '保管場所',
                '入出庫予定': '入出庫予定',
                'Itm': 'Itm'
            }
            
            # カラム名を変更
            df = df.rename(columns=column_mapping)
            
            # 引当と過不足カラムを追加
            df['引当'] = None
            df['過不足'] = None
            
            # 日付列処理
            df['所要日付'] = pd.to_datetime(df['所要日付'], format='%Y%m%d', errors='coerce')
            df['再日程計画日付'] = pd.to_datetime(df['再日程計画日付'], format='%Y%m%d', errors='coerce')
            
            # 数値列処理
            df['入庫_所要量'] = df['入庫_所要量'].apply(self._safe_decimal_conversion)
            df['利用可能数量'] = df['利用可能数量'].apply(self._safe_decimal_conversion)
            
            # 引当計算
            self.log_message("引当計算処理開始...")
            df = self._calculate_zp138_inventory(df)
            self.log_message("引当計算処理完了")
            
            # テーブル名
            table_name = "t_zp138引当"
            
            # SQLiteに保存
            df.to_sql(table_name, self.app.conn, if_exists='replace', index=False)
            self.app.conn.commit()
            
            return True, table_name, len(df)
            
        except Exception as e:
            self.log_message(f"ZP138処理エラー: {e}")
            import traceback
            self.log_message(traceback.format_exc())
            return False, None, 0
    
    def _safe_decimal_conversion(self, value):
        """安全にDecimal型に変換する"""
        from decimal import Decimal, InvalidOperation
        
        # SAPの後ろマイナス表記を処理
        if isinstance(value, str) and value.endswith('-'):
            value = f"-{value[:-1]}"
        
        try:
            if value in [None, '', '']:
                return Decimal(0)
            return float(Decimal(str(value)).quantize(Decimal('0.001')))
        except (InvalidOperation, ValueError, TypeError):
            return 0.0
    
    def _calculate_zp138_inventory(self, df):
        """ZP138の引当計算を行う"""
        from decimal import Decimal
        
        df_result = df.copy()
        grouped = df_result.sort_values(by=['品目', '連続行番号']).groupby('品目')
        
        for item, group in grouped:
            actual_stock = Decimal(0).quantize(Decimal('0.001'))
            shortage = Decimal(0).quantize(Decimal('0.001'))
            
            for index, row in group.iterrows():
                row_quantity = Decimal(str(row['入庫_所要量'])).quantize(Decimal('0.001'))
                
                if row['MRP要素'] == '在庫':
                    actual_stock = row_quantity
                    shortage = Decimal(0)
                    allocation = Decimal(0)
                    excess_shortage = actual_stock
                    df_result.loc[index, '引当'] = float(allocation)
                    df_result.loc[index, '過不足'] = float(excess_shortage)
                elif row['MRP要素'] in ['外注依', '受注', '従所要', '入出予', '出荷']:
                    required_qty = abs(row_quantity)
                    
                    if actual_stock >= required_qty:
                        allocation = required_qty
                        actual_stock -= allocation
                    else:
                        allocation = actual_stock
                        shortage += (required_qty - actual_stock)
                        actual_stock = Decimal(0)
                    
                    excess_shortage = actual_stock - shortage
                    df_result.loc[index, '引当'] = float(allocation)
                    df_result.loc[index, '過不足'] = float(excess_shortage)
                else:
                    df_result.loc[index, '引当'] = 0.0
                    df_result.loc[index, '過不足'] = None
        
        return df_result
    
    def process_zp138_individual(self):
        """ZP138ファイルの個別処理"""
        if not self.app.conn:
            self.app.show_message("データベースに接続されていません。", "warning")
            return
            
        # 確認ダイアログ
        if not messagebox.askyesno("確認", "ZP138ファイルの個別処理を実行しますか？"):
            return
            
        try:
            # ZP138.txtファイルのパスを取得
            gui_tool_dir = Path(os.path.abspath(os.path.dirname(__file__)))
            project_root = gui_tool_dir.parents[2]
            zp138_file = project_root / 'data' / 'raw' / 'ZP138.txt'
            
            if not zp138_file.exists():
                self.app.show_message(f"ZP138.txtファイルが見つかりません: {zp138_file}", "error")
                return
            
            self.log_message("=== ZP138個別処理開始 ===")
            
            # ZP138処理を実行
            success, table_name, row_count = self._process_zp138_file(zp138_file)
            
            if success:
                # ファイル名とテーブル名のマッピングを保存
                self.file_table_mapping[table_name] = zp138_file.name
                
                self.log_message(f"ZP138処理完了: {table_name} ({row_count:,} 行)")
                
                # テーブル情報を更新
                self.refresh_table_info()
                
                # 他のタブも更新
                self._update_all_tabs()
                
                self.app.show_message(f"ZP138処理が完了しました。\nテーブル: {table_name}\n行数: {row_count:,} 行", "info")
            else:
                self.log_message("ZP138処理に失敗しました")
                self.app.show_message("ZP138処理に失敗しました。", "error")
                
        except Exception as e:
            self.log_message(f"ZP138個別処理エラー: {e}")
            self.app.show_message(f"ZP138個別処理エラー: {e}", "error")
            import traceback
            self.log_message(traceback.format_exc())

    def diagnose_database(self):
        """データベースの診断情報を表示"""
        if not self.app.conn:
            self.app.show_message("データベースに接続されていません。", "warning")
            return
            
        try:
            self.log_message("=== データベース診断開始 ===")
            
            # データベースファイル情報
            if self.app.db_path:
                self.log_message(f"データベースファイル: {self.app.db_path}")
                if os.path.exists(self.app.db_path):
                    file_size = os.path.getsize(self.app.db_path)
                    self.log_message(f"ファイルサイズ: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
                else:
                    self.log_message("警告: データベースファイルが見つかりません")
            
            # SQLiteバージョン
            self.app.cursor.execute("SELECT sqlite_version()")
            sqlite_version = self.app.cursor.fetchone()[0]
            self.log_message(f"SQLiteバージョン: {sqlite_version}")
            
            # ジャーナルモード
            self.app.cursor.execute("PRAGMA journal_mode")
            journal_mode = self.app.cursor.fetchone()[0]
            self.log_message(f"ジャーナルモード: {journal_mode}")
            
            # すべてのオブジェクトを表示
            self.app.cursor.execute("SELECT type, name FROM sqlite_master ORDER BY type, name")
            objects = self.app.cursor.fetchall()
            self.log_message(f"データベース内のオブジェクト数: {len(objects)}")
            
            object_counts = {}
            for obj_type, obj_name in objects:
                if obj_type not in object_counts:
                    object_counts[obj_type] = 0
                object_counts[obj_type] += 1
                self.log_message(f"  {obj_type}: {obj_name}")
            
            # オブジェクト種別の集計
            self.log_message("オブジェクト種別集計:")
            for obj_type, count in object_counts.items():
                self.log_message(f"  {obj_type}: {count}個")
            
            # テーブルの詳細情報
            self.app.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
            tables = self.app.cursor.fetchall()
            
            if tables:
                self.log_message(f"ユーザーテーブル数: {len(tables)}")
                total_rows = 0
                for table in tables:
                    table_name = table[0]
                    try:
                        self.app.cursor.execute(f"SELECT COUNT(*) FROM [{table_name}]")
                        row_count = self.app.cursor.fetchone()[0]
                        total_rows += row_count
                        self.log_message(f"  テーブル {table_name}: {row_count:,} 行")
                    except Exception as e:
                        self.log_message(f"  テーブル {table_name}: エラー - {e}")
                
                self.log_message(f"総行数: {total_rows:,} 行")
            else:
                self.log_message("ユーザーテーブルが見つかりません")
            
            self.log_message("=== データベース診断完了 ===")
            
        except Exception as e:
            self.log_message(f"診断エラー: {e}")
            self.app.show_message(f"データベース診断エラー: {e}", "error")