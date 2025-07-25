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
    
    # 実行するスクリプトのリスト（この順番で実行される）
    scripts = [
        'z01_excel_close.py',  # アプリを強制終了
        'a1_app_open_edge.py',  # アプリを開く
        'a1_app_open_a.py',  # アプリを開く
        'z900_filecopy_txt.py',  # txt等をサーバーからコピー（← **ここが重要！**）
        'z090_zp138_txt.py',  # コピーしたデータを使用
        'z090_zp138_field_mapping.py',  # 追加加工
        'zm87.py',  # コピーしたデータを使用
        'zp02.py',  # コピーしたデータを使用
        'zt_zm87_code.py',  # コピーしたデータを使用
        'zs65.py',  # コピーしたデータを使用
        'a1_app_open_ac.py',  # PythonからAccessのテーブルを開く
    ]

    for script in scripts:
        script_path = os.path.join(current_path, script)
        if not os.path.exists(script_path):
            print(f"[警告] スクリプトが存在しません: {script_path}")
            continue

        print(f"実行中: {script}")
        result = subprocess.run([py_path, script_path], check=True)
        
        if result.returncode != 0:
            print(f"[エラー] スクリプトが失敗しました: {script}")
            break  # 失敗したら処理を止める

    # 最後に実行
    final_script1 = os.path.join(current_path, '_01_sap_zm61_comp.py')
    if os.path.exists(final_script1):
        subprocess.run([py_path, final_script1], check=True)
    else:
        print(f"[警告] 最後のスクリプトが存在しません: {final_script1}")

if __name__ == '__main__':
    multiprocessing.freeze_support()
    main()
