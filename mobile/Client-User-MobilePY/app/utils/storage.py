import base64
import json
import sqlite3

DB_NAME = "tconecta.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS auth (key TEXT PRIMARY KEY, value TEXT)")
    conn.commit()
    conn.close()


def save(key: str, value: str):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO auth (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()


def get(key: str) -> str | None:
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT value FROM auth WHERE key = ?", (key,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None


def clear():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM auth")
    conn.commit()
    conn.close()


def decode_jwt(token: str) -> dict:
    try:
        payload = token.split(".")[1]
        payload += "=" * (4 - len(payload) % 4)
        data = json.loads(base64.b64decode(payload))
        role = data.get("role") or data.get(
            "http://schemas.microsoft.com/ws/2008/06/identity/claims/role", "User"
        )
        return {"id": data.get("sub"), "cui": data.get("cui"), "role": role, "exp": data.get("exp")}
    except Exception:
        return {}
