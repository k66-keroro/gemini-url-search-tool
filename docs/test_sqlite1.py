import sqlite3
import os
import sys

def main():
    print(f"Python version: {sys.version}")
    print(f"Current directory: {os.getcwd()}")
    
    # List files in current directory
    print("\nFiles in current directory:")
    for file in os.listdir():
        print(f"- {file}")
    
    # Check if SQLite database exists
    db_path = "data/sqlite/main.db"
    if os.path.exists(db_path):
        print(f"\nDatabase found: {db_path}")
        
        # Connect to database and get table list
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            print("\nTables in database:")
            for table in tables:
                print(f"- {table[0]}")
            
            conn.close()
        except Exception as e:
            print(f"Database connection error: {e}")
    else:
        print(f"\nDatabase not found: {db_path}")
        
        # Check if data/sqlite directory exists
        sqlite_dir = os.path.dirname(db_path)
        if os.path.exists(sqlite_dir):
            print(f"Directory exists: {sqlite_dir}")
            print(f"Files in {sqlite_dir}:")
            for file in os.listdir(sqlite_dir):
                print(f"- {file}")
        else:
            print(f"Directory not found: {sqlite_dir}")

if __name__ == "__main__":
    main()