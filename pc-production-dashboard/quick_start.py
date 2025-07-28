"""
PC製造専用ダッシュボード - クイックスタート

データ統合とダッシュボード起動を自動実行
"""

import sys
from pathlib import Path
import subprocess

# アプリケーションパスを追加
app_path = Path(__file__).parent / "app"
sys.path.insert(0, str(app_path))

def main():
    """クイックスタート実行"""
    print("🏭 PC製造専用ダッシュボード - クイックスタート")
    print("=" * 60)
    
    # Step 1: データ統合実行
    print("🔄 Step 1: データ統合実行中...")
    try:
        from data_loader import PCProductionDataLoader
        
        loader = PCProductionDataLoader()
        result = loader.integrate_all_data()
        
        if not result.empty:
            print(f"✅ データ統合完了: {len(result)}行")
            pc_data = result[result['MRP管理者'].str.contains('PC', na=False)]
            print(f"🏭 PC製造データ: {len(pc_data)}行")
            print(f"💰 総生産金額: ¥{pc_data['金額'].sum():,.0f}")
        else:
            print("⚠️ 統合データが空です")
            
    except Exception as e:
        print(f"❌ データ統合エラー: {e}")
        print("💡 既存データでダッシュボードを起動します...")
    
    # Step 2: ダッシュボード起動
    print("\n🚀 Step 2: ダッシュボード起動中...")
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
            '--server.address=localhost',
            '--server.headless=false'
        ])
        
    except KeyboardInterrupt:
        print("\n\n✅ ダッシュボードを正常に停止しました")
        print("👋 お疲れさまでした！")
    except Exception as e:
        print(f"\n❌ ダッシュボード起動エラー: {e}")

if __name__ == "__main__":
    main()