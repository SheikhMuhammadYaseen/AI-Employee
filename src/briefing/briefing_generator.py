"""Weekly Briefing generator — Gold Tier.

Collects data from Odoo (financial), audit logs (operational),
social activity (vault/Done), and generates a Briefing.md.

Gold Tier — US2: Weekly Briefing (FR-005, FR-006).
"""

import logging
import os
import shutil
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)


def collect_financial_data(start_date, end_date, prev_start=None, prev_end=None):
    """Collect financial data from Odoo for the briefing.

    Args:
        start_date: Week start (YYYY-MM-DD string).
        end_date: Week end (YYYY-MM-DD string).
        prev_start: Previous week start for trend comparison.
        prev_end: Previous week end for trend comparison.

    Returns:
        Dict with current and previous period financial metrics.
    """
    try:
        from src.mcp.tools.odoo_reports import get_financial_summary

        current = get_financial_summary(start_date, end_date)
        previous = None
        if prev_start and prev_end:
            previous = get_financial_summary(prev_start, prev_end)

        return {
            "status": "success",
            "current": current if current.get("status") == "success" else None,
            "previous": previous if previous and previous.get("status") == "success" else None,
        }
    except Exception as e:
        logger.warning("Financial data collection failed: %s", e)
        return {"status": "unavailable", "error": str(e), "current": None, "previous": None}


def collect_operational_data(vault_path, start_date, end_date):
    """Collect operational data from audit logs and service health.

    Args:
        vault_path: Path to vault root.
        start_date: Start date (datetime object).
        end_date: End date (datetime object).

    Returns:
        Dict with service health and scheduler run data.
    """
    result = {"services": {}, "scheduler_runs": 0, "scheduler_success": 0, "scheduler_failed": 0}

    # Service health
    try:
        from src.health.service_health import ServiceHealthTracker
        tracker = ServiceHealthTracker(vault_path)
        result["services"] = tracker.get_all_health()
    except Exception as e:
        logger.warning("Service health collection failed: %s", e)

    # Audit log summary
    try:
        from src.logging.audit_logger import summarize_week
        log_summary = summarize_week(vault_path, start_date, end_date)
        sched = log_summary.get("categories", {}).get("scheduler", {})
        result["scheduler_runs"] = sched.get("entries", 0)
        result["scheduler_success"] = sched.get("successes", 0)
        result["scheduler_failed"] = sched.get("failures", 0)
        result["log_summary"] = log_summary
    except Exception as e:
        logger.warning("Audit log summary failed: %s", e)

    return result


def collect_social_data(vault_path, start_date, end_date):
    """Collect social media activity from vault/Done folder.

    Args:
        vault_path: Path to vault root.
        start_date: Start date (datetime object).
        end_date: End date (datetime object).

    Returns:
        Dict with platform activity counts.
    """
    result = {"platforms": {}, "total_posts": 0, "total_engagements": 0}

    done_dir = os.path.join(vault_path, "Done")
    if not os.path.isdir(done_dir):
        return result

    try:
        import frontmatter as fm
    except ImportError:
        return result

    for filename in os.listdir(done_dir):
        if not filename.endswith(".md"):
            continue

        try:
            filepath = os.path.join(done_dir, filename)
            post = fm.load(filepath)
            meta = post.metadata

            post_type = meta.get("type", "")
            if post_type not in ("mastodon-post", "facebook-post", "instagram-post", "x-post"):
                continue

            executed_date = meta.get("executed_date", "")
            if isinstance(executed_date, str) and executed_date:
                post_date = datetime.fromisoformat(executed_date.replace("Z", "+00:00"))
                if not (start_date <= post_date <= end_date):
                    continue

            platform = post_type.replace("-post", "")
            if platform not in result["platforms"]:
                result["platforms"][platform] = {"posts": 0, "engagements": 0}

            result["platforms"][platform]["posts"] += 1
            result["total_posts"] += 1

        except Exception:
            continue

    return result


