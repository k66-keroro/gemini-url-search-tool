import os
import subprocess
import multiprocessing
from _99_database_config import current_path, py_path
from z00_laccdb_deleat import delete_laccdb_files  # laccdb_deleteモジュールをインポート

def main():
    # _01_sap_logoutファイルのディレクトリを設定
    notebook_directory = r"C:\t_20_python\a_everyday"

    # スクリプトの実行前にディレクトリを変更
    os.chdir(notebook_directory)

    # Cドライブ内の.laccdbファイルを削除
    delete_laccdb_files()

    # 実行するスクリプトのリスト
    scripts = [
        'z01_excel_close.py',
        'a1_app_open_a.py',
        'a1_app_open_ac.py',
        'a1_app_open_edge.py',
        'z090_zp138_txt.py',
        'z090_zp138_field_mapping.py',
    ]

    processes = []
    for script in scripts:
        script_path = os.path.join(current_path, script)
        if not os.path.exists(script_path):
            print(f"[警告] スクリプトが存在しません: {script_path}")
            continue
        processes.append(subprocess.Popen([py_path, script_path]))

    # 全てのプロセスが終了するのを待つ
    for process in processes:
        process.wait()

    # 最後に実行
    final_script = os.path.join(current_path, '_01_sap_zm61_comp.py')
    if os.path.exists(final_script):
        subprocess.Popen([py_path, final_script])
    else:
        print(f"[警告] 最後のスクリプトが存在しません: {final_script}")

if __name__ == '__main__':
    # Windowsのプロセス生成でfreeze_supportを呼び出し
    multiprocessing.freeze_support()
    main()
