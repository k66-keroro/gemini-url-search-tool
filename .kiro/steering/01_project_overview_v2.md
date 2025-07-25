---
title: プロジェクト概要 v2.0 (モジュラー版)
inclusion: always
---

# SQLite GUI Tool - モジュラー版

## プロジェクト概要

既存の手動データ更新処理を自動化・効率化するためのPythonツールです。モジュラー化されたアーキテクチャにより、保守性と拡張性を向上させました。

## アーキテクチャの変更点

### v1.0 (モノリシック版)
- 単一の大きなファイル (`sqlite_gui_tool_v2_fixed.py`)
- すべての機能が一つのクラスに集約
- 保守が困難

### v2.0 (モジュラー版)
- 機能別にタブモジュールを分離
- 各タブが独立したクラスとして実装
- 保守性と拡張性の向上

## 主要コンポーネント

### 1. エントリーポイント
- **`src/core/sqlite_gui_tool_v2_fixed_modular.py`** - アプリケーションの起動点

### 2. コアアプリケーション
- **`src/core/sqlite_gui_tool/app.py`** - メインアプリケーションクラス
- **`src/core/sqlite_gui_tool/__init__.py`** - モジュール初期化

### 3. タブモジュール
- **`src/core/sqlite_gui_tool/query_tab.py`** - SQLクエリ実行機能
- **`src/core/sqlite_gui_tool/schema_tab.py`** - データベーススキーマ表示
- **`src/core/sqlite_gui_tool/import_tab.py`** - データインポート機能
- **`src/core/sqlite_gui_tool/export_tab.py`** - データエクスポート機能
- **`src/core/sqlite_gui_tool/analyze_tab.py`** - データ分析機能
- **`src/core/sqlite_gui_tool/code_converter_tab.py`** - コードフィールド変換
- **`src/core/sqlite_gui_tool/admin_tab.py`** - データベース管理機能

### 4. 基底クラス
- **`src/core/sqlite_gui_tool/base_tab.py`** - タブの基底クラス

### 5. サポートモジュール
- **`src/core/sqlite_manager_wrapper.py`** - SQLiteManager のラッパー
- **`src/core/sqlite_manager.py`** - データベース操作のコアロジック

## 主要機能

### 1. クエリ実行タブ
- SQLクエリの実行
- 結果の表示とエクスポート
- クエリ履歴の管理

### 2. スキーマタブ
- テーブル一覧の表示
- カラム情報の詳細表示
- インデックス情報の表示
- CREATE文の表示

### 3. インポートタブ
- CSV、TSV、Excelファイルのインポート
- エンコーディング自動検出
- データプレビュー機能

### 4. エクスポートタブ
- テーブルデータのエクスポート
- カスタムクエリ結果のエクスポート
- CSV、Excelフォーマット対応

### 5. データ分析タブ
- データ統計情報の表示
- 頻度分布の分析
- NULL値チェック

### 6. コードフィールド変換タブ
- 数値コードフィールドの分析
- データ型変換機能

### 7. DB管理タブ（重要）
- **全件データ更新機能**: data/rawフォルダの全ファイルを自動処理
- **ZP138個別処理**: ZP138.txtファイルの引当計算付き特殊処理
- **テーブル情報表示**: テーブル名と元ファイル名の対応表示
- テーブル削除機能
- VACUUM操作
- データベース診断

## 全件データ更新機能の詳細

### 処理フロー
1. **既存テーブル削除**: すべてのユーザーテーブルを削除
2. **ファイル自動検出**: data/rawフォルダ内のファイルを自動検出
3. **ファイル処理**: 各ファイルを適切な形式で読み込み
4. **テーブル作成**: ファイルごとにテーブルを作成
5. **データ型最適化**: 日付、コード列などの自動変換

### サポートファイル形式
- **CSV**: カンマ区切り
- **TSV**: タブ区切り
- **TXT**: 自動区切り文字検出
- **Excel**: .xlsx, .xls

### 特殊ファイル対応
- **zm37.txt**: CP932エンコーディング、特殊区切り文字
- **PP_SUMMARY_ZTBP080_KOJOZISSEKI_D_0.xlsx**: ヘッダー7行の特殊Excel
- **ZP138.txt**: 引当計算付きの特殊処理（在庫管理計算）

## 技術スタック

- **言語**: Python 3.8+
- **GUI**: tkinter
- **データベース**: SQLite
- **主要ライブラリ**:
  - pandas: データ処理
  - sqlite3: データベース操作
  - chardet: エンコーディング検出
  - openpyxl: Excel処理

## ファイル構造

```
claude-test/
├── src/
│   └── core/
│       ├── sqlite_gui_tool_v2_fixed_modular.py  # エントリーポイント
│       ├── sqlite_manager.py                    # データベース操作
│       ├── sqlite_manager_wrapper.py            # ラッパー
│       └── sqlite_gui_tool/                     # モジュラー実装
│           ├── __init__.py
│           ├── app.py                           # メインアプリ
│           ├── base_tab.py                      # 基底クラス
│           ├── query_tab.py                     # クエリ実行
│           ├── schema_tab.py                    # スキーマ表示
│           ├── import_tab.py                    # インポート
│           ├── export_tab.py                    # エクスポート
│           ├── analyze_tab.py                   # データ分析
│           ├── code_converter_tab.py            # コード変換
│           └── admin_tab.py                     # DB管理
├── data/
│   ├── raw/                                     # 入力データ
│   └── sqlite/                                  # SQLiteDB
│       └── main.db
└── .kiro/
    └── steering/                                # ドキュメント
```

## 使用方法

### 起動
```bash
python src/core/sqlite_gui_tool_v2_fixed_modular.py
```

### 基本的なワークフロー
1. **データベース接続**: 「データベース接続」ボタンでSQLiteファイルを選択
2. **全件データ更新**: DB管理タブで「全件データ更新」を実行
3. **データ確認**: スキーマタブでテーブル構造を確認
4. **クエリ実行**: クエリタブでデータを検索・分析
5. **データエクスポート**: 必要に応じてデータをエクスポート

## 開発ガイドライン

### 新しいタブの追加
1. `src/core/sqlite_gui_tool/` に新しいタブファイルを作成
2. `BaseTab` クラスを継承
3. `app.py` の `init_tabs` メソッドに追加

### エラーハンドリング
- 各タブで適切な例外処理を実装
- ユーザーフレンドリーなエラーメッセージを表示
- ログ出力による詳細なデバッグ情報

### パフォーマンス
- 大量データ処理時のメモリ使用量に注意
- UIの応答性を保つための適切な更新処理
- データベース操作の最適化