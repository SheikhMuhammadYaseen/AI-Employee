"""Per-service connection test functions."""

import smtplib
import socket
from pathlib import Path

import requests

# Timeout for all connection tests (seconds)
CONNECTION_TIMEOUT = 10


def test_connection(service_name: str, credentials: dict) -> dict:
    """Dispatch connection test to the appropriate service handler.

    Args:
        service_name: Service key (gmail, odoo, linkedin, etc.).
        credentials: Dict of env key -> value for the service.

    Returns:
        {"success": bool, "message": str, "details": str or None}
    """
    testers = {
        "gmail": _test_gmail,
        "odoo": _test_odoo,
        "linkedin": _test_linkedin,
        "mastodon": _test_mastodon,
        "facebook": _test_facebook,
        "instagram": _test_instagram,
        "x_twitter": _test_x_twitter,
        "whatsapp": _test_whatsapp,
    }
    tester = testers.get(service_name)
    if not tester:
        return {"success": False, "message": f"Unknown service: {service_name}", "details": None}

    try:
        result = tester(credentials)
    except Exception as e:
        result = {"success": False, "message": f"Unexpected error: {type(e).__name__}", "details": str(e)}

    # Update health tracker on success
    if result.get("success"):
        _update_health(service_name, success=True)
    else:
        _update_health(service_name, success=False, error=result.get("message"))

    return result


def _update_health(service_name: str, success: bool, error=None):
    """Update ServiceHealthTracker if available."""
    try:
        from src.health.service_health import ServiceHealthTracker
        from dashboard.utils.path_setup import VAULT_PATH
        tracker = ServiceHealthTracker(str(VAULT_PATH))
        tracker.update_health(service_name, success=success, error=error)
    except Exception:
        pass  # Health tracking is best-effort


def _test_gmail(creds: dict) -> dict:
    """Test Gmail SMTP login (no email sent)."""
    address = creds.get("GMAIL_ADDRESS", "").strip()
    password = creds.get("GMAIL_APP_PASSWORD", "").strip()
    if not address or not password:
        return {"success": False, "message": "Gmail address and app password are required.", "details": None}

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587, timeout=CONNECTION_TIMEOUT)
        server.ehlo()
        server.starttls()
        server.login(address, password)
        server.quit()
        return {"success": True, "message": "SMTP login verified.", "details": f"Authenticated as {address}"}
    except smtplib.SMTPAuthenticationError:
        return {
            "success": False,
            "message": "Authentication failed. Check your app password.",
            "details": "Ensure you're using a 16-character App Password, not your regular password.",
        }
    except (socket.timeout, socket.gaierror, OSError) as e:
        return {"success": False, "message": "Could not connect to Gmail SMTP.", "details": str(e)}


