import subprocess
from _99_database_config import py_path, current_path
#py_path = r"C:\workspace\jypy_test\Scripts\python.exe"
#current_path = r"C:\workspace\jypy_test\.a_everyday"


def main():
    # _01_sap_zm61のプロセスを実行
    process_zm61 = subprocess.Popen(
        [py_path, current_path +r'/_01_sap_zm61.py'])

    # _01_sap_zm61のプロセスが終了するまで待機
    process_zm61.communicate()

    # _01_sap_zm61_excelのプロセスを実行
    process_zm61_excel = subprocess.Popen(
        [py_path, current_path + r'/_01_sap_zm61_excel.py'])


    # _01_sap_zm61_excelのプロセスが終了するまで待機
    process_zm61_excel.communicate()

    # _01_sap_zm61_renameを実行
    #subprocess.run([py_path,current_path + r'/_01_sap_zm61_rename.py'])

if __name__ == '__main__':
    # Windowsのプロセス生成でfreeze_supportを呼び出し
    #multiprocessing.freeze_support()
    main()
