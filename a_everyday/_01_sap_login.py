import os
import pyautogui
import subprocess
import time
import _01_sap_logout

import os

# _01_sap_logoutファイルのディレクトリを設定
notebook_directory = r"C:\t_20_python\a_everyday"

# スクリプトの実行前にディレクトリを変更
os.chdir(notebook_directory)

# SAP GUI のパス
filename = r'C:\Program Files (x86)\SAP\FrontEnd\SAPgui\saplogon.exe'

# SAP GUI を起動
subprocess.Popen(filename)

# SAP GUI のウィンドウがアクティブになるまで待つ
sap_gui_title = "SAP Logon "
active_window = None
while not active_window:
    windows = pyautogui.getWindowsWithTitle(sap_gui_title)
    for window in windows:
        if window.title.startswith(sap_gui_title):
            active_window = window
            break
time.sleep(3)
# ウィンドウをアクティブにする
active_window.activate()
pyautogui.press('enter')


time.sleep(2)
# IDフィールドに入力する文字列
# id_string = "pp1144"
id_string = os.getenv('sap_id')
# パスワードフィールドに入力する文字列
password_string = os.getenv('sap_PASSWORD')
print(password_string)
# パスワードが取得できた場合のみ入力する
if password_string:
    pyautogui.write(id_string)
    pyautogui.press('tab')
    pyautogui.write(password_string)
    pyautogui.press('enter')
else:
    print("環境変数'sap_PASSWORD'からパスワードが取得できませんでした。")
