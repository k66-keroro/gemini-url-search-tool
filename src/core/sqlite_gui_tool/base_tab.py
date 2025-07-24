"""
SQLite GUI Tool - 基底タブクラス

すべてのタブの基底クラスを提供します。
"""

import tkinter as tk
from tkinter import ttk


class BaseTab:
    """
    すべてのタブの基底クラス
    
    各タブはこのクラスを継承して実装します。
    """
    
    def __init__(self, parent, app):
        """
        初期化
        
        Args:
            parent: 親ウィジェット（タブコントロール）
            app: アプリケーションのインスタンス
        """
        self.parent = parent
        self.app = app
        self.frame = ttk.Frame(parent)
        self.frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # データベース接続の参照
        self.conn = None
        self.cursor = None
        
        # 初期化
        self.init_ui()
    
    def init_ui(self):
        """
        UIの初期化
        
        このメソッドをオーバーライドして、タブ固有のUIを構築します。
        """
        pass
    
    def on_db_connect(self, conn, cursor):
        """
        データベース接続時の処理
        
        Args:
            conn: データベース接続オブジェクト
            cursor: カーソルオブジェクト
        """
        self.conn = conn
        self.cursor = cursor
    
    def on_db_disconnect(self):
        """
        データベース切断時の処理
        """
        self.conn = None
        self.cursor = None
    
    def refresh(self):
        """
        タブの内容を更新
        """
        pass
    
    def create_scrollable_treeview(self, parent):
        """
        スクロール可能なTreeviewを作成
        
        Args:
            parent: 親ウィジェット
            
        Returns:
            treeview: 作成したTreeviewウィジェット
            frame: Treeviewを含むフレーム
        """
        frame = ttk.Frame(parent)
        
        # Treeviewの作成
        treeview = ttk.Treeview(frame)
        
        # スクロールバーの作成
        y_scrollbar = ttk.Scrollbar(frame, orient="vertical", command=treeview.yview)
        x_scrollbar = ttk.Scrollbar(frame, orient="horizontal", command=treeview.xview)
        
        # Treeviewとスクロールバーの関連付け
        treeview.configure(yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set)
        
        # 配置
        treeview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        return treeview, frame
    
    def show_message(self, message, message_type="info"):
        """
        メッセージを表示
        
        Args:
            message: 表示するメッセージ
            message_type: メッセージの種類（"info", "warning", "error"）
        """
        self.app.show_message(message, message_type)