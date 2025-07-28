"""
PC製造専用ダッシュボード - 統合テスト実行

データ統合からダッシュボード起動まで自動実行
"""

import sys
from pathlib import Path

# アプリケーションパスを追加
app_path = Path(__file__).parent / "app"
sys.path.insert(0, str(app_path))

from data_loader import PCProductionDataLoader
import subprocess
import time

def run_full_integration():
    """完全なデータ統合処理を実行"""
    print("🏭 PC製造専用ダッシュボード - 統合処理開始")
    print("=" * 60)
    
    # データローダーの初期化
    loader = PCProductionDataLoader()
    
    # 統合処理実行
    print("🔄 データ統合処理実行中...")
    result = loader.integrate_all_data()
    
    if not result.empty:
        print(f"✅ データ統合完了: {len(result)}行")
        print(f"📊 データ期間: {result['転記日付'].min()} ～ {result['転記日付'].max()}")
        
        # PC製造データの確認
        pc_data = result[result['MRP管理者'].str.contains('PC', na=False)]
        print(f"🏭 PC製造データ: {len(pc_data)}行")
        
        if 'MRP管理者' in pc_data.columns:
            mrp_managers = sorted(pc_data['MRP管理者'].unique())
            print(f"👥 MRP管理者: {mrp_managers}")
        
        # 月別週区分の確認
        if '月別週区分' in pc_data.columns:
            week_dist = pc_data['月別週区分'].value_counts().sort_index()
            print(f"📅 週区分分布: {dict(week_dist)}")
        
        # 金額サマリー
        if '金額' in pc_data.columns:
            total_amount = pc_data['金額'].sum()
            print(f"💰 総生産金額: ¥{total_amount:,.0f}")
        
        return True
    else:
        print("❌ データ統合に失敗しました")
        return False

def launch_dashboard():
    """ダッシュボードを起動"""
    print("\n🚀 ダッシュボード起動中...")
    print("📊 ブラウザが自動で開きます")
    print("🔗 手動アクセス: http://localhost:8502")
    print("⏹️  停止: Ctrl+C")
    print("-" * 60)
    
    try:
        dashboard_path = Path(__file__).parent / "app" / "dashboard.py"
        
        # Streamlitダッシュボードを起動
        subprocess.run([
            sys.executable, '-m', 'streamlit', 'run', 
            str(dashboard_path),
            '--server.port=8502',
            '--server.address=localhost'
        ])
        
    except KeyboardInterrupt:
        print("\n\n✅ ダッシュボードを正常に停止しました")
        print("👋 お疲れさまでした！")
    except Exception as e:
        print(f"\n❌ ダッシュボード起動エラー: {e}")

def main():
    """メイン実行"""
    # Step 1: データ統合
    success = run_full_integration()
    
    if success:
        print("\n" + "=" * 60)
        print("🎉 データ統合が完了しました！")
        print("💡 ダッシュボードを起動します...")
        print("=" * 60)
        
        # 少し待機
        time.sleep(2)
        
        # Step 2: ダッシュボード起動
        launch_dashboard()
    else:
        print("\n❌ データ統合に失敗したため、処理を終了します")
        input("Enterキーを押して終了...")

if __name__ == "__main__":
    main()