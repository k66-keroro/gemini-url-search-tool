{
  "mcpServers": {
    "python-server": {
      "command": "python",
      "args": [
        "-m",
        "fastmcp",
        "run",
        "--stdio",
        "--port",
        "3001",
        "--log-level",
        "DEBUG"
      ],
      "env": {
        "PYTHONPATH": ".",
        "PYTHONUNBUFFERED": "1",
        "FASTMCP_LOG_LEVEL": "DEBUG"
      },
      "disabled": false,
      "autoApprove": [
        "execute_python"
      ]
    }
  }
}
