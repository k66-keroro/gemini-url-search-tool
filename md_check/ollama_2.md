## 1. Ollama の動作確認

まず、Ollama が正常に動作していることを確認：

bash

```bash
# Ollama のステータス確認
ollama list

# llama2 モデルの存在確認
ollama show llama2

# API エンドポイントの動作確認
curl http://localhost:11434/api/generate -d '{"model": "llama2", "prompt": "Hello"}'
```

## 2. Continue の設定ファイル

Continue の設定は `~/.continue/config.json` に配置する必要があります。あなたの設定は正しく見えますが、以下の点を確認してください：

json

```json
{
  "models": [
    {
      "title": "Local Llama2",
      "provider": "ollama",
      "model": "llama2",
      "apiBase": "http://localhost:11434"
    }
  ],
  "tabAutocompleteModel": {
    "title": "Local Llama2",
    "provider": "ollama", 
    "model": "llama2",
    "apiBase": "http://localhost:11434"
  },
  "customCommands": [
    {
      "name": "test",
      "prompt": "Write a simple hello world function"
    }
  ]
}
```

## 3. トラブルシューティング手順

### 設定ファイルの場所確認

bash

```bash
# Windows
%USERPROFILE%\.continue\config.json

# macOS/Linux
~/.continue/config.json
```

### Continue 拡張機能の再起動

1. VSCode で `Ctrl+Shift+P` (または `Cmd+Shift+P`)
2. `Continue: Reload Config` を実行
3. VSCode を再起動

### ログの確認

1. Continue パネルを開く
2. 設定歯車アイコンをクリック
3. "View Logs" でエラーを確認

## 4. 代替設定

もし上記で解決しない場合は、以下の設定を試してください：

json

```json
{
  "models": [
    {
      "title": "Llama2",
      "provider": "ollama",
      "model": "llama2"
    }
  ],
  "allowAnonymousTelemetry": false,
  "embeddingsProvider": {
    "provider": "ollama",
    "model": "nomic-embed-text"
  }
}
```

## 5. 一般的な問題と解決策

- **ポート競合**: `ollama serve --host 0.0.0.0:11434` で明示的にポート指定
- **モデル名**: `ollama list` で正確なモデル名を確認
- **権限問題**: 管理者権限でVSCodeを起動

どの段階で問題が発生していますか？エラーメッセージがあれば教えてください。



NAME             ID              SIZE      MODIFIED
llama2:latest    78e26419b446    3.8 GB    2 hours ago

## 5. 推奨モデル（メモリ別）

- **2GB以下**: `tinyllama`
- **3GB程度**: `gemma:2b`
- **4GB程度**: `phi3:mini`
- **6GB程度**: `llama2:7b-chat-q2_K`

`PS C:\Users\sem3171> ollama list
NAME                ID              SIZE      MODIFIED
tinyllama:latest    2644915ede35    637 MB    About an hour ago
llama2:latest       78e26419b446    3.8 GB    3 hours ago`


Developer Tools