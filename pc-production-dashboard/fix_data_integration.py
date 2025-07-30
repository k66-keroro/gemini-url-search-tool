#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
データ統合修正スクリプト - 金額・数量を含む正しいデータを作成
"""

import sys
import sqlite3
import pandas as pd
from pathlib import Path
import os

def fix_data_integration():
    """データ統合を修正して実行"""
    print("🔧 データ統合修正を開始...")
    
    # 1. 既存のデータベースを削除
    db_path = Path("data/sqlite/pc_production.db")
    if db_path.exists():
        try:
            db_path.unlink()
            print("✅ 既存データベースを削除")
        except Exception as e:
            print(f"⚠️ データベース削除エラー: {e}")
    
    # 2. データローダーを修正して実行
    sys.path.append(str(Path(__file__).parent / "app"))
    
    try:
        from data_loader_simple import PCProductionDataLoaderSimple
        
        # データローダーのインスタンスを作成
        loader = PCProductionDataLoaderSimple()
        
        # 統合処理を実行
        print("📊 データ統合処理を実行中...")
        result = loader.integrate_all_data()
        
        if result is not None and not result.empty:
            print(f"✅ データ統合成功: {len(result):,}行")
            
            # カラム一覧を表示
            print("\n📋 作成されたカラム:")
            for col in result.columns:
                print(f"  - {col}")
            
            # 金額・数量カラムの確認
            amount_columns = [col for col in result.columns if '金額' in col or '価格' in col or 'amount' in col.lower()]
            quantity_columns = [col for col in result.columns if '数量' in col or '個数' in col or 'qty' in col.lower()]
            
            print(f"\n💰 金額関連カラム: {amount_columns}")
            print(f"📦 数量関連カラム: {quantity_columns}")
            
            if amount_columns:
                total_amount = result[amount_columns[0]].sum()
                print(f"💰 総金額: ¥{total_amount:,.0f}")
            
            if quantity_columns:
                total_quantity = result[quantity_columns[0]].sum()
                print(f"📦 総数量: {total_quantity:,.0f}")
            
            return True
        else:
            print("❌ データ統合に失敗")
            return False
            
    except Exception as e:
        print(f"❌ データ統合エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_zm29_files():
    """ZM29ファイルの存在確認"""
    print("\n📂 ZM29ファイル確認...")
    
    possible_paths = [
        Path("data/zm29_Monthly_performance"),
        Path("../data/zm29_Monthly_performance"),
        Path("../../data/raw")
    ]
    
    for path in possible_paths:
        if path.exists():
            zm29_files = list(path.glob("ZM29*.txt")) + list(path.glob("zm29*.txt"))
            if zm29_files:
                print(f"✅ ZM29ファイル発見: {path}")
                for file in zm29_files:
                    print(f"  - {file.name}")
                return True
    
    print("❌ ZM29ファイルが見つかりません")
    print("📋 確認すべきパス:")
    for path in possible_paths:
        print(f"  - {path.absolute()}")
    
    return False

def create_sample_data():
    """サンプルデータを作成（テスト用）"""
    print("\n🧪 サンプルデータを作成中...")
    
    try:
        # サンプルデータを作成
        import datetime
        import random
        
        data = []
        for i in range(1000):
            data.append({
                'データソース': 'サンプル',
                'MRP管理者': random.choice(['PC1', 'PC2', 'PC3']),
                '転記日': datetime.date(2024, 7, random.randint(1, 29)),
                '完成日': datetime.date(2024, 7, random.randint(1, 29)),
                '品目コード': f'ITEM{i:04d}',
                '生産金額': random.randint(10000, 1000000),
                '数量': random.randint(1, 100),
                '内製外注': random.choice(['内製', '外注']),
                '指図番号': f'ORDER{i:06d}'
            })
        
        df = pd.DataFrame(data)
        
        # データベースに保存
        db_path = Path("data/sqlite/pc_production.db")
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(str(db_path))
        df.to_sql('pc_production_zm29', conn, if_exists='replace', index=False)
        conn.close()
        
        print(f"✅ サンプルデータ作成完了: {len(df):,}行")
        print(f"💰 総生産金額: ¥{df['生産金額'].sum():,.0f}")
        print(f"📦 総数量: {df['数量'].sum():,.0f}")
        
        return True
        
    except Exception as e:
        print(f"❌ サンプルデータ作成エラー: {e}")
        return False

def main():
    """メイン処理"""
    print("=" * 60)
    print("🔧 データ統合修正スクリプト")
    print("=" * 60)
    
    # ZM29ファイルの確認
    has_zm29 = check_zm29_files()
    
    if has_zm29:
        # 実データで統合処理
        success = fix_data_integration()
    else:
        # サンプルデータを作成
        print("\n⚠️ 実データが見つからないため、サンプルデータを作成します")
        success = create_sample_data()
    
    if success:
        print("\n🎉 データ準備完了！")
        print("💡 ダッシュボードを起動してください:")
        print("   .\\run_standalone.bat")
    else:
        print("\n❌ データ準備に失敗しました")

if __name__ == "__main__":
    main()
    input("\nEnterキーを押して終了...")