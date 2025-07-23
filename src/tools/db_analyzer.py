#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
SQLiteデータベース分析ツール

このスクリプトは、SQLiteデータベースの構造と内容を分析し、
レポートを生成するためのツールです。
"""

import sqlite3
import pandas as pd
import os
import sys
import argparse
from datetime import datetime
import json


def analyze_table_structure(conn, table_name):
    """テーブルの構造を分析する"""
    cursor = conn.cursor()
    
    # テーブル名を引用符で囲む（PRAGMAコマンドでは引用符は不要）
    quoted_table = f'"{table_name}"'
    
    # カラム情報の取得
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    
    column_info = []
    for col in columns:
        col_id, name, type_, not_null, default_val, pk = col
        column_info.append({
            'name': name,
            'type': type_,
            'not_null': bool(not_null),
            'default': default_val,
            'primary_key': bool(pk)
        })
    
    # インデックス情報の取得
    cursor.execute(f"PRAGMA index_list({table_name})")
    indexes = cursor.fetchall()
    
    index_info = []
    for idx in indexes:
        idx_name = idx[1]
        
        # インデックスの詳細情報
        cursor.execute(f"PRAGMA index_info({idx_name})")
        idx_columns = cursor.fetchall()
        
        columns = []
        for info in idx_columns:
            col_pos, col_idx = info[0], info[1]
            cursor.execute(f"PRAGMA table_info({table_name})")
            col_name = cursor.fetchall()[col_idx][1]
            columns.append({
                'position': col_pos,
                'name': col_name
            })
        
        index_info.append({
            'name': idx_name,
            'columns': columns
        })
    
    return {
        'columns': column_info,
        'indexes': index_info
    }


def get_table_stats(conn, table_name):
    """テーブルの統計情報を取得する"""
    cursor = conn.cursor()
    
    # テーブル名を引用符で囲む
    quoted_table = f'"{table_name}"'
    
    # 行数のカウント
    cursor.execute(f"SELECT COUNT(*) FROM {quoted_table}")
    row_count = cursor.fetchone()[0]
    
    # サンプルデータの取得
    cursor.execute(f"SELECT * FROM {quoted_table} LIMIT 5")
    sample_data = cursor.fetchall()
    
    # カラム名の取得
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [col[1] for col in cursor.fetchall()]
    
    # サンプルデータを辞書のリストに変換
    sample_rows = []
    for row in sample_data:
        sample_rows.append(dict(zip(columns, row)))
    
    return {
        'row_count': row_count,
        'sample_data': sample_rows
    }


def analyze_data_distribution(conn, table_name, column_name):
    """カラムのデータ分布を分析する"""
    try:
        # カラム名を引用符で囲む
        quoted_column = f'"{column_name}"'
        quoted_table = f'"{table_name}"'
        
        # 基本統計情報
        query = f"""
        SELECT 
            COUNT(*) as count,
            COUNT(DISTINCT {quoted_column}) as unique_count,
            MIN({quoted_column}) as min_value,
            MAX({quoted_column}) as max_value
        FROM {quoted_table}
        WHERE {quoted_column} IS NOT NULL
        """
        
        df = pd.read_sql_query(query, conn)
        stats = df.to_dict('records')[0]
        
        # 頻度分布（上位10件）
        query = f"""
        SELECT 
            {quoted_column} as value,
            COUNT(*) as frequency
        FROM {quoted_table}
        WHERE {quoted_column} IS NOT NULL
        GROUP BY {quoted_column}
        ORDER BY frequency DESC
        LIMIT 10
        """
        
        df = pd.read_sql_query(query, conn)
        distribution = df.to_dict('records')
        
        return {
            'stats': stats,
            'distribution': distribution
        }
    except Exception as e:
        return {
            'error': str(e)
        }


def check_data_quality(conn, table_name):
    """データ品質をチェックする"""
    cursor = conn.cursor()
    
    # カラム情報の取得
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [col[1] for col in cursor.fetchall()]
    
    quality_issues = []
    
    # テーブル名を引用符で囲む
    quoted_table = f'"{table_name}"'
    
    # 各カラムの NULL 値をチェック
    for col in columns:
        quoted_col = f'"{col}"'
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {quoted_table} WHERE {quoted_col} IS NULL")
            null_count = cursor.fetchone()[0]
            
            cursor.execute(f"SELECT COUNT(*) FROM {quoted_table}")
            total_count = cursor.fetchone()[0]
            
            if null_count > 0:
                null_percentage = (null_count / total_count) * 100
                quality_issues.append({
                    'type': 'NULL値',
                    'column': col,
                    'count': null_count,
                    'percentage': null_percentage
                })
        except Exception as e:
            quality_issues.append({
                'type': 'エラー',
                'column': col,
                'error': str(e)
            })
    
    # 重複値のチェック
    for col in columns:
        quoted_col = f'"{col}"'
        try:
            cursor.execute(f"""
            SELECT {quoted_col}, COUNT(*) as count
            FROM {quoted_table}
            GROUP BY {quoted_col}
            HAVING count > 1
            ORDER BY count DESC
            LIMIT 5
            """)
            
            duplicates = cursor.fetchall()
            if duplicates:
                for dup in duplicates:
                    quality_issues.append({
                        'type': '重複値',
                        'column': col,
                        'value': str(dup[0]),
                        'count': dup[1]
                    })
        except Exception as e:
            # すでにエラーが記録されている場合は追加しない
            if not any(issue['type'] == 'エラー' and issue['column'] == col for issue in quality_issues):
                quality_issues.append({
                    'type': 'エラー',
                    'column': col,
                    'error': str(e)
                })
    
    return quality_issues


def generate_report(db_path, table_name=None, output_format='text'):
    """データベース分析レポートを生成する"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # テーブル一覧の取得
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [table[0] for table in cursor.fetchall()]
    
    report = {
        'database': os.path.basename(db_path),
        'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'table_count': len(tables),
        'tables': []
    }
    
    # 特定のテーブルのみ分析
    if table_name:
        if table_name in tables:
            tables = [table_name]
        else:
            return {'error': f"テーブル '{table_name}' が見つかりません。"}
    
    # 各テーブルの分析
    for table in tables:
        table_structure = analyze_table_structure(conn, table)
        table_stats = get_table_stats(conn, table)
        quality_issues = check_data_quality(conn, table)
        
        # カラムごとのデータ分布（最初の5カラムのみ）
        distributions = {}
        for i, col in enumerate(table_structure['columns']):
            if i >= 5:  # 最初の5カラムのみ
                break
            distributions[col['name']] = analyze_data_distribution(conn, table, col['name'])
        
        table_report = {
            'name': table,
            'structure': table_structure,
            'stats': table_stats,
            'quality_issues': quality_issues,
            'distributions': distributions
        }
        
        report['tables'].append(table_report)
    
    conn.close()
    
    # レポート出力
    if output_format == 'json':
        return report
    else:  # text
        text_report = []
        text_report.append(f"データベース: {report['database']}")
        text_report.append(f"分析時間: {report['analysis_time']}")
        text_report.append(f"テーブル数: {report['table_count']}")
        text_report.append("")
        
        for table in report['tables']:
            text_report.append(f"テーブル: {table['name']}")
            text_report.append("=" * 50)
            
            # 構造
            text_report.append("カラム構造:")
            for col in table['structure']['columns']:
                pk_str = " [PK]" if col['primary_key'] else ""
                nn_str = " [NOT NULL]" if col['not_null'] else ""
                text_report.append(f"- {col['name']} ({col['type']}){pk_str}{nn_str}")
            
            # インデックス
            if table['structure']['indexes']:
                text_report.append("\nインデックス:")
                for idx in table['structure']['indexes']:
                    text_report.append(f"- {idx['name']}")
                    for col in idx['columns']:
                        text_report.append(f"  - カラム: {col['name']}")
            
            # 統計
            text_report.append(f"\n行数: {table['stats']['row_count']}")
            
            # サンプルデータ
            if table['stats']['sample_data']:
                text_report.append("\nサンプルデータ (最初の5行):")
                for i, row in enumerate(table['stats']['sample_data']):
                    text_report.append(f"行 {i+1}: {row}")
            
            # 品質問題
            if table['quality_issues']:
                text_report.append("\nデータ品質問題:")
                for issue in table['quality_issues']:
                    if issue['type'] == 'NULL値':
                        text_report.append(f"- {issue['column']}: NULL値 {issue['count']}件 ({issue['percentage']:.2f}%)")
                    elif issue['type'] == '重複値':
                        text_report.append(f"- {issue['column']}: 値「{issue['value']}」が {issue['count']}回出現")
            
            text_report.append("\n")
        
        return "\n".join(text_report)


def main():
    parser = argparse.ArgumentParser(description='SQLiteデータベース分析ツール')
    parser.add_argument('db_path', help='SQLiteデータベースのパス')
    parser.add_argument('-t', '--table', help='分析するテーブル名（指定しない場合は全テーブル）')
    parser.add_argument('-o', '--output', choices=['text', 'json'], default='text', help='出力形式（text または json）')
    parser.add_argument('-f', '--file', help='出力ファイル（指定しない場合は標準出力）')
    
    args = parser.parse_args()
    
    try:
        report = generate_report(args.db_path, args.table, args.output)
        
        if args.file:
            with open(args.file, 'w', encoding='utf-8') as f:
                if args.output == 'json':
                    json.dump(report, f, ensure_ascii=False, indent=2)
                else:
                    f.write(report)
        else:
            if args.output == 'json':
                print(json.dumps(report, ensure_ascii=False, indent=2))
            else:
                print(report)
    except Exception as e:
        print(f"エラー: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()