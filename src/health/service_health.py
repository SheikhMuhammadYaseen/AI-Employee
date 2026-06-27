"""Service health tracker for Gold Tier.

Tracks operational status of external services (Odoo, Mastodon, Facebook, etc.).
Persists state to vault/.service_health.json.
Status transitions: operational -> degraded (3 failures) -> unavailable (6 failures).
Any success resets to operational (FR-017, FR-018).
"""

import json
import os
from datetime import datetime, timezone


CONSECUTIVE_FAILURES_DEGRADED = 3
CONSECUTIVE_FAILURES_UNAVAILABLE = 6


class ServiceHealthTracker:
    """Track and persist service health status."""

    def __init__(self, vault_path):
        self.vault_path = vault_path
        self.health_file = os.path.join(vault_path, ".service_health.json")
        self._health = self._load()

    def _load(self):
        """Load health state from JSON file."""
        if os.path.exists(self.health_file):
            try:
                with open(self.health_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def _save(self):
        """Persist health state to JSON file."""
        os.makedirs(os.path.dirname(self.health_file), exist_ok=True)
        with open(self.health_file, "w", encoding="utf-8") as f:
            json.dump(self._health, f, indent=2)

    def _ensure_service(self, service):
        """Initialize service entry if not present."""
        if service not in self._health:
            self._health[service] = {
                "status": "operational",
                "last_ok": None,
                "last_error": None,
                "error_count": 0,
                "last_error_message": None,
            }

    def update_health(self, service, success, error=None):
        """Update health status after a service call.

        Args:
            service: Service name (e.g., 'odoo', 'mastodon').
            success: True if call succeeded, False if failed.
            error: Error message string (if failed).
        """
        self._ensure_service(service)
        now = datetime.now(timezone.utc).isoformat()
        entry = self._health[service]

        if success:
            entry["status"] = "operational"
            entry["last_ok"] = now
            entry["error_count"] = 0
            entry["last_error_message"] = None
        else:
            entry["error_count"] += 1
            entry["last_error"] = now
            entry["last_error_message"] = str(error) if error else None

            if entry["error_count"] >= CONSECUTIVE_FAILURES_UNAVAILABLE:
                entry["status"] = "unavailable"
            elif entry["error_count"] >= CONSECUTIVE_FAILURES_DEGRADED:
                entry["status"] = "degraded"

        self._save()

    def get_health(self, service):
        """Get health status for a specific service.

        Returns:
            Dict with status, last_ok, last_error, error_count, last_error_message.
            Returns None if service not tracked.
        """
        return self._health.get(service)

    def get_all_health(self):
        """Get health status for all tracked services.

        Returns:
            Dict mapping service names to health dicts.
        """
        return dict(self._health)

    def is_operational(self, service):
        """Check if a service is operational."""
        entry = self._health.get(service)
        if entry is None:
            return True  # Unknown service assumed operational
        return entry["status"] == "operational"

    def get_unavailable_services(self):
        """Get list of services that are unavailable."""
        return [
            name for name, entry in self._health.items()
            if entry["status"] == "unavailable"
        ]

    def get_services_down_over(self, hours=1):
        """Get services that have been unavailable for more than N hours.

        Args:
            hours: Minimum hours of unavailability.

        Returns:
            List of (service_name, hours_down) tuples.
        """
        results = []
        now = datetime.now(timezone.utc)

        for name, entry in self._health.items():
            if entry["status"] == "unavailable" and entry.get("last_ok"):
                try:
                    last_ok = datetime.fromisoformat(entry["last_ok"])
                    if last_ok.tzinfo is None:
                        last_ok = last_ok.replace(tzinfo=timezone.utc)
                    hours_down = (now - last_ok).total_seconds() / 3600
                    if hours_down >= hours:
                        results.append((name, round(hours_down, 1)))
                except (ValueError, TypeError):
                    pass

        return results
