---
title: Excel処理機能
inclusion: always
---

# Excel処理機能

## 複数シートの処理

### 現状の実装

現在のSQLiteManagerクラスでは、Excelファイルの最初のシート（sheet_name=0）のみを読み込む実装になっています：

```python
# 通常のExcelファイル処理
df = pd.read_excel(file_path, sheet_name=0, engine='openpyxl')
```

### 複数シート処理の実装方針

複数シートを持つExcelファイルを処理するには、以下の方法が考えられます：

1. **すべてのシートを別々のテーブルとして読み込む**:
   ```python
   # すべてのシートを辞書として読み込む
   dfs = pd.read_excel(file_path, sheet_name=None, engine='openpyxl')
   
   # 各シートを別々のテーブルとして処理
   for sheet_name, df in dfs.items():
       table_name = f"{base_table_name}_{sheet_name}"
       # テーブル名を適切に変換
       table_name = sanitize_table_name(table_name)
       # データをSQLiteに書き込み
       df.to_sql(table_name, conn, if_exists='replace', index=False)
   ```

2. **特定のシートのみを処理する**:
   ```python
   # 設定ファイルから特定のシートを指定
   sheet_config = {
       'date.xlsx': ['postgres_date', 'sqlite_date']
   }
   
   # ファイル名に基づいて処理するシートを決定
   sheets_to_process = sheet_config.get(file_path.name, [0])  # デフォルトは最初のシート
   
   for sheet in sheets_to_process:
       df = pd.read_excel(file_path, sheet_name=sheet, engine='openpyxl')
       table_name = f"{base_table_name}_{sheet}" if isinstance(sheet, str) else base_table_name
       # 以下、通常の処理
   ```

### 日付データの処理

Excelファイル内の日付データは、以下の形式で存在する可能性があります：

1. **Excel日付形式**: Excel内部の日付表現（1900年1月1日からの経過日数）
2. **文字列形式の日付**: 'YYYY/MM/DD'や'YYYY-MM-DD'などの形式
3. **8桁数値形式**: 'YYYYMMDD'形式の数値

これらを適切に処理するために、`_optimize_dtypes`メソッドでは以下の処理を行っています：

```python
# 日付列の名前パターン
date_column_patterns = [
    'date', '日付', 'day', '年月日', '登録日', '有効開始日', '有効終了日', 
    '作成日', '更新日', '開始日', '終了日', '期限', '期日'
]

# 列名に基づく日付型の検出と変換
is_date_column = any(pattern in col_lower for pattern in date_column_patterns)

if is_date_column:
    # まず標準的な日付形式で変換を試みる
    df[col] = pd.to_datetime(df[col], errors='coerce')
    
    # 変換に失敗した値（NaT）がある場合、8桁数値形式（YYYYMMDD）で再試行
    if df[col].isna().any():
        # 8桁数値形式で変換を試みる
        mask = df[col].isna()
        str_values = df.loc[mask, col].astype(str)
        date_values = pd.to_datetime(str_values, format='%Y%m%d', errors='coerce')
        df.loc[mask, col] = date_values
```

## 特殊なExcelファイルの処理

### ヘッダー行が複数ある場合

一部のExcelファイルでは、ヘッダー行が複数行あり、実際のフィールド名が数行目にある場合があります：

```python
# 特殊なExcelファイルの処理
if file_path.name.lower() == 'pp_summary_ztbp080_kojozisseki_d_0.xlsx':
    # ヘッダーが7行あり、8行目がフィールド名（0-indexedなので7が8行目に相当）
    df = pd.read_excel(file_path, sheet_name=0, engine='openpyxl', header=7)
```

### 設定ファイルによる特殊処理の管理

今後、特殊なExcelファイルが増えた場合は、設定ファイルで管理することも検討できます：

```python
# Excel特殊処理設定
excel_special_config = {
    'pp_summary_ztbp080_kojozisseki_d_0.xlsx': {'header': 7},
    'another_special_file.xlsx': {'header': 5, 'skiprows': [0, 1, 3]},
}

# ファイル名に基づいて特殊処理を適用
config = excel_special_config.get(file_path.name.lower(), {'header': 0})
df = pd.read_excel(file_path, sheet_name=0, engine='openpyxl', **config)
```

## 今後の拡張

1. **複数シート処理の実装**:
   - 設定ファイルによるシート指定
   - シート名に基づくテーブル名の生成

2. **Excel特殊処理の拡張**:
   - ヘッダー行の自動検出
   - 複雑なデータ構造（マルチヘッダー、結合セルなど）の処理

3. **データ型の自動推論の強化**:
   - Excelのセル書式に基づくデータ型の推定
   - 列名パターンの拡充