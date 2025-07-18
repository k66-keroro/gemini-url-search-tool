import sqlite3
import pandas as pd

# Connect to your database
conn = sqlite3.connect("data/sqlite/main.db")

# List all tables
tables = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table'", conn)
print(tables)

# Close the connection
conn.close()
