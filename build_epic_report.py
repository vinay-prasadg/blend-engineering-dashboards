#!/usr/bin/env python3
"""Build Epic-to-Story mapping report by pulling live data from JIRA REST API."""
import json, os, sys, time
from datetime import datetime

try:
    import requests
except ImportError:
    sys.exit("Install requests: pip3 install requests")

CONFIG_PATH = os.path.expanduser('~/.cursor/mcp.json')
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), 'epic-story-mapping.html')

PROJECTS = ['APEX', 'BAI', 'CBP', 'CLN', 'DA', 'DD', 'DDINDIA', 'QUAL', 'RHL', 'SENG']

def load_creds():
    with open(CONFIG_PATH) as f:
        cfg = json.load(f)
    env = cfg['mcpServers']['mcp-atlassian']['env']
    return env['JIRA_URL'], env['JIRA_USERNAME'], env['JIRA_API_TOKEN']

def jira_search(base_url, auth, jql, fields=None, max_results=100):
    """Paginated JQL search using the new POST /search/jql endpoint."""
    if fields is None:
        fields = ['summary', 'status', 'priority', 'assignee', 'parent', 'issuetype']
    all_issues = []
    next_token = None
    while True:
        body = {'jql': jql, 'fields': fields, 'maxResults': max_results}
        if next_token:
            body['nextPageToken'] = next_token
        resp = requests.post(
            f'{base_url}/rest/api/3/search/jql',
            auth=auth, json=body, timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        issues = data.get('issues', [])
        all_issues.extend(issues)
        if data.get('isLast', True) or not issues:
            break
        next_token = data.get('nextPageToken')
        if not next_token:
            break
        time.sleep(0.2)
    return all_issues

def jira_count(base_url, auth, jql):
    """Count issues matching JQL without fetching them."""
    body = {'jql': jql, 'fields': ['key'], 'maxResults': 1}
    resp = requests.post(f'{base_url}/rest/api/3/search/jql', auth=auth, json=body, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    count = len(data.get('issues', []))
    if not data.get('isLast', True):
        all_issues = jira_search(base_url, auth, jql, fields=['key'], max_results=100)
        return len(all_issues)
    return count

def parse_issue(raw):
    f = raw.get('fields', {})
    status = f.get('status', {}) or {}
    priority = f.get('priority', {}) or {}
    assignee = f.get('assignee', {}) or {}
    parent = f.get('parent', {}) or {}
    itype = f.get('issuetype', {}) or {}
    return {
        'key': raw['key'],
        'summary': f.get('summary', ''),
        'status': status.get('name', ''),
        'status_cat': status.get('statusCategory', {}).get('name', ''),
        'priority': priority.get('name', ''),
        'assignee': assignee.get('displayName', 'Unassigned') if assignee else 'Unassigned',
        'type': itype.get('name', 'Story'),
        'parent_key': parent.get('key', ''),
    }


def main():
    base_url, username, token = load_creds()
    auth = (username, token)
    print(f"Connecting to {base_url} as {username}...")

    all_epics = {}
    epic_children = {}

    for proj in PROJECTS:
        print(f"\n--- {proj} ---")
        # Fetch active epics (not Done)
        jql_epics = f'issuetype = Epic AND project = {proj} AND statusCategory != Done ORDER BY priority ASC, key ASC'
        raw_epics = jira_search(base_url, auth, jql_epics)
        print(f"  Epics (active): {len(raw_epics)}")

        for raw in raw_epics:
            ep = parse_issue(raw)
            ep['project'] = proj
            all_epics[ep['key']] = ep
            if ep['key'] not in epic_children:
                epic_children[ep['key']] = {}

        # Fetch all non-epic active issues with parents
        jql_children = f'project = {proj} AND issuetype != Epic AND statusCategory != Done ORDER BY key ASC'
        raw_children = jira_search(base_url, auth, jql_children)
        print(f"  Active children: {len(raw_children)}")

        linked = 0
        orphan = 0
        for raw in raw_children:
            child = parse_issue(raw)
            parent_key = child['parent_key']
            if parent_key and parent_key in all_epics:
                if parent_key not in epic_children:
                    epic_children[parent_key] = {}
                epic_children[parent_key][child['key']] = child
                linked += 1
            elif parent_key:
                if parent_key not in epic_children:
                    epic_children[parent_key] = {}
                    all_epics[parent_key] = {
                        'key': parent_key, 'summary': f'(Epic not in active set)',
                        'status': 'Unknown', 'status_cat': '', 'priority': '',
                        'assignee': 'Unknown', 'project': parent_key.split('-')[0],
                    }
                epic_children[parent_key][child['key']] = child
                linked += 1
            else:
                orphan += 1
        print(f"  Linked to epics: {linked}, Orphans: {orphan}")

        # Also fetch Done children for known active epics (for progress %)
        epic_keys = [k for k in all_epics if all_epics[k].get('project') == proj]
        if epic_keys:
            batch_size = 30
            for i in range(0, len(epic_keys), batch_size):
                batch = epic_keys[i:i+batch_size]
                parents_jql = ', '.join(batch)
                jql_done = f'parent in ({parents_jql}) AND statusCategory = Done ORDER BY key ASC'
                try:
                    raw_done = jira_search(base_url, auth, jql_done)
                    for raw in raw_done:
                        child = parse_issue(raw)
                        pk = child['parent_key']
                        if pk not in epic_children:
                            epic_children[pk] = {}
                        epic_children[pk][child['key']] = child
                    print(f"  Done children (batch {i//batch_size+1}): {len(raw_done)}")
                except Exception as e:
                    print(f"  Warning fetching done children: {e}")

    # Build epic_data structure
    epic_data = {}
    for key, ep in all_epics.items():
        children = list(epic_children.get(key, {}).values())
        bugs = [c for c in children if c.get('type', '').lower() == 'bug']
        done = sum(1 for c in children if c.get('status_cat') == 'Done')
        in_prog = sum(1 for c in children if c.get('status_cat') == 'In Progress')
        todo = sum(1 for c in children if c.get('status_cat') == 'To Do')
        epic_data[key] = {
            **ep,
            'stories': children,
            'story_count': len(children),
            'bug_count': len(bugs),
            'done': done,
            'in_progress': in_prog,
            'todo': todo,
        }

    # Group by project
    projects = {}
    for key, ep in epic_data.items():
        proj = ep.get('project', key.split('-')[0])
        if proj not in projects:
            projects[proj] = []
        projects[proj].append(ep)

    priority_order = {'P0': 0, 'P1': 1, 'P2': 2, 'P3': 3, 'P4': 4}
    for proj in projects:
        projects[proj].sort(key=lambda e: (priority_order.get(e.get('priority', '')[:2], 5), e['key']))

    proj_list = sorted(projects.keys())
    total_epics = len(epic_data)
    total_stories = sum(e['story_count'] for e in epic_data.values())
    total_bugs = sum(e['bug_count'] for e in epic_data.values())

    # Count orphans per project
    orphan_counts = {}
    for proj in PROJECTS:
        jql_orphans = f'project = {proj} AND issuetype != Epic AND parent IS EMPTY AND statusCategory != Done'
        try:
            orphan_counts[proj] = jira_count(base_url, auth, jql_orphans)
        except Exception as e:
            print(f"  Warning counting orphans for {proj}: {e}")
            orphan_counts[proj] = 0
        print(f"  {proj} orphans: {orphan_counts[proj]}")
        time.sleep(0.1)
    total_orphans = sum(max(0, v) for v in orphan_counts.values())

    proj_colors = {
        'DDINDIA': '#22d3ee', 'CLN': '#60a5fa', 'CBP': '#a78bfa',
        'DD': '#34d399', 'SENG': '#fb923c', 'IMB': '#f87171',
        'DA': '#c084fc', 'RHL': '#f472b6', 'APEX': '#38bdf8',
        'BAI': '#facc15', 'QUAL': '#4ade80',
    }

    def clr(p): return proj_colors.get(p, '#94a3b8')
    def bg(p):
        c = proj_colors.get(p, '#94a3b8')
        r, g, b = int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16)
        return f"rgba({r},{g},{b},.12)"
    def pbadge(p):
        if 'P0' in p: return 'badge-p0'
        if 'P1' in p: return 'badge-p1'
        if 'P2' in p: return 'badge-p2'
        if 'P3' in p: return 'badge-p3'
        return 'badge-p4'
    def sbadge(s):
        sl = s.lower()
        if 'done' in sl or 'resolved' in sl or 'complete' in sl: return 'badge-done'
        if 'progress' in sl or 'review' in sl or 'dev' in sl: return 'badge-progress'
        if 'block' in sl or 'cancel' in sl: return 'badge-blocked'
        if 'qa' in sl: return 'badge-qa'
        return 'badge-todo'
    def esc(s): return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

    now = datetime.now().strftime('%B %d, %Y %I:%M %p')

    # ── Build HTML ────────────────────────────────────────────────────
    h = []
    h.append(f'''<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Epic &rarr; Story &amp; Bug Mapping — All Projects | Blend Engineering</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"></script>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Segoe UI',system-ui,-apple-system,sans-serif;background:#070b14;color:#e2e8f0;min-height:100vh}}
.container{{max-width:1560px;margin:0 auto;padding:24px}}
header{{text-align:center;padding:32px 0 12px;border-bottom:1px solid rgba(99,102,241,.25);margin-bottom:28px}}
header h1{{font-size:2rem;font-weight:700;background:linear-gradient(135deg,#818cf8,#a78bfa,#c084fc);-webkit-background-clip:text;-webkit-text-fill-color:transparent}}
header p{{color:#94a3b8;font-size:.95rem;margin-top:6px}}
.ts{{color:#64748b;font-size:.75rem;margin-top:4px}}
.kpi-row{{display:grid;grid-template-columns:repeat(5,1fr);gap:16px;margin-bottom:28px}}
.kpi{{background:linear-gradient(135deg,#111827 0%,#1a1f3a 100%);border:1px solid rgba(99,102,241,.15);border-radius:14px;padding:22px;text-align:center}}
.kpi .val{{font-size:2.2rem;font-weight:800}}.kpi .lbl{{font-size:.82rem;color:#94a3b8;margin-top:6px;text-transform:uppercase;letter-spacing:.5px}}
.section-title{{font-size:1.15rem;font-weight:700;color:#a5b4fc;margin:28px 0 16px;padding-left:12px;border-left:3px solid #6366f1}}
.grid-2{{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:24px}}
.card{{background:linear-gradient(135deg,#111827 0%,#151c32 100%);border:1px solid rgba(99,102,241,.12);border-radius:14px;padding:22px}}
.card h3{{font-size:.95rem;font-weight:600;color:#a5b4fc;margin-bottom:16px;display:flex;align-items:center;gap:8px}}
.chart-wrap{{width:100%;height:300px}}
canvas{{display:block}}
.toolbar{{position:sticky;top:0;z-index:20;background:#070b14;padding:16px 0 12px;border-bottom:1px solid rgba(99,102,241,.1);margin-bottom:20px}}
.search-row{{display:flex;gap:12px;align-items:center;margin-bottom:12px}}
.search-input{{flex:1;max-width:400px;padding:10px 16px;border-radius:10px;border:1px solid rgba(99,102,241,.2);background:#111827;color:#e2e8f0;font-size:.88rem;outline:none;transition:border-color .2s}}
.search-input:focus{{border-color:rgba(99,102,241,.5)}}
.search-input::placeholder{{color:#475569}}
.toolbar-actions{{display:flex;gap:8px;margin-left:auto}}
.action-btn{{padding:8px 16px;border-radius:8px;border:1px solid rgba(99,102,241,.2);background:transparent;color:#94a3b8;font-size:.78rem;cursor:pointer;font-weight:600;transition:all .15s}}
.action-btn:hover{{background:rgba(99,102,241,.12);color:#a5b4fc}}
.filter-bar{{display:flex;gap:8px;flex-wrap:wrap}}
.filter-btn{{padding:7px 16px;border-radius:8px;border:1px solid rgba(99,102,241,.2);background:transparent;color:#94a3b8;font-size:.8rem;cursor:pointer;font-weight:600;transition:all .15s}}
.filter-btn:hover,.filter-btn.active{{background:rgba(99,102,241,.15);color:#a5b4fc;border-color:rgba(99,102,241,.4)}}
.page-controls{{display:flex;gap:8px;align-items:center;justify-content:center;margin:24px 0}}
.page-btn{{padding:8px 18px;border-radius:8px;border:1px solid rgba(99,102,241,.2);background:transparent;color:#94a3b8;font-size:.82rem;cursor:pointer;font-weight:600;transition:all .15s}}
.page-btn:hover{{background:rgba(99,102,241,.12);color:#a5b4fc}}
.page-btn.active{{background:rgba(99,102,241,.2);color:#a5b4fc;border-color:rgba(99,102,241,.4)}}
.page-btn:disabled{{opacity:.3;cursor:default}}
.page-info{{color:#64748b;font-size:.82rem}}
.epic-block{{background:rgba(17,24,39,.8);border:1px solid rgba(99,102,241,.1);border-radius:12px;margin-bottom:16px;overflow:hidden}}
.epic-header{{padding:14px 20px;display:flex;align-items:center;gap:10px;cursor:pointer;border-bottom:1px solid rgba(99,102,241,.06)}}
.epic-header:hover{{background:rgba(99,102,241,.03)}}
.epic-key a{{color:#818cf8;text-decoration:none;font-weight:700;font-size:.88rem}}.epic-key a:hover{{text-decoration:underline}}
.epic-summary{{flex:1;font-size:.92rem;color:#e2e8f0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.epic-meta{{display:flex;gap:6px;align-items:center}}
.story-count{{background:rgba(99,102,241,.15);color:#818cf8;padding:2px 10px;border-radius:10px;font-size:.72rem;font-weight:600}}
.progress-bar{{width:100px;height:6px;background:rgba(148,163,184,.15);border-radius:3px;overflow:hidden}}
.progress-fill{{height:100%;border-radius:3px;background:linear-gradient(90deg,#34d399,#6ee7b7)}}
.toggle-icon{{color:#64748b;font-size:.75rem;transition:transform .2s}}
.epic-block.open .toggle-icon{{transform:rotate(90deg)}}
.story-list{{display:none;padding:0}}.epic-block.open .story-list{{display:block}}
.story-row{{display:grid;grid-template-columns:110px 68px 1fr 90px 130px 170px;gap:10px;padding:10px 20px;border-bottom:1px solid rgba(99,102,241,.04);font-size:.84rem;align-items:center}}
.story-row:nth-child(even){{background:rgba(99,102,241,.02)}}
.story-row:hover{{background:rgba(99,102,241,.05)}}.story-row:last-child{{border-bottom:none}}
.story-row-header{{font-weight:600;color:#94a3b8;text-transform:uppercase;font-size:.72rem;letter-spacing:.5px;background:rgba(99,102,241,.04)}}
.story-key a{{color:#818cf8;text-decoration:none;font-weight:600;font-size:.78rem}}.story-key a:hover{{text-decoration:underline}}
.story-summary{{color:#cbd5e1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.no-stories{{padding:16px 20px;color:#64748b;font-size:.82rem;font-style:italic}}
.badge{{display:inline-block;padding:2px 10px;border-radius:12px;font-size:.68rem;font-weight:600;white-space:nowrap}}
.badge-p0{{background:rgba(248,113,113,.2);color:#f87171;border:1px solid rgba(248,113,113,.3)}}
.badge-p1{{background:rgba(251,146,60,.15);color:#fb923c;border:1px solid rgba(251,146,60,.25)}}
.badge-p2{{background:rgba(251,191,36,.12);color:#fbbf24}}.badge-p3{{background:rgba(148,163,184,.12);color:#94a3b8}}
.badge-p4{{background:rgba(100,116,139,.12);color:#64748b}}
.badge-todo{{background:rgba(148,163,184,.15);color:#94a3b8}}.badge-progress{{background:rgba(251,191,36,.15);color:#fbbf24}}
.badge-blocked{{background:rgba(248,113,113,.15);color:#f87171}}.badge-qa{{background:rgba(52,211,153,.15);color:#6ee7b7}}
.badge-done{{background:rgba(52,211,153,.15);color:#34d399}}
.badge-bug{{background:rgba(248,113,113,.18);color:#f87171;border:1px solid rgba(248,113,113,.25)}}
.badge-story{{background:rgba(96,165,250,.15);color:#60a5fa;border:1px solid rgba(96,165,250,.2)}}
.badge-task{{background:rgba(251,191,36,.15);color:#fbbf24;border:1px solid rgba(251,191,36,.2)}}
.proj-tag{{display:inline-block;padding:2px 10px;border-radius:6px;font-size:.72rem;font-weight:700}}
.proj-summary{{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:16px;margin-bottom:24px}}
.proj-card{{background:linear-gradient(135deg,#111827 0%,#151c32 100%);border-radius:12px;padding:20px;border-left:4px solid;transition:transform .15s}}
.proj-card:hover{{transform:translateY(-2px)}}
.proj-card h4{{font-size:1rem;font-weight:700;margin-bottom:8px}}.proj-card .stat{{font-size:.82rem;color:#94a3b8;margin-top:4px}}
.proj-card .stat strong{{color:#e2e8f0}}
footer{{text-align:center;padding:24px 0 16px;color:#475569;font-size:.72rem;border-top:1px solid rgba(99,102,241,.1);margin-top:32px}}
@media(max-width:1024px){{.kpi-row{{grid-template-columns:repeat(3,1fr)}}.grid-2{{grid-template-columns:1fr}}.story-row{{grid-template-columns:80px 50px 1fr 80px 100px 120px}}}}
</style></head><body><div class="container">
<header>
  <a href="index.html" style="display:inline-flex;align-items:center;gap:6px;text-decoration:none;color:#94a3b8;font-size:.78rem;font-weight:600;padding:5px 14px;border:1px solid rgba(99,102,241,.2);border-radius:8px;margin-bottom:12px;transition:all .15s" onmouseover="this.style.background='rgba(99,102,241,.15)';this.style.color='#a5b4fc'" onmouseout="this.style.background='transparent';this.style.color='#94a3b8'">&larr; Home</a>
  <h1>Epic &rarr; Story &amp; Bug Mapping — All Projects</h1>
  <p>Comprehensive view of active Epics and their child Stories, Bugs &amp; Tasks</p>
  <div class="ts">{' &bull; '.join(proj_list)} &mdash; Live data from JIRA &bull; {now}</div>
</header>''')

    h.append(f'''<div class="kpi-row">
  <div class="kpi"><div class="val" style="color:#a78bfa">{total_epics}</div><div class="lbl">Active Epics</div></div>
  <div class="kpi"><div class="val" style="color:#818cf8">{total_stories}</div><div class="lbl">Children Mapped</div></div>
  <div class="kpi"><div class="val" style="color:#f87171">{total_bugs}</div><div class="lbl">Bugs</div></div>
  <div class="kpi"><div class="val" style="color:#fb923c">{total_orphans}</div><div class="lbl">Orphan Items</div></div>
  <div class="kpi"><div class="val" style="color:#60a5fa">{len(proj_list)}</div><div class="lbl">Projects</div></div>
</div>''')

    h.append('<div class="section-title">Project Overview</div><div class="proj-summary">')
    for proj in proj_list:
        eps = projects.get(proj, [])
        sc = sum(e['story_count'] for e in eps)
        bc = sum(e['bug_count'] for e in eps)
        dc = sum(e['done'] for e in eps)
        pc = round(dc / sc * 100) if sc else 0
        active = sum(1 for e in eps if 'Progress' in e.get('status', ''))
        blocked = sum(1 for e in eps if 'Block' in e.get('status', ''))
        h.append(f'''<div class="proj-card" style="border-color:{clr(proj)}">
      <h4 style="color:{clr(proj)}">{proj}</h4>
      <div class="stat"><strong>{len(eps)}</strong> Epics &bull; <strong>{sc}</strong> Children &bull; <strong style="color:#f87171">{bc}</strong> Bugs</div>
      <div class="stat"><strong>{active}</strong> active &bull; <strong>{blocked}</strong> blocked &bull; <strong>{pc}%</strong> done</div>
    </div>''')
    h.append('</div>')

    h.append('''<div class="section-title">Distribution Charts</div>
<div class="grid-2">
  <div class="card"><h3>Epics by Project</h3><div class="chart-wrap"><canvas id="epicChart"></canvas></div></div>
  <div class="card"><h3>Epic Priority Distribution</h3><div class="chart-wrap"><canvas id="prioChart" width="500" height="300"></canvas></div></div>
</div>
<div class="grid-2">
  <div class="card"><h3>Epic Status Breakdown</h3><div class="chart-wrap"><canvas id="statusChart" width="500" height="300"></canvas></div></div>
  <div class="card"><h3>Bugs by Project</h3><div class="chart-wrap"><canvas id="bugChart"></canvas></div></div>
</div>''')

    # Toolbar + Epics
    h.append('<div class="section-title">Epic &rarr; Story Details</div>')
    h.append('''<div class="toolbar" id="epicToolbar">
  <div class="search-row">
    <input type="text" class="search-input" id="epicSearch" placeholder="Search epics by key, name, or assignee..." oninput="searchEpics(this.value)">
    <div class="toolbar-actions">
      <button class="action-btn" onclick="toggleAll(true)">Expand All</button>
      <button class="action-btn" onclick="toggleAll(false)">Collapse All</button>
    </div>
  </div>
  <div class="filter-bar">
    <button class="filter-btn active" onclick="filterProject('all')">All</button>''')
    for p in proj_list:
        h.append(f'    <button class="filter-btn" onclick="filterProject(\'{p}\')" style="border-color:{clr(p)}50">{p} ({len(projects.get(p, []))})</button>')
    h.append('''  </div>
</div>
<div id="pageInfo" class="page-info" style="text-align:center;margin-bottom:12px"></div>''')

    for proj in proj_list:
        for ep in projects.get(proj, []):
            stories = ep['stories']
            pct = round(ep['done'] / ep['story_count'] * 100) if ep['story_count'] else 0
            h.append(f'<div class="epic-block" data-project="{proj}">')
            h.append(f'<div class="epic-header" onclick="this.parentElement.classList.toggle(\'open\')">')
            h.append(f'<span class="toggle-icon">&#9654;</span>')
            h.append(f'<span class="proj-tag" style="background:{bg(proj)};color:{clr(proj)}">{proj}</span>')
            h.append(f'<span class="epic-key"><a href="https://blendlabs.atlassian.net/browse/{ep["key"]}" target="_blank">{ep["key"]}</a></span>')
            h.append(f'<span class="epic-summary">{esc(ep["summary"])}</span>')
            h.append(f'<span class="epic-meta">')
            prio_str = ep.get('priority', '')
            h.append(f'<span class="badge {pbadge(prio_str)}">{prio_str[:2] if prio_str else "?"}</span>')
            h.append(f'<span class="badge {sbadge(ep.get("status", ""))}">{esc(ep.get("status", "Unknown"))}</span>')
            if ep['story_count']:
                bug_label = f' / {ep["bug_count"]} bugs' if ep['bug_count'] else ''
                h.append(f'<span class="story-count">{ep["story_count"]} items{bug_label}</span>')
                h.append(f'<span class="progress-bar"><span class="progress-fill" style="width:{pct}%"></span></span>')
            else:
                h.append(f'<span class="story-count" style="color:#64748b">0 items</span>')
            h.append(f'</span></div>')

            h.append('<div class="story-list">')
            if stories:
                h.append('<div class="story-row story-row-header"><span>Key</span><span>Type</span><span>Summary</span><span>Priority</span><span>Status</span><span>Assignee</span></div>')
                for s in sorted(stories, key=lambda x: (0 if x.get('status_cat') == 'In Progress' else 1 if x.get('status_cat') == 'To Do' else 2, x['key'])):
                    itype = s.get('type', 'Story')
                    itype_cls = 'badge-bug' if itype.lower() == 'bug' else ('badge-task' if 'task' in itype.lower() else 'badge-story')
                    sp = s.get('priority', '')
                    h.append(f'<div class="story-row">')
                    h.append(f'<span class="story-key"><a href="https://blendlabs.atlassian.net/browse/{s["key"]}" target="_blank">{s["key"]}</a></span>')
                    h.append(f'<span><span class="badge {itype_cls}">{esc(itype)}</span></span>')
                    h.append(f'<span class="story-summary" title="{esc(s["summary"])}">{esc(s["summary"])}</span>')
                    h.append(f'<span><span class="badge {pbadge(sp)}">{sp[:2] if sp else "?"}</span></span>')
                    h.append(f'<span><span class="badge {sbadge(s.get("status", ""))}">{esc(s.get("status", ""))}</span></span>')
                    h.append(f'<span style="font-size:.72rem;color:#94a3b8">{esc(s.get("assignee", "Unassigned"))}</span>')
                    h.append(f'</div>')
            else:
                h.append('<div class="no-stories">No child stories mapped yet — click the Epic key to view in JIRA</div>')
            h.append('</div></div>')

    h.append('<div class="page-controls" id="pageControls"></div>')

    # Orphans section
    h.append('<div class="section-title">Orphan Stories &amp; Bugs (No Parent Epic)</div>')
    h.append('<p style="color:#94a3b8;font-size:.85rem;margin-bottom:20px">Active Stories and Bugs that are <strong style="color:#fb923c">not linked</strong> to any Epic.</p>')
    h.append('<div class="grid-2">')
    h.append('<div class="card"><h3>Orphans by Project</h3><div class="chart-wrap"><canvas id="orphanChart"></canvas></div></div>')
    h.append('<div class="card"><h3>Orphan Breakdown</h3><table style="width:100%;border-collapse:collapse;font-size:.82rem">')
    h.append('<tr style="border-bottom:1px solid rgba(99,102,241,.15);color:#94a3b8;text-align:left"><th style="padding:8px 12px">Project</th><th style="padding:8px 12px">Orphan Count</th></tr>')
    orphan_sorted = sorted(orphan_counts.items(), key=lambda x: -x[1])
    for pn, cnt in orphan_sorted:
        if cnt <= 0:
            continue
        h.append(f'<tr style="border-bottom:1px solid rgba(99,102,241,.06)">')
        h.append(f'<td style="padding:8px 12px"><span class="proj-tag" style="background:{bg(pn)};color:{clr(pn)}">{pn}</span></td>')
        h.append(f'<td style="padding:8px 12px"><strong style="color:#e2e8f0">{cnt}</strong></td>')
        h.append('</tr>')
    h.append(f'<tr style="border-top:2px solid rgba(99,102,241,.2);font-weight:700"><td style="padding:10px 12px;color:#a5b4fc">TOTAL</td><td style="padding:10px 12px;color:#fb923c;font-size:1rem">{total_orphans}</td></tr>')
    h.append('</table></div></div>')

    h.append(f'''<footer>Epic &rarr; Story &amp; Bug Mapping &bull; {' &bull; '.join(proj_list)} &bull; Live data from JIRA &bull; {now}</footer></div>''')

    # Charts JS
    p0 = sum(1 for e in epic_data.values() if 'P0' in e.get('priority', ''))
    p1 = sum(1 for e in epic_data.values() if 'P1' in e.get('priority', ''))
    p2 = sum(1 for e in epic_data.values() if 'P2' in e.get('priority', ''))
    p3 = sum(1 for e in epic_data.values() if 'P3' in e.get('priority', ''))
    st_todo = sum(1 for e in epic_data.values() if e.get('status_cat') == 'To Do' or (not e.get('status_cat') and 'To Do' in e.get('status', '')))
    st_prog = sum(1 for e in epic_data.values() if 'Progress' in e.get('status', ''))
    st_block = sum(1 for e in epic_data.values() if 'Block' in e.get('status', ''))

    J = json
    h.append(f'''<script>
Chart.defaults.color='#94a3b8';Chart.defaults.borderColor='rgba(99,102,241,0.06)';
Chart.defaults.font.family="'Segoe UI',system-ui,sans-serif";

new Chart(document.getElementById('epicChart'),{{
  type:'bar',data:{{labels:{J.dumps(proj_list)},datasets:[{{label:'Epics',
    data:{J.dumps([len(projects.get(p, [])) for p in proj_list])},
    backgroundColor:{J.dumps([clr(p) for p in proj_list])},
    borderWidth:0,borderRadius:4}}]}},
  options:{{responsive:true,maintainAspectRatio:false,plugins:{{legend:{{display:false}}}},
    scales:{{x:{{grid:{{display:false}}}},y:{{grid:{{color:'rgba(99,102,241,.05)'}},beginAtZero:true}}}}}}
}});

new Chart(document.getElementById('prioChart'),{{
  type:'doughnut',data:{{labels:['P0 Blocking','P1 Critical','P2 Major','P3 Minor'],
    datasets:[{{data:[{p0},{p1},{p2},{p3}],
      backgroundColor:['rgba(248,113,113,.7)','rgba(251,146,60,.7)','rgba(251,191,36,.6)','rgba(148,163,184,.5)'],
      borderWidth:0,hoverOffset:8}}]}},
  options:{{responsive:true,maintainAspectRatio:false,cutout:'60%',
    plugins:{{legend:{{position:'bottom',labels:{{padding:12,usePointStyle:true,pointStyleWidth:10,font:{{size:10}}}}}}}}}}
}});

new Chart(document.getElementById('statusChart'),{{
  type:'doughnut',data:{{labels:['To Do','In Progress','Blocked'],
    datasets:[{{data:[{st_todo},{st_prog},{st_block}],
      backgroundColor:['rgba(148,163,184,.5)','rgba(251,191,36,.7)','rgba(248,113,113,.7)'],
      borderWidth:0,hoverOffset:8}}]}},
  options:{{responsive:true,maintainAspectRatio:false,cutout:'60%',
    plugins:{{legend:{{position:'bottom',labels:{{padding:12,usePointStyle:true,pointStyleWidth:10,font:{{size:11}}}}}}}}}}
}});

new Chart(document.getElementById('bugChart'),{{
  type:'bar',data:{{labels:{J.dumps(proj_list)},datasets:[{{label:'Bugs',
    data:{J.dumps([sum(e['bug_count'] for e in projects.get(p, [])) for p in proj_list])},
    backgroundColor:{J.dumps([clr(p) for p in proj_list])},
    borderWidth:0,borderRadius:4}}]}},
  options:{{responsive:true,maintainAspectRatio:false,plugins:{{legend:{{display:false}}}},
    scales:{{x:{{grid:{{display:false}}}},y:{{grid:{{color:'rgba(99,102,241,.05)'}},beginAtZero:true}}}}}}
}});

const PAGE_SIZE=25;let currentPage=1;let currentFilter='all';let currentSearch='';
function getVisibleEpics(){{const blocks=Array.from(document.querySelectorAll('.epic-block'));return blocks.filter(el=>{{const matchProj=currentFilter==='all'||el.dataset.project===currentFilter;if(!matchProj)return false;if(!currentSearch)return true;return el.textContent.toLowerCase().includes(currentSearch.toLowerCase());}});}}
function renderPage(){{const visible=getVisibleEpics();const totalPages=Math.max(1,Math.ceil(visible.length/PAGE_SIZE));if(currentPage>totalPages)currentPage=totalPages;const start=(currentPage-1)*PAGE_SIZE;const end=start+PAGE_SIZE;document.querySelectorAll('.epic-block').forEach(el=>el.style.display='none');visible.forEach((el,i)=>{{el.style.display=(i>=start&&i<end)?'':'none';}});document.getElementById('pageInfo').textContent='Showing '+(start+1)+'-'+Math.min(end,visible.length)+' of '+visible.length+' epics';const ctrl=document.getElementById('pageControls');let btns='<button class="page-btn" onclick="goPage(1)" '+(currentPage===1?'disabled':'')+'>&laquo;</button>';btns+='<button class="page-btn" onclick="goPage('+(currentPage-1)+')" '+(currentPage===1?'disabled':'')+'>&lsaquo;</button>';for(let p=Math.max(1,currentPage-3);p<=Math.min(totalPages,currentPage+3);p++)btns+='<button class="page-btn '+(p===currentPage?'active':'')+'" onclick="goPage('+p+')">'+p+'</button>';btns+='<button class="page-btn" onclick="goPage('+(currentPage+1)+')" '+(currentPage>=totalPages?'disabled':'')+'>&rsaquo;</button>';btns+='<button class="page-btn" onclick="goPage('+totalPages+')" '+(currentPage>=totalPages?'disabled':'')+'>&raquo;</button>';ctrl.innerHTML=btns;}}
function goPage(p){{currentPage=p;renderPage();}}
function filterProject(proj){{document.querySelectorAll('.filter-btn').forEach(b=>b.classList.remove('active'));event.target.classList.add('active');currentFilter=proj;currentPage=1;renderPage();}}
function searchEpics(q){{currentSearch=q;currentPage=1;renderPage();}}
function toggleAll(expand){{const visible=getVisibleEpics();const start=(currentPage-1)*PAGE_SIZE;const end=start+PAGE_SIZE;visible.forEach((el,i)=>{{if(i>=start&&i<end){{if(expand)el.classList.add('open');else el.classList.remove('open');}}}});}}
renderPage();

(function(){{
  const orphanLabels={J.dumps([p for p, c in orphan_sorted if c > 0])};
  const orphanData={J.dumps([c for _, c in orphan_sorted if c > 0])};
  const orphanColors={J.dumps([clr(p) for p, c in orphan_sorted if c > 0])};
  new Chart(document.getElementById('orphanChart'),{{
    type:'bar',data:{{labels:orphanLabels,datasets:[{{label:'Orphans',data:orphanData,backgroundColor:orphanColors,borderWidth:0,borderRadius:4}}]}},
    options:{{indexAxis:'y',responsive:true,maintainAspectRatio:false,plugins:{{legend:{{display:false}}}},scales:{{x:{{grid:{{color:'rgba(99,102,241,.05)'}},beginAtZero:true}},y:{{grid:{{display:false}}}}}}}}
  }});
}})();
</script></body></html>''')

    with open(OUTPUT_PATH, 'w') as f:
        f.write('\n'.join(h))

    print(f'\nReport written to: {OUTPUT_PATH}')
    print(f'Epics: {total_epics} | Children: {total_stories} | Bugs: {total_bugs} | Orphans: {total_orphans}')
    for p in proj_list:
        eps = projects.get(p, [])
        bc = sum(e['bug_count'] for e in eps)
        print(f'  {p}: {len(eps)} epics, {sum(e["story_count"] for e in eps)} children ({bc} bugs), {orphan_counts.get(p, 0)} orphans')


if __name__ == '__main__':
    main()
