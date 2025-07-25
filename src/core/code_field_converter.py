#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
SQLiteデータベース内の数値型コードフィールドを文字列型に変換するモジュール

このモジュールは、コード値が数値型(REAL/INTEGER)として保存されているフィールドを
文字列型(TEXT)に変換し、データの一貫性を確保します。
"""

import sqlite3
import pandas as pd
import traceback
import logging
from pathlib import Path


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


def convert_table_column(conn, table, column):
    """テーブルの特定のカラムを数値型から文字列型に変換する"""
    cursor = conn.cursor()
    
    try:
        # トランザクション開始
        cursor.execute("BEGIN TRANSACTION")
        
        # テーブル構造の取得
        cursor.execute(f"PRAGMA table_info('{table}')")
        columns_info = cursor.fetchall()
        
        # 一時テーブルの作成
        temp_table = f"{table}_temp"
        cursor.execute(f'CREATE TABLE "{temp_table}" AS SELECT * FROM "{table}"')
        
        # 元のテーブルを削除
        cursor.execute(f'DROP TABLE "{table}"')
        
        # 新しいテーブル作成用のSQL生成
        column_defs = []
        for col_info in columns_info:
            col_id, name, type_, not_null, default_val, pk = col_info
            
            # 変換対象のカラムの型をTEXTに変更
            if name == column:
                col_type = "TEXT"
            else:
                col_type = type_
            
            # NOT NULL制約
            nn_str = "NOT NULL" if not_null else ""
            
            # デフォルト値
            default_str = f"DEFAULT {default_val}" if default_val is not None else ""
            
            column_defs.append(f'"{name}" {col_type} {nn_str} {default_str}'.strip())
        
        # 主キー制約
        pk_columns = [columns_info[i][1] for i in range(len(columns_info)) if columns_info[i][5]]
        pk_str = ""
        if pk_columns:
            # 単純な文字列連結を使用
            pk_str = ", PRIMARY KEY ("
            for i, col in enumerate(pk_columns):
                if i > 0:
                    pk_str += ", "
                pk_str += '"' + col + '"'
            pk_str += ")"
        
        # 新しいテーブルを作成
        create_sql = f'CREATE TABLE "{table}" ({", ".join(column_defs)}{pk_str})'
        cursor.execute(create_sql)
        
        # データのコピー（変換対象カラムはCASTを使用）
        select_cols = []
        for col_info in columns_info:
            name = col_info[1]
            if name == column:
                select_cols.append(f'CAST("{name}" AS TEXT) AS "{name}"')
            else:
                select_cols.append(f'"{name}"')
        
        copy_sql = f'INSERT INTO "{table}" SELECT {", ".join(select_cols)} FROM "{temp_table}"'
        cursor.execute(copy_sql)
        
        # 一時テーブルを削除
        cursor.execute(f'DROP TABLE "{temp_table}"')
        
        # トランザクションのコミット
        conn.commit()
        return True, None
        
    except Exception as e:
        # エラー発生時はロールバック
        conn.rollback()
        return False, str(e)


def analyze_numeric_code_fields(conn):
    """
    数値型コードフィールドを分析し、変換対象のフィールドを特定する
    
    Args:
        conn: SQLite接続オブジェクト
        
    Returns:
        fields_to_convert: 変換対象フィールドのリスト
        fields_not_to_convert: 変換対象外フィールドのリスト
    """
    # コードフィールドの特定
    code_fields = identify_code_fields(conn)
    
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
        else:
            fields_not_to_convert.append({
                'table': table,
                'column': column,
                'current_type': current_type,
                'reason': analysis['reason'],
                'sample_values': analysis['sample_values']
            })
    
    return fields_to_convert, fields_not_to_convert