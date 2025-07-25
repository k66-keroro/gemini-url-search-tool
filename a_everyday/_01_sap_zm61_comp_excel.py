import os
import subprocess

from _99_database_config import current_path, py_path

# _01_sap_logoutファイルのディレクトリを設定
notebook_directory = r"C:\t_20_python\a_everyday"

# スクリプトの実行前にディレクトリを変更
os.chdir(notebook_directory)

# _01_sap_zm61_excelのプロセスを実行
process_zm61_excel = subprocess.Popen(
    [py_path,current_path + r'/_01_sap_zm61_excel.py'])


# _01_sap_zm61_excelのプロセスが終了するまで待機
process_zm61_excel.communicate()

# _01_sap_zm61_renameを実行
subprocess.run([py_path,current_path + r'/_01_sap_zm61_rename.py'])
