"""
修正版データローダーでデータベースを強制更新
"""

import sys
from pathlib import Path

# アプリケーションパスを追加
app_path = Path(__file__).parent / "app"
sys.path.insert(0, str(app_path))

def main():
    """修正版データローダーでデータベース更新"""
    print("=" * 60)
    print("修正版データローダーでデータベース更新")
    print("=" * 60)
    
    try:
        from data_loader_fixed import PCProductionDataLoaderFixed
        
        # 修正版データローダーの実行
        loader = PCProductionDataLoaderFixed()
        result = loader.integrate_all_data()
        
        if not result.empty:
            print(f"✅ データ更新成功: {len(result)}行")
            
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
            
            # サンプルデータ表示
            print(f"\n📋 サンプルデータ:")
            sample = result[['品目コード', '完成数', '単価', '金額']].head(3)
            print(sample.to_string())
            
            print(f"\n✅ データベース更新完了: {loader.db_path}")
            
        else:
            print("❌ データ更新に失敗しました")
            
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()