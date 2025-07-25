import subprocess
import _03_chrome_open
import _04_edge_open
import _04_OUTLOOK_open
import os
from _99_database_config import py_path, current_path

# _01_sap_logoutファイルのディレクトリを設定
notebook_directory = r"C:\workspace\jypy_test\.a_everyday"

# スクリプトの実行前にディレクトリを変更
os.chdir(notebook_directory)

# メイン関数

# _02_access_postgreのプロセスを実行
process__02_access_postgre = subprocess.Popen(
    [py_path, current_path + '/_02_access_postgre.py'])
    #[r'C:/Users/sem3171/AppData/Local/Programs/Python/Python311/python.exe', 'C:/04_python/_main/_02_access_postgre.py'])
# _02_access_postgrelのプロセスが終了するまで待機
process__02_access_postgre.communicate()

# _03_chrome_open.py
def chrome_open():
    _03_chrome_open


if __name__ == "__main__":
    chrome_open()

# _04_edge_open.py
def edge_open():
    _04_edge_open


if __name__ == "__main__":
    edge_open()

# _04_OUTLOOK_open.py
def OUTLOOK_open():
    _04_OUTLOOK_open


if __name__ == "__main__":
    OUTLOOK_open()

# _01_sap_loginを実行
subprocess.run([py_path, current_path + r'\_01_sap_login.py'])
