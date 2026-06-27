"""System Status — Monitor all connected services and integrations."""

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils.path_setup import VAULT_PATH
from utils.theme import inject_custom_css, kpi_card, status_badge, render_sidebar_branding
from utils.formatters import time_ago
from utils.icons import lucide, icon_text, service_icon

st.set_page_config(page_title="System Status", page_icon="💚", layout="wide")
inject_custom_css()
render_sidebar_branding()

# --- src/ imports ---
try:
    from src.health.service_health import ServiceHealthTracker
except ImportError:
    ServiceHealthTracker = None

try:
    from src.mcp.router import health_check_all
except ImportError:
    health_check_all = None

st.markdown(
    icon_text("shield-check", "System Status", 30, "success", "h1")
    .replace("<svg", "<svg style='position:relative; top:-3px;'"),
    unsafe_allow_html=True
)

# --- Load health data ---
@st.cache_data(ttl=30)
def load_health():
    if ServiceHealthTracker is None:
        return {}
    try:
        tracker = ServiceHealthTracker(str(VAULT_PATH))
        return tracker.get_all_health()
    except Exception:
        return {}


health = load_health()

SERVICES = ["odoo", "gmail", "linkedin", "mastodon", "facebook", "instagram", "x_twitter"]

# Demo health data for showcase
_is_demo = not health
if _is_demo:
    health = {
        "odoo": {"status": "operational", "last_ok": "2026-02-17T14:30:00Z", "error_count": 0, "last_error": ""},
        "gmail": {"status": "operational", "last_ok": "2026-02-17T14:25:00Z", "error_count": 0, "last_error": ""},
        "linkedin": {"status": "operational", "last_ok": "2026-02-17T13:00:00Z", "error_count": 0, "last_error": ""},
        "mastodon": {"status": "operational", "last_ok": "2026-02-17T13:15:00Z", "error_count": 0, "last_error": ""},
        "facebook": {"status": "operational", "last_ok": "2026-02-17T12:00:00Z", "error_count": 0, "last_error": ""},
        "instagram": {"status": "degraded", "last_ok": "2026-02-16T18:00:00Z", "error_count": 2, "last_error": "Rate limit exceeded"},
        "x_twitter": {"status": "unavailable", "last_ok": "2026-02-15T10:00:00Z", "error_count": 6, "last_error": "Connection refused"},
    }
SERVICE_LABELS = {
    "odoo": ("Accounting (Odoo)", service_icon("odoo", 20, "primary"), "Financial operations, invoicing, payments"),
    "gmail": ("Email (Gmail)", service_icon("gmail", 20, "primary"), "Email monitoring and sending"),
    "linkedin": ("LinkedIn", service_icon("linkedin", 20, "primary"), "B2B social posting and sales leads"),
    "mastodon": ("Mastodon", service_icon("mastodon", 20, "primary"), "Social media posting"),
    "facebook": ("Facebook", service_icon("facebook", 20, "primary"), "Page posts and engagement"),
    "instagram": ("Instagram", service_icon("instagram", 20, "primary"), "Photo and story sharing"),
    "x_twitter": ("X (Twitter)", service_icon("x_twitter", 20, "primary"), "Tweets and social engagement"),
}

# --- Overall Status Banner ---
statuses = [health.get(s, {}).get("status", "unknown") for s in SERVICES]
green_count = sum(1 for s in statuses if s == "operational")
down_count = sum(1 for s in statuses if s in ("unavailable", "down", "error"))
degraded_count = len(SERVICES) - green_count - down_count

if _is_demo:
    st.caption("Demo data — connect services and run health checks for live status")

if green_count == len(SERVICES):
    st.success("All services are running smoothly")
elif down_count > 0:
    st.error(f"{down_count} service(s) are down — {green_count} still operational")
elif degraded_count > 0:
    st.warning(f"{degraded_count} service(s) experiencing issues — {green_count} operational")

# --- KPI Row ---
cols = st.columns(3)
cols[0].markdown(kpi_card("Online", green_count, lucide("circle-check", 28, "success")), unsafe_allow_html=True)
cols[1].markdown(kpi_card("Issues", degraded_count, lucide("circle-alert", 28, "warning")), unsafe_allow_html=True)
cols[2].markdown(kpi_card("Offline", down_count, lucide("circle-x", 28, "danger")), unsafe_allow_html=True)

