"""
データエクスポートタブ
データベースのテーブルをCSV、Excel形式でエクスポートする
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


class ExportTab(BaseTab):
    """データエクスポートタブ"""
    
    def __init__(self, parent, db_connection: DatabaseConnection):
        super().__init__(parent, "エクスポート")
        self.db_connection = db_connection
        self.table_utils = TableUtils(db_connection)
        self.logger = Logger.get_logger(__name__)
        self.error_handler = ErrorHandler()
        
        # エクスポート設定
        self.export_settings = {
            'format': 'csv',
            'encoding': 'utf-8',
            'include_header': True,
            'limit_rows': 0,
            'where_clause': ''
        }
        
        self._create_widgets()
        self._load_tables()
        
    def _create_widgets(self):
        """ウィジェットの作成"""
        # メインフレーム
        main_frame = ttk.Frame(self.frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 上部: エクスポート設定
        top_frame = ttk.LabelFrame(main_frame, text="エクスポート設定", padding=5)
        top_frame.pack(fill=tk.X, pady=(0, 5))
        
        # テーブル選択
        table_frame = ttk.Frame(top_frame)
        table_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(table_frame, text="テーブル:", width=12).pack(side=tk.LEFT)
        
        self.table_var = tk.StringVar()
        self.table_combo = ttk.Combobox(
            table_frame,
            textvariable=self.table_var,
            state="readonly",
            width=30
        )
        self.table_combo.pack(side=tk.LEFT, padx=(5, 10))
        self.table_combo.bind('<<ComboboxSelected>>', self._on_table_selected)
        
        # プレビューボタン
        self.preview_btn = ttk.Button(
            table_frame,
            text="プレビュー",
            command=self._preview_data,
            state='disabled'
        )
        self.preview_btn.pack(side=tk.LEFT, padx=(5, 0))
        
        # オプション設定
        options_frame = ttk.Frame(top_frame)
        options_frame.pack(fill=tk.X, pady=(5, 0))
        
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
            values=["csv", "excel", "json"],
            state="readonly",
            width=15
        )
        format_combo.pack(side=tk.LEFT, padx=(5, 0))
        
        # エンコーディング
        encoding_frame = ttk.Frame(left_options)
        encoding_frame.pack(fill=tk.X, pady=(2, 2))
        
        ttk.Label(encoding_frame, text="エンコーディング:", width=12).pack(side=tk.LEFT)
        self.encoding_var = tk.StringVar(value="utf-8")
        encoding_combo = ttk.Combobox(
            encoding_frame,
            textvariable=self.encoding_var,
            values=["utf-8", "cp932", "shift_jis"],
            state="readonly",
            width=15
        )
        encoding_combo.pack(side=tk.LEFT, padx=(5, 0))
        
        # ヘッダー含む
        header_frame = ttk.Frame(left_options)
        header_frame.pack(fill=tk.X, pady=(2, 0))
        
        self.header_var = tk.BooleanVar(value=True)
        header_check = ttk.Checkbutton(
            header_frame,
            text="ヘッダー行を含む",
            variable=self.header_var
        )
        header_check.pack(side=tk.LEFT)
        
        # 右側のオプション
        right_options = ttk.Frame(options_frame)
        right_options.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(10, 0))
        
        # 行数制限
        limit_frame = ttk.Frame(right_options)
        limit_frame.pack(fill=tk.X, pady=(0, 2))
        
        ttk.Label(limit_frame, text="行数制限:", width=12).pack(side=tk.LEFT)
        self.limit_var = tk.StringVar(value="0")
        limit_entry = ttk.Entry(limit_frame, textvariable=self.limit_var, width=15)
        limit_entry.pack(side=tk.LEFT, padx=(5, 0))
        ttk.Label(limit_frame, text="(0=制限なし)").pack(side=tk.LEFT, padx=(5, 0))
        
        # WHERE句
        where_frame = ttk.Frame(right_options)
        where_frame.pack(fill=tk.X, pady=(2, 2))
        
        ttk.Label(where_frame, text="WHERE句:", width=12).pack(side=tk.LEFT)
        self.where_var = tk.StringVar()
        where_entry = ttk.Entry(where_frame, textvariable=self.where_var, width=25)
        where_entry.pack(side=tk.LEFT, padx=(5, 0))
        
        # エクスポートボタン
        export_frame = ttk.Frame(right_options)
        export_frame.pack(fill=tk.X, pady=(2, 0))
        
        self.export_btn = ttk.Button(
            export_frame,
            text="エクスポート",
            command=self._export_data,
            state='disabled'
        )
        self.export_btn.pack(side=tk.LEFT)
        
        # 中央: プレビューエリア
        preview_frame = ttk.LabelFrame(main_frame, text="データプレビュー", padding=5)
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        self.preview_table = DataTable(preview_frame)
        self.preview_table.pack(fill=tk.BOTH, expand=True)
        
        # 下部: ログエリア
        log_frame = ttk.LabelFrame(main_frame, text="エクスポートログ", padding=5)
        log_frame.pack(fill=tk.X)
        log_frame.config(height=100)
        
        self.log_text = tk.Text(log_frame, height=6, wrap=tk.WORD)
        log_scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.config(yscrollcommand=log_scrollbar.set)
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
    def _load_tables(self):
        """テーブル一覧を読み込み"""
        try:
            if not self.db_connection.is_connected():
                return
                
            tables = self.table_utils.get_table_list()
            self.table_combo['values'] = tables
            
            if tables:
                self.table_combo.current(0)
                self._on_table_selected()
                
        except Exception as e:
            self.error_handler.handle_error(e, "テーブル一覧の読み込みエラー")
            self._log(f"エラー: {str(e)}")
            
    def _on_table_selected(self, event=None):
        """テーブル選択時の処理"""
        table_name = self.table_var.get()
        if table_name:
            self.preview_btn.config(state='normal')
            self.export_btn.config(state='normal')
        else:
            self.preview_btn.config(state='disabled')
            self.export_btn.config(state='disabled')
            
    def _preview_data(self):
        """データのプレビューを表示"""
        try:
            table_name = self.table_var.get()
            if not table_name:
                MessageBox.show_warning("テーブルが選択されていません。")
                return
                
            self._log("データプレビューを開始...")
            
            # クエリを構築
            query = f"SELECT * FROM `{table_name}`"
            
            # WHERE句があれば追加
            where_clause = self.where_var.get().strip()
            if where_clause:
                query += f" WHERE {where_clause}"
                
            # プレビューは100行まで
            query += " LIMIT 100"
            
            # データを取得
            conn = self.db_connection.get_connection()
            cursor = conn.cursor()
            cursor.execute(query)
            
            data = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            
            # プレビューテーブルに表示
            self.preview_table.load_data(data, columns)
            
            # 総行数を取得
            count_query = f"SELECT COUNT(*) FROM `{table_name}`"
            if where_clause:
                count_query += f" WHERE {where_clause}"
                
            cursor.execute(count_query)
            total_rows = cursor.fetchone()[0]
            
            self._log(f"プレビュー完了: {len(data)}行表示 (総行数: {total_rows}行)")
            
        except sqlite3.Error as e:
            self.error_handler.handle_error(e, "データプレビューエラー")
            self._log(f"SQLエラー: {str(e)}")
            MessageBox.show_error(f"プレビューに失敗しました: {str(e)}")
            
        except Exception as e:
            self.error_handler.handle_error(e, "データプレビューエラー")
            self._log(f"エラー: {str(e)}")
            MessageBox.show_error(f"プレビューに失敗しました: {str(e)}")
            
    def _export_data(self):
        """データをエクスポート"""
        try:
            table_name = self.table_var.get()
            if not table_name:
                MessageBox.show_warning("テーブルが選択されていません。")
                return
                
            # 設定を更新
            self._update_settings()
            
            # 保存先を選択
            file_path = self._get_save_path(table_name)
            if not file_path:
                return
                
            # 確認ダイアログ
            if not MessageBox.show_question(
                f"テーブル '{table_name}' を\n"
                f"ファイル '{Path(file_path).name}' にエクスポートしますか？"
            ):
                return
                
            self._log("データエクスポートを開始...")
            
            # クエリを構築
            query = f"SELECT * FROM `{table_name}`"
            
            # WHERE句があれば追加
            if self.export_settings['where_clause']:
                query += f" WHERE {self.export_settings['where_clause']}"
                
            # 行数制限があれば追加
            if self.export_settings['limit_rows'] > 0:
                query += f" LIMIT {self.export_settings['limit_rows']}"
                
            # データを取得
            conn = self.db_connection.get_connection()
            df = pd.read_sql_query(query, conn)
            
            # エクスポート実行
            self._export_to_file(df, file_path)
            
            self._log(f"エクスポート完了: {len(df)}行")
            MessageBox.show_info(f"データのエクスポートが完了しました。\n保存先: {file_path}")
            
        except Exception as e:
            self.error_handler.handle_error(e, "データエクスポートエラー")
            self._log(f"エラー: {str(e)}")
            MessageBox.show_error(f"エクスポートに失敗しました: {str(e)}")
            
    def _get_save_path(self, table_name: str) -> Optional[str]:
        """保存先パスを取得"""
        format_type = self.export_settings['format']
        
        if format_type == 'csv':
            return FileDialog.save_file(
                title="CSVファイルとして保存",
                defaultextension=".csv",
                filetypes=[("CSVファイル", "*.csv"), ("すべてのファイル", "*.*")],
                initialname=f"{table_name}.csv"
            )
        elif format_type == 'excel':
            return FileDialog.save_file(
                title="Excelファイルとして保存",
                defaultextension=".xlsx",
                filetypes=[("Excelファイル", "*.xlsx"), ("すべてのファイル", "*.*")],
                initialname=f"{table_name}.xlsx"
            )
        elif format_type == 'json':
            return FileDialog.save_file(
                title="JSONファイルとして保存",
                defaultextension=".json",
                filetypes=[("JSONファイル", "*.json"), ("すべてのファイル", "*.*")],
                initialname=f"{table_name}.json"
            )
        else:
            return None
            
    def _export_to_file(self, df: pd.DataFrame, file_path: str):
        """ファイルにエクスポート"""
        format_type = self.export_settings['format']
        encoding = self.export_settings['encoding']
        include_header = self.export_settings['include_header']
        
        if format_type == 'csv':
            df.to_csv(
                file_path,
                index=False,
                encoding=encoding,
                header=include_header
            )
        elif format_type == 'excel':
            df.to_excel(
                file_path,
                index=False,
                header=include_header,
                engine='openpyxl'
            )
        elif format_type == 'json':
            df.to_json(
                file_path,
                orient='records',
                force_ascii=False,
                indent=2
            )
        else:
            raise ValueError(f"サポートされていない形式: {format_type}")
            
    def _update_settings(self):
        """設定を更新"""
        limit_str = self.limit_var.get().strip()
        limit_rows = int(limit_str) if limit_str.isdigit() else 0
        
        self.export_settings.update({
            'format': self.format_var.get(),
            'encoding': self.encoding_var.get(),
            'include_header': self.header_var.get(),
            'limit_rows': limit_rows,
            'where_clause': self.where_var.get().strip()
        })
        
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
        self.preview_table.clear()
        
        # ログをクリア
        self.log_text.delete(1.0, tk.END)