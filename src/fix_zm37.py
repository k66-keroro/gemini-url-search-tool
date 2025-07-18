#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
zm37.txtファイルの読み込み問題を解決するスクリプト
file_encodings.csvによると、zm37.txtのエンコーディングはCP932です。
"""

import pandas as pd
import sqlite3
from pathlib import Path
import sys
import csv

# プロジェクトルートへのパスを設定
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

# データベースパス
db_path = PROJECT_ROOT / 'data' / 'sqlite' / 'main.db'
file_path = PROJECT_ROOT / 'data' / 'raw' / 'zm37.txt'
table_name = 'zm37'

print(f"zm37.txtファイルの読み込み開始")
print(f"ファイルパス: {file_path}")
print(f"テーブル名: {table_name}")
print(f"エンコーディング: CP932")
print("-" * 50)

try:
    # ファイルの先頭数行を表示
    try:
        with open(file_path, 'r', encoding='cp932') as f:
            print("ファイル先頭の内容:")
            for i, line in enumerate(f):
                if i >= 5:  # 最初の5行だけ表示
                    break
                print(f"  行 {i+1}: {line.strip()}")
    except Exception as e:
        print(f"ファイル読み込みエラー: {e}")
        sys.exit(1)
    
    # 区切り文字を判定
    with open(file_path, 'r', encoding='cp932') as f:
        first_line = f.readline()
        if '\t' in first_line:
            separator = '\t'
            print(f"区切り文字: タブ ('\\t')")
        elif ',' in first_line:
            separator = ','
            print(f"区切り文字: カンマ (',')")
        elif '|' in first_line:
            separator = '|'
            print(f"区切り文字: パイプ ('|')")
        elif '  ' in first_line:  # 複数のスペース
            separator = r'\s+'
            print(f"区切り文字: 複数スペース ('\\s+')")
        else:
            separator = None
            print(f"区切り文字: 判定できません")
            sys.exit(1)
    
    # pandasで読み込み
    print(f"pandas.read_csvで読み込み中...")
    
    # 特殊な設定でzm37.txtを読み込む
    df = pd.read_csv(
        file_path, 
        encoding='cp932',
        sep=separator,
        quoting=csv.QUOTE_NONE,  # クォーテーションを無視
        engine='python',  # より柔軟な解析のためpythonエンジンを使用
        on_bad_lines='skip',  # 問題のある行をスキップ
        escapechar='\\',  # エスケープ文字を指定
        low_memory=False,  # 型推論のためにすべてのデータを読み込む
        dtype=str  # すべての列を文字列として読み込む
    )
    
    # 成功した場合、データの概要を表示
    print(f"読み込み成功! 行数: {len(df)}, 列数: {len(df.columns)}")
    print(f"列名: {df.columns.tolist()[:10]}...")  # 最初の10列のみ表示
    
    # SQLiteに書き込み
    print(f"SQLiteにテーブル {table_name} を作成中...")
    with sqlite3.connect(db_path) as conn:
        # 既存のテーブルがあれば削除
        conn.execute(f'DROP TABLE IF EXISTS "{table_name}"')
        
        # データをSQLiteに書き込み
        df.to_sql(table_name, conn, if_exists='replace', index=False)
        
        # テーブルが作成されたか確認
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"SQLiteテーブル作成成功! 行数: {count}")
        
        # 主キーを追加
        print(f"主キー(_rowid_)を追加中...")
        cursor.execute(f"ALTER TABLE {table_name} RENAME TO temp_{table_name}")
        
        # 列名を取得
        cursor.execute(f"PRAGMA table_info('temp_{table_name}')")
        columns = [col[1] for col in cursor.fetchall()]
        columns_str = ', '.join([f'"{col}"' for col in columns])
        
        # 新しいテーブルを作成（主キー付き）
        cursor.execute(f'CREATE TABLE "{table_name}" ("_rowid_" INTEGER PRIMARY KEY AUTOINCREMENT, {", ".join([f\'"{col}" TEXT\' for col in columns])})')
        
        # データをコピー
        cursor.execute(f'INSERT INTO "{table_name}" ({columns_str}) SELECT {columns_str} FROM "temp_{table_name}"')
        
        # 一時テーブルを削除
        cursor.execute(f'DROP TABLE "temp_{table_name}"')
        
        print(f"主キー(_rowid_)を追加しました")
    
    print(f"✅ zm37.txtの処理が成功しました!")
    
except Exception as e:
    print(f"❌ エラーが発生しました: {e}")
    import traceback
    print(traceback.format_exc())
    sys.exit(1)