st.divider()

# --- Service Cards (3 per row) ---
st.subheader("Service Details")

# Build card data
service_cards = []
for svc in SERVICES:
    svc_health = health.get(svc, {})
    svc_status = svc_health.get("status", "unknown")
    last_ok = svc_health.get("last_ok")
    error_count = svc_health.get("error_count", 0)
    last_error = svc_health.get("last_error", "")

    label, emoji, description = SERVICE_LABELS.get(svc, (svc.title(), service_icon(svc, 20, "muted"), ""))
    card_class = "health-card-ok" if svc_status == "operational" else (
        "health-card-degraded" if svc_status == "degraded" else "health-card-down"
    )

    # Friendly error message
    error_display = ""
    if last_error:
        err_text = str(last_error)
        if "Connection refused" in err_text:
            error_display = "Cannot connect to service"
        elif "timeout" in err_text.lower():
            error_display = "Service is not responding"
        elif "auth" in err_text.lower() or "401" in err_text:
            error_display = "Authentication issue"
        else:
            error_display = "Service error detected"

    service_cards.append((label, emoji, description, card_class, svc_status, last_ok, error_count, error_display))

# Render in rows of 3
for i in range(0, len(service_cards), 3):
    row_cards = service_cards[i:i + 3]
    cols = st.columns(3)
    for col, (label, emoji, description, card_class, svc_status, last_ok, error_count, error_display) in zip(cols, row_cards):
        with col:
            last_active = time_ago(str(last_ok)) if last_ok else '—'
            issues_line = f'<div>Recent issues: <strong>{error_count}</strong></div>' if error_count else ''
            error_line = ''
            badge = status_badge(svc_status)

            card_html = (
                '<div class="health-card ' + card_class + '" style="min-height:140px;">'
                '<div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:4px;margin-bottom:0.8rem;">'
                '<strong style="font-size:1rem;display:inline-flex;align-items:center;gap:6px;">' + emoji + ' ' + label + '</strong>'
                + badge +
                '</div>'
                '<div style="font-size:0.85rem; color:#8899aa; line-height:1.8;">'
                '<div style="margin-bottom:0.3rem;">' + description + '</div>'
                '<div>Last active: <strong>' + last_active + '</strong></div>'
                + issues_line + error_line +
                '</div>'
                '</div>'
            )
            st.markdown(card_html, unsafe_allow_html=True)

st.divider()

# --- Capabilities Overview ---
st.subheader("What Your AI Employee Can Do")

capabilities = {
    "Accounting (Odoo)": ["Create & manage invoices", "Record payments", "Generate financial reports", "Track receivables"],
    "Email (Gmail)": ["Monitor incoming emails", "Send replies", "Forward important messages"],
    "Social Media": ["Post to LinkedIn, Mastodon, Facebook, Instagram, X", "Track engagement", "Generate content drafts"],
}

for capability, features in capabilities.items():
    with st.expander(capability, expanded=False):
        for feature in features:
            st.markdown(f"- {feature}")

st.divider()

# --- Refresh Button ---
if st.button("Check All Services", type="primary", icon=":material/refresh:"):
    if health_check_all and not _is_demo:
        with st.spinner("Checking all services..."):
            try:
                tracker = ServiceHealthTracker(str(VAULT_PATH)) if ServiceHealthTracker else None
                results = health_check_all(health_tracker=tracker)
                st.success("Health check complete!")
                for svc_name, result in results.items():
                    svc_status = result.get("status", "unknown")
                    friendly_name = SERVICE_LABELS.get(svc_name, (svc_name,))[0]
                    badge = status_badge(svc_status)
                    st.markdown(f"**{friendly_name}**: {badge}", unsafe_allow_html=True)
                st.rerun()
            except Exception as e:
                st.error(f"Could not complete health check. Some services may be offline.")
    else:
        # Demo simulation
        with st.spinner("Checking all services..."):
            import time
            time.sleep(1.5)
        st.success("Health check complete!")
        for svc in SERVICES:
            svc_health = health.get(svc, {})
            svc_status = svc_health.get("status", "unknown")
            label = SERVICE_LABELS.get(svc, (svc.title(),))[0]
            st.markdown(f"**{label}**: {status_badge(svc_status)}", unsafe_allow_html=True)

