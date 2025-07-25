import os
import subprocess

import a1_app_open_a
import a1_app_open_ac
import a1_app_open_edge
from _99_database_config import current_path, py_path

# _01_sap_logoutファイルのディレクトリを設定
notebook_directory = r"C:\t_20_python\a_everyday"

# スクリプトの実行前にディレクトリを変更
os.chdir(notebook_directory)

# 各関数を順次呼び出してアプリを開く
subprocess.run([py_path, current_path + r'\a1_app_open_a.py'])
subprocess.run([py_path, current_path + r'\a1_app_open_ac.py'])
subprocess.run([py_path, current_path + r'\a1_app_open_edge.py'])
subprocess.run([py_path, current_path + r'\_01_sap_login.py'])


