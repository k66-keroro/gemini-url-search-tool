・モデル一覧
ollama list
・
ollama show llama2

`curl http://localhost:11434`



# システム全体のメモリ使用量
`Get-WmiObject -Class Win32_OperatingSystem | Select-Object @{Name="TotalMemoryGB";Expression={[math]::round($_.TotalVisibleMemorySize/1MB,2)}}, @{Name="FreeMemoryGB";Expression={[math]::round($_.FreePhysicalMemory/1MB,2)}}`

# Ollamaプロセスのメモリ使用量
`Get-Process ollama -ErrorAction SilentlyContinue | Select-Object Name, @{Name="MemoryMB";Expression={[math]::round($_.WorkingSet/1MB,2)}}`

日本語対応
### 3. 推奨アプローチ

**段階的に試してみることをお勧めします：**

1. **現在のTinyLlamaで試用**
    - 基本的な英語でのコーディング支援
    - 簡単な日本語コメント生成
2. **Qwen2.5 0.5Bを追加**
    - 日本語対応が良好
    - メモリ使用量も軽量（397MB）
    - 必要に応じて切り替え可能
3. **メモリに余裕があればGemma2 2Bも**
    - より高品質な日本語対応
    - ただし、メモリ使用量は増加

### 4. 実際の設定手順

日本語対応を試したい場合：

bash

```bash
# Qwen2.5 0.5Bモデルをダウンロード
ollama pull qwen2.5:0.5b

# 必要に応じてGemma2 2Bも
ollama pull gemma2:2b
```

その後、上記の日本語対応設定ファイルを適用すれば、モデルを切り替えながら使用できます。

まずは現在のTinyLlamaで少し試してみて、日本語対応の必要性を感じたら追加モデルを検討されてはいかがでしょうか？