"""CSS injection and theming for the dashboard."""

import streamlit as st


def inject_custom_css():
    """Inject custom CSS for KPI cards, status badges, and layout."""
    st.markdown(
        """
        <style>
        /* KPI Cards */
        .kpi-card {
            background: linear-gradient(135deg, #1a1f2e 0%, #252b3b 100%);
            border: 1px solid #2d3548;
            border-radius: 12px;
            padding: 1.2rem 1.5rem;
            text-align: center;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .kpi-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 20px rgba(0, 212, 255, 0.15);
        }
        .kpi-value {
            font-size: 2.2rem;
            font-weight: 700;
            color: #00d4ff;
            margin: 0.3rem 0;
        }
        .kpi-label {
            font-size: 0.85rem;
            color: #8899aa;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        /* Status Badges */
        .badge {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
            letter-spacing: 0.03em;
        }
        .badge-green {
            background: rgba(0, 200, 83, 0.15);
            color: #00c853;
            border: 1px solid rgba(0, 200, 83, 0.3);
        }
        .badge-red {
            background: rgba(255, 82, 82, 0.15);
            color: #ff5252;
            border: 1px solid rgba(255, 82, 82, 0.3);
        }
        .badge-yellow {
            background: rgba(255, 193, 7, 0.15);
            color: #ffc107;
            border: 1px solid rgba(255, 193, 7, 0.3);
        }
        .badge-blue {
            background: rgba(0, 212, 255, 0.15);
            color: #00d4ff;
            border: 1px solid rgba(0, 212, 255, 0.3);
        }
        .badge-gray {
            background: rgba(158, 158, 158, 0.15);
            color: #9e9e9e;
            border: 1px solid rgba(158, 158, 158, 0.3);
        }

        /* Service Health Cards */
        .health-card {
            background: #1a1f2e;
            border: 1px solid #2d3548;
            border-radius: 10px;
            padding: 1rem;
            margin-bottom: 0.5rem;
        }
        .health-card-ok {
            border-left: 4px solid #00c853;
        }
        .health-card-down {
            border-left: 4px solid #ff5252;
        }
        .health-card-degraded {
            border-left: 4px solid #ffc107;
        }

        /* Pipeline Flow */
        .pipeline-flow {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0;
            padding: 1rem 0;
        }
        .pipeline-stage {
            background: linear-gradient(135deg, #1a1f2e 0%, #252b3b 100%);
            border: 1px solid #2d3548;
            border-radius: 12px;
            padding: 1rem 1.2rem;
            text-align: center;
            min-width: 110px;
            flex: 1;
            max-width: 160px;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .pipeline-stage:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 16px rgba(0, 212, 255, 0.12);
        }
        .pipeline-count {
            font-size: 1.8rem;
            font-weight: 700;
            color: #00d4ff;
            line-height: 1.2;
        }
        .pipeline-label {
            font-size: 0.75rem;
            color: #8899aa;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            margin-top: 0.2rem;
        }
        .pipeline-arrow {
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 0 0.3rem;
            flex-shrink: 0;
        }

        /* Approval Buttons */
        .approve-btn {
            background: rgba(0, 200, 83, 0.2);
            color: #00c853;
            border: 1px solid #00c853;
            padding: 0.5rem 1.5rem;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
        }
        .reject-btn {
            background: rgba(255, 82, 82, 0.2);
            color: #ff5252;
            border: 1px solid #ff5252;
            padding: 0.5rem 1.5rem;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
        }

        /* Severity cards */
        .severity-critical {
            border-left: 4px solid #ff5252;
            background: rgba(255, 82, 82, 0.05);
            padding: 0.8rem 1rem;
            border-radius: 0 8px 8px 0;
            margin-bottom: 0.5rem;
        }
        .severity-warning {
            border-left: 4px solid #ffc107;
            background: rgba(255, 193, 7, 0.05);
            padding: 0.8rem 1rem;
            border-radius: 0 8px 8px 0;
            margin-bottom: 0.5rem;
        }
        .severity-info {
            border-left: 4px solid #00d4ff;
            background: rgba(0, 212, 255, 0.05);
            padding: 0.8rem 1rem;
            border-radius: 0 8px 8px 0;
            margin-bottom: 0.5rem;
        }

        /* Sidebar styling */
        [data-testid="stSidebar"] {
            background: #0a0e14;
        }

        /* Activity table */
        .activity-table {
            width: 100%;
            border-collapse: collapse;
        }
        .activity-table th {
            text-align: left;
            color: #8899aa;
            padding: 0.5rem;
            border-bottom: 1px solid #2d3548;
            font-size: 0.8rem;
            text-transform: uppercase;
        }
        .activity-table td {
            padding: 0.5rem;
            border-bottom: 1px solid #1a1f2e;
            font-size: 0.9rem;
        }
        /* Disable typing in all selectbox dropdowns */
        .stSelectbox input,
        .stSelectbox div[data-baseweb="select"] input,
        div[data-baseweb="select"] input[aria-autocomplete] {
            caret-color: transparent !important;
            color: transparent !important;
            width: 0 !important;
            min-width: 0 !important;
            padding: 0 !important;
            position: absolute !important;
        }
        .stSelectbox div[data-baseweb="select"],
        div[data-baseweb="select"] > div {
            cursor: pointer !important;
        }
        /* Force all dropdowns to open downward */
        .stSelectbox div[data-baseweb="popover"],
        div[data-baseweb="popover"][data-placement] {
            top: 100% !important;
            bottom: auto !important;
            transform: none !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def kpi_card(label: str, value, icon: str = "") -> str:
    """Return HTML for a KPI card.

    icon can be raw HTML (SVG) or a plain emoji string.
    """
    if icon:
        # If icon starts with '<', it's already HTML (SVG); otherwise wrap as emoji
        if icon.strip().startswith("<"):
            icon_html = f'<div style="margin-bottom:0.3rem">{icon}</div>'
        else:
            icon_html = f'<div style="font-size:1.5rem">{icon}</div>'
    else:
        icon_html = ""
    return f"""
    <div class="kpi-card">
        {icon_html}
        <div class="kpi-value">{value}</div>
        <div class="kpi-label">{label}</div>
    </div>
    """


def status_badge(status: str) -> str:
    """Return HTML for a colored status badge."""
    mapping = {
        "operational": ("badge-green", "Operational"),
        "ok": ("badge-green", "OK"),
        "success": ("badge-green", "Success"),
        "approved": ("badge-green", "Approved"),
        "done": ("badge-green", "Done"),
        "degraded": ("badge-yellow", "Degraded"),
        "warning": ("badge-yellow", "Warning"),
        "pending": ("badge-yellow", "Pending"),
        "unavailable": ("badge-red", "Unavailable"),
        "down": ("badge-red", "Down"),
        "error": ("badge-red", "Error"),
        "failed": ("badge-red", "Failed"),
        "rejected": ("badge-red", "Rejected"),
        "timeout": ("badge-red", "Timeout"),
        "unknown": ("badge-gray", "Unknown"),
    }
    key = status.lower().strip() if status else "unknown"
    cls, label = mapping.get(key, ("badge-gray", status.title()))
    return f'<span class="badge {cls}">{label}</span>'


def pipeline_flow_html(counts: dict) -> str:
    """Return HTML for the pipeline flow visualization."""
    from utils.icons import lucide

    stages = [
        ("Inbox", counts.get("Inbox", 0), "inbox", "primary"),
        ("Needs Action", counts.get("Needs_Action", 0), "clipboard-list", "warning"),
        ("Plans", counts.get("Plans", 0), "file-text", "primary"),
        ("Pending Approval", counts.get("Pending_Approval", 0), "hourglass", "warning"),
        ("Done", counts.get("Done", 0), "check-circle", "success"),
    ]
    cards = []
    for i, (label, count, icon_name, color) in enumerate(stages):
        cards.append(
            f'<div class="pipeline-stage">'
            f'<div style="margin-bottom:0.4rem">{lucide(icon_name, 20, color)}</div>'
            f'<div class="pipeline-count">{count}</div>'
            f'<div class="pipeline-label">{label}</div>'
            f'</div>'
        )
        if i < len(stages) - 1:
            cards.append(
                '<div class="pipeline-arrow">'
                f'{lucide("chevron-right", 22, "muted")}'
                '</div>'
            )
    return '<div class="pipeline-flow">' + ''.join(cards) + '</div>'


def render_sidebar_branding():
    """Add AI Employee logo and caption to sidebar bottom."""
    from utils.icons import lucide

    st.sidebar.markdown(
        '<div style="display:inline-flex;align-items:center;gap:6px;"><span style="position:relative;top:-4px;">'
        + lucide("bot", 22, "primary")
        + '</span> <strong style="font-size:1.2rem;">AI Employee</strong></div>',
        unsafe_allow_html=True,
    )
    st.sidebar.caption("Your Personal AI Assistant")


def auto_refresh_sidebar(key_prefix: str = "ar") -> tuple:
    """Render auto-refresh toggle and interval in sidebar.

    Returns (enabled: bool, interval_seconds: int).
    Call st_autorefresh() in the page body using the returned values.
    """
    enabled_key = f"{key_prefix}_enabled"
    interval_key = f"{key_prefix}_interval"

    if enabled_key not in st.session_state:
        st.session_state[enabled_key] = True
    if interval_key not in st.session_state:
        st.session_state[interval_key] = 30

    st.sidebar.markdown(
        '<small style="color:#888;">Auto-Refresh</small>',
        unsafe_allow_html=True,
    )
    enabled = st.sidebar.toggle(
        "Auto-Refresh",
        value=st.session_state[enabled_key],
        key=f"{key_prefix}_toggle",
    )
    st.session_state[enabled_key] = enabled

    interval = st.sidebar.selectbox(
        "Every",
        options=[15, 30, 60, 120],
        index=[15, 30, 60, 120].index(st.session_state[interval_key]),
        format_func=lambda x: f"{x}s" if x < 60 else f"{x//60}m",
        key=f"{key_prefix}_intv",
        disabled=not enabled,
    )
    st.session_state[interval_key] = interval

    return enabled, interval
