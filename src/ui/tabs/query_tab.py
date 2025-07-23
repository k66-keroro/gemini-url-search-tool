"""
クエリ実行タブ
SQLクエリの実行と結果表示を行う
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import sqlite3
from typing import Optional, List, Dict, Any

from .base_tab import BaseTab
from ..components.data_table import DataTable
from ..components.message_box import MessageBox
from ...core.db_connection import DatabaseConnection
from ...utils.error_handler import ErrorHandler
from ...utils.logger import Logger


class QueryTab(BaseTab):
    """SQLクエリ実行タブ"""
    
    def __init__(self, parent, db_connection: DatabaseConnection):
        super().__init__(parent, "クエリ")
        self.db_connection = db_connection
        self.logger = Logger.get_logger(__name__)
        self.error_handler = ErrorHandler()
        
        # クエリ履歴
        self.query_history: List[str] = []
        self.history_index = -1
        
        self._create_widgets()
        self._setup_bindings()
        
    def _create_widgets(self):
        """ウィジェットの作成"""
        # メインフレーム
        main_frame = ttk.Frame(self.frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 上部: クエリ入力エリア
        query_frame = ttk.LabelFrame(main_frame, text="SQLクエリ", padding=5)
        query_frame.pack(fill=tk.BOTH, expand=False, pady=(0, 5))
        
        # クエリテキストエリア
        self.query_text = scrolledtext.ScrolledText(
            query_frame,
            height=8,
            wrap=tk.WORD,
            font=('Consolas', 10)
        )
        self.query_text.pack(fill=tk.BOTH, expand=True)
        
        # ボタンフレーム
        button_frame = ttk.Frame(query_frame)
        button_frame.pack(fill=tk.X, pady=(5, 0))
        
        # 実行ボタン
        self.execute_btn = ttk.Button(
            button_frame,
            text="実行 (Ctrl+Enter)",
            command=self.execute_query
        )
        self.execute_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # クリアボタン
        self.clear_btn = ttk.Button(
            button_frame,
            text="クリア",
            command=self.clear_query
        )
        self.clear_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # 履歴ボタン
        self.history_btn = ttk.Button(
            button_frame,
            text="履歴",
            command=self.show_history
        )
        self.history_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # サンプルクエリボタン
        self.sample_btn = ttk.Button(
            button_frame,
            text="サンプル",
            command=self.show_sample_queries
        )
        self.sample_btn.pack(side=tk.LEFT)
        
        # 下部: 結果表示エリア
        result_frame = ttk.LabelFrame(main_frame, text="実行結果", padding=5)
        result_frame.pack(fill=tk.BOTH, expand=True)
        
        # 結果テーブル
        self.result_table = DataTable(result_frame)
        self.result_table.pack(fill=tk.BOTH, expand=True)
        
        # ステータスバー
        self.status_var = tk.StringVar(value="準備完了")
        status_bar = ttk.Label(result_frame, textvariable=self.status_var)
        status_bar.pack(fill=tk.X, pady=(5, 0))
        
    def _setup_bindings(self):
        """キーバインドの設定"""
        # Ctrl+Enter でクエリ実行
        self.query_text.bind('<Control-Return>', lambda e: self.execute_query())
        
        # 履歴ナビゲーション
        self.query_text.bind('<Control-Up>', self.previous_query)
        self.query_text.bind('<Control-Down>', self.next_query)
        
    def execute_query(self):
        """クエリを実行"""
        query = self.query_text.get(1.0, tk.END).strip()
        if not query:
            MessageBox.show_warning("クエリが入力されていません。")
            return
            
        try:
            self.status_var.set("実行中...")
            self.execute_btn.config(state='disabled')
            
            # データベース接続確認
            if not self.db_connection.is_connected():
                MessageBox.show_error("データベースに接続されていません。")
                return
                
            # クエリ実行
            conn = self.db_connection.get_connection()
            cursor = conn.cursor()
            
            # クエリの種類を判定
            query_type = query.strip().upper().split()[0]
            
            if query_type in ['SELECT', 'PRAGMA']:
                # SELECT文の場合
                cursor.execute(query)
                results = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                
                # 結果をテーブルに表示
                self.result_table.load_data(results, columns)
                
                self.status_var.set(f"実行完了: {len(results)}行取得")
                
            else:
                # INSERT, UPDATE, DELETE等の場合
                cursor.execute(query)
                conn.commit()
                
                affected_rows = cursor.rowcount
                self.result_table.clear()
                
                self.status_var.set(f"実行完了: {affected_rows}行影響")
                
            # クエリを履歴に追加
            self._add_to_history(query)
            
        except sqlite3.Error as e:
            self.error_handler.handle_error(e, "クエリ実行エラー")
            MessageBox.show_error(f"SQLエラー: {str(e)}")
            self.status_var.set("エラー")
            
        except Exception as e:
            self.error_handler.handle_error(e, "予期しないエラー")
            MessageBox.show_error(f"エラー: {str(e)}")
            self.status_var.set("エラー")
            
        finally:
            self.execute_btn.config(state='normal')
            
    def clear_query(self):
        """クエリをクリア"""
        self.query_text.delete(1.0, tk.END)
        self.result_table.clear()
        self.status_var.set("準備完了")
        
    def _add_to_history(self, query: str):
        """クエリを履歴に追加"""
        if query not in self.query_history:
            self.query_history.append(query)
            # 履歴は最大50件まで
            if len(self.query_history) > 50:
                self.query_history.pop(0)
        self.history_index = len(self.query_history)
        
    def previous_query(self, event=None):
        """前のクエリを表示"""
        if self.query_history and self.history_index > 0:
            self.history_index -= 1
            query = self.query_history[self.history_index]
            self.query_text.delete(1.0, tk.END)
            self.query_text.insert(1.0, query)
            
    def next_query(self, event=None):
        """次のクエリを表示"""
        if self.query_history and self.history_index < len(self.query_history) - 1:
            self.history_index += 1
            query = self.query_history[self.history_index]
            self.query_text.delete(1.0, tk.END)
            self.query_text.insert(1.0, query)
            
    def show_history(self):
        """履歴ダイアログを表示"""
        if not self.query_history:
            MessageBox.show_info("クエリ履歴がありません。")
            return
            
        # 履歴選択ダイアログ
        history_window = tk.Toplevel(self.frame)
        history_window.title("クエリ履歴")
        history_window.geometry("600x400")
        history_window.transient(self.frame.winfo_toplevel())
        history_window.grab_set()
        
        # リストボックス
        listbox_frame = ttk.Frame(history_window)
        listbox_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        listbox = tk.Listbox(listbox_frame)
        scrollbar = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=listbox.yview)
        listbox.config(yscrollcommand=scrollbar.set)
        
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 履歴を追加
        for i, query in enumerate(reversed(self.query_history)):
            preview = query.replace('\n', ' ')[:100]
            if len(query) > 100:
                preview += "..."
            listbox.insert(tk.END, f"{len(self.query_history)-i}: {preview}")
            
        # ボタンフレーム
        button_frame = ttk.Frame(history_window)
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        def select_query():
            selection = listbox.curselection()
            if selection:
                index = len(self.query_history) - 1 - selection[0]
                query = self.query_history[index]
                self.query_text.delete(1.0, tk.END)
                self.query_text.insert(1.0, query)
                history_window.destroy()
                
        ttk.Button(button_frame, text="選択", command=select_query).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="キャンセル", command=history_window.destroy).pack(side=tk.LEFT)
        
    def show_sample_queries(self):
        """サンプルクエリを表示"""
        samples = [
            ("テーブル一覧", "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"),
            ("テーブル構造確認", "PRAGMA table_info('テーブル名');"),
            ("インデックス一覧", "SELECT name FROM sqlite_master WHERE type='index' ORDER BY name;"),
            ("データ件数確認", "SELECT COUNT(*) FROM テーブル名;"),
            ("上位10件取得", "SELECT * FROM テーブル名 LIMIT 10;"),
            ("重複データ確認", "SELECT カラム名, COUNT(*) FROM テーブル名 GROUP BY カラム名 HAVING COUNT(*) > 1;"),
        ]
        
        # サンプル選択ダイアログ
        sample_window = tk.Toplevel(self.frame)
        sample_window.title("サンプルクエリ")
        sample_window.geometry("500x300")
        sample_window.transient(self.frame.winfo_toplevel())
        sample_window.grab_set()
        
        # リストボックス
        listbox_frame = ttk.Frame(sample_window)
        listbox_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        listbox = tk.Listbox(listbox_frame)
        scrollbar = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=listbox.yview)
        listbox.config(yscrollcommand=scrollbar.set)
        
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # サンプルを追加
        for name, query in samples:
            listbox.insert(tk.END, name)
            
        # ボタンフレーム
        button_frame = ttk.Frame(sample_window)
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        def select_sample():
            selection = listbox.curselection()
            if selection:
                _, query = samples[selection[0]]
                self.query_text.delete(1.0, tk.END)
                self.query_text.insert(1.0, query)
                sample_window.destroy()
                
        ttk.Button(button_frame, text="選択", command=select_sample).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="キャンセル", command=sample_window.destroy).pack(side=tk.LEFT)
        
    def refresh(self):
        """タブの更新"""
        # 必要に応じて実装
        pass