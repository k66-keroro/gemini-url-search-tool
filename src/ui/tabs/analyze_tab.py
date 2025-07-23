"""
データ分析タブ
データベースのテーブルデータを分析し、統計情報を表示する
"""

import tkinter as tk
from tkinter import ttk
import sqlite3
import pandas as pd
from typing import Optional, List, Dict, Any, Tuple

from .base_tab import BaseTab
from ..components.data_table import DataTable
from ..components.message_box import MessageBox
from ...core.db_connection import DatabaseConnection
from ...core.table_utils import TableUtils
from ...utils.error_handler import ErrorHandler
from ...utils.logger import Logger


class AnalyzeTab(BaseTab):
    """データ分析タブ"""
    
    def __init__(self, parent, db_connection: DatabaseConnection):
        super().__init__(parent, "分析")
        self.db_connection = db_connection
        self.table_utils = TableUtils(db_connection)
        self.logger = Logger.get_logger(__name__)
        self.error_handler = ErrorHandler()
        
        self._create_widgets()
        self._load_tables()
        
    def _create_widgets(self):
        """ウィジェットの作成"""
        # メインフレーム
        main_frame = ttk.Frame(self.frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 上部: 分析設定
        top_frame = ttk.LabelFrame(main_frame, text="分析設定", padding=5)
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
        
        # 分析実行ボタン
        self.analyze_btn = ttk.Button(
            table_frame,
            text="分析実行",
            command=self._analyze_data,
            state='disabled'
        )
        self.analyze_btn.pack(side=tk.LEFT, padx=(5, 0))
        
        # 分析オプション
        options_frame = ttk.Frame(top_frame)
        options_frame.pack(fill=tk.X, pady=(5, 0))
        
        # 基本統計
        self.basic_stats_var = tk.BooleanVar(value=True)
        basic_check = ttk.Checkbutton(
            options_frame,
            text="基本統計",
            variable=self.basic_stats_var
        )
        basic_check.pack(side=tk.LEFT, padx=(0, 10))
        
        # データ品質チェック
        self.quality_check_var = tk.BooleanVar(value=True)
        quality_check = ttk.Checkbutton(
            options_frame,
            text="データ品質チェック",
            variable=self.quality_check_var
        )
        quality_check.pack(side=tk.LEFT, padx=(0, 10))
        
        # 重複データ検出
        self.duplicate_check_var = tk.BooleanVar(value=True)
        duplicate_check = ttk.Checkbutton(
            options_frame,
            text="重複データ検出",
            variable=self.duplicate_check_var
        )
        duplicate_check.pack(side=tk.LEFT, padx=(0, 10))
        
        # カラム分析
        self.column_analysis_var = tk.BooleanVar(value=False)
        column_check = ttk.Checkbutton(
            options_frame,
            text="詳細カラム分析",
            variable=self.column_analysis_var
        )
        column_check.pack(side=tk.LEFT)
        
        # 中央: 分析結果表示
        result_frame = ttk.Frame(main_frame)
        result_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        # タブ形式で結果を表示
        self.result_notebook = ttk.Notebook(result_frame)
        self.result_notebook.pack(fill=tk.BOTH, expand=True)
        
        # 基本統計タブ
        self.stats_frame = ttk.Frame(self.result_notebook)
        self.result_notebook.add(self.stats_frame, text="基本統計")
        
        self.stats_table = DataTable(self.stats_frame)
        self.stats_table.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # データ品質タブ
        self.quality_frame = ttk.Frame(self.result_notebook)
        self.result_notebook.add(self.quality_frame, text="データ品質")
        
        self.quality_table = DataTable(self.quality_frame)
        self.quality_table.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 重複データタブ
        self.duplicate_frame = ttk.Frame(self.result_notebook)
        self.result_notebook.add(self.duplicate_frame, text="重複データ")
        
        self.duplicate_table = DataTable(self.duplicate_frame)
        self.duplicate_table.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # カラム分析タブ
        self.column_frame = ttk.Frame(self.result_notebook)
        self.result_notebook.add(self.column_frame, text="カラム分析")
        
        self.column_table = DataTable(self.column_frame)
        self.column_table.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 下部: ステータス
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X)
        
        self.status_var = tk.StringVar(value="準備完了")
        status_label = ttk.Label(status_frame, textvariable=self.status_var)
        status_label.pack(side=tk.LEFT)
        
        # プログレスバー
        self.progress = ttk.Progressbar(status_frame, mode='indeterminate')
        self.progress.pack(side=tk.RIGHT, padx=(10, 0))
        
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
            MessageBox.show_error(f"テーブル一覧の読み込みに失敗しました: {str(e)}")
            
    def _on_table_selected(self, event=None):
        """テーブル選択時の処理"""
        table_name = self.table_var.get()
        if table_name:
            self.analyze_btn.config(state='normal')
        else:
            self.analyze_btn.config(state='disabled')
            
    def _analyze_data(self):
        """データ分析を実行"""
        table_name = self.table_var.get()
        if not table_name:
            MessageBox.show_warning("テーブルが選択されていません。")
            return
            
        try:
            self.status_var.set("分析実行中...")
            self.progress.start()
            self.analyze_btn.config(state='disabled')
            
            # 各分析を実行
            if self.basic_stats_var.get():
                self._analyze_basic_stats(table_name)
                
            if self.quality_check_var.get():
                self._analyze_data_quality(table_name)
                
            if self.duplicate_check_var.get():
                self._analyze_duplicates(table_name)
                
            if self.column_analysis_var.get():
                self._analyze_columns(table_name)
                
            self.status_var.set("分析完了")
            
        except Exception as e:
            self.error_handler.handle_error(e, "データ分析エラー")
            MessageBox.show_error(f"データ分析に失敗しました: {str(e)}")
            self.status_var.set("エラー")
            
        finally:
            self.progress.stop()
            self.analyze_btn.config(state='normal')
            
    def _analyze_basic_stats(self, table_name: str):
        """基本統計分析"""
        try:
            conn = self.db_connection.get_connection()
            cursor = conn.cursor()
            
            # テーブル情報を取得
            cursor.execute(f"PRAGMA table_info(`{table_name}`)")
            columns = cursor.fetchall()
            
            # 基本統計データ
            stats_data = []
            
            # 総行数
            cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
            total_rows = cursor.fetchone()[0]
            stats_data.append(["総行数", str(total_rows), ""])
            
            # カラム数
            stats_data.append(["カラム数", str(len(columns)), ""])
            
            # 各カラムの統計
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
                    
                    # 数値型の場合は追加統計
                    additional_info = ""
                    if col_type in ['INTEGER', 'REAL', 'NUMERIC']:
                        try:
                            cursor.execute(f"SELECT MIN(`{col_name}`), MAX(`{col_name}`), AVG(`{col_name}`) FROM `{table_name}` WHERE `{col_name}` IS NOT NULL")
                            min_val, max_val, avg_val = cursor.fetchone()
                            if min_val is not None:
                                additional_info = f"Min: {min_val}, Max: {max_val}, Avg: {avg_val:.2f}"
                        except:
                            pass
                    
                    stats_data.append([
                        f"{col_name} - NULL値",
                        f"{null_count} ({null_count/total_rows*100:.1f}%)",
                        ""
                    ])
                    stats_data.append([
                        f"{col_name} - ユニーク値",
                        str(unique_count),
                        additional_info
                    ])
                    
                except sqlite3.Error:
                    continue
                    
            # 結果を表示
            headers = ["項目", "値", "詳細"]
            self.stats_table.load_data(stats_data, headers)
            
        except Exception as e:
            self.logger.error(f"基本統計分析エラー: {e}")
            raise
            
    def _analyze_data_quality(self, table_name: str):
        """データ品質分析"""
        try:
            conn = self.db_connection.get_connection()
            cursor = conn.cursor()
            
            # テーブル情報を取得
            cursor.execute(f"PRAGMA table_info(`{table_name}`)")
            columns = cursor.fetchall()
            
            quality_data = []
            
            # 総行数を取得
            cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
            total_rows = cursor.fetchone()[0]
            
            for col in columns:
                col_name = col[1]
                col_type = col[2]
                
                try:
                    # NULL値チェック
                    cursor.execute(f"SELECT COUNT(*) FROM `{table_name}` WHERE `{col_name}` IS NULL")
                    null_count = cursor.fetchone()[0]
                    
                    # 空文字チェック（文字列型の場合）
                    empty_count = 0
                    if col_type in ['TEXT', 'VARCHAR']:
                        cursor.execute(f"SELECT COUNT(*) FROM `{table_name}` WHERE `{col_name}` = ''")
                        empty_count = cursor.fetchone()[0]
                    
                    # データ品質スコア計算
                    valid_count = total_rows - null_count - empty_count
                    quality_score = (valid_count / total_rows * 100) if total_rows > 0 else 0
                    
                    # 品質レベル判定
                    if quality_score >= 95:
                        quality_level = "優秀"
                    elif quality_score >= 80:
                        quality_level = "良好"
                    elif quality_score >= 60:
                        quality_level = "普通"
                    else:
                        quality_level = "要改善"
                    
                    quality_data.append([
                        col_name,
                        col_type,
                        str(null_count),
                        str(empty_count),
                        f"{quality_score:.1f}%",
                        quality_level
                    ])
                    
                except sqlite3.Error:
                    quality_data.append([
                        col_name,
                        col_type,
                        "エラー",
                        "エラー",
                        "エラー",
                        "エラー"
                    ])
                    
            # 結果を表示
            headers = ["カラム名", "データ型", "NULL値", "空文字", "品質スコア", "品質レベル"]
            self.quality_table.load_data(quality_data, headers)
            
        except Exception as e:
            self.logger.error(f"データ品質分析エラー: {e}")
            raise
            
    def _analyze_duplicates(self, table_name: str):
        """重複データ分析"""
        try:
            conn = self.db_connection.get_connection()
            cursor = conn.cursor()
            
            # テーブル情報を取得
            cursor.execute(f"PRAGMA table_info(`{table_name}`)")
            columns = cursor.fetchall()
            
            duplicate_data = []
            
            # 各カラムの重複チェック
            for col in columns:
                col_name = col[1]
                
                try:
                    # 重複値を検索
                    cursor.execute(f"""
                        SELECT `{col_name}`, COUNT(*) as count
                        FROM `{table_name}`
                        WHERE `{col_name}` IS NOT NULL
                        GROUP BY `{col_name}`
                        HAVING COUNT(*) > 1
                        ORDER BY count DESC
                        LIMIT 10
                    """)
                    
                    duplicates = cursor.fetchall()
                    
                    if duplicates:
                        for value, count in duplicates:
                            # 値が長すぎる場合は切り詰め
                            display_value = str(value)
                            if len(display_value) > 50:
                                display_value = display_value[:47] + "..."
                                
                            duplicate_data.append([
                                col_name,
                                display_value,
                                str(count),
                                f"{count-1}件の重複"
                            ])
                    else:
                        duplicate_data.append([
                            col_name,
                            "重複なし",
                            "0",
                            "問題なし"
                        ])
                        
                except sqlite3.Error as e:
                    duplicate_data.append([
                        col_name,
                        "エラー",
                        "エラー",
                        str(e)
                    ])
                    
            # 結果を表示
            headers = ["カラム名", "重複値", "出現回数", "状態"]
            self.duplicate_table.load_data(duplicate_data, headers)
            
        except Exception as e:
            self.logger.error(f"重複データ分析エラー: {e}")
            raise
            
    def _analyze_columns(self, table_name: str):
        """詳細カラム分析"""
        try:
            conn = self.db_connection.get_connection()
            cursor = conn.cursor()
            
            # テーブル情報を取得
            cursor.execute(f"PRAGMA table_info(`{table_name}`)")
            columns = cursor.fetchall()
            
            column_data = []
            
            for col in columns:
                col_name = col[1]
                col_type = col[2]
                
                try:
                    # 基本情報
                    cursor.execute(f"SELECT COUNT(*) FROM `{table_name}` WHERE `{col_name}` IS NOT NULL")
                    non_null_count = cursor.fetchone()[0]
                    
                    cursor.execute(f"SELECT COUNT(DISTINCT `{col_name}`) FROM `{table_name}`")
                    unique_count = cursor.fetchone()[0]
                    
                    # データ型別の詳細分析
                    type_info = ""
                    sample_values = ""
                    
                    if col_type in ['INTEGER', 'REAL', 'NUMERIC']:
                        # 数値型の分析
                        cursor.execute(f"""
                            SELECT MIN(`{col_name}`), MAX(`{col_name}`), AVG(`{col_name}`)
                            FROM `{table_name}` WHERE `{col_name}` IS NOT NULL
                        """)
                        min_val, max_val, avg_val = cursor.fetchone()
                        if min_val is not None:
                            type_info = f"範囲: {min_val} - {max_val}, 平均: {avg_val:.2f}"
                    else:
                        # 文字列型の分析
                        cursor.execute(f"""
                            SELECT AVG(LENGTH(`{col_name}`))
                            FROM `{table_name}` WHERE `{col_name}` IS NOT NULL
                        """)
                        avg_length = cursor.fetchone()[0]
                        if avg_length is not None:
                            type_info = f"平均文字数: {avg_length:.1f}"
                    
                    # サンプル値を取得
                    cursor.execute(f"""
                        SELECT DISTINCT `{col_name}`
                        FROM `{table_name}`
                        WHERE `{col_name}` IS NOT NULL
                        LIMIT 3
                    """)
                    samples = cursor.fetchall()
                    sample_values = ", ".join([str(s[0])[:20] for s in samples])
                    
                    column_data.append([
                        col_name,
                        col_type,
                        str(non_null_count),
                        str(unique_count),
                        type_info,
                        sample_values
                    ])
                    
                except sqlite3.Error:
                    column_data.append([
                        col_name,
                        col_type,
                        "エラー",
                        "エラー",
                        "エラー",
                        "エラー"
                    ])
                    
            # 結果を表示
            headers = ["カラム名", "データ型", "有効値数", "ユニーク値数", "統計情報", "サンプル値"]
            self.column_table.load_data(column_data, headers)
            
        except Exception as e:
            self.logger.error(f"カラム分析エラー: {e}")
            raise
            
    def refresh(self):
        """タブの更新"""
        # テーブル一覧を再読み込み
        self._load_tables()
        
        # 結果をクリア
        self.stats_table.clear()
        self.quality_table.clear()
        self.duplicate_table.clear()
        self.column_table.clear()
        
        self.status_var.set("準備完了")