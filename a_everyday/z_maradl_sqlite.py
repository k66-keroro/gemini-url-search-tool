# Re-import after execution environment reset
import pandas as pd
import sqlite3
import pyodbc

# Re-define paths and constants
sqlite_db_path = r'C:\Projects_workspace\02_access\MARA_DL.sqlite'
access_db_path = r'C:\Projects_workspace\02_access\Database1.accdb'
access_table = 'MARA_DL'

access_fields = [
    '品目', '品目テキスト', 'プラント', '品目タイプコード', '標準原価',
    '納入予定日数', '入庫処理日数', '評価クラス', '安全在庫', '最終入庫日',
    '最終出庫日', '品目登録日', '将来予定原価', '現在予定原価',
    '前回予定原価', '日程計画余裕キー', '発注点', 'タイムフェンス',
    '消費モード', '調達タイプ', '特殊調達タイプ', '営業倉庫_最終入庫日',
    '営業倉庫_最終出庫日', 'プラント固有st開始日', '自動購買発注'
]

def convert_to_access_type(df: pd.DataFrame) -> pd.DataFrame:
    float_fields = ['標準原価', '安全在庫', '将来予定原価', '現在予定原価', '前回予定原価']
    long_int_fields = ['納入予定日数', '入庫処理日数', '発注点', 'タイムフェンス']
    date_fields = ['最終入庫日', '最終出庫日', '品目登録日',
                   '営業倉庫_最終入庫日', '営業倉庫_最終出庫日', 'プラント固有st開始日']

    for col in float_fields:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    for col in long_int_fields:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').astype('Int64')

    for col in date_fields:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce', format='%Y%m%d')

    return df
