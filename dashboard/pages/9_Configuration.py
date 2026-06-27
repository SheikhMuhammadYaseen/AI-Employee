"""Configuration — Service connections, watchers, and preferences."""

import sys
import os
import json
import subprocess
from pathlib import Path
from datetime import datetime, timezone

import streamlit as st
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils.path_setup import PROJECT_ROOT, VAULT_PATH
from utils.theme import inject_custom_css, kpi_card, status_badge, render_sidebar_branding
from utils.formatters import time_ago
from utils.vault_reader import count_items_by_folder
from utils.icons import lucide, icon_text, service_icon
from utils.env_manager import read_env, write_env, is_placeholder
from utils.connection_tester import test_connection

st.set_page_config(page_title="Configuration", page_icon="⚙️", layout="wide")
inject_custom_css()
render_sidebar_branding()

# --- src/ imports ---
try:
    from src.health.service_health import ServiceHealthTracker
except ImportError:
    ServiceHealthTracker = None

try:
    from src.mcp.config import get_config
except ImportError:
    get_config = None

st.markdown(
    icon_text("settings", "Configuration", 28, "primary", "h1")
    .replace("<svg", "<svg style='position:relative; top:-3px;'"),
    unsafe_allow_html=True
)

# ==========================================================
# Connected Services
# ==========================================================
st.subheader("Connected Services")
st.caption("Status of services your AI Employee uses")

SERVICE_CONFIG = {
    "gmail": {
        "label": "Email (Gmail)",
        "icon": service_icon("gmail", 18, "primary"),
        "env_keys": ["GMAIL_ADDRESS", "GMAIL_APP_PASSWORD"],
        "fields": [
            {"key": "GMAIL_ADDRESS", "label": "Gmail Address", "type": "text", "placeholder": "you@gmail.com"},
            {"key": "GMAIL_APP_PASSWORD", "label": "App Password", "type": "password",
             "placeholder": "16-character app password",
             "help": "Generate at myaccount.google.com → Security → App Passwords"},
        ],
        "description": "Reads and sends email on your behalf",
    },
    "odoo": {
        "label": "Accounting (Odoo)",
        "icon": service_icon("odoo", 18, "primary"),
        "env_keys": ["ODOO_URL", "ODOO_DB", "ODOO_USER", "ODOO_PASSWORD"],
        "fields": [
            {"key": "ODOO_URL", "label": "Odoo URL", "type": "text", "placeholder": "http://localhost:8069"},
            {"key": "ODOO_DB", "label": "Database Name", "type": "text", "placeholder": "odoo_gold"},
            {"key": "ODOO_USER", "label": "Username", "type": "text", "placeholder": "admin"},
            {"key": "ODOO_PASSWORD", "label": "Password", "type": "password", "placeholder": "admin password",
             "help": "Your Odoo instance URL, database name, and admin credentials"},
        ],
        "description": "Manages invoices, payments, and financial reports",
    },
    "linkedin": {
        "label": "LinkedIn",
        "icon": service_icon("linkedin", 18, "primary"),
        "env_keys": ["LINKEDIN_ACCESS_TOKEN", "LINKEDIN_AUTHOR_ID"],
        "fields": [
            {"key": "LINKEDIN_ACCESS_TOKEN", "label": "Access Token", "type": "password",
             "placeholder": "OAuth 2.0 token",
             "help": "Create app at linkedin.com/developers → OAuth 2.0 token with w_member_social scope"},
            {"key": "LINKEDIN_AUTHOR_ID", "label": "Author ID", "type": "text", "placeholder": "urn:li:person:..."},
        ],
        "description": "Posts business content to generate sales leads",
    },
    "mastodon": {
        "label": "Mastodon",
        "icon": service_icon("mastodon", 18, "primary"),
        "env_keys": ["MASTODON_INSTANCE_URL", "MASTODON_ACCESS_TOKEN"],
        "fields": [
            {"key": "MASTODON_INSTANCE_URL", "label": "Instance URL", "type": "text",
             "placeholder": "https://mastodon.social"},
            {"key": "MASTODON_ACCESS_TOKEN", "label": "Access Token", "type": "password",
             "placeholder": "Your access token",
             "help": "Go to your instance → Preferences → Development → New Application"},
        ],
        "description": "Posts to your Mastodon account",
    },
    "facebook": {
        "label": "Facebook",
        "icon": service_icon("facebook", 18, "primary"),
        "env_keys": ["META_PAGE_ID", "META_PAGE_ACCESS_TOKEN"],
        "fields": [
            {"key": "META_PAGE_ID", "label": "Page ID", "type": "text", "placeholder": "123456789"},
            {"key": "META_PAGE_ACCESS_TOKEN", "label": "Page Access Token", "type": "password",
             "placeholder": "Page token from Meta Business Suite",
             "help": "Meta Business Suite → Settings → Page Access Token"},
        ],
        "description": "Posts to your Facebook page",
    },
    "instagram": {
        "label": "Instagram",
        "icon": service_icon("instagram", 18, "primary"),
        "env_keys": ["META_IG_USER_ID", "META_PAGE_ACCESS_TOKEN"],
        "fields": [
            {"key": "META_IG_USER_ID", "label": "IG Business User ID", "type": "text",
             "placeholder": "17841400000000"},
            {"key": "META_PAGE_ACCESS_TOKEN", "label": "Page Access Token", "type": "password",
             "placeholder": "Same Meta token as Facebook",
             "help": "Same Meta token as Facebook + your IG Business User ID"},
        ],
        "description": "Posts to your Instagram account",
    },
    "x_twitter": {
        "label": "X (Twitter)",
        "icon": service_icon("x_twitter", 18, "primary"),
        "env_keys": ["X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_SECRET"],
        "fields": [
            {"key": "X_API_KEY", "label": "API Key", "type": "password", "placeholder": "Consumer key"},
            {"key": "X_API_SECRET", "label": "API Secret", "type": "password", "placeholder": "Consumer secret"},
            {"key": "X_ACCESS_TOKEN", "label": "Access Token", "type": "password", "placeholder": "OAuth access token"},
            {"key": "X_ACCESS_SECRET", "label": "Access Secret", "type": "password", "placeholder": "OAuth access secret",
             "help": "developer.twitter.com → Projects → Keys and Tokens"},
        ],
        "description": "Posts tweets on your behalf",
    },
    "whatsapp": {
        "label": "WhatsApp",
        "icon": service_icon("whatsapp", 18, "primary"),
        "env_keys": [],
        "fields": [],
        "description": "Monitors WhatsApp Web for urgent messages",
        "is_whatsapp": True,
    },
}

