`PS C:\Users\sem3171> ollama
Usage:
  ollama [flags]
  ollama [command]

Available Commands:
  serve       Start ollama
  create      Create a model from a Modelfile
  show        Show information for a model
  run         Run a model
  stop        Stop a running model
  pull        Pull a model from a registry
  push        Push a model to a registry
  list        List models
  ps          List running models
  cp          Copy a model
  rm          Remove a model
  help        Help about any command

Flags:
  -h, --help      help for ollama
  -v, --version   Show version information

Use "ollama [command] --help" for more information about a command.`

`PS C:\Users\sem3171> ollama run llama2
pulling manifest
pulling 8934d96d3f08: 100% ▕███████████████████████████████████████████████████████████████████████▏ 3.8 GB
pulling 8c17c2ebb0ea: 100% ▕███████████████████████████████████████████████████████████████████████▏ 7.0 KB
pulling 7c23fb36d801: 100% ▕███████████████████████████████████████████████████████████████████████▏ 4.8 KB
pulling 2e0493f67d0c: 100% ▕███████████████████████████████████████████████████████████████████████▏   59 B
pulling fa304d675061: 100% ▕███████████████████████████████████████████████████████████████████████▏   91 B
pulling 42ba7f8a01dd: 100% ▕███████████████████████████████████████████████████████████████████████▏  557 B
verifying sha256 digest
writing manifest
success`
## 💡 補足

- モデルは `llama2` 以外にも `mistral`, `phi3`, `codellama` など選べます
- 軽量モデルならGPUなしでもOK（ただし少し遅いかも）
- `ollama list` でインストール済みモデルを確認できます

json
`{

  "models": [

    {

      "name": "local-llama2",

      "type": "ollama",

      "model": "llama2"

    }

  ]

}`
