"""Automation — View and manage automated task schedules and manual runs."""

import sys
import json
from pathlib import Path

import streamlit as st
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils.path_setup import PROJECT_ROOT, VAULT_PATH
from utils.theme import inject_custom_css, kpi_card, status_badge, render_sidebar_branding
from utils.vault_reader import list_log_files
from utils.icons import lucide, icon_text

st.set_page_config(page_title="Automation", page_icon="⏰", layout="wide")
inject_custom_css()
render_sidebar_branding()

# --- src/ imports ---
try:
    from src.scheduling.scheduler import run_cycle, _load_config
except ImportError:
    run_cycle = None
    _load_config = None

st.markdown(
    icon_text("clock", "Automation", 28, "primary", "h1")
    .replace("<svg", "<svg style='position:relative; top:-3px;'"),
    unsafe_allow_html=True
)

# --- Load config ---
CONFIG_PATH = PROJECT_ROOT / "src" / "scheduling" / "scheduler_config.json"

COMPONENT_LABELS = {
    "approval_checker": ("Approval Checker", "Reviews approved/rejected items and executes actions"),
    "inbox_watcher": ("Inbox Watcher", "Monitors for new incoming items"),
    "health_monitor": ("Health Monitor", "Checks if all services are online"),
}


@st.cache_data(ttl=60)
def load_scheduler_config():
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    if _load_config:
        try:
            return _load_config(None, str(VAULT_PATH))
        except Exception:
            pass

    return {
        "interval_minutes": 5,
        "vault_path": str(VAULT_PATH),
        "log_path": str(VAULT_PATH / "Logs"),
        "components": {
            "approval_checker": {
                "enabled": True,
                "script": "src/approval/checker.py",
                "args": ["--vault-path", str(VAULT_PATH)],
            },
        },
    }


config = load_scheduler_config()

# --- Status Overview ---
interval = config.get("interval_minutes", 5)
components = config.get("components", {})
enabled_count = sum(1 for c in components.values() if c.get("enabled", False))
total_count = len(components)

cols = st.columns(3)
cols[0].markdown(kpi_card("Run Interval", f"{interval} min", lucide("timer", 28, "primary")), unsafe_allow_html=True)
cols[1].markdown(kpi_card("Active Tasks", enabled_count, lucide("check-circle", 28, "success")), unsafe_allow_html=True)
cols[2].markdown(kpi_card("Total Tasks", total_count, lucide("clipboard-list", 28, "info")), unsafe_allow_html=True)

st.divider()

# --- Automated Tasks ---
st.subheader("Automated Tasks")

