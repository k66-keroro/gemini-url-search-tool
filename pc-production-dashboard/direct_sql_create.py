import sqlite3
import os
from pathlib import Path

# データベースパス
db_path = Path("data/sqlite/pc_production.db")
db_path.parent.mkdir(parents=True, exist_ok=True)

# 既存ファイル削除
if db_path.exists():
    os.remove(str(db_path))

# データベース作成
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# テーブル作成
cursor.execute("""
CREATE TABLE pc_production_zm29 (
    データソース TEXT,
    MRP管理者 TEXT,
    転記日 TEXT,
    完成日 TEXT,
    品目コード TEXT,
    生産金額 INTEGER,
    数量 INTEGER,
    内製外注 TEXT,
    指図番号 TEXT,
    品目テキスト TEXT,
    単価 INTEGER
)
""")

# サンプルデータ挿入
import random
import datetime

for i in range(1000):
    cursor.execute("""
    INSERT INTO pc_production_zm29 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        'Sample',
        random.choice(['PC1', 'PC2', 'PC3']),
        f'2024-07-{random.randint(1,29):02d}',
        f'2024-07-{random.randint(1,29):02d}',
        f'ITEM{i:04d}',
        random.randint(100000, 1000000),
        random.randint(1, 50),
        random.choice(['内製', '外注']),
        f'{50000000 + i}',
        f'Sample Item {i}',
        random.randint(2000, 20000)
    ))

conn.commit()
conn.close()

print("Database created successfully!")
print(f"Location: {db_path.absolute()}")