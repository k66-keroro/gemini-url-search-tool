"""
ランチャータブ - 外部スクリプトの実行管理
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import subprocess
import os
import json
from pathlib import Path
import tkinter.simpledialog

class LauncherTab:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.tab_frame = parent
        self.scripts_config = {}
        self.load_scripts_config()
        self.create_widgets()
    
    def create_widgets(self):
        """ランチャーインターフェースを作成"""
        # メインフレーム
        main_frame = ttk.Frame(self.tab_frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 設定フレーム
        config_frame = ttk.LabelFrame(main_frame, text="スクリプト設定")
        config_frame.pack(fill=tk.X, pady=(0, 10))
        
        # スクリプト追加ボタン
        ttk.Button(config_frame, text="スクリプト追加", 
                  command=self.add_script).pack(side=tk.LEFT, padx=5, pady=5)
        
        ttk.Button(config_frame, text="設定保存", 
                  command=self.save_scripts_config).pack(side=tk.LEFT, padx=5, pady=5)
        
        ttk.Button(config_frame, text="設定リロード", 
                  command=self.load_scripts_config).pack(side=tk.LEFT, padx=5, pady=5)
        
        # スクリプト一覧フレーム
        scripts_frame = ttk.LabelFrame(main_frame, text="登録済みスクリプト")
        scripts_frame.pack(fill=tk.BOTH, expand=True)
        
        # スクロール可能なフレーム
        canvas = tk.Canvas(scripts_frame)
        scrollbar = ttk.Scrollbar(scripts_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.refresh_script_buttons()
    
    def load_scripts_config(self):
        """スクリプト設定を読み込み"""
        config_file = Path("config/launcher_scripts.json")
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    self.scripts_config = json.load(f)
                self.log_message("スクリプト設定を読み込みました")
            except Exception as e:
                self.log_message(f"設定読み込みエラー: {e}")
                self.scripts_config = {}
        else:
            # デフォルト設定
            self.scripts_config = {
                "データ更新スクリプト": {
                    "path": "a_everyday/_00_アプリ起動_main.py",
                    "description": "毎日のデータ更新処理",
                    "category": "データ処理"
                },
                "Excel終了": {
                    "path": "a_everyday/z01_excel_close.py", 
                    "description": "Excelプロセスを終了",
                    "category": "ユーティリティ"
                },
                "ZP138処理": {
                    "path": "a_everyday/z090_zp138_integrated.py",
                    "description": "ZP138引当計算処理",
                    "category": "データ処理"
                },
                "PC生産実績ダッシュボード": {
                    "path": "run_dashboard.py",
                    "description": "StreamlitによるPC生産実績ダッシュボード",
                    "category": "ダッシュボード"
                }
            }
    
    def save_scripts_config(self):
        """スクリプト設定を保存"""
        config_file = Path("config/launcher_scripts.json")
        config_file.parent.mkdir(exist_ok=True)
        
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(self.scripts_config, f, ensure_ascii=False, indent=2)
            self.log_message("スクリプト設定を保存しました")
        except Exception as e:
            self.log_message(f"設定保存エラー: {e}")
    
    def add_script(self):
        """新しいスクリプトを追加"""
        file_path = filedialog.askopenfilename(
            title="スクリプトファイルを選択",
            filetypes=[("Python files", "*.py"), ("All files", "*.*")]
        )
        
        if file_path:
            # スクリプト名を入力
            script_name = tk.simpledialog.askstring(
                "スクリプト名", "スクリプト名を入力してください:"
            )
            
            if script_name:
                description = tk.simpledialog.askstring(
                    "説明", "スクリプトの説明を入力してください:"
                ) or ""
                
                self.scripts_config[script_name] = {
                    "path": file_path,
                    "description": description,
                    "category": "カスタム"
                }
                
                self.refresh_script_buttons()
                self.log_message(f"スクリプト '{script_name}' を追加しました")
    
    def refresh_script_buttons(self):
        """スクリプトボタンを更新"""
        # 既存のボタンを削除
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        # カテゴリ別にグループ化
        categories = {}
        for name, config in self.scripts_config.items():
            category = config.get("category", "その他")
            if category not in categories:
                categories[category] = []
            categories[category].append((name, config))
        
        # カテゴリ別にボタンを作成
        for category, scripts in categories.items():
            # カテゴリフレーム
            cat_frame = ttk.LabelFrame(self.scrollable_frame, text=category)
            cat_frame.pack(fill=tk.X, padx=5, pady=5)
            
            for script_name, config in scripts:
                self.create_script_button(cat_frame, script_name, config)
    
    def create_script_button(self, parent, script_name, config):
        """個別のスクリプトボタンを作成"""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, padx=5, pady=2)
        
        # 実行ボタン
        run_btn = ttk.Button(
            button_frame, 
            text=f"▶ {script_name}",
            command=lambda: self.run_script_threaded(script_name, config)
        )
        run_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # 説明ラベル
        desc_label = ttk.Label(
            button_frame, 
            text=config.get("description", ""),
            foreground="gray"
        )
        desc_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 削除ボタン
        del_btn = ttk.Button(
            button_frame,
            text="✕",
            width=3,
            command=lambda: self.remove_script(script_name)
        )
        del_btn.pack(side=tk.RIGHT)
    
    def run_script_threaded(self, script_name, config):
        """スクリプトをスレッドで実行"""
        thread = threading.Thread(
            target=self.run_script,
            args=(script_name, config),
            daemon=True
        )
        thread.start()
    
    def run_script(self, script_name, config):
        """スクリプトを実行"""
        script_path = Path(config["path"])
        
        if not script_path.exists():
            self.log_message(f"エラー: スクリプトが見つかりません: {script_path}")
            return
        
        try:
            self.log_message(f"実行開始: {script_name}")
            
            # 作業ディレクトリをスクリプトの場所に設定
            cwd = script_path.parent if script_path.is_absolute() else None
            
            # スクリプト実行
            result = subprocess.run(
                ["python", str(script_path)],
                capture_output=True,
                text=True,
                cwd=cwd,
                encoding='utf-8',
                errors='replace'
            )
            
            if result.returncode == 0:
                self.log_message(f"実行完了: {script_name}")
                if result.stdout:
                    self.log_message(f"出力: {result.stdout}")
            else:
                self.log_message(f"実行エラー: {script_name} (終了コード: {result.returncode})")
                if result.stderr:
                    self.log_message(f"エラー出力: {result.stderr}")
                    
        except Exception as e:
            self.log_message(f"実行例外: {script_name} - {e}")
    
    def log_message(self, message):
        """ログメッセージを表示（簡易版）"""
        print(f"[Launcher] {message}")  # 簡易実装
    
    def remove_script(self, script_name):
        """スクリプトを削除"""
        if messagebox.askyesno("確認", f"スクリプト '{script_name}' を削除しますか？"):
            del self.scripts_config[script_name]
            self.refresh_script_buttons()
            self.log_message(f"スクリプト '{script_name}' を削除しました")