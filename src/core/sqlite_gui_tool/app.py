"""
SQLite GUI Tool - メインアプリケーションクラス

アプリケーションのメインクラスを提供します。
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sqlite3
import os
import sys
import json
import time
from pathlib import Path
import traceback

# タブのインポート
from .query_tab import QueryTab
from .schema_tab import SchemaTab
from .import_tab import ImportTab
from .export_tab import ExportTab
from .analyze_tab import AnalyzeTab
from .code_converter_tab import CodeConverterTab
from .admin_tab import AdminTab
from .launcher_tab import LauncherTab

# プロジェクトルートを特定
GUI_TOOL_DIR = Path(os.path.abspath(os.path.dirname(__file__)))
GUI_PROJECT_ROOT = GUI_TOOL_DIR.parents[2]  # src/core/sqlite_gui_tool の2つ上の階層

# プロジェクトルートをsys.pathに追加
if str(GUI_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(GUI_PROJECT_ROOT))

try:
    # SQLiteManagerをインポート（簡易版）
    from src.core.sqlite_manager_wrapper import SQLiteManager
    
    # Paths クラスの定義
    class Paths:
        def __init__(self):
            self.PROJECT_ROOT = GUI_PROJECT_ROOT
            self.LOGS = self.PROJECT_ROOT / 'logs'
            self.RAW_DATA = self.PROJECT_ROOT / 'data' / 'raw'
            self.SQLITE_DB = self.PROJECT_ROOT / 'data' / 'sqlite' / 'main.db'

except ImportError as e:
    SQLiteManager = None
    
    class Paths:
        def __init__(self):
            self.PROJECT_ROOT = GUI_PROJECT_ROOT
            self.LOGS = self.PROJECT_ROOT / 'logs'
            self.RAW_DATA = self.PROJECT_ROOT / 'data' / 'raw'
            self.SQLITE_DB = self.PROJECT_ROOT / 'data' / 'sqlite' / 'main.db'
    
    print(f"警告: SQLiteManagerのインポートに失敗しました。一部機能が制限されます。エラー: {e}")
    print(traceback.format_exc())


class SQLiteGUITool:
    """
    SQLite GUI Toolのメインアプリケーションクラス
    """
    
    def __init__(self, root):
        """
        初期化
        
        Args:
            root: Tkinterのルートウィンドウ
        """
        self.root = root
        self.root.title("SQLite GUI Tool v2")
        self.root.geometry("1200x800")
        
        # データベース接続
        self.conn = None
        self.cursor = None
        self.db_path = None
        
        # メインフレーム
        self.main_frame = ttk.Frame(root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # タブコントロール
        self.tab_control = ttk.Notebook(self.main_frame)
        
        # タブの作成
        self.tabs = {}
        self.init_tabs()
        
        self.tab_control.pack(expand=1, fill="both")
        
        # ステータスバー
        self.status_var = tk.StringVar()
        self.status_var.set("データベースが接続されていません")
        self.status_bar = ttk.Label(
            root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # データベース接続ボタン
        self.connect_button = ttk.Button(
            self.main_frame, text="データベース接続", command=self.connect_database)
        self.connect_button.pack(side=tk.TOP, pady=5)
        
        # デフォルトのデータベースパスを設定
        self.default_db_path = Paths().PROJECT_ROOT / 'data' / 'sqlite' / 'main.db'
        
        # SQLiteManagerのインスタンス
        try:
            self.sqlite_manager = SQLiteManager() if SQLiteManager else None
        except Exception as e:
            print(f"SQLiteManager初期化エラー: {e}")
            self.sqlite_manager = None
        
        # 前回のデータベースパスを読み込み
        last_db_path = self._load_db_path()
        if last_db_path and os.path.exists(last_db_path):
            # 自動接続（遅延実行）
            self.root.after(500, lambda: self._connect_to_db(last_db_path))
    
    def init_tabs(self):
        """タブの初期化"""
        # クエリ実行タブ
        query_tab_frame = ttk.Frame(self.tab_control)
        self.tabs['query'] = QueryTab(query_tab_frame, self)
        self.tab_control.add(query_tab_frame, text='クエリ実行')
        
        # スキーマタブ
        schema_tab_frame = ttk.Frame(self.tab_control)
        self.tabs['schema'] = SchemaTab(schema_tab_frame, self)
        self.tab_control.add(schema_tab_frame, text='スキーマ')
        
        # インポートタブ
        import_tab_frame = ttk.Frame(self.tab_control)
        self.tabs['import'] = ImportTab(import_tab_frame, self)
        self.tab_control.add(import_tab_frame, text='インポート')
        
        # エクスポートタブ
        export_tab_frame = ttk.Frame(self.tab_control)
        self.tabs['export'] = ExportTab(export_tab_frame, self)
        self.tab_control.add(export_tab_frame, text='エクスポート')
        
        # データ分析タブ
        analyze_tab_frame = ttk.Frame(self.tab_control)
        self.tabs['analyze'] = AnalyzeTab(analyze_tab_frame, self)
        self.tab_control.add(analyze_tab_frame, text='データ分析')
        
        # コードフィールド変換タブ
        code_converter_tab_frame = ttk.Frame(self.tab_control)
        self.tabs['code_converter'] = CodeConverterTab(code_converter_tab_frame, self)
        self.tab_control.add(code_converter_tab_frame, text='コードフィールド変換')
        
        # 管理タブ
        admin_tab_frame = ttk.Frame(self.tab_control)
        self.tabs['admin'] = AdminTab(admin_tab_frame, self)
        self.tab_control.add(admin_tab_frame, text='DB管理')
        
        # ランチャータブ
        launcher_tab_frame = ttk.Frame(self.tab_control)
        self.tabs['launcher'] = LauncherTab(launcher_tab_frame, self)
        self.tab_control.add(launcher_tab_frame, text='スクリプト実行')
    
    def connect_database(self):
        """データベース接続"""
        # ファイル選択ダイアログ
        db_path = filedialog.askopenfilename(
            title="SQLiteデータベースを選択",
            filetypes=[("SQLiteデータベース", "*.db *.sqlite *.sqlite3"), ("すべてのファイル", "*.*")],
            initialdir=os.path.dirname(self.default_db_path)
        )
        
        if not db_path:
            return
        
        self._connect_to_db(db_path)
    
    def _connect_to_db(self, db_path):
        """指定されたパスのデータベースに接続"""
        try:
            # 既存の接続を閉じる
            self.close_connection()
            
            # 新しい接続を開く
            self.conn = sqlite3.connect(db_path)
            self.conn.row_factory = sqlite3.Row
            self.cursor = self.conn.cursor()
            
            # データベースパスを保存
            self.db_path = db_path
            
            # 設定ファイルに保存
            self._save_db_path(db_path)
            
            # ステータスバーを更新
            self.status_var.set(f"接続済み: {os.path.basename(db_path)}")
            
            # 各タブに接続を通知
            for tab in self.tabs.values():
                tab.on_db_connect(self.conn, self.cursor)
            
            # 管理タブを表示して、テーブル情報を更新
            if 'admin' in self.tabs:
                self.tab_control.select(self.tab_control.index(self.tabs['admin'].parent))
                self.tabs['admin'].refresh_table_info()
            
            # 成功メッセージ
            self.show_message(f"データベース '{os.path.basename(db_path)}' に接続しました。", "info")
            
        except sqlite3.Error as e:
            self.show_message(f"データベース接続エラー: {e}", "error")
            traceback.print_exc()
    
    def _save_db_path(self, path):
        """データベースパスを設定ファイルに保存"""
        config_file = "db_config.json"
        try:
            with open(config_file, "w") as f:
                json.dump({"last_db_path": path}, f)
        except Exception as e:
            self.show_message(f"設定ファイル保存エラー: {e}", "warning")
    
    def _load_db_path(self):
        """設定ファイルからデータベースパスを読み込み"""
        config_file = "db_config.json"
        if os.path.exists(config_file):
            try:
                with open(config_file, "r") as f:
                    return json.load(f).get("last_db_path", "")
            except Exception:
                return ""
        return ""
    
    def close_connection(self):
        """データベース接続を閉じる"""
        if self.conn:
            try:
                # 保留中のトランザクションをコミット
                try:
                    self.conn.commit()
                except:
                    pass
                
                # 接続を閉じる
                self.conn.close()
                
                # 各タブに切断を通知
                for tab in self.tabs.values():
                    tab.on_db_disconnect()
                
                # ジャーナルファイルの削除を試みる
                if self.db_path:
                    journal_file = f"{self.db_path}-journal"
                    if os.path.exists(journal_file):
                        try:
                            os.remove(journal_file)
                            print(f"ジャーナルファイルを削除しました: {journal_file}")
                        except Exception as e:
                            print(f"ジャーナルファイル削除エラー: {e}")
                
            except sqlite3.Error as e:
                self.show_message(f"データベース切断エラー: {e}", "error")
            
            self.conn = None
            self.cursor = None
            self.db_path = None
    
    def show_message(self, message, message_type="info"):
        """
        メッセージを表示
        
        Args:
            message: 表示するメッセージ
            message_type: メッセージの種類（"info", "warning", "error"）
        """
        if message_type == "info":
            messagebox.showinfo("情報", message)
        elif message_type == "warning":
            messagebox.showwarning("警告", message)
        elif message_type == "error":
            messagebox.showerror("エラー", message)
        
        # ステータスバーにも表示
        self.status_var.set(message)
    
    def refresh_all_tabs(self):
        """すべてのタブを更新"""
        for tab in self.tabs.values():
            tab.refresh()
    
    def get_table_list(self):
        """
        テーブル一覧を取得
        
        Returns:
            list: テーブル名のリスト
        """
        if not self.conn:
            return []
        
        try:
            self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            return [row[0] for row in self.cursor.fetchall()]
        except sqlite3.Error:
            return []
            
    # 各タブから呼び出されるメソッド
    def on_table_select(self, event):
        """テーブル選択時の処理"""
        # スキーマタブからの呼び出し
        tab = self.tabs.get('schema')
        if not tab or not self.conn:
            return
            
        # 選択されたテーブルを取得
        selection = tab.table_listbox.curselection()
        if not selection:
            return
            
        table_name = tab.table_listbox.get(selection[0])
        
        try:
            # テーブル名を表示
            tab.table_name_var.set(table_name)
            
            # テーブル統計情報を取得
            self.cursor.execute(f"SELECT COUNT(*) FROM '{table_name}'")
            row_count = self.cursor.fetchone()[0]
            
            # カラム情報を取得
            self.cursor.execute(f"PRAGMA table_info('{table_name}')")
            columns = self.cursor.fetchall()
            column_count = len(columns)
            
            # 統計情報を表示
            tab.table_stats_var.set(f"行数: {row_count}, カラム数: {column_count}")
            
            # カラム情報をツリービューに表示
            for item in tab.column_tree.get_children():
                tab.column_tree.delete(item)
                
            for col in columns:
                cid, name, type_, not_null, default_val, pk = col
                tab.column_tree.insert("", "end", values=(cid, name, type_, not_null, default_val, pk))
                
            # インデックス情報を取得
            self.cursor.execute(f"PRAGMA index_list('{table_name}')")
            indexes = self.cursor.fetchall()
            
            # インデックス情報をツリービューに表示
            for item in tab.index_tree.get_children():
                tab.index_tree.delete(item)
                
            for idx in indexes:
                idx_name = idx[1]
                is_unique = "Yes" if idx[2] else "No"
                
                try:
                    # インデックスのカラム情報を取得
                    self.cursor.execute(f"PRAGMA index_info('{idx_name}')")
                    idx_columns = self.cursor.fetchall()
                    
                    # カラム名を取得
                    column_names = []
                    for col in idx_columns:
                        col_index = col[1]  # カラムのインデックス
                        if col_index is not None and col_index < len(columns):
                            column_names.append(columns[col_index][1])  # カラム名
                    
                    columns_str = ", ".join(column_names) if column_names else "Unknown"
                    
                    tab.index_tree.insert("", "end", values=(idx_name, is_unique, columns_str))
                    
                except Exception as e:
                    # エラーが発生した場合はスキップ
                    tab.index_tree.insert("", "end", values=(idx_name, is_unique, "Error"))
                
            # ボタンを有効化
            tab.show_sql_button.config(state="normal")
            tab.show_sample_button.config(state="normal")
            
        except Exception as e:
            self.show_message(f"テーブル情報の取得エラー: {e}", "error")
            
    def show_create_sql(self):
        """CREATE TABLE SQL文を表示"""
        tab = self.tabs.get('schema')
        if not tab or not self.conn:
            return
            
        # 選択されたテーブルを取得
        selection = tab.table_listbox.curselection()
        if not selection:
            return
            
        table_name = tab.table_listbox.get(selection[0])
        
        try:
            # CREATE TABLE文を取得
            self.cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}'")
            sql = self.cursor.fetchone()[0]
            
            # 結果表示ウィンドウを作成
            sql_window = tk.Toplevel(self.root)
            sql_window.title(f"CREATE TABLE {table_name}")
            sql_window.geometry("600x400")
            
            # SQL表示エリア
            sql_text = tk.Text(sql_window, wrap=tk.WORD)
            sql_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # SQLを表示
            sql_text.insert("1.0", sql)
            
            # 閉じるボタン
            close_button = ttk.Button(sql_window, text="閉じる", command=sql_window.destroy)
            close_button.pack(pady=10)
            
        except Exception as e:
            self.show_message(f"SQL取得エラー: {e}", "error")
            
    def show_sample_data(self):
        """サンプルデータを表示"""
        tab = self.tabs.get('schema')
        if not tab or not self.conn:
            return
            
        # 選択されたテーブルを取得
        selection = tab.table_listbox.curselection()
        if not selection:
            return
            
        table_name = tab.table_listbox.get(selection[0])
        
        try:
            # サンプルデータを取得（最大100行）
            self.cursor.execute(f"SELECT * FROM '{table_name}' LIMIT 100")
            rows = self.cursor.fetchall()
            
            if not rows:
                self.show_message(f"テーブル {table_name} にデータがありません。", "info")
                return
                
            # カラム名を取得
            columns = [description[0] for description in self.cursor.description]
            
            # 結果表示ウィンドウを作成
            data_window = tk.Toplevel(self.root)
            data_window.title(f"サンプルデータ: {table_name}")
            data_window.geometry("800x600")
            
            # ツリービューの作成
            tree_frame = ttk.Frame(data_window)
            tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            tree = ttk.Treeview(tree_frame, columns=columns, show="headings")
            
            # カラムの設定
            for col in columns:
                tree.heading(col, text=col)
                tree.column(col, width=100)
                
            # スクロールバー
            y_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
            x_scrollbar = ttk.Scrollbar(tree_frame, orient="horizontal", command=tree.xview)
            tree.configure(yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set)
            
            # 配置
            tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
            
            # データを追加
            for row in rows:
                values = [str(val) if val is not None else "NULL" for val in row]
                tree.insert("", "end", values=values)
                
            # 閉じるボタン
            close_button = ttk.Button(data_window, text="閉じる", command=data_window.destroy)
            close_button.pack(pady=10)
            
        except Exception as e:
            self.show_message(f"データ取得エラー: {e}", "error")
            
    def preview_import_data(self):
        """インポートデータのプレビュー"""
        tab = self.tabs.get('import')
        if not tab:
            return
        
        # インポートタブのプレビュー機能を呼び出し
        tab.preview_import_data()
        
    def execute_import(self):
        """インポートを実行"""
        tab = self.tabs.get('import')
        if not tab or not self.conn:
            return
        
        file_path = tab.import_path_var.get()
        if not file_path or not os.path.exists(file_path):
            self.show_message("有効なファイルパスを入力してください。", "warning")
            return
        
        table_name = tab.table_name_entry_var.get()
        if not table_name:
            self.show_message("テーブル名を入力してください。", "warning")
            return
        
        try:
            # テーブル名をサニタイズ
            sanitized_table_name = tab.sanitize_table_name(table_name)
            
            # ファイル情報を取得
            file_type = tab.file_type_var.get()
            encoding = tab.encoding_var.get()
            delimiter = tab.delimiter_var.get()
            header = 0 if tab.header_var.get() else None
            if_exists = tab.existing_var.get()
            
            # if_existsを変換
            if if_exists == "置換":
                if_exists = "replace"
            elif if_exists == "追加":
                if_exists = "append"
            elif if_exists == "エラー":
                if_exists = "fail"
            
            # ファイルタイプの自動検出
            if file_type == "自動検出":
                ext = os.path.splitext(file_path)[1].lower()
                if ext == '.csv':
                    file_type = "CSV"
                elif ext in ['.tsv', '.txt']:
                    file_type = "TSV"
                elif ext in ['.xlsx', '.xls']:
                    file_type = "Excel"
                else:
                    file_type = "CSV"
            
            # エンコーディングの自動検出（改良版）
            if encoding == "自動検出":
                encoding = self._detect_encoding_robust(file_path)
            
            # 区切り文字の自動検出（改良版）
            if delimiter == "自動検出":
                delimiter = self._detect_delimiter_robust(file_path, encoding)
            elif delimiter == "\\t":
                delimiter = "\t"
            
            # データを読み込み
            if file_type in ["CSV", "TSV"]:
                import pandas as pd
                try:
                    df = pd.read_csv(
                        file_path, 
                        sep=delimiter, 
                        encoding=encoding, 
                        header=header,
                        dtype=str,
                        on_bad_lines='skip',
                        engine='python'
                    )
                except Exception as e:
                    # エラー時のフォールバック
                    df = pd.read_csv(
                        file_path, 
                        sep=delimiter, 
                        encoding='latin-1', 
                        header=header,
                        dtype=str,
                        on_bad_lines='skip',
                        engine='python'
                    )
            elif file_type == "Excel":
                import pandas as pd
                df = pd.read_excel(file_path, header=header, dtype=str)
            else:
                self.show_message(f"サポートされていないファイルタイプです: {file_type}", "error")
                return
            
            # データ型最適化を適用
            df = self._optimize_dataframe_dtypes(df)
            
            # データをSQLiteに保存
            df.to_sql(sanitized_table_name, self.conn, if_exists=if_exists, index=False)
            self.conn.commit()
            
            # 結果を表示
            row_count = len(df)
            tab.import_result_var.set(f"{row_count:,}行のデータを '{sanitized_table_name}' テーブルにインポートしました。")
            
            # 成功メッセージ
            self.show_message(f"{row_count:,}行のデータを '{sanitized_table_name}' テーブルにインポートしました。", "info")
            
            # 他のタブを更新
            self.refresh_all_tabs()
            
        except Exception as e:
            self.show_message(f"インポートエラー: {e}", "error")
            tab.import_result_var.set(f"エラー: {e}")
            import traceback
            print(traceback.format_exc())
    
    def _detect_encoding_robust(self, file_path):
        """より確実なエンコーディング検出"""
        import chardet
        
        # 複数の方法でエンコーディングを試行
        encodings_to_try = ['cp932', 'shift_jis', 'utf-8', 'euc-jp', 'iso-2022-jp']
        
        # chardetによる検出
        try:
            with open(file_path, 'rb') as f:
                raw_data = f.read(50000)  # より多くのデータを読み込み
                result = chardet.detect(raw_data)
                detected_encoding = result['encoding']
                confidence = result['confidence']
                
                # 信頼度が高い場合は使用
                if confidence > 0.7 and detected_encoding:
                    # 日本語ファイルの場合はcp932を優先
                    if detected_encoding.lower() in ['shift_jis', 'shift-jis']:
                        return 'cp932'
                    return detected_encoding
        except:
            pass
        
        # 各エンコーディングで実際に読み込みテスト
        for encoding in encodings_to_try:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    # 最初の1000文字を読んでみる
                    test_data = f.read(1000)
                    # 日本語文字が含まれているかチェック
                    if any('\u3040' <= c <= '\u309F' or '\u30A0' <= c <= '\u30FF' or '\u4E00' <= c <= '\u9FAF' for c in test_data):
                        return encoding
                    # 文字化けしていないかチェック
                    if '?' not in test_data and '�' not in test_data:
                        return encoding
            except (UnicodeDecodeError, UnicodeError):
                continue
        
        # デフォルトはcp932
        return 'cp932'
    
    def _detect_delimiter_robust(self, file_path, encoding):
        """より確実な区切り文字検出"""
        import csv
        
        # 区切り文字の候補
        delimiters = [',', '\t', ';', '|', ' ']
        
        try:
            # ファイルの最初の数行を読み込み
            with open(file_path, 'r', encoding=encoding) as f:
                sample_lines = []
                for i, line in enumerate(f):
                    if i >= 10:  # 最初の10行まで
                        break
                    sample_lines.append(line.strip())
                
                if not sample_lines:
                    return ','
                
                # 各区切り文字での分割結果を評価
                best_delimiter = ','
                max_columns = 1
                
                for delimiter in delimiters:
                    # 各行での分割数をチェック
                    column_counts = []
                    for line in sample_lines:
                        if line:  # 空行をスキップ
                            parts = line.split(delimiter)
                            column_counts.append(len(parts))
                    
                    if column_counts:
                        # 分割数の一貫性をチェック
                        avg_columns = sum(column_counts) / len(column_counts)
                        max_count = max(column_counts)
                        
                        # 2列以上で、かつ一貫性がある場合
                        if max_count > 1 and avg_columns > max_columns:
                            # 分割数のばらつきをチェック
                            variance = sum((count - avg_columns) ** 2 for count in column_counts) / len(column_counts)
                            if variance < 2:  # ばらつきが小さい場合
                                max_columns = avg_columns
                                best_delimiter = delimiter
                
                # CSV Snifferも試行
                try:
                    sample_text = '\n'.join(sample_lines[:5])
                    sniffer = csv.Sniffer()
                    dialect = sniffer.sniff(sample_text, delimiters=',\t;|')
                    detected_delimiter = dialect.delimiter
                    
                    # Snifferの結果も考慮
                    if detected_delimiter in delimiters:
                        # Snifferの結果での分割数をチェック
                        test_columns = len(sample_lines[0].split(detected_delimiter)) if sample_lines else 1
                        if test_columns > max_columns:
                            best_delimiter = detected_delimiter
                except:
                    pass
                
                return best_delimiter
                
        except Exception as e:
            print(f"区切り文字検出エラー: {e}")
            return ','
    
    def _optimize_dataframe_dtypes(self, df):
        """DataFrameのデータ型を最適化（インポートタブ用）"""
        import pandas as pd
        import numpy as np
        
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
        
        # 品目コード系のパターン（先頭0保持が必要）
        item_code_patterns = ['品目', 'item', 'material', '部品', 'part', '製品', 'product']
        
        for col in df.columns:
            col_lower = str(col).lower()
            
            # 空の列はスキップ
            if df[col].empty:
                continue
            
            # サンプルデータを取得（最大1000行）
            sample = df[col].dropna().head(1000)
            if len(sample) == 0:
                continue
            
            # SAP後ろマイナス処理を適用
            df[col] = df[col].apply(self._process_sap_trailing_minus)
            
            # 日付列の処理
            is_date_column = any(pattern in col_lower for pattern in date_column_patterns)
            
            if is_date_column:
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
                    pass
            
            # 数値列の処理
            elif any(pattern in col_lower for pattern in numeric_column_patterns):
                try:
                    # 数値変換を試行
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                except Exception as e:
                    pass
            
            # 品目コード系の処理
            elif any(pattern in col_lower for pattern in item_code_patterns):
                # 品目コードは文字列として保持
                df[col] = df[col].astype(str)
            
            # その他の列の自動判定
            else:
                # 数値として解釈できるかチェック
                try:
                    # サンプルの90%以上が数値として変換可能な場合
                    numeric_sample = pd.to_numeric(sample, errors='coerce')
                    valid_numeric_ratio = (~numeric_sample.isna()).mean()
                    
                    if valid_numeric_ratio >= 0.9:
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
                        df[col] = pd.to_datetime(df[col], errors='coerce')
                        continue
                except:
                    pass
        
        return df
    
    def _process_sap_trailing_minus(self, value):
        """SAP後ろマイナス表記を処理する"""
        if isinstance(value, str) and value.endswith('-'):
            return f"-{value[:-1]}"
        return value
        
    def preview_export_data(self):
        """エクスポートデータのプレビュー"""
        tab = self.tabs.get('export')
        if not tab:
            return
            
        self.show_message("エクスポート機能は現在実装中です。", "info")
        
    def execute_export(self):
        """エクスポートを実行"""
        tab = self.tabs.get('export')
        if not tab:
            return
            
        self.show_message("エクスポート機能は現在実装中です。", "info")
        
    def on_analyze_table_select(self, event):
        """分析タブでテーブル選択時の処理"""
        tab = self.tabs.get('analyze')
        if not tab or not self.conn:
            return
            
        # 選択されたテーブルを取得
        table_name = tab.analyze_table_var.get()
        if not table_name:
            return
            
        try:
            # カラム一覧を取得
            self.cursor.execute(f"PRAGMA table_info('{table_name}')")
            columns = [row[1] for row in self.cursor.fetchall()]
            
            # カラム一覧を更新
            tab.analyze_column_combo['values'] = columns
            if columns:
                tab.analyze_column_var.set(columns[0])
                
        except Exception as e:
            self.show_message(f"カラム情報の取得エラー: {e}", "error")
            
    def execute_analysis(self):
        """データ分析を実行"""
        tab = self.tabs.get('analyze')
        if not tab or not self.conn:
            return
            
        self.show_message("データ分析機能は現在実装中です。", "info")
        
    def analyze_code_fields(self):
        """コードフィールドを分析"""
        tab = self.tabs.get('code_converter')
        if not tab or not self.conn:
            return
            
        table_name = tab.converter_table_var.get()
        if not table_name:
            self.show_message("テーブルを選択してください。", "warning")
            return
            
        try:
            # テーブルの列情報を取得
            self.cursor.execute(f"PRAGMA table_info('{table_name}')")
            columns = self.cursor.fetchall()
            
            # 分析結果をクリア
            for item in tab.code_field_tree.get_children():
                tab.code_field_tree.delete(item)
            
            for col_info in columns:
                col_name = col_info[1]
                col_type = col_info[2]
                
                # サンプルデータを取得（カラム名をエスケープ）
                self.cursor.execute(f"SELECT DISTINCT [{col_name}] FROM [{table_name}] WHERE [{col_name}] IS NOT NULL LIMIT 10")
                samples = [str(row[0]) for row in self.cursor.fetchall()]
                sample_str = ", ".join(samples[:3]) + ("..." if len(samples) > 3 else "")
                
                # コードフィールドかどうかを判定
                code_type, should_convert = self._analyze_code_field(table_name, col_name, col_type)
                
                # ツリービューに追加
                convert_text = "✓" if should_convert else ""
                tab.code_field_tree.insert("", "end", values=(
                    col_name, col_type, sample_str, code_type, convert_text
                ))
                
        except Exception as e:
            self.show_message(f"コードフィールド分析エラー: {e}", "error")
            
    def _analyze_code_field(self, table_name, col_name, col_type):
        """個別のフィールドがコードフィールドかどうかを分析"""
        try:
            # サンプルデータを取得（最大1000行）（カラム名をエスケープ）
            self.cursor.execute(f"SELECT [{col_name}] FROM [{table_name}] WHERE [{col_name}] IS NOT NULL LIMIT 1000")
            values = [str(row[0]) for row in self.cursor.fetchall()]
            
            if not values:
                return "データなし", False
            
            # カラム名を小文字に変換して分析
            col_name_lower = col_name.lower()
            
            # 品目コード系のカラムかチェック
            item_code_patterns = ['品目', 'item', 'material', '部品', 'part', '製品', 'product']
            is_item_code = any(pattern in col_name_lower for pattern in item_code_patterns)
            
            # 数値として格納されているが、実際はコードの可能性をチェック
            numeric_values = []
            for val in values:
                try:
                    numeric_values.append(float(val))
                except:
                    pass
            
            # すべて数値として解釈可能な場合
            if len(numeric_values) == len(values):
                # 先頭ゼロの可能性をチェック
                zero_padded_count = sum(1 for val in values if val.startswith('0') and len(val) > 1)
                
                if zero_padded_count > len(values) * 0.1:  # 10%以上が先頭ゼロ
                    if is_item_code:
                        # 品目コードの場合は文字列として保持
                        return "品目コード（先頭0保持）", True
                    else:
                        # その他の場合はSAPゼロパディング（先頭0除去）
                        return "SAPゼロパディング（先頭0除去）", True
                
                # 固定長の可能性をチェック
                lengths = [len(val) for val in values]
                if len(set(lengths)) <= 2:  # 長さが1-2種類のみ
                    avg_length = sum(lengths) / len(lengths)
                    if avg_length >= 4:  # 平均4文字以上
                        if is_item_code:
                            return "品目コード（固定長）", True
                        else:
                            return "固定長ID（数値変換可）", False
                
                # 連続性のチェック
                sorted_nums = sorted(numeric_values)
                gaps = [sorted_nums[i+1] - sorted_nums[i] for i in range(len(sorted_nums)-1)]
                if gaps and max(gaps) > 1000:  # 大きなギャップがある
                    if is_item_code:
                        return "品目コード（非連続）", True
                    else:
                        return "非連続ID（数値変換可）", False
                        
                return "数値", False
            
            # 文字列の場合
            else:
                # 英数字コードの可能性
                alphanumeric_count = sum(1 for val in values if val.isalnum())
                if alphanumeric_count > len(values) * 0.8:  # 80%以上が英数字
                    return "英数字コード", False  # 既に文字列なので変換不要
                
                return "文字列", False
                
        except Exception as e:
            return f"分析エラー: {e}", False
            
    def execute_conversion(self):
        """コード変換を実行"""
        import time
        
        tab = self.tabs.get('code_converter')
        if not tab or not self.conn:
            return
            
        table_name = tab.converter_table_var.get()
        if not table_name:
            self.show_message("テーブルを選択してください。", "warning")
            return
            
        # 変換対象のフィールドを取得
        convert_fields = []
        for item in tab.code_field_tree.get_children():
            values = tab.code_field_tree.item(item, "values")
            if values[4] == "✓":  # 変換フラグがチェックされている
                convert_fields.append({
                    'column': values[0],
                    'type': values[1],
                    'code_type': values[3]
                })
        
        if not convert_fields:
            self.show_message("変換対象のフィールドが選択されていません。", "warning")
            return
            
        try:
            # バックアップの作成（構造も含めて完全コピー）
            if tab.backup_var.get():
                backup_table = f"{table_name}_backup_{int(time.time())}"
                
                # 元のテーブル構造を取得
                self.cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}'")
                create_sql = self.cursor.fetchone()[0]
                
                # バックアップテーブル用にCREATE文を修正
                backup_create_sql = create_sql.replace(f'"{table_name}"', f'"{backup_table}"')
                backup_create_sql = backup_create_sql.replace(f"'{table_name}'", f"'{backup_table}'")
                backup_create_sql = backup_create_sql.replace(f"[{table_name}]", f"[{backup_table}]")
                backup_create_sql = backup_create_sql.replace(f" {table_name} ", f" {backup_table} ")
                
                # バックアップテーブルを作成
                self.cursor.execute(backup_create_sql)
                
                # データをコピー
                self.cursor.execute(f"INSERT INTO [{backup_table}] SELECT * FROM [{table_name}]")
                
                # ログ出力（admin_tabのlog_messageメソッドを使用）
                if 'admin' in self.tabs:
                    self.tabs['admin'].log_message(f"バックアップテーブルを作成しました: {backup_table}")
                self.conn.commit()
                
            converted_count = 0
            
            # テーブル再作成による型変換
            if convert_fields:
                # 元のテーブル構造を取得
                self.cursor.execute(f"PRAGMA table_info([{table_name}])")
                original_columns = self.cursor.fetchall()
                
                # 新しいテーブル構造を作成
                new_columns = []
                for col_info in original_columns:
                    col_id, col_name, col_type, not_null, default_val, pk = col_info
                    
                    # 変換対象のカラムかチェック
                    convert_field = None
                    for field in convert_fields:
                        if field['column'] == col_name:
                            convert_field = field
                            break
                    
                    if convert_field:
                        code_type = convert_field['code_type']
                        if code_type in ["品目コード（先頭0保持）", "品目コード（固定長）", "品目コード（非連続）"]:
                            # 品目コードは文字列として保持
                            new_type = "TEXT"
                        elif code_type in ["SAPゼロパディング（先頭0除去）"]:
                            # ゼロパディング除去して数値型
                            new_type = "INTEGER"
                        else:
                            # その他のコード変換
                            new_type = "TEXT"
                        converted_count += 1
                    else:
                        new_type = col_type
                    
                    # カラム定義を作成
                    col_def = f"[{col_name}] {new_type}"
                    if not_null:
                        col_def += " NOT NULL"
                    if default_val is not None:
                        col_def += f" DEFAULT {default_val}"
                    if pk:
                        col_def += " PRIMARY KEY"
                    
                    new_columns.append(col_def)
                
                # 新しいテーブルを作成
                temp_table = f"{table_name}_temp_{int(time.time())}"
                create_sql = f"CREATE TABLE [{temp_table}] ({', '.join(new_columns)})"
                self.cursor.execute(create_sql)
                
                # データをコピー（型変換を適用）
                column_names = [col[1] for col in original_columns]
                select_columns = []
                
                for col_name in column_names:
                    convert_field = None
                    for field in convert_fields:
                        if field['column'] == col_name:
                            convert_field = field
                            break
                    
                    if convert_field:
                        code_type = convert_field['code_type']
                        if code_type in ["品目コード（先頭0保持）", "品目コード（固定長）", "品目コード（非連続）"]:
                            # 品目コードは文字列として保持（ゼロパディング保持）
                            select_columns.append(f"CAST([{col_name}] AS TEXT) AS [{col_name}]")
                        elif code_type in ["SAPゼロパディング（先頭0除去）"]:
                            # ゼロパディング除去して数値変換（空文字対策）
                            select_columns.append(f"CAST(CASE WHEN LTRIM([{col_name}], '0') = '' THEN '0' ELSE LTRIM([{col_name}], '0') END AS INTEGER) AS [{col_name}]")
                        else:
                            # その他のコード変換
                            select_columns.append(f"CAST([{col_name}] AS TEXT) AS [{col_name}]")
                    else:
                        select_columns.append(f"[{col_name}]")
                
                insert_sql = f"""
                INSERT INTO [{temp_table}] 
                SELECT {', '.join(select_columns)} 
                FROM [{table_name}]
                """
                self.cursor.execute(insert_sql)
                
                # 元のテーブルを削除
                self.cursor.execute(f"DROP TABLE [{table_name}]")
                
                # 新しいテーブルを元の名前にリネーム
                self.cursor.execute(f"ALTER TABLE [{temp_table}] RENAME TO [{table_name}]")
            
            self.conn.commit()
            
            tab.conversion_result_var.set(f"{converted_count} 個のフィールドを変換しました。")
            self.show_message(f"コード変換が完了しました。{converted_count} 個のフィールドを変換しました。", "info")
            
        except Exception as e:
            self.conn.rollback()
            self.show_message(f"コード変換エラー: {e}", "error")
            tab.conversion_result_var.set(f"変換エラー: {e}")