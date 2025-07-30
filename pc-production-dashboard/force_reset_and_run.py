#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
強制リセット + データ統合 + ダッシュボード起動
"""

import os
import sys
import sqlite3
import subprocess
import time
from pathlib import Path

def force_reset():
    """データベースを強制リセット"""
    print("🔄 データベースを強制リセット中...")
    
    db_path = Path("data/sqlite/pc_production.db")
    
    # 複数回試行してデータベースを削除
    for attempt in range(5):
        try:
            if db_path.exists():
                # ファイルを読み取り専用から変更
                os.chmod(str(db_path), 0o777)
                db_path.unlink()
                print("✅ データベースファイルを削除しました")
                break
        except Exception as e:
            print(f"⚠️ 削除試行 {attempt + 1}/5: {e}")
            time.sleep(1)
    
    # ディレクトリを作成
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 新しい空のデータベースを作成
    try:
        conn = sqlite3.connect(str(db_path))
        conn.execute("PRAGMA journal_mode=WAL")
        conn.close()
        print("✅ 新しいデータベースを作成しました")
        return True
    except Exception as e:
        print(f"❌ データベース作成エラー: {e}")
        return False

def run_data_integration():
    """データ統合を実行"""
    print("🔄 データ統合を実行中...")
    
    try:
        # data_loader_simpleを直接インポートして実行
        sys.path.append(str(Path(__file__).parent / "app"))
        from data_loader_simple import PCProductionDataLoaderSimple
        
        loader = PCProductionDataLoaderSimple()
        result = loader.integrate_all_data()
        
        if result is not None and not result.empty:
            print(f"✅ データ統合完了: {len(result):,}行")
            return True
        else:
            print("❌ データ統合に失敗しました")
            return False
            
    except Exception as e:
        print(f"❌ データ統合エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_dashboard():
    """ダッシュボードを起動"""
    print("🚀 ダッシュボードを起動中...")
    print("📊 ブラウザが自動で開きます")
    print("🔗 URL: http://localhost:8508")
    print("⏹️  停止するには Ctrl+C を押してください")
    print("-" * 60)
    
    try:
        cmd = [sys.executable, "-m", "streamlit", "run", "standalone_dashboard.py", "--server.port", "8508"]
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n⏹️  ダッシュボードを停止しました")
    except Exception as e:
        print(f"❌ ダッシュボード起動エラー: {e}")

def main():
    """メイン処理"""
    print("=" * 60)
    print("🏭 PC製造専用ダッシュボード - 強制リセット版")
    print("=" * 60)
    
    # 1. データベースリセット
    if not force_reset():
        print("❌ データベースリセットに失敗しました")
        return
    
    # 2. データ統合
    if not run_data_integration():
        print("❌ データ統合に失敗しました")
        return
    
    # 3. ダッシュボード起動
    run_dashboard()

if __name__ == "__main__":
    main()