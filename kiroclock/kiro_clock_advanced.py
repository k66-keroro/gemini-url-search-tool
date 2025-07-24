"""
Kiro Clock Advanced - 設定永続化対応版

Kiroのリセット時間を表示する時計アプリ（設定保存機能付き）
"""

import tkinter as tk
from tkinter import ttk, messagebox
import datetime
import json
import os
from pathlib import Path


class KiroClockAdvanced:
    def __init__(self, root):
        self.root = root
        self.root.title("Kiro Clock Advanced - リセット時間表示")
        self.root.geometry("450x350")
        self.root.configure(bg='#2b2b2b')
        
        # 設定ファイルのパス
        self.config_file = Path("kiroclock_config.json")
        
        # デフォルト設定
        self.default_config = {
            "reset_hour": 9,
            "reset_minute": 0,
            "theme": "dark",
            "always_on_top": False,
            "show_seconds": True
        }
        
        # 設定を読み込み
        self.load_config()
        
        self.setup_ui()
        self.update_clock()
        
    def load_config(self):
        """設定ファイルから設定を読み込み"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    
                self.reset_hour = config.get("reset_hour", self.default_config["reset_hour"])
                self.reset_minute = config.get("reset_minute", self.default_config["reset_minute"])
                self.theme = config.get("theme", self.default_config["theme"])
                self.always_on_top = config.get("always_on_top", self.default_config["always_on_top"])
                self.show_seconds = config.get("show_seconds", self.default_config["show_seconds"])
            else:
                # デフォルト設定を使用
                self.reset_hour = self.default_config["reset_hour"]
                self.reset_minute = self.default_config["reset_minute"]
                self.theme = self.default_config["theme"]
                self.always_on_top = self.default_config["always_on_top"]
                self.show_seconds = self.default_config["show_seconds"]
                
        except Exception as e:
            print(f"設定読み込みエラー: {e}")
            # エラー時はデフォルト設定を使用
            self.reset_hour = self.default_config["reset_hour"]
            self.reset_minute = self.default_config["reset_minute"]
            self.theme = self.default_config["theme"]
            self.always_on_top = self.default_config["always_on_top"]
            self.show_seconds = self.default_config["show_seconds"]
    
    def save_config(self):
        """設定をファイルに保存"""
        try:
            config = {
                "reset_hour": self.reset_hour,
                "reset_minute": self.reset_minute,
                "theme": self.theme,
                "always_on_top": self.always_on_top,
                "show_seconds": self.show_seconds
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"設定保存エラー: {e}")
            messagebox.showerror("エラー", f"設定の保存に失敗しました: {e}")
    
    def get_theme_colors(self):
        """テーマに応じた色を取得"""
        if self.theme == "light":
            return {
                "bg": "#ffffff",
                "fg": "#000000",
                "accent": "#0066cc",
                "warning": "#ff6600",
                "error": "#cc0000",
                "success": "#00aa00"
            }
        else:  # dark theme
            return {
                "bg": "#2b2b2b",
                "fg": "#ffffff",
                "accent": "#00ff00",
                "warning": "#ffaa00",
                "error": "#ff0000",
                "success": "#00ff00"
            }
    
    def setup_ui(self):
        """UIの設定"""
        colors = self.get_theme_colors()
        
        # 常に最前面表示の設定
        if self.always_on_top:
            self.root.attributes('-topmost', True)
        
        # メインフレーム
        main_frame = tk.Frame(self.root, bg=colors["bg"])
        main_frame.pack(expand=True, fill='both', padx=20, pady=20)
        
        # タイトル
        title_label = tk.Label(
            main_frame, 
            text="🕐 Kiro Clock Advanced", 
            font=('Arial', 18, 'bold'),
            fg=colors["fg"],
            bg=colors["bg"]
        )
        title_label.pack(pady=(0, 15))
        
        # 現在時刻表示
        self.current_time_label = tk.Label(
            main_frame,
            text="",
            font=('Arial', 14),
            fg=colors["accent"],
            bg=colors["bg"]
        )
        self.current_time_label.pack(pady=8)
        
        # リセット時間表示
        self.reset_info_label = tk.Label(
            main_frame,
            text="",
            font=('Arial', 11),
            fg=colors["fg"],
            bg=colors["bg"]
        )
        self.reset_info_label.pack(pady=5)
        
        # 次回リセットまでの時間
        self.next_reset_label = tk.Label(
            main_frame,
            text="",
            font=('Arial', 12, 'bold'),
            fg=colors["warning"],
            bg=colors["bg"]
        )
        self.next_reset_label.pack(pady=12)
        
        # カウントダウン表示
        self.countdown_label = tk.Label(
            main_frame,
            text="",
            font=('Arial', 16, 'bold'),
            fg=colors["warning"],
            bg=colors["bg"]
        )
        self.countdown_label.pack(pady=8)
        
        # ステータス表示
        self.status_label = tk.Label(
            main_frame,
            text="",
            font=('Arial', 11),
            fg=colors["fg"],
            bg=colors["bg"]
        )
        self.status_label.pack(pady=8)
        
        # ボタンフレーム
        button_frame = tk.Frame(main_frame, bg=colors["bg"])
        button_frame.pack(pady=15)
        
        # 設定ボタン
        settings_button = tk.Button(
            button_frame,
            text="⚙️ 設定",
            command=self.open_settings,
            font=('Arial', 10),
            bg='#4a4a4a',
            fg='#ffffff',
            relief='flat',
            padx=15,
            pady=5
        )
        settings_button.pack(side='left', padx=5)
        
        # 最前面表示切り替えボタン
        topmost_text = "📌 最前面ON" if not self.always_on_top else "📌 最前面OFF"
        self.topmost_button = tk.Button(
            button_frame,
            text=topmost_text,
            command=self.toggle_topmost,
            font=('Arial', 10),
            bg='#4a4a4a',
            fg='#ffffff',
            relief='flat',
            padx=15,
            pady=5
        )
        self.topmost_button.pack(side='left', padx=5)
        
        # テーマ切り替えボタン
        theme_text = "🌙 ダーク" if self.theme == "light" else "☀️ ライト"
        self.theme_button = tk.Button(
            button_frame,
            text=theme_text,
            command=self.toggle_theme,
            font=('Arial', 10),
            bg='#4a4a4a',
            fg='#ffffff',
            relief='flat',
            padx=15,
            pady=5
        )
        self.theme_button.pack(side='left', padx=5)
        
        # 初期表示を更新
        self.update_reset_info()
    
    def update_reset_info(self):
        """リセット時間情報を更新"""
        reset_time_str = f"毎日 {self.reset_hour:02d}:{self.reset_minute:02d}"
        self.reset_info_label.config(text=f"Kiroリセット時間: {reset_time_str}")
    
    def get_next_reset_time(self):
        """次回のリセット時間を取得"""
        now = datetime.datetime.now()
        
        # 今日のリセット時間
        today_reset = now.replace(
            hour=self.reset_hour, 
            minute=self.reset_minute, 
            second=0, 
            microsecond=0
        )
        
        # 今日のリセット時間がまだ来ていない場合
        if now < today_reset:
            return today_reset
        else:
            # 明日のリセット時間
            tomorrow_reset = today_reset + datetime.timedelta(days=1)
            return tomorrow_reset
    
    def format_time_delta(self, delta):
        """時間差を読みやすい形式でフォーマット"""
        total_seconds = int(delta.total_seconds())
        
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        if self.show_seconds:
            if hours > 0:
                return f"{hours}時間 {minutes}分 {seconds}秒"
            elif minutes > 0:
                return f"{minutes}分 {seconds}秒"
            else:
                return f"{seconds}秒"
        else:
            if hours > 0:
                return f"{hours}時間 {minutes}分"
            else:
                return f"{minutes}分"
    
    def update_clock(self):
        """時計の更新"""
        colors = self.get_theme_colors()
        now = datetime.datetime.now()
        next_reset = self.get_next_reset_time()
        time_until_reset = next_reset - now
        
        # 現在時刻を更新
        if self.show_seconds:
            current_time_str = now.strftime("%Y年%m月%d日 %H:%M:%S")
        else:
            current_time_str = now.strftime("%Y年%m月%d日 %H:%M")
        self.current_time_label.config(text=current_time_str)
        
        # 次回リセット時間を更新
        if next_reset.date() == now.date():
            next_reset_str = f"今日 {next_reset.strftime('%H:%M')}"
        else:
            next_reset_str = next_reset.strftime("%m月%d日 %H:%M")
        self.next_reset_label.config(text=f"次回リセット: {next_reset_str}")
        
        # カウントダウンを更新
        countdown_str = self.format_time_delta(time_until_reset)
        self.countdown_label.config(text=f"⏰ あと {countdown_str}")
        
        # ステータスを更新
        if time_until_reset.total_seconds() < 3600:  # 1時間以内
            self.status_label.config(
                text="⚠️ まもなくリセットです！",
                fg=colors["error"]
            )
        elif time_until_reset.total_seconds() < 7200:  # 2時間以内
            self.status_label.config(
                text="🔔 リセットが近づいています",
                fg=colors["warning"]
            )
        else:
            self.status_label.config(
                text="✅ Kiro使用可能",
                fg=colors["success"]
            )
        
        # 1秒後に再更新
        self.root.after(1000, self.update_clock)
    
    def toggle_topmost(self):
        """最前面表示の切り替え"""
        self.always_on_top = not self.always_on_top
        self.root.attributes('-topmost', self.always_on_top)
        
        topmost_text = "📌 最前面OFF" if self.always_on_top else "📌 最前面ON"
        self.topmost_button.config(text=topmost_text)
        
        self.save_config()
    
    def toggle_theme(self):
        """テーマの切り替え"""
        self.theme = "light" if self.theme == "dark" else "dark"
        self.save_config()
        
        # UIを再構築
        for widget in self.root.winfo_children():
            widget.destroy()
        self.setup_ui()
    
    def open_settings(self):
        """設定ウィンドウを開く"""
        colors = self.get_theme_colors()
        
        settings_window = tk.Toplevel(self.root)
        settings_window.title("設定")
        settings_window.geometry("350x300")
        settings_window.configure(bg=colors["bg"])
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        # 設定フレーム
        settings_frame = tk.Frame(settings_window, bg=colors["bg"])
        settings_frame.pack(expand=True, fill='both', padx=20, pady=20)
        
        # タイトル
        tk.Label(
            settings_frame,
            text="⚙️ 設定",
            font=('Arial', 16, 'bold'),
            fg=colors["fg"],
            bg=colors["bg"]
        ).pack(pady=(0, 20))
        
        # リセット時間設定
        time_frame = tk.LabelFrame(
            settings_frame, 
            text="リセット時間", 
            fg=colors["fg"], 
            bg=colors["bg"],
            font=('Arial', 12)
        )
        time_frame.pack(fill='x', pady=10)
        
        time_input_frame = tk.Frame(time_frame, bg=colors["bg"])
        time_input_frame.pack(pady=10)
        
        tk.Label(time_input_frame, text="時:", fg=colors["fg"], bg=colors["bg"]).pack(side='left')
        hour_var = tk.StringVar(value=str(self.reset_hour))
        hour_spinbox = tk.Spinbox(
            time_input_frame, 
            from_=0, 
            to=23, 
            textvariable=hour_var,
            width=5
        )
        hour_spinbox.pack(side='left', padx=5)
        
        tk.Label(time_input_frame, text="分:", fg=colors["fg"], bg=colors["bg"]).pack(side='left')
        minute_var = tk.StringVar(value=str(self.reset_minute))
        minute_spinbox = tk.Spinbox(
            time_input_frame, 
            from_=0, 
            to=59, 
            textvariable=minute_var,
            width=5
        )
        minute_spinbox.pack(side='left', padx=5)
        
        # 表示設定
        display_frame = tk.LabelFrame(
            settings_frame, 
            text="表示設定", 
            fg=colors["fg"], 
            bg=colors["bg"],
            font=('Arial', 12)
        )
        display_frame.pack(fill='x', pady=10)
        
        # 秒表示設定
        seconds_var = tk.BooleanVar(value=self.show_seconds)
        seconds_check = tk.Checkbutton(
            display_frame,
            text="秒を表示する",
            variable=seconds_var,
            fg=colors["fg"],
            bg=colors["bg"],
            selectcolor=colors["bg"]
        )
        seconds_check.pack(anchor='w', padx=10, pady=5)
        
        # ボタンフレーム
        button_frame = tk.Frame(settings_frame, bg=colors["bg"])
        button_frame.pack(pady=20)
        
        # 保存ボタン
        def save_settings():
            try:
                self.reset_hour = int(hour_var.get())
                self.reset_minute = int(minute_var.get())
                self.show_seconds = seconds_var.get()
                
                self.save_config()
                self.update_reset_info()
                
                messagebox.showinfo("設定保存", "設定を保存しました。")
                settings_window.destroy()
                
            except ValueError:
                messagebox.showerror("エラー", "時間の値が正しくありません。")
        
        save_button = tk.Button(
            button_frame,
            text="💾 保存",
            command=save_settings,
            font=('Arial', 12),
            bg='#4a4a4a',
            fg='#ffffff',
            relief='flat',
            padx=20,
            pady=8
        )
        save_button.pack(side='left', padx=5)
        
        # キャンセルボタン
        cancel_button = tk.Button(
            button_frame,
            text="❌ キャンセル",
            command=settings_window.destroy,
            font=('Arial', 12),
            bg='#666666',
            fg='#ffffff',
            relief='flat',
            padx=20,
            pady=8
        )
        cancel_button.pack(side='left', padx=5)


def main():
    """メイン関数"""
    root = tk.Tk()
    app = KiroClockAdvanced(root)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("アプリケーションを終了します...")


if __name__ == "__main__":
    main()