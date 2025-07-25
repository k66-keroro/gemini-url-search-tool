import os
import subprocess
import time

import _01_sap_login
import _01_sap_logout
import pyautogui as p
from _99_database_config import current_path, py_path

# _01_sap_logoutファイルのディレクトリを設定
notebook_directory = r"C:\t_20_python\a_everyday"

# スクリプトの実行前にディレクトリを変更
os.chdir(notebook_directory)


subprocess.run([py_path, current_path + r'\_01_sap_logout.py'])
p.sleep(4)

# _01_sap_loginを実行
subprocess.run([py_path, current_path + r'\_01_sap_login.py'])

p.sleep(1)
# p.press('tab')


tr_str = "zm61"
p.write(tr_str)
p.press('enter')

p.sleep(1)
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


p.sleep(1)
p.press('enter')
p.sleep(1)
p.press('enter')
p.sleep(1)
p.press('up')
p.press('enter')
p.sleep(1)
p.press('enter')
    
#p.sleep(10)
