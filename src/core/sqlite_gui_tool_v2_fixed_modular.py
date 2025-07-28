"""
SQLite GUI Tool - エントリーポイント

モジュール化されたSQLite GUI Toolのエントリーポイントです。
"""

import tkinter as tk
import sys
import os
from pathlib import Path
import traceback

# プロジェクトルートを特定
SCRIPT_DIR = Path(os.path.abspath(os.path.dirname(__file__)))
PROJECT_ROOT = SCRIPT_DIR.parent.parent  # src/core の2つ上の階層

# プロジェクトルートをsys.pathに追加
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# 必要なモジュールをインポート
try:
    # SQLite GUI Toolのインポート
    from src.core.sqlite_gui_tool import SQLiteGUITool
except ImportError as e:
    print(f"エラー: モジュールのインポートに失敗しました: {e}")
    print(traceback.format_exc())
    sys.exit(1)


def main():
    """メイン関数"""
    try:
        # Tkinterのルートウィンドウを作成
        root = tk.Tk()
        root.title("SQLite GUI Tool v2")

        # SQLite GUI Toolのインスタンスを作成
        app = SQLiteGUITool(root)

        # イベントループを開始
        root.mainloop()
    except Exception as e:
        print(f"エラー: アプリケーションの起動に失敗しました: {e}")
        print(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
