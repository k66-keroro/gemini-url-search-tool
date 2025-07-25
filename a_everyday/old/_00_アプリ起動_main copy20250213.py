import os
import subprocess
import logging
import time
import tkinter as tk
from tkinter import ttk, messagebox
from _99_database_config import current_path, py_path
from datetime import datetime

# ログの設定
log_filename = f'script_execution_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
logging.basicConfig(filename=log_filename, level=logging.INFO)

class ProgressDialog:
    def __init__(self, parent):
        self.parent = parent
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("データ更新")
        self.dialog.geometry("300x150")

        self.label = ttk.Label(self.dialog, text="")
        self.label.grid(row=0, column=1, padx=5, pady=5, sticky="we")

        self.progress_bar = ttk.Progressbar(self.dialog, maximum=1)
        self.progress_bar.grid(row=1, column=1, padx=5, pady=5, sticky="we")

        self.time_label = ttk.Label(self.dialog, text="経過時間: 0秒")
        self.time_label.grid(row=2, column=1, padx=5, pady=5, sticky="we")

        self.close_button = ttk.Button(self.dialog, text="閉じる", command=self.close)
        self.close_button.grid(row=3, column=1, padx=5, pady=5)

        self.dialog.transient(parent)
        self.dialog.grab_set()

    def close(self):
        self.dialog.destroy()

    def update_pg(self, total, current, script_name, elapsed_time):
        self.progress_bar.configure(value=(current / total))
        self.label.configure(text=f"処理中: {script_name} ({current}/{total})")
        self.time_label.configure(text=f"経過時間: {elapsed_time:.2f}秒")
        self.dialog.update()


def main():
    root = tk.Tk()
    root.withdraw()  # メインウィンドウを非表示
    progress_dialog = ProgressDialog(root)

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
        'a1_app_open_ac.py',
    ]

    total_scripts = len(scripts)
    failed_scripts = set()
    start_time = time.time()

    for index, script in enumerate(scripts):
        script_path = os.path.join(current_path, script)
        if not os.path.exists(script_path):
            logging.warning(f"[警告] スクリプトが存在しません: {script_path}")
            continue

        print(f"実行中: {script}")
        try:
            result = subprocess.run([py_path, script_path], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            logging.info(f"[成功] スクリプトが正常に実行されました: {script}")
        except subprocess.CalledProcessError as e:
            if e.returncode != 3221225477:
                logging.error(f"[エラー] スクリプトが失敗しました: {script}, エラー: {e}, 出力: {e.output.decode()}, エラー出力: {e.stderr.decode()}")
                failed_scripts.add(script)

        elapsed_time = time.time() - start_time
        progress_dialog.update_pg(total_scripts, index + 1, script, elapsed_time)

        # mappingエラー時の処理
        if script == 'z090_zp138_field_mapping.py' and script in failed_scripts:
            root.deiconify()
            retry = messagebox.askyesno("エラー発生", "DBを閉じてください！再試行しますか？")
            root.withdraw()
            if retry and 'a1_app_open_ac.py' not in failed_scripts:
                failed_scripts.add('a1_app_open_ac.py')
            progress_dialog.dialog.deiconify()
            progress_dialog.dialog.update()

    if failed_scripts:
        for script in list(failed_scripts):
            script_path = os.path.join(current_path, script)
            try:
                result = subprocess.run([py_path, script_path], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                logging.info(f"[再実行成功] スクリプトが正常に実行されました: {script}")
                failed_scripts.remove(script)
            except subprocess.CalledProcessError as e:
                if e.returncode != 3221225477:
                    logging.error(f"[再実行エラー] スクリプトが失敗しました: {script}, エラー: {e}, 出力: {e.output.decode()}, エラー出力: {e.stderr.decode()}")

    logging.info("全スクリプトの処理が完了しました。")
    progress_dialog.label.configure(text="完了")
    progress_dialog.dialog.deiconify()
    progress_dialog.dialog.update()
    root.mainloop()

if __name__ == '__main__':
    main()
