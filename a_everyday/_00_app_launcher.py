import os
import sys
import tkinter as tk
from subprocess import Popen
import threading

from _99_database_config import current_path, py_path

# スクリプトの実行前にディレクトリを変更
os.chdir(current_path)

# メイン関数
def main():
    ButtonDef = (
        ("アプリ起動", lambda: run_in_thread(doapp, os.path.join(current_path, "_00_アプリ起動_main_spot.py"))),
        ("アプリ終了", lambda: run_in_thread(doapp1, os.path.join(current_path, "_00_アプリ終了.py"))),
        ("sap_login", lambda: run_in_thread(dosap, os.path.join(current_path, "_01_sap_login.py"))),
        ("sap_logout", lambda: run_in_thread(dosap1, os.path.join(current_path, "_01_sap_logout.py"))),
        ("sap_zm61_comp", lambda: run_in_thread(dosapzm61, os.path.join(current_path, "_01_sap_zm61_comp.py"))),
        ("sap_zm61_excel", lambda: run_in_thread(dosapzm61e, os.path.join(current_path, "_01_sap_zm61_comp_excel.py"))),
        ("sap_zm61_rename", lambda: run_in_thread(dosapzm61r, os.path.join(current_path, "_01_sap_zm61_rename.py"))),
        ("delete_cache", lambda: run_in_thread(dosap_cache, os.path.join(current_path, "a001_delete_cache.py"))),
        ("b1_filecheck", lambda: run_in_thread(dosap_cache, os.path.join(current_path, "b1_filecheck.py"))),
        ("z1_script_check", lambda: run_in_thread(dosap_cache, os.path.join(current_path, "z1_script_check.py"))),
        ("_00_アプリ起動_main", lambda: run_in_thread(dosap_cache, os.path.join(current_path, "_00_アプリ起動_main.py"))),
        ("エクスプローラ", doexplorer),
        
        ("終わり", sys.exit),
    )

    root = tk.Tk()
    root.title("ランチャー")
    root.minsize(100, 60)
    root.option_add("*Button.font", "ＭＳPゴシック 12")

    for label, func in ButtonDef:
        Button = tk.Button(text=label, command=func)
        Button.pack(fill=tk.X)

    root.mainloop()

# ボタン毎の動作を定義（イベントドライバ群）
def run_in_thread(func, *args):
    thread = threading.Thread(target=func, args=args)
    thread.start()

def doapp(e):
    Popen(["python", e])

def doapp1(e):
    Popen(["python", e])

def dosap(e):
    Popen(["python", e])

def dosap1(e):
    Popen(["python", e])

def dosapzm61(e):
    Popen(["python", e])

def dosapzm61e(e):
    Popen(["python", e])

def dosapzm61r(e):
    Popen(["python", e])

def dosap_cache(e):
    Popen(["python", e])

def doexplorer():
    Popen(["explorer.exe", os.getcwd()])  # 修正

if __name__ == "__main__":
    main()
