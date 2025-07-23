#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
SQLiteクエリ実行ツール

このスクリプトは、SQLiteデータベースに対してSQLクエリを実行し、
結果を表示するためのツールです。
"""

import sqlite3
import pandas as pd
import os
import sys
import argparse
import json
import time


def execute_query(db_path, query, output_format='text', limit=None):
    """SQLクエリを実行し、結果を返す"""
    conn = sqlite3.connect(db_path)
    
    try:
        # クエリ実行時間の測定
        start_time = time.time()
        
        # SELECTクエリの場合はpandasを使用
        if query.strip().upper().startswith('SELECT'):
            if limit and 'LIMIT' not in query.upper():
                query = f"{query} LIMIT {limit}"
            
            df = pd.read_sql_query(query, conn)
            end_time = time.time()
            
            result = {
                'success': True,
                'query': query,
                'execution_time': end_time - start_time,
                'row_count': len(df),
                'column_count': len(df.columns),
                'columns': list(df.columns),
                'data': df.to_dict('records') if output_format == 'json' else None
            }
            
            if output_format == 'text':
                # テキスト形式での出力
                text_result = []
                text_result.append(f"クエリ: {query}")
                text_result.append(f"実行時間: {result['execution_time']:.6f}秒")
                text_result.append(f"行数: {result['row_count']}")
                text_result.append(f"列数: {result['column_count']}")
                text_result.append("\n結果:")
                text_result.append(df.to_string(index=False))
                
                result['text_output'] = "\n".join(text_result)
        else:
            # 非SELECTクエリの場合
            cursor = conn.cursor()
            cursor.execute(query)
            conn.commit()
            end_time = time.time()
            
            result = {
                'success': True,
                'query': query,
                'execution_time': end_time - start_time,
                'affected_rows': cursor.rowcount
            }
            
            if output_format == 'text':
                # テキスト形式での出力
                text_result = []
                text_result.append(f"クエリ: {query}")
                text_result.append(f"実行時間: {result['execution_time']:.6f}秒")
                text_result.append(f"影響を受けた行数: {result['affected_rows']}")
                
                result['text_output'] = "\n".join(text_result)
    
    except Exception as e:
        result = {
            'success': False,
            'query': query,
            'error': str(e)
        }
        
        if output_format == 'text':
            result['text_output'] = f"エラー: {str(e)}"
    
    finally:
        conn.close()
    
    return result


def explain_query(db_path, query):
    """クエリの実行計画を取得する"""
    conn = sqlite3.connect(db_path)
    
    try:
        # EXPLAIN QUERY PLAN の実行
        cursor = conn.cursor()
        cursor.execute(f"EXPLAIN QUERY PLAN {query}")
        plan = cursor.fetchall()
        
        # 実行計画の整形
        plan_text = []
        for step in plan:
            plan_text.append(f"- {step}")
        
        result = {
            'success': True,
            'query': query,
            'plan': plan,
            'text_output': "\n".join([f"クエリ: {query}", "\n実行計画:"] + plan_text)
        }
    
    except Exception as e:
        result = {
            'success': False,
            'query': query,
            'error': str(e),
            'text_output': f"エラー: {str(e)}"
        }
    
    finally:
        conn.close()
    
    return result


def main():
    parser = argparse.ArgumentParser(description='SQLiteクエリ実行ツール')
    parser.add_argument('db_path', help='SQLiteデータベースのパス')
    parser.add_argument('-q', '--query', help='実行するSQLクエリ')
    parser.add_argument('-f', '--file', help='SQLクエリを含むファイル')
    parser.add_argument('-o', '--output', choices=['text', 'json'], default='text', help='出力形式（text または json）')
    parser.add_argument('-l', '--limit', type=int, help='結果の最大行数')
    parser.add_argument('-e', '--explain', action='store_true', help='クエリの実行計画を表示')
    parser.add_argument('--output-file', help='出力ファイル（指定しない場合は標準出力）')
    
    args = parser.parse_args()
    
    # クエリの取得
    query = None
    if args.query:
        query = args.query
    elif args.file:
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                query = f.read()
        except Exception as e:
            print(f"ファイル読み込みエラー: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print("エラー: --query または --file オプションを指定してください。", file=sys.stderr)
        sys.exit(1)
    
    try:
        # 実行計画の表示
        if args.explain:
            result = explain_query(args.db_path, query)
        else:
            # クエリの実行
            result = execute_query(args.db_path, query, args.output, args.limit)
        
        # 結果の出力
        if args.output_file:
            with open(args.output_file, 'w', encoding='utf-8') as f:
                if args.output == 'json':
                    json.dump(result, f, ensure_ascii=False, indent=2)
                else:
                    f.write(result['text_output'])
        else:
            if args.output == 'json':
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print(result['text_output'])
    
    except Exception as e:
        print(f"エラー: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()