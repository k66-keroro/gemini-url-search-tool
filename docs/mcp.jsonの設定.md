### 1. **正しい mcp.json の設定**

json

```json
{
  "mcpServers": {
    "python-server": {
      "command": "uvx",
      "args": ["mcp@latest", "--name", "python-server"],
      "env": {
        "MCP_LOG_LEVEL": "ERROR"
      },
      "disabled": false,
      "autoApprove": ["execute_python"]
    }
  }
}
```

### 2. **または、fastmcp を使用する場合**

json

```json
{
  "mcpServers": {
    "python-server": {
      "command": "uvx",
      "args": ["fastmcp@latest"],
      "disabled": false,
      "autoApprove": ["execute_python"]
    }
  }
}
```

### 3. **事前準備（推奨）**

bash

```bash
# uvでプロジェクトを作成
uv init mcp-python-server
cd mcp-python-server

# MCPパッケージをインストール
uv add "mcp[cli]"

# または fastmcpを使用
uv add fastmcp
```

### 4. **動作確認**

bash

```bash
# パッケージが利用可能か確認
uvx --help

# MCPサーバーをテスト実行
uvx mcp --help
```

公式ドキュメントでは`uv add "mcp[cli]"`の使用が推奨されており、FastMCP は公式 MCP の Python SDK に統合されています [Model Context Protocol](https://modelcontextprotocol.io/quickstart/server)[Firecrawl](https://www.firecrawl.dev/blog/fastmcp-tutorial-building-mcp-servers-python)。

まず上記のいずれかの方法で設定を修正してみてください。

`PS C:\Users\sem3171> uv init mcp-python-server
Initialized project `mcp-python-server`at`C:\Users\sem3171\mcp-python-server`
PS C:\Users\sem3171> cd mcp-python-server
PS C:\Users\sem3171\mcp-python-server> uv add "mcp[cli]"
Using CPython 3.11.1 interpreter at: C:\Users\sem3171\AppData\Local\Programs\Python\Python311\python.exe
Creating virtual environment at: .venv
Resolved 35 packages in 1.48s
Prepared 34 packages in 11.43s
Installed 34 packages in 3.40s

- annotated-types==0.7.0
- anyio==4.9.0
- attrs==25.3.0
- certifi==2025.7.14
- click==8.2.1
- colorama==0.4.6
- h11==0.16.0
- httpcore==1.0.9
- httpx==0.28.1
- httpx-sse==0.4.1
- idna==3.10
- jsonschema==4.24.1
- jsonschema-specifications==2025.4.1
- markdown-it-py==3.0.0
- mcp==1.12.0
- mdurl==0.1.2
- pydantic==2.11.7
- pydantic-core==2.33.2
- pydantic-settings==2.10.1
- pygments==2.19.2
- python-dotenv==1.1.1
- python-multipart==0.0.20
- pywin32==311
- referencing==0.36.2
- rich==14.0.0
- rpds-py==0.26.0
- shellingham==1.5.4
- sniffio==1.3.1
- sse-starlette==2.4.1
- starlette==0.47.1
- typer==0.16.0
- typing-extensions==4.14.1
- typing-inspection==0.4.1
- uvicorn==0.35.0
  PS C:\Users\sem3171\mcp-python-server> uv add fastmcp
  Resolved 49 packages in 13.40s
  Built pyperclip==1.9.0
  Prepared 14 packages in 6.03s
  Installed 14 packages in 2.00s
- authlib==1.6.0
- cffi==1.17.1
- cryptography==45.0.5
- cyclopts==3.22.2
- dnspython==2.7.0
- docstring-parser==0.16
- docutils==0.21.2
- email-validator==2.2.0
- exceptiongroup==1.3.0
- fastmcp==2.10.5
- openapi-pydantic==0.5.1
- pycparser==2.22
- pyperclip==1.9.0
- rich-rst==1.3.1
  PS C:\Users\sem3171\mcp-python-server>`

`PS C:\Users\sem3171> uvx --help
Run a command provided by a Python package.

Usage: uvx [OPTIONS] [COMMAND]

Options:
--from <FROM> Use the given package to provide the command
-w, --with <WITH> Run with the given packages installed
--with-editable <WITH_EDITABLE> Run with the given packages installed in editable mode
--with-requirements <WITH_REQUIREMENTS> Run with all packages listed in the given `requirements.txt` files
-c, --constraints <CONSTRAINTS> Constrain versions using the given requirements files [env: UV_CONSTRAINT=]
-b, --build-constraints <BUILD_CONSTRAINTS> Constrain build dependencies using the given requirements files when building source
distributions [env: UV_BUILD_CONSTRAINT=]
--overrides <OVERRIDES> Override versions using the given requirements files [env: UV_OVERRIDE=]
--isolated Run the tool in an isolated virtual environment, ignoring any already-installed tools
--env-file <ENV_FILE> Load environment variables from a `.env` file [env: UV_ENV_FILE=]
--no-env-file Avoid reading environment variables from a `.env` file [env: UV_NO_ENV_FILE=]
-V, --version Display the uvx version

Index options:
--index <INDEX> The URLs to use when resolving dependencies, in addition to the default index [env:
UV_INDEX=]
--default-index <DEFAULT_INDEX> The URL of the default package index (by default: <https://pypi.org/simple>) [env:
UV_DEFAULT_INDEX=]
-i, --index-url <INDEX_URL> (Deprecated: use `--default-index` instead) The URL of the Python package index (by
default: <https://pypi.org/simple>) [env: UV_INDEX_URL=]
--extra-index-url <EXTRA_INDEX_URL> (Deprecated: use `--index` instead) Extra URLs of package indexes to use, in addition to
`--index-url` [env: UV_EXTRA_INDEX_URL=]
-f, --find-links <FIND_LINKS> Locations to search for candidate distributions, in addition to those found in the
registry indexes [env: UV_FIND_LINKS=]
--no-index Ignore the registry index (e.g., PyPI), instead relying on direct URL dependencies and
those provided via `--find-links`
--index-strategy <INDEX_STRATEGY> The strategy to use when resolving against multiple index URLs [env: UV_INDEX_STRATEGY=]
[possible values: first-index, unsafe-first-match, unsafe-best-match]
--keyring-provider <KEYRING_PROVIDER> Attempt to use `keyring` for authentication for index URLs [env: UV_KEYRING_PROVIDER=]
[possible values: disabled, subprocess]

Resolver options:
-U, --upgrade Allow package upgrades, ignoring pinned versions in any existing output file. Implies
`--refresh`
-P, --upgrade-package <UPGRADE_PACKAGE> Allow upgrades for a specific package, ignoring pinned versions in any existing output
file. Implies `--refresh-package`
--resolution <RESOLUTION> The strategy to use when selecting between the different compatible versions for a given
package requirement [env: UV_RESOLUTION=] [possible values: highest, lowest,
lowest-direct]
--prerelease <PRERELEASE> The strategy to use when considering pre-release versions [env: UV_PRERELEASE=] [possible
values: disallow, allow, if-necessary, explicit, if-necessary-or-explicit]
--fork-strategy <FORK_STRATEGY> The strategy to use when selecting multiple versions of a given package across Python
versions and platforms [env: UV_FORK_STRATEGY=] [possible values: fewest, requires-python]
--exclude-newer <EXCLUDE_NEWER> Limit candidate packages to those that were uploaded prior to the given date [env:
UV_EXCLUDE_NEWER=]
--no-sources Ignore the `tool.uv.sources` table when resolving dependencies. Used to lock against the
standards-compliant, publishable package metadata, as opposed to using any workspace, Git,
URL, or local path sources

Installer options:
--reinstall Reinstall all packages, regardless of whether they're already installed. Implies
`--refresh`
--reinstall-package <REINSTALL_PACKAGE> Reinstall a specific package, regardless of whether it's already installed. Implies
`--refresh-package`
--link-mode <LINK_MODE> The method to use when installing packages from the global cache [env: UV_LINK_MODE=]
[possible values: clone, copy, hardlink, symlink]
--compile-bytecode Compile Python files to bytecode after installation [env: UV_COMPILE_BYTECODE=]

Build options:
-C, --config-setting <CONFIG_SETTING>
Settings to pass to the PEP 517 build backend, specified as `KEY=VALUE` pairs
--no-build-isolation
Disable isolation when building source distributions [env: UV_NO_BUILD_ISOLATION=]
--no-build-isolation-package <NO_BUILD_ISOLATION_PACKAGE>
Disable isolation when building source distributions for a specific package
--no-build
Don't build source distributions [env: UV_NO_BUILD=]
--no-build-package <NO_BUILD_PACKAGE>
Don't build source distributions for a specific package [env: UV_NO_BUILD_PACKAGE=]
--no-binary
Don't install pre-built wheels [env: UV_NO_BINARY=]
--no-binary-package <NO_BINARY_PACKAGE>
Don't install pre-built wheels for a specific package [env: UV_NO_BINARY_PACKAGE=]

Cache options:
-n, --no-cache Avoid reading from or writing to the cache, instead using a temporary directory for the
duration of the operation [env: UV_NO_CACHE=]
--cache-dir <CACHE_DIR> Path to the cache directory [env: UV_CACHE_DIR=]
--refresh Refresh all cached data
--refresh-package <REFRESH_PACKAGE> Refresh cached data for a specific package

Python options:
-p, --python <PYTHON> The Python interpreter to use to build the run environment. [env: UV_PYTHON=]
--managed-python Require use of uv-managed Python versions [env: UV_MANAGED_PYTHON=]
--no-managed-python Disable use of uv-managed Python versions [env: UV_NO_MANAGED_PYTHON=]
--no-python-downloads Disable automatic downloads of Python. [env: "UV_PYTHON_DOWNLOADS=never"]

Global options:
-q, --quiet... Use quiet output
-v, --verbose... Use verbose output
--color <COLOR_CHOICE> Control the use of color in output [possible values: auto, always, never]
--native-tls Whether to load TLS certificates from the platform's native certificate store
[env: UV_NATIVE_TLS=]
--offline Disable network access [env: UV_OFFLINE=]
--allow-insecure-host <ALLOW_INSECURE_HOST> Allow insecure connections to a host [env: UV_INSECURE_HOST=]
--no-progress Hide all progress outputs [env: UV_NO_PROGRESS=]
--directory <DIRECTORY> Change to the given directory prior to running the command
--project <PROJECT> Run the command within the given project directory [env: UV_PROJECT=]
--config-file <CONFIG_FILE> The path to a `uv.toml` file to use for configuration [env: UV_CONFIG_FILE=]
--no-config Avoid discovering configuration files (`pyproject.toml`, `uv.toml`) [env:
UV_NO_CONFIG=]
-h, --help Display the concise help for this command

Use `uv help tool run` for more details.
PS C:\Users\sem3171> uvx mcp --help
Installed 28 packages in 2.21s
Error: typer is required. Install with 'pip install mcp[cli]'
PS C:\Users\sem3171>`

1 個は繋がった 2025-07-18 14:43:15.880 [info] [python-server] Adding new MCP server from updated configuration 2025-07-18 14:43:15.880 [info] [python-server] Registering MCP server and starting connection 2025-07-18 14:43:15.880 [warning] [python-server] Log from MCP Server: Installed 28 packages in 3.02s 2025-07-18 14:43:25.216 [error] [python-server] Failed to connect to MCP server: MCP error -32000: Connection closed 2025-07-18 14:43:25.216 [info] [python-server] MCP connection closed successfully 2025-07-18 14:43:25.217 [error] [python-server] Error connecting to MCP server: MCP error -32000: Connection closed

## 修正された mcp.json

json

```json
{
  "mcpServers": {
    "python-server": {
      "command": "uvx",
      "args": ["fastmcp@latest", "--port", "3001"],
      "env": {
        "PYTHONPATH": ".",
        "PYTHONUNBUFFERED": "1"
      },
      "disabled": false,
      "autoApprove": ["execute_python"]
    }
  }
}
```

## または、より安定した設定

json

```json
{
  "mcpServers": {
    "python-server": {
      "command": "python",
      "args": ["-m", "mcp.server.stdio", "mcp.server.python"],
      "env": {
        "PYTHONPATH": ".",
        "PYTHONUNBUFFERED": "1"
      },
      "disabled": false,
      "autoApprove": ["execute_python"]
    }
  }
}
```

## 診断手順

1. **手動で fastmcp を実行してテスト**

   bash

   ```bash
   uvx fastmcp@latest --help
   ```

2. **Python が正しく動作するか確認**

   bash

   ```bash
   python --version
   python -c "import sys; print(sys.executable)"
   ```

3. **MCP サーバーの直接実行テスト**

   bash

   ```bash
   uvx fastmcp@latest --stdio
   ```

4. **ログレベルを上げて詳細を確認**

   json

   ```json
   {
     "mcpServers": {
       "python-server": {
         "command": "uvx",
         "args": ["fastmcp@latest"],
         "env": {
           "FASTMCP_LOG_LEVEL": "DEBUG",
           "PYTHONUNBUFFERED": "1"
         },
         "disabled": false,
         "autoApprove": ["execute_python"]
       }
     }
   }
   ```

接続エラーの多くは、サーバーの起動方法や通信プロトコルの問題です。上記の設定を試してみて、どれが動作するか確認してください。

`PS C:\Users\sem3171> uvx fastmcp@latest --help
Installed 46 packages in 3.86s
Usage: fastmcp COMMAND

FastMCP 2.0 - The fast, Pythonic way to build MCP servers and clients.

╭─ Commands ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ dev Run an MCP server with the MCP Inspector for development. │
│ inspect Inspect an MCP server and generate a JSON report. │
│ install Install MCP servers in various clients and formats. │
│ run Run an MCP server or connect to a remote one. │
│ version Display version information and platform details. │
│ --help -h Display this message and exit. │
│ --version Display application version. │
╰───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
PS C:\Users\sem3171> python --version
Python 3.11.1
PS C:\Users\sem3171> python -c "import sys; print(sys.executable)"
C:\Users\sem3171\AppData\Local\Programs\Python\Python311\python.exe
PS C:\Users\sem3171> uvx fastmcp@latest --stdio
Installed 46 packages in 2.66s`
