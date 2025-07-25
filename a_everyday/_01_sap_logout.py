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


close_application("saplogon.exe")
