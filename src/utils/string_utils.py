"""
文字列操作ユーティリティモジュール

SQLite GUI Toolで使用される文字列操作機能を提供します。
"""

import re
import chardet
from typing import Optional, Union, List
from pathlib import Path


class StringUtils:
    """文字列操作ユーティリティクラス"""
    
    @staticmethod
    def sanitize_table_name(table_name: str) -> str:
        """
        テーブル名を適切に変換（日本語や特殊文字を避ける）

        Args:
            table_name: 元のテーブル名

        Returns:
            変換後のテーブル名
        """
        # 日本語文字を含むかチェック
        has_japanese = re.search(r'[ぁ-んァ-ン一-龥]', table_name)

        # 日本語文字を含む場合は、プレフィックスを付ける
        if has_japanese:
            # 簡易的な変換: 日本語テーブル名にはt_を付ける
            sanitized = f"t_{hash(table_name) % 10000:04d}"
        else:
            # 英数字以外の文字を_に置換
            sanitized = re.sub(r'[^a-zA-Z0-9]', '_', table_name)

            # 連続する_を単一の_に置換
            sanitized = re.sub(r'_+', '_', sanitized)

            # 先頭が数字の場合、t_を付ける
            if sanitized and sanitized[0].isdigit():
                sanitized = f"t_{sanitized}"

            # 先頭と末尾の_を削除
            sanitized = sanitized.strip('_')

        return sanitized

    @staticmethod
    def detect_encoding(file_path: Union[str, Path]) -> str:
        """
        ファイルのエンコーディングを検出する

        Args:
            file_path: ファイルパス

        Returns:
            検出されたエンコーディング名
        """
        try:
            with open(file_path, 'rb') as f:
                raw_data = f.read(10000)  # 最初の10KBを読み込み
                
            result = chardet.detect(raw_data)
            encoding = result.get('encoding', 'utf-8')
            
            # 信頼度が低い場合はデフォルトエンコーディングを使用
            confidence = result.get('confidence', 0)
            if confidence < 0.7:
                encoding = 'utf-8'
                
            return encoding
            
        except Exception:
            return 'utf-8'  # デフォルトエンコーディング

    @staticmethod
    def format_sql(sql: str) -> str:
        """
        SQLクエリを整形する

        Args:
            sql: 整形するSQLクエリ

        Returns:
            整形されたSQLクエリ
        """
        # 基本的なSQL整形
        sql = sql.strip()
        
        # キーワードを大文字に変換
        keywords = [
            'SELECT', 'FROM', 'WHERE', 'ORDER BY', 'GROUP BY', 'HAVING',
            'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER',
            'JOIN', 'LEFT JOIN', 'RIGHT JOIN', 'INNER JOIN', 'OUTER JOIN',
            'UNION', 'UNION ALL', 'AND', 'OR', 'NOT', 'IN', 'EXISTS',
            'LIKE', 'BETWEEN', 'IS NULL', 'IS NOT NULL'
        ]
        
        formatted_sql = sql
        for keyword in keywords:
            pattern = r'\b' + re.escape(keyword) + r'\b'
            formatted_sql = re.sub(pattern, keyword, formatted_sql, flags=re.IGNORECASE)
        
        return formatted_sql

    @staticmethod
    def truncate_string(text: str, max_length: int = 50, suffix: str = "...") -> str:
        """
        文字列を指定した長さで切り詰める

        Args:
            text: 切り詰める文字列
            max_length: 最大長
            suffix: 切り詰め時に追加する文字列

        Returns:
            切り詰められた文字列
        """
        if len(text) <= max_length:
            return text
        
        return text[:max_length - len(suffix)] + suffix

    @staticmethod
    def escape_sql_identifier(identifier: str) -> str:
        """
        SQLの識別子をエスケープする

        Args:
            identifier: エスケープする識別子

        Returns:
            エスケープされた識別子
        """
        # ダブルクォートで囲む
        return f'"{identifier}"'

    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """
        ファイルサイズを人間が読みやすい形式に変換する

        Args:
            size_bytes: バイト数

        Returns:
            フォーマットされたファイルサイズ
        """
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        size = float(size_bytes)
        
        while size >= 1024.0 and i < len(size_names) - 1:
            size /= 1024.0
            i += 1
        
        return f"{size:.1f} {size_names[i]}"

    @staticmethod
    def format_number(number: Union[int, float], decimal_places: int = 2) -> str:
        """
        数値を3桁区切りでフォーマットする

        Args:
            number: フォーマットする数値
            decimal_places: 小数点以下の桁数

        Returns:
            フォーマットされた数値文字列
        """
        if isinstance(number, int):
            return f"{number:,}"
        else:
            return f"{number:,.{decimal_places}f}"

    @staticmethod
    def validate_table_name(table_name: str) -> bool:
        """
        テーブル名が有効かどうかを検証する

        Args:
            table_name: 検証するテーブル名

        Returns:
            有効な場合True、無効な場合False
        """
        if not table_name:
            return False
        
        # SQLiteの識別子の規則に従って検証
        # 英数字とアンダースコアのみ許可、先頭は英字またはアンダースコア
        pattern = r'^[a-zA-Z_][a-zA-Z0-9_]*$'
        return bool(re.match(pattern, table_name))

    @staticmethod
    def clean_whitespace(text: str) -> str:
        """
        文字列から余分な空白を除去する

        Args:
            text: クリーンアップする文字列

        Returns:
            クリーンアップされた文字列
        """
        # 連続する空白を単一の空白に置換
        text = re.sub(r'\s+', ' ', text)
        
        # 先頭と末尾の空白を除去
        return text.strip()

    @staticmethod
    def extract_table_names_from_sql(sql: str) -> List[str]:
        """
        SQLクエリからテーブル名を抽出する

        Args:
            sql: 解析するSQLクエリ

        Returns:
            抽出されたテーブル名のリスト
        """
        table_names = []
        
        # FROM句のテーブル名を抽出
        from_pattern = r'\bFROM\s+([a-zA-Z_][a-zA-Z0-9_]*)'
        matches = re.findall(from_pattern, sql, re.IGNORECASE)
        table_names.extend(matches)
        
        # JOIN句のテーブル名を抽出
        join_pattern = r'\bJOIN\s+([a-zA-Z_][a-zA-Z0-9_]*)'
        matches = re.findall(join_pattern, sql, re.IGNORECASE)
        table_names.extend(matches)
        
        # 重複を除去
        return list(set(table_names))