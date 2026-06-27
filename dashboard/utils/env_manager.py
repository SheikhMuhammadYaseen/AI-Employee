"""Safe .env file read/write utilities."""

import os
import tempfile
from pathlib import Path


def read_env(env_path) -> dict:
    """Parse .env file into key-value dict.

    Args:
        env_path: Path to .env file.

    Returns:
        Dict of environment variable names to values.
    """
    env_path = Path(env_path)
    result = {}
    if not env_path.exists():
        return result
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            result[key.strip()] = value.strip()
    return result


def write_env(env_path, updates: dict):
    """Update specific keys in .env while preserving comments, ordering, and unrelated keys.

    If a key exists, update its value. If not, append it.
    Uses atomic write (temp file + rename) to prevent corruption.

    Args:
        env_path: Path to .env file.
        updates: Dict of key-value pairs to set.
    """
    env_path = Path(env_path)
    lines = []
    updated_keys = set()

    if env_path.exists():
        lines = env_path.read_text(encoding="utf-8").splitlines()

    new_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            key, _, _ = stripped.partition("=")
            key = key.strip()
            if key in updates:
                new_lines.append(f"{key}={updates[key]}")
                updated_keys.add(key)
                continue
        new_lines.append(line)

    # Append keys that weren't found in existing file
    for key, value in updates.items():
        if key not in updated_keys:
            new_lines.append(f"{key}={value}")

    content = "\n".join(new_lines)
    if not content.endswith("\n"):
        content += "\n"

    # Atomic write: write to temp file in same directory, then rename
    env_path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(
        dir=str(env_path.parent), suffix=".tmp", prefix=".env_"
    )
    try:
        os.write(fd, content.encode("utf-8"))
        os.close(fd)
        # On Windows, target must not exist for rename
        if env_path.exists():
            env_path.unlink()
        os.rename(tmp_path, str(env_path))
    except Exception:
        try:
            os.close(fd)
        except OSError:
            pass
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


def is_placeholder(value: str) -> bool:
    """Check if a value is a known placeholder.

    Args:
        value: Environment variable value to check.

    Returns:
        True if the value looks like a placeholder.
    """
    if not value or not value.strip():
        return True
    v = value.strip().lower()
    placeholders = [
        "your-", "your_", "changeme", "replace-",
        "xxx", "todo", "placeholder", "example",
    ]
    return any(v.startswith(p) for p in placeholders)
