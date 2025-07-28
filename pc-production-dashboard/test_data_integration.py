"""
PC製造専用ダッシュボード - データ統合テスト

過去データの読み込みと統合処理をテスト
"""

import sys
from pathlib import Path

# アプリケーションパスを追加
app_path = Path(__file__).parent / "app"
sys.path.insert(0, str(app_path))

from data_loader import PCProductionDataLoader
import pandas as pd

def test_historical_data_loading():
    """過去データ読み込みテスト"""
    print("=" * 60)
    print("🧪 過去データ読み込みテスト")
    print("=" * 60)
    
    loader = PCProductionDataLoader()
    
    # 過去データの読み込み
    print("📂 過去データフォルダの確認...")
    historical_path = Path("data/zm29_Monthly_performance")
    
    if not historical_path.exists():
        print(f"❌ 過去データフォルダが見つかりません: {historical_path}")
        print("💡 claude-testから過去データをコピーしてください")
        return False
    
    files = list(historical_path.glob("ZM29_*.txt"))
    print(f"📁 見つかったファイル数: {len(files)}")
    
    for file in sorted(files):
        print(f"  - {file.name}")
    
    if not files:
        print("❌ ZM29_*.txtファイルが見つかりません")
        return False
    
    # データ読み込み実行
    print("\n🔄 過去データ読み込み実行...")
    historical_data = loader.load_historical_zm29_data()
    
    if historical_data.empty:
        print("❌ 過去データの読み込みに失敗しました")
        return False
    
    print(f"✅ 過去データ読み込み成功: {len(historical_data)}行")
    
    # データ内容の確認
    print("\n📊 データ内容確認:")
    print(f"  - カラム数: {len(historical_data.columns)}")
    print(f"  - データ年月: {sorted(historical_data['データ年月'].unique())}")
    
    if 'MRP管理者' in historical_data.columns:
        mrp_managers = historical_data['MRP管理者'].unique()
        pc_managers = [m for m in mrp_managers if 'PC' in str(m)]
        print(f"  - PC関連MRP管理者: {pc_managers}")
    
    # サンプルデータ表示
    print("\n📋 サンプルデータ（最初の3行）:")
    print(historical_data.head(3).to_string())
    
    return True

def test_data_processing():
    """データ処理テスト"""
    print("\n" + "=" * 60)
    print("🧪 データ処理テスト")
    print("=" * 60)
    
    loader = PCProductionDataLoader()
    
    # 過去データの読み込み
    historical_data = loader.load_historical_zm29_data()
    
    if historical_data.empty:
        print("❌ テスト用データがありません")
        return False
    
    # データ処理実行
    print("🔄 データ処理実行...")
    processed_data = loader.process_zm29_data(historical_data)
    
    if processed_data.empty:
        print("❌ データ処理に失敗しました")
        return False
    
    print(f"✅ データ処理成功: {len(processed_data)}行")
    
    # 処理結果の確認
    print("\n📊 処理結果確認:")
    
    if '転記日付' in processed_data.columns:
        date_range = processed_data['転記日付'].dropna()
        if not date_range.empty:
            print(f"  - 日付範囲: {date_range.min()} ～ {date_range.max()}")
    
    if '月別週区分' in processed_data.columns:
        week_dist = processed_data['月別週区分'].value_counts().sort_index()
        print(f"  - 週区分分布: {dict(week_dist)}")
    
    if '金額' in processed_data.columns:
        total_amount = processed_data['金額'].sum()
        print(f"  - 総金額: ¥{total_amount:,.0f}")
    
    # PC製造データのフィルタリング確認
    if 'MRP管理者' in processed_data.columns:
        pc_data = processed_data[processed_data['MRP管理者'].str.contains('PC', na=False)]
        print(f"  - PC製造データ: {len(pc_data)}行")
    
    return True

