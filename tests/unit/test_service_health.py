"""Unit tests for service health tracker (T012)."""

import json
import os
import tempfile
import unittest
from unittest.mock import patch
from datetime import datetime, timezone, timedelta

from src.health.service_health import (
    ServiceHealthTracker,
    CONSECUTIVE_FAILURES_DEGRADED,
    CONSECUTIVE_FAILURES_UNAVAILABLE,
)


class TestServiceHealthTracker(unittest.TestCase):
    """Test ServiceHealthTracker."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def _tracker(self):
        return ServiceHealthTracker(self.tmpdir)

    def test_initial_state_empty(self):
        tracker = self._tracker()
        assert tracker.get_all_health() == {}

    def test_success_creates_operational_entry(self):
        tracker = self._tracker()
        tracker.update_health("odoo", success=True)

        health = tracker.get_health("odoo")
        assert health["status"] == "operational"
        assert health["last_ok"] is not None
        assert health["error_count"] == 0

    def test_single_failure_stays_operational(self):
        tracker = self._tracker()
        tracker.update_health("odoo", success=True)
        tracker.update_health("odoo", success=False, error="Connection refused")

        health = tracker.get_health("odoo")
        assert health["status"] == "operational"
        assert health["error_count"] == 1
        assert health["last_error_message"] == "Connection refused"

    def test_three_failures_becomes_degraded(self):
        tracker = self._tracker()
        for i in range(CONSECUTIVE_FAILURES_DEGRADED):
            tracker.update_health("odoo", success=False, error="fail")

        health = tracker.get_health("odoo")
        assert health["status"] == "degraded"
        assert health["error_count"] == CONSECUTIVE_FAILURES_DEGRADED

    def test_six_failures_becomes_unavailable(self):
        tracker = self._tracker()
        for i in range(CONSECUTIVE_FAILURES_UNAVAILABLE):
            tracker.update_health("odoo", success=False, error="fail")

        health = tracker.get_health("odoo")
        assert health["status"] == "unavailable"

    def test_success_resets_to_operational(self):
        tracker = self._tracker()
        for i in range(CONSECUTIVE_FAILURES_UNAVAILABLE):
            tracker.update_health("odoo", success=False)

        assert tracker.get_health("odoo")["status"] == "unavailable"

        tracker.update_health("odoo", success=True)
        health = tracker.get_health("odoo")
        assert health["status"] == "operational"
        assert health["error_count"] == 0

    def test_persists_to_json(self):
        tracker = self._tracker()
        tracker.update_health("mastodon", success=True)

        # Load fresh tracker from same directory
        tracker2 = ServiceHealthTracker(self.tmpdir)
        health = tracker2.get_health("mastodon")
        assert health["status"] == "operational"

    def test_json_file_location(self):
        tracker = self._tracker()
        tracker.update_health("odoo", success=True)

        json_path = os.path.join(self.tmpdir, ".service_health.json")
        assert os.path.exists(json_path)

        with open(json_path, "r") as f:
            data = json.load(f)
        assert "odoo" in data

    def test_multiple_services_tracked(self):
        tracker = self._tracker()
        tracker.update_health("odoo", success=True)
        tracker.update_health("mastodon", success=False, error="rate limit")
        tracker.update_health("facebook", success=True)

        all_health = tracker.get_all_health()
        assert len(all_health) == 3
        assert all_health["odoo"]["status"] == "operational"
        assert all_health["mastodon"]["error_count"] == 1

    def test_is_operational(self):
        tracker = self._tracker()
        tracker.update_health("odoo", success=True)
        assert tracker.is_operational("odoo") is True

        for i in range(CONSECUTIVE_FAILURES_UNAVAILABLE):
            tracker.update_health("odoo", success=False)
        assert tracker.is_operational("odoo") is False

    def test_unknown_service_assumed_operational(self):
        tracker = self._tracker()
        assert tracker.is_operational("unknown_service") is True

    def test_get_unavailable_services(self):
        tracker = self._tracker()
        tracker.update_health("odoo", success=True)
        for i in range(CONSECUTIVE_FAILURES_UNAVAILABLE):
            tracker.update_health("facebook", success=False)

        unavailable = tracker.get_unavailable_services()
        assert "facebook" in unavailable
        assert "odoo" not in unavailable

    def test_get_health_none_for_untracked(self):
        tracker = self._tracker()
        assert tracker.get_health("nonexistent") is None

    def test_degraded_to_operational_on_success(self):
        tracker = self._tracker()
        for i in range(CONSECUTIVE_FAILURES_DEGRADED):
            tracker.update_health("odoo", success=False)
        assert tracker.get_health("odoo")["status"] == "degraded"

        tracker.update_health("odoo", success=True)
        assert tracker.get_health("odoo")["status"] == "operational"

    def test_corrupted_json_starts_fresh(self):
        json_path = os.path.join(self.tmpdir, ".service_health.json")
        with open(json_path, "w") as f:
            f.write("not valid json{{{")

        tracker = self._tracker()
        assert tracker.get_all_health() == {}
        tracker.update_health("odoo", success=True)
        assert tracker.get_health("odoo")["status"] == "operational"


if __name__ == "__main__":
    unittest.main()
