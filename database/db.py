import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "schedule.db")

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    # Create Users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        discord_id TEXT PRIMARY KEY,
        student_code TEXT NOT NULL,
        password_encrypted TEXT,
        last_sync DATETIME
    );
    """)
    
    # Create Schedules table
    # We store individual class sessions
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS schedules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        subject_name TEXT,
        subject_code TEXT,
        class_code TEXT,
        teacher TEXT,
        room TEXT,
        date DATE,
        period_start INTEGER,
        period_count INTEGER,
        unique_id TEXT, -- to prevent duplicates (e.g. subject_code + date + period)
        FOREIGN KEY(user_id) REFERENCES users(discord_id)
    );
    """)
    
    conn.commit()
    conn.close()
    print(f"Database initialized at {DB_PATH}")

if __name__ == "__main__":
    init_db()
