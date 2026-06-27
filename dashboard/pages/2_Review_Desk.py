"""Review Desk — Review and approve or reject pending actions."""

import sys
import re
from pathlib import Path
from datetime import datetime, timezone, timedelta

import streamlit as st
import frontmatter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils.path_setup import VAULT_PATH
from utils.theme import inject_custom_css, status_badge, render_sidebar_branding
from utils.formatters import format_timestamp, time_ago, truncate, friendly_name
from utils.vault_reader import list_vault_items
from utils.icons import lucide, icon_text, service_icon

st.set_page_config(page_title="Review Desk", page_icon="✅", layout="wide")
inject_custom_css()
render_sidebar_branding()

# --- src/ imports ---
try:
    from src.approval.checker import check_approvals
except ImportError:
    check_approvals = None

st.markdown(
    icon_text("check-circle", "Review Desk", 28, "success", "h1")
    .replace("<svg", "<svg style='position:relative; top:-3px;'"),
    unsafe_allow_html=True
)
st.caption("Review actions your AI Employee wants to take on your behalf")

# Friendly action labels
ACTION_LABELS = {
    "email_send": ("Send Email", service_icon("gmail", 18, "primary")),
    "linkedin_post": ("Post to LinkedIn", service_icon("linkedin", 18, "primary")),
    "mastodon_post": ("Post to Mastodon", service_icon("mastodon", 18, "primary")),
    "facebook_post": ("Post to Facebook", service_icon("facebook", 18, "primary")),
    "instagram_post": ("Post to Instagram", service_icon("instagram", 18, "primary")),
    "x_post": ("Post to X", service_icon("x_twitter", 18, "primary")),
    "create_invoice": ("Create Invoice", lucide("dollar-sign", 18, "success")),
    "record_payment": ("Record Payment", lucide("credit-card", 18, "primary")),
    "action": ("Execute Action", lucide("zap", 18, "warning")),
}

# --- Load pending items ---
_all_pending = list_vault_items(VAULT_PATH / "Pending_Approval")


def _is_already_decided(item: dict) -> bool:
    """Check if an item already has Approved or Rejected checked."""
    body = item.get("body", "")
    return bool(
        re.search(r"\[[\u2705x]\]\s*Approved", body, re.IGNORECASE)
        or re.search(r"\[[\u2705x]\]\s*Rejected", body, re.IGNORECASE)
    )


pending_items = [it for it in _all_pending if not _is_already_decided(it)]
decided_items = [it for it in _all_pending if _is_already_decided(it)]

# --- Dynamic demo dates (always relative to now, never stale) ---
_now = datetime.now(timezone.utc)
_demo_ts = [
    (_now - timedelta(hours=1, minutes=30)).isoformat(),    # 1.5h ago
    (_now - timedelta(hours=5, minutes=45)).isoformat(),    # ~6h ago (HIGH priority)
    (_now - timedelta(hours=8)).isoformat(),                # 8h ago
    (_now - timedelta(hours=14, minutes=15)).isoformat(),   # ~14h ago
]
_demo_fmt = [
    (_now - timedelta(hours=1, minutes=30)).strftime("%b %d, %Y at %I:%M %p"),
    (_now - timedelta(hours=5, minutes=45)).strftime("%b %d, %Y at %I:%M %p"),
    (_now - timedelta(hours=8)).strftime("%b %d, %Y at %I:%M %p"),
    (_now - timedelta(hours=14, minutes=15)).strftime("%b %d, %Y at %I:%M %p"),
]
_email_orig_ts = (_now - timedelta(hours=20)).strftime("%b %d, %Y at %I:%M %p")

