"""
データベースの問題を修正するスクリプト
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from app.data_loader_simple import PCProductionDataLoaderSimple

def main():
    print("=" * 60)
    print("PC製造データベース修正処理")
    print("=" * 60)
    
    # データローダーを初期化
    loader = PCProductionDataLoaderSimple()
    
    # データ統合処理を実行
    try:
        result = loader.integrate_all_data()
        if result is not None and not result.empty:
            print(f"✅ データ統合成功: {len(result)}行")
            print(f"カラム一覧: {list(result.columns)}")
        else:
            print("❌ データ統合失敗: 結果が空です")
    except Exception as e:
        print(f"❌ データ統合エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()