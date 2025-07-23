"""
SQLite GUI Tool メインアプリケーション
"""

import tkinter as tk
from tkinter import ttk
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any

from .tabs.query_tab import QueryTab
from .tabs.schema_tab import SchemaTab
from .tabs.import_tab import ImportTab
from .tabs.export_tab import ExportTab
from .tabs.analyze_tab import AnalyzeTab
from .tabs.converter_tab import ConverterTab
from .components.file_dialog import FileDialog
from .components.message_box import MessageBox
from ..core.db_connection import DatabaseConnection
from ..config.settings import Settings
from ..config.constants import APP_NAME, APP_VERSION
from ..utils.logger import Logger
from ..utils.error_handler import ErrorHandler


class SQLiteGUIApp:
    """SQLite GUI Tool メインアプリケーション"""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.settings = Settings()
        self.logger = Logger.get_logger(__name__)
        self.error_handler = ErrorHandler()
        
        # データベース接続
        self.db_connection = DatabaseConnection()
        
        # ウィンドウ設定
        self._setup_window()
        
        # メニュー作成
        self._create_menu()
        
        # メインフレーム作成
        self._create_main_frame()
        
        # 最近使用したデータベースを読み込み
        self._load_recent_databases()
        
    def _setup_window(self):
        """ウィンドウの設定"""
        self.root.title(f"{APP_NAME} v{APP_VERSION}")
        self.root.geometry("1024x768")
        
        # アイコン設定（あれば）
        icon_path = Path(__file__).parent.parent.parent / "assets" / "icon.ico"
        if icon_path.exists():
            self.root.iconbitmap(icon_path)
            
        # 終了時の処理
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # テーマ設定
        style = ttk.Style()
        try:
            style.theme_use("clam")  # より近代的なテーマ
        except tk.TclError:
            pass  # テーマが利用できない場合はデフォルトを使用
            
    def _create_menu(self):
        """メニューバーの作成"""
        menubar = tk.Menu(self.root)
        
        # ファイルメニュー
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="データベースを開く", command=self._open_database)
        file_menu.add_command(label="新規データベース作成", command=self._create_database)
        
        # 最近使用したデータベースのサブメニュー
        self.recent_menu = tk.Menu(file_menu, tearoff=0)
        file_menu.add_cascade(label="最近使用したデータベース", menu=self.recent_menu)
        
        file_menu.add_separator()
        file_menu.add_command(label="設定", command=self._show_settings)
        file_menu.add_separator()
        file_menu.add_command(label="終了", command=self._on_close)
        
        menubar.add_cascade(label="ファイル", menu=file_menu)
        
        # ツールメニュー
        tools_menu = tk.Menu(menubar, tearoff=0)
        tools_menu.add_command(label="データベース最適化", command=self._optimize_database)
        tools_menu.add_command(label="バキューム", command=self._vacuum_database)
        tools_menu.add_command(label="整合性チェック", command=self._check_integrity)
        menubar.add_cascade(label="ツール", menu=tools_menu)
        
        # ヘルプメニュー
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="ヘルプ", command=self._show_help)
        help_menu.add_command(label="バージョン情報", command=self._show_about)
        menubar.add_cascade(label="ヘルプ", menu=help_menu)
        
        self.root.config(menu=menubar)
        
    def _create_main_frame(self):
        """メインフレームの作成"""
        # メインフレーム
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 上部: データベース情報
        db_frame = ttk.Frame(self.main_frame)
        db_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(db_frame, text="データベース:").pack(side=tk.LEFT)
        
        self.db_path_var = tk.StringVar(value="接続されていません")
        db_path_label = ttk.Label(db_frame, textvariable=self.db_path_var)
        db_path_label.pack(side=tk.LEFT, padx=(5, 10))
        
        self.connect_btn = ttk.Button(
            db_frame,
            text="接続",
            command=self._open_database
        )
        self.connect_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.disconnect_btn = ttk.Button(
            db_frame,
            text="切断",
            command=self._disconnect_database,
            state='disabled'
        )
        self.disconnect_btn.pack(side=tk.LEFT)
        
        # タブコントロール
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # 各タブを作成
        self.tabs = {}
        self._create_tabs()
        
        # ステータスバー
        self.status_var = tk.StringVar(value="準備完了")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
    def _create_tabs(self):
        """タブの作成"""
        # クエリタブ
        self.tabs['query'] = QueryTab(self.notebook, self.db_connection)
        self.notebook.add(self.tabs['query'].frame, text="クエリ")
        
        # スキーマタブ
        self.tabs['schema'] = SchemaTab(self.notebook, self.db_connection)
        self.notebook.add(self.tabs['schema'].frame, text="スキーマ")
        
        # インポートタブ
        self.tabs['import'] = ImportTab(self.notebook, self.db_connection)
        self.notebook.add(self.tabs['import'].frame, text="インポート")
        
        # エクスポートタブ
        self.tabs['export'] = ExportTab(self.notebook, self.db_connection)
        self.notebook.add(self.tabs['export'].frame, text="エクスポート")
        
        # 分析タブ
        self.tabs['analyze'] = AnalyzeTab(self.notebook, self.db_connection)
        self.notebook.add(self.tabs['analyze'].frame, text="分析")
        
        # 変換タブ
        self.tabs['converter'] = ConverterTab(self.notebook, self.db_connection)
        self.notebook.add(self.tabs['converter'].frame, text="変換")
        
    def _open_database(self):
        """データベースを開く"""
        db_path = FileDialog.open_file(
            title="データベースを開く",
            filetypes=[
                ("SQLiteデータベース", "*.db;*.sqlite;*.sqlite3"),
                ("すべてのファイル", "*.*")
            ]
        )
        
        if db_path:
            self._connect_database(db_path)
            
    def _create_database(self):
        """新規データベースを作成"""
        db_path = FileDialog.save_file(
            title="新規データベース作成",
            defaultextension=".db",
            filetypes=[
                ("SQLiteデータベース", "*.db"),
                ("SQLiteデータベース", "*.sqlite"),
                ("SQLiteデータベース", "*.sqlite3"),
                ("すべてのファイル", "*.*")
            ]
        )
        
        if db_path:
            try:
                # 新規データベースを作成
                self.db_connection.create_database(db_path)
                
                # 接続
                self._connect_database(db_path)
                
                MessageBox.show_info(f"新規データベースを作成しました: {db_path}")
                
            except Exception as e:
                self.error_handler.handle_error(e, "データベース作成エラー")
                MessageBox.show_error(f"データベースの作成に失敗しました: {str(e)}")
                
    def _connect_database(self, db_path: str):
        """データベースに接続"""
        try:
            # 既存の接続を閉じる
            if self.db_connection.is_connected():
                self.db_connection.close()
                
            # 新しいデータベースに接続
            self.db_connection.connect(db_path)
            
            # UI更新
            self.db_path_var.set(db_path)
            self.connect_btn.config(state='disabled')
            self.disconnect_btn.config(state='normal')
            
            # 最近使用したデータベースに追加
            self._add_recent_database(db_path)
            
            # 各タブを更新
            self._refresh_all_tabs()
            
            self.status_var.set(f"データベース接続: {db_path}")
            
        except Exception as e:
            self.error_handler.handle_error(e, "データベース接続エラー")
            MessageBox.show_error(f"データベースへの接続に失敗しました: {str(e)}")
            
    def _disconnect_database(self):
        """データベース接続を切断"""
        try:
            if self.db_connection.is_connected():
                self.db_connection.close()
                
            # UI更新
            self.db_path_var.set("接続されていません")
            self.connect_btn.config(state='normal')
            self.disconnect_btn.config(state='disabled')
            
            # 各タブを更新
            self._refresh_all_tabs()
            
            self.status_var.set("データベース切断")
            
        except Exception as e:
            self.error_handler.handle_error(e, "データベース切断エラー")
            MessageBox.show_error(f"データベースの切断に失敗しました: {str(e)}")
            
    def _refresh_all_tabs(self):
        """すべてのタブを更新"""
        for tab in self.tabs.values():
            tab.refresh()
            
    def _load_recent_databases(self):
        """最近使用したデータベースを読み込み"""
        recent_dbs = self.settings.get('recent_databases', [])
        
        # メニューをクリア
        self.recent_menu.delete(0, tk.END)
        
        if recent_dbs:
            for db_path in recent_dbs:
                if os.path.exists(db_path):
                    self.recent_menu.add_command(
                        label=db_path,
                        command=lambda path=db_path: self._connect_database(path)
                    )
        else:
            self.recent_menu.add_command(label="履歴なし", state='disabled')
            
    def _add_recent_database(self, db_path: str):
        """最近使用したデータベースに追加"""
        recent_dbs = self.settings.get('recent_databases', [])
        
        # 既に存在する場合は削除して先頭に追加
        if db_path in recent_dbs:
            recent_dbs.remove(db_path)
            
        # 先頭に追加
        recent_dbs.insert(0, db_path)
        
        # 最大10件まで保持
        recent_dbs = recent_dbs[:10]
        
        # 設定を更新
        self.settings.set('recent_databases', recent_dbs)
        self.settings.save()
        
        # メニューを更新
        self._load_recent_databases()
        
    def _optimize_database(self):
        """データベースを最適化"""
        if not self.db_connection.is_connected():
            MessageBox.show_warning("データベースに接続されていません。")
            return
            
        try:
            # 最適化実行
            conn = self.db_connection.get_connection()
            cursor = conn.cursor()
            
            # PRAGMA optimize
            cursor.execute("PRAGMA optimize")
            
            MessageBox.show_info("データベースの最適化が完了しました。")
            
        except Exception as e:
            self.error_handler.handle_error(e, "データベース最適化エラー")
            MessageBox.show_error(f"データベースの最適化に失敗しました: {str(e)}")
            
    def _vacuum_database(self):
        """データベースのバキューム実行"""
        if not self.db_connection.is_connected():
            MessageBox.show_warning("データベースに接続されていません。")
            return
            
        # 確認ダイアログ
        if not MessageBox.show_question(
            "データベースのバキュームを実行しますか？\n"
            "この処理には時間がかかる場合があります。"
        ):
            return
            
        try:
            # バキューム実行
            conn = self.db_connection.get_connection()
            cursor = conn.cursor()
            
            # VACUUM
            cursor.execute("VACUUM")
            
            MessageBox.show_info("データベースのバキュームが完了しました。")
            
        except Exception as e:
            self.error_handler.handle_error(e, "データベースバキュームエラー")
            MessageBox.show_error(f"データベースのバキュームに失敗しました: {str(e)}")
            
    def _check_integrity(self):
        """データベースの整合性チェック"""
        if not self.db_connection.is_connected():
            MessageBox.show_warning("データベースに接続されていません。")
            return
            
        try:
            # 整合性チェック実行
            conn = self.db_connection.get_connection()
            cursor = conn.cursor()
            
            # PRAGMA integrity_check
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()[0]
            
            if result == "ok":
                MessageBox.show_info("データベースの整合性チェックに問題はありませんでした。")
            else:
                MessageBox.show_warning(f"データベースの整合性に問題があります: {result}")
                
        except Exception as e:
            self.error_handler.handle_error(e, "整合性チェックエラー")
            MessageBox.show_error(f"整合性チェックに失敗しました: {str(e)}")
            
    def _show_settings(self):
        """設定ダイアログを表示"""
        # 設定ダイアログの実装
        settings_window = tk.Toplevel(self.root)
        settings_window.title("設定")
        settings_window.geometry("500x400")
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        # 設定内容を実装
        ttk.Label(settings_window, text="設定", font=("", 12, "bold")).pack(pady=10)
        
        # 設定項目
        settings_frame = ttk.Frame(settings_window)
        settings_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 例: 表示行数設定
        row_frame = ttk.Frame(settings_frame)
        row_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(row_frame, text="デフォルト表示行数:").pack(side=tk.LEFT)
        
        row_limit_var = tk.StringVar(value=self.settings.get('default_row_limit', '1000'))
        row_limit_entry = ttk.Entry(row_frame, textvariable=row_limit_var, width=10)
        row_limit_entry.pack(side=tk.LEFT, padx=(5, 0))
        
        # ボタン
        button_frame = ttk.Frame(settings_window)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def save_settings():
            try:
                # 設定を保存
                self.settings.set('default_row_limit', int(row_limit_var.get()))
                self.settings.save()
                settings_window.destroy()
                
            except ValueError:
                MessageBox.show_error("入力値が正しくありません。")
                
        ttk.Button(button_frame, text="保存", command=save_settings).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="キャンセル", command=settings_window.destroy).pack(side=tk.RIGHT)
        
    def _show_help(self):
        """ヘルプを表示"""
        help_text = """
SQLite GUI Tool ヘルプ

【基本操作】
・データベースを開く: ファイルメニューから「データベースを開く」を選択
・クエリ実行: クエリタブでSQLを入力し、「実行」ボタンをクリック
・テーブル構造確認: スキーマタブでテーブルを選択

【各タブの機能】
・クエリ: SQL文の実行と結果表示
・スキーマ: テーブル構造とインデックスの表示
・インポート: CSVやExcelファイルのインポート
・エクスポート: テーブルデータのエクスポート
・分析: データの統計情報と品質分析
・変換: データ形式の変換とクレンジング

詳細なマニュアルは開発者にお問い合わせください。
"""
        
        help_window = tk.Toplevel(self.root)
        help_window.title("ヘルプ")
        help_window.geometry("600x400")
        help_window.transient(self.root)
        
        text = tk.Text(help_window, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(help_window, orient=tk.VERTICAL, command=text.yview)
        text.config(yscrollcommand=scrollbar.set)
        
        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
        
        text.insert(tk.END, help_text)
        text.config(state='disabled')
        
    def _show_about(self):
        """バージョン情報を表示"""
        about_text = f"""
{APP_NAME} v{APP_VERSION}

SQLiteデータベース管理ツール

Copyright © 2023-2025
"""
        
        MessageBox.show_info(about_text, title="バージョン情報")
        
    def _on_close(self):
        """アプリケーション終了時の処理"""
        try:
            # データベース接続を閉じる
            if self.db_connection.is_connected():
                self.db_connection.close()
                
            # 設定を保存
            self.settings.save()
            
            # アプリケーションを終了
            self.root.destroy()
            
        except Exception as e:
            self.error_handler.handle_error(e, "終了処理エラー")
            self.root.destroy()
            
    def run(self):
        """アプリケーションの実行"""
        self.root.mainloop()


def main():
    """メイン関数"""
    root = tk.Tk()
    app = SQLiteGUIApp(root)
    app.run()


if __name__ == "__main__":
    main()