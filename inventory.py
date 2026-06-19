"""
inventory.py
------------
Business logic for Inventory Management: adding, updating, deleting and
searching products, plus stock-level helpers (low stock, restock).

All functions return plain Python data structures (dicts/lists) or pandas
DataFrames so the UI layer (app.py) never has to know about SQL.
"""

import pandas as pd
from database import get_connection


# ---------------------------------------------------------------------------
# CREATE
# ---------------------------------------------------------------------------

def add_product(product_name: str, category: str, price: float,
                 current_stock: int, reorder_level: int, supplier_id: int | None):
    """Inserts a new product. Returns the new ProductID."""
    if not product_name or not product_name.strip():
        raise ValueError("Product name cannot be empty.")
    if price < 0:
        raise ValueError("Price cannot be negative.")
    if current_stock < 0:
        raise ValueError("Stock cannot be negative.")

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO Products
               (ProductName, Category, Price, CurrentStock, ReorderLevel, SupplierID)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (product_name.strip(), category.strip(), price, current_stock,
             reorder_level, supplier_id),
        )
        return cur.lastrowid


def add_supplier(supplier_name: str, contact_number: str, email: str):
    """Inserts a new supplier. Returns the new SupplierID."""
    if not supplier_name or not supplier_name.strip():
        raise ValueError("Supplier name cannot be empty.")

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO Suppliers (SupplierName, ContactNumber, Email) VALUES (?, ?, ?)",
            (supplier_name.strip(), contact_number, email),
        )
        return cur.lastrowid


# ---------------------------------------------------------------------------
# READ
# ---------------------------------------------------------------------------

def get_all_products(include_inactive: bool = False) -> pd.DataFrame:
    """Returns all products joined with supplier name, as a DataFrame."""
    query = """
        SELECT p.ProductID, p.ProductName, p.Category, p.Price,
               p.CurrentStock, p.ReorderLevel, p.SupplierID,
               s.SupplierName, p.IsActive
        FROM Products p
        LEFT JOIN Suppliers s ON p.SupplierID = s.SupplierID
    """
    if not include_inactive:
        query += " WHERE p.IsActive = 1"
    query += " ORDER BY p.ProductName"

    with get_connection() as conn:
        return pd.read_sql_query(query, conn)


def get_product_by_id(product_id: int):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM Products WHERE ProductID = ?", (product_id,))
        row = cur.fetchone()
        return dict(row) if row else None


def get_all_suppliers() -> pd.DataFrame:
    with get_connection() as conn:
        return pd.read_sql_query("SELECT * FROM Suppliers ORDER BY SupplierName", conn)


def search_products(keyword: str = "", category: str = "All") -> pd.DataFrame:
    """Searches products by name (case-insensitive substring) and/or category."""
    df = get_all_products()
    if keyword:
        df = df[df["ProductName"].str.contains(keyword, case=False, na=False)]
    if category and category != "All":
        df = df[df["Category"] == category]
    return df.reset_index(drop=True)


def get_categories() -> list:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT Category FROM Products ORDER BY Category")
        return [row["Category"] for row in cur.fetchall()]


def get_low_stock_products() -> pd.DataFrame:
    """Products where CurrentStock <= ReorderLevel -- candidates for reordering."""
    query = """
        SELECT p.ProductID, p.ProductName, p.Category, p.CurrentStock,
               p.ReorderLevel, s.SupplierName, s.ContactNumber
        FROM Products p
        LEFT JOIN Suppliers s ON p.SupplierID = s.SupplierID
        WHERE p.CurrentStock <= p.ReorderLevel AND p.IsActive = 1
        ORDER BY (p.CurrentStock * 1.0 / NULLIF(p.ReorderLevel, 0)) ASC
    """
    with get_connection() as conn:
        return pd.read_sql_query(query, conn)


def get_inventory_value() -> float:
    """Total value of current inventory = sum(Price * CurrentStock)."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT SUM(Price * CurrentStock) AS total FROM Products WHERE IsActive = 1")
        result = cur.fetchone()["total"]
        return float(result) if result is not None else 0.0


# ---------------------------------------------------------------------------
# UPDATE
# ---------------------------------------------------------------------------

def update_product(product_id: int, **fields):
    """
    Updates arbitrary fields on a product, e.g.:
        update_product(5, Price=199.0, ReorderLevel=20)
    Only allows known, safe columns to be updated.
    """
    allowed = {"ProductName", "Category", "Price", "CurrentStock",
               "ReorderLevel", "SupplierID", "IsActive"}
    fields = {k: v for k, v in fields.items() if k in allowed}
    if not fields:
        return

    set_clause = ", ".join(f"{col} = ?" for col in fields)
    values = list(fields.values()) + [product_id]

    with get_connection() as conn:
        conn.execute(f"UPDATE Products SET {set_clause} WHERE ProductID = ?", values)


def adjust_stock(product_id: int, delta: int):
    """
    Increases or decreases stock by `delta` (can be negative).
    Raises ValueError if the result would go below zero.
    """
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT CurrentStock FROM Products WHERE ProductID = ?", (product_id,))
        row = cur.fetchone()
        if row is None:
            raise ValueError(f"Product ID {product_id} not found.")
        new_stock = row["CurrentStock"] + delta
        if new_stock < 0:
            raise ValueError("Stock cannot go below zero.")
        cur.execute("UPDATE Products SET CurrentStock = ? WHERE ProductID = ?",
                    (new_stock, product_id))
        return new_stock


# ---------------------------------------------------------------------------
# DELETE
# ---------------------------------------------------------------------------

def delete_product(product_id: int, hard_delete: bool = False):
    """
    By default performs a SOFT delete (IsActive = 0) so historical sales
    records remain valid and reportable. Pass hard_delete=True to actually
    remove the row (will cascade-delete its sales history).
    """
    with get_connection() as conn:
        if hard_delete:
            conn.execute("DELETE FROM Products WHERE ProductID = ?", (product_id,))
        else:
            conn.execute("UPDATE Products SET IsActive = 0 WHERE ProductID = ?", (product_id,))
