"""
PC製造専用ダッシュボード - 修正版データローダーテスト
"""

import sys
from pathlib import Path

# アプリケーションパスを追加
app_path = Path(__file__).parent / "app"
sys.path.insert(0, str(app_path))

def main():
    """修正版データローダーのテスト"""
    print("=" * 60)
    print("PC製造専用ダッシュボード - 修正版テスト")
    print("=" * 60)
    
    try:
        from data_loader_fixed import PCProductionDataLoaderFixed
        
        # データローダーの初期化
        loader = PCProductionDataLoaderFixed()
        
        # データ統合実行
        result = loader.integrate_all_data()
        
        if not result.empty:
            print(f"成功: {len(result)}行のデータを統合しました")
            print(f"データベース: {loader.db_path}")
            
            # 結果の詳細表示
            if 'MRP管理者' in result.columns:
                mrp_summary = result['MRP管理者'].value_counts()
                print(f"MRP管理者別件数:")
                for mrp, count in mrp_summary.items():
                    print(f"  {mrp}: {count}件")
            
            if '金額' in result.columns:
                total_amount = result['金額'].sum()
                print(f"総生産金額: {total_amount:,.0f}円")
            
            if '月別週区分' in result.columns:
                week_summary = result['月別週区分'].value_counts().sort_index()
                print(f"週区分別件数:")
                for week, count in week_summary.items():
                    print(f"  第{int(week)}週: {count}件")
        else:
            print("データ統合に失敗しました")
            
    except Exception as e:
        print(f"エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()