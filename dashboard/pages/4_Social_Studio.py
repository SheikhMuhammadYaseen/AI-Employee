"""Social Studio — Social media management and engagement overview."""

import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone

import streamlit as st
import pandas as pd
import plotly.express as px
import frontmatter as fm

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils.path_setup import VAULT_PATH
from utils.theme import inject_custom_css, kpi_card, status_badge, render_sidebar_branding
from utils.formatters import format_status_badge
from utils.icons import lucide, icon_text

st.set_page_config(page_title="Social Studio", page_icon="📱", layout="wide")
inject_custom_css()
render_sidebar_branding()

# --- src/ imports ---
try:
    from src.mcp.tools.social_summary import social_engagement_summary
except ImportError:
    social_engagement_summary = None

try:
    from src.health.service_health import ServiceHealthTracker
except ImportError:
    ServiceHealthTracker = None

st.markdown(
    icon_text("smartphone", "Social Studio", 28, "primary", "h1")
    .replace("<svg", "<svg style='position:relative; top:-3px;'"),
    unsafe_allow_html=True
)

# --- Date Range Filter ---s
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("Start Date", value=datetime.now() - timedelta(days=30))
with col2:
    end_date = st.date_input("End Date", value=datetime.now())

# --- Load social data ---
@st.cache_data(ttl=300)
def load_social_data(start, end):
    if social_engagement_summary is None:
        return None
    try:
        return social_engagement_summary(
            start_date=str(start),
            end_date=str(end),
            vault_path=str(VAULT_PATH),
        )
    except Exception as e:
        return {"error": str(e)}


social = load_social_data(start_date, end_date)

# --- Demo data fallback ---
DEMO_PLATFORMS = {
    "linkedin": {"posts": 3, "engagements": 156, "top_post": "Business growth strategies for 2026", "followers": 5200, "new_followers": 64},
    "mastodon": {"posts": 4, "engagements": 89, "top_post": "Product launch announcement", "followers": 1240, "new_followers": 18},
    "facebook": {"posts": 2, "engagements": 35, "top_post": "Product launch cross-post", "followers": 3850, "new_followers": 42},
    "instagram": {"posts": 1, "engagements": 32, "top_post": "Weekly productivity tip", "followers": 2100, "new_followers": 27},
    "x_twitter": {"posts": 0, "engagements": 0, "top_post": "Service unavailable", "followers": 980, "new_followers": 0},
}

DEMO_HEALTH = {
    "linkedin": "operational",
    "mastodon": "operational",
    "facebook": "operational",
    "instagram": "degraded",
    "x_twitter": "unavailable",
}

DEMO_POSTS = [
    {"Date": "Feb 16", "Platform": "LinkedIn", "Content": "Business growth strategies for 2026 — AI-first approach", "Engagements": 87, "Type": "Thought Leadership"},
    {"Date": "Feb 16", "Platform": "Mastodon", "Content": "Product launch announcement — new features!", "Engagements": 47, "Type": "Announcement"},
    {"Date": "Feb 16", "Platform": "Facebook", "Content": "Product launch cross-post", "Engagements": 23, "Type": "Cross-post"},
    {"Date": "Feb 15", "Platform": "LinkedIn", "Content": "How we automated 85% of our operations with AI", "Engagements": 42, "Type": "Case Study"},
    {"Date": "Feb 15", "Platform": "Mastodon", "Content": "Weekly tip: 5 ways to automate tasks", "Engagements": 22, "Type": "Tip"},
    {"Date": "Feb 15", "Platform": "Instagram", "Content": "Weekly productivity tip (image post)", "Engagements": 32, "Type": "Tip"},
    {"Date": "Feb 14", "Platform": "LinkedIn", "Content": "Hiring? Consider a Digital FTE first", "Engagements": 27, "Type": "Sales"},
    {"Date": "Feb 14", "Platform": "Mastodon", "Content": "Behind the scenes: building our AI assistant", "Engagements": 14, "Type": "BTS"},
    {"Date": "Feb 13", "Platform": "Facebook", "Content": "Customer success story — Acme Corp", "Engagements": 12, "Type": "Case Study"},
    {"Date": "Feb 13", "Platform": "Mastodon", "Content": "Tech industry news roundup", "Engagements": 6, "Type": "Curation"},
]

use_demo = not social or not social.get("platforms") or social.get("error")
platform_data = DEMO_PLATFORMS if use_demo else social.get("platforms", {})