DEMO_PENDING = [
    {
        "mcp_tool": "linkedin_post",
        "subject": "AI trends for business leaders — 5 predictions for 2026",
        "target": "",
        "priority": "normal",
        "created_date": _demo_ts[0],
        "body": (
            "### Social Post: LinkedIn\n\n"
            "| Detail | Value |\n"
            "|--------|-------|\n"
            "| **Platform** | LinkedIn |\n"
            "| **Tone** | Thought Leadership |\n"
            "| **Characters** | 412 / 3,000 |\n"
            f"| **Generated** | {_demo_fmt[0]} |\n\n"
            "---\n\n"
            "#### Preview\n\n"
            "The AI landscape is shifting fast. Here are 5 trends every business leader "
            "needs to watch in 2026:\n\n"
            "1. **Autonomous AI employees** handling routine operations end-to-end — from inbox "
            "triage to invoice management\n"
            "2. **AI-first accounting** — real-time financial reporting without manual data entry\n"
            "3. **Multi-platform social automation** — one brief, five platforms, zero copy-paste\n"
            "4. **Natural language interfaces** — talk to your business tools like you talk to a colleague\n"
            "5. **Predictive inbox management** — AI that knows which emails need your attention "
            "before you do\n\n"
            "At our company, we've already implemented all five. The result? "
            "85% reduction in routine tasks and 3x faster response times.\n\n"
            "Which of these is your organization investing in? I'd love to hear your perspective.\n\n"
            "#AI #BusinessStrategy #Automation #Leadership #FutureOfWork\n\n"
            "---\n\n"
            "#### Decision\n\n"
            "- [ ] Approved\n"
            "- [ ] Rejected\n"
        ),
    },
    {
        "mcp_tool": "email_send",
        "subject": "Reply to CloudTech Solutions — Partnership inquiry",
        "target": "sarah.chen@cloudtech.io",
        "priority": "high",
        "created_date": _demo_ts[1],
        "body": (
            "### Email Reply\n\n"
            "| Detail | Value |\n"
            "|--------|-------|\n"
            "| **To** | sarah.chen@cloudtech.io |\n"
            "| **Subject** | Re: Partnership Opportunity — AI Employee x CloudTech |\n"
            "| **Priority** | High |\n"
            f"| **Original received** | {_email_orig_ts} |\n\n"
            "---\n\n"
            "#### Original Message (from Sarah Chen, VP Partnerships)\n\n"
            "> Hi there,\n>\n"
            "> I came across your AI Employee platform and was impressed by the multi-service "
            "automation approach. At CloudTech Solutions, we provide cloud infrastructure "
            "to 2,000+ SMBs and I think there's a strong partnership opportunity here.\n>\n"
            "> Would you be open to exploring an integration where our clients could "
            "deploy your AI Employee directly on our platform?\n>\n"
            "> Looking forward to hearing from you.\n>\n"
            "> — Sarah Chen, VP of Partnerships, CloudTech Solutions\n\n"
            "---\n\n"
            "#### Drafted Reply\n\n"
            "Hi Sarah,\n\n"
            "Thank you for reaching out — we've been following CloudTech's growth in "
            "the SMB cloud space and this sounds like a great fit.\n\n"
            "I'd love to schedule a call to explore:\n\n"
            "- **Integration architecture** — deploying AI Employee on CloudTech infrastructure\n"
            "- **Joint go-to-market** — bundling AI automation for your 2,000+ SMB clients\n"
            "- **Technical requirements** — API compatibility and security considerations\n"
            "- **Revenue model** — partnership pricing and revenue sharing structure\n\n"
            "Would next Tuesday at 2:00 PM EST work for a 30-minute introductory call? "
            "I'll send a calendar invite with a Zoom link.\n\n"
            "Best regards,\n"
            "AI Employee on behalf of the team\n\n"
            "---\n\n"
            "#### Decision\n\n"
            "- [ ] Approved\n"
            "- [ ] Rejected\n"
        ),
    },
    {
        "mcp_tool": "mastodon_post",
        "subject": "Weekly automation results — behind the numbers",
        "target": "",
        "priority": "normal",
        "created_date": _demo_ts[2],
        "body": (
            "### Social Post: Mastodon\n\n"
            "| Detail | Value |\n"
            "|--------|-------|\n"
            "| **Platform** | Mastodon |\n"
            "| **Tone** | Casual & Community-friendly |\n"
            "| **Characters** | 287 / 500 |\n"
            f"| **Generated** | {_demo_fmt[2]} |\n\n"
            "---\n\n"
            "#### Preview\n\n"
            "Our AI Employee's weekly report card:\n\n"
            "- 18 emails triaged and classified\n"
            "- 10 social posts across 4 platforms\n"
            "- 3 invoices created and sent\n"
            "- 2 partnership inquiries answered\n"
            "- 312 social engagements generated\n\n"
            "All of this happened autonomously while the team focused on product "
            "development and customer calls.\n\n"
            "The future of work isn't about replacing humans — it's about giving "
            "them superpowers.\n\n"
            "#Automation #AI #FutureOfWork #OpenSource\n\n"
            "---\n\n"
            "#### Decision\n\n"
            "- [ ] Approved\n"
            "- [ ] Rejected\n"
        ),
    },
    {
        "mcp_tool": "facebook_post",
        "subject": "Customer success story — Acme Corp saves 20 hours/week",
        "target": "",
        "priority": "normal",
        "created_date": _demo_ts[3],
        "body": (
            "### Social Post: Facebook\n\n"
            "| Detail | Value |\n"
            "|--------|-------|\n"
            "| **Platform** | Facebook Page |\n"
            "| **Tone** | Friendly & Engaging |\n"
            "| **Characters** | 478 / 5,000 |\n"
            f"| **Generated** | {_demo_fmt[3]} |\n\n"
            "---\n\n"
            "#### Preview\n\n"
            "Meet Acme Corp — one of our earliest adopters.\n\n"
            "Before AI Employee:\n"
            "- 20+ hours/week on email management\n"
            "- Manual invoice creation and follow-ups\n"
            "- Inconsistent social media presence\n"
            "- Missed partnership opportunities buried in inbox\n\n"
            "After 3 months with AI Employee:\n"
            "- Email response time: 4 hours \u2192 15 minutes\n"
            "- Invoice processing: fully automated\n"
            "- Social posts: 10/week across 4 platforms\n"
            "- 0 missed high-priority messages\n\n"
            "\"It's like having a tireless assistant who never sleeps and never "
            "forgets.\" \u2014 James Rodriguez, COO at Acme Corp\n\n"
            "Want similar results? Let's talk.\n\n"
            "---\n\n"
            "#### Decision\n\n"
            "- [ ] Approved\n"
            "- [ ] Rejected\n"
        ),
    },
]

