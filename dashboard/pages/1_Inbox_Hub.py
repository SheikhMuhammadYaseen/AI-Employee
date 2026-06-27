"""Inbox Hub — Central inbox for all incoming items across workflow stages."""

import sys
import shutil
from pathlib import Path
from datetime import datetime, timezone

import streamlit as st
import pandas as pd
import frontmatter as fm

# Path setup
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils.path_setup import VAULT_PATH, PROJECT_ROOT
from utils.theme import inject_custom_css, kpi_card, status_badge, pipeline_flow_html, render_sidebar_branding
from utils.formatters import format_status_badge, format_timestamp, truncate, friendly_name
from utils.vault_reader import list_vault_items, count_items_by_folder
from utils.icons import lucide, icon_text

# --- src/ imports for processing ---
try:
    from src.reasoning.classifier import classify
except ImportError:
    classify = None

try:
    from src.reasoning.planner import generate_plan
except ImportError:
    generate_plan = None

st.set_page_config(page_title="Inbox Hub", page_icon="📥", layout="wide")
inject_custom_css()
render_sidebar_branding()

st.markdown(
    icon_text("inbox", "Inbox Hub", 28, "primary", "h1")
    .replace("<svg", "<svg style='position:relative; top:-3px;'"),
    unsafe_allow_html=True
)

# --- Pipeline Flow at Top ---
counts = count_items_by_folder(VAULT_PATH)
_total_vault = sum(counts.values())
_is_demo = _total_vault == 0

DEMO_PIPELINE = {"Inbox": 2, "Needs_Action": 3, "Plans": 2, "Pending_Approval": 3, "Done": 12}
_disp = counts if not _is_demo else DEMO_PIPELINE

if _is_demo:
    st.caption("Demo data — items will populate as your AI Employee runs")

st.markdown(pipeline_flow_html(_disp), unsafe_allow_html=True)

st.divider()

# ═══════════════════════════════════════════════════════════════════════════════
# PROCESS INBOX SECTION — Classify & route items from /Needs_Action
# ═══════════════════════════════════════════════════════════════════════════════

needs_action_items = list_vault_items(VAULT_PATH / "Needs_Action")
# Filter out items that are already classified or are plans
unprocessed = [
    it for it in needs_action_items
    if not it["metadata"].get("classification")
    and it["metadata"].get("type") != "plan"
    and it["metadata"].get("status") != "planned"
]

# Demo counts for showcase
_na_count = len(needs_action_items) or (3 if _is_demo else 0)
_unproc = len(unprocessed) or (2 if _is_demo else 0)
_classified = _na_count - _unproc

st.markdown(
    icon_text("zap", "Process Inbox", 24, "warning", "h2")
    .replace("<svg", "<svg style='position:relative; top:-2px;'"),
    unsafe_allow_html=True,
)
st.caption("Classify items in Needs Action and route them automatically")

proc_cols = st.columns(3)
with proc_cols[0]:
    st.markdown(
        kpi_card("Needs Action", _na_count, lucide("clipboard-list", 24, "warning")),
        unsafe_allow_html=True,
    )
with proc_cols[1]:
    st.markdown(
        kpi_card("Unprocessed", _unproc, lucide("inbox", 24, "primary")),
        unsafe_allow_html=True,
    )
with proc_cols[2]:
    st.markdown(
        kpi_card("Already Classified", _classified, lucide("check-circle", 24, "success")),
        unsafe_allow_html=True,
    )

st.markdown("")

if classify is None:
    st.warning("Classifier module not available. Check `src/reasoning/classifier.py`.")
elif _is_demo and not needs_action_items:
    st.info("Demo mode — add items to Needs Action or start watchers to process real inbox items.")
elif not needs_action_items:
    st.info("No items in Needs Action. New emails and messages will appear here automatically.")
elif not unprocessed:
    st.info("All items are already classified! Nothing left to process.")
