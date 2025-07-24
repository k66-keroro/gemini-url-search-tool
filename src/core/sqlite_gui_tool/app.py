"""
SQLite GUI Tool - メインアプリケーションクラス

アプリケーションのメインクラスを提供します。
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sqlite3
import os
import sys
from pathlib import Path
import traceback

# タブのインポート
from .query_tab import QueryTab
from .schema_tab import SchemaTab
from .import_tab import ImportTab
from .export_tab import ExportTab
from .analyze_tab import AnalyzeTab
from .code_converter_tab import CodeConverterTab

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
        self.sqlite_manager = SQLiteManager() if SQLiteManager else None
    
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
        
        try:
            # 既存の接続を閉じる
            self.close_connection()
            
            # 新しい接続を開く
            self.conn = sqlite3.connect(db_path)
            self.conn.row_factory = sqlite3.Row
            self.cursor = self.conn.cursor()
            
            # データベースパスを保存
            self.db_path = db_path
            
            # ステータスバーを更新
            self.status_var.set(f"接続済み: {os.path.basename(db_path)}")
            
            # 各タブに接続を通知
            for tab in self.tabs.values():
                tab.on_db_connect(self.conn, self.cursor)
            
            # 成功メッセージ
            self.show_message(f"データベース '{os.path.basename(db_path)}' に接続しました。", "info")
            
        except sqlite3.Error as e:
            self.show_message(f"データベース接続エラー: {e}", "error")
            traceback.print_exc()
    
    def close_connection(self):
        """データベース接続を閉じる"""
        if self.conn:
            try:
                self.conn.close()
                
                # 各タブに切断を通知
                for tab in self.tabs.values():
                    tab.on_db_disconnect()
                
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