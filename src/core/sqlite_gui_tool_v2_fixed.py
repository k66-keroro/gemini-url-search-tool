import re
import time
import csv
import json
from tkinter import filedialog, ttk, messagebox
import tkinter as tk
import sqlite3
import sys
import os
from pathlib import Path
import traceback

# GUIツール自身のファイルパスを基準にプロジェクトルートを特定
GUI_TOOL_DIR = Path(os.path.abspath(os.path.dirname(__file__)))
GUI_PROJECT_ROOT = GUI_TOOL_DIR.parents[1]  # src/core の2つ上の階層

# プロジェクトルートをsys.pathに追加
if str(GUI_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(GUI_PROJECT_ROOT))

try:
    # SQLiteManagerをインポート
    from src.core.sqlite_manager import SQLiteManager
    from src.core.code_field_converter import analyze_numeric_code_fields, convert_table_column
    from config.constants import Paths
    # PathsクラスのPROJECT_ROOTをGUI_PROJECT_ROOTで上書き
    _original_paths_init = Paths.__init__

    def _new_paths_init(self, *args, **kwargs):
        _original_paths_init(self, *args, **kwargs)
        self.PROJECT_ROOT = GUI_PROJECT_ROOT
        self.LOGS = self.PROJECT_ROOT / 'logs'
        self.RAW_DATA = self.PROJECT_ROOT / 'data' / 'raw'
    Paths.__init__ = _new_paths_init

except ImportError as e:
    SQLiteManager = None

    class Paths:
        def __init__(self):
            self.PROJECT_ROOT = GUI_PROJECT_ROOT
            self.LOGS = self.PROJECT_ROOT / 'logs'
            self.RAW_DATA = self.PROJECT_ROOT / 'data' / 'raw'
    print(f"警告: SQLiteManagerまたはPathsのインポートに失敗しました。一部機能が制限されます。エラー: {e}")
    print(traceback.format_exc())

"""
改善版コード – SQLite GUI ツール（提案変更反映済み）
・with sqlite3.connect を使用
・スクロールバー追加
・pyperclip 未インストール時警告
・traceback ログ出力
・エラー再処理機能追加
"""

try:
    import pyperclip
except ImportError:
    pyperclip = None

CONFIG_FILE = "db_config.json"


def sanitize_table_name(table_name: str) -> str:
    """
    テーブル名を適切に変換（日本語や特殊文字を避ける）

    Args:
        table_name: 元のテーブル名

    Returns:
        変換後のテーブル名
    """
    import re

    # 日本語文字を含むかチェック
    has_japanese = re.search(r'[ぁ-んァ-ン一-龥]', table_name)

    # 日本語文字を含む場合は、ローマ字に変換するか、プレフィックスを付ける
    if has_japanese:
        # 簡易的な変換: 日本語テーブル名にはt_を付ける
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


