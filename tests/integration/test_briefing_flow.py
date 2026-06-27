"""Integration test for CEO Briefing flow (T029)."""

import os
import tempfile
import unittest
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock


class TestBriefingFlow(unittest.TestCase):
    """Test full briefing generation with mock Odoo data and real vault."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.tmpdir, "Logs"), exist_ok=True)
        os.makedirs(os.path.join(self.tmpdir, "Done"), exist_ok=True)

    @patch("src.mcp.tools.odoo_reports.get_financial_summary")
    def test_full_briefing_generation(self, mock_summary):
        from src.briefing.briefing_generator import generate_briefing

        mock_summary.return_value = {
            "status": "success",
            "total_revenue": 10000,
            "total_expenses": 4000,
            "net_cash_flow": 3000,
            "outstanding_receivables": 2000,
            "overdue_count": 1,
            "overdue_amount": 500,
            "invoice_count": 8,
            "payment_count": 5,
        }

        result = generate_briefing(self.tmpdir)
        assert result["status"] == "generated"
        assert os.path.exists(result["file_path"])
        assert len(result["sections"]) == 5

        with open(result["file_path"]) as f:
            content = f.read()
        assert "Financial Summary" in content
        assert "Operational Status" in content
        assert "Bottlenecks" in content

    @patch("src.mcp.tools.odoo_reports.get_financial_summary")
    def test_briefing_archives_previous(self, mock_summary):
        from src.briefing.briefing_generator import generate_briefing

        mock_summary.return_value = {
            "status": "success", "total_revenue": 0, "total_expenses": 0,
            "net_cash_flow": 0, "outstanding_receivables": 0,
            "overdue_count": 0, "overdue_amount": 0,
            "invoice_count": 0, "payment_count": 0,
        }

        briefing_path = os.path.join(self.tmpdir, "Briefing.md")
        with open(briefing_path, "w") as f:
            f.write("# Previous Briefing\n")

        result = generate_briefing(self.tmpdir)
        assert result["status"] == "generated"

        done_files = os.listdir(os.path.join(self.tmpdir, "Done"))
        assert any("briefing-" in f for f in done_files)


if __name__ == "__main__":
    unittest.main()
