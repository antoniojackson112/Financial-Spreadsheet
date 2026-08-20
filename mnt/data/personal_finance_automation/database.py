from pathlib import Path
import sqlite3

DB_PATH = Path(__file__).resolve().parent / "data" / "finance.db"


def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with connect() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS plaid_items (
            item_id TEXT PRIMARY KEY,
            institution_name TEXT,
            cursor TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS accounts (
            account_id TEXT PRIMARY KEY,
            item_id TEXT NOT NULL,
            institution TEXT,
            account_name TEXT,
            account_type TEXT,
            currency TEXT DEFAULT 'USD',
            current_balance REAL,
            external_account_id TEXT UNIQUE NOT NULL,
            last_sync TEXT,
            FOREIGN KEY(item_id) REFERENCES plaid_items(item_id)
        );

        CREATE TABLE IF NOT EXISTS transactions (
            transaction_id TEXT PRIMARY KEY,
            account_id TEXT NOT NULL,
            date TEXT NOT NULL,
            merchant TEXT,
            description TEXT,
            amount REAL NOT NULL,
            currency TEXT DEFAULT 'USD',
            transaction_type TEXT,
            category TEXT,
            subcategory TEXT,
            recurring INTEGER DEFAULT 0,
            pending INTEGER DEFAULT 0,
            source TEXT,
            fingerprint TEXT UNIQUE,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS category_rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            priority INTEGER NOT NULL,
            active INTEGER NOT NULL DEFAULT 1,
            pattern TEXT NOT NULL,
            category TEXT NOT NULL,
            subcategory TEXT NOT NULL,
            transaction_type TEXT,
            recurring INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS sync_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            started_at TEXT NOT NULL,
            completed_at TEXT,
            transactions_added INTEGER DEFAULT 0,
            transactions_modified INTEGER DEFAULT 0,
            transactions_removed INTEGER DEFAULT 0,
            status TEXT NOT NULL,
            error TEXT
        );
        """)


def upsert_rule(priority, active, pattern, category, subcategory, transaction_type, recurring):
    with connect() as con:
        con.execute("""
        INSERT INTO category_rules(priority, active, pattern, category, subcategory, transaction_type, recurring)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (priority, active, pattern, category, subcategory, transaction_type, recurring))


def get_rules():
    with connect() as con:
        return con.execute("""
            SELECT * FROM category_rules
            WHERE active = 1
            ORDER BY priority ASC, id ASC
        """).fetchall()