def detect_bottlenecks(financial, operational, social):
    """Analyze collected data for bottlenecks and risks.

    Returns:
        List of bottleneck dicts with severity, description, recommendation.
    """
    bottlenecks = []

    # Financial bottlenecks
    if financial.get("current"):
        current = financial["current"]
        if current.get("overdue_count", 0) > 0:
            bottlenecks.append({
                "severity": "warning",
                "description": f"{current['overdue_count']} overdue invoices totaling ${current.get('overdue_amount', 0):,.2f}",
                "recommendation": "Review overdue invoices and follow up with clients.",
            })
        if current.get("net_cash_flow", 0) < 0:
            bottlenecks.append({
                "severity": "critical",
                "description": f"Negative net cash flow: ${current['net_cash_flow']:,.2f}",
                "recommendation": "Review expenses and accelerate receivables collection.",
            })

    # Operational bottlenecks
    for service, health in operational.get("services", {}).items():
        if isinstance(health, dict) and health.get("status") in ("degraded", "unavailable"):
            bottlenecks.append({
                "severity": "critical" if health["status"] == "unavailable" else "warning",
                "description": f"Service '{service}' is {health['status']}",
                "recommendation": f"Investigate {service} connectivity. Last error: {health.get('last_error_message', 'unknown')}",
            })

    # Check for high failure rates in logs
    log_summary = operational.get("log_summary", {})
    for cat, stats in log_summary.get("categories", {}).items():
        if stats.get("failures", 0) > 0 and stats.get("entries", 0) > 0:
            failure_rate = stats["failures"] / stats["entries"] * 100
            if failure_rate > 20:
                bottlenecks.append({
                    "severity": "warning",
                    "description": f"High failure rate in {cat}: {failure_rate:.0f}% ({stats['failures']}/{stats['entries']})",
                    "recommendation": f"Review {cat} error patterns and address recurring failures.",
                })

    if not bottlenecks:
        bottlenecks.append({
            "severity": "info",
            "description": "No significant bottlenecks detected.",
            "recommendation": "Continue current operations.",
        })

    return bottlenecks


def _trend_indicator(current, previous):
    """Return trend indicator comparing two values."""
    if previous is None or previous == 0:
        return "—"
    diff = current - previous
    pct = (diff / abs(previous)) * 100
    if pct > 5:
        return f"↑ +{pct:.0f}%"
    elif pct < -5:
        return f"↓ {pct:.0f}%"
    return "→ stable"


def _format_currency(amount):
    """Format amount as currency string."""
    if amount is None:
        return "N/A"
    return f"${amount:,.2f}"


