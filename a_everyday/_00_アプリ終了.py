import psutil
import os


def close_application(process_name):
    for process in psutil.process_iter(['pid', 'name']):
        if process.info['name'] == process_name:
            try:
                pid = process.info['pid']
                os.system(f"taskkill /F /PID {pid}")
                print(f"Process {process_name} with PID {pid} terminated.")
            except Exception as e:
                print(f"Error terminating process {process_name}: {e}")


# Excelを終了
close_application("EXCEL.EXE")

# Outlookを終了
close_application("OUTLOOK.EXE")
# close_application("python.exe")
close_application("Arc.exe")
close_application("Docker Desktop.exe")

close_application("MSACCESS.EXE")
close_application("saplogon.exe")
close_application("chrome.exe")
close_application("msedge.exe")
# close_application("explorer.exe")
# close_application("Taskmgr.exe")
