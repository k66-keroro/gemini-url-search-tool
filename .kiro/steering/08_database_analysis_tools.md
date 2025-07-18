# SQLiteデータベース分析ツールとテクニック

## 基本的な分析アプローチ

### 1. テーブル構造の分析

```python
def analyze_table_structure(db_path, table_name):
    """テーブルの構造を分析する"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # カラム情報の取得
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    
    print(f"\n{table_name}のカラム構造:")
    for col in columns:
        col_id, name, type_, not_null, default_val, pk = col
        print(f"- {name} ({type_}){' [PK]' if pk else ''}{' [NOT NULL]' if not_null else ''}")
    
    # インデックス情報の取得
    cursor.execute(f"PRAGMA index_list({table_name})")
    indexes = cursor.fetchall()
    
    if indexes:
        print(f"\n{table_name}のインデックス:")
        for idx in indexes:
            idx_name = idx[1]
            print(f"- {idx_name}")
            
            # インデックスの詳細情報
            cursor.execute(f"PRAGMA index_info({idx_name})")
            idx_info = cursor.fetchall()
            for info in idx_info:
                col_pos, col_idx = info[0], info[1]
                cursor.execute(f"PRAGMA table_info({table_name})")
                col_name = cursor.fetchall()[col_idx][1]
                print(f"  - カラム: {col_name}")
    
    conn.close()
```

### 2. データ分布の分析

```python
def analyze_data_distribution(db_path, table_name, column_name):
    """カラムのデータ分布を分析する"""
    conn = sqlite3.connect(db_path)
    
    # 基本統計情報
    query = f"""
    SELECT 
        COUNT(*) as count,
        COUNT(DISTINCT {column_name}) as unique_count,
        MIN({column_name}) as min_value,
        MAX({column_name}) as max_value,
        AVG({column_name}) as avg_value
    FROM {table_name}
    WHERE {column_name} IS NOT NULL
    """
    
    df = pd.read_sql_query(query, conn)
    print(f"\n{table_name}.{column_name}の基本統計:")
    print(df)
    
    # 頻度分布（上位10件）
    query = f"""
    SELECT 
        {column_name},
        COUNT(*) as frequency
    FROM {table_name}
    WHERE {column_name} IS NOT NULL
    GROUP BY {column_name}
    ORDER BY frequency DESC
    LIMIT 10
    """
    
    df = pd.read_sql_query(query, conn)
    print(f"\n{table_name}.{column_name}の頻度分布（上位10件）:")
    print(df)
    
    conn.close()
```

### 3. テーブル間の関連性分析

```python
def analyze_table_relationships(db_path):
    """テーブル間の関連性を分析する"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # テーブル一覧の取得
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [table[0] for table in cursor.fetchall()]
    
    relationships = []
    
    # 各テーブルの外部キー情報を取得
    for table in tables:
        cursor.execute(f"PRAGMA foreign_key_list({table})")
        fks = cursor.fetchall()
        
        for fk in fks:
            id_, seq, ref_table, from_col, to_col, on_update, on_delete, match = fk
            relationships.append({
                'table': table,
                'column': from_col,
                'references_table': ref_table,
                'references_column': to_col
            })
    
    print("\nテーブル間の関連性:")
    for rel in relationships:
        print(f"- {rel['table']}.{rel['column']} -> {rel['references_table']}.{rel['references_column']}")
    
    conn.close()
```

## 高度な分析テクニック

### 1. データ品質チェック

```python
def check_data_quality(db_path, table_name):
    """データ品質をチェックする"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # カラム情報の取得
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [col[1] for col in cursor.fetchall()]
    
    quality_issues = []
    
    # 各カラムの NULL 値をチェック
    for col in columns:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE {col} IS NULL")
        null_count = cursor.fetchone()[0]
        
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        total_count = cursor.fetchone()[0]
        
        if null_count > 0:
            null_percentage = (null_count / total_count) * 100
            quality_issues.append({
                'type': 'NULL値',
                'column': col,
                'count': null_count,
                'percentage': null_percentage
            })
    
    # 重複値のチェック
    for col in columns:
        cursor.execute(f"""
        SELECT {col}, COUNT(*) as count
        FROM {table_name}
        GROUP BY {col}
        HAVING count > 1
        ORDER BY count DESC
        LIMIT 5
        """)
        
        duplicates = cursor.fetchall()
        if duplicates:
            for dup in duplicates:
                quality_issues.append({
                    'type': '重複値',
                    'column': col,
                    'value': dup[0],
                    'count': dup[1]
                })
    
    print(f"\n{table_name}のデータ品質問題:")
    for issue in quality_issues:
        if issue['type'] == 'NULL値':
            print(f"- {issue['column']}: NULL値 {issue['count']}件 ({issue['percentage']:.2f}%)")
        elif issue['type'] == '重複値':
            print(f"- {issue['column']}: 値「{issue['value']}」が {issue['count']}回出現")
    
    conn.close()
```

