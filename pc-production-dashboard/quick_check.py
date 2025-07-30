import sqlite3
import pandas as pd
from pathlib import Path

db_path = Path('data/sqlite/pc_production.db')
print(f'データベースパス: {db_path}')
print(f'存在確認: {db_path.exists()}')

if db_path.exists():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
    tables = cursor.fetchall()
    print(f'テーブル一覧: {tables}')
    
    if tables:
        table_name = tables[0][0]
        
        # テーブル構造を確認
        cursor.execute(f'PRAGMA table_info({table_name})')
        columns = cursor.fetchall()
        print(f'\n{table_name}のカラム構造:')
        for col in columns:
            print(f'  {col[1]} ({col[2]})')
        
        cursor.execute(f'SELECT COUNT(*) FROM {table_name}')
        count = cursor.fetchone()[0]
        print(f'\n{table_name}テーブル: {count}行')
        
        # サンプルデータをDataFrameで表示
        df = pd.read_sql_query(f'SELECT * FROM {table_name} LIMIT 5', conn)
        print(f'\nサンプルデータ:')
        print(df.to_string())
        
        # 必要なカラムの存在確認
        required_columns = ['MRP管理者', '転記日付', '完成数', '金額', '月別週区分']
        print(f'\n必要カラムの存在確認:')
        for col in required_columns:
            exists = col in df.columns
            print(f'  {col}: {"✅" if exists else "❌"}')
    
    conn.close()
else:
    print('データベースが見つかりません')