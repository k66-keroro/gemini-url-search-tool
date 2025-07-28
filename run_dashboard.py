"""
PC生産実績ダッシュボード実行スクリプト

使用方法:
python run_dashboard.py
"""

import subprocess
import sys
from pathlib import Path
import os

def install_requirements():
    """必要なパッケージをインストール"""
    required_packages = [
        'streamlit',
        'plotly',
        'pandas',
        'numpy'
    ]
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} は既にインストールされています")
        except ImportError:
            print(f"📦 {package} をインストール中...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
            print(f"✅ {package} のインストールが完了しました")

def run_dashboard():
    """ダッシュボードを実行"""
    dashboard_path = Path("streamlit_apps/pc_production_dashboard.py")
    
    if not dashboard_path.exists():
        print(f"❌ ダッシュボードファイルが見つかりません: {dashboard_path}")
        return
    
    print("🚀 PC生産実績ダッシュボードを起動中...")
    print("📊 ブラウザが自動で開きます")
    print("🔗 手動でアクセスする場合: http://localhost:8501")
    print("⏹️  停止するには Ctrl+C を押してください")
    print("-" * 50)
    
    # Streamlitアプリを実行
    subprocess.run([
        sys.executable, '-m', 'streamlit', 'run', 
        str(dashboard_path),
        '--server.port=8501',
        '--server.address=localhost'
    ])

def main():
    """メイン関数"""
    print("=" * 50)
    print("📊 PC生産実績ダッシュボード")
    print("=" * 50)
    
    # 必要なパッケージをインストール
    print("\n1️⃣ 依存パッケージの確認...")
    install_requirements()
    
    # データベースファイルの確認
    print("\n2️⃣ データベースファイルの確認...")
    db_path = Path("data/sqlite/main.db")
    if db_path.exists():
        print(f"✅ データベースファイルが見つかりました: {db_path}")
        file_size = db_path.stat().st_size / (1024 * 1024)  # MB
        print(f"📁 ファイルサイズ: {file_size:.2f} MB")
    else:
        print(f"❌ データベースファイルが見つかりません: {db_path}")
        print("💡 先に全件データ更新を実行してください")
        return
    
    # ダッシュボード実行
    print("\n3️⃣ ダッシュボードの起動...")
    try:
        run_dashboard()
    except KeyboardInterrupt:
        print("\n\n✅ ダッシュボードを正常に停止しました")
        print("👋 お疲れさまでした！")
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")

if __name__ == "__main__":
    main()