class SQLiteGUITool:
    def __init__(self, root):
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
        self.tab_query = ttk.Frame(self.tab_control)
        self.tab_schema = ttk.Frame(self.tab_control)
        self.tab_import = ttk.Frame(self.tab_control)
        self.tab_export = ttk.Frame(self.tab_control)
        self.tab_analyze = ttk.Frame(self.tab_control)
        self.tab_code_converter = ttk.Frame(self.tab_control)

        self.tab_control.add(self.tab_query, text='クエリ実行')
        self.tab_control.add(self.tab_schema, text='スキーマ')
        self.tab_control.add(self.tab_import, text='インポート')
        self.tab_control.add(self.tab_export, text='エクスポート')
        self.tab_control.add(self.tab_analyze, text='データ分析')
        self.tab_control.add(self.tab_code_converter, text='コードフィールド変換')

        self.tab_control.pack(expand=1, fill="both")

        # 各タブの初期化
        self.init_query_tab()
        self.init_schema_tab()
        self.init_import_tab()
        self.init_export_tab()
        self.init_analyze_tab()
        self.init_code_converter_tab()

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
        self.default_db_path = Paths().SQLITE_DB

    def init_query_tab(self):
        """クエリ実行タブの初期化"""
        # メインフレーム
        query_frame = ttk.Frame(self.tab_query)
        query_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 上部フレーム（クエリ入力エリア）
        top_frame = ttk.Frame(query_frame)
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
        button_frame = ttk.Frame(query_frame)
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
        result_label = ttk.Label(query_frame, text="実行結果:")
        result_label.pack(anchor=tk.W, pady=(10, 5))

        # 結果表示エリア（ツリービュー）
        result_frame = ttk.Frame(query_frame)
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
            query_frame, textvariable=self.result_info_var)
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

    def init_schema_tab(self):
        """スキーマタブの初期化"""
        # メインフレーム
        schema_frame = ttk.Frame(self.tab_schema)
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

    def init_import_tab(self):
        """インポートタブの初期化"""
        # メインフレーム
        import_frame = ttk.Frame(self.tab_import)
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

        # SQLiteManagerのインスタンス
        self.sqlite_manager = SQLiteManager() if SQLiteManager else None

    def init_export_tab(self):
        """エクスポートタブの初期化"""
        # メインフレーム
        export_frame = ttk.Frame(self.tab_export)
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

    def init_analyze_tab(self):
        """データ分析タブの初期化"""
        # メインフレーム
        analyze_frame = ttk.Frame(self.tab_analyze)
        analyze_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 説明ラベル
        description = (
            "このタブでは、テーブルのデータ分析を行うことができます。\n"
            "テーブルとカラムを選択して、データの分布や統計情報を確認できます。"
        )
        desc_label = ttk.Label(
            analyze_frame, text=description, wraplength=800, justify="left")
        desc_label.pack(fill=tk.X, pady=10)

        # テーブル選択フレーム
        table_frame = ttk.LabelFrame(analyze_frame, text="テーブルとカラムの選択")
        table_frame.pack(fill=tk.X, pady=5)

        # テーブル選択
        table_select_frame = ttk.Frame(table_frame)
        table_select_frame.pack(fill=tk.X, padx=5, pady=5)

        table_label = ttk.Label(table_select_frame, text="テーブル:")
        table_label.pack(side=tk.LEFT, padx=(0, 5))

        self.analyze_table_var = tk.StringVar()
        self.analyze_table_combo = ttk.Combobox(table_select_frame, textvariable=self.analyze_table_var,
                                               width=30, state="readonly")
        self.analyze_table_combo.pack(side=tk.LEFT)

        # テーブル選択時のイベント
        self.analyze_table_combo.bind(
            "<<ComboboxSelected>>", self.on_analyze_table_select)

        # カラム選択
        column_select_frame = ttk.Frame(table_frame)
        column_select_frame.pack(fill=tk.X, padx=5, pady=5)

        column_label = ttk.Label(column_select_frame, text="カラム:")
        column_label.pack(side=tk.LEFT, padx=(0, 5))

        self.analyze_column_var = tk.StringVar()
        self.analyze_column_combo = ttk.Combobox(column_select_frame, textvariable=self.analyze_column_var,
                                                width=30, state="readonly")
        self.analyze_column_combo.pack(side=tk.LEFT)

        # 分析タイプフレーム
        analysis_type_frame = ttk.LabelFrame(analyze_frame, text="分析タイプ")
        analysis_type_frame.pack(fill=tk.X, pady=5)

        # 分析タイプ選択
        self.analysis_type_var = tk.StringVar(value="基本統計")

        basic_stats_radio = ttk.Radiobutton(analysis_type_frame, text="基本統計",
                                           variable=self.analysis_type_var, value="基本統計")
        basic_stats_radio.pack(anchor=tk.W, padx=5, pady=2)

        freq_dist_radio = ttk.Radiobutton(analysis_type_frame, text="頻度分布",
                                         variable=self.analysis_type_var, value="頻度分布")
        freq_dist_radio.pack(anchor=tk.W, padx=5, pady=2)

        null_check_radio = ttk.Radiobutton(analysis_type_frame, text="NULL値チェック",
                                          variable=self.analysis_type_var, value="NULL値チェック")
        null_check_radio.pack(anchor=tk.W, padx=5, pady=2)

        duplicate_check_radio = ttk.Radiobutton(analysis_type_frame, text="重複値チェック",
                                               variable=self.analysis_type_var, value="重複値チェック")
        duplicate_check_radio.pack(anchor=tk.W, padx=5, pady=2)

        # 分析実行ボタン
        analyze_button = ttk.Button(
            analyze_frame, text="分析実行", command=self.execute_analysis)
        analyze_button.pack(anchor=tk.W, pady=10)

        # 結果表示フレーム
        result_frame = ttk.LabelFrame(analyze_frame, text="分析結果")
        result_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # 結果表示エリア
        self.analysis_result_text = tk.Text(
            result_frame, wrap=tk.WORD, height=10)
        self.analysis_result_text.pack(
            side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # スクロールバー
        result_scrollbar = ttk.Scrollbar(
            result_frame, orient="vertical", command=self.analysis_result_text.yview)
        self.analysis_result_text.configure(
            yscrollcommand=result_scrollbar.set)
        result_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 結果ツリービュー
        self.analysis_tree_frame = ttk.Frame(analyze_frame)
        self.analysis_tree_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.analysis_tree = ttk.Treeview(self.analysis_tree_frame)

        # スクロールバー
        tree_y_scrollbar = ttk.Scrollbar(
            self.analysis_tree_frame, orient="vertical", command=self.analysis_tree.yview)
        tree_x_scrollbar = ttk.Scrollbar(
            self.analysis_tree_frame, orient="horizontal", command=self.analysis_tree.xview)
        self.analysis_tree.configure(
            yscrollcommand=tree_y_scrollbar.set, xscrollcommand=tree_x_scrollbar.set)

        # 配置
        self.analysis_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree_x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

    def init_code_converter_tab(self):
        """コードフィールド変換タブの初期化"""
        # フレームの作成
        converter_frame = ttk.Frame(self.tab_code_converter)
        converter_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 説明ラベル
        description = (
            "このタブでは、数値型(REAL/INTEGER)として保存されているコードフィールドを文字列型(TEXT)に変換できます。\n\n"
            "コードフィールドを数値型で保存すると以下の問題が発生します：\n"
            "・先頭の0が削除される（例：「001」→「1」）\n"
            "・SAPの後ろマイナス表記（例：「1234-」）が正しく扱われない\n"
            "・テーブル間の結合時にデータ型の不一致が発生する（REALとINTEGERの混在）"
        )
        desc_label = ttk.Label(
            converter_frame, text=description, wraplength=800, justify="left")
        desc_label.pack(fill=tk.X, pady=10)

        # 操作ボタンフレーム
        button_frame = ttk.Frame(converter_frame)
        button_frame.pack(fill=tk.X, pady=5)

        # 分析ボタン
        analyze_button = ttk.Button(
            button_frame, text="変換対象フィールドを分析", command=self.analyze_code_fields)
        analyze_button.pack(side=tk.LEFT, padx=5)

        # 変換ボタン
        self.convert_button = ttk.Button(
            button_frame, text="選択したフィールドを変換", command=self.convert_selected_fields, state="disabled")
        self.convert_button.pack(side=tk.LEFT, padx=5)

        # 全て選択/解除ボタン
        self.select_all_button = ttk.Button(
            button_frame, text="全て選択", command=self.select_all_fields, state="disabled")
        self.select_all_button.pack(side=tk.LEFT, padx=5)

        self.deselect_all_button = ttk.Button(
            button_frame, text="全て解除", command=self.deselect_all_fields, state="disabled")
        self.deselect_all_button.pack(side=tk.LEFT, padx=5)

        # 変換対象フィールド表示エリア
        fields_frame = ttk.LabelFrame(converter_frame, text="変換対象フィールド")
        fields_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # ツリービュー（表形式）でフィールドを表示
        columns = ("select", "table", "column",
                   "current_type", "reason", "sample")
        self.fields_tree = ttk.Treeview(
            fields_frame, columns=columns, show="headings")

        # 列の設定
        self.fields_tree.heading("select", text="選択")
        self.fields_tree.heading("table", text="テーブル")
        self.fields_tree.heading("column", text="カラム")
        self.fields_tree.heading("current_type", text="現在の型")
        self.fields_tree.heading("reason", text="変換理由")
        self.fields_tree.heading("sample", text="サンプル値")

        self.fields_tree.column("select", width=50, anchor="center")
        self.fields_tree.column("table", width=150)
        self.fields_tree.column("column", width=150)
        self.fields_tree.column("current_type", width=80, anchor="center")
        self.fields_tree.column("reason", width=250)
        self.fields_tree.column("sample", width=200)

        # スクロールバー
        tree_scrollbar = ttk.Scrollbar(
            fields_frame, orient="vertical", command=self.fields_tree.yview)
        self.fields_tree.configure(yscrollcommand=tree_scrollbar.set)

        # 配置
        self.fields_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # クリックイベントの設定（チェックボックスの切り替え）
        self.fields_tree.bind("<ButtonRelease-1>", self.toggle_field_selection)

        # 結果表示エリア
        result_frame = ttk.LabelFrame(converter_frame, text="変換結果")
        result_frame.pack(fill=tk.X, pady=5)

        self.conversion_result_var = tk.StringVar(value="変換対象フィールドを分析してください。")
        result_label = ttk.Label(
            result_frame, textvariable=self.conversion_result_var, wraplength=800)
        result_label.pack(fill=tk.X, padx=5, pady=5)

        # フィールドデータを保存する変数
        self.code_fields_data = []

    def connect_database(self):
        """データベースに接続"""
        try:
            # デフォルトのパスを設定
            initial_dir = str(GUI_PROJECT_ROOT / 'data' / 'sqlite')

            # ファイル選択ダイアログを表示
            db_path = filedialog.askopenfilename(
                title="SQLiteデータベースを選択",
                filetypes=[("SQLiteデータベース", "*.db *.sqlite *.sqlite3"),
                            ("すべてのファイル", "*.*")],
                initialdir=initial_dir
            )

            if not db_path:  # キャンセルされた場合
                return

            # 既存の接続を閉じる
            if self.conn:
                self.conn.close()

            # 新しい接続を開く
            self.conn = sqlite3.connect(db_path)
            self.cursor = self.conn.cursor()
            self.db_path = db_path

            # 接続テスト
            self.cursor.execute("SELECT sqlite_version()")
            version = self.cursor.fetchone()[0]

            # テーブル一覧を取得
            self.cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            tables = self.cursor.fetchall()
            table_count = len(tables)

            # ステータスを更新
            self.status_var.set(
                f"データベース接続成功: {os.path.basename(db_path)} (SQLite {version}, テーブル数: {table_count})")

            # 設定を保存
            self.save_config({"last_db_path": db_path})

            # 成功メッセージ
            messagebox.showinfo(
                "接続成功", f"データベース '{os.path.basename(db_path)}' に接続しました。\nテーブル数: {table_count}")

            # 各タブの更新
            self.update_tabs_after_connection()

        except Exception as e:
            messagebox.showerror("接続エラー", f"データベースへの接続中にエラーが発生しました: {str(e)}")
            self.status_var.set("データベース接続に失敗しました")
            print(traceback.format_exc())

    def analyze_code_fields(self):
        """数値型コードフィールドを分析"""
        if not self.conn:
            messagebox.showerror("エラー", "データベースに接続されていません。")
            return

        try:
            # 既存のデータをクリア
            self.fields_tree.delete(*self.fields_tree.get_children())
            self.code_fields_data = []

            # ステータス更新
            self.status_var.set("コードフィールドを分析中...")
            self.root.update()

            # 分析実行
            fields_to_convert, _ = analyze_numeric_code_fields(self.conn)

            if not fields_to_convert:
                messagebox.showinfo("情報", "変換対象のコードフィールドは見つかりませんでした。")
                self.status_var.set("コードフィールドの分析が完了しました。変換対象はありません。")
                return

            # データを保存
            self.code_fields_data = fields_to_convert

            # ツリービューに表示
            for i, field in enumerate(fields_to_convert):
                table = field['table']
                column = field['column']
                current_type = field['current_type']
                reason = field['reason']
                sample_values = ", ".join(
                    [str(val) for val in field['sample_values'][:3]])

                # 選択状態を「✓」で表示
                self.fields_tree.insert("", "end", values=(
                    "☐", table, column, current_type, reason, sample_values), tags=(str(i),))

            # ボタンを有効化
            self.select_all_button.config(state="normal")
            self.deselect_all_button.config(state="normal")
            self.convert_button.config(state="normal")

            # 結果表示
            self.conversion_result_var.set(
                f"{len(fields_to_convert)}個のコードフィールドが変換対象として見つかりました。変換するフィールドを選択してください。")
            self.status_var.set("コードフィールドの分析が完了しました。")

        except Exception as e:
            messagebox.showerror("エラー", f"コードフィールドの分析中にエラーが発生しました: {str(e)}")
            self.status_var.set("コードフィールドの分析中にエラーが発生しました。")
            print(traceback.format_exc())

    def toggle_field_selection(self, event):
        """フィールドの選択状態を切り替え"""
        # クリックされた位置を取得
        region = self.fields_tree.identify("region", event.x, event.y)
        if region != "cell":
            return

        # クリックされた行を取得
        item_id = self.fields_tree.identify_row(event.y)
        if not item_id:
            return

        # クリックされた列を取得
        column = self.fields_tree.identify_column(event.x)
        if column != "#1":  # 選択列（最初の列）のみ処理
            return

        # 現在の値を取得
        values = self.fields_tree.item(item_id, "values")
        if not values:
            return

        # 選択状態を切り替え
        new_values = list(values)
        new_values[0] = "☑" if values[0] == "☐" else "☐"

        # 更新
        self.fields_tree.item(item_id, values=new_values)

    def select_all_fields(self):
        """すべてのフィールドを選択"""
        for item_id in self.fields_tree.get_children():
            values = list(self.fields_tree.item(item_id, "values"))
            values[0] = "☑"
            self.fields_tree.item(item_id, values=values)

    def deselect_all_fields(self):
        """すべてのフィールドの選択を解除"""
        for item_id in self.fields_tree.get_children():
            values = list(self.fields_tree.item(item_id, "values"))
            values[0] = "☐"
            self.fields_tree.item(item_id, values=values)

    def convert_selected_fields(self):
        """選択したフィールドを変換"""
        if not self.conn:
            messagebox.showerror("エラー", "データベースに接続されていません。")
            return

        # 選択されたフィールドを取得
        selected_fields = []
        for item_id in self.fields_tree.get_children():
            values = self.fields_tree.item(item_id, "values")
            if values[0] == "☑":
                tag = self.fields_tree.item(item_id, "tags")[0]
                index = int(tag)
                if 0 <= index < len(self.code_fields_data):
                    selected_fields.append(self.code_fields_data[index])

        if not selected_fields:
            messagebox.showinfo("情報", "変換するフィールドが選択されていません。")
            return

        # 確認ダイアログ
        confirm = messagebox.askyesno(
            "確認",
            f"選択された {len(selected_fields)} 個のフィールドを文字列型に変換します。\n\n" +
            "この操作は元に戻せません。続行しますか？"
        )

        if not confirm:
            return

        try:
            # ステータス更新
            self.status_var.set("フィールドを変換中...")
            self.root.update()

            # 変換実行
            success_count = 0
            failed_fields = []

            for field in selected_fields:
                table = field['table']
                column = field['column']

                success, error = convert_table_column(self.conn, table, column)

                if success:
                    success_count += 1
                else:
                    failed_fields.append({
                        'table': table,
                        'column': column,
                        'error': error
                    })

            # 結果表示
            if failed_fields:
                error_msg = "\n".join(
                    [f"{field['table']}.{field['column']}: {field['error']}" for field in failed_fields])
                messagebox.showwarning(
                    "警告",
                    f"{success_count}/{len(selected_fields)} 個のフィールドの変換が完了しました。\n\n" +
                    f"{len(failed_fields)} 個のフィールドの変換に失敗しました:\n{error_msg}"
                )
            else:
                messagebox.showinfo(
                    "成功", f"{success_count}/{len(selected_fields)} 個のフィールドの変換が完了しました。")

            # 分析を再実行して表示を更新
            self.analyze_code_fields()

        except Exception as e:
            messagebox.showerror("エラー", f"フィールドの変換中にエラーが発生しました: {str(e)}")
            self.status_var.set("フィールドの変換中にエラーが発生しました。")
            print(traceback.format_exc())

    def save_config(self, config_data):
        """設定を保存する"""
        try:
            # 既存の設定を読み込む
            existing_config = {}
            config_path = os.path.join(str(GUI_PROJECT_ROOT), CONFIG_FILE)

            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        existing_config = json.load(f)
                except:
                    pass

            # 新しい設定を追加
            existing_config.update(config_data)

            # 設定を保存
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(existing_config, f, ensure_ascii=False, indent=2)

        except Exception as e:
            print(f"設定の保存中にエラーが発生しました: {str(e)}")
            print(traceback.format_exc())

    def load_config(self):
        """設定を読み込む"""
        try:
            config_path = os.path.join(str(GUI_PROJECT_ROOT), CONFIG_FILE)

            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)

        except Exception as e:
            print(f"設定の読み込み中にエラーが発生しました: {str(e)}")
            print(traceback.format_exc())

        return {}

    def update_tabs_after_connection(self):
        """データベース接続後に各タブを更新する"""
        try:
            # クエリタブの更新
            self.update_query_tab()

            # スキーマタブの更新
            self.update_schema_tab()

            # インポートタブの更新
            self.update_import_tab()

            # エクスポートタブの更新
            self.update_export_tab()

            # データ分析タブの更新
            self.update_analyze_tab()

        except Exception as e:
            print(f"タブの更新中にエラーが発生しました: {str(e)}")
            print(traceback.format_exc())

    def update_query_tab(self):
        """クエリタブを更新する"""
        if not hasattr(self, 'query_text'):
            return

        # テーブル一覧を取得してサンプルクエリを更新
        try:
            if self.conn:
                self.cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
                tables = [row[0] for row in self.cursor.fetchall()]

                if tables:
                    # サンプルクエリの「テーブル名」を実際のテーブル名に置き換え
                    sample_table = tables[0]

                    # テーブルのカラム情報を取得
                    self.cursor.execute(f"PRAGMA table_info({sample_table})")
                    columns = self.cursor.fetchall()

                    if columns:
                        sample_column = columns[0][1]  # 最初のカラム名

                        # サンプルクエリを更新
                        self.sample_queries = [
                            "-- テーブル一覧を表示\nSELECT name FROM sqlite_master WHERE type='table' ORDER BY name;",
                            f"-- テーブルのスキーマを表示\nPRAGMA table_info({sample_table});",
                            f"-- テーブルの最初の10行を表示\nSELECT * FROM {sample_table} LIMIT 10;",
                            f"-- カラムの値の分布を確認\nSELECT {sample_column}, COUNT(*) as count FROM {sample_table} GROUP BY {sample_column} ORDER BY count DESC LIMIT 10;",
                            f"-- NULL値の数を確認\nSELECT COUNT(*) as null_count FROM {sample_table} WHERE {sample_column} IS NULL;",
                        ]

                        # 2つ以上のテーブルがある場合は結合クエリも追加
                        if len(tables) >= 2:
                            second_table = tables[1]
                            self.cursor.execute(
                                f"PRAGMA table_info({second_table})")
                            second_columns = self.cursor.fetchall()

                            if second_columns:
                                self.sample_queries.append(
                                    f"-- テーブル間の結合\nSELECT a.*, b.* FROM {sample_table} a JOIN {second_table} b ON a.{sample_column} = b.{second_columns[0][1]} LIMIT 10;"
                                )
        except Exception as e:
            print(f"クエリタブの更新中にエラーが発生しました: {str(e)}")
            print(traceback.format_exc())

    def update_schema_tab(self):
        """スキーマタブを更新する"""
        if not hasattr(self, 'table_listbox'):
            return

        # テーブル一覧をクリア
        self.table_listbox.delete(0, tk.END)

        try:
            if self.conn:
                # テーブル一覧を取得
                self.cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
                tables = self.cursor.fetchall()

                # テーブル一覧を表示
                for table in tables:
                    self.table_listbox.insert(tk.END, table[0])

                # テーブル情報をリセット
                self.table_name_var.set("テーブルを選択してください")
                self.table_stats_var.set("")

                # カラム情報をクリア
                for item in self.column_tree.get_children():
                    self.column_tree.delete(item)

                # インデックス情報をクリア
                for item in self.index_tree.get_children():
                    self.index_tree.delete(item)

                # ボタンを無効化
                self.show_sql_button.config(state="disabled")
                self.show_sample_button.config(state="disabled")

        except Exception as e:
            print(f"スキーマタブの更新中にエラーが発生しました: {str(e)}")
            print(traceback.format_exc())

    def update_import_tab(self):
        """インポートタブを更新する"""
        # インポートタブが実装されていない場合はスキップ
        pass

    def update_export_tab(self):
        """エクスポートタブを更新する"""
        # エクスポートタブが実装されていない場合はスキップ
        pass

    def update_analyze_tab(self):
        """データ分析タブを更新する"""
        # データ分析タブが実装されていない場合はスキップ
        pass


