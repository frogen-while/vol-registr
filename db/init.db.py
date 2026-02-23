import sqlite3
import os

def init_database():
    db_dir = os.path.dirname(os.path.abspath(__file__))
    sql_file_path = os.path.join(db_dir, 'init_reg.sql')
    db_path = os.path.join(db_dir, 'database.db')
    
    with open(sql_file_path, 'r') as sql_file:
        sql_script = sql_file.read()
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.executescript(sql_script)
    
    conn.commit()
    conn.close()
    
    print(f"Database initialized successfully at {db_path}")

if __name__ == '__main__':
    init_database()