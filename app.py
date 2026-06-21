"""
app.py
------
StockHub — Inventory Management System (single-file build).

Everything that used to live in theme.py / components.py / pages_/*.py is
merged into this one file so it can be pasted directly into app.py. The
backend modules (database.py, inventory.py, sales.py, analytics.py,
utils.py, seed_data.py) are NOT merged here -- they stay as separate files
since this is meant to be dropped in alongside them, not replace them.

File map of what's inside, in order:
  1. Imports + page config + demo-data bootstrap
  2. THEME            -- palette tokens + CSS (load_theme, style_fig)
  3. COMPONENTS        -- shared UI: KPI cards, badges, page headers, empty states
  4. PAGE: DASHBOARD
  5. PAGE: INVENTORY
  6. PAGE: SALES
  7. PAGE: SUPPLIERS
  8. PAGE: BUSINESS INSIGHTS (analytics)
  9. PAGE: AI FEATURES
  10. PAGE: CHAT ASSISTANT
  11. PAGE: SETTINGS
  12. LOGIN + SIDEBAR + ROUTING + main()

To re-skin the app, edit the palette block inside load_theme() in the
THEME section below -- every color used anywhere in the file is derived
from those few tokens.

Run with:  streamlit run app.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta

import database
import inventory
import sales
import analytics
import utils
import seed_data


# ---------------------------------------------------------------------------
# PAGE CONFIG + DATA BOOTSTRAP
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


# ---------------------------------------------------------------------------
# SESSION STATE INIT
# ---------------------------------------------------------------------------

_DEFAULTS = {
    "logged_in": False,
    "username": None,
    "role": "staff",
    "dark_mode": True,
    "chat_history": [],
    "_pending_nav": None,
}
for _key, _default in _DEFAULTS.items():
    if _key not in st.session_state:
        st.session_state[_key] = _default


# ============================================================================
# THEME — palette tokens + CSS. Edit the colors here to re-skin the app.
# ============================================================================

def load_theme(dark_mode: bool) -> dict:
    """Injects the app's CSS and returns the active palette as a dict so
    Python code (chart colors, inline styles) can stay in sync with it.
    """
    if dark_mode:
        bg = "#0F1117"
        sidebar_bg = "#171923"
        surface = "#1E2230"
        surface2 = "#252A3B"
        surface3 = "#2C3142"
        text = "#F8FAFC"
        text_secondary = "#94A3B8"
        border = "rgba(255,255,255,0.08)"
        shadow = "rgba(0,0,0,0.4)"
    else:
        bg = "#FAFAF9"
        sidebar_bg = "#FFFFFF"
        surface = "#FFFFFF"
        surface2 = "#F3F0FA"
        surface3 = "#ECE8F7"
        text = "#18181B"
        text_secondary = "#71717A"
        border = "#E8E6EE"
        shadow = "rgba(15,17,23,0.08)"

    primary = "#7C3AED"
    primary_hover = "#6D28D9"
    accent = "#A855F7"
    success = "#22C55E"
    warning = "#F59E0B"
    danger = "#EF4444"
    info = "#0EA5E9"

    st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        html, body, [class*="css"] {{
            font-family: 'Inter', sans-serif;
        }}

        .stApp {{
            background-color: {bg};
            color: {text};
        }}

        h1, h2, h3 {{
            font-family: 'Inter', sans-serif;
            letter-spacing: -0.01em;
        }}

        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}

        section[data-testid="stSidebar"] {{
            background-color: {sidebar_bg};
            border-right: 1px solid {border};
        }}

        /* ---------------------------------------------------------------
           BRAND MARK -- the one non-AI place the gradient appears
        --------------------------------------------------------------- */
        .brand-bar {{
            display: flex; align-items: center; gap: 10px;
            padding: 4px 0 18px 0;
        }}
        .brand-mark {{
            background: {primary}; color: white; font-weight: 700; font-size: 18px;
            width: 36px; height: 36px; border-radius: 10px;
            display: flex; align-items: center; justify-content: center;
        }}
        .brand-title {{ font-weight: 700; font-size: 17px; color: {text}; letter-spacing: -0.2px; }}
        .brand-sub {{ font-size: 12px; color: {text_secondary}; margin-top: -2px; }}

        /* ---------------------------------------------------------------
           PAGE HEADER -- consistent title/subtitle/action row used at the
           top of every page, so navigating between pages feels like one
           coherent product instead of six separately-designed screens
        --------------------------------------------------------------- */
        .page-header {{
            display: flex; align-items: flex-start; justify-content: space-between;
            margin-bottom: 22px; flex-wrap: wrap; gap: 12px;
        }}
        .page-header h2 {{ margin: 0; font-size: 22px; font-weight: 700; color: {text}; }}
        .page-header p {{ margin: 4px 0 0 0; font-size: 13.5px; color: {text_secondary}; }}
        .page-icon {{
            display: inline-flex; align-items: center; justify-content: center;
            width: 34px; height: 34px; border-radius: 10px;
            background: {surface2}; margin-right: 10px; font-size: 16px;
        }}

        /* ---------------------------------------------------------------
           KPI CARDS -- no icon-in-a-square, flat colored corner glow
        --------------------------------------------------------------- */
        .kpi-card {{
            position: relative; background: {surface}; border: 1px solid {border};
            border-radius: 16px; padding: 18px 20px; height: 100%; overflow: hidden;
            transition: border-color 0.2s;
        }}
        .kpi-card:hover {{ border-color: rgba(124,58,237,0.35); }}
        .kpi-card::before {{
            content: ""; position: absolute; top: -24px; right: -24px;
            width: 96px; height: 96px; border-radius: 50%;
            background: radial-gradient(circle, var(--glow-color, {primary}), transparent 70%);
            opacity: 0.18; filter: blur(14px); pointer-events: none;
        }}
        .kpi-card.accent  {{ --glow-color: {accent}; }}
        .kpi-card.warning {{ --glow-color: {warning}; }}
        .kpi-card.danger  {{ --glow-color: {danger}; }}
        .kpi-card.success {{ --glow-color: {success}; }}

        .kpi-eyebrow {{ font-size: 13px; color: {text_secondary}; margin-bottom: 8px; position: relative; }}
        .kpi-row {{ display: flex; align-items: flex-end; justify-content: space-between; gap: 10px; position: relative; }}
        .kpi-value {{ font-size: 26px; font-weight: 700; color: {text}; line-height: 1; }}
        .kpi-trend {{ font-size: 12px; font-weight: 600; padding-bottom: 2px; white-space: nowrap; }}
        .kpi-trend.up {{ color: {success}; }}
        .kpi-trend.down {{ color: {danger}; }}

        /* ---------------------------------------------------------------
           HERO CARD -- revenue gets visual weight others don't
        --------------------------------------------------------------- */
        .hero-card {{
            position: relative; height: 100%;
            background: linear-gradient(155deg, {surface} 0%, #221B36 100%);
            border: 1px solid rgba(168,85,247,0.18); border-radius: 16px;
            padding: 20px 22px 16px;
        }}
        .hero-eyebrow {{ font-size: 13px; color: {text_secondary}; margin-bottom: 6px; }}
        .hero-value {{ font-size: 32px; font-weight: 700; color: {text}; line-height: 1; }}
        .hero-trend {{ font-size: 12px; font-weight: 600; }}

        /* ---------------------------------------------------------------
           SECTION HEADERS
        --------------------------------------------------------------- */
        .section-title {{
            font-weight: 700; font-size: 17px; color: {text};
            margin: 4px 0 14px 0; display: flex; align-items: center; gap: 8px;
        }}
        .section-sub {{ font-size: 13px; color: {text_secondary}; margin-top: -10px; margin-bottom: 14px; }}

        /* ---------------------------------------------------------------
           STATUS BADGE -- shared vocabulary: stock state, order state,
           confidence level, all reuse this same component
        --------------------------------------------------------------- */
        .status-badge {{
            display: inline-flex; align-items: center; gap: 6px;
            padding: 4px 10px; border-radius: 999px; font-size: 12px; font-weight: 600;
        }}
        .status-dot {{ width: 6px; height: 6px; border-radius: 50%; }}

        /* ---------------------------------------------------------------
           INVENTORY / ENTITY CARD -- colored left edge instead of a
           letter-avatar (products don't have "initials")
        --------------------------------------------------------------- */
        .inv-card {{
            background: {surface}; border: 1px solid {border};
            border-left: 3px solid var(--stripe-color, {primary});
            border-radius: 4px 16px 16px 4px; padding: 16px 18px; margin-bottom: 4px;
            transition: transform 0.15s, box-shadow 0.15s;
        }}
        .inv-card:hover {{ transform: translateY(-1px); box-shadow: 0 8px 20px -8px {shadow}; }}
        .inv-name {{ font-weight: 600; font-size: 14px; color: {text}; margin-bottom: 2px; }}
        .inv-meta {{ font-size: 12px; color: {text_secondary}; margin-bottom: 12px; }}
        .inv-stock-row {{ display:flex; justify-content: space-between; font-size: 12px; margin-bottom: 6px; }}
        .inv-stock-bar-bg {{ height: 6px; border-radius: 4px; background: rgba(127,127,127,0.15); overflow: hidden; }}
        .inv-stock-bar-fill {{ height: 100%; border-radius: 4px; transition: width 0.4s; }}
        .inv-footer {{
            display: flex; justify-content: space-between; align-items: center;
            margin-top: 12px; padding-top: 10px; border-top: 1px solid {border};
            font-size: 12px; color: {text_secondary};
        }}

        /* ---------------------------------------------------------------
           SUPPLIER CARD -- same family as inv-card but with a contact row
        --------------------------------------------------------------- */
        .supplier-card {{
            background: {surface}; border: 1px solid {border}; border-radius: 14px;
            padding: 16px 18px; margin-bottom: 4px;
        }}
        .supplier-name {{ font-weight: 600; font-size: 14px; color: {text}; margin-bottom: 8px; }}
        .supplier-row {{ display: flex; align-items: center; gap: 8px; font-size: 12.5px; color: {text_secondary}; margin-bottom: 4px; }}
        .supplier-count-pill {{
            display: inline-flex; align-items: center; gap: 6px; font-size: 12px; font-weight: 600;
            padding: 3px 10px; border-radius: 999px; background: {surface2}; color: {primary};
            margin-top: 10px;
        }}

        /* ---------------------------------------------------------------
           ALERT PILLS
        --------------------------------------------------------------- */
        .alert-pill {{
            background: {surface2}; border-radius: 8px; padding: 10px 14px; margin-bottom: 8px;
            font-size: 14px; color: {text}; border-left: 3px solid {danger};
        }}
        .alert-pill.warning {{ border-left-color: {warning}; }}
        .alert-pill.info {{ border-left-color: {info}; }}

        /* ---------------------------------------------------------------
           EMPTY STATE -- designed, not a one-line st.info()
        --------------------------------------------------------------- */
        .empty-state {{
            text-align: center; padding: 48px 24px;
            background: {surface}; border: 1px dashed {border}; border-radius: 16px;
        }}
        .empty-state .empty-icon {{
            width: 48px; height: 48px; border-radius: 14px; background: {surface2};
            display: inline-flex; align-items: center; justify-content: center;
            font-size: 20px; margin-bottom: 14px;
        }}
        .empty-state .empty-title {{ font-weight: 600; font-size: 15px; color: {text}; margin-bottom: 4px; }}
        .empty-state .empty-sub {{ font-size: 13px; color: {text_secondary}; max-width: 320px; margin: 0 auto; }}

        /* ---------------------------------------------------------------
           AI CHAT -- the SECOND and only other gradient placement
        --------------------------------------------------------------- */
        .ai-badge {{
            display: inline-flex; align-items: center; justify-content: center;
            width: 26px; height: 26px; border-radius: 50%;
            background: linear-gradient(135deg, {primary}, {accent}); color: white;
            font-size: 13px; margin-right: 8px;
        }}
        .chat-user {{
            background: {primary}; color: white; padding: 10px 14px;
            border-radius: 12px 12px 2px 12px; margin: 6px 0; max-width: 80%;
            margin-left: auto; font-size: 14px;
        }}
        .chat-bot {{
            background: {surface2}; color: {text}; padding: 10px 14px;
            border-radius: 12px 12px 12px 2px; margin: 6px 0; max-width: 85%; font-size: 14px;
        }}

        /* ---------------------------------------------------------------
           NAV -- active state indicator, consistent with kpi/inv accents
        --------------------------------------------------------------- */
        div[data-testid="stSidebar"] .stRadio > div {{ gap: 2px; }}
        div[data-testid="stSidebar"] label[data-baseweb="radio"] {{
            border-radius: 10px; padding: 6px 10px; transition: background 0.15s;
        }}
        div[data-testid="stSidebar"] label[data-baseweb="radio"]:hover {{
            background: {surface2};
        }}

        /* ---------------------------------------------------------------
           DATA TABLES -- match dark theme instead of default light chrome
        --------------------------------------------------------------- */
        div[data-testid="stDataFrame"] {{
            border: 1px solid {border}; border-radius: 12px; overflow: hidden;
        }}

        /* ---------------------------------------------------------------
           METRICS / BUTTONS
        --------------------------------------------------------------- */
        div[data-testid="stMetricValue"] {{ font-family: 'Inter', sans-serif; }}

        .stButton button {{ border-radius: 10px; font-weight: 600; }}
        .stButton button[kind="primary"] {{
            background-color: {primary}; border-color: {primary};
        }}
        .stButton button[kind="primary"]:hover {{
            background-color: {primary_hover}; border-color: {primary_hover};
        }}

        /* ---------------------------------------------------------------
           TOASTS -- themed to match rather than Streamlit's default style
        --------------------------------------------------------------- */
        div[data-testid="stToast"] {{
            background: {surface3}; border: 1px solid {border}; color: {text};
        }}
    </style>
    """, unsafe_allow_html=True)

    return {
        "primary": primary, "primary_hover": primary_hover, "accent": accent,
        "danger": danger, "warning": warning, "success": success, "info": info,
        "text": text, "text_secondary": text_secondary,
        "surface": surface, "surface2": surface2, "surface3": surface3,
        "bg": bg, "border": border, "shadow": shadow,
    }


