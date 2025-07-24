"""
Kiro Clock - Kiroのリセット時間を表示する時計アプリ

Kiroが「リセットまで使えません」と表示される問題を解決するため、
リセット時間までのカウントダウンを表示します。
"""

import tkinter as tk
from tkinter import ttk
import datetime
import time
import threading


class KiroClock:
    def __init__(self, root):
        self.root = root
        self.root.title("Kiro Clock - リセット時間表示")
        self.root.geometry("400x300")
        self.root.configure(bg='#2b2b2b')
        
        # Kiroのリセット時間（仮定：毎日午前9時にリセット）
        # 実際のリセット時間に合わせて調整してください
        self.reset_hour = 9
        self.reset_minute = 0
        
        self.setup_ui()
        self.update_clock()
        
    def setup_ui(self):
        """UIの設定"""
        # メインフレーム
        main_frame = tk.Frame(self.root, bg='#2b2b2b')
        main_frame.pack(expand=True, fill='both', padx=20, pady=20)
        
        # タイトル
        title_label = tk.Label(
            main_frame, 
            text="🕐 Kiro Clock", 
            font=('Arial', 20, 'bold'),
            fg='#ffffff',
            bg='#2b2b2b'
        )
        title_label.pack(pady=(0, 20))
        
        # 現在時刻表示
        self.current_time_label = tk.Label(
            main_frame,
            text="",
            font=('Arial', 16),
            fg='#00ff00',
            bg='#2b2b2b'
        )
        self.current_time_label.pack(pady=10)
        
        # リセット時間表示
        reset_info_label = tk.Label(
            main_frame,
            text=f"Kiroリセット時間: 毎日 {self.reset_hour:02d}:{self.reset_minute:02d}",
            font=('Arial', 12),
            fg='#cccccc',
            bg='#2b2b2b'
        )
        reset_info_label.pack(pady=5)
        
        # 次回リセットまでの時間
        self.next_reset_label = tk.Label(
            main_frame,
            text="",
            font=('Arial', 14, 'bold'),
            fg='#ffff00',
            bg='#2b2b2b'
        )
        self.next_reset_label.pack(pady=15)
        
        # カウントダウン表示
        self.countdown_label = tk.Label(
            main_frame,
            text="",
            font=('Arial', 18, 'bold'),
            fg='#ff6600',
            bg='#2b2b2b'
        )
        self.countdown_label.pack(pady=10)
        
        # ステータス表示
        self.status_label = tk.Label(
            main_frame,
            text="",
            font=('Arial', 12),
            fg='#ffffff',
            bg='#2b2b2b'
        )
        self.status_label.pack(pady=10)
        
        # 設定ボタン
        settings_button = tk.Button(
            main_frame,
            text="リセット時間設定",
            command=self.open_settings,
            font=('Arial', 10),
            bg='#4a4a4a',
            fg='#ffffff',
            relief='flat',
            padx=20,
            pady=5
        )
        settings_button.pack(pady=10)
        
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
        
        if hours > 0:
            return f"{hours}時間 {minutes}分 {seconds}秒"
        elif minutes > 0:
            return f"{minutes}分 {seconds}秒"
        else:
            return f"{seconds}秒"
    
    def update_clock(self):
        """時計の更新"""
        now = datetime.datetime.now()
        next_reset = self.get_next_reset_time()
        time_until_reset = next_reset - now
        
        # 現在時刻を更新
        current_time_str = now.strftime("%Y年%m月%d日 %H:%M:%S")
        self.current_time_label.config(text=current_time_str)
        
        # 次回リセット時間を更新
        next_reset_str = next_reset.strftime("%m月%d日 %H:%M")
        self.next_reset_label.config(text=f"次回リセット: {next_reset_str}")
        
        # カウントダウンを更新
        countdown_str = self.format_time_delta(time_until_reset)
        self.countdown_label.config(text=f"⏰ あと {countdown_str}")
        
        # ステータスを更新
        if time_until_reset.total_seconds() < 3600:  # 1時間以内
            self.status_label.config(
                text="⚠️ まもなくリセットです！",
                fg='#ff0000'
            )
        elif time_until_reset.total_seconds() < 7200:  # 2時間以内
            self.status_label.config(
                text="🔔 リセットが近づいています",
                fg='#ffaa00'
            )
        else:
            self.status_label.config(
                text="✅ Kiro使用可能",
                fg='#00ff00'
            )
        
        # 1秒後に再更新
        self.root.after(1000, self.update_clock)
    
    def open_settings(self):
        """設定ウィンドウを開く"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("リセット時間設定")
        settings_window.geometry("300x200")
        settings_window.configure(bg='#2b2b2b')
        
        # 設定フレーム
        settings_frame = tk.Frame(settings_window, bg='#2b2b2b')
        settings_frame.pack(expand=True, fill='both', padx=20, pady=20)
        
        # 時間設定
        tk.Label(
            settings_frame,
            text="リセット時間設定",
            font=('Arial', 14, 'bold'),
            fg='#ffffff',
            bg='#2b2b2b'
        ).pack(pady=(0, 20))
        
        # 時間入力
        time_frame = tk.Frame(settings_frame, bg='#2b2b2b')
        time_frame.pack(pady=10)
        
        tk.Label(time_frame, text="時:", fg='#ffffff', bg='#2b2b2b').pack(side='left')
        hour_var = tk.StringVar(value=str(self.reset_hour))
        hour_spinbox = tk.Spinbox(
            time_frame, 
            from_=0, 
            to=23, 
            textvariable=hour_var,
            width=5
        )
        hour_spinbox.pack(side='left', padx=5)
        
        tk.Label(time_frame, text="分:", fg='#ffffff', bg='#2b2b2b').pack(side='left')
        minute_var = tk.StringVar(value=str(self.reset_minute))
        minute_spinbox = tk.Spinbox(
            time_frame, 
            from_=0, 
            to=59, 
            textvariable=minute_var,
            width=5
        )
        minute_spinbox.pack(side='left', padx=5)
        
        # 保存ボタン
        def save_settings():
            self.reset_hour = int(hour_var.get())
            self.reset_minute = int(minute_var.get())
            settings_window.destroy()
        
        save_button = tk.Button(
            settings_frame,
            text="保存",
            command=save_settings,
            font=('Arial', 12),
            bg='#4a4a4a',
            fg='#ffffff',
            relief='flat',
            padx=20,
            pady=5
        )
        save_button.pack(pady=20)


def main():
    """メイン関数"""
    root = tk.Tk()
    app = KiroClock(root)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("アプリケーションを終了します...")


if __name__ == "__main__":
    main()