# Load env to check what's configured
env_path = PROJECT_ROOT / ".env"
env_values = read_env(env_path)

@st.cache_data(ttl=30)
def _load_health_data():
    if ServiceHealthTracker is None:
        return {}
    try:
        tracker = ServiceHealthTracker(str(VAULT_PATH))
        return tracker.get_all_health()
    except Exception:
        return {}


# Load health data
health = _load_health_data()

# Demo health for showcase
_is_settings_demo = not health and not env_values
if _is_settings_demo:
    st.caption("Demo data — configure .env credentials to connect real services")
    health = {
        "gmail": {"status": "operational"}, "odoo": {"status": "operational"},
        "linkedin": {"status": "operational"}, "mastodon": {"status": "operational"},
        "facebook": {"status": "operational"}, "instagram": {"status": "degraded"},
        "x_twitter": {"status": "unavailable"},
    }

def _check_watcher_status(watcher_name: str) -> dict:
    """Check if a watcher is running via its lock file."""
    lock_path = VAULT_PATH / f".watcher_{watcher_name}.lock"
    state_path = VAULT_PATH / f".watcher_state_{watcher_name}.json"

    result = {"running": False, "pid": None, "last_poll": None, "processed": 0}

    # Check lock file
    if lock_path.exists():
        try:
            pid = int(lock_path.read_text().strip())
            try:
                os.kill(pid, 0)
                result["running"] = True
                result["pid"] = pid
            except (OSError, ProcessLookupError):
                pass  # stale lock
        except (ValueError, OSError):
            pass

    # Check state file
    if state_path.exists():
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
            result["last_poll"] = state.get("last_poll")
            result["processed"] = len(state.get("processed_ids", []))
        except Exception:
            pass

    return result


