import pandas as pd
import pyodbc
import numpy as np
from decimal import Decimal

def import_data_to_access():
    # ファイルパスとデータベースの設定
    txt_file_path = r'C:\Projects_workspace\02_access\テキスト\MARA_DL.csv'
    access_db_path = r'C:\Projects_workspace\02_access\Database1.accdb'
    table_name = 'MARA_DL'

    # Accessデータベースへの接続
    conn_str = f'DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={access_db_path};'
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    # 既存のテーブルがあれば削除
    try:
        cursor.execute(f'DROP TABLE {table_name}')
        conn.commit()
        print(f"テーブル '{table_name}' を削除しました。")
    except Exception as e:
        print(f"テーブル削除中にエラー: {e}")
    


    # TXTファイルの読み込み（カンマ区切りの場合）
    df = pd.read_csv(
        txt_file_path,
        delimiter=',',
        encoding='UTF-16',
        na_values=["", "NA", " "],
        dtype={'品目': str}  # 品目を文字列型として読み込む
    )
    

    #df = df.replace(r'^\s*|\s*$|nan|NaN|NA|None', '', regex=True)
    
    #numeric_columns = ['現会計年度', '将来会計年度', '前回会計年度']
    # 0をNoneに変換
    #df[numeric_columns] = df[numeric_columns].replace(0, None)
    # 品目を文字列型に変換（ゼロ埋めは行わない）
    df['品目'] = df['品目'].astype(str)
    
    # 数値型の列に対して欠損値を 0 に変換
    numeric_fields = ['標準原価', '納入予定日数', '入庫処理日数', '安全在庫','現会計年度', '将来会計年度', '前回会計年度',
                      '現期間', '将来期間', '将来予定原価', '現在予定原価','前回期間', '前回予定原価', 
                      '日程計画余裕キー','タイムフェンス','発注点','逆消費期間','順消費期間']
    for field in numeric_fields:
        if field in df.columns:
            df[field] = df[field].apply(lambda x: None if x == 0 else x)
    # データのクレンジング
    df = df.where(pd.notnull(df), None)
    
    
    # CSVファイルの列名を確認
    ##print("元のCSVファイルの列名:", df.columns.tolist())

    # 列名の空白や特殊文字を削除
    df.columns = df.columns.str.strip()

    # 正規化後の列名を確認
    ##print("正規化後のデータフレームの列名:", df.columns.tolist())

    # プラントでフィルタリング
    df = df[df['プラント'].str.startswith('P1', na=False)]

    # データをランダムにサンプリング（検証用）
    ##df = df.sample(n=10000, random_state=42)
    
    # 列名をマッピング
    df.rename(columns={
        '最終入庫日': '最終入庫日',
        '最終出庫日': '最終出庫日',
        '品目登録日': '品目登録日',
        '営業倉庫最終入庫日': '営業倉庫_最終入庫日',
        '営業倉庫最終出庫日': '営業倉庫_最終出庫日',
        'プラント固有開始日': 'プラント固有st開始日'
    }, inplace=True)
    
    # 日付フィールドをリストにする
    date_fields = [
        '最終入庫日', '最終出庫日', '品目登録日', '営業倉庫_最終入庫日',
        '営業倉庫_最終出庫日', 'プラント固有st開始日','ROHS日付'
    ]
    from datetime import datetime
    
    # 日付フィールドの処理
    for field in date_fields:
        if field in df.columns:
            df[field] = df[field].apply(
                lambda x: None if pd.isnull(x) or x == 0 else datetime.strptime(str(int(x)), '%Y%m%d') if isinstance(x, (int, float)) and not pd.isnull(x) else x
            )
        else:
            print(f"警告: {field} がCSVファイルに存在しません。")

    # 評価クラスを文字列型に変換
    df['評価クラス'] = df['評価クラス'].apply(lambda x: None if pd.isnull(x) or str(x).strip() == '' else int(float(str(x).strip())))
    # 保管場所のデータ型を整数型に設定
    df['評価クラス'] = df['評価クラス'].astype('Int64') 
    #df['評価クラス'] = df['評価クラス'].astype(str)
    df['品目'] = df['品目'].astype(str)



    # テーブル構造を定義
    table_columns = {
    '品目':'TEXT','品目テキスト':'TEXT','プラント':'TEXT','品目タイプコード':'TEXT',
    '標準原価':'DOUBLE','品目階層':'TEXT','納入予定日数':'INTEGER','入庫処理日数':'INTEGER',
    'MRP_管理者':'TEXT','MRP_管理者名':'TEXT','メーカー名':'TEXT','安全重要部品':'TEXT',
    'ROHSコード':'TEXT','ROHS日付':'DATETIME','材料費_設計予算_':'DOUBLE',
    '加工費_設計予算_':'DOUBLE','工程':'TEXT','CMコード':'TEXT','評価クラス':'TEXT',
    '品目グループ':'TEXT','品目grpテキスト':'TEXT','研究室_設計室':'TEXT','発注点':'INTEGER',
    '安全在庫':'DOUBLE','最終入庫日':'DATETIME','最終出庫日':'DATETIME',
    '利益センタ':'TEXT','調達タイプ':'TEXT','特殊調達タイプ':'TEXT','消費モード':'TEXT',
    '逆消費期間':'TEXT','順消費期間':'TEXT','二重ＭＲＰ区分':'TEXT','販売ステータス':'TEXT',
    'ＭＲＰタイプ':'TEXT','タイムフェンス':'INTEGER','ＭＲＰ出庫保管場所':'TEXT',
    '棚番':'TEXT','BOM':'TEXT','作業手順':'TEXT','ロットサイズ':'TEXT','最小ロットサイズ':'DOUBLE',
    '最大ロットサイズ':'INTEGER','丸め数量':'DOUBLE','現会計年度':'INTEGER',
    '現期間':'INTEGER','格上げ区分':'TEXT','将来会計年度':'INTEGER','将来期間':'INTEGER',
    '将来予定原価':'DOUBLE','現在予定原価':'DOUBLE','前回会計年度':'INTEGER',
    '前回期間':'INTEGER','前回予定原価':'DOUBLE','間接費グループ':'TEXT',
    '品目登録日':'DATETIME','日程計画余裕キー':'INTEGER','プラント固有ステータス':'TEXT',
    '営業倉庫_最終入庫日':'DATETIME','営業倉庫_最終出庫日':'DATETIME','原価計算ロットサイズ':'INTEGER',
    '設計担当者ID':'TEXT','設計担当者名':'TEXT','プラント固有st開始日':'DATETIME',
    '自動購買発注':'TEXT',
    }
    

        # テーブルに必要な列のみを選択
    df = df[list(table_columns.keys())]
    #<NA>をNoneに置き換える
    df[field] = df[field].replace({"<NA>": None})
    df = df.replace({pd.NaT: None, np.nan: None})
    
    if df.empty:
        print("データフレームが空です。データを確認してください。")
    else:
        create_table_query = f'CREATE TABLE {table_name} ({", ".join([f"[{col}] {dtype} NULL" for col, dtype in table_columns.items()])})'
        cursor.execute(create_table_query)
        conn.commit()

        df = df[list(table_columns.keys())]

        for index, row in df.iterrows():
            placeholders = ', '.join(['?'] * len(row))
            insert_query = f'INSERT INTO {table_name} VALUES ({placeholders})'
            row_data = tuple(row)
            try:
                cursor.execute(insert_query, row_data)
            except Exception as e:
                print(f"挿入エラーの詳細: {e}")
                print(f"行データ: {row_data}")

        conn.commit()
    #print(df[['受注伝票番号', '受注伝票明細', '完成数']])
    cursor.close()
    conn.close()
    print("データのインポートが完了しました。")

if __name__ == "__main__":
    import_data_to_access()
