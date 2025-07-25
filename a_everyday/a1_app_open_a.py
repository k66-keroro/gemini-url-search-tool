import subprocess
import glob
import os


def OUTLOOK_open():
    app_path = r'C:\Program Files\Microsoft Office\root\Office16\OUTLOOK.EXE'
    subprocess.Popen([app_path])

if __name__ == "__main__":
    OUTLOOK_open()  # これで直接実行時のみOutlookが開かれる
    
def chrome_open():
    app_path1 = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
    subprocess.Popen([app_path1])

if __name__ == "__main__":
    chrome_open()  # これで直接実行時のみchromeが開かれる

def Arc_open():
    app_path2 = r'C:\Users\sem3171\AppData\Local\Microsoft\WindowsApps\Arc.exe'
    subprocess.Popen([app_path2])

if __name__ == "__main__":
    Arc_open()  # これで直接実行時のみArcが開かれる
    


def VSCode_open():
    app_path3 = r'C:\Users\sem3171\AppData\Local\Programs\Microsoft VS Code\Code.exe'

    subprocess.Popen([app_path3])
if __name__ == "__main__":
    VSCode_open()  # これで直接実行時のみVSCodeが開かれる    

def notion_open():
    app_path4 = r'C:\Users\sem3171\AppData\Local\Programs\Notion\Notion.exe'
    try:
        subprocess.Popen([app_path4])
        print('Notionを開きました')
    except Exception as e:
        print(f'エラーが発生しました: {e}')
if __name__ == "__main__":
    notion_open()  # これで直接実行時のみNotionが開かれる
    

def cursor_open():
    app_path6 = r"C:\Users\sem3171\AppData\Local\Programs\cursor\resources\app\bin\cursor.cmd"
    try:
        subprocess.Popen([app_path6], shell=True)
        print("Cursorを開きました (CMD版)")
    except Exception as e:
        print(f"エラーが発生しました: {e}")

if __name__ == "__main__":
    cursor_open()  
