import os
from collections import defaultdict

def classify_files(directory):
    classified_files = defaultdict(list)

    # ディレクトリ内のファイルをリストアップ
    for filename in os.listdir(directory):
        if os.path.isfile(os.path.join(directory, filename)):
            # 拡張子を取得
            ext = filename.split('.')[-1] if '.' in filename else 'no_extension'
            classified_files[ext].append(filename)

    return classified_files

directory_path = r'C:\t_20_python\a_everyday'  # 対象ディレクトリのパスを指定
classified_results = classify_files(directory_path)

# 分類結果を表示
for ext, files in classified_results.items():
    print(f'拡張子: {ext}, ファイル: {files}')
