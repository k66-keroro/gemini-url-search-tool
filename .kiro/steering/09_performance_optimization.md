# パフォーマンス最適化ガイドライン

## SQLiteデータベースのパフォーマンス最適化

### 1. インデックス最適化

#### 効果的なインデックス作成

```sql
-- 検索条件としてよく使用されるカラムにインデックスを作成
CREATE INDEX idx_zp138_品目コード ON zp138(品目コード);

-- 複合インデックスの作成（複数のカラムを組み合わせた検索条件に効果的）
CREATE INDEX idx_zp138_品目コード_日付 ON zp138(品目コード, 日付);

-- 部分的なインデックス（特定の条件に一致するレコードのみインデックス化）
CREATE INDEX idx_zp138_有効データ ON zp138(品目コード) WHERE 削除フラグ = 0;
```

#### インデックス管理のベストプラクティス

1. **必要最小限のインデックス**:
   - インデックスは検索を高速化するが、挿入・更新・削除は遅くなる
   - 本当に必要なカラムだけにインデックスを作成する

2. **インデックスの再構築**:
   - 大量のデータ変更後はインデックスを再構築する
   ```sql
   REINDEX idx_zp138_品目コード;
   ```

3. **未使用インデックスの削除**:
   - 使用されていないインデックスは削除する
   ```sql
   DROP INDEX idx_unused;
   ```

4. **インデックス使用状況の確認**:
   ```sql
   EXPLAIN QUERY PLAN SELECT * FROM zp138 WHERE 品目コード = 'A001';
   ```

### 2. クエリ最適化

#### 効率的なクエリの書き方

1. **必要なカラムのみ選択**:
   ```sql
   -- 非効率
   SELECT * FROM zp138 WHERE 品目コード = 'A001';
   
   -- 効率的
   SELECT 品目コード, 数量, 単価 FROM zp138 WHERE 品目コード = 'A001';
   ```

2. **LIKE演算子の最適化**:
   ```sql
   -- 非効率（前方一致以外はインデックスを使用できない）
   SELECT * FROM zp138 WHERE 品目コード LIKE '%001';
   
   -- 効率的（前方一致はインデックスを使用可能）
   SELECT * FROM zp138 WHERE 品目コード LIKE 'A%';
   ```

3. **IN句とJOINの適切な使い分け**:
   ```sql
   -- 少量のデータの場合はIN句が効率的
   SELECT * FROM zp138 WHERE 品目コード IN ('A001', 'A002', 'A003');
   
   -- 大量のデータの場合はJOINが効率的
   SELECT zp138.* FROM zp138 
   JOIN (SELECT 'A001' AS code UNION SELECT 'A002' UNION SELECT 'A003') AS codes
   ON zp138.品目コード = codes.code;
   ```

4. **サブクエリの最適化**:
   ```sql
   -- 非効率なサブクエリ
   SELECT * FROM zp138 
   WHERE 品目コード IN (SELECT 品目コード FROM zp02 WHERE 分類 = 'A');
   
   -- 効率的なJOIN
   SELECT zp138.* FROM zp138 
   JOIN zp02 ON zp138.品目コード = zp02.品目コード
   WHERE zp02.分類 = 'A';
   ```

### 3. トランザクション最適化

#### 効率的なトランザクション処理

```python
def efficient_bulk_insert(db_path, table_name, data):
    """大量データの効率的な挿入"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # WALモードを有効化
    cursor.execute("PRAGMA journal_mode = WAL")
    
    # 同期モードを調整（安全性とパフォーマンスのバランス）
    cursor.execute("PRAGMA synchronous = NORMAL")
    
    # キャッシュサイズを増やす
    cursor.execute("PRAGMA cache_size = 10000")
    
    # 一時的にインデックスを無効化（オプション）
    # cursor.execute("DROP INDEX IF EXISTS idx_table_column")
    
    # トランザクション開始
    cursor.execute("BEGIN TRANSACTION")
    
    try:
        # バッチ処理（例: 1000件ずつ）
        batch_size = 1000
        for i in range(0, len(data), batch_size):
            batch = data[i:i+batch_size]
            cursor.executemany(
                f"INSERT INTO {table_name} VALUES (?, ?, ?)",
                batch
            )
        
        # トランザクションのコミット
        conn.commit()
        
        # インデックスの再作成（必要に応じて）
        # cursor.execute("CREATE INDEX idx_table_column ON table(column)")
        
    except Exception as e:
        # エラー発生時はロールバック
        conn.rollback()
        raise e
    finally:
        # 接続を閉じる
        conn.close()
```

#### トランザクション使用のベストプラクティス

