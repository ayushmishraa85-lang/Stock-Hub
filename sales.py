"""
sales.py
--------
Handles sales transactions: recording a sale, automatically decrementing
stock, and retrieving sales history.
"""

import pandas as pd
from datetime import datetime
from database import get_connection
from inventory import get_product_by_id, adjust_stock


def record_sale(product_id: int, quantity_sold: int, sale_date: str | None = None):
    """
    Records a sale and atomically reduces stock for that product.

    - Validates that enough stock exists before committing.
    - Stores the unit price AT THE TIME OF SALE (UnitPriceAtSale) so that
      historical revenue figures remain accurate even if the product's
      price changes later.

    Returns the new SaleID.
    Raises ValueError on invalid input (bad product, insufficient stock, etc).
    """
    if quantity_sold <= 0:
        raise ValueError("Quantity sold must be greater than zero.")

    product = get_product_by_id(product_id)
    if product is None:
        raise ValueError(f"Product ID {product_id} does not exist.")
    if product["IsActive"] == 0:
        raise ValueError(f"'{product['ProductName']}' is inactive/discontinued.")
    if product["CurrentStock"] < quantity_sold:
        raise ValueError(
            f"Insufficient stock for '{product['ProductName']}'. "
            f"Available: {product['CurrentStock']}, Requested: {quantity_sold}."
        )

    sale_date = sale_date or datetime.now().strftime("%Y-%m-%d")

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO Sales (ProductID, QuantitySold, SaleDate, UnitPriceAtSale)
               VALUES (?, ?, ?, ?)""",
            (product_id, quantity_sold, sale_date, product["Price"]),
        )
        sale_id = cur.lastrowid

    # Reduce stock AFTER the sale row is committed (separate connection scope
    # is fine here since adjust_stock manages its own transaction).
    adjust_stock(product_id, -quantity_sold)
    return sale_id


def bulk_record_sales(sales_list: list[dict]):
    """
    Records multiple sales at once, e.g. for sample data generation.
    Each dict needs: ProductID, QuantitySold, SaleDate, UnitPriceAtSale.
    Bypasses per-sale validation for speed (used only for seeding).
    """
    with get_connection() as conn:
        conn.executemany(
            """INSERT INTO Sales (ProductID, QuantitySold, SaleDate, UnitPriceAtSale)
               VALUES (?, ?, ?, ?)""",
            [(s["ProductID"], s["QuantitySold"], s["SaleDate"], s["UnitPriceAtSale"])
             for s in sales_list],
        )


def get_sales_history(limit: int = 500) -> pd.DataFrame:
    """Returns the most recent sales transactions, newest first."""
    query = """
        SELECT sa.SaleID, p.ProductName, p.Category, sa.QuantitySold,
               sa.UnitPriceAtSale, (sa.QuantitySold * sa.UnitPriceAtSale) AS LineTotal,
               sa.SaleDate
        FROM Sales sa
        JOIN Products p ON sa.ProductID = p.ProductID
        ORDER BY sa.SaleDate DESC, sa.SaleID DESC
        LIMIT ?
    """
    with get_connection() as conn:
        return pd.read_sql_query(query, conn, params=(limit,))


def get_all_sales_raw() -> pd.DataFrame:
    """Returns the full sales table joined with product info, for analytics use."""
    query = """
        SELECT sa.SaleID, sa.ProductID, p.ProductName, p.Category,
               sa.QuantitySold, sa.UnitPriceAtSale,
               (sa.QuantitySold * sa.UnitPriceAtSale) AS Revenue,
               sa.SaleDate
        FROM Sales sa
        JOIN Products p ON sa.ProductID = p.ProductID
    """
    with get_connection() as conn:
        df = pd.read_sql_query(query, conn)
    if not df.empty:
        df["SaleDate"] = pd.to_datetime(df["SaleDate"])
    return df


def delete_sale(sale_id: int, restock: bool = True):
    """
    Deletes a sale record. If restock=True, adds the quantity back to
    CurrentStock (treats the deletion as 'this sale never happened').
    """
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT ProductID, QuantitySold FROM Sales WHERE SaleID = ?", (sale_id,))
        row = cur.fetchone()
        if row is None:
            raise ValueError(f"Sale ID {sale_id} not found.")
        product_id, qty = row["ProductID"], row["QuantitySold"]
        cur.execute("DELETE FROM Sales WHERE SaleID = ?", (sale_id,))

    if restock:
        adjust_stock(product_id, qty)
