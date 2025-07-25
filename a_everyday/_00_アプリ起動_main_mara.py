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

        self.dialog.protocol("WM_DELETE_WINDOW", self.close)  # 閉じるボタンの動作を設定

        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.update()

    def close(self):
        """ダイアログを閉じる"""
        try:
            self.dialog.destroy()  # Toplevelウィンドウを破棄
            self.parent.update_idletasks()  # 親ウィンドウを更新
        except Exception as e:
            logging.error(f"ProgressDialogを閉じる際にエラーが発生しました: {e}")

    def update_pg(self, total, current, script_name, elapsed_time):
        progress_value = min(current / total, 1.0) if total > 0 else 0
        self.progress_bar["value"] = int(progress_value * 100)
        self.label.configure(text=f"処理中: {script_name} ({current}/{total})")
        self.time_label.configure(text=f"経過時間: {elapsed_time:.2f}秒")
        self.dialog.update_idletasks()
        self.dialog.update()

def execute_script(script_path, progress_dialog, index, total_scripts, start_time):
    try:
        process = subprocess.run(
            [py_path, script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',  # エンコーディングを明示的に指定cp932
            errors='replace'   # エンコーディングエラーを回避
        )
        stdout = process.stdout
        stderr = process.stderr

        # ログに標準出力とエラー出力を記録
        if stdout:
            logging.info(f"[標準出力] {script_path}:\n{stdout}")
        if stderr:
            logging.error(f"[エラー出力] {script_path}:\n{stderr}")

        if process.returncode != 0:
            logging.warning(f"[警告] スクリプト {script_path} がエラーコード {process.returncode} で終了しましたが、続行します。")

        # z_Parsed Pc Master Diff Logger.py 実行後にファイル更新確認
        if "z_Parsed Pc Master Diff Logger.py" in script_path:
            log_file_path = os.path.abspath(os.path.join(current_path, "差分登録ログ.csv"))
            if os.path.exists(log_file_path):
                last_modified_time = os.path.getmtime(log_file_path)
                logging.info(f"[確認] 差分登録ログ.csv の最終更新日時: {datetime.fromtimestamp(last_modified_time)}")
            else:
                logging.error("[エラー] 差分登録ログ.csv が存在しません。")

        return True
    except Exception as e:
        logging.error(f"[例外] スクリプト実行中の例外: {script_path}, エラー: {e}")
        return False

def main():
    root = tk.Tk()
    
    scripts = [

        'z_maradl.py',
        'z_maradl2.py',
        'z_view_pcmaster.py',
        'z_Parsed Pc Master Diff Logger.py',
    ]
    total_scripts = len(scripts)
    start_time = time.time()
    overall_progress_dialog = ProgressDialog(root, title="全体の進捗", x_offset=100, y_offset=100)
    overall_progress_dialog.dialog.geometry("400x200")

    
    for index, script in enumerate(scripts):
        script_path = os.path.join(current_path, script)
        logging.debug(f"[デバッグ] チェック中のスクリプトパス: {script_path}")
        if not os.path.exists(script_path):
            logging.warning(f"[警告] スクリプトが存在しません: {script_path}")
            continue
    
        elapsed_time = time.time() - start_time
        overall_progress_dialog.update_pg(total_scripts, index, script, elapsed_time)
    
        script_progress_dialog = ProgressDialog(root, title=f"{script} の進捗", x_offset=200 + index * 40, y_offset=250 + index * 40)
        script_progress_dialog.update_pg(100, 0, script, elapsed_time)
    
        logging.info(f"[実行開始] {script}")
        execute_script(script_path, script_progress_dialog, index, total_scripts, start_time)
        logging.info(f"[実行終了] {script}")
    
        if script == 'z_view_pcmaster.py':
            logging.info("[待機] z_view_pcmaster.py 実行後に10秒待機")
            time.sleep(10)
        else:
            time.sleep(5)

    overall_progress_dialog.label.configure(text="完了")
    overall_progress_dialog.dialog.deiconify()
    overall_progress_dialog.dialog.update()
    
    final_script1 = os.path.join(current_path, '_01_sap_zm61_comp.py')
    if os.path.exists(final_script1):
        subprocess.run([py_path, final_script1], check=True)
    
    root.mainloop()

if __name__ == '__main__':
    main()

# ログ設定
logging.basicConfig(
    filename="main_execution_log.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"  # 日付と時間のフォーマットを指定
)

# z_Parsed Pc Master Diff Logger.py の実行
try:
    logging.info("z_Parsed Pc Master Diff Logger.py を実行します。")
    result = subprocess.run(
        ["python", "z_Parsed Pc Master Diff Logger.py"],
        capture_output=True,
        text=True
    )
    logging.info(f"実行結果: {result.stdout}")
    if result.stderr:
        logging.error(f"エラー出力: {result.stderr}")
except Exception as e:
    logging.error(f"スクリプト実行中にエラーが発生しました: {e}")
