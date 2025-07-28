"""
PC製造専用ダッシュボード - メインエントリーポイント

Embeddable-Python環境での実行用
"""

import sys
import subprocess
from pathlib import Path
import os

def setup_environment():
    """環境設定"""
    # 現在のディレクトリをPythonパスに追加
    current_dir = Path(__file__).parent
    if str(current_dir) not in sys.path:
        sys.path.insert(0, str(current_dir))
    
    # データフォルダの作成
    data_folders = [
        "data/sqlite",
        "data/current",
        "data/historical"
    ]
    
    for folder in data_folders:
        Path(folder).mkdir(parents=True, exist_ok=True)

def install_required_packages():
    """必要なパッケージのインストール"""
    required_packages = [
        'streamlit',
        'plotly',
        'pandas',
        'numpy',
        'chardet'
    ]
    
    print("📦 必要なパッケージを確認中...")
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} は既にインストールされています")
        except ImportError:
            print(f"📦 {package} をインストール中...")
            try:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
                print(f"✅ {package} のインストールが完了しました")
            except subprocess.CalledProcessError as e:
                print(f"❌ {package} のインストールに失敗しました: {e}")
                return False
    
    return True

def run_data_integration():
    """データ統合処理の実行"""
    print("\n🔄 データ統合処理を開始...")
    
    try:
        from data_loader import PCProductionDataLoader
        
        loader = PCProductionDataLoader()
        result = loader.integrate_all_data()
        
        if not result.empty:
            print(f"✅ データ統合完了: {len(result)}行")
            return True
        else:
            print("⚠️ 統合するデータがありませんでした")
            return False
            
    except Exception as e:
        print(f"❌ データ統合エラー: {e}")
        return False

def run_dashboard():
    """ダッシュボードの起動"""
    print("\n🚀 PC製造専用ダッシュボードを起動中...")
    print("📊 ブラウザが自動で開きます")
    print("🔗 手動でアクセスする場合: http://localhost:8502")
    print("⏹️  停止するには Ctrl+C を押してください")
    print("-" * 60)
    
    try:
        # Streamlitダッシュボードを実行
        dashboard_path = Path(__file__).parent / "dashboard.py"
        
        subprocess.run([
            sys.executable, '-m', 'streamlit', 'run', 
            str(dashboard_path),
            '--server.port=8502',
            '--server.address=localhost',
            '--server.headless=false'
        ])
        
    except KeyboardInterrupt:
        print("\n\n✅ ダッシュボードを正常に停止しました")
    except Exception as e:
        print(f"\n❌ ダッシュボード起動エラー: {e}")

def show_menu():
    """メニュー表示"""
    print("=" * 60)
    print("🏭 PC製造専用ダッシュボード")
    print("=" * 60)
    print("1. データ統合 + ダッシュボード起動（推奨）")
    print("2. データ統合のみ実行")
    print("3. ダッシュボードのみ起動")
    print("4. 終了")
    print("-" * 60)
    
    while True:
        try:
            choice = input("選択してください (1-4): ").strip()
            if choice in ['1', '2', '3', '4']:
                return int(choice)
            else:
                print("❌ 1-4の数字を入力してください")
        except KeyboardInterrupt:
            print("\n\n👋 プログラムを終了します")
            return 4

def main():
    """メイン関数"""
    print("🔧 環境設定中...")
    setup_environment()
    
    # パッケージインストール
    if not install_required_packages():
        print("❌ 必要なパッケージのインストールに失敗しました")
        input("Enterキーを押して終了...")
        return
    
    # メニュー表示
    choice = show_menu()
    
    if choice == 1:
        # データ統合 + ダッシュボード起動
        if run_data_integration():
            run_dashboard()
        else:
            print("❌ データ統合に失敗したため、ダッシュボードを起動できません")
            input("Enterキーを押して終了...")
    
    elif choice == 2:
        # データ統合のみ
        run_data_integration()
        input("Enterキーを押して終了...")
    
    elif choice == 3:
        # ダッシュボードのみ
        run_dashboard()
    
    elif choice == 4:
        # 終了
        print("👋 お疲れさまでした！")
    
    print("\n🏁 プログラムを終了します")

if __name__ == "__main__":
    main()