### 2. パフォーマンス分析

```python
def analyze_query_performance(db_path, query):
    """クエリのパフォーマンスを分析する"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # EXPLAIN QUERY PLAN の実行
    cursor.execute(f"EXPLAIN QUERY PLAN {query}")
    plan = cursor.fetchall()
    
    print("\nクエリ実行計画:")
    for step in plan:
        print(f"- {step}")
    
    # 実行時間の測定
    import time
    start_time = time.time()
    cursor.execute(query)
    results = cursor.fetchall()
    end_time = time.time()
    
    print(f"\n実行時間: {end_time - start_time:.6f}秒")
    print(f"結果件数: {len(results)}件")
    
    conn.close()
```

## 実用的な分析スクリプト

### 1. テーブル概要レポート生成

```python
def generate_table_summary(db_path):
    """データベース内の全テーブルの概要レポートを生成する"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # テーブル一覧の取得
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [table[0] for table in cursor.fetchall()]
    
    summary = []
    
    for table in tables:
        # 行数のカウント
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        row_count = cursor.fetchone()[0]
        
        # カラム数の取得
        cursor.execute(f"PRAGMA table_info({table})")
        column_count = len(cursor.fetchall())
        
        # インデックス数の取得
        cursor.execute(f"PRAGMA index_list({table})")
        index_count = len(cursor.fetchall())
        
        # サイズの概算（SQLiteでは正確なテーブルサイズを取得するのは難しい）
        cursor.execute(f"SELECT * FROM {table} LIMIT 1")
        sample_row = cursor.fetchone()
        if sample_row:
            # 1行あたりのバイト数を概算
            bytes_per_row = sum(len(str(field)) for field in sample_row)
            size_estimate = bytes_per_row * row_count
        else:
            size_estimate = 0
        
        summary.append({
            'table': table,
            'rows': row_count,
            'columns': column_count,
            'indexes': index_count,
            'size_estimate': size_estimate
        })
    
    # 結果の表示
    print("\nデータベーステーブル概要:")
    print(f"{'テーブル名':<30} {'行数':>10} {'カラム数':>10} {'インデックス数':>15} {'推定サイズ':>15}")
    print("-" * 80)
    
    for item in summary:
        size_str = f"{item['size_estimate'] / 1024:.2f} KB" if item['size_estimate'] < 1024 * 1024 else f"{item['size_estimate'] / (1024 * 1024):.2f} MB"
        print(f"{item['table']:<30} {item['rows']:>10} {item['columns']:>10} {item['indexes']:>15} {size_str:>15}")
    
    conn.close()
```

### 2. データ整合性チェック

```python
def check_data_integrity(db_path):
    """データベース全体の整合性をチェックする"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 整合性チェックの実行
    cursor.execute("PRAGMA integrity_check")
    integrity_result = cursor.fetchone()[0]
    
    print(f"\nデータベース整合性チェック結果: {integrity_result}")
    
    # 外部キー制約の有効化
    cursor.execute("PRAGMA foreign_keys = ON")
    
    # 外部キー制約のチェック
    cursor.execute("PRAGMA foreign_key_check")
    fk_violations = cursor.fetchall()
    
    if fk_violations:
        print("\n外部キー制約違反:")
        for violation in fk_violations:
            table, rowid, parent, fkid = violation
            print(f"- テーブル: {table}, 行ID: {rowid}, 参照先テーブル: {parent}, 外部キーID: {fkid}")
    else:
        print("\n外部キー制約違反はありません")
    
    conn.close()
```

## 使用例

```python
# データベースパス
db_path = "data/sqlite/main.db"

# テーブル構造の分析
analyze_table_structure(db_path, "zp138")

# データ分布の分析
analyze_data_distribution(db_path, "zp138", "品目コード")

# テーブル間の関連性分析
analyze_table_relationships(db_path)

# データ品質チェック
check_data_quality(db_path, "zp138")

# クエリパフォーマンス分析
analyze_query_performance(db_path, "SELECT * FROM zp138 WHERE 品目コード LIKE 'A%'")

# テーブル概要レポート生成
generate_table_summary(db_path)

# データ整合性チェック
check_data_integrity(db_path)
```

## 分析結果の活用方法

1. **データモデルの最適化**:
   - 正規化の不足している箇所の特定
   - 冗長なデータの削除
   - 適切なデータ型の選定

2. **インデックス戦略の改善**:
   - 頻繁にアクセスされるカラムへのインデックス追加
   - 不要なインデックスの削除
   - 複合インデックスの最適化

3. **データ品質の向上**:
   - NULL値の適切な処理
   - 重複データの統合
   - 不整合データの修正

4. **パフォーマンスチューニング**:
   - クエリの最適化
   - テーブル構造の見直し
   - 適切なキャッシュ戦略の導入