import sqlite3
import pandas as pd
import os
import sys
from datetime import datetime

def analyze_table(conn, table_name):
    """Analyze a single table and return its structure and sample data"""
    print(f"\n{'='*50}")
    print(f"Table: {table_name}")
    print(f"{'='*50}")
    
    # Get column information
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    
    print("\nColumn Structure:")
    for col in columns:
        print(f"- {col[1]} ({col[2]})")
    
    # Get row count
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    row_count = cursor.fetchone()[0]
    print(f"\nRow Count: {row_count}")
    
    # Get sample data (first 5 rows)
    if row_count > 0:
        print("\nSample Data (first 5 rows):")
        try:
            df = pd.read_sql_query(f"SELECT * FROM {table_name} LIMIT 5", conn)
            print(df)
        except Exception as e:
            print(f"Error fetching sample data: {e}")
    
    # Check for primary keys
    cursor.execute(f"PRAGMA table_info({table_name})")
    primary_keys = [col[1] for col in cursor.fetchall() if col[5] == 1]
    if primary_keys:
        print(f"\nPrimary Key(s): {', '.join(primary_keys)}")
    else:
        print("\nNo explicit primary key defined")
    
    # Check for indexes
    cursor.execute(f"PRAGMA index_list({table_name})")
    indexes = cursor.fetchall()
    if indexes:
        print("\nIndexes:")
        for idx in indexes:
            print(f"- {idx[1]}")
    else:
        print("\nNo indexes defined")

def main():
    print(f"Python version: {sys.version}")
    print(f"Current directory: {os.getcwd()}")
    print(f"Analysis time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Connect to database
    db_path = "data/sqlite/main.db"
    if not os.path.exists(db_path):
        print(f"Database not found: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    
    # Get list of tables
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()
    
    print(f"\nFound {len(tables)} tables in database")
    
    # Ask user which tables to analyze
    print("\nAvailable tables:")
    for i, table in enumerate(tables):
        print(f"{i+1}. {table[0]}")
    
    print("\nOptions:")
    print("1. Analyze all tables")
    print("2. Analyze specific tables")
    print("3. Analyze tables matching a pattern")
    
    choice = input("\nEnter your choice (1-3): ")
    
    if choice == "1":
        # Analyze all tables
        for table in tables:
            analyze_table(conn, table[0])
    elif choice == "2":
        # Analyze specific tables
        table_indices = input("Enter table numbers separated by commas (e.g., 1,3,5): ")
        indices = [int(idx.strip()) for idx in table_indices.split(",")]
        for idx in indices:
            if 1 <= idx <= len(tables):
                analyze_table(conn, tables[idx-1][0])
            else:
                print(f"Invalid table number: {idx}")
    elif choice == "3":
        # Analyze tables matching a pattern
        pattern = input("Enter pattern to match (e.g., zp for all tables starting with zp): ")
        matching_tables = [table[0] for table in tables if pattern.lower() in table[0].lower()]
        print(f"Found {len(matching_tables)} matching tables")
        for table in matching_tables:
            analyze_table(conn, table)
    else:
        print("Invalid choice")
    
    conn.close()

if __name__ == "__main__":
    main()