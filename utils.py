"""
utils.py
--------
Shared helper utilities:
- Currency/number formatting
- CSV / Excel export
- Low-stock alert helpers
- A lightweight rule-based "AI chat assistant" that answers natural-language
  questions about inventory using the analytics module (no external LLM
  call required, so it works fully offline -- this is what is meant by
  "AI Chat Assistant" in the project scope: it's a query-routing assistant
  over the same analytics functions that power the dashboard).
"""

import io
import re
import pandas as pd

import inventory
import analytics


# ---------------------------------------------------------------------------
# FORMATTING
# ---------------------------------------------------------------------------

def format_currency(value: float) -> str:
    """Formats a number as Indian-Rupee-style currency, e.g. ₹1,23,456.00"""
    try:
        return f"₹{value:,.2f}"
    except (TypeError, ValueError):
        return "₹0.00"


def format_number(value) -> str:
    try:
        return f"{int(value):,}"
    except (TypeError, ValueError):
        return "0"


# ---------------------------------------------------------------------------
# EXPORT
# ---------------------------------------------------------------------------

def dataframe_to_csv_bytes(df: pd.DataFrame) -> bytes:
    """Converts a DataFrame to CSV bytes, suitable for st.download_button."""
    return df.to_csv(index=False).encode("utf-8")


def dataframe_to_excel_bytes(df: pd.DataFrame, sheet_name: str = "Sheet1") -> bytes:
    """Converts a DataFrame to an in-memory .xlsx file's bytes."""
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name[:31])  # Excel sheet name limit
    return buffer.getvalue()


def multi_sheet_excel_bytes(sheets: dict) -> bytes:
    """
    Builds a single .xlsx with multiple sheets.
    `sheets` is a dict of {sheet_name: DataFrame}.
    """
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        for name, df in sheets.items():
            df.to_excel(writer, index=False, sheet_name=name[:31])
    return buffer.getvalue()


# ---------------------------------------------------------------------------
# ALERTS
# ---------------------------------------------------------------------------

def get_low_stock_alerts() -> list[str]:
    """Returns a list of human-readable low-stock alert strings."""
    low = inventory.get_low_stock_products()
    alerts = []
    for _, row in low.iterrows():
        alerts.append(
            f"⚠️ **{row['ProductName']}** ({row['Category']}) — only "
            f"{row['CurrentStock']} left (reorder level: {row['ReorderLevel']})"
        )
    return alerts


# ---------------------------------------------------------------------------
# AI CHAT ASSISTANT (rule-based intent routing over analytics functions)
# ---------------------------------------------------------------------------

def answer_chat_query(question: str) -> str:
    """
    Routes a natural-language question to the right analytics function and
    returns a formatted text answer. Pattern-matches on keywords -- this
    keeps the assistant fully deterministic and offline, while still
    covering every example question in the project spec.
    """
    q = question.lower().strip()

    # --- Low stock / reorder questions -----------------------------------
    if any(p in q for p in ["low stock", "low in stock", "running low", "reorder", "re-order", "restock"]):
        low = inventory.get_low_stock_products()
        if low.empty:
            return "✅ Good news — no products are currently low on stock."
        lines = [f"- **{r['ProductName']}**: {r['CurrentStock']} left (reorder level {r['ReorderLevel']})"
                  for _, r in low.iterrows()]
        return f"📦 **{len(low)} product(s) need reordering:**\n\n" + "\n".join(lines)

    # --- Top selling products ---------------------------------------------
    if any(p in q for p in ["top selling", "top-selling", "best selling", "best-selling",
                             "fastest selling", "fastest-selling", "most sold", "popular"]):
        n_match = re.search(r"top\s*(\d+)", q)
        n = int(n_match.group(1)) if n_match else 5
        top = analytics.get_top_selling_products(n=n)
        if top.empty:
            return "No sales recorded yet, so there's no top-seller data."
        lines = [f"{i+1}. **{r['ProductName']}** — {int(r['QuantitySold'])} units sold "
                 f"({format_currency(r['Revenue'])})"
                 for i, (_, r) in enumerate(top.iterrows())]
        return f"🏆 **Top {len(top)} selling products:**\n\n" + "\n".join(lines)

    # --- Inventory value ----------------------------------------------------
    if any(p in q for p in ["inventory value", "stock value", "worth", "total value"]):
        value = inventory.get_inventory_value()
        return f"💰 Current total inventory value is **{format_currency(value)}**."

    # --- Revenue ------------------------------------------------------------
    if "revenue" in q and "categor" not in q:
        sales = analytics.get_all_sales_raw() if hasattr(analytics, "get_all_sales_raw") else None
        kpis = analytics.get_kpi_summary()
        return (f"📈 Total revenue to date is **{format_currency(kpis['total_revenue'])}**, "
                f"with **{format_currency(kpis['revenue_last_30_days'])}** earned in the last 30 days.")

    # --- Category revenue ----------------------------------------------------
    if "categor" in q and ("revenue" in q or "sales" in q or "highest" in q):
        cat = analytics.get_category_revenue()
        if cat.empty:
            return "No sales recorded yet, so there's no category breakdown available."
        top_cat = cat.iloc[0]
        lines = [f"- **{r['Category']}**: {format_currency(r['Revenue'])}" for _, r in cat.head(5).iterrows()]
        return (f"🏷️ **{top_cat['Category']}** generates the most revenue "
                f"({format_currency(top_cat['Revenue'])}). Top categories:\n\n" + "\n".join(lines))

    # --- Stale / not sold recently --------------------------------------------
    if any(p in q for p in ["not sold", "haven't sold", "stale", "dead stock", "no sales"]):
        stale = analytics.get_stale_products(days=30)
        if stale.empty:
            return "✅ Every active product has sold at least once in the last 30 days."
        names = ", ".join(stale["ProductName"].head(10).tolist())
        return f"🧊 **{len(stale)} product(s)** haven't sold in 30+ days, including: {names}."

    # --- Supplier with most products --------------------------------------------
    if "supplier" in q:
        sup = analytics.get_supplier_product_counts()
        if sup.empty or sup["ProductCount"].max() == 0:
            return "No supplier-product links found yet."
        top_sup = sup.iloc[0]
        return (f"🚚 **{top_sup['SupplierName']}** supplies the most products "
                f"({int(top_sup['ProductCount'])} products).")

    # --- Stockout prediction ----------------------------------------------------
    if any(p in q for p in ["run out", "stockout", "stock out", "next week"]):
        risky = analytics.predict_stockouts_next_week()
        if risky.empty:
            return "✅ No products are predicted to run out within the next 7 days."
        lines = [f"- **{r['ProductName']}**: projected stock {r['ProjectedStockAfter']} "
                 f"(current {r['CurrentStock']})" for _, r in risky.head(10).iterrows()]
        return f"⏳ **{len(risky)} product(s)** are predicted to run out within 7 days:\n\n" + "\n".join(lines)

    # --- Total products -------------------------------------------------------
    if "how many product" in q or "total product" in q:
        kpis = analytics.get_kpi_summary()
        return f"📦 There are currently **{kpis['total_products']}** active products in inventory."

    # --- Fallback ------------------------------------------------------------
    return (
        "I'm not sure how to answer that yet. Try asking things like:\n\n"
        "- *Which products are low in stock?*\n"
        "- *What are the top-selling products?*\n"
        "- *How much inventory value do we currently have?*\n"
        "- *Which products should be reordered?*\n"
        "- *Which products haven't sold in 30 days?*\n"
        "- *Which products are likely to run out next week?*"
    )
