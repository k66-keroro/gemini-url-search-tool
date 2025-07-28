"""
シンプル版データローダーのテスト実行
"""

import sys
from pathlib import Path

# アプリケーションパスを追加
app_path = Path(__file__).parent / "app"
sys.path.insert(0, str(app_path))

def main():
    """シンプル版データローダーのテスト"""
    print("=" * 60)
    print("シンプル版データローダーテスト")
    print("=" * 60)
    
    try:
        from data_loader_simple import PCProductionDataLoaderSimple
        
        # シンプル版データローダーの実行
        loader = PCProductionDataLoaderSimple()
        result = loader.integrate_all_data()
        
        if not result.empty:
            print(f"✅ データ統合成功: {len(result)}行")
            
            # 数値データの確認
            if '完成数' in result.columns:
                total_qty = result['完成数'].sum()
                print(f"📊 総完成数: {total_qty}")
            
            if '金額' in result.columns:
                total_amount = result['金額'].sum()
                print(f"💰 総金額: ¥{total_amount:,.0f}")
            
            if '単価' in result.columns:
                avg_price = result['単価'].mean()
                print(f"💱 平均単価: ¥{avg_price:.0f}")
            
            # カラム一覧
            print(f"📋 カラム一覧: {list(result.columns)}")
            
            # サンプルデータ表示
            print(f"\n📝 サンプルデータ:")
            if '品目コード' in result.columns:
                sample_cols = ['品目コード', '完成数', '単価', '金額', 'MRP管理者']
                available_cols = [col for col in sample_cols if col in result.columns]
                sample = result[available_cols].head(3)
                print(sample.to_string())
            
            print(f"\n✅ データベース更新完了: {loader.db_path}")
            
        else:
            print("❌ データ統合に失敗しました")
            
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()