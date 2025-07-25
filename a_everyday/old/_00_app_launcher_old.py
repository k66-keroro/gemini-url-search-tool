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
        #    ラベル  関数
        (
            "アプリ起動",
            lambda e: doapp(
                os.path.join(os.path.dirname(__file__),
                             "_00_アプリ起動_main_spot.py")
            ),
        ),
        (
            "アプリ終了",
            lambda e: doapp1(
                os.path.join(os.path.dirname(__file__), "_00_アプリ終了.py")
            ),
        ),
        (
            "sap_login",
            lambda e: dosap(
                os.path.join(os.path.dirname(__file__), "_01_sap_login.py")
            ),
        ),
        (
            "sap_logout",
            lambda e: dosap1(
                os.path.join(os.path.dirname(__file__), "_01_sap_logout.py")
            ),
        ),
        (
            "sap_zm61_comp",
            lambda e: dosapzm61(
                os.path.join(os.path.dirname(__file__), "_01_sap_zm61_comp.py")
            ),
        ),
        (
            "sap_zm61_excel",
            lambda e: dosapzm61e(
                os.path.join(os.path.dirname(__file__),"_01_sap_zm61_comp_excel.py")
            ),
        ),
        (
            "sap_zm61_rename",
            lambda e: dosapzm61e(
                os.path.join(os.path.dirname(__file__),"_01_sap_zm61_rename.py")
            ),            
        ), 
       (
            "dereat_cache",
            lambda e: dosapzm61e(
                os.path.join(os.path.dirname(__file__),"a001_dereat_cache.py")
            ),            
        ),                
        ("エクスプローラ", doexplorer),
        ("終わり", sys.exit),
    )

    root = tk.Tk()
    root.title("ランチャー")
    root.minsize(100, 60)  # 最小ウィンドウサイズ、
    # ボタンはこの幅まで横に延ばされる
    # ボタンの個数が増えると自動的に縦に延びる
    # ボタンを配置
    root.option_add("*Button.font", "ＭＳPゴシック 12")
    for label, func in ButtonDef:
        Button = tk.Button(text=label)
        Button.bind("<Button-1>", func)
        Button.pack(fill=tk.X)

    root.mainloop()


# ボタン毎の動作を定義（イベントドライバ群）

file01 = "\_00_アプリ起動_main_spot.py"
file02 = "\_00_アプリ終了.py"
file03 = "\_01_sap_login.py"
file04 = "\_01_sap_logout.py"
file05 = "\_01_sap_zm61_comp.py"
file06 = "\_01_sap_zm61_comp_excel.py"
file07 = "\_01_sap_zm61_rename.py"
file08 = "\a001_dereat_cache.py"


def doapp(e):
    call(["python", current_path + file01])


def doapp1(e):
    call(["python", current_path + file02])


def dosap(e):
    call(["python", current_path + file03])


def dosap1(e):
    call(["python", current_path + file04])


def dosapzm61(e):
    call(["python", current_path + file05])


def dosapzm61e(e):
    call(["python", current_path + file06])

def dosapzm61e(e):
    call(["python", current_path + file07])
    
def dosapzm61e(e):
    call(["python", current_path + file08])        


def doexplorer(e):  # エクスプローラを起動
    call(r"explorer.exe " + os.getcwd())


if __name__ == "__main__":
    main()
