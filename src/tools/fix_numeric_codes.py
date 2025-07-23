#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
SQLiteデータベース内の数値型コードフィールドを文字列型に修正するツール

このスクリプトは、コード値が数値型(REAL/INTEGER)として保存されているフィールドを
文字列型(TEXT)に変換し、データの一貫性を確保します。
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
    logger = logging.getLogger("fix_numeric_codes")
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

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
            is_code_field = any(
                pattern in name_lower for pattern in code_patterns)

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
                'reason': '値がありません'
            }

        # 値の分析
        values = df[column].dropna().astype(str).tolist()

        # 先頭に0が付いている値があるか
        has_leading_zeros = any(str(val).startswith(
            '0') and len(str(val)) > 1 for val in values)

        # 固定桁数の数値が多いか
        lengths = [len(str(val)) for val in values]
        most_common_length = max(
            set(lengths), key=lengths.count) if lengths else 0
        fixed_length_ratio = lengths.count(
            most_common_length) / len(lengths) if lengths else 0

        # SAPの後ろマイナス表記（例: 1234-）があるか
        has_sap_minus = any(str(val).endswith('-') for val in values)

        # 判断
        should_convert = has_leading_zeros or fixed_length_ratio > 0.8 or has_sap_minus

        reason = []
        if has_leading_zeros:
            reason.append('先頭に0が付いている値があります')
        if fixed_length_ratio > 0.8:
            reason.append(
                f'固定桁数({most_common_length}桁)の値が多い({fixed_length_ratio:.1%})')
        if has_sap_minus:
            reason.append('SAPの後ろマイナス表記があります')

        return {
            'should_convert': should_convert,
            'reason': ', '.join(reason) if reason else '一般的なコードフィールド'
        }

    except Exception as e:
        return {
            'should_convert': False,
            'reason': f'分析エラー: {str(e)}'
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
        cursor.execute(
            f'CREATE TABLE "{temp_table}" AS SELECT * FROM "{table}"')

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

            column_defs.append(
                f'"{name}" {col_type} {nn_str} {default_str}'.strip())

        # 主キー制約
        pk_columns = [columns_info[i][1]
                      for i in range(len(columns_info)) if columns_info[i][5]]
        if pk_columns:
            pk_str = f", PRIMARY KEY ({', '.join([f'"{col}"' for col in pk_columns])})"
        else:
            pk_str = ""

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


def fix_numeric_code_fields(db_path, dry_run=True, log_file=None, specific_tables=None):
    """
    数値型コードフィールドを文字列型に修正する

    Args:
        db_path: SQLiteデータベースのパス
        dry_run: 変換対象を表示するだけで実際の変換は行わない場合はTrue
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
            code_fields = [
                field for field in code_fields if field['table'] in specific_tables]
            logger.info(f"指定されたテーブルに絞り込み: {len(code_fields)} 個のフィールドを分析します")

        # 変換対象フィールドの特定
        fields_to_convert = []

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
                    'reason': analysis['reason']
                })
                logger.info(
                    f"変換対象: {table}.{column} ({current_type} → TEXT) - {analysis['reason']}")
            else:
                logger.info(
                    f"変換対象外: {table}.{column} ({current_type}) - {analysis['reason']}")

        logger.info(f"{len(fields_to_convert)} 個のフィールドを文字列型に変換します")

        # ドライランモードの場合は実際の変換は行わない
        if dry_run:
            logger.info("ドライランモードのため、実際の変換は行いません")
            return {
                'fields_analyzed': len(code_fields),
                'fields_to_convert': fields_to_convert,
                'converted': 0
            }

        # 実際の変換処理
        converted_count = 0
        failed_conversions = []

        for field in fields_to_convert:
            table = field['table']
            column = field['column']

            logger.info(f"{table}.{column} を文字列型に変換中...")

            success, error = convert_table_column(conn, table, column)

            if success:
                logger.info(f"{table}.{column} の変換が完了しました")
                converted_count += 1
            else:
                logger.error(f"{table}.{column} の変換中にエラーが発生しました: {error}")
                failed_conversions.append({
                    'table': table,
                    'column': column,
                    'error': error
                })

        logger.info(
            f"変換完了: {converted_count}/{len(fields_to_convert)} フィールドを変換しました")
        if failed_conversions:
            logger.warning(f"{len(failed_conversions)} 個のフィールドの変換に失敗しました")

        return {
            'fields_analyzed': len(code_fields),
            'fields_to_convert': fields_to_convert,
            'converted': converted_count,
            'failed': failed_conversions
        }

    except Exception as e:
        logger.error(f"処理中にエラーが発生しました: {str(e)}")
        return {
            'error': str(e)
        }

    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(
        description='SQLiteデータベース内の数値型コードフィールドを文字列型に修正するツール')
    parser.add_argument('db_path', help='SQLiteデータベースのパス')
    parser.add_argument('--dry-run', action='store_true',
                        help='変換対象を表示するだけで実際の変換は行わない')
    parser.add_argument('--log-file', help='ログファイルのパス')
    parser.add_argument('--tables', help='処理対象のテーブル（カンマ区切り）')

    args = parser.parse_args()

    try:
        specific_tables = args.tables.split(',') if args.tables else None

        result = fix_numeric_code_fields(
            args.db_path,
            args.dry_run,
            args.log_file,
            specific_tables
        )

        if 'error' in result:
            print(f"エラー: {result['error']}")
            sys.exit(1)

        print(f"分析したフィールド数: {result['fields_analyzed']}")
        print(f"変換対象フィールド数: {len(result['fields_to_convert'])}")

        if not args.dry_run:
            print(f"変換完了フィールド数: {result['converted']}")
            if result.get('failed'):
                print(f"変換失敗フィールド数: {len(result['failed'])}")

    except Exception as e:
        print(f"エラー: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