else:
    action_col1, action_col2, action_col3 = st.columns([2, 1, 1])
    with action_col1:
        st.markdown(f"**{len(unprocessed)}** items ready to be classified and routed.")
    with action_col2:
        dry_run = st.checkbox("Preview only", value=False, key="inbox_dry_run")
    with action_col3:
        process_clicked = st.button(
            f"Process {len(unprocessed)} Items",
            type="primary",
            key="process_inbox_btn",
            use_container_width=True,
        )

    if process_clicked:
            progress_bar = st.progress(0, text="Starting inbox processing...")
            results = {"simple": 0, "complex": 0, "action_required": 0, "errors": 0}
            result_details = []

            for i, item in enumerate(unprocessed):
                progress = (i + 1) / len(unprocessed)
                item_name = item["metadata"].get("subject", friendly_name(item["filename"]))
                progress_bar.progress(progress, text=f"Processing: {truncate(item_name, 40)}")

                try:
                    classification = classify(item["metadata"], item["body"])
                    results[classification] = results.get(classification, 0) + 1

                    if not dry_run:
                        # Update the file with classification
                        post = fm.load(str(item["path"]))
                        post["classification"] = classification
                        post["classified_date"] = datetime.now(timezone.utc).isoformat()

                        if classification == "simple":
                            # Move to /Done
                            post["status"] = "completed"
                            done_path = VAULT_PATH / "Done" / item["path"].name
                            done_path.write_text(fm.dumps(post), encoding="utf-8")
                            item["path"].unlink()
                            result_details.append(("simple", item_name, "Moved to Done"))

                        elif classification == "complex":
                            # Generate plan, save updated item
                            item["path"].write_text(fm.dumps(post), encoding="utf-8")
                            if generate_plan:
                                plan_path = generate_plan(item["path"], VAULT_PATH)
                                result_details.append(("complex", item_name, f"Plan created: {plan_path.name}"))
                            else:
                                result_details.append(("complex", item_name, "Classified (planner unavailable)"))

                        elif classification == "action_required":
                            # Create approval draft in /Pending_Approval
                            post["status"] = "awaiting_approval"
                            mcp_tool = "action"
                            body_lower = item["body"].lower()
                            if any(kw in body_lower for kw in ["email", "reply", "send", "forward"]):
                                mcp_tool = "email_send"
                            elif any(kw in body_lower for kw in ["linkedin", "professional"]):
                                mcp_tool = "linkedin_post"
                            elif any(kw in body_lower for kw in ["mastodon", "toot"]):
                                mcp_tool = "mastodon_post"
                            elif any(kw in body_lower for kw in ["facebook", "fb"]):
                                mcp_tool = "facebook_post"
                            elif any(kw in body_lower for kw in ["instagram", "insta"]):
                                mcp_tool = "instagram_post"
                            elif any(kw in body_lower for kw in ["tweet", "twitter", "x post"]):
                                mcp_tool = "x_post"

                            draft_post = fm.Post(
                                content=(
                                    f"# Action Required: {item_name}\n\n"
                                    f"## Content\n\n{item['body'][:2000]}\n\n"
                                    f"## Decision\n\n"
                                    f"- [ ] Approved\n"
                                    f"- [ ] Rejected\n"
                                ),
                                type="approval_draft",
                                mcp_tool=mcp_tool,
                                subject=item_name,
                                linked_item=item["path"].name,
                                status="pending",
                                priority=item["metadata"].get("priority", "normal"),
                                created_date=datetime.now(timezone.utc).isoformat(),
                                target=item["metadata"].get("from", ""),
                            )

                            slug = item["path"].stem
                            ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
                            draft_path = VAULT_PATH / "Pending_Approval" / f"draft-{ts}-{slug}.md"
                            draft_path.write_text(fm.dumps(draft_post), encoding="utf-8")

                            # Update original
                            item["path"].write_text(fm.dumps(post), encoding="utf-8")
                            result_details.append(("action_required", item_name, f"Draft: {draft_path.name}"))
                    else:
                        result_details.append((classification, item_name, "Preview only"))

                except Exception as e:
                    results["errors"] += 1
                    result_details.append(("error", item_name, str(e)))

            progress_bar.progress(1.0, text="Processing complete!")

            # --- Results Summary ---
            st.markdown("---")
            st.markdown("### Results")
            res_cols = st.columns(4)
            with res_cols[0]:
                st.markdown(
                    f'<div class="health-card health-card-ok" style="text-align:center;padding:0.8rem">'
                    f'<div style="font-size:1.8rem;font-weight:700;color:#00c853">{results["simple"]}</div>'
                    f'<div style="color:#8899aa;font-size:0.8rem">SIMPLE (Done)</div></div>',
                    unsafe_allow_html=True,
                )
            with res_cols[1]:
                st.markdown(
                    f'<div class="health-card health-card-degraded" style="text-align:center;padding:0.8rem">'
                    f'<div style="font-size:1.8rem;font-weight:700;color:#ffc107">{results["complex"]}</div>'
                    f'<div style="color:#8899aa;font-size:0.8rem">COMPLEX (Plan)</div></div>',
                    unsafe_allow_html=True,
                )
            with res_cols[2]:
                st.markdown(
                    f'<div class="health-card" style="text-align:center;padding:0.8rem;border-left:4px solid #00d4ff">'
                    f'<div style="font-size:1.8rem;font-weight:700;color:#00d4ff">{results["action_required"]}</div>'
                    f'<div style="color:#8899aa;font-size:0.8rem">ACTION (Approval)</div></div>',
                    unsafe_allow_html=True,
                )
            with res_cols[3]:
                st.markdown(
                    f'<div class="health-card health-card-down" style="text-align:center;padding:0.8rem">'
                    f'<div style="font-size:1.8rem;font-weight:700;color:#ff5252">{results["errors"]}</div>'
                    f'<div style="color:#8899aa;font-size:0.8rem">ERRORS</div></div>',
                    unsafe_allow_html=True,
                )

            # Detailed results table
            if result_details:
                st.markdown("#### Item Details")
                detail_rows = []
                classification_icons = {
                    "simple": "check-circle",
                    "complex": "file-text",
                    "action_required": "hourglass",
                    "error": "circle-x",
                }
                for cls, name, detail in result_details:
                    detail_rows.append({
                        "Classification": cls.replace("_", " ").title(),
                        "Item": truncate(name, 50),
                        "Result": detail,
                    })
                st.dataframe(pd.DataFrame(detail_rows), use_container_width=True, hide_index=True)

            st.success(
                f"Done! {results['simple']} simple, {results['complex']} complex, "
                f"{results['action_required']} action required, {results['errors']} errors"
            )
            st.rerun()