def main():
    root = tk.Tk()
    app = SQLiteGUITool(root)
    root.mainloop()


if __name__ == "__main__":
    main()
 def execute_query(self):
        """SQLクエリを実行する"""
        if not self.conn:
            messagebox.showerror("エラー", "データベースに接続されていません。")
            return
            
        # クエリを取得
        query = self.query_text.get("1.0", tk.END).strip()
        if not query:
            messagebox.showinfo("情報", "実行するクエリを入力してください。")
            return
            
        try:
            # ステータス更新
            self.status_var.set("クエリを実行中...")
            self.root.update()
            
            # クエリ実行開始時間
            start_time = time.time()
            
            # クエリ実行
            self.cursor.execute(query)
            
            # 結果を取得
            results = self.cursor.fetchall()
            
            # 実行時間
            execution_time = time.time() - start_time
            
            # 列名を取得
            column_names = [description[0] for description in self.cursor.description] if self.cursor.description else []
            
            # 結果を表示
            self.display_query_results(results, column_names)
            
            # 結果情報を更新
            row_count = len(results)
            self.result_info_var.set(f"実行結果: {row_count}行 ({execution_time:.3f}秒)")
            
            # ボタンを有効化
            if row_count > 0:
                self.copy_button.config(state="normal")
                self.export_button.config(state="normal")
            else:
                self.copy_button.config(state="disabled")
                self.export_button.config(state="disabled")
                
            # ステータスを更新
            self.status_var.set(f"クエリ実行完了: {row_count}行 ({execution_time:.3f}秒)")
            
        except sqlite3.Error as e:
            messagebox.showerror("SQLエラー", f"クエリの実行中にエラーが発生しました: {str(e)}")
            self.status_var.set("クエリ実行エラー")
            self.result_info_var.set(f"エラー: {str(e)}")
            print(traceback.format_exc())
            
        except Exception as e:
            messagebox.showerror("エラー", f"予期しないエラーが発生しました: {str(e)}")
            self.status_var.set("クエリ実行エラー")
            self.result_info_var.set(f"エラー: {str(e)}")
            print(traceback.format_exc())
            
    def display_query_results(self, results, column_names):
        """クエリ結果をツリービューに表示する"""
        # 既存の結果をクリア
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)
            
        # 列がない場合は何もしない
        if not column_names:
            return
            
        # 列の設定
        self.result_tree["columns"] = column_names
        self.result_tree["show"] = "headings"  # ヘッダーのみ表示
        
        # 列の見出しと幅を設定
        for col in column_names:
            self.result_tree.heading(col, text=col)
            self.result_tree.column(col, width=100)  # デフォルト幅
            
        # データを挿入
        for row in results:
            # NULL値を「NULL」として表示
            formatted_row = [str(val) if val is not None else "NULL" for val in row]
            self.result_tree.insert("", "end", values=formatted_row)
            
        # 列幅を調整（最大100文字まで）
        if results:
            for i, col in enumerate(column_names):
                # 列の値の最大長を計算
                max_len = len(str(col))
                for row in results[:100]:  # 最初の100行だけ調査
                    val = row[i]
                    if val is not None:
                        val_len = len(str(val))
                        if val_len > max_len:
                            max_len = min(val_len, 100)  # 最大100文字
                
                # 列幅を設定（文字数 * 平均文字幅）
                char_width = 7  # 平均文字幅（ピクセル）
                self.result_tree.column(col, width=max_len * char_width)
                
    def clear_query(self):
        """クエリ入力エリアをクリアする"""
        self.query_text.delete("1.0", tk.END)
        
    def show_query_examples(self):
        """サンプルクエリを表示するダイアログ"""
        example_window = tk.Toplevel(self.root)
        example_window.title("クエリ例")
        example_window.geometry("600x400")
        
        # 説明ラベル
        desc_label = ttk.Label(example_window, text="以下のサンプルクエリから選択してください。ダブルクリックでクエリをコピーします。")
        desc_label.pack(padx=10, pady=10, anchor=tk.W)
        
        # リストボックス
        listbox = tk.Listbox(example_window, width=80, height=15)
        listbox.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
        
        # スクロールバー
        scrollbar = ttk.Scrollbar(listbox, orient="vertical", command=listbox.yview)
        listbox.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # サンプルクエリを追加
        for query in self.sample_queries:
            listbox.insert(tk.END, query.split('\n')[0])  # 最初の行（コメント）のみ表示
            
        # ダブルクリック時の処理
        def on_double_click(event):
            try:
                # 選択されたインデックスを取得
                index = listbox.curselection()[0]
                
                # クエリをクリアして選択されたクエリを挿入
                self.query_text.delete("1.0", tk.END)
                self.query_text.insert("1.0", self.sample_queries[index])
                
                # ウィンドウを閉じる
                example_window.destroy()
            except IndexError:
                pass
                
        listbox.bind("<Double-1>", on_double_click)
        
        # 閉じるボタン
        close_button = ttk.Button(example_window, text="閉じる", command=example_window.destroy)
        close_button.pack(pady=10)
        
    def copy_results(self):
        """クエリ結果をクリップボードにコピーする"""
        if not pyperclip:
            messagebox.showwarning("警告", "pyperclipモジュールがインストールされていないため、コピー機能は使用できません。\n\npip install pyperclipでインストールしてください。")
            return
            
        try:
            # 列名を取得
            columns = self.result_tree["columns"]
            
            # 結果を取得
            rows = []
            for item_id in self.result_tree.get_children():
                values = self.result_tree.item(item_id, "values")
                rows.append(values)
                
            if not rows:
                return
                
            # TSV形式に変換
            tsv_data = "\t".join(columns) + "\n"
            for row in rows:
                tsv_data += "\t".join([str(val) for val in row]) + "\n"
                
            # クリップボードにコピー
            pyperclip.copy(tsv_data)
            
            # 成功メッセージ
            self.status_var.set(f"{len(rows)}行のデータをクリップボードにコピーしました。")
            messagebox.showinfo("成功", f"{len(rows)}行のデータをクリップボードにコピーしました。")
            
        except Exception as e:
            messagebox.showerror("エラー", f"データのコピー中にエラーが発生しました: {str(e)}")
            print(traceback.format_exc())
            
    def export_results(self):
        """クエリ結果をCSVファイルにエクスポートする"""
        try:
            # 列名を取得
            columns = self.result_tree["columns"]
            
            # 結果を取得
            rows = []
            for item_id in self.result_tree.get_children():
                values = self.result_tree.item(item_id, "values")
                rows.append(values)
                
            if not rows:
                return
                
            # 保存先を選択
            file_path = filedialog.asksaveasfilename(
                title="CSVファイルを保存",
                filetypes=[("CSVファイル", "*.csv"), ("すべてのファイル", "*.*")],
                defaultextension=".csv"
            )
            
            if not file_path:
                return
                
            # CSVファイルに書き込み
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(columns)
                writer.writerows(rows)
                
            # 成功メッセージ
            self.status_var.set(f"{len(rows)}行のデータをCSVファイルにエクスポートしました。")
            messagebox.showinfo("成功", f"{len(rows)}行のデータをCSVファイル '{os.path.basename(file_path)}' にエクスポートしました。")
            
        except Exception as e:
            messagebox.showerror("エラー", f"データのエクスポート中にエラーが発生しました: {str(e)}")
            print(traceback.format_exc()) 
   def on_table_select(self, event):
        """テーブルが選択されたときの処理"""
        if not self.conn:
            return
            
        # 選択されたテーブルを取得
        selection = self.table_listbox.curselection()
        if not selection:
            return
            
        table_name = self.table_listbox.get(selection[0])
        self.show_table_info(table_name)
        
    def show_table_info(self, table_name):
        """テーブル情報を表示する"""
        try:
            # テーブル名を表示
            self.table_name_var.set(table_name)
            
            # テーブルの行数を取得
            self.cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = self.cursor.fetchone()[0]
            
            # テーブルのサイズを概算（SQLiteでは正確なサイズを取得するのは難しい）
            self.cursor.execute(f"PRAGMA page_count, page_size, table_info({table_name})")
            table_info = self.cursor.fetchall()
            column_count = len(table_info)
            
            # テーブル統計情報を表示
            self.table_stats_var.set(f"行数: {row_count:,}  |  カラム数: {column_count}")
            
            # カラム情報を表示
            self.show_column_info(table_name)
            
            # インデックス情報を表示
            self.show_index_info(table_name)
            
            # ボタンを有効化
            self.show_sql_button.config(state="normal")
            self.show_sample_button.config(state="normal")
            
        except Exception as e:
            messagebox.showerror("エラー", f"テーブル情報の取得中にエラーが発生しました: {str(e)}")
            print(traceback.format_exc())
            
    def show_column_info(self, table_name):
        """カラム情報を表示する"""
        try:
            # 既存のカラム情報をクリア
            for item in self.column_tree.get_children():
                self.column_tree.delete(item)
                
            # カラム情報を取得
            self.cursor.execute(f"PRAGMA table_info({table_name})")
            columns = self.cursor.fetchall()
            
            # カラム情報を表示
            for column in columns:
                cid, name, type_, notnull, dflt_value, pk = column
                
                # NOT NULLとPKを「はい/いいえ」で表示
                notnull_text = "はい" if notnull else "いいえ"
                pk_text = "はい" if pk else "いいえ"
                
                # デフォルト値がNoneの場合は空文字列に
                dflt_value = dflt_value if dflt_value is not None else ""
                
                self.column_tree.insert("", "end", values=(cid, name, type_, notnull_text, dflt_value, pk_text))
                
        except Exception as e:
            messagebox.showerror("エラー", f"カラム情報の取得中にエラーが発生しました: {str(e)}")
            print(traceback.format_exc())
            
    def show_index_info(self, table_name):
        """インデックス情報を表示する"""
        try:
            # 既存のインデックス情報をクリア
            for item in self.index_tree.get_children():
                self.index_tree.delete(item)
                
            # インデックス一覧を取得
            self.cursor.execute(f"PRAGMA index_list({table_name})")
            indexes = self.cursor.fetchall()
            
            # インデックス情報を表示
            for index in indexes:
                index_name = index[1]
                is_unique = "はい" if index[2] else "いいえ"
                
                # インデックスのカラム情報を取得
                self.cursor.execute(f"PRAGMA index_info({index_name})")
                index_columns = self.cursor.fetchall()
                
                # カラム名のリストを作成
                column_names = []
                for idx_col in index_columns:
                    col_pos, col_idx = idx_col[0], idx_col[1]
                    self.cursor.execute(f"PRAGMA table_info({table_name})")
                    table_columns = self.cursor.fetchall()
                    if col_idx < len(table_columns):
                        column_names.append(table_columns[col_idx][1])
                
                # カラム名をカンマで結合
                columns_text = ", ".join(column_names)
                
                self.index_tree.insert("", "end", values=(index_name, is_unique, columns_text))
                
        except Exception as e:
            messagebox.showerror("エラー", f"インデックス情報の取得中にエラーが発生しました: {str(e)}")
            print(traceback.format_exc())
            
    def show_create_sql(self):
        """CREATE文を表示する"""
        # 選択されたテーブルを取得
        selection = self.table_listbox.curselection()
        if not selection:
            return
            
        table_name = self.table_listbox.get(selection[0])
        
        try:
            # CREATE文を取得
            self.cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
            create_sql = self.cursor.fetchone()[0]
            
            # インデックスのCREATE文を取得
            self.cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='index' AND tbl_name=?", (table_name,))
            index_sqls = [row[0] for row in self.cursor.fetchall() if row[0] is not None]
            
            # 結果を表示するダイアログ
            sql_window = tk.Toplevel(self.root)
            sql_window.title(f"CREATE文 - {table_name}")
            sql_window.geometry("600x400")
            
            # テキストエリア
            sql_text = tk.Text(sql_window, wrap=tk.WORD)
            sql_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # スクロールバー
            scrollbar = ttk.Scrollbar(sql_text, orient="vertical", command=sql_text.yview)
            sql_text.configure(yscrollcommand=scrollbar.set)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # CREATE文を挿入
            sql_text.insert(tk.END, create_sql + ";\n\n")
            
            # インデックスのCREATE文を挿入
            if index_sqls:
                sql_text.insert(tk.END, "-- インデックス\n")
                for index_sql in index_sqls:
                    sql_text.insert(tk.END, index_sql + ";\n")
                    
            # 編集不可に設定
            sql_text.configure(state="disabled")
            
            # コピーボタン
            def copy_sql():
                if pyperclip:
                    pyperclip.copy(sql_text.get("1.0", tk.END))
                    messagebox.showinfo("成功", "SQLをクリップボードにコピーしました。")
                else:
                    messagebox.showwarning("警告", "pyperclipモジュールがインストールされていないため、コピー機能は使用できません。")
            
            copy_button = ttk.Button(sql_window, text="SQLをコピー", command=copy_sql)
            copy_button.pack(side=tk.LEFT, padx=10, pady=10)
            
            # 閉じるボタン
            close_button = ttk.Button(sql_window, text="閉じる", command=sql_window.destroy)
            close_button.pack(side=tk.RIGHT, padx=10, pady=10)
            
        except Exception as e:
            messagebox.showerror("エラー", f"CREATE文の取得中にエラーが発生しました: {str(e)}")
            print(traceback.format_exc())
            
    def show_sample_data(self):
        """サンプルデータを表示する"""
        # 選択されたテーブルを取得
        selection = self.table_listbox.curselection()
        if not selection:
            return
            
        table_name = self.table_listbox.get(selection[0])
        
        try:
            # サンプルデータを取得（最大100行）
            self.cursor.execute(f"SELECT * FROM {table_name} LIMIT 100")
            rows = self.cursor.fetchall()
            
            # 列名を取得
            column_names = [description[0] for description in self.cursor.description]
            
            # 結果を表示するダイアログ
            data_window = tk.Toplevel(self.root)
            data_window.title(f"サンプルデータ - {table_name}")
            data_window.geometry("800x500")
            
            # ツリービュー
            tree_frame = ttk.Frame(data_window)
            tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # ツリービューの設定
            tree = ttk.Treeview(tree_frame, columns=column_names, show="headings")
            
            # 列の設定
            for col in column_names:
                tree.heading(col, text=col)
                tree.column(col, width=100)
                
            # データを挿入
            for row in rows:
                # NULL値を「NULL」として表示
                formatted_row = [str(val) if val is not None else "NULL" for val in row]
                tree.insert("", "end", values=formatted_row)
                
            # スクロールバー
            y_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
            x_scrollbar = ttk.Scrollbar(tree_frame, orient="horizontal", command=tree.xview)
            tree.configure(yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set)
            
            # 配置
            tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
            
            # 情報ラベル
            info_text = f"表示: {len(rows)}行 / 全{self.get_table_row_count(table_name):,}行"
            info_label = ttk.Label(data_window, text=info_text)
            info_label.pack(anchor=tk.W, padx=10)
            
            # 閉じるボタン
            close_button = ttk.Button(data_window, text="閉じる", command=data_window.destroy)
            close_button.pack(pady=10)
            
        except Exception as e:
            messagebox.showerror("エラー", f"サンプルデータの取得中にエラーが発生しました: {str(e)}")
            print(traceback.format_exc())
            
    def get_table_row_count(self, table_name):
        """テーブルの行数を取得する"""
        try:
            self.cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            return self.cursor.fetchone()[0]
        except:
            return 0 
   def update_import_tab(self):
        """インポートタブを更新する"""
        # 特に更新する必要がない場合は何もしない
        pass
        
    def browse_import_file(self):
        """インポートするファイルを選択する"""
        filetypes = [
            ("すべてのサポートされるファイル", "*.csv *.tsv *.txt *.xlsx *.xls"),
            ("CSVファイル", "*.csv"),
            ("TSVファイル", "*.tsv *.txt"),
            ("Excelファイル", "*.xlsx *.xls"),
            ("すべてのファイル", "*.*")
        ]
        
        # ファイル選択ダイアログを表示
        file_path = filedialog.askopenfilename(
            title="インポートするファイルを選択",
            filetypes=filetypes,
            initialdir=str(Paths().RAW_DATA)
        )
        
        if not file_path:
            return
            
        # ファイルパスを設定
        self.import_path_var.set(file_path)
        
        # ファイル名からテーブル名を推測
        file_name = os.path.basename(file_path)
        table_name = os.path.splitext(file_name)[0]
        self.table_name_entry_var.set(table_name)
        
        # ファイルタイプを推測
        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.csv':
            self.file_type_var.set("CSV")
        elif ext in ['.tsv', '.txt']:
            self.file_type_var.set("TSV")
        elif ext in ['.xlsx', '.xls']:
            self.file_type_var.set("Excel")
        else:
            self.file_type_var.set("自動検出")
            
    def on_table_name_change(self, *args):
        """テーブル名が変更されたときの処理"""
        table_name = self.table_name_entry_var.get()
        if table_name:
            sanitized = sanitize_table_name(table_name)
            if sanitized != table_name:
                self.sanitized_name_var.set(f"→ {sanitized}")
            else:
                self.sanitized_name_var.set("")
        else:
            self.sanitized_name_var.set("")
            
    def preview_import_data(self):
        """インポートデータのプレビューを表示する"""
        file_path = self.import_path_var.get()
        if not file_path or not os.path.exists(file_path):
            messagebox.showerror("エラー", "有効なファイルパスを入力してください。")
            return
            
        try:
            # ステータス更新
            self.status_var.set("データをプレビュー中...")
            self.root.update()
            
            # ファイルタイプを取得
            file_type = self.file_type_var.get()
            if file_type == "自動検出":
                ext = os.path.splitext(file_path)[1].lower()
                if ext == '.csv':
                    file_type = "CSV"
                elif ext in ['.tsv', '.txt']:
                    file_type = "TSV"
                elif ext in ['.xlsx', '.xls']:
                    file_type = "Excel"
                else:
                    file_type = "CSV"  # デフォルト
                    
            # エンコーディングを取得
            encoding = self.encoding_var.get()
            if encoding == "自動検出":
                encoding = None  # SQLiteManagerで自動検出
                
            # 区切り文字を取得
            delimiter = self.delimiter_var.get()
            if delimiter == "自動検出":
                delimiter = None  # SQLiteManagerで自動検出
            elif delimiter == "\\t":
                delimiter = "\t"
                
            # ヘッダーの有無
            header = 0 if self.header_var.get() else None
            
            # プレビューデータを読み込む（最大10行）
            if file_type in ["CSV", "TSV"]:
                # CSVまたはTSVファイル
                import pandas as pd
                try:
                    df = pd.read_csv(file_path, sep=delimiter, encoding=encoding or 'utf-8', 
                                    header=header, nrows=10)
                except UnicodeDecodeError:
                    # UTF-8で失敗した場合はCP932を試す
                    df = pd.read_csv(file_path, sep=delimiter, encoding='cp932', 
                                    header=header, nrows=10)
            elif file_type == "Excel":
                # Excelファイル
                import pandas as pd
                df = pd.read_excel(file_path, header=header, nrows=10)
            else:
                messagebox.showerror("エラー", f"サポートされていないファイルタイプです: {file_type}")
                return
                
            # プレビューを表示
            self.display_preview_data(df)
            
            # ステータスを更新
            self.status_var.set(f"データプレビュー完了: {file_path}")
            
        except Exception as e:
            messagebox.showerror("エラー", f"データのプレビュー中にエラーが発生しました: {str(e)}")
            self.status_var.set("データプレビューエラー")
            print(traceback.format_exc())
            
    def display_preview_data(self, df):
        """プレビューデータをツリービューに表示する"""
        try:
            # 既存のデータをクリア
            for item in self.preview_tree.get_children():
                self.preview_tree.delete(item)
                
            # 列の設定
            columns = list(df.columns)
            self.preview_tree["columns"] = columns
            self.preview_tree["show"] = "headings"  # ヘッダーのみ表示
            
            # 列の見出しと幅を設定
            for col in columns:
                self.preview_tree.heading(col, text=str(col))
                self.preview_tree.column(col, width=100)  # デフォルト幅
                
            # データを挿入
            for _, row in df.iterrows():
                # NULL値を「NULL」として表示
                formatted_row = [str(val) if pd.notna(val) else "NULL" for val in row]
                self.preview_tree.insert("", "end", values=formatted_row)
                
            # 列幅を調整
            for i, col in enumerate(columns):
                # 列の値の最大長を計算
                max_len = len(str(col))
                for _, row in df.iterrows():
                    val = row[i]
                    if pd.notna(val):
                        val_len = len(str(val))
                        if val_len > max_len:
                            max_len = min(val_len, 50)  # 最大50文字
                
                # 列幅を設定（文字数 * 平均文字幅）
                char_width = 7  # 平均文字幅（ピクセル）
                self.preview_tree.column(col, width=max_len * char_width)
                
        except Exception as e:
            messagebox.showerror("エラー", f"プレビューの表示中にエラーが発生しました: {str(e)}")
            print(traceback.format_exc())
            
    def execute_import(self):
        """データのインポートを実行する"""
        file_path = self.import_path_var.get()
        if not file_path or not os.path.exists(file_path):
            messagebox.showerror("エラー", "有効なファイルパスを入力してください。")
            return
            
        if not self.conn:
            messagebox.showerror("エラー", "データベースに接続されていません。")
            return
            
        # テーブル名を取得
        table_name = self.table_name_entry_var.get()
        if not table_name:
            messagebox.showerror("エラー", "テーブル名を入力してください。")
            return
            
        # テーブル名を変換
        sanitized_table_name = sanitize_table_name(table_name)
        
        # 既存テーブルの処理方法
        if_exists = self.existing_var.get()
        if if_exists == "置換":
            if_exists = "replace"
        elif if_exists == "追加":
            if_exists = "append"
        elif if_exists == "エラー":
            if_exists = "fail"
            
        try:
            # ステータス更新
            self.status_var.set("データをインポート中...")
            self.root.update()
            
            # インポート開始時間
            start_time = time.time()
            
            # ファイルタイプを取得
            file_type = self.file_type_var.get()
            if file_type == "自動検出":
                ext = os.path.splitext(file_path)[1].lower()
                if ext == '.csv':
                    file_type = "CSV"
                elif ext in ['.tsv', '.txt']:
                    file_type = "TSV"
                elif ext in ['.xlsx', '.xls']:
                    file_type = "Excel"
                else:
                    file_type = "CSV"  # デフォルト
                    
            # エンコーディングを取得
            encoding = self.encoding_var.get()
            if encoding == "自動検出":
                encoding = None  # SQLiteManagerで自動検出
                
            # 区切り文字を取得
            delimiter = self.delimiter_var.get()
            if delimiter == "自動検出":
                delimiter = None  # SQLiteManagerで自動検出
            elif delimiter == "\\t":
                delimiter = "\t"
                
            # ヘッダーの有無
            header = 0 if self.header_var.get() else None
            
            # データをインポート
            if file_type in ["CSV", "TSV"]:
                # CSVまたはTSVファイル
                import pandas as pd
                try:
                    df = pd.read_csv(file_path, sep=delimiter, encoding=encoding or 'utf-8', header=header)
                except UnicodeDecodeError:
                    # UTF-8で失敗した場合はCP932を試す
                    df = pd.read_csv(file_path, sep=delimiter, encoding='cp932', header=header)
            elif file_type == "Excel":
                # Excelファイル
                import pandas as pd
                df = pd.read_excel(file_path, header=header)
            else:
                messagebox.showerror("エラー", f"サポートされていないファイルタイプです: {file_type}")
                return
                
            # データをSQLiteに書き込む
            df.to_sql(sanitized_table_name, self.conn, if_exists=if_exists, index=False)
            
            # 実行時間
            execution_time = time.time() - start_time
            
            # 結果を表示
            row_count = len(df)
            self.import_result_var.set(f"{row_count:,}行のデータを '{sanitized_table_name}' テーブルにインポートしました。({execution_time:.2f}秒)")
            
            # ステータスを更新
            self.status_var.set(f"データインポート完了: {row_count:,}行 ({execution_time:.2f}秒)")
            
            # 成功メッセージ
            messagebox.showinfo("成功", f"{row_count:,}行のデータを '{sanitized_table_name}' テーブルにインポートしました。")
            
            # スキーマタブを更新
            self.update_schema_tab()
            
        except Exception as e:
            messagebox.showerror("エラー", f"データのインポート中にエラーが発生しました: {str(e)}")
            self.status_var.set("データインポートエラー")
            self.import_result_var.set(f"エラー: {str(e)}")
            print(traceback.format_exc())    de
