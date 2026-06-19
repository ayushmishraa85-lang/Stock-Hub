# StockHub — Inventory Management System

A full-stack Inventory Management System built with Python, SQLite, Streamlit, and Plotly — inspired by the dashboards used at quick-commerce companies like Zepto. Tracks products, sales, stock levels, and suppliers, and layers on AI-powered demand forecasting, reorder recommendations, and a natural-language chat assistant.

## Features

- **Inventory Management** — add, update, soft-delete, search, and filter products by category
- **Sales Management** — record sales with automatic stock deduction, view/export/undo sales history
- **Analytics Dashboard** — KPI cards, revenue trends, category breakdowns, top sellers, low-stock alerts
- **6 Business Questions** answered with dedicated views (fastest sellers, reorder candidates, category revenue, stale stock, inventory value, top suppliers)
- **AI Features** — demand forecasting (scikit-learn linear regression), automatic reorder recommendations, 7-day stockout prediction
- **AI Chat Assistant** — ask plain-English questions about your inventory ("Which products are low in stock?")
- **Login system**, **CSV/Excel export**, **dark mode**, **mobile-responsive** Streamlit UI

## Project Structure

```
inventory_system/
├── app.py              # Streamlit UI — login, theming, navigation, all pages
├── database.py         # SQLite connection, schema, auth helpers
├── inventory.py        # Product CRUD, stock adjustments, low-stock logic
├── sales.py            # Sale recording, stock auto-deduction, sales history
├── analytics.py        # All 6 business questions + AI forecasting/reorder logic
├── utils.py             # Formatting, CSV/Excel export, chat assistant
├── seed_data.py         # Generates realistic sample data (suppliers, products, 90 days of sales)
├── sql_queries.sql      # Reference SQL for every analytics query (for learning/porting to MySQL)
├── requirements.txt
├── sample_data/
│   ├── products_sample.csv
│   ├── suppliers_sample.csv
│   └── sales_sample.csv
└── README.md
```

## Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Generate the database + sample data (39 products, 8 suppliers, ~90 days of sales)
python seed_data.py

# 3. Launch the app
streamlit run app.py
```

Open the URL Streamlit prints (typically `http://localhost:8501`).

**Login:** `admin` / `admin123`

> You can also click **"Reset Sample Data"** in the sidebar's Admin Tools at any time to wipe and regenerate fresh sample data without leaving the app.

## Database Schema

| Table | Key Columns |
|---|---|
| **Products** | ProductID, ProductName, Category, Price, CurrentStock, ReorderLevel, SupplierID, IsActive |
| **Sales** | SaleID, ProductID, QuantitySold, SaleDate, UnitPriceAtSale |
| **Suppliers** | SupplierID, SupplierName, ContactNumber, Email |
| **Users** | UserID, Username, PasswordHash, Role |

Notes on design choices:
- **`UnitPriceAtSale`** is stored on each sale (a price snapshot) so historical revenue stays accurate even if a product's current price changes later.
- **`IsActive`** implements a soft delete on Products — removing a product hides it from active views but keeps its sales history intact and reportable.
- Stock decrements happen inside `sales.record_sale()`, which validates available stock first and raises a clear error rather than allowing negative stock.

## The AI Features, Explained

- **Demand forecasting** (`analytics.forecast_demand`) fits a `scikit-learn LinearRegression` model on a product's daily sales history (day index → quantity sold) and projects forward. A simple linear trend is used deliberately — with sparse per-product daily data, a complex model would overfit; the goal is a directional signal for reorder planning, not a precise forecast. Confidence is labeled `low` / `medium` / `high` based on how many days of history are available.
- **Reorder recommendations** (`analytics.get_reorder_recommendations`) combine current stock with forecasted demand over the next N days to flag products at risk of running out and suggest a reorder quantity.
- **Stockout prediction** (`analytics.predict_stockouts_next_week`) is a convenience filter on the above, showing only products projected to hit zero within 7 days.
- **Chat assistant** (`utils.answer_chat_query`) is a deterministic, fully offline rule-based router: it pattern-matches the question's intent (low stock, top sellers, inventory value, reorder, stale products, supplier ranking, stockout risk) and calls the same analytics functions that power the dashboard. This keeps answers consistent with the rest of the app and requires no external API or internet connection.

## Extending This Project

- **Switch to MySQL/PostgreSQL**: `sql_queries.sql` includes inline notes on syntax differences (e.g. `AUTOINCREMENT` → `AUTO_INCREMENT`, `date('now', '-30 days')` → `DATE_SUB(CURDATE(), INTERVAL 30 DAY)`). Swap `database.get_connection()` to use a different driver (e.g. `mysql-connector-python` or `psycopg2`) and most of the codebase is unaffected since all SQL is parameterized and isolated to `database.py`, `inventory.py`, `sales.py`, and `analytics.py`.
- **Stronger auth**: the current login uses SHA-256 password hashing with no salt — adequate for a demo, not for production. Swap in `bcrypt` or `argon2` in `database.hash_password`/`verify_user` for real deployments.
- **Real LLM-backed chat**: `utils.answer_chat_query` can be replaced with a call to the Anthropic API (or any LLM) that's given the analytics functions as tools, for free-form question answering beyond the current pattern-matched intents.

## Tech Stack

Python · Pandas · SQLite · Streamlit · Plotly · scikit-learn · openpyxl
