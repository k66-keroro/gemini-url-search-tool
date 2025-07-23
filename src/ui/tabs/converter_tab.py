"""
データ変換タブ
データ形式の変換やデータクレンジング機能を提供する
"""

import tkinter as tk
from tkinter import ttk
import sqlite3
import pandas as pd
from pathlib import Path
from typing import Optional, List, Dict, Any

from .base_tab import BaseTab
from ..components.file_dialog import FileDialog
from ..components.message_box import MessageBox
from ..components.data_table import DataTable
from ...core.db_connection import DatabaseConnection
from ...core.table_utils import TableUtils
from ...utils.error_handler import ErrorHandler
from ...utils.logger import Logger
from ...utils.string_utils import StringUtils


class ConverterTab(BaseTab):
    """データ変換タブ"""
    
    def __init__(self, parent, db_connection: DatabaseConnection):
        super().__init__(parent, "変換")
        self.db_connection = db_connection
        self.table_utils = TableUtils(db_connection)
        self.logger = Logger.get_logger(__name__)
        self.error_handler = ErrorHandler()
        
        # 変換設定
        self.conversion_settings = {
            'source_type': 'table',
            'target_format': 'csv',
            'clean_data': True,
            'normalize_text': False,
            'remove_duplicates': False,
            'fill_missing': False
        }
        
        self._create_widgets()
        self._load_tables()
        
    def _create_widgets(self):
        """ウィジェットの作成"""
        # メインフレーム
        main_frame = ttk.Frame(self.frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 上部: 変換設定
        top_frame = ttk.LabelFrame(main_frame, text="変換設定", padding=5)
        top_frame.pack(fill=tk.X, pady=(0, 5))
        
        # ソース設定
        source_frame = ttk.LabelFrame(top_frame, text="変換元", padding=5)
        source_frame.pack(fill=tk.X, pady=(0, 5))
        
        # ソースタイプ選択
        source_type_frame = ttk.Frame(source_frame)
        source_type_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.source_type_var = tk.StringVar(value="table")
        
        table_radio = ttk.Radiobutton(
            source_type_frame,
            text="データベーステーブル",
            variable=self.source_type_var,
            value="table",
            command=self._on_source_type_changed
        )
        table_radio.pack(side=tk.LEFT, padx=(0, 10))
        
        file_radio = ttk.Radiobutton(
            source_type_frame,
            text="ファイル",
            variable=self.source_type_var,
            value="file",
            command=self._on_source_type_changed
        )
        file_radio.pack(side=tk.LEFT)
        
        # テーブル選択
        self.table_frame = ttk.Frame(source_frame)
        self.table_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Label(self.table_frame, text="テーブル:", width=10).pack(side=tk.LEFT)
        
        self.table_var = tk.StringVar()
        self.table_combo = ttk.Combobox(
            self.table_frame,
            textvariable=self.table_var,
            state="readonly",
            width=30
        )
        self.table_combo.pack(side=tk.LEFT, padx=(5, 0))
        
        # ファイル選択
        self.file_frame = ttk.Frame(source_frame)
        
        ttk.Label(self.file_frame, text="ファイル:", width=10).pack(side=tk.LEFT)
        
        self.file_var = tk.StringVar()
        self.file_entry = ttk.Entry(self.file_frame, textvariable=self.file_var, state='readonly')
        self.file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 5))
        
        self.browse_btn = ttk.Button(
            self.file_frame,
            text="参照",
            command=self._browse_file
        )
        self.browse_btn.pack(side=tk.RIGHT)
        
        # 変換オプション
        options_frame = ttk.LabelFrame(top_frame, text="変換オプション", padding=5)
        options_frame.pack(fill=tk.X, pady=(5, 5))
        
        # 左側のオプション
        left_options = ttk.Frame(options_frame)
        left_options.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 出力形式
        format_frame = ttk.Frame(left_options)
        format_frame.pack(fill=tk.X, pady=(0, 2))
        
        ttk.Label(format_frame, text="出力形式:", width=12).pack(side=tk.LEFT)
        self.format_var = tk.StringVar(value="csv")
        format_combo = ttk.Combobox(
            format_frame,
            textvariable=self.format_var,
            values=["csv", "excel", "json", "sql"],
            state="readonly",
            width=15
        )
        format_combo.pack(side=tk.LEFT, padx=(5, 0))
        
        # データクレンジング
        self.clean_var = tk.BooleanVar(value=True)
        clean_check = ttk.Checkbutton(
            left_options,
            text="データクレンジング（空白除去、型変換）",
            variable=self.clean_var
        )
        clean_check.pack(fill=tk.X, pady=(2, 0))
        
        # 右側のオプション
        right_options = ttk.Frame(options_frame)
        right_options.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(10, 0))
        
        # テキスト正規化
        self.normalize_var = tk.BooleanVar(value=False)
        normalize_check = ttk.Checkbutton(
            right_options,
            text="テキスト正規化（全角半角統一）",
            variable=self.normalize_var
        )
        normalize_check.pack(fill=tk.X, pady=(0, 2))
        
        # 重複除去
        self.dedup_var = tk.BooleanVar(value=False)
        dedup_check = ttk.Checkbutton(
            right_options,
            text="重複データ除去",
            variable=self.dedup_var
        )
        dedup_check.pack(fill=tk.X, pady=(2, 2))
        
        # 欠損値補完
        self.fill_var = tk.BooleanVar(value=False)
        fill_check = ttk.Checkbutton(
            right_options,
            text="欠損値補完",
            variable=self.fill_var
        )
        fill_check.pack(fill=tk.X, pady=(2, 0))
        
        # 実行ボタン
        button_frame = ttk.Frame(top_frame)
        button_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.preview_btn = ttk.Button(
            button_frame,
            text="プレビュー",
            command=self._preview_conversion,
            state='disabled'
        )
        self.preview_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.convert_btn = ttk.Button(
            button_frame,
            text="変換実行",
            command=self._execute_conversion,
            state='disabled'
        )
        self.convert_btn.pack(side=tk.LEFT)
        
        # 中央: プレビューエリア
        preview_frame = ttk.LabelFrame(main_frame, text="変換プレビュー", padding=5)
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        # Before/After比較
        comparison_frame = ttk.Frame(preview_frame)
        comparison_frame.pack(fill=tk.BOTH, expand=True)
        
        # 変換前
        before_frame = ttk.LabelFrame(comparison_frame, text="変換前", padding=5)
        before_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 2))
        
        self.before_table = DataTable(before_frame)
        self.before_table.pack(fill=tk.BOTH, expand=True)
        
        # 変換後
        after_frame = ttk.LabelFrame(comparison_frame, text="変換後", padding=5)
        after_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(2, 0))
        
        self.after_table = DataTable(after_frame)
        self.after_table.pack(fill=tk.BOTH, expand=True)
        
        # 下部: ログエリア
        log_frame = ttk.LabelFrame(main_frame, text="変換ログ", padding=5)
        log_frame.pack(fill=tk.X)
        log_frame.config(height=100)
        
        self.log_text = tk.Text(log_frame, height=6, wrap=tk.WORD)
        log_scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.config(yscrollcommand=log_scrollbar.set)
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 初期状態設定
        self._on_source_type_changed()
        
    def _load_tables(self):
        """テーブル一覧を読み込み"""
        try:
            if not self.db_connection.is_connected():
                return
                
            tables = self.table_utils.get_table_list()
            self.table_combo['values'] = tables
            
            if tables:
                self.table_combo.current(0)
                self._update_button_state()
                
        except Exception as e:
            self.error_handler.handle_error(e, "テーブル一覧の読み込みエラー")
            self._log(f"エラー: {str(e)}")
            
    def _on_source_type_changed(self):
        """ソースタイプ変更時の処理"""
        source_type = self.source_type_var.get()
        
        if source_type == "table":
            self.table_frame.pack(fill=tk.X, pady=(5, 0))
            self.file_frame.pack_forget()
        else:
            self.file_frame.pack(fill=tk.X, pady=(5, 0))
            self.table_frame.pack_forget()
            
        self._update_button_state()
        
    def _browse_file(self):
        """ファイル選択ダイアログを表示"""
        file_path = FileDialog.open_file(
            title="変換元ファイルを選択",
            filetypes=[
                ("すべて対応ファイル", "*.csv;*.txt;*.xlsx;*.xls"),
                ("CSVファイル", "*.csv"),
                ("テキストファイル", "*.txt"),
                ("Excelファイル", "*.xlsx;*.xls"),
                ("すべてのファイル", "*.*")
            ]
        )
        
        if file_path:
            self.file_var.set(file_path)
            self._update_button_state()
            
    def _update_button_state(self):
        """ボタンの状態を更新"""
        source_type = self.source_type_var.get()
        
        if source_type == "table":
            has_source = bool(self.table_var.get())
        else:
            has_source = bool(self.file_var.get())
            
        state = 'normal' if has_source else 'disabled'
        self.preview_btn.config(state=state)
        self.convert_btn.config(state=state)
        
    def _preview_conversion(self):
        """変換プレビューを表示"""
        try:
            self._log("変換プレビューを開始...")
            
            # 元データを読み込み
            original_df = self._load_source_data(limit=100)
            if original_df is None:
                return
                
            # 変換を実行
            converted_df = self._apply_conversions(original_df.copy())
            
            # Before/Afterを表示
            self._display_comparison(original_df, converted_df)
            
            self._log("プレビュー完了")
            
        except Exception as e:
            self.error_handler.handle_error(e, "変換プレビューエラー")
            self._log(f"エラー: {str(e)}")
            MessageBox.show_error(f"プレビューに失敗しました: {str(e)}")
            
    def _execute_conversion(self):
        """変換を実行"""
        try:
            # 保存先を選択
            output_path = self._get_output_path()
            if not output_path:
                return
                
            # 確認ダイアログ
            if not MessageBox.show_question(
                f"データを変換して\n{Path(output_path).name} に保存しますか？"
            ):
                return
                
            self._log("データ変換を開始...")
            
            # 元データを読み込み
            original_df = self._load_source_data()
            if original_df is None:
                return
                
            # 変換を実行
            converted_df = self._apply_conversions(original_df)
            
            # ファイルに保存
            self._save_converted_data(converted_df, output_path)
            
            self._log(f"変換完了: {len(converted_df)}行を保存")
            MessageBox.show_info(f"データの変換が完了しました。\n保存先: {output_path}")
            
        except Exception as e:
            self.error_handler.handle_error(e, "データ変換エラー")
            self._log(f"エラー: {str(e)}")
            MessageBox.show_error(f"変換に失敗しました: {str(e)}")
            
    def _load_source_data(self, limit: Optional[int] = None) -> Optional[pd.DataFrame]:
        """ソースデータを読み込み"""
        source_type = self.source_type_var.get()
        
        if source_type == "table":
            table_name = self.table_var.get()
            if not table_name:
                MessageBox.show_warning("テーブルが選択されていません。")
                return None
                
            # テーブルからデータを読み込み
            conn = self.db_connection.get_connection()
            query = f"SELECT * FROM `{table_name}`"
            if limit:
                query += f" LIMIT {limit}"
                
            return pd.read_sql_query(query, conn)
            
        else:
            file_path = self.file_var.get()
            if not file_path:
                MessageBox.show_warning("ファイルが選択されていません。")
                return None
                
            # ファイルからデータを読み込み
            path = Path(file_path)
            
            if path.suffix.lower() == '.csv':
                kwargs = {'nrows': limit} if limit else {}
                return pd.read_csv(file_path, **kwargs)
            elif path.suffix.lower() in ['.xlsx', '.xls']:
                kwargs = {'nrows': limit} if limit else {}
                return pd.read_excel(file_path, **kwargs)
            else:
                raise ValueError(f"サポートされていないファイル形式: {path.suffix}")
                
    def _apply_conversions(self, df: pd.DataFrame) -> pd.DataFrame:
        """データ変換を適用"""
        self._log("データ変換を適用中...")
        
        # データクレンジング
        if self.clean_var.get():
            df = self._clean_data(df)
            
        # テキスト正規化
        if self.normalize_var.get():
            df = self._normalize_text(df)
            
        # 重複除去
        if self.dedup_var.get():
            original_count = len(df)
            df = df.drop_duplicates()
            removed_count = original_count - len(df)
            if removed_count > 0:
                self._log(f"重複データを {removed_count} 行除去")
                
        # 欠損値補完
        if self.fill_var.get():
            df = self._fill_missing_values(df)
            
        return df
        
    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """データクレンジング"""
        self._log("データクレンジングを実行...")
        
        for col in df.columns:
            if df[col].dtype == 'object':
                # 文字列の前後空白を除去
                df[col] = df[col].astype(str).str.strip()
                
                # 空文字をNaNに変換
                df[col] = df[col].replace('', pd.NA)
                
        return df
        
    def _normalize_text(self, df: pd.DataFrame) -> pd.DataFrame:
        """テキスト正規化"""
        self._log("テキスト正規化を実行...")
        
        import unicodedata
        
        for col in df.columns:
            if df[col].dtype == 'object':
                # 全角半角統一（NFKC正規化）
                df[col] = df[col].astype(str).apply(
                    lambda x: unicodedata.normalize('NFKC', x) if pd.notna(x) else x
                )
                
        return df
        
    def _fill_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """欠損値補完"""
        self._log("欠損値補完を実行...")
        
        for col in df.columns:
            if df[col].dtype in ['int64', 'float64']:
                # 数値型は平均値で補完
                df[col] = df[col].fillna(df[col].mean())
            else:
                # 文字列型は最頻値で補完
                mode_value = df[col].mode()
                if not mode_value.empty:
                    df[col] = df[col].fillna(mode_value[0])
                    
        return df
        
    def _display_comparison(self, before_df: pd.DataFrame, after_df: pd.DataFrame):
        """Before/After比較を表示"""
        # 変換前データを表示
        before_data = before_df.head(50).values.tolist()
        before_columns = before_df.columns.tolist()
        self.before_table.load_data(before_data, before_columns)
        
        # 変換後データを表示
        after_data = after_df.head(50).values.tolist()
        after_columns = after_df.columns.tolist()
        self.after_table.load_data(after_data, after_columns)
        
    def _get_output_path(self) -> Optional[str]:
        """出力パスを取得"""
        format_type = self.format_var.get()
        
        if format_type == 'csv':
            return FileDialog.save_file(
                title="CSVファイルとして保存",
                defaultextension=".csv",
                filetypes=[("CSVファイル", "*.csv"), ("すべてのファイル", "*.*")]
            )
        elif format_type == 'excel':
            return FileDialog.save_file(
                title="Excelファイルとして保存",
                defaultextension=".xlsx",
                filetypes=[("Excelファイル", "*.xlsx"), ("すべてのファイル", "*.*")]
            )
        elif format_type == 'json':
            return FileDialog.save_file(
                title="JSONファイルとして保存",
                defaultextension=".json",
                filetypes=[("JSONファイル", "*.json"), ("すべてのファイル", "*.*")]
            )
        elif format_type == 'sql':
            return FileDialog.save_file(
                title="SQLファイルとして保存",
                defaultextension=".sql",
                filetypes=[("SQLファイル", "*.sql"), ("すべてのファイル", "*.*")]
            )
        else:
            return None
            
    def _save_converted_data(self, df: pd.DataFrame, output_path: str):
        """変換データを保存"""
        format_type = self.format_var.get()
        
        if format_type == 'csv':
            df.to_csv(output_path, index=False, encoding='utf-8')
        elif format_type == 'excel':
            df.to_excel(output_path, index=False, engine='openpyxl')
        elif format_type == 'json':
            df.to_json(output_path, orient='records', force_ascii=False, indent=2)
        elif format_type == 'sql':
            # SQLのINSERT文として保存
            table_name = "converted_data"
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(f"-- 変換データ\n")
                f.write(f"CREATE TABLE {table_name} (\n")
                
                # カラム定義
                col_defs = []
                for col in df.columns:
                    col_defs.append(f"    `{col}` TEXT")
                f.write(",\n".join(col_defs))
                f.write("\n);\n\n")
                
                # データ挿入
                for _, row in df.iterrows():
                    values = []
                    for val in row:
                        if pd.isna(val):
                            values.append("NULL")
                        else:
                            values.append(f"'{str(val).replace(\"'\", \"''\")}'")
                    f.write(f"INSERT INTO {table_name} VALUES ({', '.join(values)});\n")
        else:
            raise ValueError(f"サポートされていない形式: {format_type}")
            
    def _log(self, message: str):
        """ログメッセージを追加"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        
        self.log_text.insert(tk.END, log_message)
        self.log_text.see(tk.END)
        self.log_text.update()
        
    def refresh(self):
        """タブの更新"""
        # テーブル一覧を再読み込み
        self._load_tables()
        
        # プレビューをクリア
        self.before_table.clear()
        self.after_table.clear()
        
        # ログをクリア
        self.log_text.delete(1.0, tk.END)