svc_keys = list(SERVICE_CONFIG.keys())
for i in range(0, len(svc_keys), 3):
    row = svc_keys[i:i + 3]
    cols = st.columns(3)
    for col, svc_key in zip(cols, row):
        svc = SERVICE_CONFIG[svc_key]
        svc_health = health.get(svc_key, {})
        svc_status = svc_health.get("status", "unknown")
        last_ok = svc_health.get("last_ok")

        # Check if configured (env keys present OR health tracker shows operational OR demo mode)
        is_configured = (
            bool(svc["env_keys"]) and all(
                not is_placeholder(env_values.get(k, ""))
                for k in svc["env_keys"]
            )
        ) or svc_status in ("operational", "degraded", "unavailable")

        if svc_status == "operational":
            card_class = "health-card-ok"
            config_label = "Connected"
        elif svc_status == "degraded":
            card_class = "health-card-degraded"
            config_label = "Degraded"
        elif svc_status == "unavailable":
            card_class = "health-card-down"
            config_label = "Unavailable"
        elif is_configured:
            card_class = "health-card-degraded"
            config_label = "Configured but offline"
        else:
            card_class = "health-card-down"
            config_label = "Not configured"

        with col:
            badge = status_badge(svc_status if is_configured else 'unknown')
            last_active_text = time_ago(str(last_ok)) if last_ok else '—'
            last_active_line = '<div>Last active: ' + last_active_text + '</div>'

            card_html = (
                '<div class="health-card ' + card_class + '">'
                '<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.5rem;">'
                '<strong style="display:inline-flex;align-items:center;gap:6px;">' + svc['icon'] + ' ' + svc['label'] + '</strong>'
                + badge +
                '</div>'
                '<div style="font-size:0.85rem; color:#8899aa;">'
                '<div>' + svc['description'] + '</div>'
                '<div style="margin-top:0.3rem;">Status: <strong>' + config_label + '</strong></div>'
                + last_active_line +
                '</div>'
                '</div>'
            )
            st.markdown(card_html, unsafe_allow_html=True)

            # --- Configure expander ---
            if svc.get("is_whatsapp"):
                with st.expander(f"Configure {svc['label']}", expanded=False):
                    st.info(
                        "WhatsApp uses browser-based QR code scanning — no API credentials needed.\n\n"
                        "**Setup steps:**\n"
                        "1. Start the WhatsApp Watcher from the Watchers section below\n"
                        "2. Scan the QR code with your phone\n"
                        "3. The watcher will monitor for new messages"
                    )
                    watcher_status = _check_watcher_status("whatsapp")
                    if watcher_status["running"]:
                        st.success(f"WhatsApp Watcher is running (PID {watcher_status['pid']})")
                    else:
                        st.caption("WhatsApp Watcher is not running. Start it in the Watchers section below.")
            elif svc.get("fields"):
                with st.expander(f"Configure {svc['label']}", expanded=False):
                    field_values = {}
                    for field in svc["fields"]:
                        current = env_values.get(field["key"], "")
                        display_val = current if not is_placeholder(current) else ""
                        input_type = "password" if field["type"] == "password" else "default"
                        field_values[field["key"]] = st.text_input(
                            field["label"],
                            value=display_val,
                            type=input_type,
                            placeholder=field.get("placeholder", ""),
                            key=f"cfg_{svc_key}_{field['key']}",
                        )
                        if field.get("help"):
                            st.caption(field["help"])

                    btn_col1, btn_col2 = st.columns(2)
                    with btn_col1:
                        if st.button(
                            "Save & Test Connection",
                            key=f"save_test_{svc_key}",
                            type="primary",
                            use_container_width=True,
                        ):
                            # Save to .env
                            updates = {k: v for k, v in field_values.items() if v.strip()}
                            if updates:
                                try:
                                    write_env(env_path, updates)
                                    st.success("Credentials saved to .env")
                                    # Run connection test
                                    with st.spinner("Testing connection..."):
                                        result = test_connection(svc_key, {**env_values, **updates})
                                    if result["success"]:
                                        st.success(f"Connection successful! {result['message']}")
                                        if result.get("details"):
                                            st.caption(result["details"])
                                    else:
                                        st.error(f"Connection failed: {result['message']}")
                                        if result.get("details"):
                                            st.caption(result["details"])
                                except Exception as e:
                                    st.error(f"Could not save: {e}")
                            else:
                                st.warning("Enter at least one credential before saving.")

                    with btn_col2:
                        if st.button(
                            "Clear Credentials",
                            key=f"clear_creds_{svc_key}",
                            use_container_width=True,
                        ):
                            clear_updates = {f["key"]: "" for f in svc["fields"]}
                            try:
                                write_env(env_path, clear_updates)
                                st.success("Credentials cleared.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Could not clear: {e}")

