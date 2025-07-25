import tkinter as tk
from tkinter import messagebox

def calculate_square():
    try:
        number = float(entry.get())
        square = number ** 2
        messagebox.showinfo("結果", f"{number}の平方: {square}")
    except ValueError:
        messagebox.showerror("エラー", "数値を入力してください。")

root = tk.Tk()
root.title("平方計算機")

entry = tk.Entry(root)
entry.pack(pady=10)

button = tk.Button(root, text="計算", command=calculate_square)
button.pack(pady=5)

root.mainloop()
