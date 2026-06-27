"""Unit tests for CEO Briefing generator (T028)."""

import os
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch


class TestCollectFinancialData(unittest.TestCase):
    """Test financial data collection."""

    @patch("src.mcp.tools.odoo_reports.get_financial_summary")
    def test_collect_financial_success(self, mock_summary):
        from src.briefing.briefing_generator import collect_financial_data

        mock_summary.side_effect = [
            {"status": "success", "total_revenue": 8000, "total_expenses": 3000},
            {"status": "success", "total_revenue": 6000, "total_expenses": 2500},
        ]

        result = collect_financial_data("2026-02-03", "2026-02-09", "2026-01-27", "2026-02-02")
        assert result["status"] == "success"
        assert result["current"]["total_revenue"] == 8000
        assert result["previous"]["total_revenue"] == 6000

    @patch("src.mcp.tools.odoo_reports.get_financial_summary")
    def test_collect_financial_odoo_down(self, mock_summary):
        from src.briefing.briefing_generator import collect_financial_data

        mock_summary.side_effect = Exception("Connection refused")

        result = collect_financial_data("2026-02-03", "2026-02-09")
        assert result["status"] == "unavailable"
        assert result["current"] is None


class TestCollectOperationalData(unittest.TestCase):
    """Test operational data collection."""

    def test_collect_operational_no_vault(self):
        from src.briefing.briefing_generator import collect_operational_data

        result = collect_operational_data(
            "/nonexistent",
            datetime(2026, 2, 3, tzinfo=timezone.utc),
            datetime(2026, 2, 9, tzinfo=timezone.utc),
        )
        assert result["scheduler_runs"] == 0

    @patch("src.health.service_health.ServiceHealthTracker")
    def test_collect_operational_with_health(self, mock_tracker_cls):
        from src.briefing.briefing_generator import collect_operational_data

        tracker = MagicMock()
        tracker.get_all_health.return_value = {
            "odoo": {"status": "operational"},
            "mastodon": {"status": "degraded"},
        }
        mock_tracker_cls.return_value = tracker

        result = collect_operational_data(
            "/tmp/test_vault",
            datetime(2026, 2, 3, tzinfo=timezone.utc),
            datetime(2026, 2, 9, tzinfo=timezone.utc),
        )
        assert "odoo" in result["services"]
        assert result["services"]["odoo"]["status"] == "operational"


class TestCollectSocialData(unittest.TestCase):
    """Test social data collection."""

    def test_no_done_dir(self):
        from src.briefing.briefing_generator import collect_social_data

        result = collect_social_data(
            "/nonexistent",
            datetime(2026, 2, 3, tzinfo=timezone.utc),
            datetime(2026, 2, 9, tzinfo=timezone.utc),
        )
        assert result["total_posts"] == 0


class TestDetectBottlenecks(unittest.TestCase):
    """Test bottleneck detection."""

    def test_overdue_invoices(self):
        from src.briefing.briefing_generator import detect_bottlenecks

        financial = {"current": {"overdue_count": 3, "overdue_amount": 5000, "net_cash_flow": 1000}}
        result = detect_bottlenecks(financial, {"services": {}}, {})
        assert any(b["severity"] == "warning" for b in result)
        assert any("overdue" in b["description"].lower() for b in result)

    def test_negative_cash_flow(self):
        from src.briefing.briefing_generator import detect_bottlenecks

        financial = {"current": {"overdue_count": 0, "net_cash_flow": -5000}}
        result = detect_bottlenecks(financial, {"services": {}}, {})
        assert any(b["severity"] == "critical" for b in result)

    def test_degraded_service(self):
        from src.briefing.briefing_generator import detect_bottlenecks

        operational = {
            "services": {"odoo": {"status": "unavailable", "last_error_message": "timeout"}},
            "log_summary": {"categories": {}},
        }
        result = detect_bottlenecks({"current": None}, operational, {})
        assert any("odoo" in b["description"].lower() for b in result)

    def test_no_bottlenecks(self):
        from src.briefing.briefing_generator import detect_bottlenecks

        result = detect_bottlenecks(
            {"current": {"overdue_count": 0, "net_cash_flow": 5000}},
            {"services": {}, "log_summary": {"categories": {}}},
            {},
        )
        assert result[0]["severity"] == "info"


class TestTrendIndicator(unittest.TestCase):
    """Test trend calculation."""

    def test_upward_trend(self):
        from src.briefing.briefing_generator import _trend_indicator

        result = _trend_indicator(1000, 800)
        assert "↑" in result

    def test_downward_trend(self):
        from src.briefing.briefing_generator import _trend_indicator

        result = _trend_indicator(800, 1000)
        assert "↓" in result

    def test_stable_trend(self):
        from src.briefing.briefing_generator import _trend_indicator

        result = _trend_indicator(1000, 1000)
        assert "stable" in result

    def test_no_previous(self):
        from src.briefing.briefing_generator import _trend_indicator

        result = _trend_indicator(1000, None)
        assert result == "—"


class TestGenerateBriefing(unittest.TestCase):
    """Test full briefing generation."""

    @patch("src.briefing.briefing_generator.collect_social_data")
    @patch("src.briefing.briefing_generator.collect_operational_data")
    @patch("src.briefing.briefing_generator.collect_financial_data")
    def test_generate_briefing_success(self, mock_fin, mock_ops, mock_social):
        from src.briefing.briefing_generator import generate_briefing
        import tempfile

        mock_fin.return_value = {
            "status": "success",
            "current": {
                "total_revenue": 8000, "total_expenses": 3000, "net_cash_flow": 2000,
                "outstanding_receivables": 1500, "overdue_count": 0, "overdue_amount": 0,
                "invoice_count": 5, "payment_count": 3,
            },
            "previous": None,
        }
        mock_ops.return_value = {
            "services": {}, "scheduler_runs": 10, "scheduler_success": 9, "scheduler_failed": 1,
        }
        mock_social.return_value = {"platforms": {}, "total_posts": 0, "total_engagements": 0}

        with tempfile.TemporaryDirectory() as tmpdir:
            result = generate_briefing(tmpdir)
            assert result["status"] == "generated"
            assert os.path.exists(result["file_path"])
            assert len(result["sections"]) == 5


class TestFormatCurrency(unittest.TestCase):
    def test_format_positive(self):
        from src.briefing.briefing_generator import _format_currency

        assert _format_currency(1500.50) == "$1,500.50"

    def test_format_none(self):
        from src.briefing.briefing_generator import _format_currency

        assert _format_currency(None) == "N/A"


if __name__ == "__main__":
    unittest.main()
