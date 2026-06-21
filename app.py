"""
app.py
------
Entry point: page config, session state, login gate, sidebar navigation,
and routing to the page modules in pages_/.

This file is intentionally thin. Theming lives in theme.py, shared UI
pieces live in components.py, and each page's logic lives in its own
module under pages_/ -- app.py just wires them together. That split means
a change to (say) the KPI card design happens in one place and is
consistent everywhere, instead of being copy-pasted across every page.

Run with:  streamlit run app.py
"""

import streamlit as st

import database
import seed_data
from theme import load_theme

from pages_ import (
    dashboard, inventory_page, sales_page, analytics_page,
    ai_page, chat_page, suppliers_page, settings_page,
)


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
    "nav_override": None,
}
for key, default in _DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = default

PALETTE = load_theme(st.session_state.dark_mode)


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

        # If a page's quick-action button asked to jump elsewhere (e.g. the
        # dashboard's "Record a sale" button), honor that as the radio's
        # starting index for this run, then clear it so it doesn't stick
        # on every future visit to the sidebar.
        default_index = 0
        if st.session_state.nav_override in NAV_PAGES:
            default_index = NAV_PAGES.index(st.session_state.nav_override)
        st.session_state.nav_override = None

        page = st.radio(
            "Navigate", NAV_PAGES, index=default_index, label_visibility="collapsed",
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
    "📊 Dashboard": dashboard.render,
    "📦 Inventory": inventory_page.render,
    "🧾 Sales": sales_page.render,
    "🚚 Suppliers": suppliers_page.render,
    "🔍 Business Insights": analytics_page.render,
    "🤖 AI Features": ai_page.render,
    "✨ Chat Assistant": chat_page.render,
    "⚙️ Settings": settings_page.render,
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
