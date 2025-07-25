import os
import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox

def export_excel_sheets_to_txt():
    excel_path = filedialog.askopenfilename(
        title="Excelファイルを選択してください",
        filetypes=[("Excel files", "*.xlsx *.xls")]
    )

    if not excel_path:
        return

    try:
        excel_data = pd.read_excel(excel_path, sheet_name=None, engine='openpyxl')
        output_dir = os.path.dirname(excel_path)

        for sheet_name, data in excel_data.items():
            txt_path = os.path.join(output_dir, f"{sheet_name}.txt")
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(data.to_string(index=False))

        messagebox.showinfo("完了", f"{len(excel_data)} シートを .txt ファイルとして保存しました。")
    except Exception as e:
        messagebox.showerror("エラー", f"処理中にエラーが発生しました:\n{str(e)}")

# GUIの作成
root = tk.Tk()
root.title("ExcelシートをTXTに変換")
root.geometry("400x150")

label = tk.Label(root, text="Excelファイルを選択して、各シートをTXTに保存します。", wraplength=380)
label.pack(pady=20)

button = tk.Button(root, text="Excelファイルを選択", command=export_excel_sheets_to_txt)
button.pack(pady=10)

root.mainloop()
