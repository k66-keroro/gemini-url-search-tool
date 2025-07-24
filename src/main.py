"""
SQLite GUI Tool メイン実行ファイル

プロジェクトのルートディレクトリから実行するためのエントリーポイント
"""

import sys
import os
import tkinter as tk
from pathlib import Path
import traceback

# プロジェクトのルートディレクトリをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 必要なディレクトリを作成
os.makedirs(project_root / "logs", exist_ok=True)
os.makedirs(project_root / "data" / "sqlite", exist_ok=True)
os.makedirs(project_root / "data" / "raw", exist_ok=True)

# SQLite GUI Toolのインポート
try:
    from src.core.sqlite_gui_tool import SQLiteGUITool
except ImportError as e:
    print(f"エラー: モジュールのインポートに失敗しました: {e}")
    print(traceback.format_exc())
    sys.exit(1)


def main():
    """メイン関数"""
    try:
        # Tkinterルートウィンドウの作成
        root = tk.Tk()
        root.title("SQLite GUI Tool v2")
        
        # SQLite GUI Toolのインスタンスを作成
        app = SQLiteGUITool(root)
        
        # イベントループを開始
        root.mainloop()
        
    except Exception as e:
        # 未処理の例外をキャッチ
        print(f"エラー: アプリケーションの起動に失敗しました: {e}")
        print(traceback.format_exc())
        
        # エラーメッセージを表示
        try:
            import tkinter.messagebox as messagebox
            messagebox.showerror(
                "エラー",
                f"アプリケーションの起動中にエラーが発生しました:\n{str(e)}"
            )
        except:
            pass
            
        sys.exit(1)


if __name__ == "__main__":
    main()