1. **適切なトランザクションサイズ**:
   - 小さすぎるトランザクション: オーバーヘッドが大きい
   - 大きすぎるトランザクション: メモリ使用量が増加、ロールバック時間が長くなる
   - 推奨: 1,000〜10,000行程度のバッチサイズ

2. **トランザクション内での処理の最小化**:
   - トランザクション内では必要最小限の処理のみを行う
   - 計算や変換はトランザクション外で行う

3. **エラーハンドリング**:
   - 必ず例外処理を行い、エラー時にはロールバックする
   - トランザクション状態を監視し、長時間のトランザクションを避ける

### 4. メモリ使用量の最適化

#### 大規模データ処理のメモリ最適化

```python
def process_large_file(file_path, db_path, table_name):
    """大きなファイルを少ないメモリで処理する"""
    conn = sqlite3.connect(db_path)
    
    # チャンクサイズを設定（メモリ使用量とのバランス）
    chunk_size = 10000
    
    # チャンク単位で読み込み、処理、保存
    for chunk in pd.read_csv(file_path, chunksize=chunk_size):
        # データ前処理
        chunk = preprocess_data(chunk)
        
        # データベースに保存
        chunk.to_sql(table_name, conn, if_exists='append', index=False)
    
    conn.close()
```

#### メモリ使用量削減のテクニック

1. **データ型の最適化**:
   ```python
   def optimize_dataframe_memory(df):
       """DataFrameのメモリ使用量を最適化する"""
       # 整数型の最適化
       for col in df.select_dtypes(include=['int']).columns:
           col_min = df[col].min()
           col_max = df[col].max()
           
           # 適切な整数型を選択
           if col_min >= 0:
               if col_max < 256:
                   df[col] = df[col].astype(np.uint8)
               elif col_max < 65536:
                   df[col] = df[col].astype(np.uint16)
               elif col_max < 4294967296:
                   df[col] = df[col].astype(np.uint32)
           else:
               if col_min > -128 and col_max < 128:
                   df[col] = df[col].astype(np.int8)
               elif col_min > -32768 and col_max < 32768:
                   df[col] = df[col].astype(np.int16)
               elif col_min > -2147483648 and col_max < 2147483648:
                   df[col] = df[col].astype(np.int32)
       
       # 浮動小数点型の最適化
       for col in df.select_dtypes(include=['float']).columns:
           df[col] = df[col].astype(np.float32)
       
       # カテゴリ型の最適化
       for col in df.select_dtypes(include=['object']).columns:
           if df[col].nunique() / len(df) < 0.5:  # カーディナリティが50%未満
               df[col] = df[col].astype('category')
       
       return df
   ```

2. **不要なデータの削除**:
   - 処理に不要なカラムは読み込み時に除外する
   - 中間結果は必要に応じて削除する
   - 大きなオブジェクトは使用後に`del`で明示的に削除する

3. **ジェネレータの活用**:
   ```python
   def process_data_with_generator(file_path):
       """ジェネレータを使用してメモリ効率を向上"""
       with open(file_path, 'r') as f:
           # ヘッダー行を処理
           header = next(f).strip().split(',')
           
           # 1行ずつ処理
           for line in f:
               # 行を解析
               values = line.strip().split(',')
               row = dict(zip(header, values))
               
               # 行を処理して結果を返す
               yield process_row(row)
   ```

### 5. ディスクI/O最適化

#### ディスクアクセスの最適化

1. **PRAGMA設定**:
   ```sql
   -- ジャーナルモードをWAL（Write-Ahead Logging）に設定
   PRAGMA journal_mode = WAL;
   
   -- 同期モードを調整（FULL: 最も安全、OFF: 最も高速だが危険）
   PRAGMA synchronous = NORMAL;
   
   -- テンポラリストレージをメモリに設定
   PRAGMA temp_store = MEMORY;
   
   -- メモリマップドI/Oを有効化（大きなデータベースでは注意）
   PRAGMA mmap_size = 30000000000;
   ```

2. **バキューム処理**:
   ```sql
   -- データベースの断片化を解消
   VACUUM;
   
   -- 自動バキュームを有効化
   PRAGMA auto_vacuum = INCREMENTAL;
   ```

3. **一時テーブルの活用**:
   ```sql
   -- 複雑な処理用の一時テーブル作成
   CREATE TEMPORARY TABLE temp_results AS
   SELECT 品目コード, SUM(数量) as 合計数量
   FROM zp138
   GROUP BY 品目コード;
   
   -- 一時テーブルを使用した処理
   SELECT * FROM temp_results WHERE 合計数量 > 100;
   
   -- 処理完了後に一時テーブルを削除
   DROP TABLE temp_results;
   ```

