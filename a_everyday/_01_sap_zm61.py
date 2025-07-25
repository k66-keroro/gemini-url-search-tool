import os
import subprocess
import time

import psutil

# Excelプロセスを取得
excel_processes = [p for p in psutil.process_iter(['name']) if 'EXCEL.EXE' in p.info['name']]

# Excelプロセスを強制終了
for process in excel_processes:
    try:
        process.terminate()
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass

# ファイルの操作を行う前に、Excelが完全に終了するまで待つ
time.sleep(5)






import _01_sap_login
import _01_sap_logout
import pyautogui as p
from _99_database_config import current_path, py_path

# _01_sap_logoutファイルのディレクトリを設定
notebook_directory = r"C:\t_20_python\a_everyday"

# スクリプトの実行前にディレクトリを変更
os.chdir(notebook_directory)


#subprocess.run([py_path, current_path + r'\_01_sap_logout.py'])
#p.sleep(4)

## _01_sap_loginを実行
#subprocess.run([py_path, current_path + r'\_01_sap_login.py'])


p.sleep(3)
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

#for _ in range(3):
#    p.press('down')
#p.sleep(1)
#p.press('tab')
#p.press('f4')
p.sleep(1)
p.press('enter')
p.press('enter')
p.sleep(1)

p.press('up')

#for _ in range(4):
# ....   p.press('up')
# p.sleep(1)
for _ in range(3):
    p.press('enter')
p.sleep(4)
p.press('up')
for _ in range(5):
    p.press('enter')

p.sleep(1)
