"""
PC製造専用ダッシュボード - データフォルダセットアップ

過去データのコピーとフォルダ構成の修正
"""

import shutil
from pathlib import Path
import os

def setup_data_folders():
    """データフォルダの設定"""
    print("📁 データフォルダセットアップ開始")
    print("=" * 50)
    
    base_dir = Path(__file__).parent
    
    # 必要なフォルダを作成
    folders_to_create = [
        "data/sqlite",
        "data/current", 
        "data/zm29_Monthly_performance"
    ]
    
    for folder in folders_to_create:
        folder_path = base_dir / folder
        folder_path.mkdir(parents=True, exist_ok=True)
        print(f"✅ フォルダ作成: {folder}")
    
    # claude-testから過去データをコピー
    source_path = Path("../data/zm29_Monthly_performance")
    target_path = base_dir / "data/zm29_Monthly_performance"
    
    if source_path.exists():
        print(f"\n📂 過去データコピー: {source_path} → {target_path}")
        
        copied_count = 0
        for source_file in source_path.glob("ZM29_*.txt"):
            target_file = target_path / source_file.name
            
            try:
                shutil.copy2(source_file, target_file)
                print(f"  ✅ {source_file.name}")
                copied_count += 1
            except Exception as e:
                print(f"  ❌ {source_file.name}: {e}")
        
        print(f"\n📊 コピー完了: {copied_count}ファイル")
    else:
        print(f"⚠️ ソースフォルダが見つかりません: {source_path}")
    
    # 現在のフォルダ構成を表示
    print(f"\n📋 現在のフォルダ構成:")
    for root, dirs, files in os.walk(base_dir / "data"):
        level = root.replace(str(base_dir), '').count(os.sep)
        indent = ' ' * 2 * level
        print(f"{indent}{os.path.basename(root)}/")
        subindent = ' ' * 2 * (level + 1)
        for file in files[:5]:  # 最初の5ファイルのみ表示
            print(f"{subindent}{file}")
        if len(files) > 5:
            print(f"{subindent}... and {len(files) - 5} more files")

def check_embeddable_python():
    """Embeddable-Python環境の確認"""
    print("\n🐍 Python環境確認")
    print("=" * 50)
    
    import sys
    print(f"Python実行ファイル: {sys.executable}")
    print(f"Pythonバージョン: {sys.version}")
    print(f"実行パス: {sys.path[0]}")
    
    # Embeddable-Python特有のファイルをチェック
    python_dir = Path(sys.executable).parent
    embeddable_files = [
        "python311._pth",
        "python311.zip",
        "python311.dll"
    ]
    
    is_embeddable = False
    for file in embeddable_files:
        file_path = python_dir / file
        if file_path.exists():
            print(f"✅ Embeddable-Python: {file}")
            is_embeddable = True
        else:
            print(f"❌ 標準Python: {file} not found")
    
    if is_embeddable:
        print("🎯 Embeddable-Python環境で実行中")
    else:
        print("🔧 標準Python環境で実行中")

def main():
    """メイン実行"""
    print("🏭 PC製造専用ダッシュボード - セットアップ")
    
    # データフォルダセットアップ
    setup_data_folders()
    
    # Python環境確認
    check_embeddable_python()
    
    print("\n🎉 セットアップ完了！")
    print("💡 次は以下のコマンドでダッシュボードを起動してください:")
    print("   python app/main.py")

if __name__ == "__main__":
    main()