f update_export_tab(self):
        """エクスポートタブを更新する"""
        if not hasattr(self, 'export_table_combo'):
            return
            
        try:
            if self.conn:
                # テーブル一覧を取得
                self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
                tables = [row[0] for row in self.cursor.fetchall()]
                
                # テーブル一覧をコンボボックスに設定
                self.export_table_combo['values'] = tables
                
                # テーブルが存在する場合は最初のテーブルを選択
                if tables:
                    self.export_table_var.set(tables[0])
                    
        except Exception as e:
            print(f"エクスポートタブの更新中にエラーが発生しました: {str(e)}")
            print(traceback.format_exc())
            
    def toggle_export_method(self):
        """エクスポート方法に応じてUIを切り替える"""
        method = self.export_method_var.get()
        
        if method == "テーブル":
            self.table_select_frame.pack(fill=tk.X, pady=5)
            self.query_frame.pack_forget()
        else:  # クエリ
            self.table_select_frame.pack_forget()
            self.query_frame.pack(fill=tk.X, pady=5)
            
    def on_export_format_change(self, *args):
        """出力形式が変更されたときの処理"""
        format_type = self.export_format_var.get()
        
        if format_type == "CSV":
            self.encoding_frame.pack(fill=tk.X, padx=5, pady=5)
        else:  # Excel
            self.encoding_frame.pack_forget()
            
    def browse_export_path(self):
        """エクスポート先のファイルパスを選択する"""
        format_type = self.export_format_var.get()
        
        if format_type == "CSV":
            filetypes = [("CSVファイル", "*.csv"), ("すべてのファイル", "*.*")]
            defaultextension = ".csv"
        else:  # Excel
            filetypes = [("Excelファイル", "*.xlsx"), ("すべてのファイル", "*.*")]
            defaultextension = ".xlsx"
            
        # 選択されているテーブル名またはクエリから出力ファイル名を推測
        if self.export_method_var.get() == "テーブル":
            table_name = self.export_table_var.get()
            default_filename = f"{table_name}{defaultextension}" if table_name else f"export{defaultextension}"
        else:
            default_filename = f"query_result{defaultextension}"
            
        # ファイル保存ダイアログを表示
        file_path = filedialog.asksaveasfilename(
            title="エクスポート先を選択",
            filetypes=filetypes,
            defaultextension=defaultextension,
            initialfile=default_filename,
            initialdir=str(GUI_PROJECT_ROOT)
        )
        
        if file_path:
            self.export_path_var.set(file_path)
            
    def preview_export_data(self):
        """エクスポートデータのプレビューを表示する"""
        if not self.conn:
            messagebox.showerror("エラー", "データベースに接続されていません。")
            return
            
        try:
            # ステータス更新
            self.status_var.set("データをプレビュー中...")
            self.root.update()
            
            # クエリを取得
            if self.export_method_var.get() == "テーブル":
                table_name = self.export_table_var.get()
                if not table_name:
                    messagebox.showerror("エラー", "エクスポートするテーブルを選択してください。")
                    return
                    
                query = f"SELECT * FROM {table_name} LIMIT 10"
            else:
                query = self.export_query_text.get("1.0", tk.END).strip()
                if not query:
                    messagebox.showerror("エラー", "SQLクエリを入力してください。")
                    return
                    
                # LIMITが指定されていない場合は追加
                if "LIMIT" not in query.upper():
                    query += " LIMIT 10"
                    
            # クエリ実行
            self.cursor.execute(query)
            
            # 結果を取得
            results = self.cursor.fetchall()
            
            # 列名を取得
            column_names = [description[0] for description in self.cursor.description] if self.cursor.description else []
            
            # プレビューを表示
            self.display_export_preview(results, column_names)
            
            # ステータスを更新
            self.status_var.set(f"データプレビュー完了: {len(results)}行")
            
        except Exception as e:
            messagebox.showerror("エラー", f"データのプレビュー中にエラーが発生しました: {str(e)}")
            self.status_var.set("データプレビューエラー")
            print(traceback.format_exc())
            
    def display_export_preview(self, results, column_names):
        """エクスポートプレビューデータをツリービューに表示する"""
        try:
            # 既存のデータをクリア
            for item in self.export_preview_tree.get_children():
                self.export_preview_tree.delete(item)
                
            # 列がない場合は何もしない
            if not column_names:
                return
                
            # 列の設定
            self.export_preview_tree["columns"] = column_names
            self.export_preview_tree["show"] = "headings"  # ヘッダーのみ表示
            
            # 列の見出しと幅を設定
            for col in column_names:
                self.export_preview_tree.heading(col, text=str(col))
                self.export_preview_tree.column(col, width=100)  # デフォルト幅
                
            # データを挿入
            for row in results:
                # NULL値を「NULL」として表示
                formatted_row = [str(val) if val is not None else "NULL" for val in row]
                self.export_preview_tree.insert("", "end", values=formatted_row)
                
            # 列幅を調整
            if results:
                for i, col in enumerate(column_names):
                    # 列の値の最大長を計算
                    max_len = len(str(col))
                    for row in results:
                        val = row[i]
                        if val is not None:
                            val_len = len(str(val))
                            if val_len > max_len:
                                max_len = min(val_len, 50)  # 最大50文字
                    
                    # 列幅を設定（文字数 * 平均文字幅）
                    char_width = 7  # 平均文字幅（ピクセル）
                    self.export_preview_tree.column(col, width=max_len * char_width)
                    
        except Exception as e:
            messagebox.showerror("エラー", f"プレビューの表示中にエラーが発生しました: {str(e)}")
            print(traceback.format_exc())
            
    def execute_export(self):
        """データのエクスポートを実行する"""
        if not self.conn:
            messagebox.showerror("エラー", "データベースに接続されていません。")
            return
            
        # 出力先パスを取得
        output_path = self.export_path_var.get()
        if not output_path:
            messagebox.showerror("エラー", "エクスポート先のファイルパスを指定してください。")
            return
            
        try:
            # ステータス更新
            self.status_var.set("データをエクスポート中...")
            self.root.update()
            
            # エクスポート開始時間
            start_time = time.time()
            
            # クエリを取得
            if self.export_method_var.get() == "テーブル":
                table_name = self.export_table_var.get()
                if not table_name:
                    messagebox.showerror("エラー", "エクスポートするテーブルを選択してください。")
                    return
                    
                query = f"SELECT * FROM {table_name}"
            else:
                query = self.export_query_text.get("1.0", tk.END).strip()
                if not query:
                    messagebox.showerror("エラー", "SQLクエリを入力してください。")
                    return
                    
            # クエリ実行
            self.cursor.execute(query)
            
            # 結果を取得
            results = self.cursor.fetchall()
            
            # 列名を取得
            column_names = [description[0] for description in self.cursor.description] if self.cursor.description else []
            
            # 出力形式を取得
            format_type = self.export_format_var.get()
            
            # データをエクスポート
            if format_type == "CSV":
                # エンコーディングを取得
                encoding = self.export_encoding_var.get()
                
                # CSVファイルに書き込み
                with open(output_path, 'w', newline='', encoding=encoding) as f:
                    writer = csv.writer(f)
                    writer.writerow(column_names)
                    writer.writerows(results)
            else:  # Excel
                # DataFrameに変換
                import pandas as pd
                df = pd.DataFrame(results, columns=column_names)
                
                # Excelファイルに書き込み
                df.to_excel(output_path, index=False)
                
            # 実行時間
            execution_time = time.time() - start_time
            
            # 結果を表示
            row_count = len(results)
            self.export_result_var.set(f"{row_count:,}行のデータを '{os.path.basename(output_path)}' にエクスポートしました。({execution_time:.2f}秒)")
            
            # ステータスを更新
            self.status_var.set(f"データエクスポート完了: {row_count:,}行 ({execution_time:.2f}秒)")
            
            # 成功メッセージ
            messagebox.showinfo("成功", f"{row_count:,}行のデータを '{os.path.basename(output_path)}' にエクスポートしました。")
            
        except Exception as e:
            messagebox.showerror("エラー", f"データのエクスポート中にエラーが発生しました: {str(e)}")
            self.status_var.set("データエクスポートエラー")
            self.export_result_var.set(f"エラー: {str(e)}")
            print(traceback.format_exc())    def 
