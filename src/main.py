"""
SQLite GUI Tool メイン実行ファイル
"""

import sys
import os
import tkinter as tk
from pathlib import Path

# プロジェクトのルートディレクトリをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 必要なディレクトリを作成
os.makedirs(project_root / "logs", exist_ok=True)
os.makedirs(project_root / "data" / "sqlite", exist_ok=True)
os.makedirs(project_root / "data" / "raw", exist_ok=True)

# アプリケーションのインポート
from src.ui.app import SQLiteGUIApp
from src.utils.logger import Logger
from src.utils.error_handler import ErrorHandler


def main():
    """メイン関数"""
    try:
        # ロガーの初期化
        logger = Logger.get_logger("main")
        logger.info("アプリケーション起動")
        
        # エラーハンドラの初期化
        error_handler = ErrorHandler()
        
        # Tkinterルートウィンドウの作成
        root = tk.Tk()
        
        # アプリケーションの作成と実行
        app = SQLiteGUIApp(root)
        app.run()
        
        logger.info("アプリケーション終了")
        
    except Exception as e:
        # 未処理の例外をキャッチ
        error_handler = ErrorHandler()
        error_handler.handle_error(e, "アプリケーション起動エラー")
        
        # エラーメッセージを表示
        try:
            import tkinter.messagebox as messagebox
            messagebox.showerror(
                "エラー",
                f"アプリケーションの起動中にエラーが発生しました:\n{str(e)}"
            )
        except:
            print(f"エラー: {str(e)}")
            
        sys.exit(1)


if __name__ == "__main__":
    main()