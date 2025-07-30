"""
重複除去機能のテスト

zm29とKANSEI_JISSEKIの重複データを確認し、
KANSEI_JISSEKIを優先した重複除去が正しく動作するかテストする
"""

import pandas as pd
import sqlite3
from pathlib import Path
import sys
import os

# パスの設定
base_dir = Path(__file__).parent
sys.path.append(str(base_dir / "app"))

from data_loader_simple import PCProductionDataLoaderSimple

def analyze_duplication():
    """重複データの分析"""
    print("=== 重複データ分析開始 ===")
    
    db_path = base_dir / "data" / "sqlite" / "pc_production.db"
    
    if not db_path.exists():
        print("データベースファイルが見つかりません")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        
        # 現在のデータを確認
        df = pd.read_sql_query("SELECT * FROM pc_production_zm29", conn)
        print(f"総データ数: {len(df)}行")
        
        # データソース別の件数
        if 'データソース' in df.columns:
            source_counts = df['データソース'].value_counts()
            print("\nデータソース別件数:")
            for source, count in source_counts.items():
                print(f"  {source}: {count}行")
        
        # 重複の可能性がある指図番号を確認
        if 'ネットワーク・指図番号' in df.columns:
            duplicate_orders = df['ネットワーク・指図番号'].value_counts()
            duplicates = duplicate_orders[duplicate_orders > 1]
            
            if not duplicates.empty:
                print(f"\n重複の可能性がある指図番号: {len(duplicates)}件")
                print("上位5件:")
                for order_no, count in duplicates.head().items():
                    print(f"  {order_no}: {count}回")
                    
                    # 具体的な重複データを表示
                    dup_data = df[df['ネットワーク・指図番号'] == order_no]
                    if 'データソース' in dup_data.columns:
                        sources = dup_data['データソース'].unique()
                        if len(sources) > 1:
                            print(f"    データソース: {', '.join(sources)}")
            else:
                print("\n重複する指図番号は見つかりませんでした")
        
        # 日付範囲の確認
        if '転記日付' in df.columns:
            df['転記日付'] = pd.to_datetime(df['転記日付'], errors='coerce')
            date_range = df['転記日付'].agg(['min', 'max'])
            print(f"\n日付範囲: {date_range['min']} ～ {date_range['max']}")
        
        conn.close()
        
    except Exception as e:
        print(f"分析エラー: {e}")

def test_deduplication():
    """重複除去機能のテスト"""
    print("\n=== 重複除去機能テスト ===")
    
    try:
        # データローダーを実行
        loader = PCProductionDataLoaderSimple()
        result_df = loader.integrate_all_data()
        
        if not result_df.empty:
            print(f"統合後データ数: {len(result_df)}行")
            
            # データソース別の確認
            if 'データソース' in result_df.columns:
                source_counts = result_df['データソース'].value_counts()
                print("\n統合後データソース別件数:")
                for source, count in source_counts.items():
                    print(f"  {source}: {count}行")
            
            # 重複チェック
            if 'ネットワーク・指図番号' in result_df.columns:
                duplicate_check = result_df['ネットワーク・指図番号'].value_counts()
                duplicates = duplicate_check[duplicate_check > 1]
                
                if not duplicates.empty:
                    print(f"\n⚠️ 重複除去後も残る重複: {len(duplicates)}件")
                    for order_no, count in duplicates.head().items():
                        print(f"  {order_no}: {count}回")
                else:
                    print("\n✅ 重複除去成功: 重複データなし")
            
        else:
            print("統合データが空です")
            
    except Exception as e:
        print(f"テストエラー: {e}")

def main():
    """メイン実行"""
    print("PC製造データ重複除去テスト")
    print("=" * 50)
    
    # 1. 現在のデータ分析
    analyze_duplication()
    
    # 2. 重複除去テスト
    test_deduplication()
    
    print("\n" + "=" * 50)
    print("テスト完了")

if __name__ == "__main__":
    main()