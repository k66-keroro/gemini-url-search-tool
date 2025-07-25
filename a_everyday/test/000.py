import pandas as pd
import os
import sys
import logging
from typing import Dict, Any
from db_utils import (
    setup_logging,
    get_db_connection,
    execute_with_commit,
    BASE_PATH
)

def create_final_output(conn) -> bool:
    """最終出力データを作成する関数"""
    try:
        # 各テーブルをDataFrameとして読み込む
        unique_transfer_items = pd.read_sql_query("SELECT * FROM unique_transfer_items", conn)
        zs65_pivot = pd.read_sql_query("SELECT * FROM zs65_pivot", conn)
        transfer_pivot = pd.read_sql_query("SELECT * FROM transfer_pivot", conn)

        # 転送先のMDMA_BERIDごとにデータを分割
        mdma_keys = ['P100_1220', 'P100_1230', 'P100_1240']
        sheets = {}

        for key in mdma_keys:
            # unique_transfer_items をメインにして、zs65_pivot と transfer_pivot を結合
            merged_df = pd.merge(unique_transfer_items, zs65_pivot, left_on='MARA_MATNR', right_on='品目コード', how='left')
            merged_df = pd.merge(merged_df, transfer_pivot, on='MARA_MATNR', how='left')

            # MDMA_BERIDでフィルタリング
            filtered_df = merged_df[merged_df['MDMA_BERID'] == key]

            # 転送計がブランクでない、かつ0以上の行をフィルタリング
            filtered_df = filtered_df[filtered_df['転送計'].notna() & (filtered_df['転送計'] > 0)]

            # 転送フィールドを動的に抽出
            transfer_columns = [col for col in transfer_pivot.columns if '転送' in col]
            
            # 所要フィールドを動的に抽出
            demand_columns = [col for col in transfer_pivot.columns if '所要' in col]

            # 必要なカラムを選択
            fixed_columns = [
                'ＭＲＰ出庫保管場所', '棚番', '転送計', '所要計', '割合',
                '品目コード', '品目テキスト',
                '1120', '1121', '1122', '1210', '1220', '1230', '1240'
            ]

            # 最終的なカラムの順序を定義（重複を避ける）
            final_columns = fixed_columns + transfer_columns + demand_columns

            # 最終的なDataFrameを作成
            final_df = filtered_df[final_columns]

            # すべての値が0の列を除外
            final_df = final_df.loc[:, (final_df != 0).any(axis=0)]

            # シート名にMDMA_BERIDを使用
            sheets[key] = final_df

        # Excelファイルに書き込む
        output_file = os.path.join(BASE_PATH, '最終統合.xlsx')
        with pd.ExcelWriter(output_file) as writer:
            for sheet_name, df in sheets.items():
                # Excel出力用はそのまま
                df.to_excel(writer, sheet_name=sheet_name, index=False)

                # SQLite保存用はカラム重複をリネーム
                sqlite_df = df.copy()
                cols = sqlite_df.columns.tolist()
                seen = {}
                for i, col in enumerate(cols):
                    if col in seen:
                        seen[col] += 1
                        cols[i] = f"{col}_{seen[col]}"
                    else:
                        seen[col] = 1
                sqlite_df.columns = cols

                dtype_dict = {col: 'VARCHAR(255)' if str(dtype).startswith('object') else 'REAL' for col, dtype in sqlite_df.dtypes.items()}
                sqlite_df.to_sql(f"final_output_{sheet_name}", conn, if_exists='replace', index=False, dtype=dtype_dict)
        
        logging.info(f"最終出力ファイル {output_file} の作成が完了しました")
        return True
    except Exception as e:
        logging.error(f"最終出力ファイルの作成中にエラーが発生しました: {e}")
        return False

def main() -> None:
    """メイン処理関数"""
    setup_logging()
    logging.info("データ処理を開始します")
    
    try:
        with get_db_connection() as conn:
            # 最終出力データを作成
            if not create_final_output(conn):
                raise Exception("最終出力データの作成に失敗しました")
            
            logging.info("データ処理が完了しました")

    except Exception as e:
        logging.error(f"予期せぬエラーが発生しました: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()