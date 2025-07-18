# MCP (Model Context Protocol) セットアップガイド

このドキュメントでは、プロジェクトでMCPを使用するためのセットアップ手順を説明します。

## 前提条件

- Python 3.8以上がインストールされていること
- pipがインストールされていること

## インストール手順

### 1. astral.shのインストール

MCPサーバーを実行するには、astral.shのツールチェーンが必要です。以下の手順でインストールします：

```bash
# Windowsの場合
curl -fsSL https://astral.sh/uv/install.ps1 | powershell

# macOS/Linuxの場合
curl -fsSL https://astral.sh/uv/install.sh | bash
```

**注意**: 
- `pip install uvx`や`pip install uvenv`を実行するとエラーになります。
- Windowsでは特に依存関係の問題が発生する可能性があります。
- 公式のインストール方法を使用することをお勧めします。

### 2. MCPサーバーの設定

MCPサーバーの設定は、`.kiro/settings/mcp.json`ファイルで管理されています。このファイルは既に作成済みで、以下のMCPサーバーが設定されています：

- **sqlite-tools**: SQLiteデータベースの操作
- **file-processor**: ファイル処理と分析
- **data-viz**: データ可視化

### 3. MCPサーバーの起動

Kiro IDEは設定ファイルを読み込み、自動的にMCPサーバーを起動します。手動で起動する場合は以下のコマンドを使用します：

```bash
# SQLite MCPサーバーを起動
uv mcp sqlite-mcp-server@latest

# ファイル処理MCPサーバーを起動
uv mcp file-processing-mcp-server@latest

# データ可視化MCPサーバーを起動
uv mcp data-visualization-mcp-server@latest
```

**注意**: コマンドは`uvx`ではなく`uv mcp`を使用します。

## MCPの使用例

### SQLiteデータベースのクエリ

```python
# MCPを使用してSQLiteデータベースにクエリを実行
result = mcp.query_database(
    database_path="data/sqlite/main.db",
    query="SELECT * FROM t_zp138引当 LIMIT 10"
)
print(result)
```

### ファイルエンコーディングの検出

```python
# MCPを使用してファイルのエンコーディングを検出
encoding_info = mcp.detect_encoding(
    file_path="data/raw/ZP138.txt"
)
print(f"Detected encoding: {encoding_info['encoding']}")
```

### データの可視化

```python
# MCPを使用してデータの可視化グラフを作成
chart = mcp.create_chart(
    data_source="data/sqlite/main.db",
    query="SELECT 所要日付, 入庫_所要量 FROM t_zp138引当 WHERE 品目='ABC123'",
    chart_type="line",
    title="品目別在庫推移"
)
chart.save("reports/inventory_trend.png")
```

## トラブルシューティング

### MCPサーバーが起動しない場合

1. uvが正しくインストールされているか確認
2. `.kiro/settings/mcp.json`ファイルの構文が正しいか確認
3. コマンドラインから手動でMCPサーバーを起動して、エラーメッセージを確認

### MCPツールが機能しない場合

1. MCPサーバーが起動しているか確認
2. Kiro IDEのMCPサーバービューで接続状態を確認
3. 必要に応じてMCPサーバーを再起動