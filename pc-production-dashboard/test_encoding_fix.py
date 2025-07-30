#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
エンコーディング修正のテストスクリプト
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent / "app"))

from data_loader_simple import PCProductionDataLoaderSimple

def test_encoding_fix():
    """エンコーディング修正のテスト"""
    print("=" * 60)
    print("🔧 エンコーディング修正テスト")
    print("=" * 60)
    
    try:
        loader = PCProductionDataLoaderSimple()
        
        # 過去データの読み込みテスト
        print("\n📂 過去データ読み込みテスト...")
        historical_data = loader.load_historical_zm29_data()
        
        if not historical_data.empty:
            print(f"✅ 過去データ読み込み成功: {len(historical_data):,}行")
            print(f"📊 データ年月: {historical_data['データ年月'].unique()}")
        else:
            print("⚠️ 過去データが空です")
        
        # データベース統合テスト
        print("\n🔄 データ統合テスト...")
        result = loader.integrate_all_data()
        
        if result is not None and not result.empty:
            print(f"✅ データ統合成功: {len(result):,}行")
            
            # 基本統計
            print(f"📈 総生産金額: ¥{result['生産金額'].sum():,.0f}")
            print(f"🏭 品目数: {result['品目コード'].nunique():,}品目")
            print(f"📅 期間: {result['完成日'].min()} ～ {result['完成日'].max()}")
            
            return True
        else:
            print("❌ データ統合に失敗しました")
            return False
            
    except Exception as e:
        print(f"❌ テスト中にエラーが発生: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_encoding_fix()
    
    if success:
        print("\n🎉 エンコーディング修正テスト完了！")
        print("💡 ダッシュボードを起動してください:")
        print("   python -m streamlit run app/dashboard.py --server.port 8506")
    else:
        print("\n❌ テストに失敗しました")
    
    input("\nEnterキーを押して終了...")