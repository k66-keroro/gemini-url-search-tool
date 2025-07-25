import os
import subprocess
from win32com.client import Dispatch  # pip install pywin32

def find_latest_chatgpt_exe():
    base_path = r"C:\Program Files\WindowsApps"
    prefix = "OpenAI.ChatGPT-Desktop_"
    suffix = "_x64__2p2nqsd0c76g0"
    app_relative_path = os.path.join("app", "ChatGPT.exe")

    try:
        # WindowsApps は読み取り制限あり → try/except で安全に扱う
        candidates = [
            d for d in os.listdir(base_path)
            if d.startswith(prefix) and d.endswith(suffix)
        ]
    except PermissionError:
        print("❌ WindowsApps フォルダへのアクセスが拒否されました。管理者で実行してください。")
        return None
    except Exception as e:
        print(f"❌ フォルダ探索中にエラー: {e}")
        return None

    if not candidates:
        print("❌ ChatGPT のインストールフォルダが見つかりません。")
        return None

    # バージョンが新しい順にソートして、最も新しいものを選ぶ
    candidates.sort(reverse=True)
    latest = candidates[0]
    full_exe_path = os.path.join(base_path, latest, app_relative_path)

    if os.path.isfile(full_exe_path):
        return full_exe_path
    else:
        print(f"❌ ChatGPT.exe が存在しません: {full_exe_path}")
        return None

def create_shortcut(target_path, shortcut_path, description=""):
    shell = Dispatch('WScript.Shell')
    shortcut = shell.CreateShortcut(shortcut_path)
    shortcut.TargetPath = target_path
    shortcut.WorkingDirectory = os.path.dirname(target_path)
    shortcut.Description = description
    shortcut.Save()
    print(f"✅ ショートカット作成: {shortcut_path}")

def launch_shortcut(shortcut_path):
    if os.path.exists(shortcut_path):
        subprocess.Popen(["cmd", "/c", "start", "", shortcut_path])
        print("🚀 ChatGPT を起動しました（ショートカット）")
    else:
        print("❌ ショートカットが見つかりません")

if __name__ == "__main__":
    # 保存するショートカットのパス（固定でOK）
    shortcut_path = os.path.expandvars(r"%LOCALAPPDATA%\Programs\ChatGPT.lnk")

    exe_path = find_latest_chatgpt_exe()
    if exe_path:
        create_shortcut(exe_path, shortcut_path, "ChatGPT Auto Shortcut")
        launch_shortcut(shortcut_path)