## Pythonコードのパフォーマンス最適化

### 1. コード最適化テクニック

#### ループの最適化

```python
# 非効率なループ
result = []
for i in range(len(data)):
    result.append(data[i] * 2)

# 効率的なリスト内包表記
result = [x * 2 for x in data]

# さらに効率的なNumPy操作（大量データの場合）
import numpy as np
data_array = np.array(data)
result = data_array * 2
```

#### データ構造の適切な選択

```python
# 頻繁な検索操作には辞書（ハッシュテーブル）を使用
lookup_dict = {item['id']: item for item in data}
result = lookup_dict.get('12345')

# 順序付きデータには collections.OrderedDict
from collections import OrderedDict
ordered_data = OrderedDict()

# 頻度カウントには Counter
from collections import Counter
word_counts = Counter(words)
most_common = word_counts.most_common(10)

# 両端からの追加/削除が多い場合は deque
from collections import deque
queue = deque(items)
queue.append(new_item)  # 右端に追加
queue.appendleft(new_item)  # 左端に追加
```

### 2. 並列処理の活用

#### マルチプロセッシング

```python
from multiprocessing import Pool

def process_chunk(chunk):
    """データチャンクを処理する関数"""
    # 処理ロジック
    return processed_data

def parallel_process_file(file_path, num_processes=4):
    """ファイルを並列処理する"""
    # データを分割
    chunks = split_data_into_chunks(file_path)
    
    # プロセスプールを作成
    with Pool(processes=num_processes) as pool:
        # 並列処理を実行
        results = pool.map(process_chunk, chunks)
    
    # 結果を結合
    final_result = combine_results(results)
    return final_result
```

#### 非同期処理

```python
import asyncio
import aiohttp

async def fetch_data(url):
    """非同期でデータを取得"""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()

async def process_multiple_sources():
    """複数のデータソースを非同期で処理"""
    urls = [
        "http://api.example.com/data1",
        "http://api.example.com/data2",
        "http://api.example.com/data3"
    ]
    
    # 非同期タスクを作成
    tasks = [fetch_data(url) for url in urls]
    
    # すべてのタスクを並行実行
    results = await asyncio.gather(*tasks)
    return results

# 非同期関数の実行
results = asyncio.run(process_multiple_sources())
```

### 3. プロファイリングとベンチマーク

#### コードプロファイリング

```python
import cProfile
import pstats
from pstats import SortKey

def profile_function(func, *args, **kwargs):
    """関数のパフォーマンスをプロファイリング"""
    profiler = cProfile.Profile()
    profiler.enable()
    
    result = func(*args, **kwargs)
    
    profiler.disable()
    stats = pstats.Stats(profiler).sort_stats(SortKey.CUMULATIVE)
    stats.print_stats(10)  # 上位10件の結果を表示
    
    return result

# 使用例
profile_function(process_large_file, "data.csv", "output.db", "table_name")
```

#### 実行時間の測定

```python
import time
import timeit

def benchmark_function(func, *args, repeat=3, **kwargs):
    """関数の実行時間をベンチマーク"""
    # 単純な時間測定
    start_time = time.time()
    result = func(*args, **kwargs)
    end_time = time.time()
    print(f"実行時間: {end_time - start_time:.6f}秒")
    
    # より正確な測定（小さな関数用）
    setup = "from __main__ import func"
    stmt = "func(*args, **kwargs)"
    timer = timeit.Timer(stmt=stmt, setup=setup, globals=locals())
    times = timer.repeat(repeat=repeat, number=1)
    print(f"平均実行時間: {sum(times) / len(times):.6f}秒")
    print(f"最小実行時間: {min(times):.6f}秒")
    
    return result

# 使用例
benchmark_function(process_data, large_dataset, repeat=5)
```

## 実装例: 最適化されたデータ処理パイプライン

### 大規模データ処理の最適化パイプライン

