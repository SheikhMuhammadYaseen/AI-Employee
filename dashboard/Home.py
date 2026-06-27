"""AI Employee Dashboard — Home / Overview page."""

import streamlit as st
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

# Path setup must come first
from utils.path_setup import PROJECT_ROOT, VAULT_PATH

from utils.theme import inject_custom_css, kpi_card, status_badge, pipeline_flow_html, render_sidebar_branding, auto_refresh_sidebar
from utils.formatters import format_timestamp, time_ago, friendly_name
from utils.icons import lucide, icon_text, service_icon
from utils.vault_reader import (
    read_dashboard_md,
    count_items_by_folder,
    get_recent_activity,
    list_vault_items,
)

# --- src/ imports (graceful fallback) ---
try:
    from src.health.service_health import ServiceHealthTracker
except ImportError:
    ServiceHealthTracker = None

# --- Page Config ---
st.set_page_config(
    page_title="AI Employee Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_custom_css()
render_sidebar_branding()

# --- Sidebar (logo moved to bottom) ---

# --- Data Loading ---
@st.cache_data(ttl=300)
def load_dashboard_data():
    dashboard = read_dashboard_md(VAULT_PATH)
    counts = count_items_by_folder(VAULT_PATH)
    activity = get_recent_activity(VAULT_PATH)
    return dashboard, counts, activity


@st.cache_data(ttl=30)
def load_health_data():
    if ServiceHealthTracker is None:
        return {}
    try:
        tracker = ServiceHealthTracker(str(VAULT_PATH))
        return tracker.get_all_health()
    except Exception:
        return {}


dashboard, counts, activity = load_dashboard_data()
health = load_health_data()

# Compute service summary
SERVICES = ["odoo", "gmail", "linkedin", "mastodon", "facebook", "instagram", "x_twitter"]
services_ok = sum(
    1 for s in SERVICES
    if health.get(s, {}).get("status") == "operational"
)

# Demo fallback detection
_total_vault = sum(counts.values())
_is_demo_mode = _total_vault == 0 and not health

# Demo service health for showcase
DEMO_HEALTH = {
    "odoo": {"status": "operational", "last_ok": "2026-02-17T14:30:00Z"},
    "gmail": {"status": "operational", "last_ok": "2026-02-17T14:25:00Z"},
    "linkedin": {"status": "operational", "last_ok": "2026-02-17T13:00:00Z"},
    "mastodon": {"status": "operational", "last_ok": "2026-02-17T13:15:00Z"},
    "facebook": {"status": "operational", "last_ok": "2026-02-17T12:00:00Z"},
    "instagram": {"status": "degraded", "last_ok": "2026-02-16T18:00:00Z", "error_count": 2},
    "x_twitter": {"status": "unavailable", "last_ok": "2026-02-15T10:00:00Z", "error_count": 6},
}

if _is_demo_mode:
    health = DEMO_HEALTH
    services_ok = sum(1 for s in SERVICES if health.get(s, {}).get("status") == "operational")

# --- Header ---
st.title("Dashboard Overview")
if _is_demo_mode:
    st.caption("Demo data — connect services and start watchers for live data")
else:
    st.caption(f"Last updated: {format_timestamp(str(dashboard.get('last_updated', '—')))}")

# --- KPI Row ---
cols = st.columns(4)
_pending = dashboard.get("items_pending", 0) or (5 if _is_demo_mode else 0)
_processed = dashboard.get("items_processed", 0) or (47 if _is_demo_mode else 0)
_approvals = dashboard.get("items_awaiting_approval", 0) or (3 if _is_demo_mode else 0)
kpis = [
    ("Pending Items", _pending, lucide("inbox", 28, "primary")),
    ("Processed Items", _processed, lucide("check-circle", 28, "success")),
    ("Pending Approvals", _approvals, lucide("hourglass", 28, "warning")),
    ("Services Online", f"{services_ok}/{len(SERVICES)}", lucide("circle-check", 28, "success")),
]
for col, (label, value, icon) in zip(cols, kpis):
    col.markdown(kpi_card(label, value, icon), unsafe_allow_html=True)

st.divider()

# --- Pipeline Visualization ---
st.subheader("Workflow Pipeline")

DEMO_COUNTS = {"Inbox": 2, "Needs_Action": 3, "Plans": 2, "Pending_Approval": 3, "Done": 12}
_display_counts = counts if not _is_demo_mode else DEMO_COUNTS

st.markdown(pipeline_flow_html(_display_counts), unsafe_allow_html=True)

st.divider()

# --- Financial Overview ---
st.subheader("Financial Overview")

from utils.formatters import format_currency

@st.cache_data(ttl=300, show_spinner=False)
def _load_financial_data():
    try:
        from src.mcp.tools.odoo_reports import get_financial_summary
        _fin = get_financial_summary(None, None)
        if _fin and _fin.get("status") != "error" and _fin.get("revenue", 0) > 0:
            return {
                "revenue": _fin["revenue"],
                "expenses": _fin.get("expenses", 0),
                "net_cash_flow": _fin.get("net_cash_flow", _fin["revenue"] - _fin.get("expenses", 0)),
                "outstanding_receivables": _fin.get("outstanding_receivables", 0),
                "is_demo": False,
            }
    except Exception:
        pass
    return {
        "revenue": 14200, "expenses": 3450, "net_cash_flow": 10750,
        "outstanding_receivables": 7200, "is_demo": True,
    }


# Try live Odoo data, fall back to demo
_fin_data = _load_financial_data()
f_rev = _fin_data["revenue"]
f_exp = _fin_data["expenses"]
f_net = _fin_data["net_cash_flow"]
f_recv = _fin_data["outstanding_receivables"]
_use_demo = _fin_data["is_demo"]

if _use_demo:
    st.caption("Demo data — connect Odoo for live numbers")

fcols = st.columns(4)
fcols[0].markdown(kpi_card("Revenue", format_currency(f_rev), lucide("banknote", 28, "success")), unsafe_allow_html=True)
fcols[1].markdown(kpi_card("Expenses", format_currency(f_exp), lucide("trending-up", 28, "danger")), unsafe_allow_html=True)
fcols[2].markdown(kpi_card("Net Cash Flow", format_currency(f_net), lucide("bar-chart-3", 28, "primary")), unsafe_allow_html=True)
fcols[3].markdown(kpi_card("Receivables", format_currency(f_recv), lucide("clipboard-list", 28, "warning")), unsafe_allow_html=True)

st.markdown("<div style='margin-top:1.5rem;'></div>", unsafe_allow_html=True)

# Mini revenue vs expenses chart
fig_fin = go.Figure()
weeks = ["Week 1", "Week 2", "Week 3", "Week 4"]
fig_fin.add_trace(go.Bar(name="Revenue", x=weeks, y=[8500, 11800, 12400, f_rev], marker_color="#00c853"))
fig_fin.add_trace(go.Bar(name="Expenses", x=weeks, y=[2800, 3200, 3100, f_exp], marker_color="#ff5252"))
fig_fin.update_layout(
    barmode="group",
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    height=280,
    margin=dict(l=0, r=0, t=30, b=0),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
)
st.plotly_chart(fig_fin, use_container_width=True)

st.divider()

# --- Service Health Grid ---
st.subheader("Connected Services")

SERVICE_LABELS = {
    "odoo": ("Accounting (Odoo)", service_icon("odoo", 18, "primary")),
    "gmail": ("Email (Gmail)", service_icon("gmail", 18, "primary")),
    "linkedin": ("LinkedIn", service_icon("linkedin", 18, "primary")),
    "mastodon": ("Mastodon", service_icon("mastodon", 18, "primary")),
    "facebook": ("Facebook", service_icon("facebook", 18, "primary")),
    "instagram": ("Instagram", service_icon("instagram", 18, "primary")),
    "x_twitter": ("X (Twitter)", service_icon("x_twitter", 18, "primary")),
}

if _is_demo_mode:
    st.caption("Demo data — connect services for live health status")

for i in range(0, len(SERVICES), 3):
    row = SERVICES[i:i + 3]
    cols = st.columns(3)
    for col, svc in zip(cols, row):
        svc_health = health.get(svc, {})
        svc_status = svc_health.get("status", "unknown")
        last_ok = svc_health.get("last_ok")

        label, emoji = SERVICE_LABELS.get(svc, (svc.title(), service_icon(svc, 18, "muted")))
        card_class = "health-card-ok" if svc_status == "operational" else (
            "health-card-degraded" if svc_status == "degraded" else "health-card-down"
        )

        with col:
            badge = status_badge(svc_status)
            last_active = time_ago(str(last_ok)) if last_ok else '—'
            card_html = (
                '<div class="health-card ' + card_class + '" style="min-height:80px;">'
                '<div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:4px;">'
                '<strong style="display:inline-flex;align-items:center;gap:6px;">' + emoji + ' ' + label + '</strong>'
                + badge +
                '</div>'
                '<div style="margin-top:0.5rem; font-size:0.8rem; color:#8899aa;">'
                'Last active: ' + last_active +
                '</div>'
                '</div>'
            )
            st.markdown(card_html, unsafe_allow_html=True)

st.divider()

# --- Quick Showcase: Urgent Items & Links to Detail Pages ---
st.subheader("Quick Actions & Urgent Items")

# Load pending approvals count for demo
pending_count = 3 if _is_demo_mode else 0

# Active Plans (Ralph Wiggum) - demo data for showcase
plans = list_vault_items(VAULT_PATH / "Plans")
active_plans = [p for p in plans if p["metadata"].get("status") in ("in_progress", "active", "running")]
if not active_plans:
    active_plans = [
        {"filename": "quarterly-review-plan.md", "metadata": {"subject": "Quarterly Business Review", "progress": "4/5 steps", "next_step": "Send email summary to leadership", "status": "in_progress"}},
        {"filename": "client-onboarding-plan.md", "metadata": {"subject": "Acme Corp Onboarding", "progress": "2/6 steps", "next_step": "Create project workspace & send welcome email", "status": "in_progress"}},
    ]

# Top pending approvals
from utils.vault_reader import list_vault_items as _list
approvals = _list(VAULT_PATH / "Pending_Approval")
pending_approvals = [a for a in approvals if a["metadata"].get("status") == "pending"]
if _is_demo_mode and not pending_approvals:
    pending_approvals = [
        {"filename": "social-20260220T145840-mastodon.md", "metadata": {"subject": "LinkedIn post: AI trends", "mcp_tool": "linkedin_post"}},
        {"filename": "action-20260213T190500-reply-client-proposal.md", "metadata": {"subject": "Reply to CloudTech inquiry", "mcp_tool": "email_send"}},
    ]

# Urgent items in Needs_Action
needs_action = _list(VAULT_PATH / "Needs_Action")
urgent_items = [i for i in needs_action if i["metadata"].get("priority") == "high"]
if _is_demo_mode and not urgent_items:
    urgent_items = [
        {"filename": "email-20260216T074500-partnership-inquiry.md", "metadata": {"subject": "Partnership inquiry from TechVentures", "priority": "high", "from": "sarah.chen@cloudtech.io"}},
        {"filename": "email-20260217T090000-urgent-renewal.md", "metadata": {"subject": "Server renewal — expires in 3 days", "priority": "high", "from": "billing@cloudhost.io"}},
        {"filename": "whatsapp-20260217T083000-client-escalation.md", "metadata": {"subject": "Client escalation: API downtime", "priority": "high", "from": "John (Acme Corp)"}},
    ]

showcase_cols = st.columns(4)

# Column 1: Active Plans
with showcase_cols[0]:
    st.markdown("#### 📋 Active Plans")
    if active_plans:
        for plan in active_plans[:2]:
            meta = plan["metadata"]
            st.markdown(
                f'<div class="health-card health-card-degraded" style="margin-bottom:0.5rem;">'
                f'<strong>{meta.get("subject", "Plan")}</strong>'
                f'<div style="font-size:0.85rem;color:#8899aa;">{meta.get("progress", "")} — {meta.get("next_step", "")}</div>'
                f'</div>', unsafe_allow_html=True)
    else:
        st.caption("No active plans")

# Column 2: Pending Approvals
with showcase_cols[1]:
    st.markdown("#### ✅ Pending Approvals")
    if pending_approvals:
        for ap in pending_approvals[:3]:
            meta = ap["metadata"]
            tool = meta.get("mcp_tool", meta.get("type", "action"))
            icon = "📧" if "email" in tool else "📱" if "post" in tool else "⚙️"
            # Show action type + subject/description
            subject = meta.get("subject") or meta.get("target") or meta.get("from", "")
            if not subject:
                # Extract from filename
                fname = ap["filename"].replace(".md", "").replace("-", " ")
                # Remove timestamp prefix
                import re
                subject = re.sub(r"^\d{8}T\d{6}-", "", fname).replace("_", " ")
            action_type = tool.replace("_", " ").title()
            st.markdown(
                f'<div class="health-card" style="margin-bottom:0.5rem;">'
                f'<div style="display:flex;align-items:center;gap:6px;">'
                f'<span>{icon}</span><strong>{action_type}</strong>'
                f'</div>'
                f'<div style="font-size:0.8rem;color:#8899aa;margin-top:0.2rem;">{subject[:50]}</div>'
                f'</div>', unsafe_allow_html=True)
    else:
        st.caption("No pending approvals")

# Column 3: Urgent Items
with showcase_cols[2]:
    st.markdown("#### 🔴 Urgent Items")
    if urgent_items:
        for ui in urgent_items[:3]:
            meta = ui["metadata"]
            sender = meta.get("from") or meta.get("target") or meta.get("source", "")
            st.markdown(
                f'<div class="health-card health-card-down" style="margin-bottom:0.5rem;">'
                f'<strong>{meta.get("subject", "Item")}</strong>'
                f'<div style="font-size:0.8rem;color:#ff5252;margin-top:0.2rem;">'
                f'From: {sender} | High priority'
                f'</div>'
                f'</div>', unsafe_allow_html=True)
    else:
        st.caption("No urgent items")

# Column 4: Quick Action Buttons
with showcase_cols[3]:
    st.markdown("#### ⚡ Quick Actions")
    if st.button("🔄 Run Full Pipeline", type="primary", use_container_width=True, key="home_run_pipeline"):
        st.info("This would run: watchers → classify → approvals → update dashboard")
    if st.button("📥 Process Inbox", use_container_width=True, key="home_process_inbox"):
        st.switch_page("pages/1_Inbox_Hub.py")
    if st.button("✅ Check Approvals", use_container_width=True, key="home_check_approvals"):
        st.switch_page("pages/2_Review_Desk.py")
    if st.button("📊 Generate Briefing", use_container_width=True, key="home_gen_briefing"):
        st.switch_page("pages/3_Executive_Brief.py")

st.divider()

# --- Recent Activity ---
st.subheader("Recent Activity")

DEMO_ACTIVITY = [
    {"date": "Feb 17", "item": "Social Post", "action": "Business growth strategies posted to LinkedIn"},
    {"date": "Feb 16", "item": "INV-2026-0340", "action": "Invoice created for DesignStudio — $6,500.00"},
    {"date": "Feb 16", "item": "Social Post", "action": "Product launch announcement posted to Mastodon"},
    {"date": "Feb 16", "item": "Social Post", "action": "Product launch cross-posted to Facebook"},
    {"date": "Feb 15", "item": "Social Post", "action": "AI automation case study posted to LinkedIn"},
    {"date": "Feb 15", "item": "INV-2026-0339", "action": "Payment received from TechVentures — $3,200.00"},
    {"date": "Feb 15", "item": "Weekly Tip", "action": "Productivity tip posted to Mastodon & Instagram"},
    {"date": "Feb 14", "item": "INV-2026-0338", "action": "Payment received from Acme Corp — $4,500.00"},
    {"date": "Feb 14", "item": "Health Check", "action": "All services operational (7/7)"},
    {"date": "Feb 13", "item": "Briefing", "action": "Weekly briefing generated and saved"},
    {"date": "Feb 13", "item": "Inbox Item", "action": "Customer inquiry from Acme Corp processed"},
    {"date": "Feb 12", "item": "Approval", "action": "Social post draft approved and published"},
]

display_activity = activity if activity else DEMO_ACTIVITY
if not activity:
    st.caption("Demo data — activity will populate as your AI Employee runs")

table_rows = ""
for a in display_activity[:10]:
    item_val = a.get("item", "")
    table_rows += (
        '<tr>'
        '<td>' + str(a.get("date", "—")) + '</td>'
        '<td>' + (friendly_name(item_val) if item_val else "—") + '</td>'
        '<td>' + str(a.get("action", "—")) + '</td>'
        '</tr>'
    )
st.markdown(
    '<table class="activity-table">'
    '<thead><tr><th>Date</th><th>Item</th><th>Action</th></tr></thead>'
    '<tbody>' + table_rows + '</tbody>'
    '</table>',
    unsafe_allow_html=True,
)

# --- Footer ---
st.divider()
st.caption("AI Employee Dashboard")

# --- Auto-Refresh & Logo (Sidebar Bottom) ---
_ar_enabled, _ar_interval = auto_refresh_sidebar("home")
if _ar_enabled:
    st_autorefresh(interval=_ar_interval * 1000, key="home_autorefresh")
