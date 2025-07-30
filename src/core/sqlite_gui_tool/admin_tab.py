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

        # 1行目のボタン
        # 全件データ更新ボタン
        update_all_button = ttk.Button(
            button_frame, text="全件データ更新", command=self.update_all_data)
        update_all_button.pack(side=tk.LEFT, padx=5)

        # ZP138個別処理ボタン
        zp138_button = ttk.Button(
            button_frame, text="ZP138個別処理", command=self.process_zp138_individual)
        zp138_button.pack(side=tk.LEFT, padx=5)

        # MARADL処理ボタン
        maradl_button = ttk.Button(
            button_frame, text="MARADL処理", command=self.process_maradl_pipeline)
        maradl_button.pack(side=tk.LEFT, padx=5)

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

        # 2行目のボタンフレーム
        button_frame2 = ttk.Frame(admin_frame)
        button_frame2.pack(fill=tk.X, pady=5)

        # データ型分析ボタン
        type_analysis_button = ttk.Button(
            button_frame2, text="データ型分析", command=self.analyze_data_type_consistency)
        type_analysis_button.pack(side=tk.LEFT, padx=5)

        # データ型統一ボタン
        type_standardize_button = ttk.Button(
            button_frame2, text="データ型統一", command=self.standardize_data_types)
        type_standardize_button.pack(side=tk.LEFT, padx=5)

        # CSV出力ボタン（2行目に移動）
        csv_export_button = ttk.Button(
            button_frame2, text="CSV出力", command=self.export_table_info_csv)
        csv_export_button.pack(side=tk.LEFT, padx=5)

        # ログ表示フレーム
        log_frame = ttk.LabelFrame(admin_frame, text="実行ログ")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # ログ表示エリア
        self.log_text = tk.Text(log_frame, height=8, wrap=tk.WORD)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH,
                           expand=True, padx=5, pady=5)

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
            self.app.cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
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
                    self.table_tree.insert("", "end", values=(
                        name, source_file, row_count, column_count, f"{estimated_size_mb:.2f} MB"))

                except Exception as e:
                    source_file = self.file_table_mapping.get(name, "不明")
                    self.table_tree.insert("", "end", values=(
                        name, source_file, "Error", "Error", "Error"))
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
            self.app.cursor.execute(
                f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
            if not self.app.cursor.fetchone():
                self.app.show_message(
                    f"テーブル '{table_name}' は存在しません。", "warning")
                return

            # テーブルを削除（クォートを修正）
            sql = f"DROP TABLE IF EXISTS [{table_name}]"
            self.log_message(f"実行SQL: {sql}")
            self.app.cursor.execute(sql)
            self.app.conn.commit()

            # 削除確認
            self.app.cursor.execute(
                f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
            if self.app.cursor.fetchone():
                self.log_message(
                    f"警告: テーブル {table_name} が削除されていません。別の方法で削除を試みます。")

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
            self.app.cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
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
                    self.app.cursor.execute(
                        f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,))
                    if self.app.cursor.fetchone():
                        self.log_message(
                            f"警告: テーブル {name} が削除されていません。別の方法で削除を試みます。")

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
                self.log_message(
                    "関連ファイル（WAL/SHM/Journal）が残っています。クリーンアップを試みます...")

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
            import time
            from datetime import datetime

            # 開始時刻を記録
            start_time = time.time()
            start_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # SQLiteManagerが利用可能かチェック
            if not self.app.sqlite_manager:
                self.app.show_message("SQLiteManagerが利用できません。", "error")
                return

            self.log_message("=== 全件データ更新（洗い替え）開始 ===")
            self.log_message(f"開始時刻: {start_datetime}")

            # 1. 既存テーブルをすべて削除
            delete_start = time.time()
            self.log_message("既存テーブルの削除を開始...")
            self.app.cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
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
            delete_time = time.time() - delete_start
            self.log_message(
                f"{deleted_count} 個のテーブルを削除しました（{delete_time:.2f}秒）")

            # 2. data/rawフォルダのファイルを処理
            import sys
            import os
            from pathlib import Path

            # プロジェクトルートを取得
            gui_tool_dir = Path(os.path.abspath(os.path.dirname(__file__)))
            # src/core/sqlite_gui_tool の2つ上
            project_root = gui_tool_dir.parents[2]
            raw_data_dir = project_root / 'data' / 'raw'

            self.log_message(f"データフォルダ: {raw_data_dir}")

            if not raw_data_dir.exists():
                self.log_message(f"データフォルダが見つかりません: {raw_data_dir}")
                self.app.show_message(
                    f"データフォルダが見つかりません: {raw_data_dir}", "error")
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
                self.app.show_message(
                    "data/rawフォルダに処理対象のファイルが見つかりません", "warning")
                return

            # 3. 各ファイルを処理
            process_start = time.time()
            processed_files = 0
            total_rows = 0
            file_times = []  # 各ファイルの処理時間を記録

            for file_path in data_files:
                try:
                    file_start = time.time()
                    self.log_message(f"ファイル処理開始: {file_path.name}")

                    # ZP138.txtの特殊処理
                    if file_path.name.upper() == 'ZP138.TXT':
                        success, table_name, row_count = self._process_zp138_file(
                            file_path)
                    else:
                        # 通常ファイル処理
                        success, table_name, row_count = self._process_single_file(
                            file_path)

                    file_time = time.time() - file_start

                    if success:
                        processed_files += 1
                        total_rows += row_count
                        # ファイル名とテーブル名のマッピングを保存
                        self.file_table_mapping[table_name] = file_path.name
                        file_times.append(
                            (file_path.name, file_time, row_count))
                        self.log_message(
                            f"ファイル処理完了: {file_path.name} → テーブル {table_name}: {row_count:,} 行 ({file_time:.2f}秒)")
                    else:
                        self.log_message(
                            f"ファイル処理失敗: {file_path.name} ({file_time:.2f}秒)")

                    # UIの更新
                    self.parent.update()

                except Exception as e:
                    self.log_message(f"ファイル {file_path.name} の処理エラー: {e}")
                    import traceback
                    self.log_message(traceback.format_exc())

            # 4. インデックスとキーの設定
            finalize_start = time.time()
            self.log_message("インデックスとキーの設定を開始...")
            try:
                if self.app.sqlite_manager and hasattr(self.app.sqlite_manager, 'finalize_database'):
                    # データベースパスを取得
                    db_path = self.app.db_path if hasattr(self.app, 'db_path') else None
                    if not db_path and self.app.conn:
                        try:
                            db_path = self.app.conn.execute("PRAGMA database_list").fetchone()[2]
                        except:
                            db_path = "data/sqlite/main.db"  # デフォルトパス
                    
                    self.app.sqlite_manager.finalize_database(db_path)
                    finalize_time = time.time() - finalize_start
                    self.log_message(
                        f"インデックスとキーの設定が完了しました（{finalize_time:.2f}秒）")
                else:
                    self.log_message("SQLiteManagerが利用できないため、インデックス設定をスキップします")
            except Exception as e:
                finalize_time = time.time() - finalize_start
                self.log_message(f"インデックス設定エラー: {e} ({finalize_time:.2f}秒)")
                import traceback
                self.log_message(traceback.format_exc())

            # 処理時間の計算
            process_time = time.time() - process_start
            total_time = time.time() - start_time
            end_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # 5. 完了処理
            self.log_message(f"=== 全件データ更新完了 ===")
            self.log_message(f"終了時刻: {end_datetime}")
            self.log_message(f"処理ファイル数: {processed_files}/{len(data_files)}")
            self.log_message(f"総行数: {total_rows:,} 行")
            self.log_message(f"ファイル処理時間: {process_time:.2f}秒")
            self.log_message(f"総実行時間: {total_time:.2f}秒")

            # ファイル別処理時間の詳細ログ
            self.log_message("--- ファイル別処理時間 ---")
            for file_name, file_time, row_count in sorted(file_times, key=lambda x: x[1], reverse=True):
                rows_per_sec = row_count / file_time if file_time > 0 else 0
                self.log_message(
                    f"{file_name}: {file_time:.2f}秒 ({row_count:,}行, {rows_per_sec:.0f}行/秒)")

            # テーブル情報を更新
            self.refresh_table_info()

            # 他のタブも更新
            self._update_all_tabs()

            self.app.show_message(
                f"全件データ更新が完了しました。\n"
                f"処理ファイル数: {processed_files}/{len(data_files)}\n"
                f"総行数: {total_rows:,} 行\n"
                f"実行時間: {total_time:.2f}秒",
                "info"
            )

        except Exception as e:
            self.log_message(f"全件データ更新エラー: {e}")
            self.app.show_message(f"全件データ更新エラー: {e}", "error")
            import traceback
            self.log_message(traceback.format_exc())

    def copy_selected_row(self):
        """選択された行をクリップボードにコピー（複数選択対応）"""
        # 選択された行を取得
        selected = self.table_tree.selection()
        if not selected:
            self.app.show_message("行が選択されていません。", "warning")
            return

        try:
            # pyperclipのインポートを試みる
            import pyperclip

            # 複数行の値を取得
            lines = []
            for item in selected:
                values = self.table_tree.item(item, "values")
                line = "\t".join(str(v) for v in values)
                lines.append(line)

            # 改行で結合
            text = "\n".join(lines)
            pyperclip.copy(text)

            self.log_message(f"{len(selected)} 行をクリップボードにコピーしました。")

        except ImportError:
            self.app.show_message(
                "pyperclipモジュールがインストールされていないため、コピー機能は使用できません。\n"
                "pip install pyperclipでインストールしてください。",
                "warning"
            )

    def export_table_info_csv(self):
        """テーブル情報をCSVファイルに出力"""
        try:
            from tkinter import filedialog
            import csv
            from datetime import datetime

            # 保存先ファイルを選択
            file_path = filedialog.asksaveasfilename(
                title="CSV出力先を選択",
                defaultextension=".csv",
                filetypes=[("CSVファイル", "*.csv"), ("すべてのファイル", "*.*")],
                initialfile=f"table_info_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            )

            if not file_path:
                return

            # CSVファイルに書き込み
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.writer(csvfile)

                # ヘッダー行を書き込み
                headers = ["テーブル名", "元ファイル名", "行数", "カラム数", "推定サイズ"]
                writer.writerow(headers)

                # データ行を書き込み
                for item in self.table_tree.get_children():
                    values = self.table_tree.item(item, "values")
                    writer.writerow(values)

            self.log_message(f"テーブル情報をCSVファイルに出力しました: {file_path}")
            self.app.show_message(f"CSVファイルに出力しました:\n{file_path}", "info")

        except Exception as e:
            self.log_message(f"CSV出力エラー: {e}")
            self.app.show_message(f"CSV出力エラー: {e}", "error")

    def log_message(self, message):
        """ログメッセージを表示"""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)

    def on_db_connect(self, conn, cursor):
        """データベース接続時の処理"""
        # 既存テーブルのファイルマッピング情報を復元
        self._restore_file_table_mapping()
        # テーブル情報を更新
        self.refresh_table_info()

    def _restore_file_table_mapping(self):
        """既存テーブルのファイルマッピング情報を復元"""
        if not self.app.conn:
            self.log_message("データベース接続がありません")
            return

        try:
            self.log_message("ファイルマッピング復元を開始...")

            # config/テキスト一覧.csvからマッピング情報を読み込み
            mapping_from_config = self._load_table_mapping_from_config()
            self.log_message(
                f"設定ファイルから読み込んだマッピング数: {len(mapping_from_config)}")

            # デバッグ: SASIZU_JISSEKIが含まれているかチェック
            if 'SASIZU_JISSEKI' in mapping_from_config:
                self.log_message(
                    f"SASIZU_JISSEKI は設定ファイルに存在: {mapping_from_config['SASIZU_JISSEKI']}")
            else:
                self.log_message("SASIZU_JISSEKI は設定ファイルに見つかりません")
                # 設定ファイルの内容をデバッグ出力
                for key in list(mapping_from_config.keys())[:5]:  # 最初の5件のみ
                    self.log_message(
                        f"設定ファイル内容例: {key} -> {mapping_from_config[key]}")

            # 既存のテーブル一覧を取得
            cursor = self.app.cursor
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
            tables = cursor.fetchall()

            self.log_message(f"テーブル数: {len(tables)}")
            self.log_message(f"設定ファイルからのマッピング数: {len(mapping_from_config)}")

            # 各テーブルに対してファイル名を設定
            for (table_name,) in tables:
                if table_name not in self.file_table_mapping:
                    # まず設定ファイルからマッピングを確認
                    if table_name in mapping_from_config:
                        filename = mapping_from_config[table_name]
                        self.file_table_mapping[table_name] = filename
                        self.log_message(
                            f"設定ファイルからマッピング: {table_name} -> {filename}")
                    else:
                        # 設定ファイルにない場合は推測
                        self.log_message(f"テーブル {table_name} のファイル名を推測中...")
                        estimated_filename = self._estimate_filename_from_table(
                            table_name)
                        self.file_table_mapping[table_name] = estimated_filename
                        self.log_message(
                            f"推測マッピング: {table_name} -> {estimated_filename}")
                else:
                    self.log_message(f"テーブル {table_name} は既にマッピング済み")

            self.log_message("ファイルマッピング復元完了")

        except Exception as e:
            self.log_message(f"ファイルマッピング復元エラー: {e}")
            import traceback
            self.log_message(f"詳細エラー: {traceback.format_exc()}")

    def _load_table_mapping_from_config(self):
        """config/テキスト一覧.csvからテーブル名とファイル名のマッピングを読み込み"""
        mapping = {}
        try:
            import pandas as pd
            from pathlib import Path

            config_file = Path('config/テキスト一覧.csv')
            if config_file.exists():
                self.log_message(f"設定ファイルを読み込み中: {config_file}")

                # CSVファイルを読み込み
                df = pd.read_csv(config_file, encoding='utf-8-sig')

                # テーブル名とファイル名の列を確認
                if 'ファイル名' in df.columns:
                    for _, row in df.iterrows():
                        file_name = str(row['ファイル名']).strip()

                        # テーブル名修正列があればそれを優先、なければテーブル名列を使用
                        table_name = None
                        if 'テーブル名修正' in df.columns and pd.notna(row['テーブル名修正']) and str(row['テーブル名修正']).strip():
                            table_name = str(row['テーブル名修正']).strip()
                            self.log_message(
                                f"修正テーブル名を使用: {table_name} -> {file_name}")
                        elif 'テーブル名' in df.columns and pd.notna(row['テーブル名']) and str(row['テーブル名']).strip():
                            table_name = str(row['テーブル名']).strip()
                            self.log_message(
                                f"元テーブル名を使用: {table_name} -> {file_name}")

                        if table_name and file_name and table_name != 'nan' and file_name != 'nan':
                            # テーブル名をそのまま使用（ローマ字表記）
                            mapping[table_name] = file_name

                            # 日本語テーブル名の場合はハッシュ化されたテーブル名も生成（後方互換性のため）
                            import re
                            has_japanese = re.search(
                                r'[ぁ-んァ-ン一-龥]', table_name)
                            if has_japanese:
                                hash_table_name = f"t_{hash(table_name) % 10000:04d}"
                                mapping[hash_table_name] = file_name
                                self.log_message(
                                    f"日本語テーブル名ハッシュマッピング: {table_name} -> {hash_table_name} -> {file_name}")
                            else:
                                # 通常のテーブル名変換も適用（sanitize処理）
                                sanitized = re.sub(
                                    r'[^a-zA-Z0-9]', '_', table_name)
                                sanitized = re.sub(r'_+', '_', sanitized)
                                if sanitized and sanitized[0].isdigit():
                                    sanitized = f"t_{sanitized}"
                                sanitized = sanitized.strip('_')
                                if sanitized != table_name:
                                    mapping[sanitized] = file_name
                                    self.log_message(
                                        f"サニタイズマッピング: {table_name} -> {sanitized} -> {file_name}")

                self.log_message(f"設定ファイルから {len(mapping)} 件のマッピングを読み込み")
            else:
                self.log_message(f"設定ファイルが見つかりません: {config_file}")

        except Exception as e:
            self.log_message(f"設定ファイル読み込みエラー: {e}")
            import traceback
            self.log_message(f"詳細: {traceback.format_exc()}")

        return mapping

    def _estimate_filename_from_table(self, table_name):
        """テーブル名からファイル名を推測（設定ファイルにない場合のフォールバック）"""
        # 特殊なテーブル名の処理
        special_mappings = {
            't_zp138引当': 'ZP138.txt (引当計算付き)',
            'view_pc_master': 'MARA_DL.csv (加工)',
            'parsed_pc_master': 'view_pc_master (解析)',
        }

        if table_name in special_mappings:
            return special_mappings[table_name]

        # t_で始まるハッシュ化テーブル名の場合
        if table_name.startswith('t_') and len(table_name) == 6 and table_name[2:].isdigit():
            return "設定ファイル未登録 (日本語ファイル名)"

        # 通常のテーブル名の場合
        if table_name.startswith('t_'):
            estimated = table_name[2:]  # t_プレフィックスを除去
        else:
            estimated = table_name

        return f"{estimated}.txt (推測)"

    def on_db_disconnect(self):
        """データベース切断時の処理"""
        # テーブル情報をクリア
        for item in self.table_tree.get_children():
            self.table_tree.delete(item)

        # ログをクリア
        self.log_text.delete(1.0, tk.END)

        # ファイルマッピングをクリア
        self.file_table_mapping.clear()

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
                        df = pd.read_csv(
                            file_path, encoding=encoding, sep=delimiter, dtype=str)
                else:
                    # 通常のCSV/TXT処理（エラー耐性を強化）
                    try:
                        # 最初は文字列として読み込み、後でデータ型を最適化
                        df = pd.read_csv(
                            file_path,
                            encoding=encoding,
                            sep=delimiter,
                            dtype=str,
                            on_bad_lines='skip',  # 問題のある行をスキップ
                            engine='python'  # より柔軟な解析
                        )
                    except (UnicodeDecodeError, pd.errors.ParserError):
                        # エンコーディングまたはパース エラーの場合
                        try:
                            # CP932で再試行
                            df = pd.read_csv(
                                file_path,
                                encoding='cp932',
                                sep=delimiter,
                                dtype=str,
                                on_bad_lines='skip',
                                engine='python'
                            )
                        except (UnicodeDecodeError, pd.errors.ParserError):
                            # それでも失敗した場合は、より寛容な設定で試行
                            try:
                                df = pd.read_csv(
                                    file_path,
                                    encoding='utf-8',
                                    sep=None,  # 区切り文字を自動検出
                                    dtype=str,
                                    on_bad_lines='skip',
                                    engine='python'
                                )
                            except Exception:
                                # 最後の手段：latin-1エンコーディング
                                df = pd.read_csv(
                                    file_path,
                                    encoding='latin-1',
                                    sep=delimiter,
                                    dtype=str,
                                    on_bad_lines='skip',
                                    engine='python'
                                )

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
            df.to_sql(table_name, self.app.conn,
                      if_exists='replace', index=False)
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

        # 品目コード系のパターン（先頭0保持が必要）
        item_code_patterns = ['品目', 'item',
                              'material', '部品', 'part', '製品', 'product']

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
            is_date_column = any(
                pattern in col_lower for pattern in date_column_patterns)

            if is_date_column:
                self.log_message(f"日付列として処理: {col}")
                try:
                    # 8桁数値形式（YYYYMMDD）をチェック
                    if all(isinstance(x, str) and len(x) == 8 and x.isdigit() for x in sample.head(10) if pd.notna(x)):
                        # 8桁数値形式として処理
                        df[col] = pd.to_datetime(
                            df[col], format='%Y%m%d', errors='coerce')

                        # 特殊な値（99991231など）を処理
                        special_mask = df[col].isna() & df[col].astype(
                            str).str.contains('9999', na=False)
                        if special_mask.any():
                            df.loc[special_mask, col] = pd.Timestamp.max
                    else:
                        # 標準的な日付形式で変換
                        import warnings
                        with warnings.catch_warnings():
                            warnings.simplefilter("ignore")
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
                # 品目コードかどうかをチェック
                is_item_code = any(
                    pattern in col_lower for pattern in item_code_patterns)

                if is_item_code:
                    self.log_message(f"品目コード列として処理（先頭0保持）: {col}")
                    # 品目コードは文字列として保持
                    df[col] = df[col].astype(str)
                else:
                    self.log_message(f"コード列として処理: {col}")
                    # その他のコードは数値変換を試行
                    try:
                        # ゼロパディングを除去して数値変換
                        df[col] = df[col].apply(
                            self._remove_zero_padding).astype(int)
                    except:
                        # 変換に失敗した場合は文字列として保持
                        df[col] = df[col].astype(str)

            # その他の列の自動判定
            else:
                # SAP後ろマイナス処理を適用
                df[col] = df[col].apply(self._process_sap_trailing_minus)

                # 数値として解釈できるかチェック
                try:
                    # サンプルの90%以上が数値として変換可能な場合
                    numeric_sample = pd.to_numeric(sample, errors='coerce')
                    valid_numeric_ratio = (~numeric_sample.isna()).mean()

                    if valid_numeric_ratio >= 0.9:
                        self.log_message(
                            f"自動判定で数値列: {col} (有効率: {valid_numeric_ratio:.2f})")
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
                        test_dates = pd.to_datetime(sample.head(
                            10), format='%Y%m%d', errors='coerce')
                        valid_dates_ratio = (~test_dates.isna()).mean()

                        if valid_dates_ratio >= 0.7:  # 70%以上が有効な日付
                            self.log_message(
                                f"自動判定で8桁日付列: {col} (有効率: {valid_dates_ratio:.2f})")
                            df[col] = pd.to_datetime(
                                df[col], format='%Y%m%d', errors='coerce')

                            # 特殊な値（99991231など）を処理
                            special_mask = df[col].isna() & df[col].astype(
                                str).str.contains('9999', na=False)
                            if special_mask.any():
                                df.loc[special_mask, col] = pd.Timestamp.max
                            continue
                except:
                    pass

                # タイムスタンプ形式をチェック
                try:
                    import warnings
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        timestamp_sample = pd.to_datetime(
                            sample.head(10), errors='coerce')
                        valid_timestamp_ratio = (
                            ~timestamp_sample.isna()).mean()

                        if valid_timestamp_ratio >= 0.7:  # 70%以上が有効なタイムスタンプ
                            self.log_message(
                                f"自動判定でタイムスタンプ列: {col} (有効率: {valid_timestamp_ratio:.2f})")
                            df[col] = pd.to_datetime(df[col], errors='coerce')
                            continue
                except:
                    pass

                # デフォルトは文字列として保持
                self.log_message(f"文字列列として保持: {col}")

        self.log_message("データ型最適化完了")
        return df

    def _process_sap_trailing_minus(self, value):
        """SAP後ろマイナス表記を処理する"""
        if isinstance(value, str) and value.endswith('-'):
            return f"-{value[:-1]}"
        return value

    def _remove_zero_padding(self, value):
        """ゼロパディングを除去する（品目コード以外用）"""
        if isinstance(value, str) and value.isdigit():
            # 先頭の0を除去（ただし、すべて0の場合は0を返す）
            stripped = value.lstrip('0')
            return stripped if stripped else '0'
        return value

    def _process_zp138_file(self, file_path):
        """ZP138.txtファイルの特殊処理（引当計算付き）"""
        try:
            import pandas as pd
            from decimal import Decimal, InvalidOperation, getcontext

            # 小数点以下の桁数を設定
            getcontext().prec = 10

            self.log_message(f"ZP138特殊処理開始: {file_path.name}")

            # ファイル読み込み
            df = pd.read_csv(file_path, delimiter='\t',
                             encoding='cp932', header=0, dtype=str)

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
            df['所要日付'] = pd.to_datetime(
                df['所要日付'], format='%Y%m%d', errors='coerce')
            df['再日程計画日付'] = pd.to_datetime(
                df['再日程計画日付'], format='%Y%m%d', errors='coerce')

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
            df.to_sql(table_name, self.app.conn,
                      if_exists='replace', index=False)
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
                row_quantity = Decimal(
                    str(row['入庫_所要量'])).quantize(Decimal('0.001'))

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
                self.app.show_message(
                    f"ZP138.txtファイルが見つかりません: {zp138_file}", "error")
                return

            self.log_message("=== ZP138個別処理開始 ===")

            # ZP138処理を実行
            success, table_name, row_count = self._process_zp138_file(
                zp138_file)

            if success:
                # ファイル名とテーブル名のマッピングを保存
                self.file_table_mapping[table_name] = zp138_file.name

                self.log_message(f"ZP138処理完了: {table_name} ({row_count:,} 行)")

                # テーブル情報を更新
                self.refresh_table_info()

                # 他のタブも更新
                self._update_all_tabs()

                self.app.show_message(
                    f"ZP138処理が完了しました。\nテーブル: {table_name}\n行数: {row_count:,} 行", "info")
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
                    self.log_message(
                        f"ファイルサイズ: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
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
            self.app.cursor.execute(
                "SELECT type, name FROM sqlite_master ORDER BY type, name")
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
            self.app.cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
            tables = self.app.cursor.fetchall()

            if tables:
                self.log_message(f"ユーザーテーブル数: {len(tables)}")
                total_rows = 0
                for table in tables:
                    table_name = table[0]
                    try:
                        self.app.cursor.execute(
                            f"SELECT COUNT(*) FROM [{table_name}]")
                        row_count = self.app.cursor.fetchone()[0]
                        total_rows += row_count
                        self.log_message(
                            f"  テーブル {table_name}: {row_count:,} 行")
                    except Exception as e:
                        self.log_message(f"  テーブル {table_name}: エラー - {e}")

                self.log_message(f"総行数: {total_rows:,} 行")
            else:
                self.log_message("ユーザーテーブルが見つかりません")

            self.log_message("=== データベース診断完了 ===")

        except Exception as e:
            self.log_message(f"診断エラー: {e}")
            self.app.show_message(f"データベース診断エラー: {e}", "error")

    def process_maradl_pipeline(self):
        """MARADLパイプライン処理（3段階のマスタ処理）"""
        if not self.app.conn:
            self.app.show_message("データベースに接続されていません。", "warning")
            return

        # 確認ダイアログ
        if not messagebox.askyesno("確認",
                                   "MARADLパイプライン処理を実行しますか？\n"
                                   "1. MARA_DL → 全120フィールドのマスタテーブル\n"
                                   "2. view_pc_master → 使用頻度の高いフィールドを抽出してPC基板に絞り込み\n"
                                   "3. parsed_pc_master → 差分検出と正規表現による要素抽出"):
            return

        try:
            self.log_message("=== MARADLパイプライン処理開始 ===")

            # 1. MARA_DLテーブルの存在確認
            self.app.cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='MARA_DL'")
            if not self.app.cursor.fetchone():
                self.log_message("エラー: MARA_DLテーブルが存在しません。先に全件データ更新を実行してください。")
                self.app.show_message(
                    "MARA_DLテーブルが存在しません。\n先に全件データ更新を実行してください。", "error")
                return

            # MARA_DLの行数確認
            self.app.cursor.execute("SELECT COUNT(*) FROM MARA_DL")
            mara_count = self.app.cursor.fetchone()[0]
            self.log_message(f"MARA_DLテーブル: {mara_count:,} 行")

            # 2. view_pc_master処理
            self.log_message("Step 1: view_pc_master処理開始...")
            success = self._create_view_pc_master()
            if not success:
                self.log_message("view_pc_master処理に失敗しました")
                return

            # 3. parsed_pc_master処理
            self.log_message("Step 2: parsed_pc_master処理開始...")
            success = self._create_parsed_pc_master()
            if not success:
                self.log_message("parsed_pc_master処理に失敗しました")
                return

            # 4. 差分検出と登録処理
            self.log_message("Step 3: 差分検出と登録処理開始...")
            success = self._process_pc_master_diff()
            if not success:
                self.log_message("差分検出処理に失敗しました")
                return

            self.log_message("=== MARADLパイプライン処理完了 ===")

            # テーブル情報を更新
            self.refresh_table_info()
            self._update_all_tabs()

            self.app.show_message("MARADLパイプライン処理が完了しました。", "info")

        except Exception as e:
            self.log_message(f"MARADLパイプライン処理エラー: {e}")
            self.app.show_message(f"MARADLパイプライン処理エラー: {e}", "error")
            import traceback
            self.log_message(traceback.format_exc())

    def _create_view_pc_master(self):
        """view_pc_masterテーブルを作成（使用頻度の高いフィールドを抽出してPC基板に絞り込み）"""
        try:
            # 既存のview_pc_masterテーブルを削除
            self.app.cursor.execute("DROP TABLE IF EXISTS view_pc_master")

            # view_pc_masterテーブルを作成
            create_sql = """
            CREATE TABLE view_pc_master AS
            SELECT 
                プラント,
                MRP_管理者,
                調達タイプ,
                評価クラス,
                格上げ区分,
                品目タイプコード,
                品目,
                品目テキスト,
                標準原価,
                現会計年度,
                現期間,
                研究室_設計室,
                ＭＲＰ出庫保管場所,
                MRP_管理者名,
                BOM,
                作業手順,
                ＭＲＰタイプ,
                タイムフェンス,
                間接費グループ,
                販売ステータス,
                プラント固有ステータス,
                ロットサイズ,
                品目登録日,
                利益センタ,
                安全在庫,
                丸め数量,
                最小ロットサイズ,
                原価計算ロットサイズ,
                日程計画余裕キー,
                設計担当者ID,
                設計担当者名,
                最終入庫日,
                最終出庫日
            FROM MARA_DL
            WHERE 
                (プラント = 'P100' AND 評価クラス = '2120') OR
                (プラント = 'P100' AND 評価クラス = '2130' AND 品目 LIKE '9710%' AND 品目 != '971030100')
            """

            self.app.cursor.execute(create_sql)
            self.app.conn.commit()

            # 作成されたテーブルの行数を確認
            self.app.cursor.execute("SELECT COUNT(*) FROM view_pc_master")
            count = self.app.cursor.fetchone()[0]
            self.log_message(f"view_pc_masterテーブルを作成しました: {count:,} 行")

            # ファイル名とテーブル名のマッピングを保存
            self.file_table_mapping['view_pc_master'] = 'MARA_DL.csv (加工)'

            return True

        except Exception as e:
            self.log_message(f"view_pc_master作成エラー: {e}")
            return False

    def _create_parsed_pc_master(self):
        """parsed_pc_masterテーブルを作成（正規表現による要素抽出）"""
        try:
            # 既存のparsed_pc_masterテーブルを削除
            self.app.cursor.execute("DROP TABLE IF EXISTS parsed_pc_master")

            # parsed_pc_masterテーブルを作成
            create_sql = """
            CREATE TABLE parsed_pc_master (
                品目 TEXT PRIMARY KEY,
                品目テキスト TEXT,
                cm_code TEXT,
                board_number TEXT,
                derivative_code TEXT,
                board_type TEXT,
                登録日 TEXT
            )
            """

            self.app.cursor.execute(create_sql)
            self.app.conn.commit()

            self.log_message("parsed_pc_masterテーブルを作成しました")

            # ファイル名とテーブル名のマッピングを保存
            self.file_table_mapping['parsed_pc_master'] = 'view_pc_master (解析)'

            return True

        except Exception as e:
            self.log_message(f"parsed_pc_master作成エラー: {e}")
            return False

    def _process_pc_master_diff(self):
        """PC Master差分検出と登録処理"""
        try:
            import pandas as pd
            import re
            from datetime import datetime

            # 正規表現パターンと処理ロジック（元のz_Parsed Pc Master Diff Logger.pyから移植）
            BLACKLIST = {"SENS", "CV", "CV-055"}
            DERIVATIVE_PATTERN = re.compile(
                r"([STU][0-9]{1,2}|[STU][A-Z][0-9])")

            Y_CODE_MAP = {
                "YAMK": "m", "YAUWM": "w", "YAWM": "w", "YBPM": "p", "YCK": "c", "YCUWM": "w",
                "YGK": "g", "YMK": "m", "YPK": "p", "YPM": "p", "YUK": "w", "YWK": "w", "YWM": "w"
            }

            HEAD_CM_MAP = {
                "AK": "a", "CK": "c", "DK": "d", "EK": "e", "GK": "g", "HK": "h", "IK": "i", "LK": "l",
                "MK": "m", "PK": "p", "PM": "p", "SK": "s", "UK": "w", "UWM": "w", "WK": "w", "WM": "w", "WS": "w",
                "BWM": "w"
            }

            def extract_derivative(text):
                if not isinstance(text, str):
                    return None
                candidates = DERIVATIVE_PATTERN.findall(text.upper())
                for cand in candidates:
                    if cand not in BLACKLIST:
                        return cand
                return None

            def extract_board_number(code, name):
                if name.startswith("DIMCOM"):
                    match = re.search(r"DIMCOM\s*(?:No\.\s*)?(\d{5})", name)
                    if match:
                        return match.group(1)
                if code.startswith("P00A"):
                    return code[5:9]
                elif code.startswith("P0A"):
                    return code[3:7]
                elif "-" in name:
                    parts = name.split("-")
                    if len(parts) > 1:
                        match = re.search(r"\d{3,4}", parts[1])
                        return match.group(0) if match else None
                elif re.search(r"\d{3,4}", name):
                    return re.search(r"\d{3,4}", name).group(0)
                return None

            def extract_cm_code(code, name):
                name = name.upper()
                if code.startswith("P0E"):
                    return "other"
                if name.startswith("WB"):
                    return "CM-W"
                if name.startswith("DIMCOM"):
                    return "CM-L"
                if name.startswith("CV"):
                    return "CM-I"
                if name.startswith("FK"):
                    return "free"
                if name.startswith("X"):
                    if name.startswith("XAMK"):
                        return "CM-M"
                    if name.startswith("XUK"):
                        return "CM-W"
                    return "CM-" + name[1]
                if name.startswith("Y"):
                    for l in [5, 4, 3]:
                        if name[:l] in Y_CODE_MAP:
                            return "CM-" + Y_CODE_MAP[name[:l]].upper()
                m = re.match(r"([A-Z]{2,4})", name)
                if m and m.group(1) in HEAD_CM_MAP:
                    return "CM-" + HEAD_CM_MAP[m.group(1)].upper()
                return "other"

            # view_pc_masterからデータを取得
            df_all = pd.read_sql(
                "SELECT 品目, 品目テキスト FROM view_pc_master", self.app.conn)
            self.log_message(f"view_pc_masterから {len(df_all):,} 件のデータを取得")

            # 既存のparsed_pc_masterからデータを取得
            try:
                df_existing = pd.read_sql(
                    "SELECT 品目, 品目テキスト FROM parsed_pc_master", self.app.conn)
                self.log_message(
                    f"parsed_pc_masterから {len(df_existing):,} 件の既存データを取得")
            except:
                df_existing = pd.DataFrame(columns=["品目", "品目テキスト"])
                self.log_message("parsed_pc_masterは空です")

            # 差分データの生成
            if not df_all.empty and not df_existing.empty:
                df_new = df_all[~df_all["品目"].isin(df_existing["品目"])]
            else:
                df_new = df_all.copy()

            self.log_message(f"差分データ: {len(df_new):,} 件")

            if df_new.empty:
                self.log_message("差分なし（追加不要）")
                return True

            # データ処理
            df_new = df_new.copy()
            df_new["cm_code"] = df_new.apply(
                lambda row: extract_cm_code(row["品目"], row["品目テキスト"]), axis=1)
            df_new["board_number"] = df_new.apply(lambda row: extract_board_number(
                row["品目"], row["品目テキスト"]) if row["cm_code"] != "other" else None, axis=1)
            df_new["derivative_code"] = df_new.apply(lambda row: extract_derivative(
                row["品目テキスト"]) if row["cm_code"] != "other" else None, axis=1)
            df_new["board_type"] = df_new.apply(
                lambda row: "派生基板" if row["derivative_code"] else "標準" if row["cm_code"] != "other" else None, axis=1)
            df_new["登録日"] = datetime.now().strftime("%Y-%m-%d")

            # データベースへの登録
            inserted_count = 0
            for _, row in df_new.iterrows():
                try:
                    self.app.cursor.execute(
                        """
                        INSERT INTO parsed_pc_master (品目, 品目テキスト, cm_code, board_number, derivative_code, board_type, 登録日)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (row["品目"], row["品目テキスト"], row["cm_code"],
                         row["board_number"], row["derivative_code"], row["board_type"], row["登録日"])
                    )
                    inserted_count += 1
                except Exception as e:
                    self.log_message(f"データベース登録エラー (品目: {row['品目']}): {e}")

            self.app.conn.commit()
            self.log_message(f"{inserted_count:,} 件をparsed_pc_masterに登録しました")

            # 差分ログをCSVに出力
            try:
                import os
                from pathlib import Path

                # ログディレクトリを作成
                log_dir = Path("logs")
                log_dir.mkdir(exist_ok=True)

                log_file = log_dir / \
                    f"pc_master_diff_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                df_new.to_csv(log_file, index=False, encoding="utf-8-sig")
                self.log_message(f"差分ログを出力しました: {log_file}")

            except Exception as e:
                self.log_message(f"差分ログ出力エラー: {e}")

            return True

        except Exception as e:
            self.log_message(f"PC Master差分処理エラー: {e}")
            import traceback
            self.log_message(traceback.format_exc())
            return False

    def process_zp138_individual(self):
        """ZP138個別処理（引当計算付き）"""
        if not self.app.conn:
            self.app.show_message("データベースに接続されていません。", "warning")
            return

        # 確認ダイアログ
        if not messagebox.askyesno("確認",
                                   "ZP138個別処理を実行しますか？\n"
                                   "・ZP138.txtファイルを読み込み\n"
                                   "・引当計算を実行\n"
                                   "・t_zp138引当テーブルを作成"):
            return

        try:
            self.log_message("=== ZP138個別処理開始 ===")

            # ZP138.txtファイルの存在確認
            import os
            from pathlib import Path

            gui_tool_dir = Path(os.path.abspath(os.path.dirname(__file__)))
            project_root = gui_tool_dir.parents[2]
            zp138_file = project_root / 'data' / 'raw' / 'ZP138.txt'

            if not zp138_file.exists():
                self.log_message(f"ZP138.txtファイルが見つかりません: {zp138_file}")
                self.app.show_message(
                    f"ZP138.txtファイルが見つかりません:\n{zp138_file}", "error")
                return

            # ZP138プロセッサーを使用
            try:
                # プロセッサーモジュールをインポート
                sys.path.append(str(project_root / 'src' / 'processors'))
                from zp138_processor import ZP138Processor

                # プロセッサーを実行
                processor = ZP138Processor(str(self.app.db_path))
                success = processor.process()

                if success:
                    self.log_message("ZP138個別処理が完了しました")

                    # テーブル情報を更新
                    self.refresh_table_info()
                    self._update_all_tabs()

                    self.app.show_message("ZP138個別処理が完了しました。", "info")
                else:
                    self.log_message("ZP138個別処理に失敗しました")
                    self.app.show_message("ZP138個別処理に失敗しました。", "error")

            except ImportError as e:
                self.log_message(f"ZP138プロセッサーのインポートエラー: {e}")
                self.app.show_message(f"ZP138プロセッサーが見つかりません:\n{e}", "error")

        except Exception as e:
            self.log_message(f"ZP138個別処理エラー: {e}")
            self.app.show_message(f"ZP138個別処理エラー: {e}", "error")
            import traceback
            self.log_message(traceback.format_exc())

    def diagnose_database(self):
        """データベース診断"""
        if not self.app.conn:
            self.app.show_message("データベースに接続されていません。", "warning")
            return

        try:
            self.log_message("=== データベース診断開始 ===")

            # 1. 基本情報
            self.log_message(f"データベースファイル: {self.app.db_path}")

            # ファイルサイズ
            import os
            if os.path.exists(self.app.db_path):
                file_size = os.path.getsize(self.app.db_path)
                self.log_message(f"ファイルサイズ: {file_size / (1024*1024):.2f} MB")

            # 2. テーブル数
            self.app.cursor.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
            table_count = self.app.cursor.fetchone()[0]
            self.log_message(f"テーブル数: {table_count}")

            # 3. 総行数
            self.app.cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
            tables = self.app.cursor.fetchall()

            total_rows = 0
            for table in tables:
                name = table[0]
                try:
                    self.app.cursor.execute(f"SELECT COUNT(*) FROM [{name}]")
                    count = self.app.cursor.fetchone()[0]
                    total_rows += count
                except:
                    pass

            self.log_message(f"総行数: {total_rows:,}")

            # 4. インデックス数
            self.app.cursor.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'")
            index_count = self.app.cursor.fetchone()[0]
            self.log_message(f"インデックス数: {index_count}")

            # 5. PRAGMA情報
            pragma_checks = [
                "journal_mode", "synchronous", "cache_size", "page_size",
                "auto_vacuum", "foreign_keys", "integrity_check"
            ]

            for pragma in pragma_checks:
                try:
                    self.app.cursor.execute(f"PRAGMA {pragma}")
                    result = self.app.cursor.fetchone()
                    if result:
                        self.log_message(f"{pragma}: {result[0]}")
                except Exception as e:
                    self.log_message(f"{pragma}: エラー - {e}")

            # 6. 大きなテーブルの特定
            self.log_message("\n--- 大きなテーブル（上位5件） ---")
            table_sizes = []
            for table in tables:
                name = table[0]
                try:
                    self.app.cursor.execute(f"SELECT COUNT(*) FROM [{name}]")
                    count = self.app.cursor.fetchone()[0]
                    table_sizes.append((name, count))
                except:
                    pass

            table_sizes.sort(key=lambda x: x[1], reverse=True)
            for name, count in table_sizes[:5]:
                self.log_message(f"{name}: {count:,} 行")

            self.log_message("=== データベース診断完了 ===")

        except Exception as e:
            self.log_message(f"データベース診断エラー: {e}")
            self.app.show_message(f"データベース診断エラー: {e}", "error")

    def standardize_data_types(self):
        """データ型の統一処理"""
        if not self.app.conn:
            self.app.show_message("データベースに接続されていません。", "warning")
            return

        # 確認ダイアログ
        if not messagebox.askyesno("確認",
                                   "データ型の統一処理を実行しますか？\n"
                                   "・品目コード系フィールドを文字列型に統一\n"
                                   "・日付系フィールドを適切な形式に統一\n"
                                   "・数値系フィールドを適切な型に統一"):
            return

        try:
            self.log_message("=== データ型統一処理開始 ===")

            # 品目コード系フィールドの統一
            code_fields = [
                ('zm29', '品目'),
                ('zp02', '品目'),
                ('zp138', '品目コード'),
                ('zs65', '品目コード'),
                ('MARA_DL', '品目'),
                ('view_pc_master', '品目'),
                ('parsed_pc_master', '品目')
            ]

            standardized_count = 0
            checked_count = 0

            for table_name, field_name in code_fields:
                try:
                    # テーブルの存在確認
                    self.app.cursor.execute(
                        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
                    if not self.app.cursor.fetchone():
                        self.log_message(f"テーブル {table_name} が存在しません")
                        continue

                    # フィールドの存在確認
                    self.app.cursor.execute(f"PRAGMA table_info({table_name})")
                    columns = [col[1] for col in self.app.cursor.fetchall()]
                    if field_name not in columns:
                        self.log_message(
                            f"テーブル {table_name} にフィールド {field_name} が存在しません")
                        continue

                    checked_count += 1

                    # 現在のデータ型を確認
                    self.app.cursor.execute(f"PRAGMA table_info({table_name})")
                    current_type = None
                    for col_info in self.app.cursor.fetchall():
                        if col_info[1] == field_name:
                            current_type = col_info[2]
                            break

                    self.log_message(
                        f"{table_name}.{field_name}: 現在の型 = {current_type}")

                    # TEXTでない場合は変換
                    if current_type and current_type.upper() != 'TEXT':
                        self.log_message(
                            f"{table_name}.{field_name}: {current_type} → TEXT に変換中...")

                        # 新しいテーブルを作成
                        temp_table = f"{table_name}_temp"

                        # 元テーブルの構造を取得
                        self.app.cursor.execute(
                            f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}'")
                        create_sql = self.app.cursor.fetchone()[0]

                        # フィールドの型をTEXTに変更
                        import re
                        pattern = rf'({re.escape(field_name)})\s+\w+'
                        new_create_sql = re.sub(
                            pattern, rf'\1 TEXT', create_sql)
                        new_create_sql = new_create_sql.replace(
                            f'CREATE TABLE {table_name}', f'CREATE TABLE {temp_table}')

                        # 一時テーブル作成
                        self.app.cursor.execute(new_create_sql)

                        # データをコピー（品目コードを文字列として）
                        self.app.cursor.execute(f"SELECT * FROM {table_name}")
                        columns = [description[0]
                                   for description in self.app.cursor.description]

                        field_index = columns.index(field_name)

                        rows = self.app.cursor.fetchall()
                        for row in rows:
                            # 品目コードを文字列に変換（ゼロパディング考慮）
                            row_list = list(row)
                            if row_list[field_index] is not None:
                                # 数値の場合、適切な桁数でゼロパディング
                                try:
                                    num_val = int(
                                        float(str(row_list[field_index])))
                                    # 品目コードは通常10桁でゼロパディング
                                    row_list[field_index] = f"{num_val:010d}"
                                except (ValueError, TypeError):
                                    row_list[field_index] = str(
                                        row_list[field_index])

                            placeholders = ','.join(['?' for _ in row_list])
                            self.app.cursor.execute(
                                f"INSERT INTO {temp_table} VALUES ({placeholders})", row_list)

                        # 元テーブルを削除して一時テーブルをリネーム
                        self.app.cursor.execute(f"DROP TABLE {table_name}")
                        self.app.cursor.execute(
                            f"ALTER TABLE {temp_table} RENAME TO {table_name}")

                        self.app.conn.commit()
                        standardized_count += 1
                        self.log_message(f"{table_name}.{field_name}: 変換完了")

                except Exception as e:
                    self.log_message(f"{table_name}.{field_name} の変換エラー: {e}")

            self.log_message(f"=== データ型統一処理完了 ===")
            self.log_message(f"チェック対象: {checked_count} フィールド")
            self.log_message(f"変換実行: {standardized_count} フィールド")

            # テーブル情報を更新
            self.refresh_table_info()
            self._update_all_tabs()

            self.app.show_message(
                f"データ型統一処理が完了しました。\nチェック対象: {checked_count} フィールド\n変換フィールド数: {standardized_count}", "info")

        except Exception as e:
            self.log_message(f"データ型統一処理エラー: {e}")
            self.app.show_message(f"データ型統一処理エラー: {e}", "error")
            import traceback
            self.log_message(traceback.format_exc())

    def analyze_data_type_consistency(self):
        """データ型の整合性分析"""
        if not self.app.conn:
            self.app.show_message("データベースに接続されていません。", "warning")
            return

        try:
            self.log_message("=== データ型整合性分析開始 ===")

            # 品目コード系フィールドの分析
            code_analysis = {}

            # テーブル一覧を取得
            self.app.cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
            tables = [row[0] for row in self.app.cursor.fetchall()]

            for table in tables:
                try:
                    # テーブル構造を取得
                    self.app.cursor.execute(f"PRAGMA table_info({table})")
                    columns = self.app.cursor.fetchall()

                    for col_info in columns:
                        col_name = col_info[1]
                        col_type = col_info[2]

                        # 品目コード系フィールドを特定
                        if any(keyword in col_name.lower() for keyword in ['品目', 'code', 'コード']):
                            key = f"{table}.{col_name}"

                            # サンプルデータを取得
                            self.app.cursor.execute(
                                f"SELECT {col_name} FROM {table} WHERE {col_name} IS NOT NULL LIMIT 5")
                            samples = [str(row[0])
                                       for row in self.app.cursor.fetchall()]

                            code_analysis[key] = {
                                'type': col_type,
                                'samples': samples
                            }

                except Exception as e:
                    self.log_message(f"テーブル {table} の分析エラー: {e}")

            # 分析結果を表示（TEXT型は除外して数値型のみ表示）
            self.log_message("\n--- 品目コード系フィールドの型分析（数値型のみ表示） ---")
            text_fields = []
            integer_fields = []
            real_fields = []

            for field, info in code_analysis.items():
                if info['type'].upper() == 'TEXT':
                    text_fields.append(field)
                elif info['type'].upper() in ['INTEGER', 'INT']:
                    integer_fields.append(field)
                    # 数値型のみログ出力
                    self.log_message(
                        f"{field}: {info['type']} - サンプル: {info['samples'][:3]}")
                elif info['type'].upper() == 'REAL':
                    real_fields.append(field)
                    # 数値型のみログ出力
                    self.log_message(
                        f"{field}: {info['type']} - サンプル: {info['samples'][:3]}")

            self.log_message(f"\nTEXT型: {len(text_fields)} フィールド（表示省略）")
            self.log_message(f"INTEGER型: {len(integer_fields)} フィールド")
            self.log_message(f"REAL型: {len(real_fields)} フィールド")

            if integer_fields:
                self.log_message("\n⚠️ 以下のフィールドはINTEGER型です（Access連携時に注意）:")
                for field in integer_fields:
                    self.log_message(f"  - {field}")

                self.log_message("\n💡 「データ型統一」ボタンで文字列型に統一できます")

            self.log_message("=== データ型整合性分析完了 ===")

        except Exception as e:
            self.log_message(f"データ型整合性分析エラー: {e}")
            import traceback
            self.log_message(traceback.format_exc())
