# database.py
import sqlite3
import os

DB_PATH = "data/database.db"

def init_db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS packages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT,
        package_type TEXT,
        accounts TEXT,
        count INTEGER,
        status TEXT DEFAULT 'available'
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS purchases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        username TEXT,
        package_id INTEGER,
        invoice_id TEXT,
        status TEXT DEFAULT 'pending',
        ref_by INTEGER
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS referrals (
        user_id INTEGER PRIMARY KEY,
        ref_count INTEGER DEFAULT 0,
        earned REAL DEFAULT 0.0
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT
    )''')
    conn.commit()
    conn.close()

def save_user(user_id, username):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO users (user_id, username) VALUES (?, ?)", (user_id, username or "NoName"))
    conn.commit()
    conn.close()

def add_package(category, package_type, accounts):
    conn = sqlite3.connect("data/database.db")
    c = conn.cursor()
    accounts_str = "\n".join(accounts)
    c.execute("""
        INSERT INTO packages (category, package_type, accounts, status)
        VALUES (?, ?, ?, 'available')
    """, (category, package_type, accounts_str))
    conn.commit()
    pid = c.lastrowid
    conn.close()
    return pid

def get_available_package(category, size):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM packages WHERE category=? AND package_type=? AND status='available' LIMIT 1", (category, size))
    row = c.fetchone()
    conn.close()
    return dict(zip([d[0] for d in c.description], row)) if row else None

def get_package_by_id(package_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM packages WHERE id=?", (package_id,))
    row = c.fetchone()
    conn.close()
    return dict(zip([d[0] for d in c.description], row)) if row else None

def mark_package_sold(package_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE packages SET status='sold' WHERE id=?", (package_id,))
    c.execute("DELETE FROM packages WHERE id=?", (package_id,))
    conn.commit()
    conn.close()

def add_purchase(user_id, username, package_id, invoice_id, ref_by=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO purchases (user_id, username, package_id, invoice_id, ref_by, status) VALUES (?, ?, ?, ?, ?, 'pending')",
              (user_id, username, package_id, invoice_id, ref_by))
    conn.commit()
    conn.close()

def get_user_purchases(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""SELECT p.*, pkg.category, pkg.package_type FROM purchases p
                 JOIN packages pkg ON p.package_id = pkg.id
                 WHERE p.user_id=? ORDER BY p.id DESC""", (user_id,))
    rows = c.fetchall()
    conn.close()
    return [dict(zip([d[0] for d in c.description], row)) for row in rows]

def add_referral(buyer_id, ref_by, reward=5.0):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO referrals (user_id, ref_count, earned) VALUES (?, 0, 0)", (ref_by,))
    c.execute("UPDATE referrals SET ref_count = ref_count + 1 WHERE user_id=?", (ref_by,))
    c.execute("UPDATE referrals SET earned = earned + ? WHERE user_id=? AND earned = 0", (reward, ref_by))
    conn.commit()
    conn.close()

def get_referral_stats(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT ref_count, earned FROM referrals WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    return {"count": row[0] if row else 0, "earned": row[1] if row else 0.0}
    # В конец database.py
def get_available_count(category, size):
    conn = sqlite3.connect("data/database.db")
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM packages WHERE category=? AND package_type=? AND status='available'", (category, size))
    count = c.fetchone()[0]
    conn.close()
    return count