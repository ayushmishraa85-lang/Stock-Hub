"""
database.py
------------
Handles all low-level database concerns for the Inventory Management System:
- Connection management (SQLite)
- Schema creation (Products, Sales, Suppliers, Users)
- Generic helper functions used by other modules

Design notes:
- SQLite is used for portability (zero-config, file-based). The schema is plain
  SQL, so swapping to MySQL later only requires changing `get_connection()`
  and minor syntax (e.g. AUTOINCREMENT -> AUTO_INCREMENT).
- All functions open/close their own connection (safe for Streamlit's
  rerun-heavy execution model, which doesn't play well with long-lived
  global connections shared across reruns/threads).
"""

import sqlite3
import os
import hashlib
from contextlib import contextmanager

# Single source of truth for the DB file location.
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "inventory.db")


@contextmanager
def get_connection():
    """
    Context manager that yields a SQLite connection with sane defaults:
    - row_factory = sqlite3.Row so results behave like dicts (col access by name)
    - foreign_keys = ON so referential integrity is enforced
    Always closes the connection on exit, even if an exception occurs.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """
    Creates all tables if they don't already exist. Safe to call on every
    app startup (idempotent via IF NOT EXISTS).
    """
    with get_connection() as conn:
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS Suppliers (
                SupplierID INTEGER PRIMARY KEY AUTOINCREMENT,
                SupplierName TEXT NOT NULL,
                ContactNumber TEXT,
                Email TEXT
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS Products (
                ProductID INTEGER PRIMARY KEY AUTOINCREMENT,
                ProductName TEXT NOT NULL,
                Category TEXT NOT NULL,
                Price REAL NOT NULL CHECK (Price >= 0),
                CurrentStock INTEGER NOT NULL DEFAULT 0 CHECK (CurrentStock >= 0),
                ReorderLevel INTEGER NOT NULL DEFAULT 10,
                SupplierID INTEGER,
                IsActive INTEGER NOT NULL DEFAULT 1,
                FOREIGN KEY (SupplierID) REFERENCES Suppliers(SupplierID)
                    ON DELETE SET NULL
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS Sales (
                SaleID INTEGER PRIMARY KEY AUTOINCREMENT,
                ProductID INTEGER NOT NULL,
                QuantitySold INTEGER NOT NULL CHECK (QuantitySold > 0),
                SaleDate TEXT NOT NULL,
                UnitPriceAtSale REAL NOT NULL,
                FOREIGN KEY (ProductID) REFERENCES Products(ProductID)
                    ON DELETE CASCADE
            )
        """)

        # Simple user table for the login system (passwords stored as SHA-256
        # hashes -- adequate for a demo app, NOT a production-grade auth system).
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Users (
                UserID INTEGER PRIMARY KEY AUTOINCREMENT,
                Username TEXT NOT NULL UNIQUE,
                PasswordHash TEXT NOT NULL,
                Role TEXT NOT NULL DEFAULT 'staff'
            )
        """)

        # Helpful indexes for the query patterns used by analytics.py
        cur.execute("CREATE INDEX IF NOT EXISTS idx_sales_date ON Sales(SaleDate)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_sales_product ON Sales(ProductID)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_products_category ON Products(Category)")

        # Seed a default admin user if no users exist yet.
        cur.execute("SELECT COUNT(*) AS c FROM Users")
        if cur.fetchone()["c"] == 0:
            cur.execute(
                "INSERT INTO Users (Username, PasswordHash, Role) VALUES (?, ?, ?)",
                ("admin", hash_password("admin123"), "admin"),
            )


def hash_password(password: str) -> str:
    """Hashes a password with SHA-256. Adequate for demo auth, not for
    production (which should use bcrypt/argon2 with per-user salts)."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_user(username: str, password: str):
    """Returns the user row if credentials are valid, else None."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM Users WHERE Username = ?", (username,))
        row = cur.fetchone()
        if row and row["PasswordHash"] == hash_password(password):
            return dict(row)
        return None


def create_user(username: str, password: str, role: str = "staff"):
    """Creates a new user. Raises sqlite3.IntegrityError if username taken."""
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO Users (Username, PasswordHash, Role) VALUES (?, ?, ?)",
            (username, hash_password(password), role),
        )


def reset_database():
    """Drops and recreates all tables. Used by the 'reset sample data' admin action."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("DROP TABLE IF EXISTS Sales")
        cur.execute("DROP TABLE IF EXISTS Products")
        cur.execute("DROP TABLE IF EXISTS Suppliers")
        cur.execute("DROP TABLE IF EXISTS Users")
    init_db()