st.divider()

# --- Filters ---
col_filter1, col_filter2 = st.columns(2)
with col_filter1:
    type_filter = st.text_input("Filter by type", placeholder="e.g. email, whatsapp, plan")
with col_filter2:
    content_filter = st.text_input("Search content", placeholder="Search in item bodies...")

# --- Tabbed View ---
FOLDERS = {
    "Inbox": "Inbox",
    "Needs Action": "Needs_Action",
    "Plans": "Plans",
    "Pending Approval": "Pending_Approval",
    "Done": "Done",
}

# Friendly type labels
TYPE_LABELS = {
    "email": "Email",
    "whatsapp": "WhatsApp",
    "approval_draft": "Approval Draft",
    "plan": "Plan",
    "scheduler_log": "Scheduler Log",
    "ceo_briefing": "Briefing",
    "briefing": "Briefing",
    "action": "Action",
}

tabs = st.tabs([f"{name} ({counts.get(folder, 0)})" for name, folder in FOLDERS.items()])

DEMO_ITEMS = {
    "Inbox": [
        {"Type": "Email", "Status": "New", "Priority": "Normal", "Date": "Feb 17, 2026", "Subject": "Partnership inquiry from CloudTech Solutions"},
        {"Type": "Email", "Status": "New", "Priority": "High", "Date": "Feb 17, 2026", "Subject": "Urgent: Server renewal reminder"},
    ],
    "Needs_Action": [
        {"Type": "Email", "Status": "Pending", "Priority": "High", "Date": "Feb 16, 2026", "Subject": "Client onboarding request — Acme Corp"},
        {"Type": "WhatsApp", "Status": "Pending", "Priority": "Normal", "Date": "Feb 16, 2026", "Subject": "Team meeting notes from project lead"},
        {"Type": "Email", "Status": "Pending", "Priority": "Normal", "Date": "Feb 15, 2026", "Subject": "Invoice dispute from OldClient Corp"},
    ],
    "Plans": [
        {"Type": "Plan", "Status": "In Progress", "Priority": "Normal", "Date": "Feb 16, 2026", "Subject": "Quarterly review — 4/5 steps completed"},
        {"Type": "Plan", "Status": "Pending", "Priority": "Normal", "Date": "Feb 15, 2026", "Subject": "Social media content calendar for March"},
    ],
    "Pending_Approval": [
        {"Type": "Social Post", "Status": "Pending", "Priority": "Normal", "Date": "Feb 17, 2026", "Subject": "LinkedIn post: AI trends for business leaders"},
        {"Type": "Email Reply", "Status": "Pending", "Priority": "High", "Date": "Feb 17, 2026", "Subject": "Reply to CloudTech partnership inquiry"},
        {"Type": "Social Post", "Status": "Pending", "Priority": "Normal", "Date": "Feb 16, 2026", "Subject": "Mastodon post: Weekly tech roundup"},
    ],
    "Done": [
        {"Type": "Social Post", "Status": "Completed", "Priority": "Normal", "Date": "Feb 16, 2026", "Subject": "Product launch posted to LinkedIn, Mastodon, Facebook"},
        {"Type": "Email", "Status": "Completed", "Priority": "Normal", "Date": "Feb 15, 2026", "Subject": "Weekly tip sent to subscriber list"},
        {"Type": "Invoice", "Status": "Completed", "Priority": "Normal", "Date": "Feb 14, 2026", "Subject": "INV-2026-0338 payment processed from Acme Corp"},
        {"Type": "Briefing", "Status": "Completed", "Priority": "Normal", "Date": "Feb 13, 2026", "Subject": "Weekly CEO Briefing generated"},
        {"Type": "Social Post", "Status": "Completed", "Priority": "Normal", "Date": "Feb 13, 2026", "Subject": "Customer success story posted to Facebook"},
    ],
}

