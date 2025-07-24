"""
Analyze Tab Module for SQLite GUI Tool

This module provides the data analysis tab functionality for the SQLite GUI Tool.
"""

import tkinter as tk
from tkinter import ttk


class AnalyzeTab:
    """Analyze tab for analyzing data in SQLite database"""
    
    def __init__(self, parent, app):
        """Initialize the analyze tab
        
        Args:
            parent: The parent frame
            app: The main application instance
        """
        self.parent = parent
        self.app = app
        
        # Create the tab UI
        self._create_ui()
        
    def _create_ui(self):
        """Create the analyze tab UI"""
        # メインフレーム
        analyze_frame = ttk.Frame(self.parent)
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
        
    def on_analyze_table_select(self, event):
        """テーブル選択時の処理"""
        # This method will be implemented in the main application
        self.app.on_analyze_table_select(event)
        
    def execute_analysis(self):
        """分析を実行"""
        # This method will be implemented in the main application
        self.app.execute_analysis()
        
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
            
            self.analyze_table_combo['values'] = tables
            if tables:
                self.analyze_table_var.set(tables[0])
                # カラム一覧を更新
                self.update_column_list(tables[0])
            else:
                self.analyze_table_var.set("")
                self.analyze_column_combo['values'] = []
                self.analyze_column_var.set("")
                
        except Exception as e:
            self.app.show_message(f"テーブル一覧の更新エラー: {e}", "error")
        
    def on_db_disconnect(self):
        """データベース切断時の処理"""
        # テーブル一覧をクリア
        self.analyze_table_combo['values'] = []
        self.analyze_table_var.set("")
        
        # カラム一覧をクリア
        self.analyze_column_combo['values'] = []
        self.analyze_column_var.set("")
        
        # 結果表示をクリア
        self.analysis_result_text.delete(1.0, tk.END)
        
    def update_column_list(self, table_name):
        """カラム一覧を更新
        
        Args:
            table_name: テーブル名
        """
        if not self.app.conn:
            return
            
        try:
            self.app.cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [row[1] for row in self.app.cursor.fetchall()]
            
            self.analyze_column_combo['values'] = columns
            if columns:
                self.analyze_column_var.set(columns[0])
        except Exception as e:
            self.app.show_message(f"カラム情報の取得エラー: {e}", "error")
        
    def refresh(self):
        """タブの表示を更新"""
        if self.app.conn:
            self.on_db_connect(self.app.conn, self.app.cursor)