def _test_odoo(creds: dict) -> dict:
    """Test Odoo connection via common.version endpoint."""
    url = creds.get("ODOO_URL", "").strip().rstrip("/")
    db = creds.get("ODOO_DB", "").strip()
    user = creds.get("ODOO_USER", "").strip()
    password = creds.get("ODOO_PASSWORD", "").strip()
    if not url:
        return {"success": False, "message": "Odoo URL is required.", "details": None}

    try:
        resp = requests.post(
            f"{url}/jsonrpc",
            json={
                "jsonrpc": "2.0",
                "method": "call",
                "params": {"service": "common", "method": "version", "args": []},
                "id": 1,
            },
            timeout=CONNECTION_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        result = data.get("result", {})
        version = result.get("server_version", "unknown")
        return {
            "success": True,
            "message": f"Odoo {version} reachable.",
            "details": f"URL: {url}, DB: {db or '(not set)'}",
        }
    except requests.ConnectionError:
        return {"success": False, "message": f"Cannot connect to {url}.", "details": "Is the Odoo server running?"}
    except requests.Timeout:
        return {"success": False, "message": "Connection timed out.", "details": None}
    except Exception as e:
        return {"success": False, "message": f"Odoo test failed: {e}", "details": None}


def _test_linkedin(creds: dict) -> dict:
    """Test LinkedIn API access via profile endpoint."""
    token = creds.get("LINKEDIN_ACCESS_TOKEN", "").strip()
    if not token:
        return {"success": False, "message": "LinkedIn access token is required.", "details": None}

    try:
        resp = requests.get(
            "https://api.linkedin.com/v2/me",
            headers={"Authorization": f"Bearer {token}"},
            timeout=CONNECTION_TIMEOUT,
        )
        if resp.status_code == 200:
            name = resp.json().get("localizedFirstName", "User")
            return {"success": True, "message": "LinkedIn connected.", "details": f"Authenticated as {name}"}
        elif resp.status_code == 401:
            return {"success": False, "message": "Invalid or expired token.", "details": "Generate a new token at linkedin.com/developers"}
        else:
            return {"success": False, "message": f"LinkedIn API returned {resp.status_code}.", "details": resp.text[:200]}
    except requests.Timeout:
        return {"success": False, "message": "Connection timed out.", "details": None}
    except Exception as e:
        return {"success": False, "message": f"LinkedIn test failed: {e}", "details": None}


def _test_mastodon(creds: dict) -> dict:
    """Test Mastodon credentials via verify_credentials endpoint."""
    instance = creds.get("MASTODON_INSTANCE_URL", "").strip().rstrip("/")
    token = creds.get("MASTODON_ACCESS_TOKEN", "").strip()
    if not instance or not token:
        return {"success": False, "message": "Instance URL and access token are required.", "details": None}

    try:
        resp = requests.get(
            f"{instance}/api/v1/accounts/verify_credentials",
            headers={"Authorization": f"Bearer {token}"},
            timeout=CONNECTION_TIMEOUT,
        )
        if resp.status_code == 200:
            username = resp.json().get("username", "user")
            return {"success": True, "message": "Mastodon connected.", "details": f"@{username}@{instance.split('//')[1]}"}
        elif resp.status_code == 401:
            return {"success": False, "message": "Invalid token.", "details": "Check your access token in Preferences > Development"}
        else:
            return {"success": False, "message": f"Mastodon API returned {resp.status_code}.", "details": resp.text[:200]}
    except requests.ConnectionError:
        return {"success": False, "message": f"Cannot connect to {instance}.", "details": "Check the instance URL."}
    except Exception as e:
        return {"success": False, "message": f"Mastodon test failed: {e}", "details": None}


def _test_facebook(creds: dict) -> dict:
    """Test Facebook Page access via Graph API."""
    page_id = creds.get("META_PAGE_ID", "").strip()
    token = creds.get("META_PAGE_ACCESS_TOKEN", "").strip()
    if not page_id or not token:
        return {"success": False, "message": "Page ID and access token are required.", "details": None}

    try:
        resp = requests.get(
            f"https://graph.facebook.com/v19.0/{page_id}",
            params={"access_token": token, "fields": "name,id"},
            timeout=CONNECTION_TIMEOUT,
        )
        if resp.status_code == 200:
            name = resp.json().get("name", "Page")
            return {"success": True, "message": "Facebook Page connected.", "details": f"Page: {name}"}
        elif resp.status_code == 190 or "OAuthException" in resp.text:
            return {"success": False, "message": "Invalid or expired token.", "details": "Regenerate in Meta Business Suite"}
        else:
            return {"success": False, "message": f"Facebook API returned {resp.status_code}.", "details": resp.text[:200]}
    except Exception as e:
        return {"success": False, "message": f"Facebook test failed: {e}", "details": None}


def _test_instagram(creds: dict) -> dict:
    """Test Instagram Business account via Graph API."""
    ig_user_id = creds.get("META_IG_USER_ID", "").strip()
    token = creds.get("META_PAGE_ACCESS_TOKEN", "").strip()
    if not ig_user_id or not token:
        return {"success": False, "message": "IG User ID and access token are required.", "details": None}

    try:
        resp = requests.get(
            f"https://graph.facebook.com/v19.0/{ig_user_id}",
            params={"access_token": token, "fields": "username,id"},
            timeout=CONNECTION_TIMEOUT,
        )
        if resp.status_code == 200:
            username = resp.json().get("username", "user")
            return {"success": True, "message": "Instagram connected.", "details": f"@{username}"}
        elif resp.status_code == 190 or "OAuthException" in resp.text:
            return {"success": False, "message": "Invalid or expired token.", "details": "Uses the same Meta Page Access Token as Facebook"}
        else:
            return {"success": False, "message": f"Instagram API returned {resp.status_code}.", "details": resp.text[:200]}
    except Exception as e:
        return {"success": False, "message": f"Instagram test failed: {e}", "details": None}


def _test_x_twitter(creds: dict) -> dict:
    """Test X/Twitter credentials via tweepy client."""
    api_key = creds.get("X_API_KEY", "").strip()
    api_secret = creds.get("X_API_SECRET", "").strip()
    access_token = creds.get("X_ACCESS_TOKEN", "").strip()
    access_secret = creds.get("X_ACCESS_SECRET", "").strip()

    if not all([api_key, api_secret, access_token, access_secret]):
        return {"success": False, "message": "All four API keys are required.", "details": None}

    try:
        import tweepy
        client = tweepy.Client(
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_secret,
        )
        me = client.get_me()
        if me and me.data:
            return {"success": True, "message": "X/Twitter connected.", "details": f"@{me.data.username}"}
        return {"success": False, "message": "Could not verify credentials.", "details": None}
    except ImportError:
        return {
            "success": False,
            "message": "tweepy package not installed.",
            "details": "Run: pip install tweepy",
        }
    except Exception as e:
        err = str(e)
        if "401" in err or "Unauthorized" in err:
            return {"success": False, "message": "Invalid credentials.", "details": "Check your API keys at developer.twitter.com"}
        return {"success": False, "message": f"X/Twitter test failed: {e}", "details": None}


def _test_whatsapp(creds: dict) -> dict:
    """WhatsApp has no API credentials — return info message."""
    return {
        "success": True,
        "message": "WhatsApp uses browser-based QR code scanning.",
        "details": "Use the WhatsApp Watcher to connect via QR code.",
    }
