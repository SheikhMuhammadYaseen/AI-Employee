"""Path setup for dashboard — adds project root to sys.path."""

import sys
from pathlib import Path

# dashboard/ is one level below project root
DASHBOARD_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = DASHBOARD_DIR.parent

# Add project root so `from src.x import y` works
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Vault path (same default as src/)
VAULT_PATH = PROJECT_ROOT / "vault"
