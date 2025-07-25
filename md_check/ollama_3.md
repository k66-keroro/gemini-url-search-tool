
Developer: Reload Window

settings.jsonに追加
`{
    // 既存の設定があればここに...

    "continue.config": {
        "name": "Local Assistant",
        "version": "1.0.0",
        "schema": "v1",
        "models": [
            {
                "name": "local-llama2",
                "type": "ollama",
                "model": "llama2",
                "apiBase": "http://localhost:11434"
            }
        ],
        "defaultChatModel": "local-llama2",
        "context": [
            { "provider": "code" },
            { "provider": "docs" },
            { "provider": "diff" },
            { "provider": "terminal" },
            { "provider": "problems" },
            { "provider": "folder" },
            { "provider": "codebase" }
        ]
    }
}`


**Ollamaのメモリ制限設定**

bash

```bash
# PowerShellまたはコマンドプロンプトで
set OLLAMA_MAX_LOADED_MODELS=1
set OLLAMA_NUM_PARALLEL=1
```
- **実行中のモデルを停止**
    
    bash
    
    ```bash
    ollama stop
    # または
    ollama ps
    # 実行中のモデルを確認して個別に停止
    ```
    
- **最軽量モデルで再起動**
    
    bash
    
    ```bash
    ollama run tinyllama
    ```