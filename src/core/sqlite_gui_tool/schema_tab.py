"""
Schema Tab Module for SQLite GUI Tool

This module provides the schema tab functionality for the SQLite GUI Tool.
"""

import tkinter as tk
from tkinter import ttk


class SchemaTab:
    """Schema tab for displaying database schema information"""
    
    def __init__(self, parent, app):
        """Initialize the schema tab
        
        Args:
            parent: The parent frame
            app: The main application instance
        """
        self.parent = parent
        self.app = app
        
        # Create the tab UI
        self._create_ui()
        
    def _create_ui(self):
        """Create the schema tab UI"""
        # メインフレーム
        schema_frame = ttk.Frame(self.parent)
        schema_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 左側フレーム（テーブル一覧）
        left_frame = ttk.LabelFrame(schema_frame, text="テーブル一覧")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 5))

        # テーブル一覧リストボックス
        self.table_listbox = tk.Listbox(left_frame, width=30)
        self.table_listbox.pack(
            side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # テーブル一覧スクロールバー
        table_scrollbar = ttk.Scrollbar(
            self.table_listbox, orient="vertical", command=self.table_listbox.yview)
        self.table_listbox.configure(yscrollcommand=table_scrollbar.set)
        table_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # テーブル選択時のイベント
        self.table_listbox.bind('<<ListboxSelect>>', self.on_table_select)

        # 右側フレーム（テーブル詳細）
        right_frame = ttk.Frame(schema_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # テーブル情報フレーム
        table_info_frame = ttk.LabelFrame(right_frame, text="テーブル情報")
        table_info_frame.pack(fill=tk.X, pady=(0, 5))

        # テーブル名ラベル
        self.table_name_var = tk.StringVar(value="テーブルを選択してください")
        table_name_label = ttk.Label(
            table_info_frame, textvariable=self.table_name_var, font=("", 12, "bold"))
        table_name_label.pack(anchor=tk.W, padx=5, pady=5)

        # テーブル統計情報
        self.table_stats_var = tk.StringVar(value="")
        table_stats_label = ttk.Label(
            table_info_frame, textvariable=self.table_stats_var)
        table_stats_label.pack(anchor=tk.W, padx=5, pady=5)

        # カラム情報フレーム
        column_frame = ttk.LabelFrame(right_frame, text="カラム情報")
        column_frame.pack(fill=tk.BOTH, expand=True)

        # カラム情報ツリービュー
        columns = ("cid", "name", "type", "notnull", "dflt_value", "pk")
        self.column_tree = ttk.Treeview(
            column_frame, columns=columns, show="headings")

        # 列の設定
        self.column_tree.heading("cid", text="ID")
        self.column_tree.heading("name", text="カラム名")
        self.column_tree.heading("type", text="データ型")
        self.column_tree.heading("notnull", text="NOT NULL")
        self.column_tree.heading("dflt_value", text="デフォルト値")
        self.column_tree.heading("pk", text="主キー")

        self.column_tree.column("cid", width=50, anchor="center")
        self.column_tree.column("name", width=150)
        self.column_tree.column("type", width=100)
        self.column_tree.column("notnull", width=80, anchor="center")
        self.column_tree.column("dflt_value", width=150)
        self.column_tree.column("pk", width=60, anchor="center")

        # スクロールバー
        column_y_scrollbar = ttk.Scrollbar(
            column_frame, orient="vertical", command=self.column_tree.yview)
        column_x_scrollbar = ttk.Scrollbar(
            column_frame, orient="horizontal", command=self.column_tree.xview)
        self.column_tree.configure(
            yscrollcommand=column_y_scrollbar.set, xscrollcommand=column_x_scrollbar.set)

        # 配置
        self.column_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        column_y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        column_x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        # インデックス情報フレーム
        index_frame = ttk.LabelFrame(right_frame, text="インデックス情報")
        index_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))

        # インデックス情報ツリービュー
        index_columns = ("name", "unique", "columns")
        self.index_tree = ttk.Treeview(
            index_frame, columns=index_columns, show="headings")

        # 列の設定
        self.index_tree.heading("name", text="インデックス名")
        self.index_tree.heading("unique", text="UNIQUE")
        self.index_tree.heading("columns", text="対象カラム")

        self.index_tree.column("name", width=150)
        self.index_tree.column("unique", width=80, anchor="center")
        self.index_tree.column("columns", width=250)

        # スクロールバー
        index_y_scrollbar = ttk.Scrollbar(
            index_frame, orient="vertical", command=self.index_tree.yview)
        index_x_scrollbar = ttk.Scrollbar(
            index_frame, orient="horizontal", command=self.index_tree.xview)
        self.index_tree.configure(
            yscrollcommand=index_y_scrollbar.set, xscrollcommand=index_x_scrollbar.set)

        # 配置
        self.index_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        index_y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        index_x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        # ボタンフレーム
        button_frame = ttk.Frame(right_frame)
        button_frame.pack(fill=tk.X, pady=5)

        # SQLボタン
        self.show_sql_button = ttk.Button(
            button_frame, text="CREATE文を表示", command=self.show_create_sql, state="disabled")
        self.show_sql_button.pack(side=tk.LEFT, padx=5)

        # サンプルデータボタン
        self.show_sample_button = ttk.Button(
            button_frame, text="サンプルデータを表示", command=self.show_sample_data, state="disabled")
        self.show_sample_button.pack(side=tk.LEFT, padx=5)
        
    def on_table_select(self, event):
        """Handle table selection event"""
        # This method will be implemented in the main application
        self.app.on_table_select(event)
        
    def show_create_sql(self):
        """Show CREATE TABLE SQL statement"""
        # This method will be implemented in the main application
        self.app.show_create_sql()
        
    def show_sample_data(self):
        """Show sample data from the selected table"""
        # This method will be implemented in the main application
        self.app.show_sample_data()
        
    def update_table_list(self, tables):
        """Update the table list with the provided tables
        
        Args:
            tables: List of table names
        """
        self.table_listbox.delete(0, tk.END)
        for table in sorted(tables):
            self.table_listbox.insert(tk.END, table)
            
    def clear(self):
        """Clear all data in the tab"""
        self.table_listbox.delete(0, tk.END)
        self.table_name_var.set("テーブルを選択してください")
        self.table_stats_var.set("")
        
        # Clear column tree
        for item in self.column_tree.get_children():
            self.column_tree.delete(item)
            
        # Clear index tree
        for item in self.index_tree.get_children():
            self.index_tree.delete(item)
            
        # Disable buttons
        self.show_sql_button.config(state="disabled")
        self.show_sample_button.config(state="disabled")