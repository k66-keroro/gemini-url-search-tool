import time

import psutil
import pyautogui as p
import pygetwindow as gw
import pyperclip


def get_process_pid(process_name):
    for process in psutil.process_iter(['pid', 'name']):
        if process.info['name'].lower() == process_name.lower():
            return process.info['pid']
    return None


def get_window_by_title(title):
    windows = gw.getWindowsWithTitle(title)
    if windows:
        return windows[0]
    return None


def activate_window(window):
    window.minimize()
    window.restore()
    window.activate()
    time.sleep(0.5)


# Excelウィンドウタイトル（必要に応じて変更してください）
excel_window_title = "Basis (1) の ワークシート - Excel"

# Excelプロセスを取得
excel_pid = get_process_pid("EXCEL.EXE")

if excel_pid:
    # ウィンドウハンドルをタイトルで取得
    excel_window = get_window_by_title(excel_window_title)

    if excel_window:
        # ウィンドウをアクティブにする
        activate_window(excel_window)

        # F12キーを押下
        p.press('f12')
        p.press('enter')
        p.press('tab')
        p.press('enter')

        p.sleep(1)
        p.press('f12')
        p.press('f4')
        p.sleep(1)
        p.hotkey('ctrl', 'a')
        s_path = r"C:\Projects_workspace\01_excel"
        # クリップボードにファイルパスをコピー
        pyperclip.copy(s_path)
        # Ctrl+Vで貼り付け
        p.hotkey('ctrl', 'v')
        p.sleep(2)
        p.press('enter')
        for _ in range(6):
            p.press('tab')
        p.press('enter')
        p.press('enter')
    else:
        print("Excelウィンドウが見つかりませんでした。".encode('CP932').decode('CP932'))
else:
    print("Excelプロセスが見つかりませんでした。".encode('CP932').decode('CP932'))
