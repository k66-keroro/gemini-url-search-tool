import sys
from pathlib import Path
import logging
import pandas as pd
from typing import Dict, List
import sqlite3
import json
import os

# プロジェクトルートをsys.pathに追加
PROJECT_ROOT = str(Path(__file__).resolve().parents[1])
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from config.constants import Paths
from src.core.sqlite_manager import SQLiteManager
# 特殊処理プロセッサをインポート
from src.processors.zp138_processor import ZP138Processor

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Paths().LOGS / "main.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def get_index_definitions(file_path: Path) -> Dict[str, List[str]]:
    """インデックス定義ファイルからテーブル名とインデックス対象カラムのリストを読み込む"""
    index_info = {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            next(f) # ヘッダーをスキップ
            for line in f:
                parts = [p.strip() for p in line.strip().split('\t')]
                if len(parts) >= 2 and parts[0]:
                    table_name = parts[0].lower()
                    index_cols = [p for p in parts[1:3] if p]
                    if index_cols:
                        index_info[table_name] = index_cols
    except FileNotFoundError:
        logger.warning(f"インデックス定義ファイルが見つかりません: {file_path}")
    except Exception as e:
        logger.error(f"インデックス定義ファイルの読み込みに失敗しました: {e}")
    return index_info

def _sanitize_table_name(table_name: str) -> str:
    """
    テーブル名を適切に変換（日本語や特殊文字を避ける）
    
    Args:
        table_name: 元のテーブル名
        
    Returns:
        変換後のテーブル名
    """
    import re
    
    # 日本語文字を含むかチェック
    has_japanese = re.search(r'[ぁ-んァ-ン一-龥]', table_name)
    
    # 日本語文字を含む場合は、ローマ字に変換するか、プレフィックスを付ける
    if has_japanese:
        # 簡易的な変換: 日本語テーブル名にはt_を付ける
        sanitized = f"t_{hash(table_name) % 10000:04d}"
    else:
        # 英数字以外の文字を_に置換
        sanitized = re.sub(r'[^a-zA-Z0-9]', '_', table_name)
        
        # 連続する_を単一の_に置換
        sanitized = re.sub(r'_+', '_', sanitized)
        
        # 先頭が数字の場合、t_を付ける
        if sanitized[0].isdigit():
            sanitized = f"t_{sanitized}"
            
        # 先頭と末尾の_を削除
        sanitized = sanitized.strip('_')
        
    return sanitized

def run_priority_batch_import():
    """
    ファイルを一括でSQLiteに格納し、各テーブルの構造を最終化（主キー追加＋インデックス作成）します。
    """
    try:
        paths = Paths()
        priority_csv_path = paths.PROJECT_ROOT / 'config' / 'テキスト一覧.csv'
        index_def_path = paths.PROJECT_ROOT / 'config' / 'index_definitions.txt'
        db_path = paths.SQLITE_DB
        raw_dir = paths.RAW_DATA
    except Exception as e:
        logger.error(f"❌ 設定の読み込みに失敗しました: {e}")
        return False

    if not priority_csv_path.exists() or not raw_dir.exists():
        logger.error(f"❌ 優先順位ファイルまたはデータディレクトリが見つかりません。")
        return False

    logger.info(f"▶️ バッチ処理を開始します - DB: {db_path}")

    manager = SQLiteManager(db_path)
    index_definitions = get_index_definitions(index_def_path)
    if index_definitions:
        logger.info(f"🔑 インデックス定義を読み込みました: {len(index_definitions)}件")

    try:
        df_priority = pd.read_csv(priority_csv_path)
        df_priority['重要度'] = df_priority['重要度'].fillna('')
        priority_map = {'zz': 0, 'z': 1}
        df_priority['sort_key'] = df_priority['重要度'].map(priority_map).fillna(99)
        df_priority = df_priority.sort_values(by='sort_key').reset_index(drop=True)
        logger.info(f"📊 処理対象ファイル数: {len(df_priority)}")
    except Exception as e:
        logger.error(f"❌ 優先順位CSVの読み込みに失敗しました: {e}")
        return False

    success_files, failed_files, skipped_files, structure_failed_tables = [], [], [], []
    total_files = len(df_priority)

    for i, row in df_priority.iterrows():
        file_name = row.get('ファイル名')
        table_name_orig = row.get('テーブル名')

        if not file_name or not table_name_orig:
            logger.warning(f"⚠️ {i+1}行目: 'ファイル名'または'テーブル名'が不足しているためスキップします。")
            continue
        
        # テーブル名を適切に変換（日本語や特殊文字を避ける）
        table_name = _sanitize_table_name(str(table_name_orig).lower())
        file_path = raw_dir / str(file_name)
        logger.info(f"--- 処理中 ({i+1}/{total_files}): {file_name} -> {table_name} ---")
        
        # 元のテーブル名と変換後のテーブル名が異なる場合はログに記録
        if table_name != str(table_name_orig).lower():
            logger.info(f"テーブル名を変換しました: {table_name_orig} -> {table_name}")

        if not file_path.exists():
            logger.warning(f"⚠️ ファイルが見つからないためスキップします: {file_path}")
            skipped_files.append(file_name)
            continue

        # ファイル処理設定を取得
        config = manager.get_file_processing_config(file_name)
        index_cols = index_definitions.get(table_name, [])
        
        # データベース接続を確立
        with sqlite3.connect(db_path) as conn:
            # ファイルをインポート
            success, error_message = manager.bulk_insert_from_file(
                conn=conn,
                file_path=file_path,
                table_name=table_name,
                encoding=config['encoding'],
                quoting=config['quoting']
            )
            
            if not success:
                failed_files.append(file_name)
                logger.error(f"❌ ファイル処理失敗: {file_name} - {error_message}")
                continue
            
            # テーブル構造を最終化（主キー追加＋インデックス作成）
            success2, error_message2 = manager.finalize_table_structure(
                conn=conn,
                table_name=table_name,
                primary_key_columns=None,  # _rowid_を使用
                index_columns=index_cols
            )
            
            if not success2:
                structure_failed_tables.append(table_name)
                logger.error(f"❌ 構造最終化失敗: {table_name} - {error_message2}")
                continue
        
        success_files.append(file_name)
        logger.info(f"✅ ファイル処理成功: {file_name}")

    # 最終サマリーレポート
    logger.info("🎉 全ての処理が完了しました。")
    
    summary_report = f"""
=== 処理サマリー ===
  📊 対象ファイル総数: {total_files}
  ✅ 成功: {len(success_files)}
  ❌ 失敗: {len(failed_files)}
  ⏭️ スキップ: {len(skipped_files)}
  ⚠️ 構造最終化失敗: {len(structure_failed_tables)}
"""
    print(summary_report)
    
    if failed_files:
        print("\n--- 失敗したファイル ---")
        for f in failed_files: print(f"  ❌ {f}")
            
    if skipped_files:
        print("\n--- スキップされたファイル ---")
        for f in skipped_files: print(f"  ⏭️ {f}")
        
    if structure_failed_tables:
        print("\n--- 構造最終化に失敗したテーブル ---")
        for t in structure_failed_tables: print(f"  ⚠️ {t}")

    return len(failed_files) == 0 and len(structure_failed_tables) == 0


def run_special_processors(config_path=None):
    """
    特殊処理プロセッサを実行します。
    
    Args:
        config_path: 設定ファイルのパス（オプション）
    
    Returns:
        bool: すべての処理が成功した場合はTrue、それ以外はFalse
    """
    # デフォルト設定
    config = {
        "processors": {
            "zp138": {
                "enabled": True,
                "config_file": "config/processors/zp138_config.json"
            }
        }
    }
    
    # 設定ファイルがある場合は読み込む
    if config_path and os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                file_config = json.load(f)
                # 設定をマージ
                if "processors" in file_config:
                    config["processors"].update(file_config["processors"])
        except Exception as e:
            logger.error(f"設定ファイルの読み込みに失敗しました: {e}")
    
    success = True
    
    # ZP138プロセッサの実行
    if config["processors"].get("zp138", {}).get("enabled", False):
        logger.info("🔄 ZP138特殊処理を開始します")
        
        # ZP138の設定ファイルを読み込む
        zp138_config = {}
        config_file = config["processors"]["zp138"].get("config_file")
        
        if config_file and os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    zp138_config = json.load(f)
            except Exception as e:
                logger.error(f"ZP138設定ファイルの読み込みに失敗しました: {e}")
        
        # ZP138プロセッサを実行
        processor = ZP138Processor(zp138_config)
        if not processor.process():
            logger.error("❌ ZP138処理に失敗しました")
            success = False
        else:
            logger.info("✅ ZP138処理が完了しました")
    
    return success

if __name__ == "__main__":
    try:
        # コマンドライン引数の解析
        import argparse
        parser = argparse.ArgumentParser(description='データ更新処理バッチ')
        parser.add_argument('--special-only', action='store_true', help='特殊処理のみを実行')
        parser.add_argument('--config', help='設定ファイルのパス')
        args = parser.parse_args()
        
        is_successful = True
        
        # 標準バッチ処理
        if not args.special_only:
            logger.info("🔄 標準バッチ処理を開始します")
            is_successful = run_priority_batch_import()
            
        # 特殊処理
        logger.info("🔄 特殊処理を開始します")
        special_success = run_special_processors(args.config)
        is_successful = is_successful and special_success
        
        exit_code = 0 if is_successful else 1
        logger.info(f"🏁 プログラム終了 (終了コード: {exit_code})")
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("⏹️ ユーザーによって処理が中断されました。")
        sys.exit(130)
    except Exception as e:
        logger.exception(f"💥 予期せぬエラーが発生しました: {e}")
        sys.exit(1)