platforms = ["linkedin", "mastodon", "facebook", "instagram", "x_twitter"]
PLATFORM_LABELS = {"linkedin": "LinkedIn", "mastodon": "Mastodon", "facebook": "Facebook", "instagram": "Instagram", "x_twitter": "X (Twitter)"}


@st.cache_data(ttl=30)
def _load_all_health():
    if ServiceHealthTracker is None:
        return {}
    try:
        tracker = ServiceHealthTracker(str(VAULT_PATH))
        return tracker.get_all_health()
    except Exception:
        return {}


def get_platform_health(platform):
    if use_demo:
        return DEMO_HEALTH.get(platform, "unknown")
    all_health = _load_all_health()
    h = all_health.get(platform, {})
    return h.get("status", "unknown") if h else "unknown"


# --- Platform Health Cards ---
st.subheader("Platform Status")
if use_demo:
    st.caption("Demo data — connect social accounts for live numbers")

from utils.icons import service_icon

platform_cards = []
for platform in platforms:
    pdata = platform_data.get(platform, {})
    post_count = pdata.get("posts", 0) if isinstance(pdata, dict) else 0
    health_status = get_platform_health(platform)
    svc_icon = service_icon(platform, 20, "primary")
    label = PLATFORM_LABELS.get(platform, platform.replace("_", " ").title())
    card_class = (
        "health-card-ok" if health_status == "operational"
        else "health-card-degraded" if health_status == "degraded"
        else "health-card-down"
    )
    platform_cards.append((label, svc_icon, card_class, health_status, post_count))

# Row 1: 3 cards, Row 2: 2 cards (centered)
for row_cards in [platform_cards[:3], platform_cards[3:]]:
    cols = st.columns(3)
    for col, (label, svc_icon, card_class, health_status, post_count) in zip(cols, row_cards):
        card_html = (
            f'<div class="health-card {card_class}" style="min-height:100px;">'
            f'<div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:4px;">'
            f'<strong style="display:inline-flex;align-items:center;gap:6px;font-size:0.95rem;">{svc_icon} {label}</strong>'
            f'{status_badge(health_status)}'
            f'</div>'
            f'<div style="margin-top:0.5rem;">'
            f'<span class="kpi-value" style="font-size:1.5rem;">{post_count}</span>'
            f'<span style="color:#8899aa;font-size:0.8rem;"> posts</span>'
            f'</div>'
            f'</div>'
        )
        with col:
            st.markdown(card_html, unsafe_allow_html=True)

st.divider()

# ═══════════════════════════════════════════════════════════════════════════════
# GENERATE SOCIAL POST SECTION — Create platform-specific drafts
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown(
    icon_text("edit-3", "Generate Social Post", 24, "primary", "h2")
    .replace("<svg", "<svg style='position:relative; top:-2px;'"),
    unsafe_allow_html=True,
)
st.caption("Create social media post drafts for one or more platforms — drafts go to Pending Approval")

# Platform character limits
PLATFORM_LIMITS = {
    "LinkedIn": 3000,
    "Mastodon": 500,
    "Facebook": 5000,
    "Instagram": 2200,
    "X (Twitter)": 280,
}

PLATFORM_MCP_TOOLS = {
    "LinkedIn": "linkedin_post",
    "Mastodon": "mastodon_post",
    "Facebook": "facebook_post",
    "Instagram": "instagram_post",
    "X (Twitter)": "x_post",
}

PLATFORM_TONES = {
    "LinkedIn": "professional and insightful",
    "Mastodon": "casual and community-friendly",
    "Facebook": "friendly and engaging",
    "Instagram": "visual and trendy with hashtags",
    "X (Twitter)": "concise and punchy",
}

