import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "users.db"))

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_users_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with get_connection() as conn:
        # Users table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                balance INTEGER DEFAULT 5, -- 5 free searches upon registration
                subscription_end DATETIME DEFAULT NULL
            )
        """)
        # Anonymous usage table (rate limiting by fingerprint)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS anonymous_usage (
                fingerprint TEXT PRIMARY KEY,
                usage_count INTEGER DEFAULT 0,
                last_used DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
    print(f"[OK] Users database initialized at: {DB_PATH}")

def create_user(email: str, password_hash: str) -> int:
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (email, password_hash) VALUES (?, ?)",
                (email, password_hash)
            )
            conn.commit()
            return cursor.lastrowid
    except sqlite3.IntegrityError:
        return -1 # Email exists

def get_user_by_email(email: str) -> dict | None:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        row = cursor.fetchone()
        return dict(row) if row else None

def get_user_by_id(user_id: int) -> dict | None:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def decrement_balance(user_id: int) -> bool:
    """Decrements balance if user doesn't have an active subscription."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT balance, subscription_end FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        if not row:
            return False
            
        sub_end = row["subscription_end"]
        if sub_end:
            sub_end_dt = datetime.strptime(sub_end, "%Y-%m-%d %H:%M:%S")
            if datetime.utcnow() < sub_end_dt:
                return True # Active subscription, no balance deduction
        
        balance = row["balance"]
        if balance > 0:
            cursor.execute("UPDATE users SET balance = balance - 1 WHERE id = ?", (user_id,))
            conn.commit()
            return True
        return False

def add_balance(user_id: int, amount: int):
    with get_connection() as conn:
        conn.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (amount, user_id))
        conn.commit()

def set_subscription(user_id: int, end_date: datetime):
    with get_connection() as conn:
        conn.execute("UPDATE users SET subscription_end = ? WHERE id = ?", 
                     (end_date.strftime("%Y-%m-%d %H:%M:%S"), user_id))
        conn.commit()

def get_anonymous_usage(fingerprint: str) -> int:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT usage_count FROM anonymous_usage WHERE fingerprint = ?", (fingerprint,))
        row = cursor.fetchone()
        return row["usage_count"] if row else 0

def increment_anonymous_usage(fingerprint: str):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT usage_count FROM anonymous_usage WHERE fingerprint = ?", (fingerprint,))
        row = cursor.fetchone()
        if row:
            cursor.execute("""
                UPDATE anonymous_usage 
                SET usage_count = usage_count + 1, last_used = CURRENT_TIMESTAMP 
                WHERE fingerprint = ?
            """, (fingerprint,))
        else:
            cursor.execute("""
                INSERT INTO anonymous_usage (fingerprint, usage_count) 
                VALUES (?, 1)
            """, (fingerprint,))
        conn.commit()
