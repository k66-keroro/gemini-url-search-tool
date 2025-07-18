`PS C:\Users\sem3171> curl -fsSL https://astral.sh/uv/install.ps1                                                                     Invoke-WebRequest : パラメーター名 'fsSL' に一致するパラメーターが見つかりません。                                                   発生場所 行:1 文字:6
+ curl -fsSL https://astral.sh/uv/install.ps1
+      ~~~~~
    + CategoryInfo          : InvalidArgument: (:) [Invoke-WebRequest]、ParameterBindingException
    + FullyQualifiedErrorId : NamedParameterNotFound,Microsoft.PowerShell.Commands.InvokeWebRequestCommand

PS C:\Users\sem3171> curl -fsSL https://astral.sh/uv/install.ps1 | powershell
Invoke-WebRequest : パラメーター名 'fsSL' に一致するパラメーターが見つかりません。
発生場所 行:1 文字:6
+ curl -fsSL https://astral.sh/uv/install.ps1 | powershell
+      ~~~~~
    + CategoryInfo          : InvalidArgument: (:) [Invoke-WebRequest]、ParameterBindingException
    + FullyQualifiedErrorId : NamedParameterNotFound,Microsoft.PowerShell.Commands.InvokeWebRequestCommand`

了解しました！ `uv` を使おうとされたのですね。

今回もエラーが出てしまいましたが、これは `curl` コマンドの使い方の問題です。 PowerShell の `curl` は、一般的な Linux や macOS の `curl` とは少し挙動が異なります。

---

### エラーの原因と解決策

PowerShell の `curl` は実際には `Invoke-WebRequest` のエイリアス（別名）です。 そして、`Invoke-WebRequest` には `-fsSL` というオプションは存在しません。そのため、「パラメーター名 'fsSL' に一致するパラメーターが見つかりません」というエラーが出ているのです。

`uv` のインストールスクリプトを実行するPowerShellの正しいコマンドは、提供されているインストールガイドにも記載されているはずですが、以下のようになります。

PowerShell

```
irm https://astral.sh/uv/install.ps1 | iex
```

- `irm` は `Invoke-RestMethod` のエイリアスで、Webコンテンツを取得するために使われます。
    
- `iex` は `Invoke-Expression` のエイリアスで、取得したスクリプトを実行します。
    

---

### 具体的な対応

PowerShellで、以下のコマンドを実行してみてください。

PowerShell

```
irm https://astral.sh/uv/install.ps1 | iex
```

これで `uv` が正しくインストールされるはずです。試してみてください！

`PS C:\Users\sem3171> irm https://astral.sh/uv/install.ps1 | iex
Downloading uv 0.8.0 (x86_64-pc-windows-msvc)
Installing to C:\Users\sem3171\.local\bin
  uv.exe
  uvx.exe
  uvw.exe
everything's installed!

To add C:\Users\sem3171\.local\bin to your PATH, either restart your shell or run:

    set Path=C:\Users\sem3171\.local\bin;%Path%   (cmd)
    $env:Path = "C:\Users\sem3171\.local\bin;$env:Path"   (powershell)`


`PS C:\Users\sem3171> uv mcp sqlite-mcp-server@latest
error: unrecognized subcommand 'mcp'

Usage: uv.exe [OPTIONS] <COMMAND>

For more information, try '--help'.
PS C:\Users\sem3171> uv mcp file-processing-mcp-server@latest
error: unrecognized subcommand 'mcp'

Usage: uv.exe [OPTIONS] <COMMAND>

For more information, try '--help'.
PS C:\Users\sem3171> uv mcp data-visualization-mcp-server@latest
error: unrecognized subcommand 'mcp'

Usage: uv.exe [OPTIONS] <COMMAND>

For more information, try '--help'.
PS C:\Users\sem3171>`