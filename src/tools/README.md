# データベース管理ツール

このディレクトリには、SQLiteデータベースの管理と最適化のためのツールが含まれています。

## fix_numeric_codes.py

コード値が数値型(REAL/INTEGER)として保存されているフィールドを文字列型(TEXT)に変換するツールです。

### 問題の背景

多くのコードフィールド（例：評価クラス、保管場所コード、勘定科目コード、受注番号など）が数値型として保存されていますが、これらは本来文字列として扱うべきです。数値型で保存すると以下の問題が発生します：

- 先頭の0が削除される（例：「001」→「1」）
- SAPの後ろマイナス表記（例：「1234-」）が正しく扱われない
- テーブル間の結合時にデータ型の不一致が発生する（REALとINTEGERの混在）

### 使用方法

```bash
# ドライラン（変換対象の確認のみ）
python src/tools/fix_numeric_codes.py data/sqlite/main.db --dry-run

# 実際に変換を実行
python src/tools/fix_numeric_codes.py data/sqlite/main.db

# 特定のテーブルのみを処理
python src/tools/fix_numeric_codes.py data/sqlite/main.db --tables zp138,zs65,zm21

# ログファイルを指定
python src/tools/fix_numeric_codes.py data/sqlite/main.db --log-file logs/fix_codes.log
```

### オプション

- `--dry-run`: 変換対象を表示するだけで実際の変換は行いません
- `--tables`: 処理対象のテーブルをカンマ区切りで指定します
- `--log-file`: ログの出力先ファイルを指定します

## analyze_numeric_codes.py

数値型コードフィールドを分析し、文字列型に変換すべきフィールドのレポートを生成するツールです。

### 使用方法

```bash
# データベース全体の分析
python src/tools/analyze_numeric_codes.py data/sqlite/main.db

# 分析結果をファイルに出力
python src/tools/analyze_numeric_codes.py data/sqlite/main.db -o reports/numeric_codes_report.md

# 特定のテーブルのみを分析
python src/tools/analyze_numeric_codes.py data/sqlite/main.db --tables zp138,zs65,zm21

# ログファイルを指定
python src/tools/analyze_numeric_codes.py data/sqlite/main.db --log-file logs/analyze_codes.log
```

### オプション

- `-o`, `--output`: レポート出力ファイルのパス
- `--tables`: 処理対象のテーブルをカンマ区切りで指定します
- `--log-file`: ログの出力先ファイルを指定します

## query_executor.py

SQLiteデータベースに対してSQLクエリを実行し、結果を表示するツールです。

### 使用方法

```bash
# 直接クエリを指定
python src/tools/query_executor.py data/sqlite/main.db --query "SELECT * FROM zp138 LIMIT 10"

# ファイルからクエリを読み込む
python src/tools/query_executor.py data/sqlite/main.db --file queries/sample_query.sql

# 実行計画の表示
python src/tools/query_executor.py data/sqlite/main.db --query "SELECT * FROM zp138 WHERE 品目コード = '1234'" --explain

# 結果の行数を制限
python src/tools/query_executor.py data/sqlite/main.db --query "SELECT * FROM zp138" --limit 100

# JSON形式で出力
python src/tools/query_executor.py data/sqlite/main.db --query "SELECT * FROM zp138 LIMIT 10" --output json

# 結果をファイルに保存
python src/tools/query_executor.py data/sqlite/main.db --query "SELECT * FROM zp138 LIMIT 10" --output-file results.txt
```

## db_analyzer.py

SQLiteデータベースの構造と内容を分析し、レポートを生成するツールです。

### 使用方法

```bash
# データベース全体の分析
python src/tools/db_analyzer.py data/sqlite/main.db

# 特定のテーブルの分析
python src/tools/db_analyzer.py data/sqlite/main.db --table zp138

# JSON形式で出力
python src/tools/db_analyzer.py data/sqlite/main.db --output json

# 結果をファイルに保存
python src/tools/db_analyzer.py data/sqlite/main.db --file report.txt
```

## check_table_names.py

テーブル名の対応関係を確認するスクリプトです。

### 使用方法

```bash
# テーブル名の確認
python docs/check_table_names.py data/sqlite/main.db

# 結果をファイルに保存
python docs/check_table_names.py data/sqlite/main.db -o docs/table_names_report.txt
```