# Form layout
with st.container():
    gen_col1, gen_col2 = st.columns([2, 1])

    with gen_col1:
        post_topic = st.text_area(
            "Post Topic / Content",
            placeholder="e.g., Our AI Employee just automated 85% of inbox processing — here's how it works...",
            height=120,
            key="social_post_topic",
        )

    with gen_col2:
        selected_platforms = st.multiselect(
            "Target Platforms",
            options=list(PLATFORM_LIMITS.keys()),
            default=["LinkedIn", "Mastodon"],
            key="social_platforms",
        )
        post_tone = st.selectbox(
            "Tone",
            options=["Professional", "Casual", "Informative", "Promotional", "Thought Leadership"],
            key="social_tone",
        )
        include_hashtags = st.checkbox("Include hashtags", value=True, key="social_hashtags")
        include_cta = st.checkbox("Include call-to-action", value=False, key="social_cta")

    # Show character limits for selected platforms
    if selected_platforms:
        limit_text = " | ".join(
            f"**{p}**: {PLATFORM_LIMITS[p]} chars" for p in selected_platforms
        )
        st.markdown(f"Character limits: {limit_text}")

    # Generate button
    gen_col_btn1, gen_col_btn2 = st.columns([1, 3])
    with gen_col_btn1:
        generate_clicked = st.button(
            "Generate Drafts",
            type="primary",
            key="generate_social_btn",
            use_container_width=True,
            disabled=not post_topic or not selected_platforms,
        )
    with gen_col_btn2:
        if not post_topic:
            st.markdown(
                f'<span style="color:#8899aa;font-size:0.85rem;line-height:2.5rem">'
                f'{lucide("circle-alert", 14, "muted")} Enter a topic above to generate posts</span>',
                unsafe_allow_html=True,
            )

    if generate_clicked and post_topic and selected_platforms:
        progress_bar = st.progress(0, text="Generating social media drafts...")
        generated_drafts = []
        errors = []

        for i, platform in enumerate(selected_platforms):
            progress = (i + 1) / len(selected_platforms)
            progress_bar.progress(progress, text=f"Creating draft for {platform}...")

            try:
                char_limit = PLATFORM_LIMITS[platform]
                mcp_tool = PLATFORM_MCP_TOOLS[platform]
                platform_tone = PLATFORM_TONES.get(platform, "neutral")

                # Build adapted content for this platform
                content = post_topic.strip()

                # Add hashtags if requested
                if include_hashtags:
                    # Extract key words for hashtags
                    words = [w for w in content.split() if len(w) > 4 and w.isalpha()]
                    tags = " ".join(f"#{w.capitalize()}" for w in words[:4])
                    if tags:
                        content = f"{content}\n\n{tags}"

                # Add CTA if requested
                if include_cta:
                    content += "\n\nLearn more and follow us for updates!"

                # Truncate to platform limit
                if len(content) > char_limit:
                    content = content[:char_limit - 3] + "..."

                # Create approval draft
                now = datetime.now(timezone.utc)
                ts_str = now.strftime("%Y%m%dT%H%M%S")
                slug = platform.lower().replace(" ", "").replace("(", "").replace(")", "")
                draft_filename = f"social-{ts_str}-{slug}.md"

                draft_post = fm.Post(
                    content=(
                        f"# Social Post: {platform}\n\n"
                        f"**Platform**: {platform}\n"
                        f"**Tone**: {post_tone}\n"
                        f"**Character count**: {len(content)}/{char_limit}\n\n"
                        f"## Content\n\n{content}\n\n"
                        f"## Decision\n\n"
                        f"- [ ] Approved\n"
                        f"- [ ] Rejected\n"
                    ),
                    type="approval_draft",
                    mcp_tool=mcp_tool,
                    subject=f"Social post: {platform} — {post_topic[:50]}",
                    status="pending",
                    platform=platform.lower(),
                    priority="normal",
                    created_date=now.isoformat(),
                    tone=post_tone.lower(),
                    char_count=len(content),
                    char_limit=char_limit,
                )

                # Ensure Pending_Approval folder exists
                approval_dir = VAULT_PATH / "Pending_Approval"
                approval_dir.mkdir(parents=True, exist_ok=True)

                draft_path = approval_dir / draft_filename
                draft_path.write_text(fm.dumps(draft_post), encoding="utf-8")

                generated_drafts.append({
                    "Platform": platform,
                    "Characters": f"{len(content)}/{char_limit}",
                    "File": draft_filename,
                    "Status": "Draft Created",
                })

            except Exception as e:
                errors.append({"Platform": platform, "Error": str(e)})

        progress_bar.progress(1.0, text="All drafts generated!")

        # --- Show results ---
        st.markdown("---")
        st.markdown("### Generated Drafts")

        if generated_drafts:
            # Preview cards for each draft
            preview_cols = st.columns(min(len(generated_drafts), 3))
            for idx, draft in enumerate(generated_drafts):
                col = preview_cols[idx % len(preview_cols)]
                with col:
                    platform_key = draft["Platform"].lower().replace(" ", "_").replace("(", "").replace(")", "")
                    svc_icon = service_icon(
                        platform_key if platform_key != "xtwitter" else "x_twitter",
                        20, "primary",
                    )
                    st.markdown(
                        f'<div class="health-card health-card-ok" style="min-height:80px">'
                        f'<div style="display:flex;align-items:center;gap:6px;margin-bottom:0.5rem">'
                        f'{svc_icon} <strong>{draft["Platform"]}</strong>'
                        f'</div>'
                        f'<div style="color:#8899aa;font-size:0.85rem">'
                        f'{lucide("file-text", 14, "muted")} {draft["Characters"]} chars'
                        f'</div>'
                        f'<div style="margin-top:0.4rem">{status_badge("pending")}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

            st.dataframe(pd.DataFrame(generated_drafts), use_container_width=True, hide_index=True)

        if errors:
            st.error("Some platforms had errors:")
            st.dataframe(pd.DataFrame(errors), use_container_width=True, hide_index=True)

        st.success(
            f"Created {len(generated_drafts)} draft(s) in Pending Approval. "
            f"Go to the **Review Desk** page to review and approve them."
        )
        st.balloons()

st.divider()

# --- KPI + Engagement Chart ---
st.subheader("Engagement Overview")

total_posts = sum(p.get("posts", 0) for p in platform_data.values() if isinstance(p, dict))
total_engagements = sum(p.get("engagements", 0) for p in platform_data.values() if isinstance(p, dict))
total_followers = sum(p.get("followers", 0) for p in platform_data.values() if isinstance(p, dict))
new_followers = sum(p.get("new_followers", 0) for p in platform_data.values() if isinstance(p, dict))

kcols = st.columns(4)
kcols[0].markdown(kpi_card("Total Posts", total_posts, lucide("edit-3", 28, "primary")), unsafe_allow_html=True)
kcols[1].markdown(kpi_card("Engagements", total_engagements, lucide("message-square", 28, "success")), unsafe_allow_html=True)
kcols[2].markdown(kpi_card("Followers", f"{total_followers:,}", lucide("heart", 28, "danger")), unsafe_allow_html=True)
kcols[3].markdown(kpi_card("New Followers", f"+{new_followers}", lucide("trending-up", 28, "success")), unsafe_allow_html=True)

# Bar chart — posts & engagements per platform
chart_data = []
for pname in platforms:
    pdata = platform_data.get(pname, {})
    if isinstance(pdata, dict):
        chart_data.append({
            "Platform": PLATFORM_LABELS.get(pname, pname),
            "Posts": pdata.get("posts", 0),
            "Engagements": pdata.get("engagements", 0),
        })

if chart_data:
    df_chart = pd.DataFrame(chart_data)
    fig = px.bar(
        df_chart, x="Platform", y=["Posts", "Engagements"],
        barmode="group", template="plotly_dark",
        color_discrete_sequence=["#00d4ff", "#00c853"],
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        legend_title_text="", height=350,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig, use_container_width=True)

# --- Recent Posts Table ---
st.divider()
st.subheader("Recent Posts")

if use_demo:
    df_posts = pd.DataFrame(DEMO_POSTS)
else:
    # Build from platform_data if available
    post_rows = []
    for pname, pdata in platform_data.items():
        if isinstance(pdata, dict) and pdata.get("recent_posts"):
            for post in pdata["recent_posts"]:
                post_rows.append({
                    "Date": post.get("date", "—"),
                    "Platform": PLATFORM_LABELS.get(pname, pname),
                    "Content": post.get("content", "—")[:80],
                    "Engagements": post.get("engagements", 0),
                })
    df_posts = pd.DataFrame(post_rows) if post_rows else pd.DataFrame(DEMO_POSTS)

st.dataframe(df_posts, use_container_width=True, hide_index=True)

# --- Per-Platform Tabs ---
st.divider()
st.subheader("Platform Details")

ptabs = st.tabs([PLATFORM_LABELS.get(p, p) for p in platforms])
for ptab, platform in zip(ptabs, platforms):
    with ptab:
        pdata = platform_data.get(platform, {})
        if isinstance(pdata, dict) and pdata:
            mcols = st.columns(4)
            mcols[0].metric("Posts", pdata.get("posts", 0))
            mcols[1].metric("Engagements", pdata.get("engagements", 0))
            mcols[2].metric("Followers", f"{pdata.get('followers', 0):,}")
            mcols[3].metric("New Followers", f"+{pdata.get('new_followers', 0)}")
            if pdata.get("top_post"):
                st.markdown(f"**Top post:** {pdata['top_post']}")
        else:
            st.info(f"No data available for {PLATFORM_LABELS.get(platform, platform)}")
