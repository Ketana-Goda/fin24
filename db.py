import hashlib
import hmac
import os
import sqlite3
from datetime import datetime

DB_PATH = "data/fin24.db"
ROLES = ("finance_manager", "viewer")


def get_conn():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    conn.execute("""CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password_hash TEXT NOT NULL,
        salt TEXT NOT NULL,
        role TEXT NOT NULL)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS decisions (
        vendor TEXT PRIMARY KEY,
        decision TEXT NOT NULL,
        decided_by TEXT,
        decided_at TEXT)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS contracts (
        vendor TEXT PRIMARY KEY,
        owner TEXT,
        contract_end TEXT,
        notice_days INTEGER,
        updated_by TEXT,
        updated_at TEXT)""")
    conn.commit()
    conn.close()


# ---------- passwords ----------
def _hash(password, salt_hex):
    return hashlib.pbkdf2_hmac(
        "sha256", password.encode(), bytes.fromhex(salt_hex), 200_000
    ).hex()


def add_user(username, password, role):
    if role not in ROLES:
        raise ValueError(f"Role must be one of {ROLES}")
    init_db()
    salt = os.urandom(16).hex()
    conn = get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO users (username, password_hash, salt, role) VALUES (?,?,?,?)",
        (username, _hash(password, salt), salt, role),
    )
    conn.commit()
    conn.close()


def check_login(username, password):
    """Return the user's role if the login is correct, otherwise None."""
    init_db()
    conn = get_conn()
    row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    if row and hmac.compare_digest(_hash(password, row["salt"]), row["password_hash"]):
        return row["role"]
    return None


# ---------- decisions ----------
def load_decisions():
    init_db()
    conn = get_conn()
    rows = conn.execute(
        "SELECT vendor, decision, decided_by, decided_at FROM decisions").fetchall()
    conn.close()
    return {r["vendor"]: dict(r) for r in rows}


def save_decisions(changes, username):
    """changes = {vendor: decision}. Only rows that actually changed are written."""
    existing = load_decisions()
    now = datetime.now().strftime("%d %b %Y %H:%M")
    conn = get_conn()
    for vendor, decision in changes.items():
        if existing.get(vendor, {}).get("decision", "Undecided") != decision:
            conn.execute(
                """INSERT INTO decisions (vendor, decision, decided_by, decided_at)
                   VALUES (?,?,?,?)
                   ON CONFLICT(vendor) DO UPDATE SET
                     decision = excluded.decision,
                     decided_by = excluded.decided_by,
                     decided_at = excluded.decided_at""",
                (vendor, decision, username, now),
            )
    conn.commit()
    conn.close()


# ---------- contracts ----------
def load_contracts():
    init_db()
    conn = get_conn()
    rows = conn.execute(
        "SELECT vendor, owner, contract_end, notice_days FROM contracts").fetchall()
    conn.close()
    return {r["vendor"]: dict(r) for r in rows}


def save_contracts(changes, username):
    """changes = {vendor: {"owner": str, "contract_end": 'YYYY-MM-DD' or None,
    "notice_days": int or None}}. Only rows that changed are written."""
    existing = load_contracts()
    now = datetime.now().strftime("%d %b %Y %H:%M")
    conn = get_conn()
    for vendor, c in changes.items():
        old = existing.get(vendor)
        old_vals = ((old["owner"] or "", old["contract_end"], old["notice_days"])
                    if old else ("", None, None))
        new_vals = (c["owner"], c["contract_end"], c["notice_days"])
        if old_vals != new_vals:
            conn.execute(
                """INSERT INTO contracts
                       (vendor, owner, contract_end, notice_days, updated_by, updated_at)
                   VALUES (?,?,?,?,?,?)
                   ON CONFLICT(vendor) DO UPDATE SET
                     owner = excluded.owner,
                     contract_end = excluded.contract_end,
                     notice_days = excluded.notice_days,
                     updated_by = excluded.updated_by,
                     updated_at = excluded.updated_at""",
                (vendor, c["owner"], c["contract_end"], c["notice_days"], username, now),
            )
    conn.commit()
    conn.close()