update_analyze_tab(self):
        """データ分析タブを更新する"""
        if not hasattr(self, 'analyze_table_combo'):
            return
            
        try:
            if self.conn:
                # テーブル一覧を取得
                self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
                tables = [row[0] for row in self.cursor.fetchall()]
                
                # テーブル一覧をコンボボックスに設定
                self.analyze_table_combo['values'] = tables
                
                # テーブルが存在する場合は最初のテーブルを選択
                if tables:
                    self.analyze_table_var.set(tables[0])
                    self.on_analyze_table_select(None)
                    
        except Exception as e:
            print(f"データ分析タブの更新中にエラーが発生しました: {str(e)}")
            print(traceback.format_exc())
            
    def on_analyze_table_select(self, event):
        """テーブルが選択されたときの処理"""
        if not self.conn:
            return
            
        table_name = self.analyze_table_var.get()
        if not table_name:
            return
            
        try:
            # カラム一覧を取得
            self.cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [row[1] for row in self.cursor.fetchall()]
            
            # カラム一覧をコンボボックスに設定
            self.analyze_column_combo['values'] = columns
            
            # カラムが存在する場合は最初のカラムを選択
            if columns:
                self.analyze_column_var.set(columns[0])
                
        except Exception as e:
            print(f"カラム一覧の取得中にエラーが発生しました: {str(e)}")
            print(traceback.format_exc())
            
    def execute_analysis(self):
        """データ分析を実行する"""
        if not self.conn:
            messagebox.showerror("エラー", "データベースに接続されていません。")
            return
            
        table_name = self.analyze_table_var.get()
        column_name = self.analyze_column_var.get()
        analysis_type = self.analysis_type_var.get()
        
        if not table_name or not column_name:
            messagebox.showerror("エラー", "テーブルとカラムを選択してください。")
            return
            
        try:
            # ステータス更新
            self.status_var.set("データ分析を実行中...")
            self.root.update()
            
            # 分析開始時間
            start_time = time.time()
            
            # 分析タイプに応じた処理
            if analysis_type == "基本統計":
                self.analyze_basic_stats(table_name, column_name)
            elif analysis_type == "頻度分布":
                self.analyze_frequency_distribution(table_name, column_name)
            elif analysis_type == "NULL値チェック":
                self.analyze_null_values(table_name, column_name)
            elif analysis_type == "重複値チェック":
                self.analyze_duplicate_values(table_name, column_name)
                
            # 実行時間
            execution_time = time.time() - start_time
            
            # ステータスを更新
            self.status_var.set(f"データ分析完了: {analysis_type} ({execution_time:.2f}秒)")
            
        except Exception as e:
            messagebox.showerror("エラー", f"データ分析中にエラーが発生しました: {str(e)}")
            self.status_var.set("データ分析エラー")
            self.analysis_result_text.delete("1.0", tk.END)
            self.analysis_result_text.insert(tk.END, f"エラー: {str(e)}")
            print(traceback.format_exc())
            
    def analyze_basic_stats(self, table_name, column_name):
        """基本統計分析を実行する"""
        try:
            # カラムのデータ型を取得
            self.cursor.execute(f"PRAGMA table_info({table_name})")
            columns = self.cursor.fetchall()
            column_type = None
            
            for col in columns:
                if col[1] == column_name:
                    column_type = col[2].upper()
                    break
                    
            # 数値型かどうかを判定
            is_numeric = column_type in ["INTEGER", "REAL", "NUMERIC", "FLOAT", "DOUBLE"]
            
            # 基本統計クエリ
            if is_numeric:
                query = f"""
                SELECT 
                    COUNT(*) as count,
                    COUNT(DISTINCT {column_name}) as unique_count,
                    MIN({column_name}) as min_value,
                    MAX({column_name}) as max_value,
                    AVG({column_name}) as avg_value,
                    SUM({column_name}) as sum_value
                FROM {table_name}
                WHERE {column_name} IS NOT NULL
                """
            else:
                query = f"""
                SELECT 
                    COUNT(*) as count,
                    COUNT(DISTINCT {column_name}) as unique_count,
                    MIN({column_name}) as min_value,
                    MAX({column_name}) as max_value
                FROM {table_name}
                WHERE {column_name} IS NOT NULL
                """
                
            # クエリ実行
            self.cursor.execute(query)
            result = self.cursor.fetchone()
            
            # NULL値の数を取得
            self.cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE {column_name} IS NULL")
            null_count = self.cursor.fetchone()[0]
            
            # 結果を表示
            self.analysis_result_text.delete("1.0", tk.END)
            self.analysis_result_text.insert(tk.END, f"テーブル: {table_name}\n")
            self.analysis_result_text.insert(tk.END, f"カラム: {column_name}\n")
            self.analysis_result_text.insert(tk.END, f"データ型: {column_type}\n\n")
            self.analysis_result_text.insert(tk.END, f"行数: {result[0]:,}\n")
            self.analysis_result_text.insert(tk.END, f"ユニーク値の数: {result[1]:,}\n")
            self.analysis_result_text.insert(tk.END, f"NULL値の数: {null_count:,}\n")
            self.analysis_result_text.insert(tk.END, f"最小値: {result[2]}\n")
            self.analysis_result_text.insert(tk.END, f"最大値: {result[3]}\n")
            
            if is_numeric:
                self.analysis_result_text.insert(tk.END, f"平均値: {result[4]:.4f}\n")
                self.analysis_result_text.insert(tk.END, f"合計値: {result[5]:,}\n")
                
                # 分位数を計算
                self.cursor.execute(f"""
                SELECT {column_name} FROM {table_name}
                WHERE {column_name} IS NOT NULL
                ORDER BY {column_name}
                """)
                values = [row[0] for row in self.cursor.fetchall()]
                
                if values:
                    # 中央値（50パーセンタイル）
                    median_idx = len(values) // 2
                    median = values[median_idx] if len(values) % 2 == 1 else (values[median_idx-1] + values[median_idx]) / 2
                    
                    # 25パーセンタイル
                    q1_idx = len(values) // 4
                    q1 = values[q1_idx]
                    
                    # 75パーセンタイル
                    q3_idx = len(values) * 3 // 4
                    q3 = values[q3_idx]
                    
                    self.analysis_result_text.insert(tk.END, f"中央値: {median:.4f}\n")
                    self.analysis_result_text.insert(tk.END, f"第1四分位数 (25%): {q1:.4f}\n")
                    self.analysis_result_text.insert(tk.END, f"第3四分位数 (75%): {q3:.4f}\n")
                    
            # ツリービューをクリア
            for item in self.analysis_tree.get_children():
                self.analysis_tree.delete(item)
                
        except Exception as e:
            messagebox.showerror("エラー", f"基本統計分析中にエラーが発生しました: {str(e)}")
            print(traceback.format_exc())
            
    def analyze_frequency_distribution(self, table_name, column_name):
        """頻度分布分析を実行する"""
        try:
            # 頻度分布クエリ
            query = f"""
            SELECT 
                {column_name},
                COUNT(*) as frequency
            FROM {table_name}
            WHERE {column_name} IS NOT NULL
            GROUP BY {column_name}
            ORDER BY frequency DESC
            LIMIT 100
            """
            
            # クエリ実行
            self.cursor.execute(query)
            results = self.cursor.fetchall()
            
            # 結果を表示
            self.analysis_result_text.delete("1.0", tk.END)
            self.analysis_result_text.insert(tk.END, f"テーブル: {table_name}\n")
            self.analysis_result_text.insert(tk.END, f"カラム: {column_name}\n\n")
            self.analysis_result_text.insert(tk.END, f"頻度分布（上位100件）:\n")
            
            # ツリービューをクリア
            for item in self.analysis_tree.get_children():
                self.analysis_tree.delete(item)
                
            # ツリービューの設定
            self.analysis_tree["columns"] = ("value", "frequency", "percentage")
            self.analysis_tree["show"] = "headings"
            
            self.analysis_tree.heading("value", text="値")
            self.analysis_tree.heading("frequency", text="頻度")
            self.analysis_tree.heading("percentage", text="割合")
            
            self.analysis_tree.column("value", width=200)
            self.analysis_tree.column("frequency", width=100, anchor="center")
            self.analysis_tree.column("percentage", width=100, anchor="center")
            
            # 総行数を取得
            self.cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE {column_name} IS NOT NULL")
            total_count = self.cursor.fetchone()[0]
            
            # データを挿入
            for row in results:
                value, frequency = row
                percentage = (frequency / total_count) * 100 if total_count > 0 else 0
                
                # NULL値を「NULL」として表示
                value_str = str(value) if value is not None else "NULL"
                
                self.analysis_tree.insert("", "end", values=(value_str, frequency, f"{percentage:.2f}%"))
                
        except Exception as e:
            messagebox.showerror("エラー", f"頻度分布分析中にエラーが発生しました: {str(e)}")
            print(traceback.format_exc())
            
    def analyze_null_values(self, table_name, column_name):
        """NULL値チェックを実行する"""
        try:
            # NULL値の数を取得
            self.cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE {column_name} IS NULL")
            null_count = self.cursor.fetchone()[0]
            
            # 総行数を取得
            self.cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            total_count = self.cursor.fetchone()[0]
            
            # NULL値の割合を計算
            null_percentage = (null_count / total_count) * 100 if total_count > 0 else 0
            
            # 結果を表示
            self.analysis_result_text.delete("1.0", tk.END)
            self.analysis_result_text.insert(tk.END, f"テーブル: {table_name}\n")
            self.analysis_result_text.insert(tk.END, f"カラム: {column_name}\n\n")
            self.analysis_result_text.insert(tk.END, f"総行数: {total_count:,}\n")
            self.analysis_result_text.insert(tk.END, f"NULL値の数: {null_count:,}\n")
            self.analysis_result_text.insert(tk.END, f"NULL値の割合: {null_percentage:.2f}%\n")
            
            # NULL値を含む行のサンプルを取得
            if null_count > 0:
                self.cursor.execute(f"SELECT * FROM {table_name} WHERE {column_name} IS NULL LIMIT 10")
                null_samples = self.cursor.fetchall()
                
                # 列名を取得
                self.cursor.execute(f"PRAGMA table_info({table_name})")
                columns = [col[1] for col in self.cursor.fetchall()]
                
                # ツリービューをクリア
                for item in self.analysis_tree.get_children():
                    self.analysis_tree.delete(item)
                    
                # ツリービューの設定
                self.analysis_tree["columns"] = columns
                self.analysis_tree["show"] = "headings"
                
                for col in columns:
                    self.analysis_tree.heading(col, text=col)
                    self.analysis_tree.column(col, width=100)
                    
                # データを挿入
                for row in null_samples:
                    # NULL値を「NULL」として表示
                    formatted_row = [str(val) if val is not None else "NULL" for val in row]
                    self.analysis_tree.insert("", "end", values=formatted_row)
                    
                self.analysis_result_text.insert(tk.END, "\nNULL値を含む行のサンプル（最大10件）:\n")
            else:
                # ツリービューをクリア
                for item in self.analysis_tree.get_children():
                    self.analysis_tree.delete(item)
                    
        except Exception as e:
            messagebox.showerror("エラー", f"NULL値チェック中にエラーが発生しました: {str(e)}")
            print(traceback.format_exc())
            
    def analyze_duplicate_values(self, table_name, column_name):
        """重複値チェックを実行する"""
        try:
            # 重複値の分布を取得
            query = f"""
            SELECT 
                {column_name},
                COUNT(*) as frequency
            FROM {table_name}
            WHERE {column_name} IS NOT NULL
            GROUP BY {column_name}
            HAVING COUNT(*) > 1
            ORDER BY frequency DESC
            LIMIT 100
            """
            
            # クエリ実行
            self.cursor.execute(query)
            results = self.cursor.fetchall()
            
            # 重複値の総数を計算
            duplicate_count = sum(row[1] - 1 for row in results)
            
            # 総行数を取得
            self.cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE {column_name} IS NOT NULL")
            total_count = self.cursor.fetchone()[0]
            
            # 重複値の割合を計算
            duplicate_percentage = (duplicate_count / total_count) * 100 if total_count > 0 else 0
            
            # 結果を表示
            self.analysis_result_text.delete("1.0", tk.END)
            self.analysis_result_text.insert(tk.END, f"テーブル: {table_name}\n")
            self.analysis_result_text.insert(tk.END, f"カラム: {column_name}\n\n")
            self.analysis_result_text.insert(tk.END, f"総行数: {total_count:,}\n")
            self.analysis_result_text.insert(tk.END, f"重複値の数: {duplicate_count:,}\n")
            self.analysis_result_text.insert(tk.END, f"重複値の割合: {duplicate_percentage:.2f}%\n")
            self.analysis_result_text.insert(tk.END, f"ユニーク値の数（重複あり）: {len(results):,}\n")
            
            # ツリービューをクリア
            for item in self.analysis_tree.get_children():
                self.analysis_tree.delete(item)
                
            if results:
                # ツリービューの設定
                self.analysis_tree["columns"] = ("value", "frequency")
                self.analysis_tree["show"] = "headings"
                
                self.analysis_tree.heading("value", text="値")
                self.analysis_tree.heading("frequency", text="出現回数")
                
                self.analysis_tree.column("value", width=200)
                self.analysis_tree.column("frequency", width=100, anchor="center")
                
                # データを挿入
                for row in results:
                    value, frequency = row
                    
                    # NULL値を「NULL」として表示
                    value_str = str(value) if value is not None else "NULL"
                    
                    self.analysis_tree.insert("", "end", values=(value_str, frequency))
                    
                self.analysis_result_text.insert(tk.END, "\n重複値の分布（上位100件）:\n")
                
        except Exception as e:
            messagebox.showerror("エラー", f"重複値チェック中にエラーが発生しました: {str(e)}")
            print(traceback.format_exc())