if not pending_items:
    st.caption("Demo data — pending items will appear as your AI Employee generates drafts")
    st.markdown(f"**{len(DEMO_PENDING)} item(s) waiting for your decision**")

    # Demo stale warning — computed from the oldest demo item (14h 15m ago)
    st.warning("1 item has been waiting for 14 hours — please review it soon")

    st.divider()

    for idx, demo in enumerate(DEMO_PENDING):
        mcp_tool = demo["mcp_tool"]
        action_label, action_emoji = ACTION_LABELS.get(mcp_tool, (mcp_tool.replace("_", " ").title(), lucide("zap", 18, "warning")))
        priority_badge = '&nbsp;' + status_badge('warning') if demo["priority"] == 'high' else ''
        target_line = f'To: {demo["target"]} | ' if demo["target"] else ''
        received_str = f'{format_timestamp(demo["created_date"])} ({time_ago(demo["created_date"])})'

        card_html = (
            '<div class="health-card health-card-degraded" style="margin-bottom:1rem;">'
            '<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.5rem;">'
            f'<strong style="font-size:1.05rem;display:inline-flex;align-items:center;gap:6px;">{action_emoji} {action_label}</strong>'
            f'<div>{status_badge("pending")}{priority_badge}</div>'
            '</div>'
            f'<div style="font-size:0.9rem; margin-bottom:0.3rem;">{demo["subject"]}</div>'
            f'<div style="font-size:0.85rem; color:#8899aa;">{target_line}Received: {received_str}</div>'
            '</div>'
        )
        st.markdown(card_html, unsafe_allow_html=True)

        with st.expander("Preview content", expanded=False):
            st.markdown(demo["body"])

        col_approve, col_reject, col_spacer = st.columns([1, 1, 3])
        with col_approve:
            if st.button("Approve", key=f"demo_approve_{idx}", icon=":material/check:"):
                st.session_state[f"demo_result_{idx}"] = "approved"
                st.rerun()
        with col_reject:
            if st.button("Reject", key=f"demo_reject_{idx}", icon=":material/close:"):
                st.session_state[f"demo_result_{idx}"] = "rejected"
                st.rerun()

        # Show result if action was taken
        result_key = f"demo_result_{idx}"
        if st.session_state.get(result_key) == "approved":
            st.success(f"Approved! {demo['subject']} — will be executed via {action_label}.")
        elif st.session_state.get(result_key) == "rejected":
            st.error(f"Rejected. {demo['subject']} — archived to Done.")

        st.divider()

    # Process All Decisions button
    st.subheader("Process Decisions")
    st.caption("After approving or rejecting items above, click here to execute the actions.")
    if st.button("Process All Decisions", type="primary", icon=":material/refresh:", key="demo_process_all"):
        decided = sum(1 for i in range(len(DEMO_PENDING)) if st.session_state.get(f"demo_result_{i}"))
        if decided == 0:
            st.warning("No decisions made yet — approve or reject items above first.")
        else:
            with st.spinner("Processing your decisions..."):
                import time
                time.sleep(1)
            approved = sum(1 for i in range(len(DEMO_PENDING)) if st.session_state.get(f"demo_result_{i}") == "approved")
            rejected = sum(1 for i in range(len(DEMO_PENDING)) if st.session_state.get(f"demo_result_{i}") == "rejected")
            st.success("Done!")
            r_cols = st.columns(4)
            r_cols[0].metric("Executed", approved)
            r_cols[1].metric("Rejected", rejected)
            r_cols[2].metric("Still Pending", len(DEMO_PENDING) - decided)
            r_cols[3].metric("Issues", 0)

    st.divider()

    # Demo recent history
    st.subheader("Recent Approval History")
    st.caption("Completed approvals from the past week")
    import pandas as pd
    _d1 = (_now - timedelta(days=1)).strftime("%b %d")
    _d2 = (_now - timedelta(days=2)).strftime("%b %d")
    _d3 = (_now - timedelta(days=3)).strftime("%b %d")
    _d4 = (_now - timedelta(days=4)).strftime("%b %d")
    DEMO_HISTORY = [
        {"Action": "Post to LinkedIn", "Subject": "How we automated 85% of operations", "Result": "Approved", "Date": _d1},
        {"Action": "Send Email", "Subject": "Invoice follow-up to TechVentures", "Result": "Approved", "Date": _d1},
        {"Action": "Post to Facebook", "Subject": "Customer success story — Acme Corp", "Result": "Rejected", "Date": _d2},
        {"Action": "Post to Mastodon", "Subject": "Behind the scenes: building our AI", "Result": "Approved", "Date": _d2},
        {"Action": "Create Invoice", "Subject": "INV-2026-0340 for DesignStudio — $6,500", "Result": "Approved", "Date": _d3},
        {"Action": "Send Email", "Subject": "Weekly newsletter to subscriber list", "Result": "Approved", "Date": _d3},
        {"Action": "Post to Instagram", "Subject": "Weekly productivity tip", "Result": "Approved", "Date": _d4},
    ]
    st.dataframe(pd.DataFrame(DEMO_HISTORY), use_container_width=True, hide_index=True)
    st.stop()

