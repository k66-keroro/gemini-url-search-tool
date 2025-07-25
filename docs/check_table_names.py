#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
テーブル名の対応関係を確認するスクリプト

このスクリプトは、SQLiteデータベース内のテーブル名と元のファイル名の対応関係を確認します。
"""

import sqlite3
import pandas as pd
import os
import sys
import argparse
from pathlib import Path


def check_table_names(db_path, output_file=None):
    """
    テーブル名の対応関係を確認する
    
    Args:
        db_path: SQLiteデータベースのパス
        output_file: 出力ファイルのパス（指定しない場合は標準出力）
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # テーブル一覧の取得
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [table[0] for table in cursor.fetchall()]
    
    # テーブル情報の収集
    table_info = []
    
    for table in tables:
        # カラム情報の取得
        cursor.execute(f"PRAGMA table_info('{table}')")
        columns = cursor.fetchall()
        
        # 行数の取得
        cursor.execute(f"SELECT COUNT(*) FROM '{table}'")
        row_count = cursor.fetchone()[0]
        
        # テーブル情報を追加
        table_info.append({
            'table_name': table,
            'column_count': len(columns),
            'row_count': row_count,
            'is_t_prefixed': table.startswith('t_')
        })
    
    # DataFrameに変換
    df = pd.DataFrame(table_info)
    
    # t_プレフィックスのテーブル数
    t_prefixed_count = df['is_t_prefixed'].sum()
    
    # 結果の出力
    output = []
    output.append(f"データベース: {db_path}")
    output.append(f"テーブル総数: {len(tables)}")
    output.append(f"t_プレフィックスのテーブル数: {t_prefixed_count}")
    output.append("\nテーブル一覧:")
    
    # テーブル情報をソート（t_プレフィックス、行数の多い順）
    df = df.sort_values(by=['is_t_prefixed', 'row_count'], ascending=[False, False])
    
    for _, row in df.iterrows():
        output.append(f"{row['table_name']}: {row['column_count']}列, {row['row_count']}行")
    
    # 結果の出力
    result = "\n".join(output)
    
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result)
    else:
        print(result)
    
    conn.close()
    
    return df


def main():
    parser = argparse.ArgumentParser(description='テーブル名の対応関係を確認するスクリプト')
    parser.add_argument('db_path', help='SQLiteデータベースのパス')
    parser.add_argument('-o', '--output', help='出力ファイルのパス')
    
    args = parser.parse_args()
    
    try:
        check_table_names(args.db_path, args.output)
    except Exception as e:
        print(f"エラー: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()