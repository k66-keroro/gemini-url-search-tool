import os
import time

import pyautogui as p
import pyperclip
import win32con
import win32gui

path1 = r'C:\Projects_workspace\01_excel/Basis (1) の ワークシート.xlsx'
#path1 = r'C:\Users\sem3171\OneDrive - 株式会社三社電機製作所\ドキュメント 2\/ALVXXL01 (1) の ワークシート.xlsx'
if (os.path.isfile(path1)):
    os.remove(path1)


def get_hwnds_by_title(title):
    def callback(hwnd, hwnds):
        if win32gui.IsWindowVisible(hwnd) and win32gui.IsWindowEnabled(hwnd):
            found_title = win32gui.GetWindowText(hwnd)
            if found_title and found_title == title:
                hwnds.append(hwnd)
        return True

    hwnds = []
    win32gui.EnumWindows(callback, hwnds)
    return hwnds


def activate_window(hwnd):
    win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)  # 最小化
    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)   # 復元
    # p.hotkey('alt', 'tab')  # Alt+Tabをシミュレート
    time.sleep(0.5)  # Alt+Tabが完了するのを待つ


excel_window_title = "ALVXXL01 (1) の ワークシート - Excel"

# Excelのウィンドウハンドルを取得
excel_hwnds = get_hwnds_by_title(excel_window_title)

if excel_hwnds:
    # 最後に見つかったExcelウィンドウをアクティブにする
    last_excel_hwnd = excel_hwnds[-1]
    activate_window(last_excel_hwnd)

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
    # p.sleep(1)
    s_path = r"C:\Projects_workspace\01_excel"
    # クリップボードにファイルパスをコピー
    pyperclip.copy(s_path)
    # Ctrl+Vで貼り付け
    p.hotkey('ctrl', 'v')
    # p.press('enter')
    p.sleep(2)

    p.press('enter')
    for _ in range(6):
        p.press('tab')
    p.press('enter')
    p.press('enter')


else:
    print(f"{excel_window_title} のウィンドウが見つかりませんでした。")
