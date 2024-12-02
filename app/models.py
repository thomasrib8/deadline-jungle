import sqlite3

DB_NAME = 'tasks.db'

def connect_db():
    return sqlite3.connect(DB_NAME)

def init_db():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS tasks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL,
                        start_date TEXT NOT NULL,
                        end_date TEXT NOT NULL,
                        assigned_to TEXT NOT NULL,
                        status TEXT DEFAULT 'Pending'
                    )''')
    conn.commit()
    conn.close()
