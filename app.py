"""
app.py
------
Main Streamlit application: login gate, theming, navigation, and all pages
of the Inventory Management System dashboard.

Run with:  streamlit run app.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

import database
import inventory
import sales
import analytics
import utils
import seed_data


# ---------------------------------------------------------------------------
# PAGE CONFIG + THEME
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="StockHub — Inventory Management",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

database.init_db()


def ensure_demo_data():
    """Populate demo data on fresh deploys where inventory.db does not exist."""
    with database.get_connection() as conn:
        product_count = conn.execute("SELECT COUNT(*) AS c FROM Products").fetchone()["c"]
    if product_count == 0:
        seed_data.seed_all(verbose=False)


ensure_demo_data()


def load_theme(dark_mode: bool):
    """Injects custom CSS for the Zepto-inspired visual identity.
    Palette: deep violet primary, electric lime accent, soft red danger.
    """
    if dark_mode:
        bg = "#121113"
        surface = "#1C1B1F"
        surface2 = "#242329"
        text = "#F4F2F7"
        text_secondary = "#A8A3AE"
        border = "#33313A"
    else:
        bg = "#FAFAF9"
        surface = "#FFFFFF"
        surface2 = "#F3F0FA"
        text = "#18181B"
        text_secondary = "#71717A"
        border = "#E8E6EE"

    primary = "#5B21B6"
    primary_light = "#7C3AED"
    accent = "#A3E635"
    danger = "#DC2626"
    warning = "#F59E0B"

    st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;600;700;800&family=Inter:wght@400;500;600&display=swap');

        html, body, [class*="css"] {{
            font-family: 'Inter', sans-serif;
        }}

        .stApp {{
            background-color: {bg};
            color: {text};
        }}

        h1, h2, h3, .kpi-value {{
            font-family: 'Sora', sans-serif;
        }}

        /* Hide default Streamlit chrome for a cleaner app feel */
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}

        /* --- Top brand bar --- */
        .brand-bar {{
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 4px 0 18px 0;
        }}
        .brand-mark {{
            background: linear-gradient(135deg, {primary}, {primary_light});
            color: white;
            font-family: 'Sora', sans-serif;
            font-weight: 800;
            font-size: 20px;
            width: 40px;
            height: 40px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .brand-title {{
            font-family: 'Sora', sans-serif;
            font-weight: 700;
            font-size: 22px;
            color: {text};
            letter-spacing: -0.3px;
        }}
        .brand-sub {{
            font-size: 12px;
            color: {text_secondary};
            margin-top: -4px;
        }}

        /* --- KPI cards: warehouse-bin styled --- */
        .kpi-card {{
            background: {surface};
            border: 1px solid {border};
            border-left: 4px solid {primary};
            border-radius: 10px;
            padding: 16px 18px;
            height: 100%;
        }}
        .kpi-card.accent {{ border-left-color: {accent}; }}
        .kpi-card.danger {{ border-left-color: {danger}; }}
        .kpi-card.warning {{ border-left-color: {warning}; }}

        .kpi-eyebrow {{
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 0.6px;
            text-transform: uppercase;
            color: {text_secondary};
            margin-bottom: 6px;
        }}
        .kpi-value {{
            font-size: 26px;
            font-weight: 700;
            color: {text};
            line-height: 1.1;
        }}
        .kpi-delta {{
            font-size: 12px;
            color: {text_secondary};
            margin-top: 4px;
        }}

        /* --- Section headers --- */
        .section-title {{
            font-family: 'Sora', sans-serif;
            font-weight: 700;
            font-size: 18px;
            color: {text};
            margin: 6px 0 12px 0;
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        /* --- Alert pills --- */
        .alert-pill {{
            background: {surface2};
            border-radius: 8px;
            padding: 10px 14px;
            margin-bottom: 8px;
            font-size: 14px;
            color: {text};
            border-left: 3px solid {danger};
        }}

        /* Chat bubbles */
        .chat-user {{
            background: {primary};
            color: white;
            padding: 10px 14px;
            border-radius: 12px 12px 2px 12px;
            margin: 6px 0;
            max-width: 80%;
            margin-left: auto;
            font-size: 14px;
        }}
        .chat-bot {{
            background: {surface2};
            color: {text};
            padding: 10px 14px;
            border-radius: 12px 12px 12px 2px;
            margin: 6px 0;
            max-width: 85%;
            font-size: 14px;
        }}

        div[data-testid="stMetricValue"] {{
            font-family: 'Sora', sans-serif;
        }}

        .stButton button {{
            border-radius: 8px;
            font-weight: 600;
        }}
        .stButton button[kind="primary"] {{
            background-color: {primary};
            border-color: {primary};
        }}
    </style>
    """, unsafe_allow_html=True)

    # Return palette so chart functions can stay theme-consistent.
    return {
        "primary": primary, "primary_light": primary_light, "accent": accent,
        "danger": danger, "warning": warning, "text": text,
        "text_secondary": text_secondary, "surface": surface, "bg": bg,
    }


