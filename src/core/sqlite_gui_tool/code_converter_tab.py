"""
Code Converter Tab Module for SQLite GUI Tool

This module provides the code field converter tab functionality for the SQLite GUI Tool.
"""

import tkinter as tk
from tkinter import ttk


class CodeConverterTab:
    """Code converter tab for converting code fields in SQLite database"""
    
    def __init__(self, parent, app):
        """Initialize the code converter tab
        
        Args:
            parent: The parent frame
            app: The main application instance
        """
        self.parent = parent
        self.app = app
        
        # Create the tab UI
        self._create_ui()
        
    def _create_ui(self):
        """Create the code converter tab UI"""
        # メインフレーム
        converter_frame = ttk.Frame(self.parent)
        converter_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 説明ラベル
        description = (
            "このタブでは、テーブル内のコードフィールド（数値として格納されている文字列）を検出し、\n"
            "適切なデータ型に変換することができます。例えば、'0001'のような先頭のゼロが重要な値を文字列として保存します。"
        )
        desc_label = ttk.Label(
            converter_frame, text=description, wraplength=800, justify="left")
        desc_label.pack(fill=tk.X, pady=10)

        # テーブル選択フレーム
        table_frame = ttk.LabelFrame(converter_frame, text="テーブル選択")
        table_frame.pack(fill=tk.X, pady=5)

        # テーブル選択
        table_select_frame = ttk.Frame(table_frame)
        table_select_frame.pack(fill=tk.X, padx=5, pady=5)

        table_label = ttk.Label(table_select_frame, text="テーブル:")
        table_label.pack(side=tk.LEFT, padx=(0, 5))

        self.converter_table_var = tk.StringVar()
        self.converter_table_combo = ttk.Combobox(table_select_frame, textvariable=self.converter_table_var,
                                                 width=30, state="readonly")
        self.converter_table_combo.pack(side=tk.LEFT)

        # テーブル選択時のイベント
        self.converter_table_combo.bind(
            "<<ComboboxSelected>>", self.on_converter_table_select)

        # 分析ボタン
        analyze_button = ttk.Button(
            table_select_frame, text="コードフィールドを分析", command=self.analyze_code_fields)
        analyze_button.pack(side=tk.LEFT, padx=(10, 0))

        # 分析結果フレーム
        result_frame = ttk.LabelFrame(converter_frame, text="分析結果")
        result_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # 分析結果ツリービュー
        columns = ("column", "type", "sample", "code_type", "convert")
        self.code_field_tree = ttk.Treeview(
            result_frame, columns=columns, show="headings")

        # 列の設定
        self.code_field_tree.heading("column", text="カラム名")
        self.code_field_tree.heading("type", text="現在の型")
        self.code_field_tree.heading("sample", text="サンプル値")
        self.code_field_tree.heading("code_type", text="推定コード型")
        self.code_field_tree.heading("convert", text="変換")

        self.code_field_tree.column("column", width=150)
        self.code_field_tree.column("type", width=100)
        self.code_field_tree.column("sample", width=150)
        self.code_field_tree.column("code_type", width=150)
        self.code_field_tree.column("convert", width=80, anchor="center")

        # スクロールバー
        tree_y_scrollbar = ttk.Scrollbar(
            result_frame, orient="vertical", command=self.code_field_tree.yview)
        tree_x_scrollbar = ttk.Scrollbar(
            result_frame, orient="horizontal", command=self.code_field_tree.xview)
        self.code_field_tree.configure(
            yscrollcommand=tree_y_scrollbar.set, xscrollcommand=tree_x_scrollbar.set)

        # 配置
        self.code_field_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree_x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        # 変換設定フレーム
        convert_frame = ttk.LabelFrame(converter_frame, text="変換設定")
        convert_frame.pack(fill=tk.X, pady=5)

        # 変換オプション
        option_frame = ttk.Frame(convert_frame)
        option_frame.pack(fill=tk.X, padx=5, pady=5)

        # バックアップオプション
        self.backup_var = tk.BooleanVar(value=True)
        backup_check = ttk.Checkbutton(
            option_frame, text="変換前にバックアップを作成", variable=self.backup_var)
        backup_check.pack(anchor=tk.W)

        # 実行ボタンフレーム
        button_frame = ttk.Frame(converter_frame)
        button_frame.pack(fill=tk.X, pady=10)

        # 変換実行ボタン
        convert_button = ttk.Button(
            button_frame, text="選択したフィールドを変換", command=self.execute_conversion)
        convert_button.pack(side=tk.RIGHT)

        # 結果表示エリア
        self.conversion_result_var = tk.StringVar()
        result_label = ttk.Label(
            converter_frame, textvariable=self.conversion_result_var, wraplength=800)
        result_label.pack(fill=tk.X, pady=5)
        
    def on_converter_table_select(self, event):
        """テーブル選択時の処理"""
        # Clear the tree view
        for item in self.code_field_tree.get_children():
            self.code_field_tree.delete(item)
            
        # Clear the result message
        self.conversion_result_var.set("")
        
    def analyze_code_fields(self):
        """コードフィールドを分析"""
        # This method will be implemented in the main application
        self.app.analyze_code_fields()
        
    def execute_conversion(self):
        """変換を実行"""
        # This method will be implemented in the main application
        self.app.execute_conversion()
        
    def on_db_connect(self, conn, cursor):
        """データベース接続時の処理"""
        # テーブル一覧を更新
        tables = self.app.get_table_list()
        self.converter_table_combo['values'] = tables
        if tables:
            self.converter_table_var.set(tables[0])
        
    def on_db_disconnect(self):
        """データベース切断時の処理"""
        # テーブル一覧をクリア
        self.converter_table_combo['values'] = []
        self.converter_table_var.set("")
        
        # 分析結果をクリア
        for item in self.code_field_tree.get_children():
            self.code_field_tree.delete(item)
            
        # 結果表示をクリア
        self.conversion_result_var.set("")
        
    def refresh(self):
        """タブの表示を更新"""
        if self.app.conn:
            self.on_db_connect(self.app.conn, self.app.cursor)