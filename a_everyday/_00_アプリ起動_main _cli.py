import os
import subprocess
import logging
import time
from datetime import datetime
from tqdm import tqdm
from _99_database_config import current_path, py_path

# ログ設定
log_filename = f'script_execution_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
logging.basicConfig(
    filename=log_filename,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

def execute_script(script_path):
    try:
        start = time.time()
        process = subprocess.run(
            [py_path, script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        elapsed = time.time() - start

        logging.info(f"[実行完了] {os.path.basename(script_path)} ({elapsed:.2f}秒)")
        if process.stdout:
            logging.info(f"[標準出力] {script_path}:\n{process.stdout}")
        if process.stderr:
            logging.error(f"[エラー出力] {script_path}:\n{process.stderr}")
        if process.returncode != 0:
            logging.warning(f"[警告] {script_path} がエラーコード {process.returncode} で終了しました")

        return elapsed

    except Exception as e:
        logging.error(f"[例外] スクリプト実行エラー: {script_path}, エラー: {e}")
        return -1

def main():
    scripts = [
        'z01_excel_close.py', 'a1_app_open_edge.py', 'a1_app_open_a.py',
        'z900_filecopy_txt.py', 'z090_zp138_txt.py', 'z090_zp138_field_mapping.py',
        'zm87.py', 'zp02.py', 'zt_zm87_code.py', 'zs65.py', 'zs61_all.py',
        'zs58.py', 'zm29.py', 'zp70.py', 'ZP51.py', 'ZP58.py',
        'z_maradl.py', 'z_maradl2.py', 'z_view_pcmaster.py',
        'z_Parsed Pc Master Diff Logger.py', 'a1_app_open_ac.py'
    ]

    total = len(scripts)
    start_time = time.time()

    print("\n=== スクリプト実行開始 ===\n")

    for i, script in enumerate(tqdm(scripts, desc="全体進捗", unit="script")):
        script_path = os.path.join(current_path, script)
        if not os.path.exists(script_path):
            logging.warning(f"[スキップ] スクリプトが存在しません: {script_path}")
            continue

        print(f"\n▶ 実行中: {script} ({i+1}/{total})")
        elapsed = execute_script(script_path)
        print(f"⏱️ 経過時間: {elapsed:.2f}秒")

        if script == 'z_view_pcmaster.py':
            print("⏳ 特別待機中... (10秒)")
            time.sleep(10)
        else:
            time.sleep(5)

    # 差分登録ログチェック
    diff_log = os.path.join(current_path, "差分登録ログ.csv")
    if os.path.exists(diff_log):
        mod_time = os.path.getmtime(diff_log)
        logging.info(f"[確認] 差分登録ログ.csv の最終更新: {datetime.fromtimestamp(mod_time)}")
    else:
        logging.warning("[未確認] 差分登録ログ.csv が存在しません")

    # 最後のスクリプト実行
    final_script = os.path.join(current_path, '_01_sap_zm61_comp.py')
    if os.path.exists(final_script):
        print(f"\n🏁 最終スクリプト実行: {os.path.basename(final_script)}")
        subprocess.run([py_path, final_script], check=True)

    total_elapsed = time.time() - start_time
    print(f"\n✅ 全スクリプト完了！総処理時間: {total_elapsed:.2f}秒")
    logging.info(f"[完了] 全スクリプト処理完了: 総時間 {total_elapsed:.2f}秒")

if __name__ == '__main__':
    main()
