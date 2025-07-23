#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
SQLiteデータベース内の数値型コードフィールドを分析するツール

このスクリプトは、コード値が数値型(REAL/INTEGER)として保存されているフィールドを
分析し、文字列型(TEXT)に変換すべきフィールドのレポートを生成します。
"""

import sqlite3
import pandas as pd
import os
import sys
import argparse
import logging
from pathlib import Path
import time


def setup_logger(log_file=None):
    """ロガーの設定"""
    logger = logging.getLogger("analyze_numeric_codes")
    logger.setLevel(logging.INFO)
    
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # コンソール出力
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # ファイル出力（指定がある場合）
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def identify_code_fields(conn):
    """コードフィールドの可能性が高いフィールドを特定する"""
    cursor = conn.cursor()
    
    # テーブル一覧の取得
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [table[0] for table in cursor.fetchall()]
    
    code_fields = []
    
    # コードフィールドのパターン
    code_patterns = [
        'code', 'コード', '番号', 'id', 'no', 'number',
        '伝票', '受注', '発注', '購買', '指図', '品目',
        'wbs', 'ネットワーク', '得意先', '勘定', '保管場所', '評価クラス'
    ]
    
    for table in tables:
        # テーブルのカラム情報を取得
        cursor.execute(f'PRAGMA table_info("{table}")')
        columns = cursor.fetchall()
        
        for col in columns:
            col_id, name, type_, not_null, default_val, pk = col
            
            # カラム名を小文字に変換して比較
            name_lower = name.lower() if isinstance(name, str) else ""
            
            # コードフィールドのパターンに一致するか確認
            is_code_field = any(pattern in name_lower for pattern in code_patterns)
            
            # 数値型（REAL または INTEGER）かつコードフィールドの可能性があるフィールド
            if is_code_field and type_ in ['REAL', 'INTEGER']:
                code_fields.append({
                    'table': table,
                    'column': name,
                    'current_type': type_
                })
    
    return code_fields


def analyze_field_values(conn, table, column):
    """フィールドの値を分析し、文字列型に変換すべきかを判断する"""
    try:
        # テーブル名とカラム名をエスケープ
        quoted_table = f'"{table}"'
        quoted_column = f'"{column}"'
        
        # サンプルデータの取得（最大100行）
        query = f"""
        SELECT {quoted_column}
        FROM {quoted_table}
        WHERE {quoted_column} IS NOT NULL
        LIMIT 100
        """
        
        df = pd.read_sql_query(query, conn)
        
        if df.empty:
            return {
                'should_convert': False,
                'reason': '値がありません',
                'sample_values': []
            }
        
        # 値の分析
        values = df[column].dropna().astype(str).tolist()
        
        # 先頭に0が付いている値があるか
        has_leading_zeros = any(str(val).startswith('0') and len(str(val)) > 1 for val in values)
        
        # 固定桁数の数値が多いか
        lengths = [len(str(val)) for val in values]
        most_common_length = max(set(lengths), key=lengths.count) if lengths else 0
        fixed_length_ratio = lengths.count(most_common_length) / len(lengths) if lengths else 0
        
        # SAPの後ろマイナス表記（例: 1234-）があるか
        has_sap_minus = any(str(val).endswith('-') for val in values)
        
        # 判断
        should_convert = has_leading_zeros or fixed_length_ratio > 0.8 or has_sap_minus
        
        reason = []
        if has_leading_zeros:
            reason.append('先頭に0が付いている値があります')
        if fixed_length_ratio > 0.8:
            reason.append(f'固定桁数({most_common_length}桁)の値が多い({fixed_length_ratio:.1%})')
        if has_sap_minus:
            reason.append('SAPの後ろマイナス表記があります')
        
        # サンプル値（最大5件）
        sample_values = values[:5]
        
        return {
            'should_convert': should_convert,
            'reason': ', '.join(reason) if reason else '一般的なコードフィールド',
            'sample_values': sample_values
        }
    
    except Exception as e:
        return {
            'should_convert': False,
            'reason': f'分析エラー: {str(e)}',
            'sample_values': []
        }


def analyze_numeric_code_fields(db_path, output_file=None, log_file=None, specific_tables=None):
    """
    数値型コードフィールドを分析し、レポートを生成する
    
    Args:
        db_path: SQLiteデータベースのパス
        output_file: 出力ファイルのパス
        log_file: ログファイルのパス
        specific_tables: 特定のテーブルのみを処理する場合はテーブル名のリスト
    """
    logger = setup_logger(log_file)
    logger.info(f"データベース {db_path} の数値型コードフィールドを分析します")
    
    conn = sqlite3.connect(db_path)
    
    try:
        # コードフィールドの特定
        code_fields = identify_code_fields(conn)
        logger.info(f"{len(code_fields)} 個の数値型コードフィールド候補を特定しました")
        
        # 特定のテーブルのみを処理する場合はフィルタリング
        if specific_tables:
            code_fields = [field for field in code_fields if field['table'] in specific_tables]
            logger.info(f"指定されたテーブルに絞り込み: {len(code_fields)} 個のフィールドを分析します")
        
        # 変換対象フィールドの特定
        fields_to_convert = []
        fields_not_to_convert = []
        
        for field in code_fields:
            table = field['table']
            column = field['column']
            current_type = field['current_type']
            
            # フィールド値の分析
            analysis = analyze_field_values(conn, table, column)
            
            if analysis['should_convert']:
                fields_to_convert.append({
                    'table': table,
                    'column': column,
                    'current_type': current_type,
                    'reason': analysis['reason'],
                    'sample_values': analysis['sample_values']
                })
                logger.info(f"変換対象: {table}.{column} ({current_type} → TEXT) - {analysis['reason']}")
            else:
                fields_not_to_convert.append({
                    'table': table,
                    'column': column,
                    'current_type': current_type,
                    'reason': analysis['reason'],
                    'sample_values': analysis['sample_values']
                })
                logger.info(f"変換対象外: {table}.{column} ({current_type}) - {analysis['reason']}")
        
        # レポートの生成
        report = []
        report.append(f"# 数値型コードフィールド分析レポート")
        report.append(f"\n## 分析概要")
        report.append(f"- データベース: {db_path}")
        report.append(f"- 分析日時: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"- 分析フィールド数: {len(code_fields)}")
        report.append(f"- 変換推奨フィールド数: {len(fields_to_convert)}")
        
        report.append(f"\n## 変換推奨フィールド")
        report.append(f"以下のフィールドは文字列型(TEXT)に変換することを推奨します：")
        report.append(f"\n| テーブル | カラム | 現在の型 | 変換理由 | サンプル値 |")
        report.append(f"|---------|-------|---------|----------|------------|")
        
        for field in fields_to_convert:
            sample_str = ", ".join([str(val) for val in field['sample_values']])
            report.append(f"| {field['table']} | {field['column']} | {field['current_type']} | {field['reason']} | {sample_str} |")
        
        report.append(f"\n## 変換非推奨フィールド")
        report.append(f"以下のフィールドは現状のまま数値型で問題ないと判断されます：")
        report.append(f"\n| テーブル | カラム | 現在の型 | 理由 | サンプル値 |")
        report.append(f"|---------|-------|---------|------|------------|")
        
        for field in fields_not_to_convert:
            sample_str = ", ".join([str(val) for val in field['sample_values']])
            report.append(f"| {field['table']} | {field['column']} | {field['current_type']} | {field['reason']} | {sample_str} |")
        
        report.append(f"\n## 変換コマンド例")
        report.append(f"以下のコマンドで変換を実行できます：")
        report.append(f"\n```bash")
        report.append(f"# ドライラン（変換対象の確認のみ）")
        report.append(f"python src/tools/fix_numeric_codes.py {db_path} --dry-run")
        report.append(f"\n# 実際に変換を実行")
        report.append(f"python src/tools/fix_numeric_codes.py {db_path}")
        report.append(f"```")
        
        # レポートの出力
        report_text = "\n".join(report)
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_text)
            logger.info(f"レポートを {output_file} に出力しました")
        else:
            print(report_text)
        
        return {
            'fields_analyzed': len(code_fields),
            'fields_to_convert': fields_to_convert,
            'fields_not_to_convert': fields_not_to_convert
        }
    
    except Exception as e:
        logger.error(f"処理中にエラーが発生しました: {str(e)}")
        return {
            'error': str(e)
        }
    
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description='SQLiteデータベース内の数値型コードフィールドを分析するツール')
    parser.add_argument('db_path', help='SQLiteデータベースのパス')
    parser.add_argument('-o', '--output', help='レポート出力ファイルのパス')
    parser.add_argument('--log-file', help='ログファイルのパス')
    parser.add_argument('--tables', help='処理対象のテーブル（カンマ区切り）')
    
    args = parser.parse_args()
    
    try:
        specific_tables = args.tables.split(',') if args.tables else None
        
        result = analyze_numeric_code_fields(
            args.db_path, 
            args.output, 
            args.log_file,
            specific_tables
        )
        
        if 'error' in result:
            print(f"エラー: {result['error']}")
            sys.exit(1)
        
        if not args.output:
            print(f"\n分析したフィールド数: {result['fields_analyzed']}")
            print(f"変換推奨フィールド数: {len(result['fields_to_convert'])}")
            print(f"変換非推奨フィールド数: {len(result['fields_not_to_convert'])}")
    
    except Exception as e:
        print(f"エラー: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()