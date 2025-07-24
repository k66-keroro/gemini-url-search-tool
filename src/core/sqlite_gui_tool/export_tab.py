"""
Export Tab Module for SQLite GUI Tool

This module provides the export tab functionality for the SQLite GUI Tool.
"""

import tkinter as tk
from tkinter import ttk, filedialog
import os


class ExportTab:
    """Export tab for exporting data from SQLite database"""
    
    def __init__(self, parent, app):
        """Initialize the export tab
        
        Args:
            parent: The parent frame
            app: The main application instance
        """
        self.parent = parent
        self.app = app
        
        # Create the tab UI
        self._create_ui()
        
    def _create_ui(self):
        """Create the export tab UI"""
        # メインフレーム
        export_frame = ttk.Frame(self.parent)
        export_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 説明ラベル
        description = (
            "このタブでは、SQLiteデータベースのテーブルをCSVファイルまたはExcelファイルにエクスポートできます。\n"
            "テーブル全体をエクスポートするか、カスタムSQLクエリの結果をエクスポートするかを選択できます。"
        )
        desc_label = ttk.Label(
            export_frame, text=description, wraplength=800, justify="left")
        desc_label.pack(fill=tk.X, pady=10)

        # エクスポート方法選択フレーム
        method_frame = ttk.LabelFrame(export_frame, text="エクスポート方法")
        method_frame.pack(fill=tk.X, pady=5)

        self.export_method_var = tk.StringVar(value="テーブル")
        table_radio = ttk.Radiobutton(method_frame, text="テーブル全体をエクスポート",
                                     variable=self.export_method_var, value="テーブル",
                                     command=self.toggle_export_method)
        table_radio.pack(anchor=tk.W, padx=5, pady=5)

        query_radio = ttk.Radiobutton(method_frame, text="SQLクエリの結果をエクスポート",
                                     variable=self.export_method_var, value="クエリ",
                                     command=self.toggle_export_method)
        query_radio.pack(anchor=tk.W, padx=5, pady=5)

        # テーブル選択フレーム
        self.table_select_frame = ttk.Frame(export_frame)
        self.table_select_frame.pack(fill=tk.X, pady=5)

        table_label = ttk.Label(self.table_select_frame, text="エクスポートするテーブル:")
        table_label.pack(side=tk.LEFT, padx=(0, 5))

        self.export_table_var = tk.StringVar()
        self.export_table_combo = ttk.Combobox(self.table_select_frame, textvariable=self.export_table_var,
                                              width=30, state="readonly")
        self.export_table_combo.pack(side=tk.LEFT)

        # クエリ入力フレーム
        self.query_frame = ttk.Frame(export_frame)
        self.query_frame.pack(fill=tk.X, pady=5)
        self.query_frame.pack_forget()  # 初期状態では非表示

        query_label = ttk.Label(self.query_frame, text="SQLクエリ:")
        query_label.pack(anchor=tk.W)

        self.export_query_text = tk.Text(
            self.query_frame, height=5, wrap=tk.WORD)
        self.export_query_text.pack(fill=tk.X, pady=5)

        # クエリ入力エリアのスクロールバー
        query_scrollbar = ttk.Scrollbar(
            self.export_query_text, orient="vertical", command=self.export_query_text.yview)
        self.export_query_text.configure(yscrollcommand=query_scrollbar.set)
        query_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 出力設定フレーム
        output_frame = ttk.LabelFrame(export_frame, text="出力設定")
        output_frame.pack(fill=tk.X, pady=5)

        # 出力形式
        format_frame = ttk.Frame(output_frame)
        format_frame.pack(fill=tk.X, padx=5, pady=5)

        format_label = ttk.Label(format_frame, text="出力形式:")
        format_label.pack(side=tk.LEFT, padx=(0, 5))

        self.export_format_var = tk.StringVar(value="CSV")
        format_combo = ttk.Combobox(format_frame, textvariable=self.export_format_var,
                                   values=["CSV", "Excel"], width=15, state="readonly")
        format_combo.pack(side=tk.LEFT)

        # エンコーディング（CSVのみ）
        self.encoding_frame = ttk.Frame(output_frame)
        self.encoding_frame.pack(fill=tk.X, padx=5, pady=5)

        encoding_label = ttk.Label(self.encoding_frame, text="エンコーディング:")
        encoding_label.pack(side=tk.LEFT, padx=(0, 5))

        self.export_encoding_var = tk.StringVar(value="utf-8-sig")
        encoding_combo = ttk.Combobox(self.encoding_frame, textvariable=self.export_encoding_var,
                                     values=["utf-8", "utf-8-sig", "cp932", "shift_jis"], width=15, state="readonly")
        encoding_combo.pack(side=tk.LEFT)

        # 出力形式が変更されたときのイベント
        self.export_format_var.trace_add("write", self.on_export_format_change)

        # 出力先フレーム
        output_path_frame = ttk.Frame(output_frame)
        output_path_frame.pack(fill=tk.X, padx=5, pady=5)

        output_path_label = ttk.Label(output_path_frame, text="出力先:")
        output_path_label.pack(side=tk.LEFT, padx=(0, 5))

        self.export_path_var = tk.StringVar()
        output_path_entry = ttk.Entry(
            output_path_frame, textvariable=self.export_path_var, width=60)
        output_path_entry.pack(side=tk.LEFT, fill=tk.X,
                               expand=True, padx=(0, 5))

        browse_button = ttk.Button(
            output_path_frame, text="参照...", command=self.browse_export_path)
        browse_button.pack(side=tk.LEFT)

        # プレビューフレーム
        preview_frame = ttk.LabelFrame(export_frame, text="データプレビュー")
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # プレビューボタン
        preview_button = ttk.Button(
            preview_frame, text="プレビュー", command=self.preview_export_data)
        preview_button.pack(anchor=tk.W, padx=5, pady=5)

        # プレビューツリービュー
        self.export_preview_tree = ttk.Treeview(preview_frame)

        # スクロールバー
        preview_y_scrollbar = ttk.Scrollbar(
            preview_frame, orient="vertical", command=self.export_preview_tree.yview)
        preview_x_scrollbar = ttk.Scrollbar(
            preview_frame, orient="horizontal", command=self.export_preview_tree.xview)
        self.export_preview_tree.configure(
            yscrollcommand=preview_y_scrollbar.set, xscrollcommand=preview_x_scrollbar.set)

        # 配置
        self.export_preview_tree.pack(
            side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        preview_y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        preview_x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        # 実行ボタンフレーム
        button_frame = ttk.Frame(export_frame)
        button_frame.pack(fill=tk.X, pady=10)

        # エクスポート実行ボタン
        export_button = ttk.Button(
            button_frame, text="エクスポート実行", command=self.execute_export)
        export_button.pack(side=tk.RIGHT)

        # 結果表示エリア
        self.export_result_var = tk.StringVar()
        result_label = ttk.Label(
            export_frame, textvariable=self.export_result_var, wraplength=800)
        result_label.pack(fill=tk.X, pady=5)
        
    def toggle_export_method(self):
        """エクスポート方法の切り替え"""
        if self.export_method_var.get() == "テーブル":
            self.table_select_frame.pack(fill=tk.X, pady=5)
            self.query_frame.pack_forget()
        else:
            self.table_select_frame.pack_forget()
            self.query_frame.pack(fill=tk.X, pady=5)
            
    def on_export_format_change(self, *args):
        """出力形式が変更されたときの処理"""
        if self.export_format_var.get() == "CSV":
            self.encoding_frame.pack(fill=tk.X, padx=5, pady=5)
        else:
            self.encoding_frame.pack_forget()
            
    def browse_export_path(self):
        """出力先選択ダイアログを表示"""
        if self.export_format_var.get() == "CSV":
            file_path = filedialog.asksaveasfilename(
                title="エクスポート先を選択",
                defaultextension=".csv",
                filetypes=[("CSVファイル", "*.csv"), ("すべてのファイル", "*.*")]
            )
        else:
            file_path = filedialog.asksaveasfilename(
                title="エクスポート先を選択",
                defaultextension=".xlsx",
                filetypes=[("Excelファイル", "*.xlsx"), ("すべてのファイル", "*.*")]
            )
            
        if file_path:
            self.export_path_var.set(file_path)
            
    def preview_export_data(self):
        """エクスポートデータのプレビュー"""
        # This method will be implemented in the main application
        self.app.preview_export_data()
        
    def execute_export(self):
        """エクスポートを実行"""
        # This method will be implemented in the main application
        self.app.execute_export()
        
    def on_db_connect(self, conn, cursor):
        """データベース接続時の処理"""
        # テーブル一覧を更新
        self.refresh_table_list()
        
    def refresh_table_list(self):
        """テーブル一覧を更新"""
        if not self.app.conn:
            return
            
        try:
            # 実際に存在するテーブルのみを取得
            self.app.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")
            tables = [row[0] for row in self.app.cursor.fetchall()]
            
            self.export_table_combo['values'] = tables
            if tables:
                self.export_table_var.set(tables[0])
            else:
                self.export_table_var.set("")
                
        except Exception as e:
            self.app.show_message(f"テーブル一覧の更新エラー: {e}", "error")
        
    def on_db_disconnect(self):
        """データベース切断時の処理"""
        # テーブル一覧をクリア
        self.export_table_combo['values'] = []
        self.export_table_var.set("")
        
        # プレビューをクリア
        for item in self.export_preview_tree.get_children():
            self.export_preview_tree.delete(item)
            
        # 結果表示をクリア
        self.export_result_var.set("")
        
    def refresh(self):
        """タブの表示を更新"""
        if self.app.conn:
            self.on_db_connect(self.app.conn, self.app.cursor)