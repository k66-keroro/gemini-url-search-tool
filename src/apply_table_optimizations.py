#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
SQLiteテーブルに主キーとインデックスを一括適用するスクリプト
"""

import sqlite3
import sys
import logging
from pathlib import Path

# プロジェクトルートへのパスを設定
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

# 修正版SQLiteManagerをインポート
from src.core.sqlite_manager_fixed import SQLiteManager

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(PROJECT_ROOT / 'logs' / 'apply_table_optimizations.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

def main():
    """メイン処理"""
    try:
        # データベースパス
        db_path = PROJECT_ROOT / 'data' / 'sqlite' / 'main.db'
        
        # 定義ファイルのパス
        primary_key_file = PROJECT_ROOT / 'config' / 'index_definitions.txt'
        index_file = PROJECT_ROOT / 'config' / 'index_definitions.txt'
        
        # 両方のファイルが存在するか確認
        if not primary_key_file.exists():
            logger.error(f"主キー定義ファイルが見つかりません: {primary_key_file}")
            return 1
            
        if not index_file.exists():
            logger.error(f"インデックス定義ファイルが見つかりません: {index_file}")
            return 1
            
        # データベースが存在するか確認
        if not db_path.exists():
            logger.error(f"データベースファイルが見つかりません: {db_path}")
            return 1
            
        logger.info("テーブル最適化処理を開始します")
        logger.info(f"データベース: {db_path}")
        logger.info(f"主キー定義: {primary_key_file}")
        logger.info(f"インデックス定義: {index_file}")
        
        # SQLiteManagerのインスタンスを作成
        manager = SQLiteManager(db_path)
        
        # 最適化を適用
        success_count, error_count, error_messages = manager.apply_table_optimizations(
            primary_key_file, index_file
        )
        
        # 結果を表示
        logger.info("=" * 50)
        logger.info(f"処理完了: 成功={success_count}, 失敗={error_count}")
        
        if error_messages:
            logger.warning("以下のエラーが発生しました:")
            for msg in error_messages:
                logger.warning(f"- {msg}")
                
        return 0 if error_count == 0 else 1
        
    except Exception as e:
        logger.exception(f"予期せぬエラーが発生しました: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())