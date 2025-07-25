import subprocess
import os

def ChatGPT_open():
    app_path = r"C:\Program Files\WindowsApps\OpenAI.ChatGPT-Desktop_1.2025.139.0_x64__2p2nqsd0c76g0\app\ChatGPT.exe"
    if os.path.exists(app_path):
        try:
            subprocess.Popen([app_path])
            print(f"ChatGPTを開きました: {app_path}")
        except Exception as e:
            print(f"エラーが発生しました: {e}")
    else:
        print("ChatGPTの実行ファイルが見つかりませんでした")

if __name__ == "__main__":
    ChatGPT_open()