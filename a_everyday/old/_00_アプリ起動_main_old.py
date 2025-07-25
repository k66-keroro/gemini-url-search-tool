import os
import subprocess

import a1_app_open_a
import a1_app_open_ac
import a1_app_open_edge
from _99_database_config import current_path, py_path
import z900_database_config


# _01_sap_logoutファイルのディレクトリを設定
notebook_directory = r"C:\t_20_python\a_everyday"

# スクリプトの実行前にディレクトリを変更
os.chdir(notebook_directory)


# 並行して実行するスクリプト# 各関数を順次呼び出してアプリを開く
processes = [
subprocess.run([py_path, current_path + r'\a1_app_open_a.py']),
subprocess.run([py_path, current_path + r'\a1_app_open_ac.py']),
subprocess.run([py_path, current_path + r'\a1_app_open_edge.py'])
]

# 全てのプロセスが終了するのを待つ
for process in processes:
    process.wait()
import a001_runpy
# 最後に実行
import _01_sap_zm61_comp