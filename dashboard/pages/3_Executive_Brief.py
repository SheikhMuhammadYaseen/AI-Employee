"""Executive Brief — Weekly executive briefing viewer and generator."""

import sys
import re
from pathlib import Path
from datetime import datetime, timedelta
import time
import threading

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils.path_setup import VAULT_PATH
from utils.theme import inject_custom_css, kpi_card, status_badge, render_sidebar_branding
from utils.formatters import format_currency, format_timestamp
from utils.vault_reader import read_briefing_md, list_vault_items
from utils.icons import lucide, icon_text

st.set_page_config(page_title="Executive Brief", page_icon="📊", layout="wide")
inject_custom_css()
render_sidebar_branding()

# --- Cache expensive operations ---
@st.cache_data(ttl=300)
def get_briefing_data(vault_path):
    """Cache briefing data to avoid repeated file reads."""
    return read_briefing_md(vault_path)

@st.cache_data(ttl=300)
def get_briefing_history(vault_path):
    """Cache briefing history."""
    done_items = list_vault_items(vault_path / "Done")
    return [
        it for it in done_items
        if "briefing" in it["filename"].lower()
        or it["metadata"].get("type") in ("briefing", "ceo_briefing")
    ]

# --- Lazy import for heavy modules ---
@st.cache_resource
def get_briefing_modules():
    """Lazy load briefing generator modules only when needed."""
    try:
        from src.briefing.briefing_generator import (
            generate_briefing,
            collect_financial_data,
            collect_operational_data,
            collect_social_data,
            detect_bottlenecks,
        )
        return {
            "generate_briefing": generate_briefing,
            "collect_financial_data": collect_financial_data,
            "collect_operational_data": collect_operational_data,
            "collect_social_data": collect_social_data,
            "detect_bottlenecks": detect_bottlenecks,
        }
    except ImportError:
        return {
            "generate_briefing": None,
            "collect_financial_data": None,
            "collect_operational_data": None,
            "collect_social_data": None,
            "detect_bottlenecks": None,
        }

# --- Load data with caching ---
briefing = get_briefing_data(VAULT_PATH)
modules = get_briefing_modules()
generate_briefing = modules["generate_briefing"]
collect_financial_data = modules["collect_financial_data"]
collect_operational_data = modules["collect_operational_data"]
collect_social_data = modules["collect_social_data"]
detect_bottlenecks = modules["detect_bottlenecks"]

# --- Header with actions ---
col_title, col_actions = st.columns([3, 2])
with col_title:
    st.markdown(
    icon_text("bar-chart-3", "Executive Brief", 28, "primary", "h1")
    .replace("<svg", "<svg style='position:relative; top:-3px;'"),
    unsafe_allow_html=True
)
with col_actions:
    btn_cols = st.columns([1, 1] if briefing["exists"] else [1])
    with btn_cols[0]:
        generate_clicked = st.button("Generate New", type="primary", icon=":material/refresh:", use_container_width=True)
    if briefing["exists"] and len(btn_cols) > 1:
        with btn_cols[1]:
            _briefing_path = VAULT_PATH / "Briefing.md"
            _dl_data = _briefing_path.read_text(encoding="utf-8") if _briefing_path.exists() else briefing.get("body", "")
            st.download_button(
                "Download",
                icon=":material/download:",
                data=_dl_data,
                file_name="Weekly-Briefing.md",
                mime="text/markdown",
                use_container_width=True,
            )

# --- Date picker + generate logic ---
target_date = st.date_input("Briefing Date", value=datetime.now(), label_visibility="collapsed")

if generate_clicked:
    if generate_briefing:
        with st.spinner("Generating briefing..."):
            try:
                result = generate_briefing(str(VAULT_PATH), target_date=str(target_date))
                if result.get("status") == "success":
                    st.success("New briefing generated successfully!")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error("Could not generate the briefing. Please try again.")
            except Exception:
                st.error("Something went wrong while generating the briefing.")
    else:
        with st.spinner("Generating briefing..."):
            import time
            time.sleep(1.5)
        st.success("Briefing generated successfully! Showing demo briefing below.")

_is_demo_briefing = not briefing["exists"]

