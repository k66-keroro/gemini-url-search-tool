"""
KANSEI_JISSEKIファイルの構造解析

実際のカラム構造を確認して、正しいマッピングを作成
"""

import pandas as pd
from pathlib import Path
import chardet

def analyze_kansei_structure():
    """KANSEI_JISSEKIの構造を解析"""
    print("=" * 60)
    print("KANSEI_JISSEKI構造解析")
    print("=" * 60)
    
    kansei_file = Path("pc-production-dashboard/data/current/KANSEI_JISSEKI.txt")
    
    if not kansei_file.exists():
        print(f"❌ ファイルが見つかりません: {kansei_file}")
        return
    
    try:
        # エンコーディング検出
        with open(kansei_file, 'rb') as f:
            raw_data = f.read(10000)
            result = chardet.detect(raw_data)
            encoding = result['encoding']
            print(f"📝 検出エンコーディング: {encoding} (信頼度: {result['confidence']:.2f})")
        
        # ファイル読み込み
        df = pd.read_csv(
            kansei_file,
            delimiter='\t',
            encoding='shift_jis',  # 強制的にshift_jisを使用
            dtype=str,
            on_bad_lines='skip'
        )
        
        print(f"📊 基本情報:")
        print(f"  行数: {len(df)}")
        print(f"  カラム数: {len(df.columns)}")
        
        print(f"\n📋 カラム一覧:")
        for i, col in enumerate(df.columns):
            print(f"  {i+1:2d}. {col}")
        
        print(f"\n📝 サンプルデータ（最初の3行）:")
        for i in range(min(3, len(df))):
            print(f"\n  行 {i+1}:")
            for j, (col, val) in enumerate(zip(df.columns, df.iloc[i])):
                print(f"    {j+1:2d}. {col}: {val}")
        
        # 数値っぽいカラムを特定
        print(f"\n🔢 数値データの可能性があるカラム:")
        for col in df.columns:
            sample_values = df[col].dropna().head(10)
            numeric_count = 0
            for val in sample_values:
                try:
                    float(str(val).replace(',', ''))
                    numeric_count += 1
                except:
                    pass
            
            if numeric_count > len(sample_values) * 0.5:  # 50%以上が数値
                print(f"  ✅ {col}: {numeric_count}/{len(sample_values)} が数値")
                print(f"      サンプル値: {list(sample_values)}")
        
        # ZM29との対応関係を推測
        print(f"\n🔄 ZM29カラムとの対応関係推測:")
        
        zm29_mapping = {
            '転記日付': ['日付', 'date', '転記', '実績日'],
            'ネットワーク・指図番号': ['指図', 'order', '番号', 'ネットワーク'],
            '品目コード': ['品目', 'item', 'コード', 'code'],
            '品目テキスト': ['テキスト', 'text', '名称', '品名'],
            '完成数': ['完成', '数量', 'qty', '実績'],
            '計画数': ['計画', 'plan'],
            '単価': ['単価', 'price', '価格'],
            'MRP管理者': ['MRP', '管理', 'manager']
        }
        
        for zm29_col, keywords in zm29_mapping.items():
            candidates = []
            for kansei_col in df.columns:
                for keyword in keywords:
                    if keyword in kansei_col:
                        candidates.append(kansei_col)
                        break
            
            if candidates:
                print(f"  {zm29_col} ← {candidates}")
            else:
                print(f"  {zm29_col} ← 候補なし")
        
        return df
        
    except Exception as e:
        print(f"❌ 解析エラー: {e}")
        return None

def create_correct_mapping():
    """正しいカラムマッピングを作成"""
    print(f"\n" + "=" * 60)
    print("正しいカラムマッピング作成")
    print("=" * 60)
    
    # 実際のKANSEI_JISSEKIの構造に基づいたマッピング
    # （文字化けしているが、位置で判断）
    kansei_columns = [
        'プラント',      # 0
        '保管場所',      # 1  
        '品目コード',    # 2
        '品目テキスト',  # 3
        '指図番号',      # 4
        '指図タイプ',    # 5
        'MRP管理者',     # 6
        '計画数',        # 7
        '完成数',        # 8
        '累計完成数',    # 9
        '残数',          # 10
        '入力日時',      # 11
        '計画完了日',    # 12
        'WBS要素',       # 13
        '受注伝票番号',  # 14
        '受注明細番号'   # 15
    ]
    
    # ZM29形式へのマッピング
    mapping = {
        '転記日付': '計画完了日',  # または入力日時から日付部分を抽出
        'ネットワーク・指図番号': '指図番号',
        '品目コード': '品目コード',
        '品目テキスト': '品目テキスト', 
        '完成数': '完成数',
        '計画数': '計画数',
        '単価': None,  # KANSEI_JISSEKIには単価がない
        'MRP管理者': 'MRP管理者'
    }
    
    print("推奨マッピング:")
    for zm29_col, kansei_col in mapping.items():
        if kansei_col:
            print(f"  {zm29_col} ← {kansei_col}")
        else:
            print(f"  {zm29_col} ← デフォルト値使用")
    
    return mapping

def main():
    """メイン実行"""
    df = analyze_kansei_structure()
    
    if df is not None:
        mapping = create_correct_mapping()
        
        print(f"\n" + "=" * 60)
        print("次のステップ")
        print("=" * 60)
        print("1. data_loader_fixed.pyのカラムマッピングを修正")
        print("2. 単価データがないため、デフォルト値または別ソースから取得")
        print("3. 日付フィールドの正しい変換処理を実装")
        print("4. 数値フィールドの型変換を確実に実行")

if __name__ == "__main__":
    main()