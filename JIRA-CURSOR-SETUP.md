# How to Connect JIRA Boards to Cursor

Cursor can use JIRA (and Confluence) through the **Model Context Protocol (MCP)**. Once connected, the AI in **Composer** can search issues, read tickets, and use JIRA data in chat—including for boards like **Documents & Delivery**.

---

## Option 1: Atlassian MCP Server (Docker) — Recommended

### What you need

- **Docker** installed and running
- **Atlassian Cloud** account (JIRA)
- **API token** from [Atlassian API tokens](https://id.atlassian.com/manage-profile/security/api-tokens)

### Step 1: Create an Atlassian API token

1. Go to [https://id.atlassian.com/manage-profile/security/api-tokens](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Click **Create API token**
3. Name it (e.g. “Cursor MCP”) and copy the token (you won’t see it again)

### Step 2: Add the MCP server in Cursor

1. In Cursor: **File → Preferences → Cursor Settings** (or **Cursor → Settings** on macOS)
2. Open the **MCP** tab
3. Click **Add new global MCP server** (or **+ Add New MCP Server**)
4. Add a server with this config (edit the placeholders):

Replace:

- `YOUR_ATLASSIAN_EMAIL` → your Atlassian account email
- `YOUR_API_TOKEN` → the token you created
- `your-instance` → your JIRA/Atlassian site name (e.g. `mycompany` if your URL is `mycompany.atlassian.net`)

**JSON configuration:**

```json
{
  "mcpServers": {
    "mcp-atlassian": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-e", "CONFLUENCE_URL",
        "-e", "CONFLUENCE_USERNAME",
        "-e", "CONFLUENCE_API_TOKEN",
        "-e", "JIRA_URL",
        "-e", "JIRA_USERNAME",
        "-e", "JIRA_API_TOKEN",
        "ghcr.io/sooperset/mcp-atlassian:latest",
        "--read-only"
      ],
      "env": {
        "CONFLUENCE_URL": "https://your-instance.atlassian.net/wiki",
        "CONFLUENCE_USERNAME": "YOUR_ATLASSIAN_EMAIL",
        "CONFLUENCE_API_TOKEN": "YOUR_API_TOKEN",
        "JIRA_URL": "https://your-instance.atlassian.net",
        "JIRA_USERNAME": "YOUR_ATLASSIAN_EMAIL",
        "JIRA_API_TOKEN": "YOUR_API_TOKEN",
        "READ_ONLY_MODE": "true"
      }
    }
  }
}
```

5. Save. Cursor will start the Docker container and load the JIRA/Confluence tools.

### Step 3: Use it in Composer (e.g. Documents & Delivery)

In **Composer** (Agent/Chat), you can ask in plain language, for example:

- *“Show production defects from the Documents & Delivery JIRA board.”*
- *“List open issues in the Documents & Delivery project.”*
- *“Search JIRA for issues in project DOC with status Open.”*

The AI will use the MCP tools (e.g. JQL search, get issue) and show results in the chat.

**Tip:** If your board is tied to a **project key** (e.g. `DOC`, `DEL`), you can say:  
*“List issues from JIRA project DOC”* or *“Show me Documents & Delivery board issues.”*

---

## Option 2: Official Atlassian Rovo MCP Server

Atlassian provides an official MCP server that works with Cursor.

### Requirements

- **Node.js v18+**
- Atlassian Cloud + API token (same as above)

### Setup

1. In Cursor: **Cursor Settings → MCP → Add new global MCP server**
2. Configure connection to: `https://mcp.atlassian.com/v1/mcp`
3. Use **SSE** as the transport type and follow any in-UI prompts to sign in or provide credentials (see [Atlassian Rovo MCP docs](https://support.atlassian.com/atlassian-rovo-mcp-server/docs/setting-up-ides/) for current steps).

This gives you official Atlassian-backed JIRA (and Confluence) tools in Cursor.

---

## Option 3: Confluence & JIRA community MCP (stdio)

Another option is the [Confluence and JIRA MCP](https://github.com/zereight/confluence-mcp) from Cursor Directory.

1. **Cursor Settings → Features → MCP → + Add New MCP Server**
2. **Type:** `stdio`
3. **Command:** set according to the repo (e.g. a `node` or `npx` command to run the server)
4. Configure any required env vars (JIRA URL, API token, etc.) as described in that repo’s README.

---

## Where Cursor stores MCP config

- **Global MCP servers:** configured in the MCP section of Cursor Settings (UI).  
- **Config file (if used):** `~/.cursor/mcp.json` (macOS/Linux) for Cursor 0.47+.

Environment variables and API tokens stay on your machine and are not sent to the LLM.

---

## Quick reference: what you can do after connecting

| Action | Example prompt |
|--------|-----------------|
| List your tickets | “List all tickets assigned to me that are In Progress.” |
| Board/project issues | “Show production defects from the Documents & Delivery JIRA board.” |
| One issue | “Get details for JIRA issue DOC-123.” |
| Compare code to ticket | “Compare `src/features/delivery/Form.tsx` with JIRA issue DEL-777.” |
| Test plan from ticket | “Generate a test plan from the acceptance criteria of issue DEL-777.” |

Use **Composer** (not only the inline chat) so the agent can call the JIRA MCP tools.

---

## Troubleshooting

- **“No JIRA tools”**  
  Confirm the MCP server is enabled in Cursor Settings → MCP and that Docker is running (for Option 1). Restart Cursor if needed.

- **Auth errors**  
  Regenerate an API token at [Atlassian API tokens](https://id.atlassian.com/manage-profile/security/api-tokens) and update the `env` block in your MCP config.

- **Documents & Delivery not found**  
  In JIRA, note the **project key** (e.g. `DOC`, `DEL`) for the Documents & Delivery board. Use that in prompts: “List issues from project DOC” or “Show Documents & Delivery board issues.”

- **Read-only**  
  Keeping `READ_ONLY_MODE: "true"` (Option 1) only allows reading from JIRA/Confluence, which is safer; the AI won’t create or update issues.

Once this is set up, you can ask Cursor to “show production defects for Documents & Delivery JIRA boards” directly in Composer.
