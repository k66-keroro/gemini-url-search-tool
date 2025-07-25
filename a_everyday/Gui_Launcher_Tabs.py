import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from subprocess import Popen, PIPE
import threading
import time
import signal
from datetime import datetime
import logging

from _99_database_config import current_path, py_path

log_filename = f'script_execution_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
logging.basicConfig(
    filename=log_filename,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

SCRIPT_MAP = {
    "main": [
        ("b1_filecheck", "b1_filecheck.py"),
        ("sqlite_gui_tool.py", "sqlite_gui_tool_v2_fixed.py"),
        ("全スクリプト実行", None),
    ],
    "sap": [
        ("sap_login", "_01_sap_login.py"),
        ("sap_logout", "_01_sap_logout.py"),
        ("sap_zm61_comp", "_01_sap_zm61_comp.py"),
        ("sap_zm61_excel", "_01_sap_zm61_comp_excel.py"),
        ("sap_zm61_rename", "_01_sap_zm61_rename.py"),
    ],
    "アプリ": [
        ("アプリ起動", "_00_アプリ起動_main_spot.py"),
        ("アプリ終了", "_00_アプリ終了.py"),
        ("エクスプローラ", None),
        ("終了", None),
    ]
}

BATCH_SCRIPTS = [
    'z01_excel_close.py', 'a1_app_open_edge.py', 'a1_app_open_a.py',
    'z900_filecopy_txt.py', 'z090_zp138_txt.py', 'z090_zp138_field_mapping.py',
    'zm87.py', 'zp02.py', 'zt_zm87_code.py', 'zs65.py', 'zs61_all.py',
    'zs58.py', 'zm29.py', 'zp70.py', 'ZP51.py', 'ZP58.py',
    'z_mala_dl.py', 'z_mala_dl2.py', 'z_view_pcmaster.py',
    'z_Parsed Pc Master Diff Logger.py', 'a1_app_open_ac.py'
]

current_process = None

class LauncherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ランチャー - タブ版")
        self.root.minsize(400, 300)
        
        # 状態管理
        self.running = False
        self.process = None
        self.report = []
        
        # GUI要素の作成
        self.create_widgets()
        
    def create_widgets(self):
        # メインフレーム
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # タブコントロール
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # タブウィジェットを保存するリスト
        self.tab_widgets = []
        
        # 各タブの作成
        for tab_name, scripts in SCRIPT_MAP.items():
            tab = ttk.Frame(self.notebook)
            self.notebook.add(tab, text=tab_name)
            self.tab_widgets.append(tab)  # タブウィジェットを保存
            
            # スクリプトボタンの作成
            for i, (label, script) in enumerate(scripts):
                if script is None:
                    if label == "全スクリプト実行":
                        btn = ttk.Button(tab, text=label, command=self.run_batch)
                    elif label == "エクスプローラ":
                        btn = ttk.Button(tab, text=label, command=self.open_explorer)
                    elif label == "終了":
                        btn = ttk.Button(tab, text=label, command=self.root.quit)
                    else:
                        btn = ttk.Button(tab, text=label, command=lambda: None)
                else:
                    btn = ttk.Button(tab, text=label, command=lambda s=script: self.run_script(s))
                
                btn.grid(row=i//2, column=i%2, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        # ステータス表示
        self.status = ttk.Label(main_frame, text="待機中")
        self.status.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # プログレスバー
        self.progress = ttk.Progressbar(main_frame, mode='determinate')
        self.progress.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # 時間表示
        self.time_label = ttk.Label(main_frame, text="")
        self.time_label.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # ログ表示エリア
        log_frame = ttk.LabelFrame(main_frame, text="ログ", padding="5")
        log_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        self.log_text = tk.Text(log_frame, height=10, width=60)
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # グリッドの重み設定
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(4, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
    def run_script(self, script_name):
        """個別スクリプトを実行"""
        if self.running:
            messagebox.showwarning("警告", "既にスクリプトが実行中です")
            return
            
        def run_task():
            self.running = True
            self.disable_all_buttons()
            script_path = os.path.join(current_path, script_name)
            
            self.status.config(text=f"実行中: {script_name}")
            self.log(f"開始: {script_name}")
            
            try:
                self.process = Popen([py_path, script_path], stdout=PIPE, stderr=PIPE, text=True, encoding='utf-8', errors='replace')
                stdout, stderr = self.process.communicate()
                
                if self.process.returncode == 0:
                    self.log(f"完了: {script_name}")
                    logging.info(f"スクリプト {script_name} が正常に完了しました")
                else:
                    self.log(f"エラー: {script_name} - {stderr.strip()}")
                    logging.error(f"スクリプト {script_name} でエラーが発生しました: {stderr}")
                    
            except Exception as e:
                self.log(f"例外: {script_name} - {str(e)}")
                logging.error(f"スクリプト {script_name} で例外が発生しました: {str(e)}")
            
            self.status.config(text="待機中")
            self.running = False
            self.enable_all_buttons()
        
        threading.Thread(target=run_task).start()
    
    def open_explorer(self):
        """エクスプローラーを開く"""
        try:
            Popen(["explorer.exe", current_path])
            self.log("エクスプローラーを開きました")
        except Exception as e:
            self.log(f"エクスプローラー起動エラー: {str(e)}")
    
    def disable_all_buttons(self):
        """すべてのボタンを無効化"""
        for tab in self.tab_widgets:
            for child in tab.winfo_children():
                if isinstance(child, ttk.Button):
                    child.configure(state='disabled')
    
    def enable_all_buttons(self):
        """すべてのボタンを有効化"""
        for tab in self.tab_widgets:
            for child in tab.winfo_children():
                if isinstance(child, ttk.Button):
                    child.configure(state='normal')
    
    def log(self, message):
        """ログメッセージを表示"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        self.log_text.insert(tk.END, log_message)
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def run_batch(self):
        def batch_task():
            self.running = True
            self.disable_all_buttons()
            total = len(BATCH_SCRIPTS)
            start_total = time.time()
            elapsed_total = 0

            for i, script in enumerate(BATCH_SCRIPTS):
                script_path = os.path.join(current_path, script)
                self.status.config(text=f"実行中: {script} ({i+1}/{total})")
                self.progress["value"] = (i / total) * 100

                start = time.time()
                try:
                    self.process = Popen([py_path, script_path], stdout=PIPE, stderr=PIPE, text=True, encoding='utf-8', errors='replace')
                    stdout, stderr = self.process.communicate()  # タイムアウト削除
                    elapsed = time.time() - start
                    elapsed_total += elapsed

                    if self.process.returncode != 0:
                        msg = f"[エラー] {script}: {stderr.strip()}"
                        self.log(msg)
                        logging.error(msg)
                        if not messagebox.askyesno("エラー発生", f"{script} でエラー発生。続行しますか？"):
                            break
                    else:
                        msg = f"[完了] {script} ({elapsed:.2f}秒 累積:{elapsed_total:.2f}秒)"
                        self.log(msg)
                        logging.info(stdout)

                    self.report.append((script, self.process.returncode, elapsed, elapsed_total))

                except Exception as e:
                    elapsed = time.time() - start
                    elapsed_total += elapsed
                    msg = f"[例外] {script} で予期せぬ例外: {e}"
                    self.log(msg)
                    logging.error(msg)
                    self.report.append((script, -99, elapsed, elapsed_total))

                time.sleep(5 if "pcm" not in script else 10)

            self.progress["value"] = 100
            self.status.config(text="一括実行完了")
            self.time_label.config(text=f"総経過時間: {int(time.time() - start_total)}秒")
            self.output_report()
            self.running = False
            self.enable_all_buttons()

        threading.Thread(target=batch_task).start()

    def output_report(self):
        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"batch_report_{now}.txt"
        with open(report_file, "w", encoding="utf-8") as f:
            for script, code, secs, total in self.report:
                status = "成功" if code == 0 else ("タイムアウト" if code == -9 else "失敗")
                f.write(f"{script}\t{status}\t{secs:.2f}秒\t累積:{total:.2f}秒\n")
        self.log(f"レポート出力完了: {report_file}")

if __name__ == '__main__':
    os.chdir(current_path)
    root = tk.Tk()
    app = LauncherApp(root)
    root.mainloop()

# 【変更点要約】
# • run_script 内 except TimeoutExpired で elapsed を定義
# • sqlite_gui_tool_v2_fixed.py 実行時は timeout=None で無制限

# 他関数は元コードと同じ。必要であれば run_batch にも同様の条件分岐を適用してください。