---
title: 実装ノート
inclusion: always
---

# 実装ノート

## テーブル課題対応

### 1. zm37.txtの処理問題

**問題点**:
- CP932エンコーディングの特殊なファイル
- 区切り文字の判定が難しい
- Pythonエンジンとの互換性問題

**解決策**:
```python
# 特殊な設定でzm37.txtを読み込む
df = pd.read_csv(
    file_path, 
    encoding='cp932',
    sep=separator,
    quoting=_csv.QUOTE_NONE,  # クォーテーションを無視
    engine='python',  # より柔軟な解析のためpythonエンジンを使用
    on_bad_lines='skip',  # 問題のある行をスキップ
    escapechar='\\',  # エスケープ文字を指定
    dtype=str  # すべての列を文字列として読み込む
)
```

### 2. 特殊なExcelファイルの処理

**問題点**:
- PP_SUMMARY_ZTBP080_KOJOZISSEKI_D_0.xlsx はヘッダーが7行
- 8行目がフィールド名

**解決策**:
```python
# 特殊なExcelファイルの処理
if file_path.name.lower() == 'pp_summary_ztbp080_kojozisseki_d_0.xlsx':
    self.logger.info(f"特殊なExcelファイル処理: {file_path.name} (ヘッダー7行)")
    # ヘッダーが7行あり、8行目がフィールド名（0-indexedなので7が8行目に相当）
    df = pd.read_excel(file_path, sheet_name=0, engine='openpyxl', header=7)
```

### 3. テーブル名の修正

**問題点**:
- 日本語や特殊文字を含むテーブル名
- SQLiteの命名規則との互換性

**解決策**:
```python
def sanitize_table_name(table_name: str) -> str:
    # 日本語文字を含むかチェック
    has_japanese = re.search(r'[ぁ-んァ-ン一-龥]', table_name)
    
    # 日本語文字を含む場合は、プレフィックスを付ける
    if has_japanese:
        sanitized = f"t_{hash(table_name) % 10000:04d}"
    else:
        # 英数字以外の文字を_に置換
        sanitized = re.sub(r'[^a-zA-Z0-9]', '_', table_name)
        
        # 連続する_を単一の_に置換
        sanitized = re.sub(r'_+', '_', sanitized)
        
        # 先頭が数字の場合、t_を付ける
        if sanitized and sanitized[0].isdigit():
            sanitized = f"t_{sanitized}"
            
        # 先頭と末尾の_を削除
        sanitized = sanitized.strip('_')
        
    return sanitized
```

### 4. データ型の修正（v2.0で大幅改善）

**問題点**:
- 日付、8桁数値・文字、codeなどの適切な型変換
- 列名に基づいたデータ型の推測
- zm37.txtの日付データ（登録日、有効開始日、有効終了日など）が正しく変換されない
- 特殊な日付値（99991231など）の処理
- すべてのデータがTEXT型になってしまう問題

**v2.0での改善内容**:
- **強化されたデータ型推論**: 列名パターンと実際のデータ内容の両方を分析
- **自動数値変換**: 90%以上が数値として解釈可能な列を自動検出
- **8桁日付の自動検出**: YYYYMMDD形式の自動判定と変換
- **タイムスタンプ検出**: 標準的なタイムスタンプ形式の自動変換
- **コードフィールド変換機能**: 数値として格納されているコードの適切な処理

