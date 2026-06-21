import sqlite3
from pathlib import Path

def inspect_database(db_path, base_dir):
    print(f"\n{'='*60}")
    # Print the path relative to the lake/ folder to keep console output clean
    print(f"DATABASE: {db_path.relative_to(base_dir)}")
    print(f"{'='*60}")

    try:
        # Connect in read-only mode just to be safe
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        cursor = conn.cursor()

        # Query the internal sqlite_master table to get all user-created tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name != 'sqlite_sequence';")
        tables = [row[0] for row in cursor.fetchall()]

        if not tables:
            print("  [No tables found in this database]")
            conn.close()
            return

        for table in tables:
            # Get total row count
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            row_count = cursor.fetchone()[0]

            # Get column names using PRAGMA
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [col[1] for col in cursor.fetchall()]

            print(f"\n[{table}] - {row_count} rows")
            print(f"Columns: {', '.join(columns)}")

        conn.close()

    except sqlite3.Error as e:
        print(f"  [!] SQLite Error: {e}")

if __name__ == "__main__":
    # __file__ gets the path to this python script (e.g., .../lake/python/inspect_dbs.py)
    # .resolve().parent gets the python/ directory
    # .parent gets the lake/ directory
    base_dir = Path(__file__).resolve().parent.parent
    
    # Find all .db files recursively starting from the lake/ directory
    db_files = list(base_dir.rglob("*.db"))
    
    if not db_files:
        print(f"No .db files found in {base_dir} or its subdirectories.")
    else:
        print(f"Found {len(db_files)} database(s). Inspecting...")
        for db_file in db_files:
            inspect_database(db_file, base_dir)
            
    print(f"\n{'='*60}\nInspection Complete.\n{'='*60}")