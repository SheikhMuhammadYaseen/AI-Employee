"""Activity Log — Browse system activity logs by category and date."""

import sys
from pathlib import Path
from datetime import datetime, timedelta

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils.path_setup import VAULT_PATH
from utils.theme import inject_custom_css, status_badge, render_sidebar_branding
from utils.formatters import format_status_badge
from utils.vault_reader import list_log_files, parse_log_entries
from utils.icons import icon_text

st.set_page_config(page_title="Activity Log", page_icon="📋", layout="wide")
inject_custom_css()
render_sidebar_branding()

# --- src/ imports ---
try:
    from src.logging.audit_logger import summarize_week
except ImportError:
    summarize_week = None

st.markdown(
    icon_text("clipboard-list", "Activity Log", 28, "primary", "h1")
    .replace("<svg", "<svg style='position:relative; top:-3px;'"),
    unsafe_allow_html=True
)

# --- Filters ---
CATEGORY_LABELS = {
    "All": "All",
    "mcp": "Service Calls",
    "classification": "Item Processing",
    "approval": "Approvals",
    "loop": "Automation Runs",
    "scheduler": "Scheduled Tasks",
}

col1, col2, col3 = st.columns(3)
with col1:
    categories = list(CATEGORY_LABELS.keys())
    category = st.selectbox("Category", categories, format_func=lambda x: CATEGORY_LABELS[x])
with col2:
    start_date = st.date_input("Start Date", value=datetime.now() - timedelta(days=7))
with col3:
    end_date = st.date_input("End Date", value=datetime.now())

cat_filter = None if category == "All" else category

# --- Tabs ---
tab_daily, tab_weekly = st.tabs(["Daily Log View", "Weekly Summary"])

