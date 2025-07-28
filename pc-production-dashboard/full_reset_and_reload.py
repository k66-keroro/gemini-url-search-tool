"""
完全リセット＆リロード
"""

import sys
from pathlib import Path
import sqlite3

# アプリケーションパスを追加
app_path = Path(__file__).parent / "app"
sys.path.insert(0, str(app_path))

def reset_database():
    """データベースを完全リセット"""
    print("Step 1: データベースリセット")
    print("-" * 40)
    
    db_path = Path("pc-production-dashboard/data/sqlite/pc_production.db")
    
    try:
        if db_path.exists():
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 全テーブルを削除
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            for table in tables:
                cursor.execute(f"DROP TABLE IF EXISTS {table[0]}")
                print(f"  ✅ テーブル削除: {table[0]}")
            
            conn.commit()
            conn.close()
            print("✅ データベースリセット完了")
        else:
            print("📁 新規データベースを作成します")
            
    except Exception as e:
        print(f"❌ リセットエラー: {e}")

def reload_data():
    """シンプル版でデータを再読み込み"""
    print("\nStep 2: データ再読み込み")
    print("-" * 40)
    
    try:
        from data_loader_simple import PCProductionDataLoaderSimple
        
        loader = PCProductionDataLoaderSimple()
        result = loader.integrate_all_data()
        
        if not result.empty:
            print(f"✅ データ読み込み成功: {len(result)}行")
            
            # 数値データの確認
            numeric_summary = {}
            for col in ['完成数', '単価', '金額']:
                if col in result.columns:
                    total = result[col].sum()
                    avg = result[col].mean()
                    numeric_summary[col] = {'合計': total, '平均': avg}
            
            print("📊 数値データサマリー:")
            for col, stats in numeric_summary.items():
                print(f"  {col}: 合計={stats['合計']:,.0f}, 平均={stats['平均']:.0f}")
            
            return True
        else:
            print("❌ データ読み込み失敗")
            return False
            
    except Exception as e:
        print(f"❌ データ読み込みエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_database():
    """データベース内容を検証"""
    print("\nStep 3: データベース検証")
    print("-" * 40)
    
    db_path = Path("pc-production-dashboard/data/sqlite/pc_production.db")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # テーブル一覧
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"📊 テーブル一覧: {[table[0] for table in tables]}")
        
        # pc_production_zm29テーブルの詳細
        if ('pc_production_zm29',) in tables:
            # カラム情報
            cursor.execute("PRAGMA table_info(pc_production_zm29)")
            columns = cursor.fetchall()
            print(f"📋 カラム一覧:")
            for col in columns:
                print(f"  - {col[1]} ({col[2]})")
            
            # データ件数
            cursor.execute("SELECT COUNT(*) FROM pc_production_zm29")
            count = cursor.fetchone()[0]
            print(f"📈 総件数: {count}行")
            
            # 数値データの確認
            for col_name in ['完成数', '単価', '金額']:
                try:
                    cursor.execute(f"SELECT COUNT(*), MIN({col_name}), MAX({col_name}), AVG({col_name}) FROM pc_production_zm29 WHERE {col_name} > 0")
                    stats = cursor.fetchone()
                    if stats and stats[0] > 0:
                        print(f"  {col_name}: 件数={stats[0]}, 最小={stats[1]}, 最大={stats[2]}, 平均={stats[3]:.2f}")
                    else:
                        print(f"  {col_name}: データなし")
                except Exception as e:
                    print(f"  {col_name}: カラムなし")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 検証エラー: {e}")
        return False

def main():
    """完全リセット＆リロード実行"""
    print("=" * 60)
    print("PC製造ダッシュボード - 完全リセット＆リロード")
    print("=" * 60)
    
    # Step 1: データベースリセット
    reset_database()
    
    # Step 2: データ再読み込み
    success = reload_data()
    
    if success:
        # Step 3: 検証
        verify_database()
        
        print("\n" + "=" * 60)
        print("🎉 完全リセット＆リロード完了！")
        print("💡 ダッシュボードを再起動してください")
        print("=" * 60)
    else:
        print("\n❌ リロードに失敗しました")

if __name__ == "__main__":
    main()