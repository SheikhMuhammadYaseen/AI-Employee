"""Financials — Accounting dashboard."""

import sys
from pathlib import Path
from datetime import datetime, timedelta

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils.path_setup import VAULT_PATH
from utils.theme import inject_custom_css, kpi_card, render_sidebar_branding
from utils.formatters import format_currency
from utils.icons import lucide, icon_text

st.set_page_config(page_title="Financials", page_icon="💰", layout="wide")
inject_custom_css()
render_sidebar_branding()

# --- src/ imports ---
try:
    from src.mcp.tools.odoo_reports import get_financial_summary
except ImportError:
    get_financial_summary = None

try:
    from src.mcp.tools.odoo_invoice import list_invoices
except ImportError:
    list_invoices = None

try:
    from src.mcp.tools.odoo_payment import list_payments
except ImportError:
    list_payments = None

st.markdown(
    icon_text("dollar-sign", "Financials", 30, "success", "h1")
    .replace("<svg", "<svg style='position:relative; top:-3px;'"),
    unsafe_allow_html=True
)

# --- Date Range ---
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("Start Date", value=datetime.now() - timedelta(days=30))
with col2:
    end_date = st.date_input("End Date", value=datetime.now())

# --- Load Financial Data ---
@st.cache_data(ttl=300, show_spinner=False)
def load_financial_data(start, end):
    if get_financial_summary is None:
        return None
    try:
        return get_financial_summary(str(start), str(end))
    except Exception:
        return {"status": "error"}


financial = load_financial_data(start_date, end_date)

# --- Demo data fallback when Odoo is not connected ---
DEMO_FINANCIAL = {
    "revenue": 14200.00,
    "expenses": 3450.00,
    "net_cash_flow": 10750.00,
    "outstanding_receivables": 7200.00,
    "overdue_count": 1,
    "overdue_amount": 2100.00,
}

DEMO_INVOICES = [
    {"Invoice #": "INV-2026-0338", "Client": "Acme Corp", "Amount": "$4,500.00", "Date": "Feb 14, 2026", "Status": "\u25cf Paid"},
    {"Invoice #": "INV-2026-0339", "Client": "TechVentures", "Amount": "$3,200.00", "Date": "Feb 15, 2026", "Status": "\u25cf Paid"},
    {"Invoice #": "INV-2026-0340", "Client": "DesignStudio", "Amount": "$6,500.00", "Date": "Feb 16, 2026", "Status": "\u25cb Pending"},
    {"Invoice #": "INV-2026-0341", "Client": "OldClient Corp", "Amount": "$2,100.00", "Date": "Feb 01, 2026", "Status": "\u25cf Overdue"},
]

DEMO_PAYMENTS = [
    {"Payment #": "PAY-2026-0112", "From": "Acme Corp", "Amount": "$4,500.00", "Date": "Feb 14, 2026", "Method": "Bank Transfer"},
    {"Payment #": "PAY-2026-0113", "From": "TechVentures", "Amount": "$3,200.00", "Date": "Feb 15, 2026", "Method": "Wire Transfer"},
    {"Payment #": "PAY-2026-0114", "From": "CloudHost", "Amount": "$249.99", "Date": "Feb 16, 2026", "Method": "Credit Card"},
]

DEMO_OVERDUE = [
    {"Invoice #": "INV-2026-0341", "Client": "OldClient Corp", "Amount": "$2,100.00", "Due Date": "Feb 01, 2026", "Days Overdue": 15},
]

use_demo = (
    not financial
    or financial.get("status") == "error"
    or financial.get("revenue", 0) == 0
)
fin = DEMO_FINANCIAL if use_demo else financial

revenue = fin.get("revenue", 0)
expenses = fin.get("expenses", 0)
net_cash = fin.get("net_cash_flow", revenue - expenses)
receivables = fin.get("outstanding_receivables", 0)

# --- KPI Row ---
st.subheader("Financial Overview")

if use_demo:
    st.caption("Showing demo data — connect Odoo for live numbers")