# --- Daily Log View ---
with tab_daily:
    log_files = list_log_files(VAULT_PATH, category=cat_filter)

    # Filter by date range
    filtered_logs = []
    for log in log_files:
        log_date_str = log["metadata"].get("date", "")
        if log_date_str:
            try:
                log_date = datetime.strptime(str(log_date_str), "%Y-%m-%d").date()
                if start_date <= log_date <= end_date:
                    filtered_logs.append(log)
            except ValueError:
                filtered_logs.append(log)  # Include if date can't be parsed
        else:
            # Try parsing date from filename
            filtered_logs.append(log)

    if not filtered_logs:
        st.caption("Demo data — logs will populate as your AI Employee runs")

        DEMO_DAILY_LOGS = [
            {"Category": "Service Calls", "Date": "Feb 17", "Entries": 8,
             "details": [
                 {"Time": "14:30", "Action": "health_check (odoo)", "Result": "Success", "Context": "All endpoints responding"},
                 {"Time": "14:25", "Action": "health_check (gmail)", "Result": "Success", "Context": "IMAP connection OK"},
                 {"Time": "13:15", "Action": "mastodon_post", "Result": "Success", "Context": "Posted: Product launch announcement"},
                 {"Time": "13:00", "Action": "linkedin_post", "Result": "Success", "Context": "Posted: Business growth strategies"},
                 {"Time": "12:00", "Action": "health_check (facebook)", "Result": "Success", "Context": "Graph API responding"},
                 {"Time": "11:30", "Action": "email_send", "Result": "Success", "Context": "Reply sent to CloudTech inquiry"},
                 {"Time": "10:00", "Action": "health_check (instagram)", "Result": "Warning", "Context": "Rate limit approaching"},
                 {"Time": "09:00", "Action": "health_check (x_twitter)", "Result": "Failed", "Context": "Connection refused"},
             ]},
            {"Category": "Item Processing", "Date": "Feb 17", "Entries": 5,
             "details": [
                 {"Time": "14:20", "Action": "classify_item", "Result": "Success", "Context": "Result: simple — moved to Done"},
                 {"Time": "13:45", "Action": "classify_item", "Result": "Success", "Context": "Result: action_required — draft created"},
                 {"Time": "11:00", "Action": "classify_item", "Result": "Success", "Context": "Result: complex — plan generated"},
                 {"Time": "10:30", "Action": "classify_item", "Result": "Success", "Context": "Result: simple — moved to Done"},
                 {"Time": "09:15", "Action": "classify_item", "Result": "Success", "Context": "Result: action_required — draft created"},
             ]},
            {"Category": "Approvals", "Date": "Feb 16", "Entries": 4,
             "details": [
                 {"Time": "16:00", "Action": "process_approval", "Result": "Success", "Context": "LinkedIn post approved and published"},
                 {"Time": "15:30", "Action": "process_approval", "Result": "Success", "Context": "Email reply approved and sent"},
                 {"Time": "14:00", "Action": "process_approval", "Result": "Success", "Context": "Mastodon post approved and published"},
                 {"Time": "11:00", "Action": "process_approval", "Result": "Rejected", "Context": "Facebook post rejected by admin"},
             ]},
            {"Category": "Automation Runs", "Date": "Feb 16", "Entries": 3,
             "details": [
                 {"Time": "18:00", "Action": "ralph_wiggum_loop", "Result": "Success", "Context": "Plan completed: 4/4 steps done"},
                 {"Time": "12:00", "Action": "ralph_wiggum_loop", "Result": "Success", "Context": "Plan in progress: 2/5 steps done"},
                 {"Time": "09:00", "Action": "ralph_wiggum_loop", "Result": "Success", "Context": "New plan started: Client onboarding"},
             ]},
        ]

        for log_entry in DEMO_DAILY_LOGS:
            with st.expander(
                f"{log_entry['Category']} — {log_entry['Date']} ({log_entry['Entries']} entries)",
                expanded=False,
            ):
                df = pd.DataFrame(log_entry["details"])
                st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.markdown(f"**{len(filtered_logs)} log file(s) found**")

        for log in filtered_logs:
            meta = log["metadata"]
            fname = log.get("filename", "")

            # Resolve category from metadata or filename
            cat = meta.get("category", "")
            if not cat or cat == "unknown":
                for key in CATEGORY_LABELS:
                    if key != "All" and key in fname.lower():
                        cat = key
                        break
                else:
                    cat = "general"
            cat_friendly = CATEGORY_LABELS.get(cat, cat.replace("_", " ").title())

            # Resolve date from metadata or filename
            date = meta.get("date", "")
            if not date or date == "—":
                import re as _re
                m = _re.search(r"(\d{4}-\d{2}-\d{2})", fname)
                if m:
                    date = m.group(1)
                else:
                    m = _re.search(r"(\d{8})", fname)
                    if m:
                        d = m.group(1)
                        date = f"{d[:4]}-{d[4:6]}-{d[6:]}"
                    else:
                        date = "Recent"

            # Resolve entry count
            entry_count = meta.get("entry_count", "")
            if not entry_count or entry_count == "—":
                body_lines = [l for l in log.get("body", "").splitlines() if l.strip()]
                entry_count = len(body_lines) if body_lines else "—"

            with st.expander(
                f"{cat_friendly} — {date} ({entry_count} entries)",
                expanded=False,
            ):
                # Parse entries
                entries = parse_log_entries(log["body"])

                if entries:
                    rows = []
                    for entry in entries:
                        result = entry.get("result", "")
                        rows.append({
                            "Time": entry.get("time", "—"),
                            "Action": entry.get("action", "—"),
                            "Result": format_status_badge(result) if result else "—",
                            "Context": entry.get("context", "—"),
                        })
                    df = pd.DataFrame(rows)
                    st.dataframe(df, use_container_width=True, hide_index=True)
                else:
                    st.markdown(log["body"][:3000] if log["body"] else "_Empty log_")

