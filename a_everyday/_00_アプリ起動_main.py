import os
import subprocess
import logging
import time
import tkinter as tk
from tkinter import ttk
from _99_database_config import current_path, py_path
from datetime import datetime
import threading
from pathlib import Path

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

        self.dialog.protocol("WM_DELETE_WINDOW", self.close)

        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.update()

    def close(self):
        """ダイアログを閉じる"""
        try:
            self.dialog.destroy()
            self.parent.update_idletasks()
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
        # 絶対パスに変換
        script_path = Path(script_path).absolute()
        script_dir = script_path.parent
        
        # 環境変数を設定
        env = os.environ.copy()
        env['PYTHONPATH'] = str(script_dir)
        
        logging.info(f"[実行開始] {script_path.name} (作業ディレクトリ: {script_dir})")
        
        process = subprocess.run(
            [py_path, str(script_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            errors='replace',
            cwd=str(script_dir),  # 作業ディレクトリを明示的に指定
            env=env  # 環境変数を設定
        )
        
        stdout = process.stdout
        stderr = process.stderr

        # ログに記録
        if stdout:
            logging.info(f"[標準出力] {script_path.name}:\n{stdout}")
        if stderr:
            logging.error(f"[エラー出力] {script_path.name}:\n{stderr}")

        if process.returncode != 0:
            logging.warning(f"[警告] スクリプト {script_path.name} がエラーコード {process.returncode} で終了しましたが、続行します。")

        # z_Parsed Pc Master Diff Logger.py 実行後の確認
        if script_path.name == "z_Parsed Pc Master Diff Logger.py":
            log_file_path = script_dir / "a_everyday" / "差分登録ログ.csv"
            logging.info(f"[確認] CSV確認パス: {log_file_path}")
            
            if log_file_path.exists():
                last_modified_time = log_file_path.stat().st_mtime
                last_modified_dt = datetime.fromtimestamp(last_modified_time)
                file_size = log_file_path.stat().st_size
                logging.info(f"[確認] 差分登録ログ.csv 更新確認:")
                logging.info(f"  - 最終更新日時: {last_modified_dt}")
                logging.info(f"  - ファイルサイズ: {file_size} bytes")
                
                # 更新時刻が実行開始時刻より新しいかチェック
                if last_modified_time > start_time:
                    logging.info("  - ✅ ファイルが正常に更新されました")
                else:
                    logging.warning("  - ⚠️ ファイルが更新されていない可能性があります")
            else:
                logging.error(f"[エラー] 差分登録ログ.csv が存在しません: {log_file_path}")

        return True
    except Exception as e:
        logging.error(f"[例外] スクリプト実行中の例外: {script_path}, エラー: {e}")
        return False

def main():
    root = tk.Tk()
    
    scripts = [
        'z01_excel_close.py',
        'a1_app_open_edge.py',
        'a1_app_open_a.py',
        'z900_filecopy_txt.py',
        'z090_zp138_integrated.py',
        'zm87.py',
        'zp02.py',
        'zt_zm87_code.py',
        'zs65.py',
        'zs61_all.py',
        'zs58.py',
        'zm29.py',
        'zp70.py',
        'ZP51.py',
        'ZP58.py',
        'z_maradl.py',
        'z_maradl2.py',
        'z_view_pcmaster.py',
        'z_Parsed Pc Master Diff Logger.py',
        'z_Compact_Database1.py',
        'a1_app_open_ac.py',
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

        execute_script(script_path, script_progress_dialog, index, total_scripts, start_time)

        if script == 'z_view_pcmaster.py':
            logging.info("[待機] z_view_pcmaster.py 実行後に10秒待機")
            time.sleep(10)
        else:
            time.sleep(5)

    overall_progress_dialog.label.configure(text="完了")
    overall_progress_dialog.dialog.deiconify()
    overall_progress_dialog.dialog.update()

    # 最終スクリプト実行
    final_script1 = os.path.join(current_path, '_01_sap_zm61_comp.py')
    if os.path.exists(final_script1):
        subprocess.run([py_path, final_script1], check=True)

    root.mainloop()

if __name__ == '__main__':
    # ログ設定（重複削除）
    logging.basicConfig(
        filename="main_execution_log.log",
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    logging.info("=== メインアプリケーション開始 ===")
    main()
    logging.info("=== メインアプリケーション終了 ===")

# 🚨 重複実行部分を削除！
# 以下のコードは削除されました（重複実行の原因）
# try:
#     logging.info("z_Parsed Pc Master Diff Logger.py を実行します。")
#     result = subprocess.run(...)
# except Exception as e:
#     logging.error(f"スクリプト実行中にエラーが発生しました: {e}")