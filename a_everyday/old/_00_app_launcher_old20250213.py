import os
import sys
import tkinter as tk
from subprocess import call

from _99_database_config import current_path, py_path

# スクリプトの実行前にディレクトリを変更
os.chdir(current_path)

# メイン関数
def main():
    ButtonDef = (
        ("アプリ起動", lambda e: doapp(os.path.join(current_path, "_00_アプリ起動_main_spot.py"))),
        ("アプリ終了", lambda e: doapp1(os.path.join(current_path, "_00_アプリ終了.py"))),
        ("sap_login", lambda e: dosap(os.path.join(current_path, "_01_sap_login.py"))),
        ("sap_logout", lambda e: dosap1(os.path.join(current_path, "_01_sap_logout.py"))),
        ("sap_zm61_comp", lambda e: dosapzm61(os.path.join(current_path, "_01_sap_zm61_comp.py"))),
        ("sap_zm61_excel", lambda e: dosapzm61e(os.path.join(current_path, "_01_sap_zm61_comp_excel.py"))),
        ("sap_zm61_rename", lambda e: dosapzm61r(os.path.join(current_path, "_01_sap_zm61_rename.py"))),
        ("delete_cache", lambda e: dosap_cache(os.path.join(current_path, "a001_delete_cache.py"))),
        ("b1_filecheck", lambda e: dosap_cache(os.path.join(current_path, "b1_filecheck.py"))),
        ("z1_script_check", lambda e: dosap_cache(os.path.join(current_path, "z1_script_check.py"))),
        ("エクスプローラ", doexplorer),
        ("終わり", sys.exit),
    )

    root = tk.Tk()
    root.title("ランチャー")
    root.minsize(100, 60)
    root.option_add("*Button.font", "ＭＳPゴシック 12")

    for label, func in ButtonDef:
        Button = tk.Button(text=label)
        Button.bind("<Button-1>", func)
        Button.pack(fill=tk.X)

    root.mainloop()

# ボタン毎の動作を定義（イベントドライバ群）
def doapp(e):
    call(["python", e])

def doapp1(e):
    call(["python", e])

def dosap(e):
    call(["python", e])

def dosap1(e):
    call(["python", e])

def dosapzm61(e):
    call(["python", e])

def dosapzm61e(e):
    call(["python", e])

def dosapzm61r(e):  # 修正された関数名
    call(["python", e])

def dosap_cache(e):
    call(["python", e])

def doexplorer(e):
    call(r"explorer.exe " + os.getcwd())

if __name__ == "__main__":
    main()