# ---------------------------------------------------------------------------
# SESSION STATE INIT
# ---------------------------------------------------------------------------

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = None
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

PALETTE = load_theme(st.session_state.dark_mode)


# ---------------------------------------------------------------------------
# LOGIN PAGE
# ---------------------------------------------------------------------------

def render_login():
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown(f"""
            <div style="text-align:center; margin-top: 60px; margin-bottom: 20px;">
                <div style="background: linear-gradient(135deg, {PALETTE['primary']}, {PALETTE['primary_light']});
                            width: 64px; height: 64px; border-radius: 16px; display: inline-flex;
                            align-items: center; justify-content: center; font-size: 28px;">📦</div>
                <h1 style="font-family:'Sora',sans-serif; margin-top: 14px; margin-bottom:0;">StockHub</h1>
                <p style="color:{PALETTE['text_secondary']}; margin-top:4px;">Inventory Management System</p>
            </div>
        """, unsafe_allow_html=True)

        with st.form("login_form"):
            username = st.text_input("Username", placeholder="admin")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            submitted = st.form_submit_button("Log in", use_container_width=True, type="primary")

            if submitted:
                user = database.verify_user(username.strip(), password)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.username = user["Username"]
                    st.session_state.role = user["Role"]
                    st.rerun()
                else:
                    st.error("Invalid username or password.")

        st.caption("Demo credentials — **admin** / **admin123**")


# ---------------------------------------------------------------------------
# REUSABLE UI HELPERS
# ---------------------------------------------------------------------------

def kpi_card(col, eyebrow, value, variant="default", delta=None):
    css_class = "kpi-card" if variant == "default" else f"kpi-card {variant}"
    delta_html = f'<div class="kpi-delta">{delta}</div>' if delta else ""
    col.markdown(f"""
        <div class="{css_class}">
            <div class="kpi-eyebrow">{eyebrow}</div>
            <div class="kpi-value">{value}</div>
            {delta_html}
        </div>
    """, unsafe_allow_html=True)


def section_title(emoji, text):
    st.markdown(f'<div class="section-title">{emoji} {text}</div>', unsafe_allow_html=True)


CHART_COLORWAY = [PALETTE["primary"], PALETTE["accent"], PALETTE["warning"],
                  "#0EA5E9", "#EC4899", "#14B8A6", PALETTE["danger"], "#F97316"]


def style_fig(fig):
    fig.update_layout(
        plot_bgcolor=PALETTE["surface"],
        paper_bgcolor=PALETTE["surface"],
        font_color=PALETTE["text"],
        font_family="Inter",
        colorway=CHART_COLORWAY,
        margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
    )
    return fig


# ---------------------------------------------------------------------------
# PAGE: DASHBOARD
# ---------------------------------------------------------------------------