st.divider()

# ==========================================================
# Watchers — Start / Stop / Status
# ==========================================================
st.markdown(
    icon_text("activity", "Watchers", 24, "warning", "h2")
    .replace("<svg", "<svg style='position:relative; top:-2px;'"),
    unsafe_allow_html=True,
)
st.caption("Monitor and control background watchers that bring items into your inbox")

WATCHERS = {
    "gmail": {
        "label": "Gmail Watcher",
        "icon": service_icon("gmail", 20, "primary"),
        "description": "Polls Gmail for new unread emails",
        "script": "src/watchers/gmail_watcher.py",
        "env_keys": ["GMAIL_ADDRESS"],
    },
    "whatsapp": {
        "label": "WhatsApp Watcher",
        "icon": service_icon("whatsapp", 20, "primary"),
        "description": "Monitors WhatsApp Web for urgent messages",
        "script": "src/watchers/whatsapp_watcher.py",
        "env_keys": [],
    },
}

# Demo watcher data for showcase
DEMO_WATCHER_STATUS = {
    "gmail": {"running": True, "pid": 12847, "last_poll": "2026-02-17T14:25:00Z", "processed": 47},
    "whatsapp": {"running": False, "pid": None, "last_poll": "2026-02-16T09:30:00Z", "processed": 8},
}

