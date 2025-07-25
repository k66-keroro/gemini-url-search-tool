import time
import tkinter as tk
from tkinter import ttk

class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master.geometry('420x160')
        self.master.title('sample')
        self.master.grid_rowconfigure((0, 1, 2), weight=1)
        self.master.grid_columnconfigure((0, 1), weight=1)

        self.label_1 = ttk.Label(self.master, text='')
        self.label_2 = ttk.Label(self.master, text='')
        self.progbar1 = ttk.Progressbar(self.master, length=400, mode="determinate", maximum=1)
        self.progbar2 = ttk.Progressbar(self.master, length=400, mode="determinate", maximum=1)
        self.button1 = ttk.Button(self.master, text='実行', width=20, command=self.loop_function)
        self.button2 = ttk.Button(self.master, text='リセット', width=20, command=self.reset_bar)
        self.label_1.grid(row=0, column=0, padx=10, pady=10)
        self.label_2.grid(row=0, column=1, padx=10, pady=10)
        self.progbar1.grid(row=1, column=0, columnspan=2, padx=10, pady=(0, 5))
        self.progbar2.grid(row=2, column=0, columnspan=2, padx=10, pady=(0, 10))
        self.button1.grid(row=3, column=0, padx=10, pady=(0, 10))
        self.button2.grid(row=3, column=1, padx=10, pady=(0, 20))

        # ループ処理をまわすリスト
        self.prog_list1 = list('abcdefghijklmnopqrstuvwxyz')
        self.prog_list2 = list('あいうえお')

    # ループ処理
    def loop_function(self):
        # ループ処理
        for i, item2 in enumerate(self.prog_list2):
            for j, item1 in enumerate(self.prog_list1):
                time.sleep(0.15)
                # ラベル表示変更
                self.label_1.configure(text=f'{item2}-{item1}')
                self.label_2.configure(text=f'{j+1}/{len(self.prog_list1)}')
                # プログレスバー表示変更
                self.progbar1.configure(value=(j+1)/len(self.prog_list1))
                self.progbar1.update()
            # プログレスバー表示変更
            self.progbar2.configure(value=(i+1)/len(self.prog_list2))
            self.progbar2.update()

    # リセット処理
    def reset_bar(self):
        # ラベル表示リセット
        self.label_1.configure(text='')
        self.label_2.configure(text='')
        # プログレスバー表示リセット
        self.progbar1.configure(value=0)
        self.progbar1.update()
        self.progbar2.configure(value=0)
        self.progbar2.update()


if __name__ == "__main__":
    root = tk.Tk()
    app = Application(master = root)
    app.mainloop()