**解決策**:
```python
def _optimize_dtypes(self, df: pd.DataFrame) -> pd.DataFrame:
    # 日付列の名前パターン
    date_column_patterns = [
        'date', '日付', 'day', '年月日', '登録日', '有効開始日', '有効終了日', 
        '作成日', '更新日', '開始日', '終了日', '期限', '期日'
    ]
    
    for col in df.columns:
        # 列名を小文字に変換して比較
        col_lower = col.lower() if isinstance(col, str) else ""
        
        # 空の列はスキップ
        if df[col].empty:
            continue
        
        # 列名に基づく日付型の検出と変換
        is_date_column = any(pattern in col_lower for pattern in date_column_patterns)
        
        if is_date_column:
            try:
                # まず標準的な日付形式で変換を試みる
                df[col] = pd.to_datetime(df[col], errors='coerce')
                
                # 変換に失敗した値（NaT）がある場合、8桁数値形式（YYYYMMDD）で再試行
                if df[col].isna().any():
                    # 元の値を保持
                    original_values = df[col].copy()
                    
                    # 8桁数値形式で変換を試みる
                    mask = df[col].isna()
                    str_values = df.loc[mask, col].astype(str)
                    date_values = pd.to_datetime(str_values, format='%Y%m%d', errors='coerce')
                    df.loc[mask, col] = date_values
                    
                    # 特殊な値（99991231など）を処理
                    special_mask = df[col].isna() & original_values.astype(str).str.contains('9999')
                    if special_mask.any():
                        df.loc[special_mask, col] = pd.Timestamp.max
            except Exception as e:
                pass
        
        # 8桁数値・文字の処理
        elif df[col].dtype == 'object':
            # サンプルデータを取得（最大100行）
            sample = df[col].dropna().head(100)
            
            # 8桁数値パターンの検出（日付の可能性）
            if all(isinstance(x, str) and len(x) == 8 and x.isdigit() for x in sample if pd.notna(x) and x):
                try:
                    # 日付として解釈できるか試す
                    test_dates = pd.to_datetime(sample, format='%Y%m%d', errors='coerce')
                    valid_dates = ~test_dates.isna()
                    
                    # 50%以上が有効な日付の場合、日付型として変換
                    if valid_dates.mean() >= 0.5:
                        df[col] = pd.to_datetime(df[col], format='%Y%m%d', errors='coerce')
                        
                        # 特殊な値（99991231など）を処理
                        special_mask = df[col].isna() & df[col].astype(str).str.contains('9999')
                        if special_mask.any():
                            df.loc[special_mask, col] = pd.Timestamp.max
                    else:
                        # 数値として保持
                        df[col] = pd.to_numeric(df[col], errors='ignore')
                except Exception as e:
                    # 数値として変換
                    df[col] = pd.to_numeric(df[col], errors='ignore')
            
            # コード列の処理
            elif 'code' in col_lower or 'コード' in col_lower:
                df[col] = df[col].astype(str)
    
    return df
```

### 5. コードフィールド変換機能（v2.0で新規実装）

**機能概要**:
- 数値として格納されているが実際はコードである列を検出
- ゼロパディング、固定長、非連続などのパターンを自動判定
- 適切なデータ型への変換を支援

**実装内容**:
```python
def _analyze_code_field(self, table_name, col_name, col_type):
    # 先頭ゼロの検出
    zero_padded_count = sum(1 for val in values if val.startswith('0') and len(val) > 1)
    if zero_padded_count > len(values) * 0.1:
        return "ゼロパディングコード", True
    
    # 固定長コードの検出
    lengths = [len(val) for val in values]
    if len(set(lengths)) <= 2 and avg_length >= 4:
        return "固定長コード", True
    
    # 非連続コードの検出
    if max(gaps) > 1000:
        return "非連続コード", True
```

## v2.0での主要改善点

1. **モジュラー化アーキテクチャ**: 保守性と拡張性の大幅向上
2. **データ型最適化の強化**: 自動推論機能の大幅改善
3. **ZP138特殊処理の統合**: 引当計算付きの処理を統合
4. **コードフィールド変換**: 新機能として実装
5. **テーブル情報の改善**: 元ファイル名併記で可視性向上

## 今後の課題

1. **wbsの親子関係**:
   - フィールド名の統一性の問題は、データ変換時に対応が必要

2. **dbo_提出用_経理_滞留在庫資料_通常.xlsx**:
   - 月初更新（稼働日2日目位）の自動化
   - 年次データと月次データの区別
   - 差分のみの更新処理

3. **パフォーマンス最適化**:
   - 大量データ処理時のメモリ使用量の最適化
   - トランザクション処理の改善

4. **データ型変換の精度向上**:
   - より複雑なデータパターンの対応
   - ユーザー定義の変換ルール機能