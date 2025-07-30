#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
サンプルデータ作成スクリプト
"""

import sqlite3
import pandas as pd
from pathlib import Path
import datetime
import random
import os

def create_sample_data():
    """金額・数量を含むサンプルデータを作成"""
    print("Creating sample data...")
    
    try:
        # データベースディレクトリを作成
        db_path = Path("data/sqlite/pc_production.db")
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 既存データベースを削除
        if db_path.exists():
            db_path.unlink()
            print("Deleted existing database")
        
        # サンプルデータを作成
        data = []
        mrp_managers = ['PC1', 'PC2', 'PC3', 'PC4']
        naisei_gaichu = ['内製', '外注']
        
        for i in range(2000):
            completion_date = datetime.date(2024, 7, random.randint(1, 29))
            data.append({
                'データソース': 'サンプルデータ',
                'MRP管理者': random.choice(mrp_managers),
                '転記日': completion_date,
                '完成日': completion_date,
                '品目コード': f'ITEM{i:04d}',
                '生産金額': random.randint(50000, 2000000),
                '数量': random.randint(1, 50),
                '内製外注': random.choice(naisei_gaichu),
                '指図番号': f'{random.randint(50000000, 60000000)}',
                '品目テキスト': f'Sample Item {i}',
                '単価': random.randint(1000, 50000)
            })
        
        df = pd.DataFrame(data)
        
        # データベースに保存
        conn = sqlite3.connect(str(db_path))
        df.to_sql('pc_production_zm29', conn, if_exists='replace', index=False)
        conn.close()
        
        print(f"Sample data created: {len(df):,} records")
        print(f"Total amount: {df['生産金額'].sum():,.0f} yen")
        print(f"Total quantity: {df['数量'].sum():,.0f}")
        print(f"Items: {df['品目コード'].nunique():,}")
        print(f"Date range: {df['完成日'].min()} to {df['完成日'].max()}")
        
        return True
        
    except Exception as e:
        print(f"Error creating sample data: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = create_sample_data()
    if success:
        print("\nSample data creation completed!")
        print("You can now run the dashboard:")
        print("  .\\run_standalone.bat")
    else:
        print("\nFailed to create sample data")
    
    input("\nPress Enter to exit...")