# --- Weekly Summary ---
with tab_weekly:
    # Try live summary first
    summary = None
    if summarize_week:
        try:
            summary = summarize_week(str(VAULT_PATH), str(start_date), str(end_date))
            if not summary or not summary.get("categories"):
                summary = None
        except Exception:
            summary = None

    # Demo data fallback
    DEMO_CATEGORIES = {
        "Service Calls": 42,
        "Item Processing": 18,
        "Approvals": 12,
        "Automation Runs": 14,
        "Scheduled Tasks": 8,
    }
    DEMO_DAILY_ACTIVITY = [
        {"Day": "Mon", "Actions": 16, "Errors": 1},
        {"Day": "Tue", "Actions": 21, "Errors": 0},
        {"Day": "Wed", "Actions": 14, "Errors": 2},
        {"Day": "Thu", "Actions": 18, "Errors": 0},
        {"Day": "Fri", "Actions": 12, "Errors": 0},
        {"Day": "Sat", "Actions": 8, "Errors": 0},
        {"Day": "Sun", "Actions": 5, "Errors": 0},
    ]
    DEMO_ERRORS = [
        "X (Twitter) API — Connection refused (4 occurrences)",
        "Instagram API — Rate limit exceeded (2 occurrences)",
    ]
    DEMO_TOP_ACTIONS = [
        {"Action": "health_check", "Count": 14, "Success Rate": "85.7%"},
        {"Action": "process_inbox", "Count": 12, "Success Rate": "100%"},
        {"Action": "social_post", "Count": 10, "Success Rate": "80%"},
        {"Action": "check_approvals", "Count": 8, "Success Rate": "100%"},
        {"Action": "send_email", "Count": 6, "Success Rate": "100%"},
        {"Action": "generate_briefing", "Count": 4, "Success Rate": "100%"},
        {"Action": "odoo_invoice", "Count": 3, "Success Rate": "100%"},
        {"Action": "odoo_payment", "Count": 3, "Success Rate": "100%"},
    ]

    if summary:
        categories_data = summary.get("categories", {})
        cat_display = {CATEGORY_LABELS.get(k, k.replace("_", " ").title()): v for k, v in categories_data.items()}
        total_entries = summary.get("total_entries", 0)
        errors = summary.get("error_patterns", [])
    else:
        cat_display = DEMO_CATEGORIES
        total_entries = sum(DEMO_CATEGORIES.values())
        errors = DEMO_ERRORS
        st.caption("Demo data — logs will populate as your AI Employee runs")

    from utils.icons import lucide
    from utils.theme import kpi_card

    # --- KPI Row ---
    total_errors = sum(d["Errors"] for d in DEMO_DAILY_ACTIVITY) if not summary else len(errors)
    success_rate = round((1 - total_errors / max(total_entries, 1)) * 100, 1)

    kcols = st.columns(4)
    kcols[0].markdown(kpi_card("Total Actions", total_entries, lucide("activity", 28, "primary")), unsafe_allow_html=True)
    kcols[1].markdown(kpi_card("Categories", len(cat_display), lucide("folder", 28, "primary")), unsafe_allow_html=True)
    kcols[2].markdown(kpi_card("Success Rate", f"{success_rate}%", lucide("check-circle", 28, "success")), unsafe_allow_html=True)
    kcols[3].markdown(kpi_card("Issues", total_errors, lucide("triangle-alert", 28, "danger" if total_errors > 0 else "success")), unsafe_allow_html=True)

    st.divider()

    # --- Activity by Category (pie + table) ---
    st.subheader("Activity by Category")

    cat_df = pd.DataFrame([{"Category": k, "Count": v} for k, v in cat_display.items()])

    col_chart, col_table = st.columns([3, 2])
    with col_chart:
        fig_pie = px.pie(
            cat_df, names="Category", values="Count",
            template="plotly_dark",
            color_discrete_sequence=["#00d4ff", "#00c853", "#ffc107", "#ff5252", "#8899aa"],
            hole=0.4,
        )
        fig_pie.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            height=320,
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    with col_table:
        st.dataframe(cat_df.sort_values("Count", ascending=False), use_container_width=True, hide_index=True)

    st.divider()

    # --- Daily Activity (bar chart) ---
    st.subheader("Daily Activity")

    if summary and summary.get("daily_activity"):
        daily_data = summary["daily_activity"]
    else:
        daily_data = DEMO_DAILY_ACTIVITY
    daily_df = pd.DataFrame(daily_data)

    fig_daily = go.Figure()
    fig_daily.add_trace(go.Bar(name="Actions", x=daily_df["Day"], y=daily_df["Actions"], marker_color="#00d4ff"))
    fig_daily.add_trace(go.Bar(name="Errors", x=daily_df["Day"], y=daily_df["Errors"], marker_color="#ff5252"))
    fig_daily.update_layout(
        barmode="stack", template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        height=300,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig_daily, use_container_width=True)

    st.divider()

    # --- Top Actions Table ---
    st.subheader("Top Actions")
    if summary and summary.get("top_actions"):
        top_df = pd.DataFrame(summary["top_actions"])
    else:
        top_df = pd.DataFrame(DEMO_TOP_ACTIONS)
    st.dataframe(top_df, use_container_width=True, hide_index=True)

    st.divider()

    # --- Issues Detected ---
    st.subheader("Issues Detected")
    if errors:
        for err in errors:
            st.markdown(
                f'<div class="severity-warning">{err}</div>',
                unsafe_allow_html=True,
            )
    else:
        st.success("No error patterns detected this week")

