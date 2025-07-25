# database_config.py

# PostgreSQLへの接続情報
pg_host = 'PC4843W'
pg_database = 'sekkeidb'
pg_user = 'sakai'
pg_password = 'sakai'
pg_port = 5432

# Accessへの接続情報
access_db_file = r'C:\Projects_workspace\02_access\Database1.accdb'
access_db_file1 = r'C:\03_Python\py_1.accdb'
access_driver = '{Microsoft Access Driver (*.mdb, *.accdb)}'

#path
py_path = r"C:\workspace\jypy_test\Scripts\python.exe"
current_path = r"C:\t_20_python\a_everyday"


from tkinter import Tk, messagebox


def MessageForefront(MesAlarm):
    root = Tk()
    root.attributes('-topmost', True)
    root.withdraw()
    ret = messagebox.askyesno('確認', MesAlarm)
    return ret

def MessageForefrontShowinfo(MesAlarmShowinfo):
    root = Tk()
    root.attributes('-topmost', True)
    root.withdraw()
    messagebox.showinfo('確認', MesAlarmShowinfo)



#from MesAlarmBox import MessageForefront, MessageForefrontShowinfo


#ret = MessageForefront('Twitter投稿を開始しますか？')
#if ret == True:
#　　......
#     ......
#     ......
#MessageForefrontShowinfo('job実行を終了します。')