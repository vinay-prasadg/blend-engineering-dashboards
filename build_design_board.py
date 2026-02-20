#!/usr/bin/env python3
"""
Fetch all JIRA issues labeled 'design' created in 2026 across all projects,
then regenerate design-board.html with the live data injected.

Usage:
    python3 build_design_board.py

Requires:
    pip install requests

Environment variables:
    JIRA_URL        — Base URL (default: https://blendlabs.atlassian.net)
    JIRA_USER       — Email for basic auth
    JIRA_API_TOKEN  — API token (https://id.atlassian.com/manage-profile/security/api-tokens)
"""

import json
import os
import re
import sys
from datetime import datetime

try:
    import requests
except ImportError:
    sys.exit("ERROR: 'requests' not installed. Run: pip install requests")

JIRA_URL = os.environ.get("JIRA_URL", "https://blendlabs.atlassian.net")
JIRA_USER = os.environ.get("JIRA_USER", "")
JIRA_API_TOKEN = os.environ.get("JIRA_API_TOKEN", "")

JQL = 'labels = design AND created >= "2026-01-01" ORDER BY priority ASC, updated DESC'
FIELDS = "summary,status,assignee,priority,issuetype,labels,project,updated,created"
MAX_RESULTS = 100

HTML_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "design-board.html")
MARKER = "/* %%ISSUE_DATA%% */"


def fetch_issues():
    """Fetch all design-labeled issues from JIRA using REST API."""
    if not JIRA_USER or not JIRA_API_TOKEN:
        print("WARNING: JIRA_USER and JIRA_API_TOKEN not set.")
        print("Set them as environment variables to fetch live data.")
        print("  export JIRA_USER='you@example.com'")
        print("  export JIRA_API_TOKEN='your-token'")
        return []

    auth = (JIRA_USER, JIRA_API_TOKEN)
    headers = {"Accept": "application/json"}
    all_issues = []
    start_at = 0

    while True:
        params = {
            "jql": JQL,
            "fields": FIELDS,
            "maxResults": MAX_RESULTS,
            "startAt": start_at,
        }
        resp = requests.get(
            f"{JIRA_URL}/rest/api/3/search",
            headers=headers,
            auth=auth,
            params=params,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()

        for raw in data.get("issues", []):
            fields = raw.get("fields", {})
            status_name = (fields.get("status") or {}).get("name", "")
            status_cat_raw = (
                (fields.get("status") or {})
                .get("statusCategory", {})
                .get("name", "")
            )

            assignee_obj = fields.get("assignee") or {}
            assignee = assignee_obj.get("displayName", "Unassigned")

            priority_obj = fields.get("priority") or {}
            priority = priority_obj.get("name", "")

            issue_type = (fields.get("issuetype") or {}).get("name", "Task")
            project_key = (fields.get("project") or {}).get("key", "")
            labels = fields.get("labels", [])

            updated = fields.get("updated", "")
            if updated:
                try:
                    updated = datetime.fromisoformat(
                        updated.replace("Z", "+00:00")
                    ).strftime("%b %d")
                except Exception:
                    updated = updated[:10]

            cat = categorize_status(status_name, status_cat_raw)

            all_issues.append(
                {
                    "key": raw["key"],
                    "project": project_key,
                    "type": issue_type,
                    "summary": (fields.get("summary") or "").replace("'", "\\'"),
                    "priority": priority,
                    "status": status_name,
                    "statusCategory": cat,
                    "assignee": assignee.replace("'", "\\'"),
                    "labels": labels,
                    "updated": updated,
                }
            )

        total = data.get("total", 0)
        start_at += MAX_RESULTS
        if start_at >= total or not data.get("issues"):
            break

    return all_issues


def categorize_status(status, jira_category=""):
    """Map a JIRA status to a board column."""
    s = status.lower()
    jc = jira_category.lower()

    if jc == "done":
        return "done"
    if "done" in s or "resolved" in s or "closed" in s or "released" in s:
        return "done"
    if "review" in s or "qa" in s or "testing" in s or "verified" in s:
        return "review"
    if "progress" in s or "dev" in s or "active" in s:
        return "in_progress"
    if "to do" in s or "open" in s or "new" in s or "ready" in s or "selected" in s:
        return "todo"
    if "backlog" in s:
        return "backlog"

    if jc == "in progress":
        return "in_progress"
    if jc == "new" or jc == "to do":
        return "todo"

    return "backlog"


def inject_data(issues):
    """Replace the ISSUE_DATA marker in design-board.html with real data."""
    if not os.path.exists(HTML_PATH):
        sys.exit(f"ERROR: {HTML_PATH} not found. Ensure design-board.html exists.")

    with open(HTML_PATH, "r") as f:
        html = f.read()

    js_array = json.dumps(issues, ensure_ascii=False)

    old_pattern = r"const ISSUES = \[.*?\];\s*/\* %%ISSUE_DATA%% \*/"
    replacement = f"const ISSUES = {js_array};\n{MARKER}"

    new_html, count = re.subn(old_pattern, replacement, html, flags=re.DOTALL)
    if count == 0:
        sys.exit("ERROR: Could not find ISSUE_DATA marker in design-board.html")

    with open(HTML_PATH, "w") as f:
        f.write(new_html)

    return len(issues)


def main():
    print(f"Design Board Builder")
    print(f"  JQL: {JQL}")
    print(f"  Target: {HTML_PATH}")
    print()

    issues = fetch_issues()

    if not issues:
        print("No issues fetched. Board will show empty state.")
        print("To populate with live data, set JIRA_USER and JIRA_API_TOKEN.")
        return

    count = inject_data(issues)
    projects = sorted(set(i["project"] for i in issues))

    print(f"SUCCESS: Injected {count} issues into design-board.html")
    print(f"  Projects: {', '.join(projects)}")
    print(f"  Statuses: {dict_summary(issues, 'statusCategory')}")
    print(f"  Types:    {dict_summary(issues, 'type')}")


def dict_summary(issues, key):
    counts = {}
    for i in issues:
        v = i.get(key, "unknown")
        counts[v] = counts.get(v, 0) + 1
    return ", ".join(f"{k}: {v}" for k, v in sorted(counts.items()))


if __name__ == "__main__":
    main()