def generate_briefing(vault_path, target_date=None):
    """Generate the weekly CEO Briefing.

    Args:
        vault_path: Path to vault root.
        target_date: Date for briefing (defaults to today). datetime object.

    Returns:
        Dict with status, file_path, and summary.
    """
    if target_date is None:
        target_date = datetime.now(timezone.utc)

    # Calculate week boundaries (Mon-Sun)
    weekday = target_date.weekday()
    week_start = target_date - timedelta(days=weekday + 7)  # Previous Monday
    week_end = week_start + timedelta(days=6)  # Previous Sunday
    prev_start = week_start - timedelta(days=7)
    prev_end = week_start - timedelta(days=1)

    start_str = week_start.strftime("%Y-%m-%d")
    end_str = week_end.strftime("%Y-%m-%d")
    prev_start_str = prev_start.strftime("%Y-%m-%d")
    prev_end_str = prev_end.strftime("%Y-%m-%d")

    # Collect data from all sources
    financial = collect_financial_data(start_str, end_str, prev_start_str, prev_end_str)
    operational = collect_operational_data(vault_path, week_start, week_end)
    social = collect_social_data(vault_path, week_start, week_end)
    bottlenecks = detect_bottlenecks(financial, operational, social)

    # Build financial section
    cur = financial.get("current") or {}
    prev = financial.get("previous") or {}

    revenue = cur.get("total_revenue", 0)
    expenses = cur.get("total_expenses", 0)
    net_cash = cur.get("net_cash_flow", 0)
    prev_revenue = prev.get("total_revenue")
    prev_expenses = prev.get("total_expenses")
    prev_net_cash = prev.get("net_cash_flow")

    financial_notes = ""
    if financial.get("status") == "unavailable":
        financial_notes = "> ⚠ Financial data unavailable — Odoo connection failed. Showing last known data."

    # Build service status rows
    service_rows = []
    for svc, health in operational.get("services", {}).items():
        if isinstance(health, dict):
            status = health.get("status", "unknown")
            emoji = "✅" if status == "operational" else "⚠️" if status == "degraded" else "❌"
            last_ok = health.get("last_ok", "—")
            if isinstance(last_ok, str) and len(last_ok) > 10:
                last_ok = last_ok[:19]
            service_rows.append(f"| {svc} | {emoji} {status} | {last_ok} | — |")

    if not service_rows:
        service_rows = ["| No services tracked | — | — | — |"]

    # Build social rows
    social_rows = []
    for platform, data in social.get("platforms", {}).items():
        social_rows.append(
            f"| {platform.capitalize()} | {data['posts']} | {data['engagements']} | — |"
        )
    if not social_rows:
        social_rows = ["| No social activity | — | — | — |"]

    # Build bottleneck text
    bottleneck_lines = []
    for b in bottlenecks:
        icon = "🔴" if b["severity"] == "critical" else "🟡" if b["severity"] == "warning" else "🟢"
        bottleneck_lines.append(f"- {icon} **{b['severity'].upper()}**: {b['description']}")
        bottleneck_lines.append(f"  - *Recommendation*: {b['recommendation']}")

    # Build actions
    action_lines = []
    for i, b in enumerate(bottlenecks, 1):
        if b["severity"] != "info":
            action_lines.append(f"{i}. {b['recommendation']}")
    if not action_lines:
        action_lines = ["No immediate actions required."]

    # Load template
    template_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "templates", "briefing_template.md"
    )

    try:
        with open(template_path, "r", encoding="utf-8") as f:
            template = f.read()
    except FileNotFoundError:
        # Fallback: build without template
        template = _fallback_template()

    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    date_str = target_date.strftime("%Y-%m-%d")

    # Replace placeholders
    content = template
    replacements = {
        "{{DATE}}": date_str,
        "{{TIMESTAMP}}": now_str,
        "{{WEEK_START}}": start_str,
        "{{WEEK_END}}": end_str,
        "{{STATUS}}": "generated",
        "{{REVENUE}}": _format_currency(revenue),
        "{{PREV_REVENUE}}": _format_currency(prev_revenue) if prev_revenue else "—",
        "{{REVENUE_TREND}}": _trend_indicator(revenue, prev_revenue),
        "{{EXPENSES}}": _format_currency(expenses),
        "{{PREV_EXPENSES}}": _format_currency(prev_expenses) if prev_expenses else "—",
        "{{EXPENSES_TREND}}": _trend_indicator(expenses, prev_expenses),
        "{{NET_CASH}}": _format_currency(net_cash),
        "{{PREV_NET_CASH}}": _format_currency(prev_net_cash) if prev_net_cash else "—",
        "{{NET_CASH_TREND}}": _trend_indicator(net_cash, prev_net_cash),
        "{{OUTSTANDING}}": _format_currency(cur.get("outstanding_receivables", 0)),
        "{{OVERDUE_COUNT}}": str(cur.get("overdue_count", 0)),
        "{{OVERDUE_AMOUNT}}": _format_currency(cur.get("overdue_amount", 0)),
        "{{INVOICE_COUNT}}": str(cur.get("invoice_count", 0)),
        "{{PAYMENT_COUNT}}": str(cur.get("payment_count", 0)),
        "{{FINANCIAL_NOTES}}": financial_notes,
        "{{SERVICE_STATUS_ROWS}}": "\n".join(service_rows),
        "{{SCHEDULER_RUNS}}": str(operational.get("scheduler_runs", 0)),
        "{{SCHEDULER_SUCCESS}}": str(operational.get("scheduler_success", 0)),
        "{{SCHEDULER_FAILED}}": str(operational.get("scheduler_failed", 0)),
        "{{OPERATIONAL_NOTES}}": "",
        "{{SOCIAL_ROWS}}": "\n".join(social_rows),
        "{{TOTAL_POSTS}}": str(social.get("total_posts", 0)),
        "{{TOTAL_ENGAGEMENTS}}": str(social.get("total_engagements", 0)),
        "{{SOCIAL_NOTES}}": "",
        "{{BOTTLENECKS}}": "\n".join(bottleneck_lines),
        "{{ACTIONS}}": "\n".join(action_lines),
    }

    for placeholder, value in replacements.items():
        content = content.replace(placeholder, value)

    # Archive existing briefing
    briefing_path = os.path.join(vault_path, "Briefing.md")
    if os.path.exists(briefing_path):
        done_dir = os.path.join(vault_path, "Done")
        os.makedirs(done_dir, exist_ok=True)
        archive_name = f"briefing-{date_str}.md"
        shutil.move(briefing_path, os.path.join(done_dir, archive_name))
        logger.info("Archived previous briefing to Done/%s", archive_name)

    # Write new briefing
    with open(briefing_path, "w", encoding="utf-8") as f:
        f.write(content)

    logger.info("Generated Briefing: %s", briefing_path)

    return {
        "status": "generated",
        "file_path": briefing_path,
        "date": date_str,
        "period": f"{start_str} to {end_str}",
        "sections": ["financial", "operational", "social", "bottlenecks", "actions"],
        "bottleneck_count": sum(1 for b in bottlenecks if b["severity"] != "info"),
    }


def _fallback_template():
    """Minimal briefing template if file not found."""
    return """---
type: briefing
date: "{{DATE}}"
generated: "{{TIMESTAMP}}"
---

# Weekly Briefing: {{DATE}}

**Period**: {{WEEK_START}} — {{WEEK_END}}

## 1. Financial Summary
Revenue: {{REVENUE}} | Expenses: {{EXPENSES}} | Net: {{NET_CASH}}
{{FINANCIAL_NOTES}}

## 2. Operational Status
{{SERVICE_STATUS_ROWS}}

## 3. Social Activity
{{SOCIAL_ROWS}}

## 4. Bottlenecks
{{BOTTLENECKS}}

## 5. Actions
{{ACTIONS}}
"""
