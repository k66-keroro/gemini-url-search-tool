import os
import time

# スクリプトの実行時間を測定
start_time = time.time()

def delete_laccdb_files(directory='C:\\'):
    """指定したディレクトリ内の.laccdbファイルを削除する関数"""
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.laccdb'):
                file_path = os.path.join(root, file)
                try:
                    os.remove(file_path)
                    print(f'{file_path} を削除しました。')
                except Exception as e:
                    print(f'{file_path} の削除中にエラーが発生しました: {e}')

print(f"Script execution time: {time.time() - start_time:.2f} seconds", flush=True)