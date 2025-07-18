# MCPを使用してSQLiteデータベースにクエリを実行
result = mcp.query_database(
    database_path="data/sqlite/main.db",
    query="SELECT * FROM t_zp138引当 LIMIT 10"
)
print(result)