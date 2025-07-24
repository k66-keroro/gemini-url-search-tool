# MCP設定ガイド

## MCPとは

Model Context Protocol (MCP) は、AIモデルに外部ツールやデータソースへのアクセスを提供するためのプロトコルです。これにより、AIアシスタントは現実世界のデータやサービスと連携し、より正確で実用的な支援を提供できるようになります。

## MCPサーバーの設定方法

### 設定ファイルの場所

MCPの設定ファイルは以下の場所にあります：

```
.kiro/settings/mcp.json
```

### 基本的な設定例

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "node",
      "args": [
        "C:\\Users\\[ユーザー名]\\AppData\\Roaming\\npm\\node_modules\\@modelcontextprotocol\\server-filesystem\\dist\\index.js",
        "C:\\Users\\[ユーザー名]"
      ],
      "disabled": false,
      "autoApprove": [
        "readFile",
        "writeFile",
        "listDirectory"
      ]
    }
  }
}
```

### 設定項目の説明

- **command**: 実行するコマンド（例：`node`, `python`）
- **args**: コマンドに渡す引数の配列
- **disabled**: サーバーを無効にするかどうか（`true`または`false`）
- **autoApprove**: 自動承認するツールのリスト
- **env**: 環境変数の設定（オプション）

## よくあるエラーと解決策

### 「Failed to connect to MCP server: Connection closed」

このエラーは、MCPサーバーとの接続が確立できない場合に発生します。

**解決策**:
1. 指定したディレクトリが存在し、アクセス権限があることを確認する
2. Node.jsが正しくインストールされていることを確認する
3. MCPサーバーのパッケージが正しくインストールされていることを確認する
4. 絶対パスを使用する（特にWindows環境では重要）

### 「MCP server connection + listTools timed out」

このエラーは、MCPサーバーとの接続は確立したものの、ツールのリスト取得でタイムアウトした場合に発生します。

**解決策**:
1. MCPサーバーの設定を見直す
2. 他のIDEやアプリケーションとの競合がないか確認する
3. ファイアウォール設定を確認する

## MCPサーバーの種類

### 1. Python MCPサーバー

```json
{
  "mcpServers": {
    "python-server": {
      "command": "python",
      "args": [
        "-m",
        "mcp.server.stdio"
      ],
      "env": {
        "PYTHONPATH": ".",
        "PYTHONUNBUFFERED": "1"
      },
      "disabled": false,
      "autoApprove": [
        "execute_python"
      ]
    }
  }
}
```

### 2. Node.js ファイルシステムMCPサーバー

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "node",
      "args": [
        "C:\\Users\\[ユーザー名]\\AppData\\Roaming\\npm\\node_modules\\@modelcontextprotocol\\server-filesystem\\dist\\index.js",
        "C:\\Users\\[ユーザー名]"
      ],
      "disabled": false,
      "autoApprove": [
        "readFile",
        "writeFile",
        "listDirectory"
      ]
    }
  }
}
```

### 3. SQLite MCPサーバー

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

## インストール方法

### Python MCPサーバー

```bash
pip install mcp
```

### Node.js ファイルシステムMCPサーバー

```bash
npm install -g @modelcontextprotocol/server-filesystem
```

### SQLite MCPサーバー

```bash
pip install uvx
```

## トラブルシューティング

1. **MCPサーバーの直接実行テスト**:
   ```bash
   node "C:\Users\[ユーザー名]\AppData\Roaming\npm\node_modules\@modelcontextprotocol\server-filesystem\dist\index.js" "C:\Users\[ユーザー名]"
   ```

2. **パスの確認**:
   ```bash
   where node
   where python
   ```

3. **インストール状況の確認**:
   ```bash
   npm list -g | findstr modelcontextprotocol
   pip list | findstr mcp
   ```