CHART_COLORWAY = ["#7C3AED", "#A855F7", "#F59E0B", "#0EA5E9", "#EC4899", "#14B8A6", "#EF4444", "#F97316"]


def style_fig(fig, palette: dict):
    """Applies consistent Plotly styling so every chart in the app shares
    the same background, font, and color sequence."""
    fig.update_layout(
        plot_bgcolor=palette["surface"],
        paper_bgcolor=palette["surface"],
        font_color=palette["text"],
        font_family="Inter",
        colorway=CHART_COLORWAY,
        margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
    )
    return fig


PALETTE = load_theme(st.session_state.dark_mode)


# ============================================================================
# COMPONENTS — shared UI building blocks used across every page
# ============================================================================

# ---------------------------------------------------------------------------
# PAGE HEADER -- used at the top of every page for a consistent feel
# ---------------------------------------------------------------------------

def page_header(icon: str, title: str, subtitle: str = None, action_label: str = None, action_key: str = None):
    """Renders a consistent title/subtitle row. If action_label is given,
    a button is rendered to the right and this function returns whether it
    was clicked, so callers can do:  if page_header(..., action_label="X"): ...
    """
    col1, col2 = st.columns([5, 1.4]) if action_label else (st.container(), None)
    if action_label:
        with col1:
            st.markdown(f"""
                <div class="page-header">
                    <div><span class="page-icon">{icon}</span></div>
                    <div style="flex:1;">
                        <h2 style="display:inline;">{title}</h2>
                        {f'<p>{subtitle}</p>' if subtitle else ''}
                    </div>
                </div>
            """, unsafe_allow_html=True)
        with col2:
            st.write("")
            clicked = st.button(action_label, type="primary", width='stretch', key=action_key)
        return clicked
    else:
        st.markdown(f"""
            <div class="page-header">
                <span class="page-icon">{icon}</span>
                <div>
                    <h2 style="display:inline;">{title}</h2>
                    {f'<p>{subtitle}</p>' if subtitle else ''}
                </div>
            </div>
        """, unsafe_allow_html=True)
        return False


