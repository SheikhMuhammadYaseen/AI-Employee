#!/usr/bin/env python3
"""Scheduler for the Personal AI Employee — Silver Tier.

Runs enabled components (watchers, approval checker) sequentially on a
configurable interval. Uses a lock file to prevent overlapping runs.

Usage:
    python src/scheduling/scheduler.py --config src/scheduling/scheduler_config.json
    python src/scheduling/scheduler.py --config src/scheduling/scheduler_config.json --once
    python src/scheduling/scheduler.py --vault-path ./vault --once
"""

import argparse
import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("scheduler")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from src.watchers.base_watcher import LockFile

import frontmatter


def _load_config(config_path: str | None, vault_path: str | None) -> dict:
    """Load scheduler configuration from JSON file or defaults."""
    if config_path and Path(config_path).exists():
        with open(config_path, encoding="utf-8") as f:
            config = json.load(f)
    else:
        config = {
            "interval_minutes": 5,
            "vault_path": vault_path or "./vault",
            "log_path": str(Path(vault_path or "./vault") / "Logs"),
            "components": {
                "approval_checker": {
                    "enabled": True,
                    "script": "src/approval/checker.py",
                    "args": ["--vault-path", vault_path or "./vault"],
                },
            },
        }

    # Override vault_path if provided via CLI
    if vault_path:
        config["vault_path"] = vault_path
        config["log_path"] = str(Path(vault_path) / "Logs")

    return config


def _run_component(name: str, component: dict, vault_path: str) -> dict:
    """Run a single component subprocess. Returns result dict."""
    script = component.get("script", "")
    args = component.get("args", [])

    # Replace vault-path placeholder in args
    resolved_args = [
        vault_path if a == "./vault" else a for a in args
    ]

    cmd = [sys.executable, script] + resolved_args
    start_time = datetime.now(timezone.utc)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(Path(__file__).resolve().parent.parent.parent),
        )
        elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()

        return {
            "name": name,
            "status": "success" if result.returncode == 0 else "error",
            "returncode": result.returncode,
            "elapsed_seconds": round(elapsed, 2),
            "stdout": result.stdout[:500] if result.stdout else "",
            "stderr": result.stderr[:500] if result.stderr else "",
        }
    except subprocess.TimeoutExpired:
        return {
            "name": name,
            "status": "timeout",
            "returncode": -1,
            "elapsed_seconds": 120,
            "stdout": "",
            "stderr": "Component timed out after 120 seconds",
        }
    except Exception as e:
        return {
            "name": name,
            "status": "error",
            "returncode": -1,
            "elapsed_seconds": 0,
            "stdout": "",
            "stderr": str(e),
        }


def _write_run_log(vault_path: str, results: list[dict]) -> Path:
    """Write a scheduler run log to /Logs."""
    log_dir = Path(vault_path) / "Logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    now = datetime.now(timezone.utc)
    ts = now.strftime("%Y%m%dT%H%M%S")
    filename = f"scheduler-{ts}.md"

    success_count = sum(1 for r in results if r["status"] == "success")
    fail_count = len(results) - success_count

    components_summary = "\n".join(
        f"- **{r['name']}**: {r['status']} ({r['elapsed_seconds']}s)"
        + (f" — {r['stderr'][:100]}" if r["status"] != "success" and r["stderr"] else "")
        for r in results
    )

    post = frontmatter.Post(
        content=(
            f"# Scheduler Run: {now.strftime('%Y-%m-%d %H:%M:%S')} UTC\n\n"
            f"**Components run**: {len(results)}\n"
            f"**Successful**: {success_count}\n"
            f"**Failed**: {fail_count}\n\n"
            f"## Results\n\n{components_summary}\n"
        ),
        type="scheduler_log",
        timestamp=now.isoformat(),
        components_run=len(results),
        successful=success_count,
        failed=fail_count,
    )

    log_path = log_dir / filename
    log_path.write_text(frontmatter.dumps(post), encoding="utf-8")
    logger.info("Scheduler log: %s", filename)
    return log_path


def run_cycle(config: dict) -> list[dict]:
    """Run one scheduler cycle: all enabled components sequentially."""
    vault_path = config.get("vault_path", "./vault")
    components = config.get("components", {})
    results = []

    for name, comp in components.items():
        if not comp.get("enabled", False):
            logger.info("Skipping disabled component: %s", name)
            continue

        logger.info("Running component: %s", name)
        result = _run_component(name, comp, vault_path)
        results.append(result)

        if result["status"] != "success":
            logger.warning(
                "Component %s failed (rc=%d): %s. Continuing with remaining components.",
                name, result["returncode"], result["stderr"][:200],
            )
        else:
            logger.info("Component %s completed successfully.", name)

    _write_run_log(vault_path, results)
    return results


def run_scheduler(config: dict, once: bool = False):
    """Main scheduler loop."""
    vault_path = config.get("vault_path", "./vault")
    interval = config.get("interval_minutes", 5) * 60

    lock = LockFile(Path(vault_path) / ".scheduler.lock")
    if not lock.acquire():
        logger.error("Scheduler already running. Exiting.")
        sys.exit(1)

    try:
        logger.info(
            "Scheduler started. Interval: %d min. Vault: %s",
            config.get("interval_minutes", 5), vault_path,
        )

        while True:
            run_cycle(config)

            if once:
                logger.info("Single run complete (--once).")
                break

            logger.info("Sleeping %d seconds until next cycle...", interval)
            time.sleep(interval)

    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user.")
    finally:
        lock.release()


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Scheduler for the Personal AI Employee."
    )
    parser.add_argument(
        "--config", default=None,
        help="Path to scheduler_config.json.",
    )
    parser.add_argument(
        "--vault-path", default=None,
        help="Path to the Obsidian vault root.",
    )
    parser.add_argument(
        "--once", action="store_true",
        help="Run one cycle and exit.",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    if not args.config and not args.vault_path:
        logger.error("Provide --config or --vault-path.")
        sys.exit(1)

    config = _load_config(args.config, args.vault_path)
    run_scheduler(config, once=args.once)


if __name__ == "__main__":
    main()
