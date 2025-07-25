import os
import subprocess
import logging
import time
import tkinter as tk
from tkinter import ttk
from _99_database_config import current_path, py_path
from datetime import datetime
import threading

# ログの設定
log_filename = f'script_execution_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
logging.basicConfig(filename=log_filename, level=logging.INFO)

class ProgressDialog:
    def __init__(self, parent, title="データ更新", x_offset=0, y_offset=0):
        self.parent = parent
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry(f"300x150+{x_offset}+{y_offset}")

        self.label = ttk.Label(self.dialog, text="処理待機中...")
        self.label.pack(pady=5)

        self.progress_bar = ttk.Progressbar(self.dialog, maximum=100, mode='determinate')
        self.progress_bar.pack(fill='x', padx=10, pady=5)

        self.time_label = ttk.Label(self.dialog, text="経過時間: 0秒")
        self.time_label.pack(pady=5)

        self.close_button = ttk.Button(self.dialog, text="閉じる", command=self.close)
        self.close_button.pack(pady=5)

        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.update()

    def close(self):
        self.dialog.destroy()

    def update_pg(self, total, current, script_name, elapsed_time):
        progress_value = min(current / total, 1.0) if total > 0 else 0
        self.progress_bar["value"] = int(progress_value * 100)
        self.label.configure(text=f"処理中: {script_name} ({current}/{total})")
        self.time_label.configure(text=f"経過時間: {elapsed_time:.2f}秒")
        self.dialog.update_idletasks()
        self.dialog.update()

def execute_script(script_path, progress_dialog, index, total_scripts, start_time):
    try:
        process = subprocess.Popen([py_path, script_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        while True:
            line = process.stdout.readline()
            if not line:
                break
            
            if "進捗:" in line:  # 例: "進捗: 50%"
                try:
                    progress = int(line.strip().split(":")[1].replace("%", ""))
                    progress_dialog.update_pg(100, progress, script_path, time.time() - start_time)
                except ValueError:
                    pass
            time.sleep(0.1)  # 更新頻度調整

        process.wait()
        progress_dialog.close()  # 子ウィンドウはスクリプト終了時に閉じる
        return process.returncode == 0
    except Exception as e:
        logging.error(f"[エラー] スクリプト実行中の例外: {script_path}, エラー: {e}")
        return False

def main():
    root = tk.Tk()
    
    scripts = [
        'z01_excel_close.py',
        'a1_app_open_edge.py',
        'a1_app_open_a.py',
        'z900_filecopy_txt.py',
        'z090_zp138_txt.py',
        'z090_zp138_field_mapping.py',
        'zm87.py',
        'zp02.py',
        'zt_zm87_code.py',
        'zs65.py',
        'zs61_all.py',
        'zs58.py',
        'zm29.py',
        'zp70.py',
        'ZP51.py',
        'z_mala_dl.py',
        'z_view_pcmaster.py',
        'z_Parsed Pc Master Diff Logger.py',
        'a1_app_open_ac.py',
        
    ]

    total_scripts = len(scripts)
    start_time = time.time()
    overall_progress_dialog = ProgressDialog(root, title="全体の進捗", x_offset=100, y_offset=100)
    overall_progress_dialog.dialog.geometry("400x200")

    for index, script in enumerate(scripts):
        script_path = os.path.join(current_path, script)
        if not os.path.exists(script_path):
            logging.warning(f"[警告] スクリプトが存在しません: {script_path}")
            continue
    
        elapsed_time = time.time() - start_time
        overall_progress_dialog.update_pg(total_scripts, index, script, elapsed_time)
    
        script_progress_dialog = ProgressDialog(root, title=f"{script} の進捗", x_offset=200 + index * 40, y_offset=250 + index * 40)
        script_progress_dialog.update_pg(100, 0, script, elapsed_time)
    
        logging.info(f"[実行開始] {script}")
        if not execute_script(script_path, script_progress_dialog, index, total_scripts, start_time):
            logging.error(f"[再実行エラー] {script} 失敗")
        logging.info(f"[実行終了] {script}")

    overall_progress_dialog.label.configure(text="完了")
    overall_progress_dialog.dialog.deiconify()
    overall_progress_dialog.dialog.update()
    
    final_script1 = os.path.join(current_path, '_01_sap_zm61_comp.py')
    if os.path.exists(final_script1):
        subprocess.run([py_path, final_script1], check=True)
    
    root.mainloop()

if __name__ == '__main__':
    main()