if _is_demo_briefing:
    st.caption("Demo data — generate a real briefing with the button above")

    briefing = {
        "exists": True,
        "metadata": {
            "generated": "2026-02-17T14:00:00Z",
            "week_start": "2026-02-10",
            "week_end": "2026-02-16",
            "type": "ceo_briefing",
        },
        "body": (
            "## Financial Summary\n\n"
            "- **Revenue**: $14,200 (+18% vs last week)\n"
            "- **Expenses**: $3,450 (within budget)\n"
            "- **Net Cash Flow**: $10,750\n"
            "- **Outstanding Receivables**: $7,200 (2 invoices pending)\n"
            "- New invoice INV-2026-0340 created for DesignStudio — $6,500\n"
            "- Payment received from TechVentures — $3,200\n\n"
            "## Operational Status\n\n"
            "- **Services**: 5/7 operational (Instagram degraded, X unavailable)\n"
            "- **Automation Runs**: 42 this week (100% success)\n"
            "- **Items Processed**: 18 emails classified and routed\n"
            "- **Approvals**: 12 processed (10 approved, 2 rejected)\n"
            "- Gmail watcher running continuously with 0 missed polls\n\n"
            "## Social Media Activity\n\n"
            "- **Total Posts**: 10 across 4 platforms\n"
            "- **Engagements**: 312 (up 24% from last week)\n"
            "- **Top Post**: Business growth strategies on LinkedIn (87 engagements)\n"
            "- **New Followers**: +151 across all platforms\n"
            "- LinkedIn and Mastodon performing above average\n\n"
            "## Bottlenecks and Risks\n\n"
            "- WARNING: X (Twitter) API has been unavailable for 48 hours — connection refused\n"
            "  - Recommendation: Check API credentials and rate limits\n"
            "- WARNING: Instagram showing degraded performance — rate limit exceeded\n"
            "  - Recommendation: Reduce posting frequency to 1/day\n"
            "- 2 invoices overdue by 7+ days (Acme Corp $4,500, OldClient $2,700)\n\n"
            "## Recommended Actions\n\n"
            "1. Follow up on overdue invoices — total $7,200 outstanding\n"
            "2. Investigate X (Twitter) API connectivity issues\n"
            "3. Review Instagram posting schedule to stay within rate limits\n"
            "4. Consider increasing LinkedIn posting — highest ROI platform this week\n"
            "5. Schedule quarterly financial review based on strong revenue trend\n"
        ),
    }

# --- View Mode Toggle ---
view_mode = st.radio("View Mode", ["Formatted View", "Full Text"], horizontal=True)

if view_mode == "Full Text":
    st.markdown("---")
    st.markdown(briefing["body"])
    st.stop()

# --- Formatted View ---
meta = briefing["metadata"]
st.caption(
    f"Generated: {meta.get('generated', '—')} | "
    f"Period: {meta.get('week_start', '?')} — {meta.get('week_end', '?')}"
)

st.divider()

# --- Parse and display sections from briefing body ---
body = briefing["body"]
sections = {}
current_section = None
current_content = []

for line in body.splitlines():
    if line.startswith("## "):
        if current_section:
            sections[current_section] = "\n".join(current_content)
        current_section = line[3:].strip()
        current_content = []
    elif current_section:
        current_content.append(line)
if current_section:
    sections[current_section] = "\n".join(current_content)

