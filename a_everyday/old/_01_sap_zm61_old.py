# import _01_sap_zm61_excel
#import win32com.client
import subprocess
#import pyperclip
import time

import _01_sap_logout
import pyautogui as p

#import shutil

#_01_sap_logout


# SAP GUI のパス
filename = r'C:\Program Files (x86)\SAP\FrontEnd\SAPgui\saplogon.exe'

# SAP GUI を起動
subprocess.Popen(filename)

# SAP GUI のウィンドウがアクティブになるまで待つ
sap_gui_title = "SAP Logon "
active_window = None
while not active_window:
    windows = p.getWindowsWithTitle(sap_gui_title)
    for window in windows:
        if window.title.startswith(sap_gui_title):
            active_window = window
            break
time.sleep(4)

# ウィンドウをアクティブにする
active_window.activate()
p.press('enter')


time.sleep(4)
# IDフィールドに入力する文字列
id_string = "pp1144"

# パスワードフィールドに入力する文字列
password_string = "03171sakai3"

p.write(id_string)
p.press('tab')
p.write(password_string)
p.press('enter')

p.sleep(4)
# p.press('tab')


tr_str = "zm61"
p.write(tr_str)
p.press('enter')

p.sleep(4)
for _ in range(12):
    p.press('down')
p.hotkey('ctrl', 'a')

tr_str = "705144"
p.write(tr_str)
p.press('f8')

p.sleep(12)

p.hotkey('alt', 'l')
p.press('e')
p.press('a')

for _ in range(3):
    p.press('down')
p.sleep(1)
p.press('tab')
p.press('f4')

for _ in range(4):
    p.press('down')
# p.sleep(1)
for _ in range(3):
    p.press('enter')
p.sleep(4)
p.press('up')
for _ in range(5):
    p.press('enter')

p.sleep(10)
