"""Ralph Wiggum autonomous task loop engine — Gold Tier.

Gold Tier — US4: Autonomous Multi-Step Task Completion (FR-012, FR-013, FR-014).
Parses Plan.md files, classifies steps, executes simple actions,
creates approval drafts for action steps, and iterates until TASK_COMPLETE.
"""

import logging
import os
import re
import time
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

MAX_ITERATIONS = 10
MAX_DURATION_MINUTES = 30
MAX_NESTING_DEPTH = 2

# Step type patterns
SIMPLE_PATTERNS = [
    r"read\b", r"analyze\b", r"summarize\b", r"classify\b",
    r"check\b", r"review\b", r"scan\b", r"process\b", r"log\b",
    r"archive\b", r"move\b", r"generate report\b", r"calculate\b",
]

ACTION_PATTERNS = [
    r"send\b", r"email\b", r"post\b", r"publish\b", r"tweet\b",
    r"create invoice\b", r"record payment\b", r"reply\b",
    r"forward\b", r"approve\b",
]


class LoopTimeout(Exception):
    """Raised when the loop exceeds max duration."""
    pass


class LoopMaxIterations(Exception):
    """Raised when the loop exceeds max iterations."""
    pass


class RalphWiggumLoop:
    """Autonomous task loop engine.

    Parses a Plan.md file, classifies each step, and iterates:
    - Simple steps: executed automatically.
    - Action steps: creates approval drafts in /Pending_Approval.
    - Re-checks after each iteration until all steps complete.
    """

    def __init__(self, vault_path, max_iterations=MAX_ITERATIONS,
                 max_duration_minutes=MAX_DURATION_MINUTES,
                 nesting_depth=0):
        self.vault_path = vault_path
        self.max_iterations = max_iterations
        self.max_duration_minutes = max_duration_minutes
        self.nesting_depth = nesting_depth
        self.start_time = None
        self.iteration = 0
        self.steps = []
        self.status = "idle"

    def parse_plan(self, plan_path):
        """Parse a Plan.md file and extract steps.

        Args:
            plan_path: Path to the Plan.md file.

        Returns:
            List of step dicts with index, text, step_type, status.
        """
        if not os.path.exists(plan_path):
            raise FileNotFoundError(f"Plan not found: {plan_path}")

        with open(plan_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.steps = []
        # Match markdown checkboxes: - [ ] or - [x]
        pattern = r"^-\s*\[([ xX])\]\s*(.+)$"
        for i, match in enumerate(re.finditer(pattern, content, re.MULTILINE)):
            checkbox, text = match.groups()
            completed = checkbox.lower() == "x"

            step = {
                "index": i,
                "text": text.strip(),
                "step_type": self._classify_step(text),
                "status": "completed" if completed else "pending",
                "line": match.group(0),
            }
            self.steps.append(step)

        return self.steps

    def _classify_step(self, text):
        """Classify a step as 'simple' or 'action_required'.

        Args:
            text: Step text content.

        Returns:
            'simple' or 'action_required'
        """
        text_lower = text.lower()

        for pattern in ACTION_PATTERNS:
            if re.search(pattern, text_lower):
                return "action_required"

        for pattern in SIMPLE_PATTERNS:
            if re.search(pattern, text_lower):
                return "simple"

        # Default to simple for unrecognized steps
        return "simple"

    def execute_step(self, step):
        """Execute a single simple step.

        Args:
            step: Step dict from parse_plan.

        Returns:
            Dict with status and details.
        """
        logger.info("Executing step %d: %s", step["index"], step["text"])

        # Simple steps are marked as completed
        step["status"] = "completed"

        self._log_step(step, "executed")

        return {
            "status": "completed",
            "step_index": step["index"],
            "step_text": step["text"],
        }

    def create_approval_draft(self, step):
        """Create an approval draft for an action step.

        Args:
            step: Step dict from parse_plan.

        Returns:
            Dict with status and draft path.
        """
        pending_dir = os.path.join(self.vault_path, "Pending_Approval")
        os.makedirs(pending_dir, exist_ok=True)

        timestamp = datetime.now(timezone.utc)
        ts_str = timestamp.strftime("%Y%m%dT%H%M%S")
        filename = f"loop-action-{ts_str}-step{step['index']}.md"
        filepath = os.path.join(pending_dir, filename)

        # Determine MCP tool from step text
        mcp_tool = self._infer_mcp_tool(step["text"])

        content = f"""---
type: loop-action
step_index: {step['index']}
step_text: "{step['text']}"
mcp_tool: "{mcp_tool}"
created: "{timestamp.isoformat()}"
status: pending
---

# Action Required: Step {step['index']}

**Step**: {step['text']}
**Suggested Tool**: {mcp_tool}

## Content

{step['text']}

## Approval

- [ ] Approved
- [ ] Rejected
"""

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        step["status"] = "awaiting_approval"
        step["draft_path"] = filepath

        self._log_step(step, "draft_created")

        logger.info("Created approval draft: %s", filename)

        return {
            "status": "awaiting_approval",
            "draft_path": filepath,
            "step_index": step["index"],
        }

    def _infer_mcp_tool(self, text):
        """Infer the MCP tool from step text."""
        text_lower = text.lower()
        if any(w in text_lower for w in ("email", "send email", "reply")):
            return "email_send"
        if any(w in text_lower for w in ("mastodon", "toot")):
            return "mastodon_post"
        if any(w in text_lower for w in ("facebook", "fb post")):
            return "facebook_post"
        if any(w in text_lower for w in ("instagram", "ig post")):
            return "instagram_post"
        if any(w in text_lower for w in ("tweet", "x post", "twitter")):
            return "x_post"
        if any(w in text_lower for w in ("invoice", "create invoice")):
            return "create_invoice"
        if any(w in text_lower for w in ("payment", "record payment")):
            return "record_payment"
        return "unknown"

    def check_approvals(self):
        """Check if any pending approval drafts have been approved.

        Returns:
            List of step indices whose approvals were processed.
        """
        processed = []
        pending_dir = os.path.join(self.vault_path, "Pending_Approval")

        if not os.path.isdir(pending_dir):
            return processed

        for step in self.steps:
            if step["status"] != "awaiting_approval":
                continue

            draft_path = step.get("draft_path")
            if not draft_path or not os.path.exists(draft_path):
                continue

            with open(draft_path, "r", encoding="utf-8") as f:
                content = f.read()

            if re.search(r"-\s*\[x\]\s*Approved", content, re.IGNORECASE):
                step["status"] = "completed"
                processed.append(step["index"])
                logger.info("Step %d approved and completed", step["index"])
            elif re.search(r"-\s*\[x\]\s*Rejected", content, re.IGNORECASE):
                step["status"] = "rejected"
                processed.append(step["index"])
                logger.info("Step %d rejected", step["index"])

        return processed

    def _check_time_limit(self):
        """Check if the loop has exceeded the time limit."""
        if self.start_time is None:
            return
        elapsed = datetime.now(timezone.utc) - self.start_time
        if elapsed > timedelta(minutes=self.max_duration_minutes):
            raise LoopTimeout(
                f"Loop exceeded {self.max_duration_minutes} minute limit "
                f"(elapsed: {elapsed.total_seconds():.0f}s)"
            )

    def run_iteration(self):
        """Run one iteration of the loop.

        Returns:
            Dict with iteration results.
        """
        self._check_time_limit()

        self.iteration += 1
        if self.iteration > self.max_iterations:
            raise LoopMaxIterations(
                f"Loop exceeded {self.max_iterations} iterations"
            )

        results = {
            "iteration": self.iteration,
            "executed": [],
            "drafts_created": [],
            "approvals_processed": [],
        }

        # Check for newly approved drafts
        results["approvals_processed"] = self.check_approvals()

        # Process pending steps
        for step in self.steps:
            if step["status"] != "pending":
                continue

            if step["step_type"] == "simple":
                result = self.execute_step(step)
                results["executed"].append(result)
            elif step["step_type"] == "action_required":
                result = self.create_approval_draft(step)
                results["drafts_created"].append(result)

        return results

    def is_complete(self):
        """Check if all steps are completed (or rejected)."""
        return all(
            s["status"] in ("completed", "rejected")
            for s in self.steps
        )

    def has_pending_approvals(self):
        """Check if any steps are awaiting approval."""
        return any(s["status"] == "awaiting_approval" for s in self.steps)

    def run(self, plan_path):
        """Run the full loop until complete or limits reached.

        Args:
            plan_path: Path to the Plan.md file.

        Returns:
            Dict with final status and summary.
        """
        if self.nesting_depth > MAX_NESTING_DEPTH:
            return {
                "status": "error",
                "error": f"Max nesting depth ({MAX_NESTING_DEPTH}) exceeded",
            }

        self.start_time = datetime.now(timezone.utc)
        self.status = "running"
        self.parse_plan(plan_path)

        if not self.steps:
            return {
                "status": "TASK_COMPLETE",
                "iterations": 0,
                "message": "No steps found in plan",
            }

        try:
            while not self.is_complete():
                result = self.run_iteration()

                # Update plan file with progress
                self._update_plan_file(plan_path)

                # If only awaiting approvals, pause
                if self.has_pending_approvals() and not any(
                    s["status"] == "pending" for s in self.steps
                ):
                    self.status = "paused_for_approval"
                    return {
                        "status": "AWAITING_APPROVAL",
                        "iterations": self.iteration,
                        "steps_completed": sum(
                            1 for s in self.steps if s["status"] == "completed"
                        ),
                        "steps_awaiting": sum(
                            1 for s in self.steps if s["status"] == "awaiting_approval"
                        ),
                        "steps_total": len(self.steps),
                    }

        except LoopTimeout as e:
            self.status = "timeout"
            return {
                "status": "LOOP_TIMEOUT",
                "iterations": self.iteration,
                "error": str(e),
                "steps_completed": sum(
                    1 for s in self.steps if s["status"] == "completed"
                ),
                "steps_total": len(self.steps),
            }
        except LoopMaxIterations as e:
            self.status = "max_iterations"
            return {
                "status": "LOOP_MAX_ITERATIONS",
                "iterations": self.iteration,
                "error": str(e),
                "steps_completed": sum(
                    1 for s in self.steps if s["status"] == "completed"
                ),
                "steps_total": len(self.steps),
            }

        self.status = "complete"
        elapsed = (datetime.now(timezone.utc) - self.start_time).total_seconds()

        return {
            "status": "TASK_COMPLETE",
            "iterations": self.iteration,
            "elapsed_seconds": round(elapsed, 1),
            "steps_completed": sum(
                1 for s in self.steps if s["status"] == "completed"
            ),
            "steps_rejected": sum(
                1 for s in self.steps if s["status"] == "rejected"
            ),
            "steps_total": len(self.steps),
        }

    def _update_plan_file(self, plan_path):
        """Update the Plan.md file with step completion status."""
        try:
            with open(plan_path, "r", encoding="utf-8") as f:
                content = f.read()

            for step in self.steps:
                if step["status"] == "completed":
                    # Replace [ ] with [x]
                    content = content.replace(step["line"], step["line"].replace("[ ]", "[x]"))

            with open(plan_path, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception as e:
            logger.warning("Failed to update plan file: %s", e)

    def _log_step(self, step, action):
        """Log a step action to the audit log."""
        try:
            from src.logging.audit_logger import log_action
            log_action(
                self.vault_path,
                "loop",
                action,
                details={
                    "step_index": step["index"],
                    "step_text": step["text"],
                    "step_type": step["step_type"],
                    "result": step["status"],
                    "iteration": self.iteration,
                    "context": f"Ralph Wiggum Loop iteration {self.iteration}",
                },
            )
        except Exception as e:
            logger.warning("Failed to log step: %s", e)

    def get_progress(self):
        """Get current loop progress summary."""
        return {
            "status": self.status,
            "iteration": self.iteration,
            "steps_total": len(self.steps),
            "steps_completed": sum(1 for s in self.steps if s["status"] == "completed"),
            "steps_pending": sum(1 for s in self.steps if s["status"] == "pending"),
            "steps_awaiting": sum(1 for s in self.steps if s["status"] == "awaiting_approval"),
            "steps_rejected": sum(1 for s in self.steps if s["status"] == "rejected"),
        }