def test_database_save():
    """データベース保存テスト"""
    print("\n" + "=" * 60)
    print("🧪 データベース保存テスト")
    print("=" * 60)
    
    loader = PCProductionDataLoader()
    
    # テストデータの作成
    test_data = pd.DataFrame({
        'MRP管理者': ['PC1', 'PC2', 'PC3'],
        '転記日付': ['2025-01-28', '2025-01-28', '2025-01-28'],
        '品目コード': ['TEST001', 'TEST002', 'TEST003'],
        '完成数': [10, 20, 30],
        '単価': [1000, 2000, 3000],
        '金額': [10000, 40000, 90000],
        'データソース': ['テストデータ', 'テストデータ', 'テストデータ']
    })
    
    print(f"🔄 テストデータ保存実行... ({len(test_data)}行)")
    
    # データベース保存
    loader.save_to_database(test_data, 'test_pc_production')
    
    # 保存確認
    import sqlite3
    try:
        conn = sqlite3.connect(loader.db_path)
        
        # テーブル存在確認
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='test_pc_production'")
        table_exists = cursor.fetchone() is not None
        
        if table_exists:
            # データ確認
            cursor.execute("SELECT COUNT(*) FROM test_pc_production")
            row_count = cursor.fetchone()[0]
            print(f"✅ データベース保存成功: {row_count}行")
            
            # サンプルデータ取得
            cursor.execute("SELECT * FROM test_pc_production LIMIT 2")
            sample_data = cursor.fetchall()
            print("📋 保存されたサンプルデータ:")
            for row in sample_data:
                print(f"  {row}")
        else:
            print("❌ テーブルが作成されませんでした")
        
        conn.close()
        return table_exists
        
    except Exception as e:
        print(f"❌ データベース確認エラー: {e}")
        return False

def copy_historical_data():
    """claude-testから過去データをコピー"""
    print("\n" + "=" * 60)
    print("📂 過去データコピー")
    print("=" * 60)
    
    source_path = Path("../data/zm29_Monthly_performance")
    target_path = Path("data/zm29_Monthly_performance")
    
    if not source_path.exists():
        print(f"❌ ソースフォルダが見つかりません: {source_path}")
        return False
    
    # ターゲットフォルダ作成
    target_path.mkdir(parents=True, exist_ok=True)
    
    # ファイルコピー
    import shutil
    copied_count = 0
    
    for source_file in source_path.glob("ZM29_*.txt"):
        target_file = target_path / source_file.name
        
        try:
            shutil.copy2(source_file, target_file)
            print(f"✅ コピー完了: {source_file.name}")
            copied_count += 1
        except Exception as e:
            print(f"❌ コピーエラー: {source_file.name} - {e}")
    
    print(f"\n📁 コピー完了: {copied_count}ファイル")
    return copied_count > 0

def main():
    """メインテスト実行"""
    print("🧪 PC製造専用ダッシュボード - データ統合テスト")
    
    # 過去データのコピー（必要に応じて）
    historical_path = Path("data/zm29_Monthly_performance")
    if not historical_path.exists() or not list(historical_path.glob("ZM29_*.txt")):
        print("\n📂 過去データが見つかりません。claude-testからコピーします...")
        if not copy_historical_data():
            print("❌ 過去データのコピーに失敗しました")
            return
    
    # テスト実行
    tests = [
        ("過去データ読み込み", test_historical_data_loading),
        ("データ処理", test_data_processing),
        ("データベース保存", test_database_save)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}テストでエラー: {e}")
            results.append((test_name, False))
    
    # 結果サマリー
    print("\n" + "=" * 60)
    print("📊 テスト結果サマリー")
    print("=" * 60)
    
    for test_name, result in results:
        status = "✅ 成功" if result else "❌ 失敗"
        print(f"{test_name}: {status}")
    
    success_count = sum(1 for _, result in results if result)
    total_count = len(results)
    
    print(f"\n🏁 総合結果: {success_count}/{total_count} テスト成功")
    
    if success_count == total_count:
        print("🎉 すべてのテストが成功しました！")
        print("💡 次は 'python app/main.py' でダッシュボードを起動してください")
    else:
        print("⚠️ 一部のテストが失敗しました。エラーを確認してください")

if __name__ == "__main__":
    main()