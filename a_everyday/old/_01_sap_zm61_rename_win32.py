import os
import time

import psutil
import win32com.client

# 変更前ファイル
path1 = r'C:\Projects_workspace\01_excel/Basis (1) の ワークシート.xlsx'

# 変更後ファイル
path2 = r'C:\Users\sem3171\OneDrive - 株式会社三社電機製作所\00_PC共有/zm61_pc.xlsx'

if (os.path.isfile(path2)):
    os.remove(path2)

time.sleep(2.5)
# ファイル名の変更
os.rename(path1, path2)

excel_app = win32com.client.Dispatch("Excel.Application")
excel_app.Quit()


def close_application(process_name):
    for process in psutil.process_iter(['pid', 'name']):
        if process.info['name'] == process_name:
            try:
                pid = process.info['pid']
                os.system(f"taskkill /F /PID {pid}")
                print(f"Process {process_name} with PID {pid} terminated.")
            except Exception as e:
                print(f"Error terminating process {process_name}: {e}")


close_application("saplogon.exe")
# ファイルの存在確認
print(os.path.exists(path2))
