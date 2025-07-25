# _04_OUTLOOK_open.py
import subprocess


def OUTLOOK_open():
    app_path = r'C:\Program Files\Microsoft Office\root\Office16\OUTLOOK.EXE'
    subprocess.Popen([app_path])

if __name__ == "__main__":
    OUTLOOK_open()  # これで直接実行時のみOutlookが開かれる