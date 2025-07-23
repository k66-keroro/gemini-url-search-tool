"""
データインポートタブ
CSV、TXT、Excelファイルをデータベースにインポートする
"""

import tkinter as tk
from tkinter import ttk
import os
from pathlib import Path
from typing import Optional, List, Dict, Any

from .base_tab import BaseTab
from ..components.file_dialog import FileDialog
from ..components.message_box import MessageBox
from ..components.data_table import DataTable
from ...core.db_connection import DatabaseConnection
from ...core.sqlite_manager import SQLiteManager
from ...utils.error_handler import ErrorHandler
from ...utils.logger import Logger
from ...utils.string_utils import StringUtils


class ImportTab(BaseTab):
    """データインポートタブ"""
    
    def __init__(self, parent, db_connection: DatabaseConnection):
        super().__init__(parent, "インポート")
        self.db_connection = db_connection
        self.sqlite_manager = SQLiteManager()
        self.logger = Logger.get_logger(__name__)
        self.error_handler = ErrorHandler()
        
        # インポート設定
        self.import_settings = {
            'encoding': 'auto',
            'separator': 'auto',
            'header_row': 0,
            'table_name': '',
            'if_exists': 'replace'
        }
        
        self._create_widgets()
        
    def _create_widgets(self):
        """ウィジェットの作成"""
        # メインフレーム
        main_frame = ttk.Frame(self.frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 上部: ファイル選択とオプション
        top_frame = ttk.LabelFrame(main_frame, text="インポート設定", padding=5)
        top_frame.pack(fill=tk.X, pady=(0, 5))
        
        # ファイル選択
        file_frame = ttk.Frame(top_frame)
        file_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(file_frame, text="ファイル:").pack(side=tk.LEFT)
        
        self.file_var = tk.StringVar()
        self.file_entry = ttk.Entry(file_frame, textvariable=self.file_var, state='readonly')
        self.file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 5))
        
        self.browse_btn = ttk.Button(
            file_frame,
            text="参照",
            command=self._browse_file
        )
        self.browse_btn.pack(side=tk.RIGHT)
        
        # オプション設定
        options_frame = ttk.Frame(top_frame)
        options_frame.pack(fill=tk.X, pady=(5, 0))
        
        # 左側のオプション
        left_options = ttk.Frame(options_frame)
        left_options.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # エンコーディング
        encoding_frame = ttk.Frame(left_options)
        encoding_frame.pack(fill=tk.X, pady=(0, 2))
        
        ttk.Label(encoding_frame, text="エンコーディング:", width=15).pack(side=tk.LEFT)
        self.encoding_var = tk.StringVar(value="auto")
        encoding_combo = ttk.Combobox(
            encoding_frame,
            textvariable=self.encoding_var,
            values=["auto", "utf-8", "cp932", "shift_jis", "euc-jp"],
            state="readonly",
            width=15
        )
        encoding_combo.pack(side=tk.LEFT, padx=(5, 0))
        
        # 区切り文字
        separator_frame = ttk.Frame(left_options)
        separator_frame.pack(fill=tk.X, pady=(2, 2))
        
        ttk.Label(separator_frame, text="区切り文字:", width=15).pack(side=tk.LEFT)
        self.separator_var = tk.StringVar(value="auto")
        separator_combo = ttk.Combobox(
            separator_frame,
            textvariable=self.separator_var,
            values=["auto", ",", "\t", "|", ";"],
            width=15
        )
        separator_combo.pack(side=tk.LEFT, padx=(5, 0))
        
        # ヘッダー行
        header_frame = ttk.Frame(left_options)
        header_frame.pack(fill=tk.X, pady=(2, 0))
        
        ttk.Label(header_frame, text="ヘッダー行:", width=15).pack(side=tk.LEFT)
        self.header_var = tk.StringVar(value="0")
        header_entry = ttk.Entry(header_frame, textvariable=self.header_var, width=15)
        header_entry.pack(side=tk.LEFT, padx=(5, 0))
        
        # 右側のオプション
        right_options = ttk.Frame(options_frame)
        right_options.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(10, 0))
        
        # テーブル名
        table_frame = ttk.Frame(right_options)
        table_frame.pack(fill=tk.X, pady=(0, 2))
        
        ttk.Label(table_frame, text="テーブル名:", width=15).pack(side=tk.LEFT)
        self.table_name_var = tk.StringVar()
        table_entry = ttk.Entry(table_frame, textvariable=self.table_name_var, width=20)
        table_entry.pack(side=tk.LEFT, padx=(5, 0))
        
        # 既存テーブルの処理
        exists_frame = ttk.Frame(right_options)
        exists_frame.pack(fill=tk.X, pady=(2, 2))
        
        ttk.Label(exists_frame, text="既存テーブル:", width=15).pack(side=tk.LEFT)
        self.if_exists_var = tk.StringVar(value="replace")
        exists_combo = ttk.Combobox(
            exists_frame,
            textvariable=self.if_exists_var,
            values=["replace", "append", "fail"],
            state="readonly",
            width=15
        )
        exists_combo.pack(side=tk.LEFT, padx=(5, 0))
        
        # ボタンフレーム
        button_frame = ttk.Frame(right_options)
        button_frame.pack(fill=tk.X, pady=(2, 0))
        
        self.preview_btn = ttk.Button(
            button_frame,
            text="プレビュー",
            command=self._preview_data,
            state='disabled'
        )
        self.preview_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.import_btn = ttk.Button(
            button_frame,
            text="インポート",
            command=self._import_data,
            state='disabled'
        )
        self.import_btn.pack(side=tk.LEFT)
        
        # 中央: プレビューエリア
        preview_frame = ttk.LabelFrame(main_frame, text="データプレビュー", padding=5)
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        self.preview_table = DataTable(preview_frame)
        self.preview_table.pack(fill=tk.BOTH, expand=True)
        
        # 下部: ログエリア
        log_frame = ttk.LabelFrame(main_frame, text="インポートログ", padding=5)
        log_frame.pack(fill=tk.X)
        log_frame.config(height=100)
        
        self.log_text = tk.Text(log_frame, height=6, wrap=tk.WORD)
        log_scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.config(yscrollcommand=log_scrollbar.set)
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # ファイル選択時のイベント
        self.file_var.trace('w', self._on_file_selected)
        
    def _browse_file(self):
        """ファイル選択ダイアログを表示"""
        file_path = FileDialog.open_file(
            title="インポートファイルを選択",
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
            
    def _on_file_selected(self, *args):
        """ファイル選択時の処理"""
        file_path = self.file_var.get()
        if not file_path or not os.path.exists(file_path):
            self.preview_btn.config(state='disabled')
            self.import_btn.config(state='disabled')
            return
            
        # ファイル名からテーブル名を自動生成
        if not self.table_name_var.get():
            file_name = Path(file_path).stem
            table_name = StringUtils.sanitize_table_name(file_name)
            self.table_name_var.set(table_name)
            
        self.preview_btn.config(state='normal')
        self.import_btn.config(state='normal')
        
        # ログをクリア
        self.log_text.delete(1.0, tk.END)
        
    def _preview_data(self):
        """データのプレビューを表示"""
        try:
            file_path = self.file_var.get()
            if not file_path:
                MessageBox.show_warning("ファイルが選択されていません。")
                return
                
            self._log("データプレビューを開始...")
            
            # 設定を更新
            self._update_settings()
            
            # データを読み込み（最初の100行のみ）
            df = self.sqlite_manager._read_file(
                Path(file_path),
                encoding=self.import_settings['encoding'],
                separator=self.import_settings['separator'],
                header=self.import_settings['header_row'],
                nrows=100  # プレビューは100行まで
            )
            
            if df is None or df.empty:
                MessageBox.show_warning("データを読み込めませんでした。")
                return
                
            # プレビューテーブルに表示
            data = df.values.tolist()
            columns = df.columns.tolist()
            
            self.preview_table.load_data(data, columns)
            
            self._log(f"プレビュー完了: {len(df)}行 x {len(df.columns)}列")
            
        except Exception as e:
            self.error_handler.handle_error(e, "データプレビューエラー")
            self._log(f"エラー: {str(e)}")
            MessageBox.show_error(f"プレビューに失敗しました: {str(e)}")
            
    def _import_data(self):
        """データをインポート"""
        try:
            file_path = self.file_var.get()
            table_name = self.table_name_var.get().strip()
            
            if not file_path:
                MessageBox.show_warning("ファイルが選択されていません。")
                return
                
            if not table_name:
                MessageBox.show_warning("テーブル名が入力されていません。")
                return
                
            # 確認ダイアログ
            if not MessageBox.show_question(
                f"ファイル '{Path(file_path).name}' を\n"
                f"テーブル '{table_name}' にインポートしますか？"
            ):
                return
                
            self._log("データインポートを開始...")
            
            # 設定を更新
            self._update_settings()
            self.import_settings['table_name'] = table_name
            
            # インポート実行
            success = self.sqlite_manager.process_file(
                Path(file_path),
                self.db_connection.db_path,
                **self.import_settings
            )
            
            if success:
                self._log("インポート完了")
                MessageBox.show_info("データのインポートが完了しました。")
                
                # プレビューを更新
                self._preview_imported_data(table_name)
                
            else:
                self._log("インポートに失敗しました")
                MessageBox.show_error("データのインポートに失敗しました。")
                
        except Exception as e:
            self.error_handler.handle_error(e, "データインポートエラー")
            self._log(f"エラー: {str(e)}")
            MessageBox.show_error(f"インポートに失敗しました: {str(e)}")
            
    def _preview_imported_data(self, table_name: str):
        """インポートされたデータのプレビューを表示"""
        try:
            conn = self.db_connection.get_connection()
            cursor = conn.cursor()
            
            # 最初の100行を取得
            cursor.execute(f"SELECT * FROM `{table_name}` LIMIT 100")
            data = cursor.fetchall()
            
            # カラム名を取得
            columns = [desc[0] for desc in cursor.description]
            
            # プレビューテーブルに表示
            self.preview_table.load_data(data, columns)
            
            # 総行数を取得
            cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
            total_rows = cursor.fetchone()[0]
            
            self._log(f"インポート結果: {total_rows}行")
            
        except Exception as e:
            self.logger.error(f"インポートデータプレビューエラー: {e}")
            
    def _update_settings(self):
        """設定を更新"""
        self.import_settings.update({
            'encoding': self.encoding_var.get(),
            'separator': self.separator_var.get(),
            'header_row': int(self.header_var.get()) if self.header_var.get().isdigit() else 0,
            'if_exists': self.if_exists_var.get()
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
        # プレビューをクリア
        self.preview_table.clear()
        
        # ログをクリア
        self.log_text.delete(1.0, tk.END)