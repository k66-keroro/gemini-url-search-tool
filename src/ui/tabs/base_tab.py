"""
タブの基底クラス

全てのタブで共通する機能を提供します。
"""

import tkinter as tk
from tkinter import ttk
from abc import ABC, abstractmethod
from typing import Optional, Any

from src.core.db_connection import DatabaseConnection
from src.config.settings import get_settings
from src.utils.logger import Logger
from src.utils.error_handler import ErrorHandler


class BaseTab(ABC):
    """タブの基底クラス"""
    
    def __init__(self, parent: tk.Widget, db_connection: DatabaseConnection):
        """
        初期化
        
        Args:
            parent: 親ウィジェット
            db_connection: データベース接続オブジェクト
        """
        self.parent = parent
        self.db_connection = db_connection
        self.settings = get_settings()
        self.frame: Optional[ttk.Frame] = None
        self.is_initialized = False
        self.is_enabled = False
        
        # タブ固有の設定
        self.tab_name = self.__class__.__name__.replace("Tab", "")
        
    @abstractmethod
    def initialize(self) -> ttk.Frame:
        """
        タブの初期化（サブクラスで実装）
        
        Returns:
            タブのメインフレーム
        """
        pass
    
    @abstractmethod
    def update_after_connection(self) -> None:
        """
        データベース接続後の更新処理（サブクラスで実装）
        """
        pass
    
    def get_frame(self) -> Optional[ttk.Frame]:
        """
        タブのフレームを取得
        
        Returns:
            タブのメインフレーム
        """
        if not self.is_initialized:
            try:
                self.frame = self.initialize()
                self.is_initialized = True
                Logger.debug(f"{self.tab_name}タブを初期化しました")
            except Exception as e:
                ErrorHandler.handle_exception(e, context=f"{self.tab_name}タブの初期化")
        
        return self.frame
    
    def enable(self) -> None:
        """タブを有効化"""
        self.is_enabled = True
        self._update_ui_state()
        Logger.debug(f"{self.tab_name}タブを有効化しました")
    
    def disable(self) -> None:
        """タブを無効化"""
        self.is_enabled = False
        self._update_ui_state()
        Logger.debug(f"{self.tab_name}タブを無効化しました")
    
    def _update_ui_state(self) -> None:
        """UI状態を更新（サブクラスでオーバーライド可能）"""
        pass
    
    def clear(self) -> None:
        """タブの内容をクリア（サブクラスでオーバーライド可能）"""
        pass
    
    def refresh(self) -> None:
        """タブの内容を更新（サブクラスでオーバーライド可能）"""
        if self.db_connection.is_connected:
            self.update_after_connection()
    
    def get_status_message(self) -> str:
        """
        ステータスメッセージを取得（サブクラスでオーバーライド可能）
        
        Returns:
            ステータスメッセージ
        """
        if not self.is_enabled:
            return f"{self.tab_name}タブは無効です"
        return f"{self.tab_name}タブが有効です"
    
    def save_tab_settings(self, settings_dict: dict) -> None:
        """
        タブ固有の設定を保存
        
        Args:
            settings_dict: 保存する設定の辞書
        """
        try:
            for key, value in settings_dict.items():
                setting_key = f"tabs.{self.tab_name.lower()}.{key}"
                self.settings.set(setting_key, value)
            
            Logger.debug(f"{self.tab_name}タブの設定を保存しました")
            
        except Exception as e:
            ErrorHandler.handle_exception(
                e, 
                context=f"{self.tab_name}タブの設定保存",
                show_message=False
            )
    
    def load_tab_settings(self) -> dict:
        """
        タブ固有の設定を読み込み
        
        Returns:
            設定の辞書
        """
        try:
            tab_settings = self.settings.get(f"tabs.{self.tab_name.lower()}", {})
            Logger.debug(f"{self.tab_name}タブの設定を読み込みました")
            return tab_settings
            
        except Exception as e:
            ErrorHandler.handle_exception(
                e, 
                context=f"{self.tab_name}タブの設定読み込み",
                show_message=False
            )
            return {}
    
    def create_labeled_frame(
        self, 
        parent: tk.Widget, 
        text: str, 
        **kwargs
    ) -> ttk.LabelFrame:
        """
        ラベル付きフレームを作成
        
        Args:
            parent: 親ウィジェット
            text: ラベルテキスト
            **kwargs: その他のオプション
            
        Returns:
            作成されたラベルフレーム
        """
        return ttk.LabelFrame(parent, text=text, **kwargs)
    
    def create_button_frame(
        self, 
        parent: tk.Widget, 
        buttons: list, 
        **kwargs
    ) -> ttk.Frame:
        """
        ボタンフレームを作成
        
        Args:
            parent: 親ウィジェット
            buttons: ボタン情報のリスト [(text, command, state), ...]
            **kwargs: その他のオプション
            
        Returns:
            作成されたボタンフレーム
        """
        button_frame = ttk.Frame(parent, **kwargs)
        
        for i, button_info in enumerate(buttons):
            if len(button_info) >= 2:
                text, command = button_info[:2]
                state = button_info[2] if len(button_info) > 2 else "normal"
                
                button = ttk.Button(
                    button_frame, 
                    text=text, 
                    command=command, 
                    state=state
                )
                button.pack(side=tk.LEFT, padx=5)
        
        return button_frame
    
    def create_info_label(
        self, 
        parent: tk.Widget, 
        textvariable: tk.StringVar, 
        **kwargs
    ) -> ttk.Label:
        """
        情報表示ラベルを作成
        
        Args:
            parent: 親ウィジェット
            textvariable: テキスト変数
            **kwargs: その他のオプション
            
        Returns:
            作成されたラベル
        """
        default_kwargs = {
            "wraplength": 800,
            "justify": "left"
        }
        default_kwargs.update(kwargs)
        
        return ttk.Label(parent, textvariable=textvariable, **default_kwargs)
    
    def show_progress(self, message: str) -> None:
        """
        進行状況を表示（サブクラスでオーバーライド可能）
        
        Args:
            message: 進行状況メッセージ
        """
        Logger.info(f"{self.tab_name}タブ: {message}")
    
    def hide_progress(self) -> None:
        """進行状況を非表示（サブクラスでオーバーライド可能）"""
        pass
    
    def validate_database_connection(self) -> bool:
        """
        データベース接続を検証
        
        Returns:
            接続されている場合True
        """
        if not self.db_connection.is_connected:
            from src.ui.components.message_box import MessageBox
            MessageBox.show_error(
                "エラー",
                "データベースに接続されていません。",
                "先にデータベースに接続してください。"
            )
            return False
        return True
    
    def handle_exception(self, exception: Exception, context: str = "") -> None:
        """
        例外を処理
        
        Args:
            exception: 発生した例外
            context: エラーのコンテキスト
        """
        full_context = f"{self.tab_name}タブ"
        if context:
            full_context += f" - {context}"
        
        ErrorHandler.handle_exception(exception, context=full_context)
    
    def get_common_file_types(self) -> list:
        """
        共通のファイルタイプを取得
        
        Returns:
            ファイルタイプのリスト
        """
        return [
            ("すべてのファイル", "*.*"),
            ("テキストファイル", "*.txt"),
            ("CSVファイル", "*.csv"),
            ("Excelファイル", "*.xlsx *.xls")
        ]
    
    def format_number(self, number: int) -> str:
        """
        数値を3桁区切りでフォーマット
        
        Args:
            number: フォーマットする数値
            
        Returns:
            フォーマットされた数値文字列
        """
        return f"{number:,}"
    
    def format_time(self, seconds: float) -> str:
        """
        時間をフォーマット
        
        Args:
            seconds: 秒数
            
        Returns:
            フォーマットされた時間文字列
        """
        if seconds < 1:
            return f"{seconds * 1000:.0f}ms"
        elif seconds < 60:
            return f"{seconds:.3f}秒"
        else:
            minutes = int(seconds // 60)
            remaining_seconds = seconds % 60
            return f"{minutes}分{remaining_seconds:.1f}秒"
    
    def __str__(self) -> str:
        """文字列表現"""
        return f"{self.tab_name}Tab(enabled={self.is_enabled}, initialized={self.is_initialized})"
    
    def __repr__(self) -> str:
        """デバッグ用文字列表現"""
        return self.__str__()