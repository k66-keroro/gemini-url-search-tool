"""
database_config.py
"""

# path
from tkinter import Tk, messagebox
#py_path = r"C:\t_20_python\t_20_venv2\Scripts\python.exe"
py_path = r"C:\Users\sem3171\AppData\Local\Programs\Python\Python311\python.exe"
current_path = r"C:\t_20_python\a_everyday"


# PostgreSQLへの接続情報
pg_host = "PC4843W"
pg_database = "sekkeidb"
pg_user = "sakai"
pg_password = "sakai"

# Accessへの接続情報
access_db_file = r"C:\04_python\pc_456_bom.accdb"
access_db_file1 = r"C:\03_Python\py_1.accdb"
access_driver = "{Microsoft Access Driver (*.mdb, *.accdb)}"


def MessageForefront(MesAlarm):
    root = Tk()
    root.attributes("-topmost", True)
    root.withdraw()
    ret = messagebox.askyesno("確認", MesAlarm)
    return ret


def MessageForefrontShowinfo(MesAlarmShowinfo):
    root = Tk()
    root.attributes("-topmost", True)
    root.withdraw()
    messagebox.showinfo("確認", MesAlarmShowinfo)


# from MesAlarmBox import MessageForefront, MessageForefrontShowinfo


# ret = MessageForefront('Twitter投稿を開始しますか？')
# if ret == True:
# ......
#     ......
#     ......
# MessageForefrontShowinfo('job実行を終了します。')
