"""
Import Tab Module for SQLite GUI Tool

This module provides the import tab functionality for the SQLite GUI Tool.
"""

import tkinter as tk
from tkinter import ttk, filedialog
import re
import os


class ImportTab:
    """Import tab for importing data into SQLite database"""
    
    def __init__(self, parent, app):
        """Initialize the import tab
        
        Args:
            parent: The parent frame
            app: The main application instance
        """
        self.parent = parent
        self.app = app
        
        # Create the tab UI
        self._create_ui()
        
    def _create_ui(self):
        """Create the import tab UI"""
        # メインフレーム
        import_frame = ttk.Frame(self.parent)
        import_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 説明ラベル
        description = (
            "このタブでは、CSVファイル、TSVファイル、Excelファイルからデータをインポートできます。\n"
            "インポート時にテーブル名を指定できます。日本語や特殊文字を含むテーブル名は自動的に変換されます。"
        )
        desc_label = ttk.Label(
            import_frame, text=description, wraplength=800, justify="left")
        desc_label.pack(fill=tk.X, pady=10)

        # ファイル選択フレーム
        file_frame = ttk.LabelFrame(import_frame, text="インポートするファイル")
        file_frame.pack(fill=tk.X, pady=5)

        # ファイルパス入力
        path_frame = ttk.Frame(file_frame)
        path_frame.pack(fill=tk.X, padx=5, pady=5)

        path_label = ttk.Label(path_frame, text="ファイルパス:")
        path_label.pack(side=tk.LEFT, padx=(0, 5))

        self.import_path_var = tk.StringVar()
        path_entry = ttk.Entry(
            path_frame, textvariable=self.import_path_var, width=60)
        path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        browse_button = ttk.Button(
            path_frame, text="参照...", command=self.browse_import_file)
        browse_button.pack(side=tk.LEFT)

        # ファイル情報フレーム
        info_frame = ttk.Frame(file_frame)
        info_frame.pack(fill=tk.X, padx=5, pady=5)

        # ファイルタイプ
        type_label = ttk.Label(info_frame, text="ファイルタイプ:")
        type_label.grid(row=0, column=0, sticky=tk.W, padx=(0, 5))

        self.file_type_var = tk.StringVar(value="自動検出")
        file_type_combo = ttk.Combobox(info_frame, textvariable=self.file_type_var,
                                      values=["自動検出", "CSV", "TSV", "Excel"], width=15, state="readonly")
        file_type_combo.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))

        # エンコーディング
        encoding_label = ttk.Label(info_frame, text="エンコーディング:")
        encoding_label.grid(row=0, column=2, sticky=tk.W, padx=(0, 5))

        self.encoding_var = tk.StringVar(value="自動検出")
        encoding_combo = ttk.Combobox(info_frame, textvariable=self.encoding_var,
                                     values=["自動検出", "utf-8", "cp932", "shift_jis", "euc_jp"], width=15, state="readonly")
        encoding_combo.grid(row=0, column=3, sticky=tk.W)

        # 区切り文字
        delimiter_label = ttk.Label(info_frame, text="区切り文字:")
        delimiter_label.grid(row=1, column=0, sticky=tk.W,
                             padx=(0, 5), pady=(5, 0))

        self.delimiter_var = tk.StringVar(value="自動検出")
        delimiter_combo = ttk.Combobox(info_frame, textvariable=self.delimiter_var,
                                      values=["自動検出", ",", "\\t", ";", "|"], width=15, state="readonly")
        delimiter_combo.grid(row=1, column=1, sticky=tk.W,
                             padx=(0, 20), pady=(5, 0))

        # ヘッダー行
        header_label = ttk.Label(info_frame, text="ヘッダー行:")
        header_label.grid(row=1, column=2, sticky=tk.W,
                          padx=(0, 5), pady=(5, 0))

        self.header_var = tk.BooleanVar(value=True)
        header_check = ttk.Checkbutton(
            info_frame, text="1行目をヘッダーとして使用", variable=self.header_var)
        header_check.grid(row=1, column=3, sticky=tk.W, pady=(5, 0))

        # テーブル設定フレーム
        table_frame = ttk.LabelFrame(import_frame, text="テーブル設定")
        table_frame.pack(fill=tk.X, pady=5)

        # テーブル名
        table_name_frame = ttk.Frame(table_frame)
        table_name_frame.pack(fill=tk.X, padx=5, pady=5)

        table_name_label = ttk.Label(table_name_frame, text="テーブル名:")
        table_name_label.pack(side=tk.LEFT, padx=(0, 5))

        self.table_name_entry_var = tk.StringVar()
        self.table_name_entry = ttk.Entry(
            table_name_frame, textvariable=self.table_name_entry_var, width=30)
        self.table_name_entry.pack(side=tk.LEFT, padx=(0, 5))

        self.sanitized_name_var = tk.StringVar()
        sanitized_name_label = ttk.Label(
            table_name_frame, textvariable=self.sanitized_name_var, foreground="blue")
        sanitized_name_label.pack(side=tk.LEFT)

        # テーブル名が変更されたときのイベント
        self.table_name_entry_var.trace_add("write", self.on_table_name_change)

        # 既存テーブルの処理
        existing_frame = ttk.Frame(table_frame)
        existing_frame.pack(fill=tk.X, padx=5, pady=5)

        existing_label = ttk.Label(existing_frame, text="既存テーブルの処理:")
        existing_label.pack(side=tk.LEFT, padx=(0, 5))

        self.existing_var = tk.StringVar(value="置換")
        replace_radio = ttk.Radiobutton(
            existing_frame, text="置換", variable=self.existing_var, value="置換")
        replace_radio.pack(side=tk.LEFT, padx=(0, 10))

        append_radio = ttk.Radiobutton(
            existing_frame, text="追加", variable=self.existing_var, value="追加")
        append_radio.pack(side=tk.LEFT, padx=(0, 10))

        fail_radio = ttk.Radiobutton(
            existing_frame, text="エラー", variable=self.existing_var, value="エラー")
        fail_radio.pack(side=tk.LEFT)

        # プレビューフレーム
        preview_frame = ttk.LabelFrame(import_frame, text="データプレビュー")
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # プレビューボタン
        preview_button = ttk.Button(
            preview_frame, text="プレビュー", command=self.preview_import_data)
        preview_button.pack(anchor=tk.W, padx=5, pady=5)

        # プレビューツリービュー
        self.preview_tree = ttk.Treeview(preview_frame)

        # スクロールバー
        preview_y_scrollbar = ttk.Scrollbar(
            preview_frame, orient="vertical", command=self.preview_tree.yview)
        preview_x_scrollbar = ttk.Scrollbar(
            preview_frame, orient="horizontal", command=self.preview_tree.xview)
        self.preview_tree.configure(
            yscrollcommand=preview_y_scrollbar.set, xscrollcommand=preview_x_scrollbar.set)

        # 配置
        self.preview_tree.pack(side=tk.LEFT, fill=tk.BOTH,
                               expand=True, padx=5, pady=5)
        preview_y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        preview_x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        # 実行ボタンフレーム
        button_frame = ttk.Frame(import_frame)
        button_frame.pack(fill=tk.X, pady=10)

        # インポート実行ボタン
        import_button = ttk.Button(
            button_frame, text="インポート実行", command=self.execute_import)
        import_button.pack(side=tk.RIGHT)

        # 結果表示エリア
        self.import_result_var = tk.StringVar()
        result_label = ttk.Label(
            import_frame, textvariable=self.import_result_var, wraplength=800)
        result_label.pack(fill=tk.X, pady=5)
        
    def browse_import_file(self):
        """ファイル選択ダイアログを表示"""
        file_path = filedialog.askopenfilename(
            title="インポートするファイルを選択",
            filetypes=[
                ("すべてのサポートされるファイル", "*.csv *.txt *.tsv *.xlsx *.xls"),
                ("CSVファイル", "*.csv"),
                ("テキストファイル", "*.txt"),
                ("TSVファイル", "*.tsv"),
                ("Excelファイル", "*.xlsx *.xls"),
                ("すべてのファイル", "*.*")
            ]
        )
        
        if file_path:
            self.import_path_var.set(file_path)
            
            # ファイル名からテーブル名を設定
            file_name = re.sub(r'\.[^.]+$', '', os.path.basename(file_path))
            self.table_name_entry_var.set(file_name)
            
    def on_table_name_change(self, *args):
        """テーブル名が変更されたときの処理"""
        table_name = self.table_name_entry_var.get()
        if table_name:
            sanitized = self.sanitize_table_name(table_name)
            if sanitized != table_name:
                self.sanitized_name_var.set(f"→ {sanitized}")
            else:
                self.sanitized_name_var.set("")
        else:
            self.sanitized_name_var.set("")
            
    def sanitize_table_name(self, table_name):
        """テーブル名を適切に変換（日本語や特殊文字を避ける）"""
        # 日本語文字を含むかチェック
        has_japanese = re.search(r'[ぁ-んァ-ン一-龥]', table_name)
        
        # 日本語文字を含む場合は、プレフィックスを付ける
        if has_japanese:
            sanitized = f"t_{hash(table_name) % 10000:04d}"
        else:
            # 英数字以外の文字を_に置換
            sanitized = re.sub(r'[^a-zA-Z0-9]', '_', table_name)
            
            # 連続する_を単一の_に置換
            sanitized = re.sub(r'_+', '_', sanitized)
            
            # 先頭が数字の場合、t_を付ける
            if sanitized and sanitized[0].isdigit():
                sanitized = f"t_{sanitized}"
                
            # 先頭と末尾の_を削除
            sanitized = sanitized.strip('_')
            
        return sanitized
            
    def preview_import_data(self):
        """インポートデータのプレビュー"""
        # This method will be implemented in the main application
        self.app.preview_import_data()
        
    def execute_import(self):
        """インポートを実行"""
        # This method will be implemented in the main application
        self.app.execute_import()
        
    def on_db_connect(self, conn, cursor):
        """データベース接続時の処理"""
        pass
        
    def on_db_disconnect(self):
        """データベース切断時の処理"""
        pass
        
    def refresh(self):
        """タブの表示を更新"""
        pass