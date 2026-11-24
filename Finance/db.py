import sqlite3

def connect_db():
    conn = sqlite3.connect("finance.db")
    return conn


def create_tables():

    conn = connect_db()

    conn.execute("""
    CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    email TEXT,
    password TEXT)
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS transactions(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    description TEXT,
    amount REAL,
    category TEXT,
    date TEXT)
    """)

    conn.commit()
    conn.close()


# CALL FUNCTION
create_tables()

print("Database and tables created successfully")