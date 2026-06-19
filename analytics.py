"""
analytics.py
------------
All analytical queries that power the dashboard and answer the project's
core business questions:

  1. Which products sell the fastest?
  2. Which products need reordering?
  3. Which categories generate the highest revenue?
  4. Which products have not sold in the last 30 days?
  5. What is the current inventory value?
  6. Which supplier provides the most products?

Also includes the AI/ML features:
  - Demand forecasting (linear regression on recent daily sales)
  - Automatic reorder recommendations (forecast-aware)
  - "Likely to run out within N days" prediction
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from database import get_connection
from sales import get_all_sales_raw
from inventory import get_all_products, get_inventory_value, get_low_stock_products


# ---------------------------------------------------------------------------
# CORE KPI NUMBERS
# ---------------------------------------------------------------------------

def get_kpi_summary() -> dict:
    """Returns the headline numbers shown as KPI cards on the dashboard."""
    products = get_all_products()
    sales = get_all_sales_raw()

    total_products = len(products)
    inventory_value = get_inventory_value()
    total_revenue = float(sales["Revenue"].sum()) if not sales.empty else 0.0
    total_units_sold = int(sales["QuantitySold"].sum()) if not sales.empty else 0
    low_stock_count = len(get_low_stock_products())

    # Revenue in the last 30 days, for a "trend" feel on the KPI card.
    if not sales.empty:
        cutoff = datetime.now() - timedelta(days=30)
        recent_revenue = float(sales[sales["SaleDate"] >= cutoff]["Revenue"].sum())
    else:
        recent_revenue = 0.0

    return {
        "total_products": total_products,
        "inventory_value": inventory_value,
        "total_revenue": total_revenue,
        "total_units_sold": total_units_sold,
        "low_stock_count": low_stock_count,
        "revenue_last_30_days": recent_revenue,
    }


# ---------------------------------------------------------------------------
# BUSINESS QUESTION 1: Which products sell the fastest?
# ---------------------------------------------------------------------------

def get_top_selling_products(n: int = 10, by: str = "quantity") -> pd.DataFrame:
    """
    Ranks products by total quantity sold (by='quantity') or total revenue
    (by='revenue'). This is the "fastest selling" / "top selling" view.
    """
    sales = get_all_sales_raw()
    if sales.empty:
        return pd.DataFrame(columns=["ProductName", "Category", "QuantitySold", "Revenue"])

    grouped = sales.groupby(["ProductName", "Category"], as_index=False).agg(
        QuantitySold=("QuantitySold", "sum"),
        Revenue=("Revenue", "sum"),
    )
    sort_col = "QuantitySold" if by == "quantity" else "Revenue"
    return grouped.sort_values(sort_col, ascending=False).head(n).reset_index(drop=True)


def get_sales_velocity() -> pd.DataFrame:
    """
    Computes average units sold per day for each product (last 30 days),
    a more rigorous answer to "which products sell fastest" than raw totals,
    since it normalizes for how long the product has been selling.
    """
    sales = get_all_sales_raw()
    if sales.empty:
        return pd.DataFrame(columns=["ProductName", "Category", "AvgUnitsPerDay"])

    cutoff = datetime.now() - timedelta(days=30)
    recent = sales[sales["SaleDate"] >= cutoff]
    if recent.empty:
        return pd.DataFrame(columns=["ProductName", "Category", "AvgUnitsPerDay"])

    grouped = recent.groupby(["ProductName", "Category"], as_index=False).agg(
        TotalUnits=("QuantitySold", "sum")
    )
    grouped["AvgUnitsPerDay"] = (grouped["TotalUnits"] / 30).round(2)
    return grouped.sort_values("AvgUnitsPerDay", ascending=False).reset_index(drop=True)


# ---------------------------------------------------------------------------
# BUSINESS QUESTION 2: Which products need reordering?
# (delegated to inventory.get_low_stock_products, re-exported here for
#  discoverability since it's a core "analytics" answer too)
# ---------------------------------------------------------------------------

def get_reorder_list() -> pd.DataFrame:
    return get_low_stock_products()


# ---------------------------------------------------------------------------
# BUSINESS QUESTION 3: Which categories generate the highest revenue?
# ---------------------------------------------------------------------------

def get_category_revenue() -> pd.DataFrame:
    sales = get_all_sales_raw()
    if sales.empty:
        return pd.DataFrame(columns=["Category", "Revenue", "QuantitySold"])

    grouped = sales.groupby("Category", as_index=False).agg(
        Revenue=("Revenue", "sum"),
        QuantitySold=("QuantitySold", "sum"),
    )
    return grouped.sort_values("Revenue", ascending=False).reset_index(drop=True)


# ---------------------------------------------------------------------------
# BUSINESS QUESTION 4: Which products have not sold in the last 30 days?
# ---------------------------------------------------------------------------

def get_stale_products(days: int = 30) -> pd.DataFrame:
    """
    Products with zero sales in the last `days` days (active products only).
    Useful for spotting dead stock that's tying up capital.
    """
    products = get_all_products()
    sales = get_all_sales_raw()

    cutoff = datetime.now() - timedelta(days=days)
    if not sales.empty:
        recently_sold_ids = set(sales[sales["SaleDate"] >= cutoff]["ProductID"].unique())
    else:
        recently_sold_ids = set()

    stale = products[~products["ProductID"].isin(recently_sold_ids)].copy()
    return stale[["ProductID", "ProductName", "Category", "CurrentStock", "Price"]].reset_index(drop=True)


# ---------------------------------------------------------------------------
# BUSINESS QUESTION 5: What is the current inventory value?
# (delegated to inventory.get_inventory_value)
# ---------------------------------------------------------------------------

def get_inventory_value_by_category() -> pd.DataFrame:
    """Breaks total inventory value down by category, for the pie chart."""
    products = get_all_products()
    if products.empty:
        return pd.DataFrame(columns=["Category", "InventoryValue"])
    products["InventoryValue"] = products["Price"] * products["CurrentStock"]
    grouped = products.groupby("Category", as_index=False)["InventoryValue"].sum()
    return grouped.sort_values("InventoryValue", ascending=False).reset_index(drop=True)


# ---------------------------------------------------------------------------
# BUSINESS QUESTION 6: Which supplier provides the most products?
# ---------------------------------------------------------------------------

def get_supplier_product_counts() -> pd.DataFrame:
    query = """
        SELECT s.SupplierName, COUNT(p.ProductID) AS ProductCount
        FROM Suppliers s
        LEFT JOIN Products p ON s.SupplierID = p.SupplierID AND p.IsActive = 1
        GROUP BY s.SupplierID, s.SupplierName
        ORDER BY ProductCount DESC
    """
    with get_connection() as conn:
        return pd.read_sql_query(query, conn)


# ---------------------------------------------------------------------------
# MONTHLY SALES TREND (for line chart)
# ---------------------------------------------------------------------------

def get_monthly_sales_trend() -> pd.DataFrame:
    sales = get_all_sales_raw()
    if sales.empty:
        return pd.DataFrame(columns=["Month", "Revenue", "QuantitySold"])

    sales["Month"] = sales["SaleDate"].dt.strftime("%Y-%m")
    grouped = sales.groupby("Month", as_index=False).agg(
        Revenue=("Revenue", "sum"),
        QuantitySold=("QuantitySold", "sum"),
    )
    return grouped.sort_values("Month").reset_index(drop=True)


def get_daily_sales_trend(days: int = 60) -> pd.DataFrame:
    """Daily revenue/units for the last `days` days -- finer-grained trend line."""
    sales = get_all_sales_raw()
    if sales.empty:
        return pd.DataFrame(columns=["Date", "Revenue", "QuantitySold"])

    cutoff = datetime.now() - timedelta(days=days)
    recent = sales[sales["SaleDate"] >= cutoff].copy()
    recent["Date"] = recent["SaleDate"].dt.strftime("%Y-%m-%d")
    grouped = recent.groupby("Date", as_index=False).agg(
        Revenue=("Revenue", "sum"),
        QuantitySold=("QuantitySold", "sum"),
    )
    return grouped.sort_values("Date").reset_index(drop=True)


# ---------------------------------------------------------------------------
# AI FEATURE: DEMAND FORECASTING (scikit-learn linear regression)
# ---------------------------------------------------------------------------

def forecast_demand(product_id: int, days_ahead: int = 7) -> dict:
    """
    Fits a simple linear regression on a product's daily sales history
    (day index -> quantity sold) and projects demand for the next
    `days_ahead` days.

    This intentionally uses a simple, explainable model (linear trend)
    rather than a complex one, since with sparse per-product daily sales
    data a simple trend is more robust than an overfit model, and the goal
    here is a directional signal for reorder planning, not a precise
    forecast.

    Returns a dict with the forecasted total units, average daily rate,
    and a confidence label based on how much history is available.
    """
    from sklearn.linear_model import LinearRegression

    sales = get_all_sales_raw()
    product_sales = sales[sales["ProductID"] == product_id].copy()

    if product_sales.empty:
        return {
            "forecast_units": 0,
            "avg_daily_rate": 0.0,
            "confidence": "no_data",
            "history_days": 0,
        }

    # Aggregate to one row per calendar day (sum quantity), filling gaps
    # with 0 so the regression sees true day-to-day variation.
    daily = product_sales.groupby(product_sales["SaleDate"].dt.date)["QuantitySold"].sum()
    full_range = pd.date_range(daily.index.min(), daily.index.max(), freq="D")
    daily = daily.reindex(full_range.date, fill_value=0)

    history_days = len(daily)
    if history_days < 5:
        # Too little history for a trend line -- fall back to a flat average.
        avg_rate = float(daily.mean())
        return {
            "forecast_units": round(avg_rate * days_ahead, 1),
            "avg_daily_rate": round(avg_rate, 2),
            "confidence": "low",
            "history_days": history_days,
        }

    X = np.arange(history_days).reshape(-1, 1)
    y = daily.values

    model = LinearRegression()
    model.fit(X, y)

    future_X = np.arange(history_days, history_days + days_ahead).reshape(-1, 1)
    predicted = model.predict(future_X)
    predicted = np.clip(predicted, 0, None)  # demand can't be negative

    confidence = "high" if history_days >= 30 else "medium"

    return {
        "forecast_units": round(float(predicted.sum()), 1),
        "avg_daily_rate": round(float(predicted.mean()), 2),
        "confidence": confidence,
        "history_days": history_days,
    }


def get_reorder_recommendations(days_ahead: int = 7) -> pd.DataFrame:
    """
    AI-powered reorder recommendation: combines current stock with the
    forecasted demand for the next `days_ahead` days to recommend how much
    to reorder, and flags products predicted to run out before restocking
    would typically arrive.
    """
    products = get_all_products()
    if products.empty:
        return pd.DataFrame()

    rows = []
    for _, p in products.iterrows():
        forecast = forecast_demand(p["ProductID"], days_ahead=days_ahead)
        projected_stock = p["CurrentStock"] - forecast["forecast_units"]
        will_run_out = projected_stock <= 0
        recommended_qty = max(0, round(forecast["forecast_units"] - p["CurrentStock"] + p["ReorderLevel"]))

        rows.append({
            "ProductID": p["ProductID"],
            "ProductName": p["ProductName"],
            "Category": p["Category"],
            "CurrentStock": p["CurrentStock"],
            "ReorderLevel": p["ReorderLevel"],
            "ForecastDemand_NextNDays": forecast["forecast_units"],
            "ProjectedStockAfter": round(projected_stock, 1),
            "WillRunOut": will_run_out,
            "RecommendedReorderQty": recommended_qty,
            "Confidence": forecast["confidence"],
        })

    df = pd.DataFrame(rows)
    # Show the most urgent (about to run out) first.
    df = df.sort_values(["WillRunOut", "ProjectedStockAfter"], ascending=[False, True])
    return df.reset_index(drop=True)


def predict_stockouts_next_week() -> pd.DataFrame:
    """Convenience wrapper: products predicted to run out within 7 days."""
    recs = get_reorder_recommendations(days_ahead=7)
    if recs.empty:
        return recs
    return recs[recs["WillRunOut"]].reset_index(drop=True)
