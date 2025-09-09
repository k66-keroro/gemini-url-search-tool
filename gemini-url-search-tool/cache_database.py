#!/usr/bin/env python3
"""
SQLite Cache Database for Gemini URL Search Tool
検索結果と分析結果のキャッシュシステム
"""

import sqlite3
import json
import hashlib
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import os

class SearchCache:
    """検索結果と分析結果のSQLiteキャッシュ"""
    
    def __init__(self, db_path: str = "data/search_cache.db"):
        """
        キャッシュデータベースを初期化
        
        Args:
            db_path: データベースファイルのパス
        """
        self.db_path = db_path
        
        # データディレクトリを作成
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # データベースを初期化
        self._init_database()
    
    def _init_database(self):
        """データベーステーブルを作成"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 検索結果キャッシュテーブル
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS search_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query_hash TEXT UNIQUE NOT NULL,
                    query TEXT NOT NULL,
                    results TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    hit_count INTEGER DEFAULT 0
                )
            """)
            
            # URL分析結果キャッシュテーブル
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analysis_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url_hash TEXT UNIQUE NOT NULL,
                    url TEXT NOT NULL,
                    query TEXT NOT NULL,
                    analysis TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    hit_count INTEGER DEFAULT 0
                )
            """)
            
            # ユーザー設定テーブル
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT UNIQUE NOT NULL,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # インデックス作成
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_search_query_hash ON search_cache(query_hash)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_search_expires ON search_cache(expires_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_analysis_url_hash ON analysis_cache(url_hash)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_analysis_expires ON analysis_cache(expires_at)")
            
            conn.commit()
    
    def _generate_hash(self, text: str) -> str:
        """テキストのハッシュを生成"""
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    def get_search_results(self, query: str) -> Optional[List[Dict[str, Any]]]:
        """
        検索結果をキャッシュから取得
        
        Args:
            query: 検索クエリ
            
        Returns:
            キャッシュされた検索結果、または None
        """
        query_hash = self._generate_hash(query.lower().strip())
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 有効期限内のキャッシュを検索
            cursor.execute("""
                SELECT results, hit_count FROM search_cache 
                WHERE query_hash = ? AND expires_at > CURRENT_TIMESTAMP
            """, (query_hash,))
            
            result = cursor.fetchone()
            
            if result:
                # ヒット数を更新
                cursor.execute("""
                    UPDATE search_cache 
                    SET hit_count = hit_count + 1 
                    WHERE query_hash = ?
                """, (query_hash,))
                conn.commit()
                
                # JSON形式の結果をデコード
                return json.loads(result[0])
        
        return None
    
    def save_search_results(self, query: str, results: List[Dict[str, Any]], 
                          cache_hours: int = 24) -> None:
        """
        検索結果をキャッシュに保存
        
        Args:
            query: 検索クエリ
            results: 検索結果
            cache_hours: キャッシュ有効時間（時間）
        """
        query_hash = self._generate_hash(query.lower().strip())
        expires_at = datetime.now() + timedelta(hours=cache_hours)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 既存のキャッシュを更新または新規作成
            cursor.execute("""
                INSERT OR REPLACE INTO search_cache 
                (query_hash, query, results, expires_at, hit_count)
                VALUES (?, ?, ?, ?, COALESCE(
                    (SELECT hit_count FROM search_cache WHERE query_hash = ?), 0
                ))
            """, (query_hash, query, json.dumps(results, ensure_ascii=False), 
                  expires_at, query_hash))
            
            conn.commit()
    
    def get_analysis_result(self, url: str, query: str) -> Optional[Dict[str, Any]]:
        """
        URL分析結果をキャッシュから取得
        
        Args:
            url: 分析対象URL
            query: 検索クエリ
            
        Returns:
            キャッシュされた分析結果、または None
        """
        url_hash = self._generate_hash(f"{url}:{query}")
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT analysis, hit_count FROM analysis_cache 
                WHERE url_hash = ? AND expires_at > CURRENT_TIMESTAMP
            """, (url_hash,))
            
            result = cursor.fetchone()
            
            if result:
                # ヒット数を更新
                cursor.execute("""
                    UPDATE analysis_cache 
                    SET hit_count = hit_count + 1 
                    WHERE url_hash = ?
                """, (url_hash,))
                conn.commit()
                
                return json.loads(result[0])
        
        return None
    
    def save_analysis_result(self, url: str, query: str, analysis: Dict[str, Any], 
                           cache_hours: int = 168) -> None:  # 1週間デフォルト
        """
        URL分析結果をキャッシュに保存
        
        Args:
            url: 分析対象URL
            query: 検索クエリ
            analysis: 分析結果
            cache_hours: キャッシュ有効時間（時間）
        """
        url_hash = self._generate_hash(f"{url}:{query}")
        expires_at = datetime.now() + timedelta(hours=cache_hours)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO analysis_cache 
                (url_hash, url, query, analysis, expires_at, hit_count)
                VALUES (?, ?, ?, ?, ?, COALESCE(
                    (SELECT hit_count FROM analysis_cache WHERE url_hash = ?), 0
                ))
            """, (url_hash, url, query, json.dumps(analysis, ensure_ascii=False), 
                  expires_at, url_hash))
            
            conn.commit()
    
    def get_user_setting(self, key: str) -> Optional[str]:
        """
        ユーザー設定を取得
        
        Args:
            key: 設定キー
            
        Returns:
            設定値、または None
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT value FROM user_settings WHERE key = ?", (key,))
            result = cursor.fetchone()
            
            return result[0] if result else None
    
    def save_user_setting(self, key: str, value: str) -> None:
        """
        ユーザー設定を保存
        
        Args:
            key: 設定キー
            value: 設定値
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO user_settings (key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, (key, value))
            
            conn.commit()
    
    def cleanup_expired_cache(self) -> int:
        """
        期限切れのキャッシュを削除
        
        Returns:
            削除されたレコード数
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 期限切れの検索キャッシュを削除
            cursor.execute("DELETE FROM search_cache WHERE expires_at <= CURRENT_TIMESTAMP")
            search_deleted = cursor.rowcount
            
            # 期限切れの分析キャッシュを削除
            cursor.execute("DELETE FROM analysis_cache WHERE expires_at <= CURRENT_TIMESTAMP")
            analysis_deleted = cursor.rowcount
            
            conn.commit()
            
            return search_deleted + analysis_deleted
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        キャッシュ統計情報を取得
        
        Returns:
            キャッシュ統計情報
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 検索キャッシュ統計
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_searches,
                    COUNT(CASE WHEN expires_at > CURRENT_TIMESTAMP THEN 1 END) as valid_searches,
                    SUM(hit_count) as total_search_hits
                FROM search_cache
            """)
            search_stats = cursor.fetchone()
            
            # 分析キャッシュ統計
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_analyses,
                    COUNT(CASE WHEN expires_at > CURRENT_TIMESTAMP THEN 1 END) as valid_analyses,
                    SUM(hit_count) as total_analysis_hits
                FROM analysis_cache
            """)
            analysis_stats = cursor.fetchone()
            
            return {
                'search_cache': {
                    'total': search_stats[0],
                    'valid': search_stats[1],
                    'total_hits': search_stats[2] or 0
                },
                'analysis_cache': {
                    'total': analysis_stats[0],
                    'valid': analysis_stats[1],
                    'total_hits': analysis_stats[2] or 0
                }
            }
    
    def clear_all_cache(self) -> None:
        """全てのキャッシュを削除"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM search_cache")
            cursor.execute("DELETE FROM analysis_cache")
            
            conn.commit()


# 使用例とテスト
if __name__ == "__main__":
    # キャッシュシステムのテスト
    cache = SearchCache()
    
    # テスト用データ
    test_query = "Python 学習"
    test_results = [
        {'title': 'Python.org', 'url': 'https://www.python.org/', 'description': 'Official Python site'},
        {'title': 'Real Python', 'url': 'https://realpython.com/', 'description': 'Python tutorials'}
    ]
    
    test_analysis = {
        'title': 'Python.org - Official Site',
        'summary': 'Python公式サイトです。',
        'analysis': 'Pythonの公式情報が豊富に掲載されています。'
    }
    
    print("=== キャッシュシステムテスト ===")
    
    # 検索結果の保存とテスト
    print("1. 検索結果をキャッシュに保存...")
    cache.save_search_results(test_query, test_results)
    
    print("2. キャッシュから検索結果を取得...")
    cached_results = cache.get_search_results(test_query)
    print(f"キャッシュヒット: {cached_results is not None}")
    
    # 分析結果の保存とテスト
    print("3. 分析結果をキャッシュに保存...")
    cache.save_analysis_result(test_results[0]['url'], test_query, test_analysis)
    
    print("4. キャッシュから分析結果を取得...")
    cached_analysis = cache.get_analysis_result(test_results[0]['url'], test_query)
    print(f"分析キャッシュヒット: {cached_analysis is not None}")
    
    # ユーザー設定のテスト
    print("5. ユーザー設定を保存...")
    cache.save_user_setting("os_version", "Windows 11")
    cache.save_user_setting("python_version", "3.11")
    
    print("6. ユーザー設定を取得...")
    os_version = cache.get_user_setting("os_version")
    python_version = cache.get_user_setting("python_version")
    print(f"OS: {os_version}, Python: {python_version}")
    
    # 統計情報の表示
    print("7. キャッシュ統計情報...")
    stats = cache.get_cache_stats()
    print(f"統計: {stats}")
    
    print("=== テスト完了 ===")