w_cols = st.columns(2)
for col, (watcher_key, watcher_info) in zip(w_cols, WATCHERS.items()):
    with col:
        status = _check_watcher_status(watcher_key)

        # Use demo data if no real status
        _is_watcher_demo = not status["running"] and not status["last_poll"]
        if _is_watcher_demo and watcher_key in DEMO_WATCHER_STATUS:
            status = DEMO_WATCHER_STATUS[watcher_key]

        if status["running"]:
            card_class = "health-card-ok"
            status_text = f"Running (PID {status['pid']})"
            badge_html = status_badge("operational")
        else:
            card_class = "health-card-degraded"
            status_text = "Ready to start"
            badge_html = status_badge("pending")

        last_poll_text = time_ago(status["last_poll"]) if status["last_poll"] else "Not yet started"

        st.markdown(
            f'<div class="health-card {card_class}" style="min-height:120px">'
            f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.5rem">'
            f'<strong style="display:inline-flex;align-items:center;gap:6px">'
            f'{watcher_info["icon"]} {watcher_info["label"]}</strong>'
            f'{badge_html}'
            f'</div>'
            f'<div style="font-size:0.85rem;color:#8899aa">'
            f'<div>{watcher_info["description"]}</div>'
            f'<div style="margin-top:0.3rem">Status: <strong>{status_text}</strong></div>'
            f'<div>Last poll: {last_poll_text}</div>'
            f'<div>Processed: {status["processed"]} items</div>'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # Action buttons
        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            if status["running"]:
                if st.button(
                    "Stop",
                    key=f"stop_{watcher_key}",
                    type="secondary",
                    use_container_width=True,
                ):
                    try:
                        lock_path = VAULT_PATH / f".watcher_{watcher_key}.lock"
                        pid = int(lock_path.read_text().strip())
                        if sys.platform == "win32":
                            subprocess.run(["taskkill", "/F", "/PID", str(pid)],
                                           capture_output=True, timeout=10)
                        else:
                            os.kill(pid, 15)  # SIGTERM
                        lock_path.unlink(missing_ok=True)
                        st.success(f"{watcher_info['label']} stopped.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Could not stop: {e}")
            else:
                # Check if credentials are configured
                is_configured = all(
                    not is_placeholder(env_values.get(k, ""))
                    for k in watcher_info["env_keys"]
                ) if watcher_info["env_keys"] else True

                if st.button(
                    "Start",
                    key=f"start_{watcher_key}",
                    type="primary",
                    use_container_width=True,
                    disabled=not is_configured,
                ):
                    try:
                        script_path = PROJECT_ROOT / watcher_info["script"]
                        cmd = [
                            sys.executable, str(script_path),
                            "--vault-path", str(VAULT_PATH),
                        ]
                        subprocess.Popen(
                            cmd,
                            cwd=str(PROJECT_ROOT),
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
                        )
                        st.success(f"{watcher_info['label']} starting...")
                        import time
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Could not start: {e}")

                if not is_configured:
                    st.caption(f"Configure {', '.join(watcher_info['env_keys'])} in .env first")

        with btn_col2:
            # Clean stale lock
            lock_path = VAULT_PATH / f".watcher_{watcher_key}.lock"
            if lock_path.exists() and not status["running"]:
                if st.button(
                    "Clear Lock",
                    key=f"clear_{watcher_key}",
                    use_container_width=True,
                ):
                    lock_path.unlink(missing_ok=True)
                    st.success("Stale lock removed.")
                    st.rerun()

st.divider()

# ==========================================================
# Automation Schedule
# ==========================================================
st.subheader("Automation Schedule")
st.caption("Control how often your AI Employee runs background tasks")

CONFIG_PATH = PROJECT_ROOT / "src" / "scheduling" / "scheduler_config.json"

if CONFIG_PATH.exists():
    try:
        config_data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        config_data = {}
else:
    config_data = {
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

# Friendly scheduler settings
current_interval = config_data.get("interval_minutes", 5)
components = config_data.get("components", {})

COMPONENT_LABELS = {
    "approval_checker": ("Approval Checker", "Reviews and processes approved/rejected items"),
    "inbox_watcher": ("Inbox Watcher", "Monitors for new incoming items"),
    "health_monitor": ("Health Monitor", "Checks service connectivity"),
}

new_interval = st.number_input(
    "Check every (minutes)",
    min_value=1,
    max_value=60,
    value=current_interval,
    step=1,
)
st.caption(f"Your AI Employee checks for new work every **{new_interval} minutes**.")

# Task toggles
st.markdown("**Automated Tasks**")
updated_components = {}
for comp_name, comp_config in components.items():
    label, desc = COMPONENT_LABELS.get(comp_name, (comp_name.replace("_", " ").title(), ""))
    enabled = st.toggle(
        f"{label}",
        value=comp_config.get("enabled", False),
        help=desc,
        key=f"toggle_{comp_name}",
    )
    updated_components[comp_name] = {**comp_config, "enabled": enabled}

if st.button("Save Schedule", type="primary", icon=":material/save:"):
    try:
        config_data["interval_minutes"] = new_interval
        config_data["components"] = updated_components
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text(json.dumps(config_data, indent=2), encoding="utf-8")
        st.success("Schedule saved!")
    except Exception as e:
        st.error(f"Could not save: {e}")

st.divider()

# ==========================================================
# Workspace Overview
# ==========================================================
st.subheader("Workspace Overview")

vault_counts = count_items_by_folder(VAULT_PATH)
total_items = sum(vault_counts.values()) or (22 if _is_settings_demo else 0)

cols = st.columns(3)
cols[0].markdown(kpi_card("Total Items", total_items, lucide("folder", 28, "primary")), unsafe_allow_html=True)

services_online = sum(1 for s in health.values() if isinstance(s, dict) and s.get("status") == "operational")
cols[1].markdown(kpi_card("Services Online", services_online, lucide("circle-check", 28, "success")), unsafe_allow_html=True)

enabled_tasks = sum(1 for c in components.values() if c.get("enabled", False))
cols[2].markdown(kpi_card("Active Tasks", enabled_tasks, lucide("zap", 28, "warning")), unsafe_allow_html=True)

st.markdown("**Items by Stage**")
stage_df = pd.DataFrame([
    {"Stage": k.replace("_", " "), "Items": v}
    for k, v in vault_counts.items()
])
st.dataframe(stage_df, use_container_width=True, hide_index=True)