cols = st.columns(4)
cols[0].markdown(kpi_card("Revenue", format_currency(revenue), lucide("banknote", 28, "success")), unsafe_allow_html=True)
cols[1].markdown(kpi_card("Expenses", format_currency(expenses), lucide("trending-up", 28, "danger")), unsafe_allow_html=True)
cols[2].markdown(kpi_card("Net Cash Flow", format_currency(net_cash), lucide("bar-chart-3", 28, "primary")), unsafe_allow_html=True)
cols[3].markdown(kpi_card("Receivables", format_currency(receivables), lucide("clipboard-list", 28, "warning")), unsafe_allow_html=True)

st.divider()

# --- Revenue vs Expenses Chart ---
st.subheader("Revenue vs Expenses")

weeks = ["Week 1", "Week 2", "Week 3", "Week 4"]
rev_data = [8500, 11800, 12400, revenue]
exp_data = [2800, 3200, 3100, expenses]

fig = go.Figure()
fig.add_trace(go.Bar(name="Revenue", x=weeks, y=rev_data, marker_color="#00c853"))
fig.add_trace(go.Bar(name="Expenses", x=weeks, y=exp_data, marker_color="#ff5252"))
fig.update_layout(
    barmode="group",
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    height=350,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
)
st.plotly_chart(fig, use_container_width=True)

# --- Monthly Trend Line ---
st.subheader("Monthly Trend")

months = ["Sep", "Oct", "Nov", "Dec", "Jan", "Feb"]
monthly_rev = [32000, 35500, 38200, 41000, 45200, 47000]
monthly_exp = [12000, 11800, 13500, 12900, 13200, 13800]
monthly_net = [r - e for r, e in zip(monthly_rev, monthly_exp)]

fig2 = go.Figure()
fig2.add_trace(go.Scatter(name="Revenue", x=months, y=monthly_rev, mode="lines+markers", line=dict(color="#00c853", width=2)))
fig2.add_trace(go.Scatter(name="Expenses", x=months, y=monthly_exp, mode="lines+markers", line=dict(color="#ff5252", width=2)))
fig2.add_trace(go.Scatter(name="Net Profit", x=months, y=monthly_net, mode="lines+markers", line=dict(color="#00d4ff", width=2, dash="dot")))
fig2.update_layout(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    height=300,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
)
st.plotly_chart(fig2, use_container_width=True)

st.divider()

# --- Tabbed Detail Views ---
st.subheader("Details")
tab_inv, tab_pay, tab_overdue = st.tabs(["Invoices", "Payments", "Overdue"])

with tab_inv:
    inv_data = None
    if list_invoices and not use_demo:
        try:
            result = list_invoices()
            if isinstance(result, list) and result:
                inv_data = result
            elif isinstance(result, dict) and result.get("invoices"):
                inv_data = result["invoices"]
        except Exception:
            pass

    if inv_data:
        df = pd.DataFrame(inv_data)
    else:
        df = pd.DataFrame(DEMO_INVOICES)
    st.dataframe(df, use_container_width=True, hide_index=True)

with tab_pay:
    pay_data = None
    if list_payments and not use_demo:
        try:
            result = list_payments()
            if isinstance(result, list) and result:
                pay_data = result
            elif isinstance(result, dict) and result.get("payments"):
                pay_data = result["payments"]
        except Exception:
            pass

    if pay_data:
        df = pd.DataFrame(pay_data)
    else:
        df = pd.DataFrame(DEMO_PAYMENTS)
    st.dataframe(df, use_container_width=True, hide_index=True)

with tab_overdue:
    if not use_demo and financial and financial.get("overdue_invoices"):
        overdue = financial["overdue_invoices"]
        if isinstance(overdue, list):
            df = pd.DataFrame(overdue)
        else:
            df = pd.DataFrame([{
                "Overdue Invoices": financial.get("overdue_count", 0),
                "Total Amount": format_currency(financial.get("overdue_amount", 0)),
            }])
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        df = pd.DataFrame(DEMO_OVERDUE)
        st.dataframe(df, use_container_width=True, hide_index=True)
