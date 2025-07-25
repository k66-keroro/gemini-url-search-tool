import subprocess
import glob
import os

def ChatGPT_open():
    base_path = r"C:\Program Files\WindowsApps"
    search_pattern = os.path.join(base_path, "OpenAI.ChatGPT-Desktop_*_x64__2p2nqsd0c76g0", "app", "ChatGPT.exe")
    app_paths = glob.glob(search_pattern)

    if app_paths:
        app_path = app_paths[0]  # 最初に見つかったパスを使用
        try:
            subprocess.Popen([app_path])
            print(f"ChatGPTを開きました: {app_path}")
        except Exception as e:
            print(f"エラーが発生しました: {e}")
    else:
        print("ChatGPTの実行ファイルが見つかりませんでした")

if __name__ == "__main__":
    ChatGPT_open()