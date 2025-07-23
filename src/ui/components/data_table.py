"""
データテーブル表示コンポーネント

ツリービューを使用したデータの表形式表示機能を提供します。
"""

import tkinter as tk
from tkinter import ttk
from typing import List, Optional, Any, Tuple

from src.utils.logger import Logger
from src.utils.error_handler import ErrorHandler


class DataTable:
    """データテーブル表示クラス"""
    
    def __init__(self, parent: tk.Widget, show_row_numbers: bool = False):
        """
        初期化
        
        Args:
            parent: 親ウィジェット
            show_row_numbers: 行番号を表示するかどうか
        """
        self.parent = parent
        self.show_row_numbers = show_row_numbers
        self.tree: Optional[ttk.Treeview] = None
        self.y_scrollbar: Optional[ttk.Scrollbar] = None
        self.x_scrollbar: Optional[ttk.Scrollbar] = None
        self.frame: Optional[ttk.Frame] = None
        self.columns: List[str] = []
        self.data: List[Tuple] = []
        
        self._initialize()
    
    def _initialize(self) -> None:
        """初期化"""
        try:
            # メインフレーム
            self.frame = ttk.Frame(self.parent)
            
            # ツリービュー
            self.tree = ttk.Treeview(self.frame)
            
            # スクロールバー
            self.y_scrollbar = ttk.Scrollbar(
                self.frame, 
                orient="vertical", 
                command=self.tree.yview
            )
            self.x_scrollbar = ttk.Scrollbar(
                self.frame, 
                orient="horizontal", 
                command=self.tree.xview
            )
            
            # スクロールバーの設定
            self.tree.configure(
                yscrollcommand=self.y_scrollbar.set,
                xscrollcommand=self.x_scrollbar.set
            )
            
            # 配置
            self.tree.grid(row=0, column=0, sticky="nsew")
            self.y_scrollbar.grid(row=0, column=1, sticky="ns")
            self.x_scrollbar.grid(row=1, column=0, sticky="ew")
            
            # グリッドの重みを設定
            self.frame.grid_rowconfigure(0, weight=1)
            self.frame.grid_columnconfigure(0, weight=1)
            
        except Exception as e:
            ErrorHandler.handle_exception(e, context="データテーブルの初期化")
    
    def pack(self, **kwargs) -> None:
        """フレームをpack"""
        if self.frame:
            self.frame.pack(**kwargs)
    
    def grid(self, **kwargs) -> None:
        """フレームをgrid"""
        if self.frame:
            self.frame.grid(**kwargs)
    
    def set_columns(self, columns: List[str]) -> None:
        """
        列を設定
        
        Args:
            columns: 列名のリスト
        """
        try:
            if not self.tree:
                return
            
            self.columns = columns.copy()
            
            # 行番号を表示する場合は先頭に追加
            display_columns = ["#"] + columns if self.show_row_numbers else columns
            
            self.tree["columns"] = display_columns
            self.tree["show"] = "headings"  # ヘッダーのみ表示
            
            # 列の見出しと幅を設定
            for i, col in enumerate(display_columns):
                self.tree.heading(col, text=str(col))
                
                # 行番号列は幅を狭く設定
                if self.show_row_numbers and i == 0:
                    self.tree.column(col, width=50, anchor="center")
                else:
                    self.tree.column(col, width=100)
            
            Logger.debug(f"データテーブルの列を設定しました: {len(display_columns)}列")
            
        except Exception as e:
            ErrorHandler.handle_exception(e, context="データテーブルの列設定")
    
    def insert_data(self, data: List[Tuple], clear_existing: bool = True) -> None:
        """
        データを挿入
        
        Args:
            data: 挿入するデータのリスト
            clear_existing: 既存のデータをクリアするかどうか
        """
        try:
            if not self.tree:
                return
            
            # 既存のデータをクリア
            if clear_existing:
                self.clear()
            
            self.data = data.copy()
            
            # データを挿入
            for row_index, row in enumerate(data):
                # NULL値を「NULL」として表示
                formatted_row = [
                    str(val) if val is not None else "NULL" 
                    for val in row
                ]
                
                # 行番号を表示する場合は先頭に追加
                if self.show_row_numbers:
                    formatted_row = [str(row_index + 1)] + formatted_row
                
                self.tree.insert("", "end", values=formatted_row)
            
            # 列幅を調整
            self.adjust_column_widths()
            
            Logger.debug(f"データテーブルにデータを挿入しました: {len(data)}行")
            
        except Exception as e:
            ErrorHandler.handle_exception(e, context="データテーブルへのデータ挿入")
    
    def append_data(self, data: List[Tuple]) -> None:
        """
        データを追加
        
        Args:
            data: 追加するデータのリスト
        """
        self.insert_data(data, clear_existing=False)
    
    def clear(self) -> None:
        """データをクリア"""
        try:
            if self.tree:
                for item in self.tree.get_children():
                    self.tree.delete(item)
                self.data.clear()
                Logger.debug("データテーブルをクリアしました")
        except Exception as e:
            ErrorHandler.handle_exception(e, context="データテーブルのクリア")
    
    def adjust_column_widths(self) -> None:
        """列幅を調整"""
        try:
            if not self.tree or not self.tree["columns"]:
                return
            
            display_columns = self.tree["columns"]
            
            for i, col in enumerate(display_columns):
                # 行番号列はスキップ
                if self.show_row_numbers and i == 0:
                    continue
                
                # 列の値の最大長を計算
                max_len = len(str(col))
                
                # データから最大長を計算
                data_col_index = i - 1 if self.show_row_numbers else i
                if data_col_index < len(self.columns):
                    for row in self.data:
                        if data_col_index < len(row):
                            val = row[data_col_index]
                            if val is not None:
                                val_len = len(str(val))
                                if val_len > max_len:
                                    max_len = min(val_len, 50)  # 最大50文字
                
                # 列幅を設定（文字数 * 平均文字幅）
                char_width = 8  # 平均文字幅（ピクセル）
                column_width = max(max_len * char_width, 80)  # 最小幅80px
                self.tree.column(col, width=column_width)
            
        except Exception as e:
            ErrorHandler.handle_exception(e, context="データテーブルの列幅調整")
    
    def get_selected_items(self) -> List[Tuple]:
        """
        選択されたアイテムを取得
        
        Returns:
            選択されたデータのリスト
        """
        try:
            if not self.tree:
                return []
            
            selected_items = []
            for item_id in self.tree.selection():
                values = self.tree.item(item_id, "values")
                if values:
                    # 行番号を除外
                    if self.show_row_numbers:
                        values = values[1:]
                    selected_items.append(values)
            
            return selected_items
            
        except Exception as e:
            ErrorHandler.handle_exception(e, context="選択アイテムの取得")
            return []
    
    def get_all_data(self) -> List[Tuple]:
        """
        全データを取得
        
        Returns:
            全データのリスト
        """
        return self.data.copy()
    
    def get_column_names(self) -> List[str]:
        """
        列名を取得
        
        Returns:
            列名のリスト
        """
        return self.columns.copy()
    
    def set_sort_function(self, column: str, sort_func) -> None:
        """
        ソート機能を設定
        
        Args:
            column: ソート対象の列名
            sort_func: ソート関数
        """
        try:
            if self.tree and column in self.columns:
                self.tree.heading(column, command=lambda: sort_func(column))
        except Exception as e:
            ErrorHandler.handle_exception(e, context="ソート機能の設定")
    
    def filter_data(self, filter_func) -> None:
        """
        データをフィルタリング
        
        Args:
            filter_func: フィルタリング関数
        """
        try:
            if not self.data:
                return
            
            filtered_data = [row for row in self.data if filter_func(row)]
            self.insert_data(filtered_data)
            
        except Exception as e:
            ErrorHandler.handle_exception(e, context="データのフィルタリング")
    
    def export_to_csv(self, file_path: str, include_headers: bool = True) -> bool:
        """
        データをCSVファイルにエクスポート
        
        Args:
            file_path: 出力ファイルパス
            include_headers: ヘッダーを含めるかどうか
            
        Returns:
            成功した場合True
        """
        try:
            import csv
            
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                
                # ヘッダーを書き込み
                if include_headers:
                    writer.writerow(self.columns)
                
                # データを書き込み
                for row in self.data:
                    # NULL値を空文字列に変換
                    formatted_row = [
                        str(val) if val is not None else ""
                        for val in row
                    ]
                    writer.writerow(formatted_row)
            
            Logger.info(f"データをCSVファイルにエクスポートしました: {file_path}")
            return True
            
        except Exception as e:
            ErrorHandler.handle_exception(e, context="CSVエクスポート")
            return False
    
    def set_row_height(self, height: int) -> None:
        """
        行の高さを設定
        
        Args:
            height: 行の高さ（ピクセル）
        """
        try:
            if self.tree:
                style = ttk.Style()
                style.configure("Treeview", rowheight=height)
        except Exception as e:
            ErrorHandler.handle_exception(e, context="行の高さ設定")
    
    def bind_double_click(self, callback) -> None:
        """
        ダブルクリックイベントをバインド
        
        Args:
            callback: コールバック関数
        """
        try:
            if self.tree:
                self.tree.bind("<Double-1>", callback)
        except Exception as e:
            ErrorHandler.handle_exception(e, context="ダブルクリックイベントのバインド")
    
    def bind_right_click(self, callback) -> None:
        """
        右クリックイベントをバインド
        
        Args:
            callback: コールバック関数
        """
        try:
            if self.tree:
                self.tree.bind("<Button-3>", callback)
        except Exception as e:
            ErrorHandler.handle_exception(e, context="右クリックイベントのバインド")