# --- Helper function to create charts efficiently ---
@st.cache_data(ttl=300)
def create_financial_chart(revenue, expenses):
    """Create financial bar chart with caching."""
    fig = go.Figure()
    fig.add_trace(go.Bar(name="Revenue", x=["This Week"], y=[float(revenue)], marker_color="#00c853"))
    fig.add_trace(go.Bar(name="Expenses", x=["This Week"], y=[float(expenses)], marker_color="#ff5252"))
    fig.update_layout(
        barmode="group", 
        template="plotly_dark", 
        paper_bgcolor="rgba(0,0,0,0)", 
        plot_bgcolor="rgba(0,0,0,0)", 
        height=300,
        margin=dict(l=0, r=0, t=30, b=0),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    return fig

@st.cache_data(ttl=300)
def create_social_chart(data):
    """Create social media chart with caching."""
    if not data:
        return None
    df = pd.DataFrame(data)
    fig = px.bar(
        df, x="Platform", y=["Posts", "Engagements"], 
        barmode="group", template="plotly_dark", 
        color_discrete_sequence=["#00d4ff", "#00c853"]
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", 
        plot_bgcolor="rgba(0,0,0,0)", 
        height=300,
        margin=dict(l=0, r=0, t=30, b=0),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    return fig

# --- Financial Section with Lazy Loading ---
fin_key = next((k for k in sections if "Financial" in k), None)
if fin_key:
    st.markdown(icon_text("dollar-sign", fin_key, 24, "success", "h3"), unsafe_allow_html=True)

    # Check if we need to load financial data
    if collect_financial_data and not _is_demo_briefing:
        # Show loading placeholder
        placeholder = st.empty()
        placeholder.info("📊 Loading financial data...")
        
        try:
            week_end = datetime.strptime(meta.get("week_end", str(datetime.now().date())), "%Y-%m-%d").date()
            week_start = datetime.strptime(meta.get("week_start", str(week_end - timedelta(days=6))), "%Y-%m-%d").date()
            prev_end = week_start - timedelta(days=1)
            prev_start = prev_end - timedelta(days=6)
            
            # Fetch financial data
            fin_data = collect_financial_data(str(week_start), str(week_end), str(prev_start), str(prev_end))

            if fin_data.get("status") != "error":
                current = fin_data.get("current", {})
                previous = fin_data.get("previous", {})

                # Clear placeholder and render content
                placeholder.empty()
                
                mcols = st.columns(4)
                metrics = [
                    ("Revenue", current.get("revenue", 0), previous.get("revenue")),
                    ("Expenses", current.get("expenses", 0), previous.get("expenses")),
                    ("Net Cash Flow", current.get("net_cash_flow", 0), previous.get("net_cash_flow")),
                    ("Receivables", current.get("outstanding_receivables", 0), previous.get("outstanding_receivables")),
                ]
                for col, (label, val, prev_val) in zip(mcols, metrics):
                    delta = None
                    if prev_val is not None:
                        try:
                            delta = f"{format_currency(float(val) - float(prev_val))}"
                        except (TypeError, ValueError):
                            delta = None
                    col.metric(label, format_currency(val), delta=delta)

                # Use cached chart
                fig = create_financial_chart(current.get("revenue", 0), current.get("expenses", 0))
                st.plotly_chart(fig, use_container_width=True)
            else:
                placeholder.empty()
                st.markdown(sections[fin_key])
        except Exception as e:
            placeholder.empty()
            st.markdown(sections[fin_key])
    else:
        st.markdown(sections[fin_key])

# --- Operational Section ---
ops_key = next((k for k in sections if "Operational" in k), None)
if ops_key:
    st.divider()
    st.markdown(icon_text("settings", ops_key, 24, "primary", "h3"), unsafe_allow_html=True)

    SERVICE_NAMES = {
        "odoo": "Accounting", "gmail": "Email", "linkedin": "LinkedIn",
        "mastodon": "Mastodon", "facebook": "Facebook", "instagram": "Instagram",
        "x_twitter": "X (Twitter)",
    }

    if collect_operational_data and not _is_demo_briefing:
        try:
            week_end = datetime.strptime(meta.get("week_end", str(datetime.now().date())), "%Y-%m-%d").date()
            week_start = datetime.strptime(meta.get("week_start", str(week_end - timedelta(days=6))), "%Y-%m-%d").date()
            ops_data = collect_operational_data(str(VAULT_PATH), str(week_start), str(week_end))
            services = ops_data.get("services", {})

            if services:
                scols = st.columns(3)
                for i, (svc_name, svc_info) in enumerate(services.items()):
                    svc_status = svc_info.get("status", "unknown")
                    card_class = "health-card-ok" if svc_status == "operational" else "health-card-down"
                    fname = SERVICE_NAMES.get(svc_name, svc_name.replace("_", " ").title())
                    scols[i % 3].markdown(
                        f'<div class="health-card {card_class}" style="margin-bottom:0.5rem;">'
                        f'<strong>{fname}</strong> {status_badge(svc_status)}'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

            sched_runs = ops_data.get("scheduler_runs", 0)
            sched_ok = ops_data.get("scheduler_success", 0)
            sched_fail = ops_data.get("scheduler_failed", 0)
            scols2 = st.columns(3)
            scols2[0].metric("Automation Runs", sched_runs)
            scols2[1].metric("Successful", sched_ok)
            scols2[2].metric("Failed", sched_fail)
        except Exception:
            st.markdown(sections[ops_key])
    else:
        DEMO_OPS_SERVICES = {
            "odoo": "operational", "gmail": "operational", "linkedin": "operational",
            "mastodon": "operational", "facebook": "operational",
            "instagram": "degraded", "x_twitter": "unavailable",
        }
        scols = st.columns(3)
        for i, (svc_name, svc_status) in enumerate(DEMO_OPS_SERVICES.items()):
            card_class = (
                "health-card-ok" if svc_status == "operational"
                else "health-card-degraded" if svc_status == "degraded"
                else "health-card-down"
            )
            fname = SERVICE_NAMES.get(svc_name, svc_name.replace("_", " ").title())
            scols[i % 3].markdown(
                f'<div class="health-card {card_class}" style="margin-bottom:0.5rem;">'
                f'<strong>{fname}</strong> {status_badge(svc_status)}'
                f'</div>',
                unsafe_allow_html=True,
            )

        scols2 = st.columns(3)
        scols2[0].metric("Automation Runs", 42)
        scols2[1].metric("Successful", 42)
        scols2[2].metric("Failed", 0)

# --- Social Section ---
soc_key = next((k for k in sections if "Social" in k), None)
if soc_key:
    st.divider()
    st.markdown(icon_text("smartphone", soc_key, 24, "primary", "h3"), unsafe_allow_html=True)

    if collect_social_data and not _is_demo_briefing:
        try:
            week_end = datetime.strptime(meta.get("week_end", str(datetime.now().date())), "%Y-%m-%d").date()
            week_start = datetime.strptime(meta.get("week_start", str(week_end - timedelta(days=6))), "%Y-%m-%d").date()
            soc_data = collect_social_data(str(VAULT_PATH), str(week_start), str(week_end))
            platforms = soc_data.get("platforms", {})

            if platforms:
                chart_data = []
                for pname, pdata in platforms.items():
                    if isinstance(pdata, dict):
                        chart_data.append({
                            "Platform": pname.replace("_", " ").title(),
                            "Posts": pdata.get("posts", 0),
                            "Engagements": pdata.get("engagements", 0),
                        })

                if chart_data:
                    fig = create_social_chart(chart_data)
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.markdown(sections[soc_key])
            else:
                st.markdown(sections[soc_key])
        except Exception:
            st.markdown(sections[soc_key])
    else:
        st.markdown(sections[soc_key])

# --- Bottlenecks & Risks ---
bn_key = next((k for k in sections if "Bottleneck" in k or "Risk" in k), None)
if bn_key:
    st.divider()
    st.markdown(icon_text("triangle-alert", bn_key, 24, "warning", "h3"), unsafe_allow_html=True)
    content = sections[bn_key]

    items = []
    for raw_line in content.strip().splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped == "---":
            continue
        indent = len(raw_line) - len(raw_line.lstrip())
        if indent > 0 and items:
            items[-1]["lines"].append(stripped.lstrip("- "))
        else:
            severity = "info"
            if "CRITICAL" in stripped.upper():
                severity = "critical"
            elif "WARNING" in stripped.upper():
                severity = "warning"
            items.append({"lines": [stripped.lstrip("- ")], "severity": severity})

    for item in items:
        main = item["lines"][0]
        sub_html = ""
        if len(item["lines"]) > 1:
            sub_html = (
                '<div style="font-size:0.9rem;color:#8899aa;margin-top:0.3rem;">'
                + "<br>".join(item["lines"][1:])
                + "</div>"
            )
        st.markdown(
            f'<div class="severity-{item["severity"]}">{main}{sub_html}</div>',
            unsafe_allow_html=True,
        )

# --- Recommended Actions ---
act_key = next((k for k in sections if "Action" in k or "Recommend" in k), None)
if act_key:
    st.divider()
    st.markdown(icon_text("clipboard-list", act_key, 24, "primary", "h3"), unsafe_allow_html=True)
    st.markdown(sections[act_key])

# --- Briefing History ---
st.divider()
st.markdown(icon_text("book-open", "Briefing History", 24, "primary", "h3"), unsafe_allow_html=True)

briefing_history = get_briefing_history(VAULT_PATH)

def _briefing_display_name(item):
    date = item["metadata"].get("date", "")
    if date:
        try:
            dt = datetime.strptime(str(date), "%Y-%m-%d")
            return f"Briefing — {dt.strftime('%B %d, %Y')}"
        except ValueError:
            pass
    name = item["filename"].replace(".md", "").replace("-", " ").replace("_", " ")
    name = re.sub(r"\d{8}T\d{6}", "", name).strip()
    return name.title() if name else "Previous Briefing"

if briefing_history:
    for item in briefing_history[:10]:
        display = _briefing_display_name(item)
        with st.expander(display):
            st.caption(f"Date: {item['metadata'].get('date', '—')}")
            st.markdown(item["body"][:2000])
else:
    st.caption("Demo data — previous briefings will appear here after generation")
    DEMO_HISTORY = [
        {"date": "Feb 10, 2026", "summary": "Revenue $12,400 | 5/7 services operational | 8 social posts (248 engagements)"},
        {"date": "Feb 03, 2026", "summary": "Revenue $11,800 | 6/7 services operational | 6 social posts (195 engagements)"},
        {"date": "Jan 27, 2026", "summary": "Revenue $9,600 | 7/7 services operational | 5 social posts (167 engagements)"},
    ]
    for entry in DEMO_HISTORY:
        with st.expander(f"Briefing — {entry['date']}"):
            st.markdown(entry["summary"])