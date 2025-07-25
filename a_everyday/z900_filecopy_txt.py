import pandas as pd
import shutil
import os
from datetime import datetime, timedelta

# Excelファイルのパス
file_path = r'C:\\Projects_workspace\\02_access\\テキスト\\テキスト一覧.xlsx'

# Excelファイルを読み込む
df = pd.read_excel(file_path)

# 更新されていないファイルを格納するリスト
not_updated_files = []

# 昨日の日時を取得
yesterday = datetime.now() - timedelta(days=1)

# 全ての行を処理
for index, row in df.iterrows():
    source_path = row['コピー元ファイルパス']
    file_name = row['ファイル名']
    destination_path = os.path.join(row['コピー先ファイルパス'], file_name)
    
    # サーバー側のファイルの更新日時を取得
    if os.path.exists(source_path):
        file_mod_time = datetime.fromtimestamp(os.path.getmtime(source_path))
        
        # 更新日時が昨日以前の場合、リストに追加
        if file_mod_time < yesterday:
            not_updated_files.append({
                'ファイル名': file_name,
                '更新日時': file_mod_time.strftime('%Y-%m-%d %H:%M:%S')
            })
    
    # ファイルを新しい場所にコピー
    try:
        shutil.copy2(source_path, destination_path)
        print(f"ファイル {file_name} が {destination_path} にコピーされました。")
    except Exception as e:
        print(f"ファイル {file_name} のコピー中にエラーが発生しました: {e}")

# 更新されていないファイルのリストをCSVに出力
not_updated_df = pd.DataFrame(not_updated_files)
not_updated_df.to_csv(r'C:\\Projects_workspace\\02_access\\テキスト\\未更新ファイル一覧.csv', index=False)

print("未更新ファイルのチェックが完了しました。")