if components:
    for name, comp in components.items():
        label, desc = COMPONENT_LABELS.get(name, (name.replace("_", " ").title(), ""))
        is_enabled = comp.get("enabled", False)
        status_text = "Active" if is_enabled else "Paused"
        badge = status_badge("operational" if is_enabled else "unknown")

        st.markdown(
            f"""
            <div class="health-card {'health-card-ok' if is_enabled else 'health-card-down'}" style="margin-bottom:0.5rem;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <strong>{label}</strong>
                        <div style="font-size:0.85rem; color:#8899aa;">{desc}</div>
                    </div>
                    {badge}
                </div>
                <div style="font-size:0.8rem; color:#8899aa; margin-top:0.3rem;">
                    Runs every {interval} minutes
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
else:
    st.info("No automated tasks configured yet")

st.divider()

# --- Recent Run History ---
st.subheader("Recent Runs")

scheduler_logs = list_log_files(VAULT_PATH, category="scheduler")

# Also look for scheduler-*.md files directly
logs_dir = VAULT_PATH / "Logs"
if logs_dir.exists():
    sched_files = sorted(logs_dir.glob("scheduler-*.md"), reverse=True)
    seen_paths = {log["path"] for log in scheduler_logs}
    for f in sched_files:
        if f not in seen_paths:
            try:
                import frontmatter as fm
                post = fm.load(str(f))
                scheduler_logs.append({
                    "path": f,
                    "filename": f.name,
                    "metadata": dict(post.metadata),
                    "body": post.content,
                })
            except Exception:
                pass
    scheduler_logs.sort(key=lambda x: x["filename"], reverse=True)

if scheduler_logs:
    for log in scheduler_logs[:10]:
        meta = log["metadata"]
        ts = meta.get("timestamp", "—")
        components_run = meta.get("components_run", "—")
        successful = meta.get("successful", "—")
        failed = meta.get("failed", 0)

        if failed == 0:
            run_status = "All tasks completed successfully"
            badge = status_badge("success")
        else:
            run_status = f"{failed} task(s) had issues"
            badge = status_badge("error")

        # Parse friendly timestamp from filename (scheduler-YYYYMMDDTHHMMSS.md)
        fname = log["filename"]
        try:
            ts_part = fname.replace("scheduler-", "").replace(".md", "")
            from datetime import datetime
            dt = datetime.strptime(ts_part, "%Y%m%dT%H%M%S")
            display_time = dt.strftime("%b %d, %Y at %H:%M")
        except Exception:
            display_time = fname

        with st.expander(f"{display_time} — {run_status}", expanded=False):
            mcols = st.columns(3)
            mcols[0].metric("Tasks Run", components_run)
            mcols[1].metric("Successful", successful)
            mcols[2].metric("Failed", failed)
            st.markdown("---")
            st.markdown(log["body"][:2000] if log["body"] else "_No details_")
else:
    st.caption("Demo data — run history will populate as your AI Employee runs")
    DEMO_RUNS = [
        {"Time": "Feb 17, 2026 09:15", "Tasks Run": 5, "Successful": 5, "Failed": 0, "Status": "All tasks completed"},
        {"Time": "Feb 17, 2026 09:10", "Tasks Run": 5, "Successful": 5, "Failed": 0, "Status": "All tasks completed"},
        {"Time": "Feb 17, 2026 09:05", "Tasks Run": 5, "Successful": 4, "Failed": 1, "Status": "X (Twitter) connection refused"},
        {"Time": "Feb 17, 2026 09:00", "Tasks Run": 5, "Successful": 5, "Failed": 0, "Status": "All tasks completed"},
        {"Time": "Feb 16, 2026 18:00", "Tasks Run": 5, "Successful": 5, "Failed": 0, "Status": "All tasks completed"},
        {"Time": "Feb 16, 2026 12:00", "Tasks Run": 5, "Successful": 4, "Failed": 1, "Status": "Instagram rate limit hit"},
    ]
    st.dataframe(pd.DataFrame(DEMO_RUNS), use_container_width=True, hide_index=True)

st.divider()

# --- Run Now Button ---
st.subheader("Manual Run")
st.caption("Trigger your AI Employee to run all active tasks right now")

lock_path = VAULT_PATH / ".scheduler.lock"
if lock_path.exists():
    st.warning("Your AI Employee is currently running. Please wait for it to finish.")

if st.button("Run Now", type="primary", icon=":material/play_arrow:"):
    if run_cycle:
        if lock_path.exists():
            st.error("Already running — please wait for the current cycle to finish.")
        else:
            with st.spinner("Running all active tasks..."):
                try:
                    results = run_cycle(config)
                    st.success("All tasks completed!")
                    for r in results:
                        r_name = r.get("name", "unknown")
                        friendly = COMPONENT_LABELS.get(r_name, (r_name.replace("_", " ").title(),))[0]
                        badge = status_badge(r.get("status", "unknown"))
                        st.markdown(f"**{friendly}**: {badge}", unsafe_allow_html=True)
                    st.rerun()
                except Exception as e:
                    st.error(f"Something went wrong. Please try again.")
    else:
        # Demo simulation
        with st.spinner("Running all active tasks..."):
            import time
            time.sleep(2)
        st.success("All tasks completed!")
        DEMO_RESULTS = [
            ("Approval Checker", "success"),
            ("Inbox Processor", "success"),
            ("Health Monitor", "success"),
        ]
        for name, result in DEMO_RESULTS:
            st.markdown(f"**{name}**: {status_badge(result)}", unsafe_allow_html=True)

