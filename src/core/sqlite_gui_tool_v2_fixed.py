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

    return sanitizedc
lass SQLiteGUITool:
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
        self.status_bar = ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # データベース接続ボタン
        self.connect_button = ttk.Button(self.main_frame, text="データベース接続", command=self.connect_database)
        self.connect_button.pack(side=tk.TOP, pady=5)
        
        # デフォルトのデータベースパスを設定
        self.default_db_path = Paths().SQLITE_DB 
   def init_query_tab(self):
        """クエリ実行タブの初期化"""
        # 実装は省略
        pass
        
    def init_schema_tab(self):
        """スキーマタブの初期化"""
        # 実装は省略
        pass
        
    def init_import_tab(self):
        """インポートタブの初期化"""
        # 実装は省略
        pass
        
    def init_export_tab(self):
        """エクスポートタブの初期化"""
        # 実装は省略
        pass
        
    def init_analyze_tab(self):
        """データ分析タブの初期化"""
        # 実装は省略
        pass
        
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
        desc_label = ttk.Label(converter_frame, text=description, wraplength=800, justify="left")
        desc_label.pack(fill=tk.X, pady=10)
        
        # 操作ボタンフレーム
        button_frame = ttk.Frame(converter_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        # 分析ボタン
        analyze_button = ttk.Button(button_frame, text="変換対象フィールドを分析", command=self.analyze_code_fields)
        analyze_button.pack(side=tk.LEFT, padx=5)
        
        # 変換ボタン
        self.convert_button = ttk.Button(button_frame, text="選択したフィールドを変換", command=self.convert_selected_fields, state="disabled")
        self.convert_button.pack(side=tk.LEFT, padx=5)
        
        # 全て選択/解除ボタン
        self.select_all_button = ttk.Button(button_frame, text="全て選択", command=self.select_all_fields, state="disabled")
        self.select_all_button.pack(side=tk.LEFT, padx=5)
        
        self.deselect_all_button = ttk.Button(button_frame, text="全て解除", command=self.deselect_all_fields, state="disabled")
        self.deselect_all_button.pack(side=tk.LEFT, padx=5)
        
        # 変換対象フィールド表示エリア
        fields_frame = ttk.LabelFrame(converter_frame, text="変換対象フィールド")
        fields_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # ツリービュー（表形式）でフィールドを表示
        columns = ("select", "table", "column", "current_type", "reason", "sample")
        self.fields_tree = ttk.Treeview(fields_frame, columns=columns, show="headings")
        
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
        tree_scrollbar = ttk.Scrollbar(fields_frame, orient="vertical", command=self.fields_tree.yview)
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
        result_label = ttk.Label(result_frame, textvariable=self.conversion_result_var, wraplength=800)
        result_label.pack(fill=tk.X, padx=5, pady=5)
        
        # フィールドデータを保存する変数
        self.code_fields_data = []   
 def connect_database(self):
        """データベースに接続"""
        # 実装は省略
        pass
        
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
                sample_values = ", ".join([str(val) for val in field['sample_values'][:3]])
                
                # 選択状態を「✓」で表示
                self.fields_tree.insert("", "end", values=("☐", table, column, current_type, reason, sample_values), tags=(str(i),))
            
            # ボタンを有効化
            self.select_all_button.config(state="normal")
            self.deselect_all_button.config(state="normal")
            self.convert_button.config(state="normal")
            
            # 結果表示
            self.conversion_result_var.set(f"{len(fields_to_convert)}個のコードフィールドが変換対象として見つかりました。変換するフィールドを選択してください。")
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
                error_msg = "\n".join([f"{field['table']}.{field['column']}: {field['error']}" for field in failed_fields])
                messagebox.showwarning(
                    "警告", 
                    f"{success_count}/{len(selected_fields)} 個のフィールドの変換が完了しました。\n\n" +
                    f"{len(failed_fields)} 個のフィールドの変換に失敗しました:\n{error_msg}"
                )
            else:
                messagebox.showinfo("成功", f"{success_count}/{len(selected_fields)} 個のフィールドの変換が完了しました。")
            
            # 分析を再実行して表示を更新
            self.analyze_code_fields()
            
        except Exception as e:
            messagebox.showerror("エラー", f"フィールドの変換中にエラーが発生しました: {str(e)}")
            self.status_var.set("フィールドの変換中にエラーが発生しました。")
            print(traceback.format_exc())def 
main():
    root = tk.Tk()
    app = SQLiteGUITool(root)
    root.mainloop()

if __name__ == "__main__":
    main()