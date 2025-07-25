import tkinter as tk
import subprocess
import time
import threading

# 実行中のスクリプトを管理するリスト
running_scripts = []

def check_process():
    while True:
        # 現在実行中のプロセスを確認
        output = subprocess.run(['tasklist'], capture_output=True, text=True)
        print(output.stdout)
        # ここで実行中のスクリプトをチェック
        current_scripts = ["_00_アプリ起動_main", "z01_excel_close.py", "a1_app_open_edge.py", 
                           "a1_app_open_a.py", "z900_filecopy_txt.py", "z090_zp138_txt.py", 
                           "z090_zp138_field_mapping.py", "zm87.py", "zp02.py", 
                           "zt_zm87_code.py", "zs65.py", "a1_app_open_ac.py"]

        running_scripts.clear()  # リストをクリア
        for script in current_scripts:
            if script in output.stdout:
                running_scripts.append(script)

        # UIを更新
        update_ui()
        time.sleep(5)  # 5秒ごとにチェック

def update_ui():
    # 実行中のスクリプトをラベルに表示
    status_text = "\n".join(running_scripts) if running_scripts else "実行中のスクリプトはありません。"
    status_var.set(status_text)

root = tk.Tk()
status_var = tk.StringVar(root)
status_label = tk.Label(root, textvariable=status_var, justify='left')
status_label.pack()

# 別スレッドでプロセスチェックを開始
threading.Thread(target=check_process, daemon=True).start()

root.mainloop()
