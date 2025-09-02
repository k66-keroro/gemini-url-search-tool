---
title: MCP活用ガイドライン
inclusion: always
---

# Model Context Protocol (MCP) 活用ガイドライン

## MCPとは

Model Context Protocol (MCP) は、AIモデルに外部ツールやデータソースへのアクセスを提供するためのプロトコルです。これにより、AIアシスタントは現実世界のデータやサービスと連携し、より正確で実用的な支援を提供できるようになります。

## MCP活用のメリット

1. **リアルタイムデータアクセス**:
   - 最新のデータベース情報を取得
   - 外部APIからの情報取得
   - ファイルシステムの直接操作

2. **拡張機能**:
   - カスタムツールの統合
   - 特定のドメイン向けの専門機能
   - 自動化ワークフローの構築

3. **セキュリティと制御**:
   - 権限管理
   - アクセス制限
   - 操作の監査

## 本プロジェクトでのMCP活用方法

### 1. データベース操作ツール

```json
{
  "mcpServers": {
    "sqlite-tools": {
      "command": "uvx",
      "args": ["sqlite-mcp-server@latest"],
      "env": {
        "FASTMCP_LOG_LEVEL": "ERROR"
      },
      "disabled": false,
      "autoApprove": ["query_database", "list_tables"]
    }
  }
}
```

このツールにより、以下の操作が可能になります：

- SQLiteデータベースへのクエリ実行
- テーブル一覧の取得
- スキーマ情報の取得
- データの可視化

### 2. ファイル処理ツール

```json
{
  "mcpServers": {
    "file-processor": {
      "command": "uvx",
      "args": ["file-processing-mcp-server@latest"],
      "env": {
        "FASTMCP_LOG_LEVEL": "ERROR"
      },
      "disabled": false,
      "autoApprove": ["analyze_file", "detect_encoding"]
    }
  }
}
```

このツールにより、以下の操作が可能になります：

- ファイルのエンコーディング検出
- CSVファイルの分析
- データ型の推論
- ファイル統計情報の取得

### 3. データ可視化ツール

```json
{
  "mcpServers": {
    "data-viz": {
      "command": "uvx",
      "args": ["data-visualization-mcp-server@latest"],
      "env": {
        "FASTMCP_LOG_LEVEL": "ERROR"
      },
      "disabled": false,
      "autoApprove": ["create_chart", "generate_report"]
    }
  }
}
```

このツールにより、以下の操作が可能になります：

- データの可視化グラフ作成
- レポート生成
- ダッシュボード要素の作成

## MCP設定方法

### 1. 設定ファイルの作成

`.kiro/settings/mcp.json` ファイルを作成し、必要なMCPサーバーを設定します：

```json
{
  "mcpServers": {
    "sqlite-tools": {
      "command": "uvx",
      "args": ["sqlite-mcp-server@latest"],
      "env": {
        "FASTMCP_LOG_LEVEL": "ERROR"
      },
      "disabled": false,
      "autoApprove": ["query_database", "list_tables"]
    },
    "file-processor": {
      "command": "uvx",
      "args": ["file-processing-mcp-server@latest"],
      "env": {
        "FASTMCP_LOG_LEVEL": "ERROR"
      },
      "disabled": false,
      "autoApprove": ["analyze_file", "detect_encoding"]
    },
    "data-viz": {
      "command": "uvx",
      "args": ["data-visualization-mcp-server@latest"],
      "env": {
        "FASTMCP_LOG_LEVEL": "ERROR"
      },
      "disabled": false,
      "autoApprove": ["create_chart", "generate_report"]
    }
  }
}
```

### 2. 必要なパッケージのインストール

```bash
# uvのインストール
pip install uv

# MCPサーバーの実行に必要なuvxのインストール
pip install uvx
```

### 3. MCPサーバーの起動

Kiro IDEは設定ファイルを読み込み、自動的にMCPサーバーを起動します。手動で起動する場合は以下のコマンドを使用します：

```bash
uvx sqlite-mcp-server@latest
```

## MCP使用例

### SQLiteデータベースのクエリ

```python
# MCPを使用してSQLiteデータベースにクエリを実行
result = mcp.query_database(
    database_path="data/sqlite/main.db",
    query="SELECT * FROM zp02 LIMIT 10"
)
print(result)
```

### ファイルエンコーディングの検出

```python
# MCPを使用してファイルのエンコーディングを検出
encoding_info = mcp.detect_encoding(
    file_path="data/raw/zm37.txt"
)
print(f"Detected encoding: {encoding_info['encoding']}")
```

### データの可視化

```python
# MCPを使用してデータの可視化グラフを作成
chart = mcp.create_chart(
    data_source="data/sqlite/main.db",
    query="SELECT 日付, 数量 FROM zs65 WHERE 品目コード='ABC123'",
    chart_type="line",
    title="品目別在庫推移"
)
chart.save("reports/inventory_trend.png")
```

## MCP使用時の注意点

1. **セキュリティ**:
   - 信頼できるMCPサーバーのみを使用
   - 機密データへのアクセスには注意

2. **パフォーマンス**:
   - 大量のデータ処理は時間がかかる場合がある
   - クエリの最適化を検討

3. **エラーハンドリング**:
   - MCPツールからのエラーを適切に処理
   - フォールバックメカニズムを実装