def section_title(emoji: str, text: str, subtitle: str = None):
    st.markdown(f'<div class="section-title">{emoji} {text}</div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="section-sub">{subtitle}</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# KPI CARDS
# ---------------------------------------------------------------------------

def kpi_card(col, eyebrow: str, value: str, trend: str = None, trend_up: bool = True, variant: str = "default"):
    """Flat KPI card -- no icon square. Trend, if given, sits inline next
    to the number rather than in a separate colored pill."""
    css_class = "kpi-card" if variant == "default" else f"kpi-card {variant}"
    trend_html = ""
    if trend:
        arrow = "↑" if trend_up else "↓"
        trend_class = "up" if trend_up else "down"
        trend_html = f'<span class="kpi-trend {trend_class}">{arrow} {trend}</span>'
    col.markdown(f"""
        <div class="{css_class}">
            <div class="kpi-eyebrow">{eyebrow}</div>
            <div class="kpi-row">
                <div class="kpi-value">{value}</div>
                {trend_html}
            </div>
        </div>
    """, unsafe_allow_html=True)


def hero_revenue_card(col, palette: dict, value_str: str, trend_pct, sparkline_df, label="Revenue (last 30 days)"):
    """Wide hero card for a headline number, with a real inline sparkline
    built from actual data (never decoration). trend_pct is a signed float
    or None when there isn't enough history to compare periods."""
    spark = None
    if sparkline_df is not None and not sparkline_df.empty:
        spark = go.Figure(go.Scatter(
            x=sparkline_df.iloc[:, 0], y=sparkline_df.iloc[:, 1],
            mode="lines", line=dict(color=palette["accent"], width=2),
            fill="tozeroy", fillcolor="rgba(168,85,247,0.18)",
        ))
        spark.update_layout(
            height=70, margin=dict(l=0, r=0, t=0, b=0),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(visible=False), yaxis=dict(visible=False),
            showlegend=False,
        )

    if trend_pct is None:
        trend_html = ""
    else:
        arrow = "↑" if trend_pct >= 0 else "↓"
        color = palette["success"] if trend_pct >= 0 else palette["danger"]
        trend_html = (f'<div class="hero-trend" style="color:{color};">'
                       f'{arrow} {abs(trend_pct):.1f}% vs prior period</div>')

    with col:
        st.markdown(f"""
            <div class="hero-card">
                <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                    <div>
                        <div class="hero-eyebrow">{label}</div>
                        <div class="hero-value">{value_str}</div>
                    </div>
                    {trend_html}
                </div>
        """, unsafe_allow_html=True)
        if spark is not None:
            st.plotly_chart(spark, width='stretch', config={"displayModeBar": False})
        st.markdown("</div>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# STATUS BADGES
# ---------------------------------------------------------------------------

def status_badge_html(palette: dict, status: str) -> str:
    config = {
        "in-stock": ("In stock", palette["success"]),
        "low-stock": ("Low stock", palette["warning"]),
        "out-of-stock": ("Out of stock", palette["danger"]),
        "completed": ("Completed", palette["success"]),
        "pending": ("Pending", palette["warning"]),
        "failed": ("Failed", palette["danger"]),
    }
    label, color = config.get(status, (status.replace("-", " ").title(), palette["text_secondary"]))
    bg = f"{color}1F"
    return (f'<span class="status-badge" style="color:{color}; background:{bg};">'
            f'<span class="status-dot" style="background:{color};"></span>{label}</span>')


def stock_status(current_stock: int, reorder_level: int) -> str:
    if current_stock <= 0:
        return "out-of-stock"
    if current_stock <= reorder_level:
        return "low-stock"
    return "in-stock"


# ---------------------------------------------------------------------------
# EMPTY STATE -- a designed placeholder instead of a bare st.info()
# ---------------------------------------------------------------------------

def empty_state(icon: str, title: str, subtitle: str = ""):
    st.markdown(f"""
        <div class="empty-state">
            <div class="empty-icon">{icon}</div>
            <div class="empty-title">{title}</div>
            <div class="empty-sub">{subtitle}</div>
        </div>
    """, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# ENTITY CARDS
# ---------------------------------------------------------------------------

def inventory_card(col, palette: dict, item, status: str):
    stripe_color = {"in-stock": palette["success"], "low-stock": palette["warning"],
                     "out-of-stock": palette["danger"]}[status]
    stock_pct = min(100, (item["CurrentStock"] / max(item["ReorderLevel"] * 2, 1)) * 100)
    supplier = item["SupplierName"] if item.get("SupplierName") and str(item["SupplierName"]) != "nan" else "No supplier set"
    with col:
        st.markdown(f"""
            <div class="inv-card" style="--stripe-color: {stripe_color};">
                <div class="inv-name">{item['ProductName']}</div>
                <div class="inv-meta">{item['Category']} · ₹{item['Price']:.0f}</div>
                <div class="inv-stock-row">
                    <span>Stock level</span><b>{item['CurrentStock']} units</b>
                </div>
                <div class="inv-stock-bar-bg">
                    <div class="inv-stock-bar-fill" style="width:{stock_pct}%; background:{stripe_color};"></div>
                </div>
                <div class="inv-footer">
                    <span>{supplier}</span>{status_badge_html(palette, status)}
                </div>
            </div>
        """, unsafe_allow_html=True)


def supplier_card(col, palette: dict, supplier_row, product_count: int):
    phone = supplier_row.get("ContactNumber") or "No phone on file"
    email = supplier_row.get("Email") or "No email on file"
    with col:
        st.markdown(f"""
            <div class="supplier-card">
                <div class="supplier-name">{supplier_row['SupplierName']}</div>
                <div class="supplier-row">📞 {phone}</div>
                <div class="supplier-row">✉️ {email}</div>
                <div class="supplier-count-pill">📦 {product_count} product{'s' if product_count != 1 else ''}</div>
            </div>
        """, unsafe_allow_html=True)


# ============================================================================
# PAGE: DASHBOARD
# ============================================================================

def get_revenue_trend_pct():
    """Compares revenue in the last 30 days to the 30 days before that.
    Returns a signed percentage, or None if there isn't enough history in
    the prior period to make the comparison meaningful.
    """
    all_sales = sales.get_all_sales_raw()
    if all_sales.empty:
        return None

    now = datetime.now()
    last_30_start = now - timedelta(days=30)
    prior_30_start = now - timedelta(days=60)

    last_30 = all_sales[all_sales["SaleDate"] >= last_30_start]["Revenue"].sum()
    prior_30 = all_sales[(all_sales["SaleDate"] >= prior_30_start) &
                          (all_sales["SaleDate"] < last_30_start)]["Revenue"].sum()

    if prior_30 <= 0:
        return None
    return ((last_30 - prior_30) / prior_30) * 100


def render_dashboard(palette: dict):
    st.markdown(f"""
        <h2 style="margin-bottom:0;">Good evening, {st.session_state.username.title()} 👋</h2>
        <p style="color:{palette['text_secondary']}; margin-top:4px; margin-bottom:20px;">
            Manage your inventory efficiently.
        </p>
    """, unsafe_allow_html=True)

    # --- Quick actions: jump straight into the two most common tasks
    # without navigating away from the dashboard first. These set
    # "_pending_nav" rather than writing to the radio's own key directly --
    # by the time this code runs, render_sidebar() has already created the
    # "nav_radio" widget for this script pass, and Streamlit forbids
    # mutating a widget's key after it's instantiated in the same run.
    # The pending flag gets applied on the NEXT run, before the widget is
    # recreated (see render_sidebar). ---
    qa1, qa2, qa3, _ = st.columns([1, 1, 1, 2])
    if qa1.button("🧾 Record a sale", width='stretch'):
        st.session_state._pending_nav = "🧾 Sales"
        st.rerun()
    if qa2.button("➕ Add product", width='stretch'):
        st.session_state._pending_nav = "📦 Inventory"
        st.rerun()
    if qa3.button("✨ Ask copilot", width='stretch'):
        st.session_state._pending_nav = "✨ Chat Assistant"
        st.rerun()

    st.write("")
    section_title("📊", "Overview")
    kpis = analytics.get_kpi_summary()

    # Asymmetric layout: Revenue leads as a wide hero card with a real
    # sparkline; the other three KPIs sit in a tighter row beside it.
    hero_col, rest_col = st.columns([1.3, 1])

    trend_df = analytics.get_daily_sales_trend(7)
    spark_df = trend_df[["Date", "Revenue"]] if not trend_df.empty else None
    hero_revenue_card(
        hero_col, palette,
        utils.format_currency(kpis["revenue_last_30_days"]),
        get_revenue_trend_pct(),
        spark_df,
        label="Revenue (last 30 days)",
    )

    with rest_col:
        r1, r2, r3 = st.columns(3)
        kpi_card(r1, "Total products", utils.format_number(kpis["total_products"]))
        kpi_card(r2, "Inventory value", utils.format_currency(kpis["inventory_value"]), variant="accent")
        kpi_card(r3, "Low stock items", utils.format_number(kpis["low_stock_count"]),
                  variant="warning" if kpis["low_stock_count"] else "default")

    st.write("")
    left, right = st.columns([1.4, 1])

    with left:
        section_title("📈", "Sales trend", "Revenue across the last 60 days")
        trend = analytics.get_daily_sales_trend(60)
        if trend.empty:
            empty_state("📈", "No sales yet", "Record a sale to see your revenue trend build up here.")
        else:
            fig = px.area(trend, x="Date", y="Revenue", markers=False)
            fig.update_traces(line_color=palette["accent"], fillcolor="rgba(168,85,247,0.15)")
            st.plotly_chart(style_fig(fig, palette), width='stretch')

    with right:
        section_title("🏷️", "Category distribution", "Share of total stock")
        cat = analytics.get_category_revenue()
        if cat.empty:
            empty_state("🏷️", "No category data yet", "Categories appear here once products start selling.")
        else:
            fig = px.pie(cat, names="Category", values="Revenue", hole=0.55)
            fig.update_traces(textinfo="percent+label")
            st.plotly_chart(style_fig(fig, palette), width='stretch')

    st.write("")
    left2, right2 = st.columns(2)

    with left2:
        section_title("🏆", "Top selling products", "By units this month")
        top = analytics.get_top_selling_products(8)
        if top.empty:
            empty_state("🏆", "No top sellers yet", "Your best-selling products will be ranked here.")
        else:
            fig = px.bar(top, x="QuantitySold", y="ProductName", orientation="h",
                          color="Category", text="QuantitySold")
            fig.update_layout(yaxis=dict(autorange="reversed"), showlegend=False)
            st.plotly_chart(style_fig(fig, palette), width='stretch')

    with right2:
        section_title("🚨", "Low stock alerts")
        low = inventory.get_low_stock_products()
        if low.empty:
            st.success("Every product is sufficiently stocked.")
        else:
            for _, row in low.head(8).iterrows():
                st.markdown(f"""
                    <div class="alert-pill">
                        <b>{row['ProductName']}</b> — {row['CurrentStock']} left
                        <span style="color:{palette['text_secondary']};">
                        (reorder level: {row['ReorderLevel']})</span>
                    </div>
                """, unsafe_allow_html=True)

    st.write("")
    section_title("🧾", "Recent transactions", "Latest sales activity")
    history = sales.get_sales_history(limit=8)
    if history.empty:
        empty_state("🧾", "No transactions yet", "Sales you record will show up here, most recent first.")
    else:
        display = history[["ProductName", "Category", "QuantitySold", "LineTotal", "SaleDate"]].copy()
        display.columns = ["Product", "Category", "Quantity", "Revenue", "Date"]
        display["Revenue"] = display["Revenue"].apply(lambda v: utils.format_currency(v))
        st.dataframe(display, width='stretch', hide_index=True)


# ============================================================================
# PAGE: INVENTORY
# ============================================================================

def render_inventory_page(palette: dict):
    page_header("📦", "Inventory", "Browse, search, and manage your product catalog.")

    tab1, tab2, tab3 = st.tabs(["Browse & Search", "Add Product", "Manage Stock"])

    with tab1:
        _render_browse_tab(palette)
    with tab2:
        _render_add_tab()
    with tab3:
        _render_manage_tab()


def _render_browse_tab(palette: dict):
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

    # Quick status filter + sort -- a real way to answer "show me what
    # needs attention" without leaving the page or opening Business Insights.
    if not df.empty:
        df["_status"] = df.apply(lambda r: stock_status(r["CurrentStock"], r["ReorderLevel"]), axis=1)

    filt_col, sort_col, count_col = st.columns([2, 1.3, 1.7])
    status_filter = filt_col.radio(
        "Status", ["All", "In stock", "Low stock", "Out of stock"],
        horizontal=True, label_visibility="collapsed",
    )
    status_map = {"In stock": "in-stock", "Low stock": "low-stock", "Out of stock": "out-of-stock"}
    if status_filter != "All" and not df.empty:
        df = df[df["_status"] == status_map[status_filter]]

    sort_by = sort_col.selectbox(
        "Sort by", ["Name (A–Z)", "Stock (low to high)", "Stock (high to low)", "Price (low to high)", "Price (high to low)"],
        label_visibility="collapsed",
    )
    if not df.empty:
        if sort_by == "Name (A–Z)":
            df = df.sort_values("ProductName")
        elif sort_by == "Stock (low to high)":
            df = df.sort_values("CurrentStock")
        elif sort_by == "Stock (high to low)":
            df = df.sort_values("CurrentStock", ascending=False)
        elif sort_by == "Price (low to high)":
            df = df.sort_values("Price")
        elif sort_by == "Price (high to low)":
            df = df.sort_values("Price", ascending=False)

    category_count_text = ""
    if not df.empty:
        n_categories = df["Category"].nunique()
        category_count_text = f" across {n_categories} categor{'y' if n_categories == 1 else 'ies'}"
    count_col.markdown(
        f"<div style='text-align:right; padding-top:8px; color:{palette['text_secondary']}; font-size:13px;'>"
        f"{len(df)} product{'s' if len(df) != 1 else ''}{category_count_text}"
        f"</div>",
        unsafe_allow_html=True,
    )

    st.write("")

    if df.empty:
        empty_state("📦", "No products match these filters",
                     "Try clearing the search, category, or status filter.")
    else:
        cards_per_row = 3
        df = df.reset_index(drop=True)
        rows = [df.iloc[i:i + cards_per_row] for i in range(0, len(df), cards_per_row)]
        for row_df in rows:
            cols = st.columns(cards_per_row)
            for col, (_, item) in zip(cols, row_df.iterrows()):
                inventory_card(col, palette, item, item["_status"])

    st.write("")
    exp1, exp2 = st.columns(2)
    exp1.download_button("⬇️ Export CSV", utils.dataframe_to_csv_bytes(df.drop(columns=["_status"], errors="ignore")),
                          "products.csv", "text/csv", width='stretch')
    exp2.download_button("⬇️ Export Excel", utils.dataframe_to_excel_bytes(df.drop(columns=["_status"], errors="ignore"), "Products"),
                          "products.xlsx",
                          "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                          width='stretch')

    st.write("")
    st.markdown("**Remove a product**")
    del_col1, del_col2 = st.columns([3, 1])
    if not df.empty:
        options = {f"{r['ProductName']} (ID {r['ProductID']})": r["ProductID"] for _, r in df.iterrows()}
        choice = del_col1.selectbox("Select product to remove", list(options.keys()), label_visibility="collapsed")
        if del_col2.button("Remove", width='stretch'):
            inventory.delete_product(options[choice])
            st.toast(f"Removed '{choice}'. Sales history is kept.", icon="🗑️")
            st.rerun()


def _render_add_tab():
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

        submitted = st.form_submit_button("Add product", type="primary")
        if submitted:
            try:
                inventory.add_product(name, cat, price, int(stock), int(reorder),
                                       supplier_options[supplier_name])
                st.toast(f"Added '{name}' to inventory.", icon="✅")
                st.rerun()
            except ValueError as e:
                st.error(str(e))

    with st.expander("Add a new supplier instead"):
        with st.form("add_supplier_form", clear_on_submit=True):
            sname = st.text_input("Supplier Name *")
            sphone = st.text_input("Contact Number")
            semail = st.text_input("Email")
            if st.form_submit_button("Add supplier"):
                try:
                    inventory.add_supplier(sname, sphone, semail)
                    st.toast(f"Added supplier '{sname}'.", icon="✅")
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))


def _render_manage_tab():
    st.markdown("Adjust stock levels or edit product details.")
    products_df = inventory.get_all_products()
    if products_df.empty:
        empty_state("📦", "No products yet", "Add one in the 'Add Product' tab to get started.")
        return

    options = {f"{r['ProductName']} (Stock: {r['CurrentStock']})": r["ProductID"]
               for _, r in products_df.iterrows()}
    choice = st.selectbox("Select Product", list(options.keys()))
    pid = options[choice]
    product = inventory.get_product_by_id(pid)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Current Stock", product["CurrentStock"])
        delta = st.number_input("Adjust stock by (+ / -)", value=0, step=1, key="stock_delta")
        if st.button("Apply stock adjustment", type="primary"):
            try:
                new_stock = inventory.adjust_stock(pid, int(delta))
                st.toast(f"Stock updated to {new_stock}.", icon="📦")
                st.rerun()
            except ValueError as e:
                st.error(str(e))
    with c2:
        new_price = st.number_input("Price (₹)", value=float(product["Price"]), step=1.0, key="edit_price")
        if st.button("Update price"):
            inventory.update_product(pid, Price=new_price)
            st.toast("Price updated.", icon="💰")
            st.rerun()
    with c3:
        new_reorder = st.number_input("Reorder Level", value=int(product["ReorderLevel"]), step=1, key="edit_reorder")
        if st.button("Update reorder level"):
            inventory.update_product(pid, ReorderLevel=int(new_reorder))
            st.toast("Reorder level updated.", icon="🔔")
            st.rerun()


# ============================================================================
# PAGE: SALES
# ============================================================================

def render_sales_page(palette: dict):
    page_header("🧾", "Sales", "Record transactions and review your sales history.")

    _render_today_strip(palette)

    tab1, tab2 = st.tabs(["Record Sale", "Sales History"])
    with tab1:
        _render_record_tab()
    with tab2:
        _render_history_tab(palette)


def _render_today_strip(palette: dict):
    """A quick at-a-glance strip of today's activity -- answers 'how's
    today going so far' without digging into the history tab."""
    history = sales.get_all_sales_raw()
    if history.empty:
        return
    today = datetime.now().date()
    today_sales = history[history["SaleDate"].dt.date == today]
    if today_sales.empty:
        st.caption("No sales recorded today yet.")
        return

    n_sales = len(today_sales)
    n_units = int(today_sales["QuantitySold"].sum())
    revenue = today_sales["Revenue"].sum()
    st.markdown(
        f"<div style='display:flex; gap:24px; padding:10px 16px; margin-bottom:18px; "
        f"background:{palette['surface2']}; border-radius:10px; font-size:13px; color:{palette['text_secondary']};'>"
        f"<span><b style='color:{palette['text']};'>{n_sales}</b> sale{'s' if n_sales != 1 else ''} today</span>"
        f"<span><b style='color:{palette['text']};'>{n_units}</b> units sold</span>"
        f"<span><b style='color:{palette['text']};'>{utils.format_currency(revenue)}</b> revenue</span>"
        f"</div>",
        unsafe_allow_html=True,
    )


def _render_record_tab():
    products_df = inventory.get_all_products()
    if products_df.empty:
        empty_state("🧾", "No products to sell", "Add a product in the Inventory page first.")
        return

    options = {f"{r['ProductName']} — ₹{r['Price']} (Stock: {r['CurrentStock']})": r["ProductID"]
               for _, r in products_df.iterrows()}
    with st.form("record_sale_form", clear_on_submit=True):
        choice = st.selectbox("Product", list(options.keys()))
        qty = st.number_input("Quantity Sold", min_value=1, step=1, value=1)
        sale_date = st.date_input("Sale Date", value=datetime.now())
        submitted = st.form_submit_button("Record sale", type="primary")

        if submitted:
            pid = options[choice]
            try:
                sale_id = sales.record_sale(pid, int(qty), sale_date.strftime("%Y-%m-%d"))
                st.toast(f"Sale #{sale_id} recorded. Stock automatically reduced.", icon="✅")
                st.rerun()
            except ValueError as e:
                st.error(str(e))


def _render_history_tab(palette: dict):
    history = sales.get_sales_history(limit=300)
    if history.empty:
        empty_state("🧾", "No sales recorded yet", "Sales you record will appear here.")
        return

    c1, c2, c3 = st.columns([1.3, 1.3, 1.4])
    cat_filter = c1.selectbox("Filter by category", ["All"] + sorted(history["Category"].unique().tolist()))
    date_range = c2.selectbox("Date range", ["All time", "Last 7 days", "Last 30 days", "Last 90 days"])

    display_df = history if cat_filter == "All" else history[history["Category"] == cat_filter]

    if date_range != "All time":
        days = {"Last 7 days": 7, "Last 30 days": 30, "Last 90 days": 90}[date_range]
        cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        display_df = display_df[display_df["SaleDate"] >= cutoff]

    n_results = len(display_df)
    total_rev = display_df["LineTotal"].sum() if not display_df.empty else 0
    c3.markdown(
        f"<div style='padding-top:28px; text-align:right; font-size:13px; color:{palette['text_secondary']};'>"
        f"{n_results} sale{'s' if n_results != 1 else ''} · {utils.format_currency(total_rev)}</div>",
        unsafe_allow_html=True,
    )

    if display_df.empty:
        empty_state("🔍", "No sales match these filters", "Try a wider date range or a different category.")
        return

    st.dataframe(display_df, width='stretch', hide_index=True)

    exp1, exp2 = st.columns(2)
    exp1.download_button("⬇️ Export CSV", utils.dataframe_to_csv_bytes(display_df),
                          "sales_history.csv", "text/csv", width='stretch')
    exp2.download_button("⬇️ Export Excel", utils.dataframe_to_excel_bytes(display_df, "Sales"),
                          "sales_history.xlsx",
                          "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                          width='stretch')

    st.write("")
    st.markdown("**Undo a sale** (restocks the item)")
    d1, d2 = st.columns([3, 1])
    sale_options = {f"#{r['SaleID']} — {r['ProductName']} x{r['QuantitySold']} ({r['SaleDate']})": r["SaleID"]
                     for _, r in display_df.head(50).iterrows()}
    sale_choice = d1.selectbox("Select sale", list(sale_options.keys()), label_visibility="collapsed")
    if d2.button("Undo sale", width='stretch'):
        sales.delete_sale(sale_options[sale_choice], restock=True)
        st.toast("Sale removed and stock restored.", icon="↩️")
        st.rerun()


# ============================================================================
# PAGE: SUPPLIERS
# ============================================================================

def render_suppliers_page(palette: dict):
    page_header("🚚", "Suppliers", "Who you buy from, and how many products they cover.")

    suppliers_df = inventory.get_all_suppliers()
    counts_df = analytics.get_supplier_product_counts()
    count_lookup = dict(zip(counts_df["SupplierName"], counts_df["ProductCount"]))

    if suppliers_df.empty:
        empty_state("🚚", "No suppliers yet", "Add your first supplier below.")
    else:
        top_supplier = counts_df.iloc[0] if not counts_df.empty and counts_df["ProductCount"].max() > 0 else None
        if top_supplier is not None:
            st.markdown(
                f"<div style='padding:10px 16px; margin-bottom:18px; background:{palette['surface2']}; "
                f"border-radius:10px; font-size:13px; color:{palette['text_secondary']};'>"
                f"🏆 <b style='color:{palette['text']};'>{top_supplier['SupplierName']}</b> supplies the most "
                f"products — <b style='color:{palette['text']};'>{int(top_supplier['ProductCount'])}</b> active items."
                f"</div>",
                unsafe_allow_html=True,
            )

        cards_per_row = 3
        rows = [suppliers_df.iloc[i:i + cards_per_row] for i in range(0, len(suppliers_df), cards_per_row)]
        for row_df in rows:
            cols = st.columns(cards_per_row)
            for col, (_, row) in zip(cols, row_df.iterrows()):
                supplier_card(col, palette, row, int(count_lookup.get(row["SupplierName"], 0)))

    st.write("")
    with st.expander("➕ Add a new supplier"):
        with st.form("supplier_page_add_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            sname = c1.text_input("Supplier Name *")
            sphone = c2.text_input("Contact Number")
            semail = c3.text_input("Email")
            if st.form_submit_button("Add supplier", type="primary"):
                try:
                    inventory.add_supplier(sname, sphone, semail)
                    st.toast(f"Added supplier '{sname}'.", icon="✅")
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))


# ============================================================================
# PAGE: BUSINESS INSIGHTS (ANALYTICS)
# ============================================================================

def render_analytics_page(palette: dict):
    page_header("🔍", "Business Insights", "Answers to the questions that matter most for running the store.")

    tabs = st.tabs([
        "🏃 Fastest sellers", "🔔 Reorder list", "🏷️ Category revenue",
        "🧊 Stale stock", "💰 Inventory value", "🚚 Top suppliers",
    ])

    with tabs[0]:
        _fastest_sellers(palette)
    with tabs[1]:
        _reorder_list()
    with tabs[2]:
        _category_revenue(palette)
    with tabs[3]:
        _stale_stock()
    with tabs[4]:
        _inventory_value(palette)
    with tabs[5]:
        _top_suppliers(palette)


def _fastest_sellers(palette):
    st.caption("Which products sell the fastest? Ranked by average units sold per day over the last 30 days.")
    velocity = analytics.get_sales_velocity()
    if velocity.empty:
        empty_state("🏃", "Not enough recent sales data", "Record a few sales to see velocity rankings here.")
    else:
        fig = px.bar(velocity.head(10), x="AvgUnitsPerDay", y="ProductName",
                      orientation="h", color="Category", text="AvgUnitsPerDay")
        fig.update_layout(yaxis=dict(autorange="reversed"))
        st.plotly_chart(style_fig(fig, palette), width='stretch')
        st.dataframe(velocity, width='stretch', hide_index=True)


def _reorder_list():
    st.caption("Which products need reordering? Anything at or below its reorder level.")
    reorder_df = analytics.get_reorder_list()
    if reorder_df.empty:
        st.success("No products currently need reordering.")
    else:
        st.dataframe(reorder_df, width='stretch', hide_index=True)
        st.download_button("⬇️ Export Reorder List (CSV)",
                            utils.dataframe_to_csv_bytes(reorder_df),
                            "reorder_list.csv", "text/csv")


def _category_revenue(palette):
    st.caption("Which categories generate the highest revenue?")
    cat = analytics.get_category_revenue()
    if cat.empty:
        empty_state("🏷️", "No sales recorded yet", "Category revenue will rank here once sales come in.")
    else:
        fig = px.bar(cat, x="Category", y="Revenue", color="Category", text="Revenue")
        st.plotly_chart(style_fig(fig, palette), width='stretch')
        st.dataframe(cat, width='stretch', hide_index=True)


def _stale_stock():
    st.caption("Which products haven't sold in the last 30 days? Candidates for a promotion or discontinuation.")
    stale = analytics.get_stale_products(30)
    if stale.empty:
        st.success("Every product has sold within the last 30 days.")
    else:
        st.dataframe(stale, width='stretch', hide_index=True)
        st.caption(f"{len(stale)} product(s) flagged as dead stock.")


def _inventory_value(palette):
    st.caption("What is the current total inventory value?")
    value = inventory.get_inventory_value()
    st.markdown(f"### {utils.format_currency(value)}")
    by_cat = analytics.get_inventory_value_by_category()
    if not by_cat.empty:
        fig = px.pie(by_cat, names="Category", values="InventoryValue", hole=0.5)
        st.plotly_chart(style_fig(fig, palette), width='stretch')
        st.dataframe(by_cat, width='stretch', hide_index=True)


def _top_suppliers(palette):
    st.caption("Which supplier provides the most products?")
    sup = analytics.get_supplier_product_counts()
    if sup.empty or sup["ProductCount"].sum() == 0:
        empty_state("🚚", "No suppliers linked yet", "Add suppliers in the Inventory page to see this ranking.")
        return
    fig = px.bar(sup, x="SupplierName", y="ProductCount", color="SupplierName")
    fig.update_layout(showlegend=False, xaxis_tickangle=-30)
    st.plotly_chart(style_fig(fig, palette), width='stretch')
    st.dataframe(sup, width='stretch', hide_index=True)


# ============================================================================
# PAGE: AI FEATURES
# ============================================================================

def render_ai_page(palette: dict):
    n_risky = len(analytics.predict_stockouts_next_week())
    subtitle = (f"{n_risky} product{'s' if n_risky != 1 else ''} at risk of running out within 7 days."
                if n_risky else "Nothing is currently at risk of running out within 7 days.")
    page_header("🤖", "AI-Powered Features", subtitle)

    tab1, tab2, tab3 = st.tabs(["Demand Forecast", "Reorder Recommendations", "Stockout Predictions"])
    with tab1:
        _demand_forecast_tab(palette)
    with tab2:
        _reorder_recs_tab()
    with tab3:
        _stockout_tab(palette)


def _confidence_badge(palette, confidence: str) -> str:
    color_map = {"high": palette["success"], "medium": palette["warning"],
                 "low": palette["danger"], "no_data": palette["text_secondary"]}
    color = color_map.get(confidence, palette["text_secondary"])
    bg = f"{color}1F"
    return (f'<span class="status-badge" style="color:{color}; background:{bg};">'
            f'<span class="status-dot" style="background:{color};"></span>{confidence.replace("_", " ").title()}</span>')


def _demand_forecast_tab(palette):
    products_df = inventory.get_all_products()
    if products_df.empty:
        empty_state("📈", "No products to forecast", "Add products in the Inventory page first.")
        return

    options = {r["ProductName"]: r["ProductID"] for _, r in products_df.iterrows()}
    c1, c2 = st.columns([2, 1])
    choice = c1.selectbox("Select a product", list(options.keys()))
    days_ahead = c2.slider("Forecast horizon (days)", 3, 30, 7)

    pid = options[choice]
    forecast = analytics.forecast_demand(pid, days_ahead)

    m1, m2, m3 = st.columns(3)
    m1.metric("Forecasted Demand", f"{forecast['forecast_units']} units")
    m2.metric("Avg Daily Rate", f"{forecast['avg_daily_rate']} units/day")
    with m3:
        st.markdown(f"<div style='font-size:13px; color:{palette['text_secondary']}; margin-bottom:4px;'>Confidence</div>"
                     f"{_confidence_badge(palette, forecast['confidence'])}", unsafe_allow_html=True)

    st.caption("Forecast uses a linear regression trend fitted on the product's daily sales history "
                "(scikit-learn `LinearRegression`). More history → higher confidence.")

    prod_sales = sales.get_all_sales_raw()
    prod_sales = prod_sales[prod_sales["ProductID"] == pid]
    if not prod_sales.empty:
        daily = prod_sales.groupby(prod_sales["SaleDate"].dt.date)["QuantitySold"].sum().reset_index()
        daily.columns = ["Date", "QuantitySold"]
        fig = px.line(daily, x="Date", y="QuantitySold", markers=True)
        fig.update_traces(line_color=palette["accent"])
        st.plotly_chart(style_fig(fig, palette), width='stretch')
    else:
        empty_state("📈", "No sales history for this product", "Forecasts improve as sales history builds up.")


def _reorder_recs_tab():
    st.markdown("AI-generated reorder suggestions based on forecasted demand vs. current stock.")
    days_ahead2 = st.slider("Planning horizon (days)", 3, 30, 7, key="reorder_horizon")
    recs = analytics.get_reorder_recommendations(days_ahead2)
    if recs.empty:
        empty_state("🔔", "No products in inventory yet", "Recommendations will appear once you've added products.")
        return

    def highlight_runout(val):
        return "background-color: rgba(239,68,68,0.15)" if val else ""
    st.dataframe(
        recs.style.map(highlight_runout, subset=["WillRunOut"]),
        width='stretch', hide_index=True,
    )
    st.download_button("⬇️ Export Recommendations (Excel)",
                        utils.dataframe_to_excel_bytes(recs, "Reorder Recs"),
                        "reorder_recommendations.xlsx",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


def _stockout_tab(palette):
    st.markdown("Products predicted to run out of stock **within the next 7 days**, based on demand forecasting.")
    risky = analytics.predict_stockouts_next_week()
    if risky.empty:
        st.success("No products are predicted to run out within 7 days.")
        return
    for _, row in risky.iterrows():
        st.markdown(f"""
            <div class="alert-pill">
                🔥 <b>{row['ProductName']}</b> — projected stock in 7 days:
                <b>{row['ProjectedStockAfter']}</b> units
                (currently {row['CurrentStock']}, forecast demand {row['ForecastDemand_NextNDays']})
            </div>
        """, unsafe_allow_html=True)


# ============================================================================
# PAGE: CHAT ASSISTANT
# ============================================================================

SUGGESTIONS = [
    "Which products are low in stock?",
    "What are the top-selling products?",
    "How much inventory value do we currently have?",
    "Which products should be reordered?",
]


def render_chat_page(palette: dict):
    header_col, clear_col = st.columns([5, 1])
    with header_col:
        st.markdown(
            '<div class="section-title"><span class="ai-badge">✨</span>Inventory copilot</div>',
            unsafe_allow_html=True,
        )
        st.caption("Ask plain-English questions about your stock, reorders, and sales.")
    with clear_col:
        st.write("")
        if st.button("Clear chat", width='stretch') and st.session_state.chat_history:
            st.session_state.chat_history = []
            st.rerun()

    if not st.session_state.chat_history:
        st.markdown(f"""
            <div class="chat-bot">
                Hi! I can answer questions about your stock levels, reorder
                needs, top sellers, and sales — try one of the suggestions
                below or type your own question.
            </div>
        """, unsafe_allow_html=True)

    cols = st.columns(len(SUGGESTIONS))
    for col, s in zip(cols, SUGGESTIONS):
        if col.button(s, width='stretch'):
            st.session_state.chat_history.append(("user", s))
            st.session_state.chat_history.append(("bot", utils.answer_chat_query(s)))

    for role, msg in st.session_state.chat_history:
        css_class = "chat-user" if role == "user" else "chat-bot"
        st.markdown(f'<div class="{css_class}">{msg}</div>', unsafe_allow_html=True)

    user_input = st.chat_input("Ask about your inventory...")
    if user_input:
        st.session_state.chat_history.append(("user", user_input))
        answer = utils.answer_chat_query(user_input)
        st.session_state.chat_history.append(("bot", answer))
        st.rerun()


# ============================================================================
# PAGE: SETTINGS
# ============================================================================

def render_settings_page(palette: dict):
    page_header("⚙️", "Settings", "Account, appearance, and data management.")

    tab1, tab2, tab3 = st.tabs(["Account", "Appearance", "Data"])
    with tab1:
        _account_tab()
    with tab2:
        _appearance_tab(palette)
    with tab3:
        _data_tab()


def _account_tab():
    st.markdown(f"**Signed in as** {st.session_state.username}")
    st.markdown(f"**Role** {st.session_state.get('role', 'staff').title()}")

    st.write("")
    st.markdown("##### Change password")
    with st.form("change_password_form", clear_on_submit=True):
        current_pw = st.text_input("Current password", type="password")
        new_pw = st.text_input("New password", type="password")
        confirm_pw = st.text_input("Confirm new password", type="password")
        submitted = st.form_submit_button("Update password", type="primary")

        if submitted:
            if not current_pw or not new_pw:
                st.error("Please fill in all fields.")
            elif new_pw != confirm_pw:
                st.error("New password and confirmation don't match.")
            elif len(new_pw) < 6:
                st.error("New password should be at least 6 characters.")
            else:
                success = database.change_password(st.session_state.username, current_pw, new_pw)
                if success:
                    st.toast("Password updated.", icon="🔒")
                else:
                    st.error("Current password is incorrect.")


def _appearance_tab(palette):
    st.markdown("##### Theme")
    st.toggle("🌙 Dark mode", key="dark_mode")
    st.caption("Switches the whole app between the dark and light palette defined in theme.py.")

    st.write("")
    st.markdown("##### Color reference")
    st.caption("These are the active palette tokens. Edit them in `theme.py` to re-skin the app.")
    swatch_cols = st.columns(6)
    swatches = [
        ("Primary", palette["primary"]), ("Accent", palette["accent"]),
        ("Success", palette["success"]), ("Warning", palette["warning"]),
        ("Danger", palette["danger"]), ("Info", palette["info"]),
    ]
    for col, (name, color) in zip(swatch_cols, swatches):
        col.markdown(
            f"<div style='height:48px; border-radius:10px; background:{color}; margin-bottom:6px;'></div>"
            f"<div style='font-size:12px; color:{palette['text_secondary']};'>{name}</div>"
            f"<div style='font-size:11px; color:{palette['text_secondary']};'>{color}</div>",
            unsafe_allow_html=True,
        )


def _data_tab():
    st.markdown("##### Snapshot")
    products = inventory.get_all_products(include_inactive=True)
    suppliers = inventory.get_all_suppliers()
    all_sales = sales.get_all_sales_raw()

    c1, c2, c3 = st.columns(3)
    c1.metric("Products (incl. discontinued)", len(products))
    c2.metric("Suppliers", len(suppliers))
    c3.metric("Sales records", len(all_sales))

    st.write("")
    st.markdown("##### Reset sample data")
    st.caption(
        "Wipes every product, supplier, sale, and user, then regenerates "
        "the demo catalog with 90 days of simulated sales. This cannot be undone."
    )
    confirm = st.checkbox("I understand this will permanently delete all current data.")
    if st.button("Reset sample data", type="primary", disabled=not confirm):
        with st.spinner("Regenerating sample data..."):
            seed_data.seed_all(verbose=False)
        st.toast("Sample data reset.", icon="🔄")
        st.rerun()

# ---------------------------------------------------------------------------
# LOGIN PAGE
# ---------------------------------------------------------------------------

def render_login():
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown(f"""
            <div style="text-align:center; margin-top: 60px; margin-bottom: 20px;">
                <div style="background: {PALETTE['primary']};
                            width: 56px; height: 56px; border-radius: 14px; display: inline-flex;
                            align-items: center; justify-content: center; font-size: 24px;">📦</div>
                <h1 style="margin-top: 14px; margin-bottom:0;">StockHub</h1>
                <p style="color:{PALETTE['text_secondary']}; margin-top:4px;">Inventory Management System</p>
            </div>
        """, unsafe_allow_html=True)

        with st.form("login_form"):
            username = st.text_input("Username", placeholder="admin")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            submitted = st.form_submit_button("Log in", width='stretch', type="primary")

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
# SIDEBAR
# ---------------------------------------------------------------------------

NAV_PAGES = [
    "📊 Dashboard", "📦 Inventory", "🧾 Sales", "🚚 Suppliers",
    "🔍 Business Insights", "🤖 AI Features", "✨ Chat Assistant", "⚙️ Settings",
]


def render_sidebar():
    with st.sidebar:
        st.markdown("""
            <div class="brand-bar">
                <div class="brand-mark">📦</div>
                <div>
                    <div class="brand-title">StockHub</div>
                    <div class="brand-sub">Inventory Management</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown(f"Signed in as **{st.session_state.username}**")

        # Navigation override pattern: quick-action buttons elsewhere in the
        # app can't write to "nav_radio" directly once this widget exists
        # for the run (Streamlit forbids mutating a widget's own key after
        # it's instantiated). Instead they set "_pending_nav" and rerun;
        # here, BEFORE the radio widget is created, we apply that pending
        # value to the widget's key and clear the flag. This must happen in
        # this exact order -- apply-then-clear, before instantiation -- or
        # the override either throws or silently fails to stick.
        if "nav_radio" not in st.session_state:
            st.session_state.nav_radio = NAV_PAGES[0]
        if st.session_state._pending_nav is not None:
            st.session_state.nav_radio = st.session_state._pending_nav
            st.session_state._pending_nav = None

        page = st.radio(
            "Navigate", NAV_PAGES, key="nav_radio", label_visibility="collapsed",
        )

        st.write("")
        if st.button("Log out", width='stretch'):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.rerun()

        return page


# ---------------------------------------------------------------------------
# ROUTING
# ---------------------------------------------------------------------------

PAGE_RENDERERS = {
    "📊 Dashboard": render_dashboard,
    "📦 Inventory": render_inventory_page,
    "🧾 Sales": render_sales_page,
    "🚚 Suppliers": render_suppliers_page,
    "🔍 Business Insights": render_analytics_page,
    "🤖 AI Features": render_ai_page,
    "✨ Chat Assistant": render_chat_page,
    "⚙️ Settings": render_settings_page,
}


def main():
    if not st.session_state.logged_in:
        render_login()
        return

    page = render_sidebar()
    renderer = PAGE_RENDERERS.get(page)
    if renderer:
        renderer(PALETTE)


if __name__ == "__main__":
    main()