def page_dashboard():
    section_title("📊", "Overview")
    kpis = analytics.get_kpi_summary()

    c1, c2, c3, c4, c5 = st.columns(5)
    kpi_card(c1, "Total Products", utils.format_number(kpis["total_products"]))
    kpi_card(c2, "Inventory Value", utils.format_currency(kpis["inventory_value"]), variant="accent")
    kpi_card(c3, "Total Revenue", utils.format_currency(kpis["total_revenue"]))
    kpi_card(c4, "Units Sold", utils.format_number(kpis["total_units_sold"]))
    kpi_card(c5, "Low Stock Items", utils.format_number(kpis["low_stock_count"]),
              variant="danger" if kpis["low_stock_count"] > 0 else "default")

    st.write("")
    left, right = st.columns([1.4, 1])

    with left:
        section_title("📈", "Daily Sales Trend (Last 60 Days)")
        trend = analytics.get_daily_sales_trend(60)
        if trend.empty:
            st.info("No sales data yet.")
        else:
            fig = px.area(trend, x="Date", y="Revenue", markers=False)
            fig.update_traces(line_color=PALETTE["primary"], fillcolor="rgba(91,33,182,0.15)")
            st.plotly_chart(style_fig(fig), use_container_width=True)

    with right:
        section_title("🏷️", "Revenue by Category")
        cat = analytics.get_category_revenue()
        if cat.empty:
            st.info("No sales data yet.")
        else:
            fig = px.pie(cat, names="Category", values="Revenue", hole=0.55)
            fig.update_traces(textinfo="percent+label")
            st.plotly_chart(style_fig(fig), use_container_width=True)

    st.write("")
    left2, right2 = st.columns(2)

    with left2:
        section_title("🏆", "Top Selling Products")
        top = analytics.get_top_selling_products(8)
        if top.empty:
            st.info("No sales data yet.")
        else:
            fig = px.bar(top, x="QuantitySold", y="ProductName", orientation="h",
                          color="Category", text="QuantitySold")
            fig.update_layout(yaxis=dict(autorange="reversed"), showlegend=False)
            st.plotly_chart(style_fig(fig), use_container_width=True)

    with right2:
        section_title("🚨", "Low Stock Alerts")
        low = inventory.get_low_stock_products()
        if low.empty:
            st.success("All products are sufficiently stocked. ✅")
        else:
            for _, row in low.head(8).iterrows():
                pct = row["CurrentStock"] / max(row["ReorderLevel"], 1)
                st.markdown(f"""
                    <div class="alert-pill">
                        <b>{row['ProductName']}</b> — {row['CurrentStock']} left
                        <span style="color:{PALETTE['text_secondary']};">
                        (reorder level: {row['ReorderLevel']})</span>
                    </div>
                """, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# PAGE: INVENTORY MANAGEMENT
# ---------------------------------------------------------------------------

def page_inventory():
    section_title("📦", "Inventory Management")

    tab1, tab2, tab3 = st.tabs(["Browse & Search", "Add Product", "Manage Stock"])

    with tab1:
        col1, col2, col3 = st.columns([2, 1, 1])
        keyword = col1.text_input("🔍 Search by product name", "")
        categories = ["All"] + inventory.get_categories()
        category = col2.selectbox("Category", categories)
        col3.write("")
        col3.write("")
        show_inactive = col3.checkbox("Show discontinued")

        df = inventory.search_products(keyword, category)
        if show_inactive:
            df_all = inventory.get_all_products(include_inactive=True)
            if keyword:
                df_all = df_all[df_all["ProductName"].str.contains(keyword, case=False, na=False)]
            if category != "All":
                df_all = df_all[df_all["Category"] == category]
            df = df_all

        st.dataframe(
            df[["ProductID", "ProductName", "Category", "Price", "CurrentStock",
                "ReorderLevel", "SupplierName"]],
            use_container_width=True, hide_index=True,
        )

        exp1, exp2 = st.columns(2)
        exp1.download_button("⬇️ Export CSV", utils.dataframe_to_csv_bytes(df),
                              "products.csv", "text/csv", use_container_width=True)
        exp2.download_button("⬇️ Export Excel", utils.dataframe_to_excel_bytes(df, "Products"),
                              "products.xlsx",
                              "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                              use_container_width=True)

        st.write("")
        st.markdown("**Delete a product**")
        del_col1, del_col2 = st.columns([3, 1])
        if not df.empty:
            options = {f"{r['ProductName']} (ID {r['ProductID']})": r["ProductID"] for _, r in df.iterrows()}
            choice = del_col1.selectbox("Select product to remove", list(options.keys()), label_visibility="collapsed")
            if del_col2.button("🗑️ Delete", use_container_width=True):
                inventory.delete_product(options[choice])
                st.success(f"Removed '{choice}'. (Soft-deleted — sales history preserved.)")
                st.rerun()

    with tab2:
        st.markdown("Add a new product to the catalog.")
        suppliers_df = inventory.get_all_suppliers()
        supplier_options = {"— None —": None}
        supplier_options.update({r["SupplierName"]: r["SupplierID"] for _, r in suppliers_df.iterrows()})

        with st.form("add_product_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            name = c1.text_input("Product Name *")
            cat = c2.text_input("Category *", placeholder="e.g. Snacks, Dairy, Beverages")
            c3, c4, c5 = st.columns(3)
            price = c3.number_input("Price (₹) *", min_value=0.0, step=1.0)
            stock = c4.number_input("Starting Stock", min_value=0, step=1, value=0)
            reorder = c5.number_input("Reorder Level", min_value=0, step=1, value=10)
            supplier_name = st.selectbox("Supplier", list(supplier_options.keys()))

            submitted = st.form_submit_button("➕ Add Product", type="primary")
            if submitted:
                try:
                    inventory.add_product(name, cat, price, int(stock), int(reorder),
                                           supplier_options[supplier_name])
                    st.success(f"Added '{name}' to inventory.")
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))

        with st.expander("➕ Add a new supplier instead"):
            with st.form("add_supplier_form", clear_on_submit=True):
                sname = st.text_input("Supplier Name *")
                sphone = st.text_input("Contact Number")
                semail = st.text_input("Email")
                if st.form_submit_button("Add Supplier"):
                    try:
                        inventory.add_supplier(sname, sphone, semail)
                        st.success(f"Added supplier '{sname}'.")
                        st.rerun()
                    except ValueError as e:
                        st.error(str(e))

    with tab3:
        st.markdown("Adjust stock levels or edit product details.")
        products_df = inventory.get_all_products()
        if products_df.empty:
            st.info("No products yet — add one in the 'Add Product' tab.")
        else:
            options = {f"{r['ProductName']} (Stock: {r['CurrentStock']})": r["ProductID"]
                       for _, r in products_df.iterrows()}
            choice = st.selectbox("Select Product", list(options.keys()))
            pid = options[choice]
            product = inventory.get_product_by_id(pid)

            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Current Stock", product["CurrentStock"])
                delta = st.number_input("Adjust stock by (+ / -)", value=0, step=1, key="stock_delta")
                if st.button("Apply Stock Adjustment", type="primary"):
                    try:
                        new_stock = inventory.adjust_stock(pid, int(delta))
                        st.success(f"Stock updated to {new_stock}.")
                        st.rerun()
                    except ValueError as e:
                        st.error(str(e))
            with c2:
                new_price = st.number_input("Price (₹)", value=float(product["Price"]), step=1.0, key="edit_price")
                if st.button("Update Price"):
                    inventory.update_product(pid, Price=new_price)
                    st.success("Price updated.")
                    st.rerun()
            with c3:
                new_reorder = st.number_input("Reorder Level", value=int(product["ReorderLevel"]), step=1, key="edit_reorder")
                if st.button("Update Reorder Level"):
                    inventory.update_product(pid, ReorderLevel=int(new_reorder))
                    st.success("Reorder level updated.")
                    st.rerun()


# ---------------------------------------------------------------------------
# PAGE: SALES MANAGEMENT
# ---------------------------------------------------------------------------

def page_sales():
    section_title("🧾", "Sales Management")

    tab1, tab2 = st.tabs(["Record Sale", "Sales History"])

    with tab1:
        products_df = inventory.get_all_products()
        if products_df.empty:
            st.info("No products available. Add products first.")
        else:
            options = {f"{r['ProductName']} — ₹{r['Price']} (Stock: {r['CurrentStock']})": r["ProductID"]
                       for _, r in products_df.iterrows()}
            with st.form("record_sale_form", clear_on_submit=True):
                choice = st.selectbox("Product", list(options.keys()))
                qty = st.number_input("Quantity Sold", min_value=1, step=1, value=1)
                sale_date = st.date_input("Sale Date", value=datetime.now())
                submitted = st.form_submit_button("✅ Record Sale", type="primary")

                if submitted:
                    pid = options[choice]
                    try:
                        sale_id = sales.record_sale(pid, int(qty), sale_date.strftime("%Y-%m-%d"))
                        st.success(f"Sale #{sale_id} recorded. Stock automatically reduced.")
                        st.rerun()
                    except ValueError as e:
                        st.error(str(e))

    with tab2:
        history = sales.get_sales_history(limit=300)
        if history.empty:
            st.info("No sales recorded yet.")
        else:
            c1, c2 = st.columns([1, 3])
            cat_filter = c1.selectbox("Filter by category", ["All"] + sorted(history["Category"].unique().tolist()))
            display_df = history if cat_filter == "All" else history[history["Category"] == cat_filter]

            st.dataframe(display_df, use_container_width=True, hide_index=True)

            exp1, exp2 = st.columns(2)
            exp1.download_button("⬇️ Export CSV", utils.dataframe_to_csv_bytes(display_df),
                                  "sales_history.csv", "text/csv", use_container_width=True)
            exp2.download_button("⬇️ Export Excel", utils.dataframe_to_excel_bytes(display_df, "Sales"),
                                  "sales_history.xlsx",
                                  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                  use_container_width=True)

            st.write("")
            st.markdown("**Undo a sale** (restocks the item)")
            d1, d2 = st.columns([3, 1])
            sale_options = {f"#{r['SaleID']} — {r['ProductName']} x{r['QuantitySold']} ({r['SaleDate']})": r["SaleID"]
                             for _, r in display_df.head(50).iterrows()}
            sale_choice = d1.selectbox("Select sale", list(sale_options.keys()), label_visibility="collapsed")
            if d2.button("↩️ Undo Sale", use_container_width=True):
                sales.delete_sale(sale_options[sale_choice], restock=True)
                st.success("Sale removed and stock restored.")
                st.rerun()


# ---------------------------------------------------------------------------
# PAGE: ANALYTICS / BUSINESS QUESTIONS
# ---------------------------------------------------------------------------

def page_analytics():
    section_title("🔍", "Business Insights")

    q = st.selectbox("Choose a business question", [
        "1. Which products sell the fastest?",
        "2. Which products need reordering?",
        "3. Which categories generate the highest revenue?",
        "4. Which products have not sold in the last 30 days?",
        "5. What is the current inventory value?",
        "6. Which supplier provides the most products?",
    ])

    st.write("")

    if q.startswith("1"):
        velocity = analytics.get_sales_velocity()
        if velocity.empty:
            st.info("Not enough recent sales data.")
        else:
            fig = px.bar(velocity.head(10), x="AvgUnitsPerDay", y="ProductName",
                          orientation="h", color="Category", text="AvgUnitsPerDay")
            fig.update_layout(yaxis=dict(autorange="reversed"))
            st.plotly_chart(style_fig(fig), use_container_width=True)
            st.caption("Average units sold per day over the last 30 days — the clearest read on sell-through speed.")
            st.dataframe(velocity, use_container_width=True, hide_index=True)

    elif q.startswith("2"):
        reorder_df = analytics.get_reorder_list()
        if reorder_df.empty:
            st.success("No products currently need reordering. ✅")
        else:
            st.dataframe(reorder_df, use_container_width=True, hide_index=True)
            st.download_button("⬇️ Export Reorder List (CSV)",
                                utils.dataframe_to_csv_bytes(reorder_df),
                                "reorder_list.csv", "text/csv")

    elif q.startswith("3"):
        cat = analytics.get_category_revenue()
        if cat.empty:
            st.info("No sales data yet.")
        else:
            fig = px.bar(cat, x="Category", y="Revenue", color="Category", text="Revenue")
            st.plotly_chart(style_fig(fig), use_container_width=True)
            st.dataframe(cat, use_container_width=True, hide_index=True)

    elif q.startswith("4"):
        stale = analytics.get_stale_products(30)
        if stale.empty:
            st.success("Every product has sold within the last 30 days. ✅")
        else:
            st.dataframe(stale, use_container_width=True, hide_index=True)
            st.caption(f"{len(stale)} product(s) flagged as dead stock — consider a promotion or discontinuation.")

    elif q.startswith("5"):
        value = inventory.get_inventory_value()
        st.markdown(f"### Total Inventory Value: {utils.format_currency(value)}")
        by_cat = analytics.get_inventory_value_by_category()
        if not by_cat.empty:
            fig = px.pie(by_cat, names="Category", values="InventoryValue", hole=0.5)
            st.plotly_chart(style_fig(fig), use_container_width=True)
            st.dataframe(by_cat, use_container_width=True, hide_index=True)

    elif q.startswith("6"):
        sup = analytics.get_supplier_product_counts()
        fig = px.bar(sup, x="SupplierName", y="ProductCount", color="SupplierName")
        fig.update_layout(showlegend=False, xaxis_tickangle=-30)
        st.plotly_chart(style_fig(fig), use_container_width=True)
        st.dataframe(sup, use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------------
# PAGE: AI FEATURES
# ---------------------------------------------------------------------------

def page_ai():
    section_title("🤖", "AI-Powered Features")

    tab1, tab2, tab3 = st.tabs(["Demand Forecast", "Reorder Recommendations", "Stockout Predictions"])

    with tab1:
        products_df = inventory.get_all_products()
        options = {r["ProductName"]: r["ProductID"] for _, r in products_df.iterrows()}
        c1, c2 = st.columns([2, 1])
        choice = c1.selectbox("Select a product", list(options.keys()))
        days_ahead = c2.slider("Forecast horizon (days)", 3, 30, 7)

        pid = options[choice]
        forecast = analytics.forecast_demand(pid, days_ahead)

        m1, m2, m3 = st.columns(3)
        m1.metric("Forecasted Demand", f"{forecast['forecast_units']} units")
        m2.metric("Avg Daily Rate", f"{forecast['avg_daily_rate']} units/day")
        m3.metric("Confidence", forecast["confidence"].title())

        st.caption("Forecast uses a linear regression trend fitted on the product's daily sales history "
                    "(scikit-learn `LinearRegression`). More history → higher confidence.")

        # Show historical + projected trend visually
        prod_sales = sales.get_all_sales_raw()
        prod_sales = prod_sales[prod_sales["ProductID"] == pid]
        if not prod_sales.empty:
            daily = prod_sales.groupby(prod_sales["SaleDate"].dt.date)["QuantitySold"].sum().reset_index()
            daily.columns = ["Date", "QuantitySold"]
            fig = px.line(daily, x="Date", y="QuantitySold", markers=True)
            fig.update_traces(line_color=PALETTE["primary"])
            st.plotly_chart(style_fig(fig), use_container_width=True)

    with tab2:
        st.markdown("AI-generated reorder suggestions based on forecasted demand vs. current stock.")
        days_ahead2 = st.slider("Planning horizon (days)", 3, 30, 7, key="reorder_horizon")
        recs = analytics.get_reorder_recommendations(days_ahead2)
        if recs.empty:
            st.info("No products in inventory yet.")
        else:
            def highlight_runout(val):
                return "background-color: rgba(220,38,38,0.15)" if val else ""
            st.dataframe(
                recs.style.map(highlight_runout, subset=["WillRunOut"]),
                use_container_width=True, hide_index=True,
            )
            st.download_button("⬇️ Export Recommendations (Excel)",
                                utils.dataframe_to_excel_bytes(recs, "Reorder Recs"),
                                "reorder_recommendations.xlsx",
                                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    with tab3:
        st.markdown("Products predicted to run out of stock **within the next 7 days**, based on demand forecasting.")
        risky = analytics.predict_stockouts_next_week()
        if risky.empty:
            st.success("No products are predicted to run out within 7 days. ✅")
        else:
            for _, row in risky.iterrows():
                st.markdown(f"""
                    <div class="alert-pill">
                        🔥 <b>{row['ProductName']}</b> — projected stock in 7 days:
                        <b>{row['ProjectedStockAfter']}</b> units
                        (currently {row['CurrentStock']}, forecast demand {row['ForecastDemand_NextNDays']})
                    </div>
                """, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# PAGE: AI CHAT ASSISTANT
# ---------------------------------------------------------------------------

def page_chat():
    section_title("💬", "AI Chat Assistant")
    st.caption("Ask natural-language questions about your inventory and sales.")

    suggestions = [
        "Which products are low in stock?",
        "What are the top-selling products?",
        "How much inventory value do we currently have?",
        "Which products should be reordered?",
    ]
    cols = st.columns(len(suggestions))
    for col, s in zip(cols, suggestions):
        if col.button(s, use_container_width=True):
            st.session_state.chat_history.append(("user", s))
            st.session_state.chat_history.append(("bot", utils.answer_chat_query(s)))

    for role, msg in st.session_state.chat_history:
        css_class = "chat-user" if role == "user" else "chat-bot"
        st.markdown(f'<div class="{css_class}">{msg}</div>', unsafe_allow_html=True)

    user_input = st.chat_input("Type your question...")
    if user_input:
        st.session_state.chat_history.append(("user", user_input))
        answer = utils.answer_chat_query(user_input)
        st.session_state.chat_history.append(("bot", answer))
        st.rerun()


# ---------------------------------------------------------------------------
# SIDEBAR + ROUTING
# ---------------------------------------------------------------------------

def render_sidebar():
    with st.sidebar:
        st.markdown(f"""
            <div class="brand-bar">
                <div class="brand-mark">S</div>
                <div>
                    <div class="brand-title">StockHub</div>
                    <div class="brand-sub">Inventory Management</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown(f"👋 Logged in as **{st.session_state.username}**")

        page = st.radio("Navigate", [
            "📊 Dashboard", "📦 Inventory", "🧾 Sales",
            "🔍 Business Insights", "🤖 AI Features", "💬 Chat Assistant",
        ], label_visibility="collapsed")

        st.write("")
        st.toggle("🌙 Dark Mode", key="dark_mode")

        with st.expander("⚙️ Admin Tools"):
            st.caption("Resets all data and regenerates 90 days of sample sales.")
            if st.button("🔄 Reset Sample Data", use_container_width=True):
                with st.spinner("Regenerating sample data..."):
                    seed_data.seed_all(verbose=False)
                st.success("Sample data reset.")
                st.rerun()

        st.write("")
        if st.button("🚪 Log out", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.rerun()

        return page


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    if not st.session_state.logged_in:
        render_login()
        return

    page = render_sidebar()

    if page == "📊 Dashboard":
        page_dashboard()
    elif page == "📦 Inventory":
        page_inventory()
    elif page == "🧾 Sales":
        page_sales()
    elif page == "🔍 Business Insights":
        page_analytics()
    elif page == "🤖 AI Features":
        page_ai()
    elif page == "💬 Chat Assistant":
        page_chat()


if __name__ == "__main__":
    main()
