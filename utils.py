# utils.py
import sqlite3

def get_referral_stats(user_id):
    conn = sqlite3.connect("data/database.db")
    c = conn.cursor()
    c.execute("SELECT ref_count, earned FROM referrals WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    return {"count": row[0] if row else 0, "earned": row[1] if row else 0.0}