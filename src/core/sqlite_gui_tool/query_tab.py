"""
SQLite GUI Tool - クエリ実行タブ

SQLクエリを実行するためのタブを提供します。
"""

import tkinter as tk
from tkinter import ttk, filedialog
import sqlite3
import csv
import traceback
import datetime

try:
    import pyperclip
except ImportError:
    pyperclip = None

from .base_tab import BaseTab


class QueryTab(BaseTab):
    """
    クエリ実行タブ
    
    SQLクエリを実行し、結果を表示するタブです。
    """
    
    def __init__(self, parent, app):
        """
        初期化
        
        Args:
            parent: 親ウィジェット
            app: アプリケーションのインスタンス
        """
        super().__init__(parent, app)
        
        # 結果データ
        self.result_data = None
        self.result_columns = None
    
    def init_ui(self):
        """UIの初期化"""
        # 上部フレーム（クエリ入力エリア）
        top_frame = ttk.Frame(self.frame)
        top_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # クエリ入力ラベル
        query_label = ttk.Label(top_frame, text="SQL クエリ:")
        query_label.pack(anchor=tk.W)
        
        # クエリ入力エリア
        self.query_text = tk.Text(top_frame, height=10, wrap=tk.WORD)
        self.query_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # クエリ入力エリアのスクロールバー
        query_scrollbar = ttk.Scrollbar(
            self.query_text, orient="vertical", command=self.query_text.yview)
        self.query_text.configure(yscrollcommand=query_scrollbar.set)
        query_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # ボタンフレーム
        button_frame = ttk.Frame(self.frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        # クエリ実行ボタン
        execute_button = ttk.Button(
            button_frame, text="クエリ実行", command=self.execute_query)
        execute_button.pack(side=tk.LEFT, padx=5)
        
        # クエリクリアボタン
        clear_button = ttk.Button(
            button_frame, text="クリア", command=self.clear_query)
        clear_button.pack(side=tk.LEFT, padx=5)
        
        # クエリ例ボタン
        example_button = ttk.Button(
            button_frame, text="クエリ例", command=self.show_query_examples)
        example_button.pack(side=tk.LEFT, padx=5)
        
        # 結果コピーボタン
        self.copy_button = ttk.Button(
            button_frame, text="結果をコピー", command=self.copy_results, state="disabled")
        self.copy_button.pack(side=tk.LEFT, padx=5)
        
        # エクスポートボタン
        self.export_button = ttk.Button(
            button_frame, text="CSVエクスポート", command=self.export_results, state="disabled")
        self.export_button.pack(side=tk.LEFT, padx=5)
        
        # 結果表示ラベル
        result_label = ttk.Label(self.frame, text="実行結果:")
        result_label.pack(anchor=tk.W, pady=(10, 5))
        
        # 結果表示エリア（ツリービュー）
        result_frame = ttk.Frame(self.frame)
        result_frame.pack(fill=tk.BOTH, expand=True)
        
        # ツリービュー（表形式）で結果を表示
        self.result_tree = ttk.Treeview(result_frame)
        
        # スクロールバー
        tree_y_scrollbar = ttk.Scrollbar(
            result_frame, orient="vertical", command=self.result_tree.yview)
        tree_x_scrollbar = ttk.Scrollbar(
            result_frame, orient="horizontal", command=self.result_tree.xview)
        self.result_tree.configure(
            yscrollcommand=tree_y_scrollbar.set, xscrollcommand=tree_x_scrollbar.set)
        
        # 配置
        self.result_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree_x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 結果情報表示エリア
        self.result_info_var = tk.StringVar(value="クエリを実行してください。")
        result_info_label = ttk.Label(
            self.frame, textvariable=self.result_info_var)
        result_info_label.pack(anchor=tk.W, pady=5)
        
        # サンプルクエリ
        self.sample_queries = [
            "-- テーブル一覧を表示\nSELECT name FROM sqlite_master WHERE type='table' ORDER BY name;",
            "-- テーブルのスキーマを表示\nPRAGMA table_info(テーブル名);",
            "-- テーブルの最初の10行を表示\nSELECT * FROM テーブル名 LIMIT 10;",
            "-- カラムの値の分布を確認\nSELECT カラム名, COUNT(*) as count FROM テーブル名 GROUP BY カラム名 ORDER BY count DESC LIMIT 10;",
            "-- NULL値の数を確認\nSELECT COUNT(*) as null_count FROM テーブル名 WHERE カラム名 IS NULL;",
            "-- テーブル間の結合\nSELECT a.*, b.* FROM テーブル名1 a JOIN テーブル名2 b ON a.共通カラム = b.共通カラム LIMIT 10;"
        ]
    
    def execute_query(self):
        """クエリを実行"""
        if not self.conn:
            self.app.show_message("データベースに接続されていません。", "warning")
            return
        
        # クエリを取得
        query = self.query_text.get("1.0", tk.END).strip()
        if not query:
            self.app.show_message("クエリが入力されていません。", "warning")
            return
        
        try:
            # クエリ実行
            start_time = datetime.datetime.now()
            self.cursor.execute(query)
            
            # 結果を取得
            result = self.cursor.fetchall()
            end_time = datetime.datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            # 結果を表示
            self.display_results(result)
            
            # 実行情報を表示
            if query.strip().upper().startswith(("SELECT", "PRAGMA", "EXPLAIN")):
                self.result_info_var.set(f"実行時間: {execution_time:.6f}秒, 結果: {len(result)}行")
            else:
                self.result_info_var.set(f"実行時間: {execution_time:.6f}秒, 影響した行数: {self.cursor.rowcount}")
            
            # ボタンを有効化
            if result:
                self.copy_button.config(state="normal")
                self.export_button.config(state="normal")
            else:
                self.copy_button.config(state="disabled")
                self.export_button.config(state="disabled")
            
        except sqlite3.Error as e:
            self.app.show_message(f"クエリ実行エラー: {e}", "error")
            traceback.print_exc()
    
    def display_results(self, result):
        """
        結果を表示
        
        Args:
            result: クエリ実行結果
        """
        # 既存の結果をクリア
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)
        
        if not result:
            return
        
        # 結果を保存
        self.result_data = result
        
        # カラム名を取得
        if isinstance(result[0], sqlite3.Row):
            columns = result[0].keys()
        else:
            columns = [f"列{i+1}" for i in range(len(result[0]))]
        
        self.result_columns = columns
        
        # ツリービューの列を設定
        self.result_tree["columns"] = columns
        self.result_tree["show"] = "headings"
        
        for col in columns:
            self.result_tree.heading(col, text=col)
            self.result_tree.column(col, width=100)
        
        # データを追加
        for i, row in enumerate(result):
            if isinstance(row, sqlite3.Row):
                values = [row[col] for col in columns]
            else:
                values = row
            
            # None値を"NULL"として表示
            values = ["NULL" if v is None else v for v in values]
            
            self.result_tree.insert("", tk.END, iid=str(i), values=values)
    
    def clear_query(self):
        """クエリをクリア"""
        self.query_text.delete("1.0", tk.END)
    
    def show_query_examples(self):
        """クエリ例を表示"""
        example_window = tk.Toplevel(self.app.root)
        example_window.title("クエリ例")
        example_window.geometry("600x400")
        
        # 説明ラベル
        desc_label = ttk.Label(
            example_window, 
            text="以下のクエリ例をクリックして使用できます。",
            wraplength=580
        )
        desc_label.pack(pady=10, padx=10, anchor=tk.W)
        
        # クエリ例リストボックス
        listbox = tk.Listbox(example_window, width=80, height=15)
        listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # スクロールバー
        scrollbar = ttk.Scrollbar(listbox, orient="vertical", command=listbox.yview)
        listbox.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # クエリ例を追加
        for query in self.sample_queries:
            listbox.insert(tk.END, query.split('\n')[0])  # 最初の行（コメント）のみ表示
        
        # クエリ例選択時の処理
        def on_select(event):
            selection = listbox.curselection()
            if selection:
                index = selection[0]
                query = self.sample_queries[index]
                self.query_text.delete("1.0", tk.END)
                self.query_text.insert("1.0", query)
                example_window.destroy()
        
        listbox.bind('<<ListboxSelect>>', on_select)
        
        # 閉じるボタン
        close_button = ttk.Button(
            example_window, text="閉じる", command=example_window.destroy)
        close_button.pack(pady=10)
    
    def copy_results(self):
        """結果をクリップボードにコピー"""
        if not pyperclip:
            self.app.show_message(
                "pyperclipモジュールがインストールされていないため、コピー機能は使用できません。\n"
                "pip install pyperclipでインストールしてください。",
                "warning"
            )
            return
        
        if not self.result_data:
            return
        
        try:
            # タブ区切りのテキストを作成
            text = "\t".join(self.result_columns) + "\n"
            
            for row in self.result_data:
                if isinstance(row, sqlite3.Row):
                    values = [str(row[col]) if row[col] is not None else "NULL" for col in self.result_columns]
                else:
                    values = [str(val) if val is not None else "NULL" for val in row]
                
                text += "\t".join(values) + "\n"
            
            # クリップボードにコピー
            pyperclip.copy(text)
            self.app.show_message("結果をクリップボードにコピーしました。", "info")
            
        except Exception as e:
            self.app.show_message(f"コピーエラー: {e}", "error")
            traceback.print_exc()
    
    def export_results(self):
        """結果をCSVファイルにエクスポート"""
        if not self.result_data:
            return
        
        # ファイル選択ダイアログ
        file_path = filedialog.asksaveasfilename(
            title="CSVファイルを保存",
            filetypes=[("CSVファイル", "*.csv"), ("すべてのファイル", "*.*")],
            defaultextension=".csv"
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                
                # ヘッダー行を書き込み
                writer.writerow(self.result_columns)
                
                # データ行を書き込み
                for row in self.result_data:
                    if isinstance(row, sqlite3.Row):
                        values = [row[col] if row[col] is not None else "" for col in self.result_columns]
                    else:
                        values = [val if val is not None else "" for val in row]
                    
                    writer.writerow(values)
            
            self.app.show_message(f"結果を {file_path} にエクスポートしました。", "info")
            
        except Exception as e:
            self.app.show_message(f"エクスポートエラー: {e}", "error")
            traceback.print_exc()