```python
import sqlite3
import pandas as pd
import numpy as np
from multiprocessing import Pool
import os
import time

def optimize_dataframe_memory(df):
    """DataFrameのメモリ使用量を最適化"""
    # 整数型の最適化
    for col in df.select_dtypes(include=['int']).columns:
        col_min = df[col].min()
        col_max = df[col].max()
        
        # 適切な整数型を選択
        if col_min >= 0:
            if col_max < 256:
                df[col] = df[col].astype(np.uint8)
            elif col_max < 65536:
                df[col] = df[col].astype(np.uint16)
            elif col_max < 4294967296:
                df[col] = df[col].astype(np.uint32)
        else:
            if col_min > -128 and col_max < 128:
                df[col] = df[col].astype(np.int8)
            elif col_min > -32768 and col_max < 32768:
                df[col] = df[col].astype(np.int16)
            elif col_min > -2147483648 and col_max < 2147483648:
                df[col] = df[col].astype(np.int32)
    
    # 浮動小数点型の最適化
    for col in df.select_dtypes(include=['float']).columns:
        df[col] = df[col].astype(np.float32)
    
    # カテゴリ型の最適化
    for col in df.select_dtypes(include=['object']).columns:
        if df[col].nunique() / len(df) < 0.5:  # カーディナリティが50%未満
            df[col] = df[col].astype('category')
    
    return df

def preprocess_chunk(chunk):
    """データチャンクの前処理"""
    # メモリ使用量の最適化
    chunk = optimize_dataframe_memory(chunk)
    
    # データクレンジング
    # 欠損値の処理
    chunk = chunk.fillna({
        '数値カラム': 0,
        '文字列カラム': ''
    })
    
    # データ変換
    if '日付' in chunk.columns:
        chunk['日付'] = pd.to_datetime(chunk['日付'], errors='coerce')
    
    if '金額' in chunk.columns:
        chunk['金額'] = chunk['金額'].astype(float)
    
    return chunk

def process_chunk(args):
    """マルチプロセッシング用のチャンク処理関数"""
    chunk, db_path, table_name = args
    
    # 前処理
    processed_chunk = preprocess_chunk(chunk)
    
    # 一時ファイルに保存（プロセス間でDataFrameを直接渡すのを避ける）
    temp_file = f"temp_{os.getpid()}.csv"
    processed_chunk.to_csv(temp_file, index=False)
    
    # 一時ファイルからデータベースに保存
    conn = sqlite3.connect(db_path)
    temp_df = pd.read_csv(temp_file)
    temp_df.to_sql(table_name, conn, if_exists='append', index=False)
    conn.close()
    
    # 一時ファイルを削除
    os.remove(temp_file)
    
    return len(processed_chunk)

def optimized_data_pipeline(file_path, db_path, table_name, chunk_size=100000, num_processes=4):
    """最適化されたデータ処理パイプライン"""
    start_time = time.time()
    total_rows = 0
    
    # データベース接続の準備
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # パフォーマンス設定
    cursor.execute("PRAGMA journal_mode = WAL")
    cursor.execute("PRAGMA synchronous = NORMAL")
    cursor.execute("PRAGMA cache_size = 10000")
    cursor.execute("PRAGMA temp_store = MEMORY")
    
    # テーブルが存在する場合は削除（必要に応じて）
    cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
    conn.commit()
    conn.close()
    
    # チャンク単位で読み込み
    reader = pd.read_csv(file_path, chunksize=chunk_size)
    
    # プロセスプールを作成
    with Pool(processes=num_processes) as pool:
        # チャンクを並列処理
        chunks_with_args = [(chunk, db_path, table_name) for chunk in reader]
        results = pool.map(process_chunk, chunks_with_args)
        total_rows = sum(results)
    
    # 処理完了後のインデックス作成
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # テーブル構造を取得してインデックスを作成
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [col[1] for col in cursor.fetchall()]
    
    # 主要カラムにインデックスを作成
    for col in columns:
        if any(keyword in col.lower() for keyword in ['code', 'id', 'key', 'date', 'コード', '番号', '日付']):
            index_name = f"idx_{table_name}_{col}"
            cursor.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name}({col})")
    
    # 最適化
    cursor.execute("PRAGMA optimize")
    conn.commit()
    conn.close()
    
    end_time = time.time()
    print(f"処理完了: {total_rows}行を処理")
    print(f"総実行時間: {end_time - start_time:.2f}秒")
    
    return total_rows

# 使用例
# optimized_data_pipeline("large_data.csv", "data/sqlite/main.db", "optimized_table", chunk_size=50000, num_processes=6)
```

## パフォーマンス最適化のベストプラクティス

1. **計測と分析を先に行う**:
   - 最適化の前に、ボトルネックを特定する
   - 「推測ではなく計測」の原則に従う

2. **最大の効果が得られる部分を最適化**:
   - パレートの法則（80/20の法則）を意識する
   - 実行時間の80%を占める20%のコードに集中する

3. **段階的に最適化する**:
   - 一度にすべてを変更せず、一つずつ変更して効果を測定する
   - 変更の影響を理解し、予期しない副作用を避ける

4. **可読性とのバランスを取る**:
   - 過度に複雑な最適化は避ける
   - コードの可読性と保守性を犠牲にしない

5. **適切なツールを使用する**:
   - プロファイラーを活用してボトルネックを特定
   - ベンチマークツールで改善を定量的に測定