for tab, (name, folder) in zip(tabs, FOLDERS.items()):
    with tab:
        items = list_vault_items(VAULT_PATH / folder)

        # Apply filters
        if type_filter:
            items = [
                it for it in items
                if type_filter.lower() in str(it["metadata"].get("type", "")).lower()
                or type_filter.lower() in it["filename"].lower()
            ]
        if content_filter:
            items = [
                it for it in items
                if content_filter.lower() in it["body"].lower()
                or content_filter.lower() in it["filename"].lower()
            ]

        if not items:
            demo = DEMO_ITEMS.get(folder, [])
            if demo:
                st.caption("Demo data — items will populate as your AI Employee runs")
                df = pd.DataFrame(demo)
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info(f"No items in {name}")
            continue

        # Build dataframe
        rows = []
        for it in items:
            meta = it["metadata"]
            raw_type = meta.get("type", "—")
            rows.append({
                "Type": TYPE_LABELS.get(raw_type, raw_type.replace("_", " ").title() if raw_type != "—" else "—"),
                "Status": format_status_badge(meta.get("status", "unknown")),
                "Priority": (meta.get("priority", "normal") or "normal").title(),
                "Date": format_timestamp(str(meta.get("date", meta.get("created_date", "")))),
                "Subject": truncate(meta.get("subject", friendly_name(it["filename"])), 60),
            })

        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)

        # Expandable details
        for it in items:
            meta = it["metadata"]
            subject = meta.get("subject", friendly_name(it["filename"]))
            with st.expander(subject):
                info_parts = []
                if meta.get("from"):
                    info_parts.append(f"**From**: {meta['from']}")
                if meta.get("target"):
                    info_parts.append(f"**To**: {meta['target']}")
                if meta.get("date") or meta.get("created_date"):
                    info_parts.append(f"**Date**: {format_timestamp(str(meta.get('date', meta.get('created_date', ''))))}")
                if meta.get("priority"):
                    info_parts.append(f"**Priority**: {meta['priority'].title()}")
                if meta.get("status"):
                    info_parts.append(f"**Status**: {format_status_badge(meta['status'])}")

                if info_parts:
                    st.markdown(" | ".join(info_parts))
                    st.markdown("---")

                st.markdown(it["body"][:3000] if it["body"] else "_No content_")