st.markdown(f"**{len(pending_items)} item(s) waiting for your decision**")

# --- Stale item warning ---
now = datetime.now(timezone.utc)
for item in pending_items:
    created = item["metadata"].get("created_date", item["metadata"].get("created"))
    if created:
        try:
            created_dt = datetime.fromisoformat(str(created).replace("Z", "+00:00"))
            if created_dt.tzinfo is None:
                created_dt = created_dt.replace(tzinfo=timezone.utc)
            hours_old = (now - created_dt).total_seconds() / 3600
            if hours_old > 48:
                days_old = int(hours_old // 24)
                st.warning(f"1 item has been waiting for {days_old} days — please review it soon")
                break
            elif hours_old > 12:
                st.warning(f"1 item has been waiting for {int(hours_old)} hours — please review it soon")
                break
        except (ValueError, TypeError):
            pass

st.divider()

# --- Approval Cards ---
for idx, item in enumerate(pending_items):
    meta = item["metadata"]
    filename = item["filename"]

    # Get friendly names
    mcp_tool = meta.get("mcp_tool", meta.get("type", "action"))
    action_label, action_emoji = ACTION_LABELS.get(mcp_tool, (mcp_tool.replace("_", " ").title(), lucide("zap", 18, "warning")))

    target = meta.get("target", "")
    priority = meta.get("priority", "normal")
    created = meta.get("created_date", meta.get("created", ""))

    # Build a friendly title from the content
    subject = meta.get("subject", "")
    if not subject:
        subject = friendly_name(filename)

    with st.container():
        priority_badge = '&nbsp;' + status_badge('warning') if priority == 'high' else ''
        target_line = f'To: {target} | ' if target else ''
        received_str = f'{format_timestamp(str(created))} ({time_ago(str(created))})'

        card_html = (
            '<div class="health-card health-card-degraded" style="margin-bottom:1rem;">'
            '<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.5rem;">'
            f'<strong style="font-size:1.05rem;display:inline-flex;align-items:center;gap:6px;">{action_emoji} {action_label}</strong>'
            f'<div>{status_badge("pending")}{priority_badge}</div>'
            '</div>'
            f'<div style="font-size:0.9rem; margin-bottom:0.3rem;">{subject}</div>'
            f'<div style="font-size:0.85rem; color:#8899aa;">{target_line}Received: {received_str}</div>'
            '</div>'
        )
        st.markdown(card_html, unsafe_allow_html=True)

        # Content preview
        with st.expander("Preview content", expanded=False):
            st.markdown(item["body"][:3000] if item["body"] else "_No content_")

        # --- Approval / Rejection with 2-step confirmation ---
        col_approve, col_reject, col_spacer = st.columns([1, 1, 3])

        with col_approve:
            confirm_key = f"confirm_approve_{idx}"
            if st.session_state.get(confirm_key):
                st.markdown("**Confirm approval?**")
                c1, c2 = st.columns(2)
                if c1.button("Yes, approve", key=f"yes_approve_{idx}", type="primary"):
                    try:
                        file_path = item["path"]
                        content = file_path.read_text(encoding="utf-8")
                        content = re.sub(r"\[\s*\]\s*Approved", "[✅] Approved", content)
                        content = re.sub(r"\[\s{2}\]\s*Approved", "[✅] Approved", content)
                        file_path.write_text(content, encoding="utf-8")
                        st.success(f"Approved!")
                        st.session_state[confirm_key] = False
                        st.rerun()
                    except Exception:
                        st.error("Could not save your decision. Please try again.")
                if c2.button("Cancel", key=f"cancel_approve_{idx}"):
                    st.session_state[confirm_key] = False
                    st.rerun()
            else:
                if st.button("Approve", key=f"approve_{idx}", icon=":material/check:"):
                    st.session_state[confirm_key] = True
                    st.rerun()

        with col_reject:
            reject_key = f"confirm_reject_{idx}"
            if st.session_state.get(reject_key):
                st.markdown("**Confirm rejection?**")
                c1, c2 = st.columns(2)
                if c1.button("Yes, reject", key=f"yes_reject_{idx}"):
                    try:
                        file_path = item["path"]
                        content = file_path.read_text(encoding="utf-8")
                        content = re.sub(r"\[\s*\]\s*Rejected", "[✅] Rejected", content)
                        content = re.sub(r"\[\s{2}\]\s*Rejected", "[✅] Rejected", content)
                        file_path.write_text(content, encoding="utf-8")
                        st.success(f"Rejected.")
                        st.session_state[reject_key] = False
                        st.rerun()
                    except Exception:
                        st.error("Could not save your decision. Please try again.")
                if c2.button("Cancel", key=f"cancel_reject_{idx}"):
                    st.session_state[reject_key] = False
                    st.rerun()
            else:
                if st.button("Reject", key=f"reject_{idx}", icon=":material/close:"):
                    st.session_state[reject_key] = True
                    st.rerun()

        st.divider()

# --- Process Approvals Button ---
st.subheader("Process Decisions")
st.caption("After approving or rejecting items above, click here to execute the actions.")

if st.button("Process All Decisions", type="primary", icon=":material/refresh:"):
    if check_approvals:
        with st.spinner("Processing your decisions..."):
            try:
                result = check_approvals(Path(VAULT_PATH))
                st.success("Done!")
                cols = st.columns(4)
                cols[0].metric("Executed", result.get("executed", 0))
                cols[1].metric("Rejected", result.get("rejected", 0))
                cols[2].metric("Still Pending", result.get("pending", 0))
                cols[3].metric("Issues", result.get("failed", 0))
                st.rerun()
            except Exception as e:
                st.error(f"Something went wrong while processing. Please try again.")
    else:
        st.info("Processing will be available once the system is fully configured.")

# --- Already decided items waiting to be processed ---
if decided_items:
    st.divider()
    st.caption(f"{len(decided_items)} item(s) already decided — click **Process All Decisions** to execute them")

