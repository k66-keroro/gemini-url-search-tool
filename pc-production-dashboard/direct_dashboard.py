"""
PC製造専用ダッシュボード - 直接起動

既存データでダッシュボードを直接起動
"""

import subprocess
import sys
from pathlib import Path

def main():
    """ダッシュボード直接起動"""
    print("🏭 PC製造専用ダッシュボード - 直接起動")
    print("=" * 60)
    print("📊 ブラウザが自動で開きます")
    print("🔗 手動アクセス: http://localhost:8503")
    print("⏹️  停止: Ctrl+C")
    print("-" * 60)
    
    try:
        dashboard_path = Path(__file__).parent / "app" / "dashboard.py"
        
        # Streamlitダッシュボードを起動（ポート8503を使用）
        subprocess.run([
            sys.executable, '-m', 'streamlit', 'run', 
            str(dashboard_path),
            '--server.port=8503',
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