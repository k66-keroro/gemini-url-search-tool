"""
スキーマ表示タブ
データベースのテーブル構造とスキーマ情報を表示する
"""

import tkinter as tk
from tkinter import ttk
import sqlite3
from typing import Optional, List, Dict, Any, Tuple

from .base_tab import BaseTab
from ..components.data_table import DataTable
from ..components.message_box import MessageBox
from ...core.db_connection import DatabaseConnection
from ...core.table_utils import TableUtils
from ...utils.error_handler import ErrorHandler
from ...utils.logger import Logger


class SchemaTab(BaseTab):
    """スキーマ表示タブ"""
    
    def __init__(self, parent, db_connection: DatabaseConnection):
        super().__init__(parent, "スキーマ")
        self.db_connection = db_connection
        self.table_utils = TableUtils(db_connection)
        self.logger = Logger.get_logger(__name__)
        self.error_handler = ErrorHandler()
        
        self._create_widgets()
        self._load_schema_info()
        
    def _create_widgets(self):
        """ウィジェットの作成"""
        # メインフレーム
        main_frame = ttk.Frame(self.frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 左側: テーブル一覧
        left_frame = ttk.LabelFrame(main_frame, text="テーブル一覧", padding=5)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 5))
        left_frame.config(width=250)
        
        # テーブルリスト
        self.table_listbox = tk.Listbox(left_frame, width=30)
        table_scrollbar = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.table_listbox.yview)
        self.table_listbox.config(yscrollcommand=table_scrollbar.set)
        
        self.table_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        table_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # テーブル選択イベント
        self.table_listbox.bind('<<ListboxSelect>>', self._on_table_select)
        
        # 右側: 詳細情報
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # タブ形式で詳細情報を表示
        self.detail_notebook = ttk.Notebook(right_frame)
        self.detail_notebook.pack(fill=tk.BOTH, expand=True)
        
        # カラム情報タブ
        self.columns_frame = ttk.Frame(self.detail_notebook)
        self.detail_notebook.add(self.columns_frame, text="カラム情報")
        
        self.columns_table = DataTable(self.columns_frame)
        self.columns_table.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # インデックス情報タブ
        self.indexes_frame = ttk.Frame(self.detail_notebook)
        self.detail_notebook.add(self.indexes_frame, text="インデックス")
        
        self.indexes_table = DataTable(self.indexes_frame)
        self.indexes_table.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 統計情報タブ
        self.stats_frame = ttk.Frame(self.detail_notebook)
        self.detail_notebook.add(self.stats_frame, text="統計情報")
        
        self.stats_table = DataTable(self.stats_frame)
        self.stats_table.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # DDL情報タブ
        self.ddl_frame = ttk.Frame(self.detail_notebook)
        self.detail_notebook.add(self.ddl_frame, text="DDL")
        
        self.ddl_text = tk.Text(self.ddl_frame, wrap=tk.WORD, font=('Consolas', 10))
        ddl_scrollbar = ttk.Scrollbar(self.ddl_frame, orient=tk.VERTICAL, command=self.ddl_text.yview)
        self.ddl_text.config(yscrollcommand=ddl_scrollbar.set)
        
        self.ddl_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        ddl_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)
        
        # ボタンフレーム
        button_frame = ttk.Frame(right_frame)
        button_frame.pack(fill=tk.X, pady=(5, 0))
        
        # 更新ボタン
        self.refresh_btn = ttk.Button(
            button_frame,
            text="更新",
            command=self.refresh
        )
        self.refresh_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # エクスポートボタン
        self.export_btn = ttk.Button(
            button_frame,
            text="スキーマエクスポート",
            command=self._export_schema
        )
        self.export_btn.pack(side=tk.LEFT)
        
    def _load_schema_info(self):
        """スキーマ情報を読み込み"""
        try:
            if not self.db_connection.is_connected():
                return
                
            # テーブル一覧を取得
            tables = self.table_utils.get_table_list()
            
            # リストボックスをクリア
            self.table_listbox.delete(0, tk.END)
            
            # テーブルを追加
            for table in tables:
                self.table_listbox.insert(tk.END, table)
                
        except Exception as e:
            self.error_handler.handle_error(e, "スキーマ情報の読み込みエラー")
            MessageBox.show_error(f"スキーマ情報の読み込みに失敗しました: {str(e)}")
            
    def _on_table_select(self, event):
        """テーブル選択時の処理"""
        selection = self.table_listbox.curselection()
        if not selection:
            return
            
        table_name = self.table_listbox.get(selection[0])
        self._load_table_details(table_name)
        
    def _load_table_details(self, table_name: str):
        """テーブルの詳細情報を読み込み"""
        try:
            # カラム情報を読み込み
            self._load_column_info(table_name)
            
            # インデックス情報を読み込み
            self._load_index_info(table_name)
            
            # 統計情報を読み込み
            self._load_stats_info(table_name)
            
            # DDL情報を読み込み
            self._load_ddl_info(table_name)
            
        except Exception as e:
            self.error_handler.handle_error(e, f"テーブル詳細情報の読み込みエラー: {table_name}")
            MessageBox.show_error(f"テーブル詳細情報の読み込みに失敗しました: {str(e)}")
            
    def _load_column_info(self, table_name: str):
        """カラム情報を読み込み"""
        try:
            conn = self.db_connection.get_connection()
            cursor = conn.cursor()
            
            # PRAGMA table_info でカラム情報を取得
            cursor.execute(f"PRAGMA table_info(`{table_name}`)")
            columns_data = cursor.fetchall()
            
            # カラムヘッダー
            headers = ["ID", "カラム名", "データ型", "NOT NULL", "デフォルト値", "主キー"]
            
            # データを整形
            formatted_data = []
            for col in columns_data:
                cid, name, type_, notnull, default_val, pk = col
                formatted_data.append([
                    cid,
                    name,
                    type_ or "TEXT",
                    "YES" if notnull else "NO",
                    default_val or "",
                    "YES" if pk else "NO"
                ])
                
            # テーブルに表示
            self.columns_table.load_data(formatted_data, headers)
            
        except Exception as e:
            self.logger.error(f"カラム情報の読み込みエラー: {e}")
            raise
            
    def _load_index_info(self, table_name: str):
        """インデックス情報を読み込み"""
        try:
            conn = self.db_connection.get_connection()
            cursor = conn.cursor()
            
            # PRAGMA index_list でインデックス一覧を取得
            cursor.execute(f"PRAGMA index_list(`{table_name}`)")
            indexes = cursor.fetchall()
            
            # インデックス詳細情報を取得
            index_data = []
            for idx in indexes:
                seq, name, unique, origin, partial = idx
                
                # インデックスの詳細情報を取得
                cursor.execute(f"PRAGMA index_info(`{name}`)")
                index_info = cursor.fetchall()
                
                # カラム名を取得
                columns = []
                for info in index_info:
                    seqno, cid, col_name = info
                    columns.append(col_name)
                    
                index_data.append([
                    name,
                    "YES" if unique else "NO",
                    ", ".join(columns),
                    origin,
                    "YES" if partial else "NO"
                ])
                
            # ヘッダー
            headers = ["インデックス名", "ユニーク", "カラム", "作成方法", "部分インデックス"]
            
            # テーブルに表示
            self.indexes_table.load_data(index_data, headers)
            
        except Exception as e:
            self.logger.error(f"インデックス情報の読み込みエラー: {e}")
            raise
            
    def _load_stats_info(self, table_name: str):
        """統計情報を読み込み"""
        try:
            conn = self.db_connection.get_connection()
            cursor = conn.cursor()
            
            # 基本統計情報を取得
            stats_data = []
            
            # 行数
            cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
            row_count = cursor.fetchone()[0]
            stats_data.append(["行数", str(row_count)])
            
            # テーブルサイズ（概算）
            cursor.execute(f"PRAGMA table_info(`{table_name}`)")
            columns = cursor.fetchall()
            column_count = len(columns)
            stats_data.append(["カラム数", str(column_count)])
            
            # 各カラムの統計情報
            for col in columns:
                col_name = col[1]
                col_type = col[2]
                
                try:
                    # NULL値の数
                    cursor.execute(f"SELECT COUNT(*) FROM `{table_name}` WHERE `{col_name}` IS NULL")
                    null_count = cursor.fetchone()[0]
                    
                    # ユニーク値の数
                    cursor.execute(f"SELECT COUNT(DISTINCT `{col_name}`) FROM `{table_name}`")
                    unique_count = cursor.fetchone()[0]
                    
                    stats_data.append([f"{col_name} (NULL値)", str(null_count)])
                    stats_data.append([f"{col_name} (ユニーク値)", str(unique_count)])
                    
                except sqlite3.Error:
                    # エラーが発生した場合はスキップ
                    continue
                    
            # ヘッダー
            headers = ["項目", "値"]
            
            # テーブルに表示
            self.stats_table.load_data(stats_data, headers)
            
        except Exception as e:
            self.logger.error(f"統計情報の読み込みエラー: {e}")
            raise
            
    def _load_ddl_info(self, table_name: str):
        """DDL情報を読み込み"""
        try:
            conn = self.db_connection.get_connection()
            cursor = conn.cursor()
            
            # CREATE文を取得
            cursor.execute(
                "SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
                (table_name,)
            )
            result = cursor.fetchone()
            
            if result and result[0]:
                ddl = result[0]
                
                # フォーマットを整える
                formatted_ddl = self._format_ddl(ddl)
                
                # テキストエリアに表示
                self.ddl_text.delete(1.0, tk.END)
                self.ddl_text.insert(1.0, formatted_ddl)
            else:
                self.ddl_text.delete(1.0, tk.END)
                self.ddl_text.insert(1.0, "DDL情報が見つかりません。")
                
        except Exception as e:
            self.logger.error(f"DDL情報の読み込みエラー: {e}")
            raise
            
    def _format_ddl(self, ddl: str) -> str:
        """DDLを見やすくフォーマット"""
        # 簡単なフォーマット処理
        formatted = ddl.replace(',', ',\n    ')
        formatted = formatted.replace('(', '(\n    ')
        formatted = formatted.replace(')', '\n)')
        
        return formatted
        
    def _export_schema(self):
        """スキーマ情報をエクスポート"""
        try:
            from tkinter import filedialog
            
            # 保存先を選択
            file_path = filedialog.asksaveasfilename(
                title="スキーマエクスポート",
                defaultextension=".sql",
                filetypes=[("SQLファイル", "*.sql"), ("すべてのファイル", "*.*")]
            )
            
            if not file_path:
                return
                
            # スキーマ情報を取得してファイルに保存
            conn = self.db_connection.get_connection()
            cursor = conn.cursor()
            
            # すべてのテーブルのCREATE文を取得
            cursor.execute(
                "SELECT sql FROM sqlite_master WHERE type='table' ORDER BY name"
            )
            tables = cursor.fetchall()
            
            # インデックスのCREATE文を取得
            cursor.execute(
                "SELECT sql FROM sqlite_master WHERE type='index' AND sql IS NOT NULL ORDER BY name"
            )
            indexes = cursor.fetchall()
            
            # ファイルに書き込み
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("-- スキーマエクスポート\n")
                f.write(f"-- 生成日時: {self._get_current_datetime()}\n\n")
                
                f.write("-- テーブル定義\n")
                for table in tables:
                    if table[0]:
                        f.write(f"{table[0]};\n\n")
                        
                f.write("-- インデックス定義\n")
                for index in indexes:
                    if index[0]:
                        f.write(f"{index[0]};\n\n")
                        
            MessageBox.show_info(f"スキーマを {file_path} にエクスポートしました。")
            
        except Exception as e:
            self.error_handler.handle_error(e, "スキーマエクスポートエラー")
            MessageBox.show_error(f"スキーマのエクスポートに失敗しました: {str(e)}")
            
    def _get_current_datetime(self) -> str:
        """現在の日時を取得"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
    def refresh(self):
        """タブの更新"""
        self._load_schema_info()
        
        # 選択されているテーブルがあれば詳細情報も更新
        selection = self.table_listbox.curselection()
        if selection:
            table_name = self.table_listbox.get(selection[0])
            self._load_table_details(table_name)