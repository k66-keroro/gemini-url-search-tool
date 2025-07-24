# SQLite GUI Tool モジュール化ドキュメント

## 概要

SQLite GUI Toolをモジュール化し、保守性と拡張性を向上させました。このドキュメントでは、モジュール化の構造と各コンポーネントの役割について説明します。

## ディレクトリ構造

```
src/core/
├── sqlite_gui_tool/              # モジュール化されたGUIツール
│   ├── __init__.py              # パッケージ初期化
│   ├── app.py                   # メインアプリケーションクラス
│   ├── base_tab.py              # 基底タブクラス
│   ├── query_tab.py             # クエリ実行タブ
│   ├── schema_tab.py            # スキーマ表示タブ
│   ├── import_tab.py            # データインポートタブ
│   ├── export_tab.py            # データエクスポートタブ
│   ├── analyze_tab.py           # データ分析タブ
│   └── code_converter_tab.py    # コードフィールド変換タブ
├── sqlite_gui_tool_v2_fixed_modular.py  # エントリーポイント
└── sqlite_manager_wrapper.py    # SQLiteManager簡易ラッパー
```

## コンポーネントの説明

### 1. エントリーポイント (`sqlite_gui_tool_v2_fixed_modular.py`)

アプリケーションのエントリーポイントです。Tkinterのルートウィンドウを作成し、SQLiteGUIToolクラスのインスタンスを初期化します。

### 2. メインアプリケーションクラス (`app.py`)

アプリケーション全体を管理するクラスです。以下の機能を提供します：

- タブの初期化と管理
- データベース接続の管理
- 共通機能の提供

### 3. 基底タブクラス (`base_tab.py`)

すべてのタブの基底クラスです。共通の機能を提供します：

- UIの基本構造
- データベース接続イベントの処理
- ユーティリティメソッド

### 4. 各機能タブ

各タブは特定の機能を担当します：

- **クエリ実行タブ** (`query_tab.py`): SQLクエリの実行と結果表示
- **スキーマ表示タブ** (`schema_tab.py`): テーブル構造の表示
- **データインポートタブ** (`import_tab.py`): 外部ファイルからのデータインポート
- **データエクスポートタブ** (`export_tab.py`): データのCSV/Excel形式でのエクスポート
- **データ分析タブ** (`analyze_tab.py`): データの統計分析
- **コードフィールド変換タブ** (`code_converter_tab.py`): コードフィールドの検出と変換

### 5. SQLiteManagerラッパー (`sqlite_manager_wrapper.py`)

SQLiteManagerの簡易版ラッパーです。元のSQLiteManagerクラスとの互換性を保ちながら、モジュール化されたGUIツールで使用できるようにしています。

## クラス間の関係

```
SQLiteGUITool (app.py)
  ├── QueryTab
  ├── SchemaTab
  ├── ImportTab
  ├── ExportTab
  ├── AnalyzeTab
  └── CodeConverterTab
```

各タブクラスは、メインアプリケーションクラス（SQLiteGUITool）への参照を持ち、必要に応じてメインアプリケーションのメソッドを呼び出します。

## 拡張方法

新しいタブを追加する場合は、以下の手順に従います：

1. `base_tab.py`を継承した新しいタブクラスを作成
2. `app.py`の`init_tabs`メソッドに新しいタブを追加
3. 必要に応じて、メインアプリケーションクラスに新しいメソッドを追加

## 注意事項

- タブ間の連携が必要な場合は、メインアプリケーションクラスを介して行います
- データベース接続は、メインアプリケーションクラスで一元管理されます
- 各タブは、`on_db_connect`と`on_db_disconnect`メソッドを実装して、データベース接続状態の変化に対応します