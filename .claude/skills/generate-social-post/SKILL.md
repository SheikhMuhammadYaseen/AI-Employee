---
name: generate-social-post
description: Generate social media post drafts for one or more platforms and place them in /Pending_Approval for human review.
---

# Generate Social Post
**Inputs**: `$ARGUMENTS` — topic or context for the post (e.g., "new product launch", "weekly update"). Optionally specify platform(s): mastodon, facebook, instagram, x, linkedin (defaults to all).
**Outputs**: Draft social post(s) in /Pending_Approval with approval checkboxes
**Error Handling**: If Company Handbook not found, use defaults. Platform-specific content limits enforced (Mastodon: 500, X: 280, LinkedIn: 3000).

## Instructions

You are the AI Employee generating social media posts. Follow these steps precisely:

### Step 1: Read Company Handbook

Read `vault/Company_Handbook.md` for:
- Brand voice and tone guidelines
- Topics to promote or avoid
- Hashtag preferences
- Any posting schedule or frequency rules

### Step 2: Generate Post Content

Based on `$ARGUMENTS` and Company Handbook guidelines, generate platform-specific content:

**Per-platform limits:**
- Mastodon: max 500 characters
- X (Twitter): max 280 characters
- Facebook: max 2000 characters (recommended <500)
- Instagram: max 2200 characters (caption)
- LinkedIn: max 3000 characters

1. Write content adapted to each target platform's character limit
2. Include relevant hashtags (2-3 max)
3. Use the brand voice from Company Handbook
4. Focus on value to the audience (not just self-promotion)
5. If the topic is unclear, write a general business update post
6. For Instagram, note that an image_url is required (suggest a placeholder)

### Step 3: Create Approval Draft

Create a draft file in `vault/Pending_Approval/` with:
- Filename: `social-[timestamp]-[slug].md`
- YAML frontmatter (per platform):
  ```yaml
  type: [platform]-post
  target: [platform]
  mcp_tool: [mastodon_post|facebook_post|instagram_post|x_post|linkedin_post]
  status: pending
  created_date: [ISO timestamp]
  visibility: public
  ```
- Body:
  ```markdown
  ## Content

  [Generated post text — max 500 chars]

  ## Preview

  **Characters**: [count]/500
  **Hashtags**: [list]
  **Visibility**: public

  ## Approval

  Review the post above and check one:

  - [ ] Approved
  - [ ] Rejected

  **Notes**: [Optional — edit the content above before approving]
  ```

### Step 4: Report

Report:
- Draft filename and path
- Character count
- Post preview
- Instruction: "Edit the post in Obsidian if needed, then check 'Approved' to publish."
