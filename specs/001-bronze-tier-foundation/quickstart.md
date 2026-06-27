# Quickstart: Bronze Tier Foundation

**Branch**: `001-bronze-tier-foundation` | **Date**: 2026-02-12

## Prerequisites

- Python 3.13+ installed
- Obsidian installed (any recent version)
- Claude Code CLI installed and authenticated
- A Gmail account with access to Google Cloud Console

## Step 1: Clone and Setup

```bash
git clone <repo-url>
cd aiemployee
git checkout 001-bronze-tier-foundation
```

## Step 2: Install Python Dependencies

```bash
pip install google-api-python-client google-auth-oauthlib python-frontmatter pyyaml
```

## Step 3: Create Gmail OAuth2 Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing)
3. Enable the **Gmail API**
4. Create **OAuth 2.0 Client ID** credentials (Desktop application type)
5. Download the credentials file as `credentials.json`
6. Place `credentials.json` in the project root (it is gitignored)

## Step 4: Initialize the Vault

```bash
python src/scripts/setup_vault.py --vault-path ./vault
```

This creates:
```
vault/
├── Dashboard.md
├── Company_Handbook.md
├── Inbox/
├── Needs_Action/
└── Done/
```

Open `vault/` as a vault in Obsidian to verify.

## Step 5: Configure and Run the Watcher

```bash
python src/watchers/gmail_watcher.py --vault-path ./vault --interval 60
```

On first run, a browser window opens for Gmail OAuth. After authorization,
`token.json` is saved locally (gitignored). The watcher then polls every
60 seconds for new unread emails.

**Test it**: Send yourself an email. Within 60 seconds, check
`vault/Needs_Action/` for a new `.md` file.

## Step 6: Process Inbox with Claude Code

```bash
claude /process-inbox
```

Or invoke skills individually:
```bash
claude /vault-read --folder Needs_Action
claude /vault-write --path Done/report.md --content "..."
```

After processing, check:
- `vault/Done/` for processed reports
- `vault/Dashboard.md` for updated summary

## Step 7: Verify Success Criteria

| Criteria | How to verify |
|----------|--------------|
| SC-001: Vault setup < 5 min | Time Steps 2-4 |
| SC-002: Watcher detects email < 2 min | Send test email, time file creation |
| SC-003: Processing skill zero crashes | Run 10 times with varied `/Needs_Action` content |
| SC-004: Dashboard accuracy | Compare Dashboard.md with actual vault state |
| SC-005: Skills work independently | Invoke each `/vault-read`, `/vault-write` alone |
| SC-006: No secrets in repo | Run `git grep -r "token\|secret\|credential"` |

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `credentials.json` not found | Re-download from Google Cloud Console |
| OAuth browser window doesn't open | Run on a machine with a browser; or use `--no-browser` flag and paste URL manually |
| Watcher lock file error | Delete `.watcher.lock` if the previous run crashed |
| Gmail API rate limit | Increase `--interval` to 120+ seconds |
| Frontmatter parse error | Check that `.md` files in `/Needs_Action` have valid YAML between `---` markers |
