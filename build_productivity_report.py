#!/usr/bin/env python3
"""Build Resource Productivity Report from JIRA data.

Reads resolved-issue JSON files from the agent-tools cache,
aggregates per-engineer metrics (story points, issues completed),
and generates a rich HTML dashboard.
"""
import json, os, sys
from datetime import datetime
from collections import defaultdict

BASE = '/Users/vinay-prasadg/.cursor/projects/Users-vinay-prasadg-Documents-Production-Defects/agent-tools'
OUT  = '/Users/vinay-prasadg/Documents/Production Defects/resource-productivity.html'

# ── Data files: per-project resolved issues (first 50 per project) ────
project_files = {
    'CBP':     ['2be3e20c-0253-42b9-858c-07a769a87b6f.txt'],
    'SENG':    ['1c931d17-9792-4bb5-b778-7ccaa2fba4d3.txt'],
    'DDINDIA': ['a8e4353c-110a-431d-b54d-d520bca4a6fe.txt'],
    'DA':      ['8040f8e8-f2ba-41d7-88c6-27d597367de8.txt'],
    'RHL':     ['309843fd-df34-4863-9c50-6950dd3b9aae.txt'],
    'APEX':    ['c778544d-3007-4972-b45e-da6a6647092c.txt'],
    'BAI':     ['0751da9f-a79f-48ac-a353-e70ccab2a9b1.txt'],
    'DD':      ['93aa649c-5a3e-4c26-a471-d1dd9930229e.txt'],
    'QUAL':    ['ad4bae5d-4117-4210-8d73-d991deceffbf.txt'],
}

# Quarterly data files (first 50 across all projects per quarter)
quarterly_files = {
    'Q3 2025': '5fef0df8-3a0d-4ebf-b74d-991269f32ab7.txt',
    'Q4 2025': 'd47ab3fe-5fde-4b9b-9f44-816abd263bc3.txt',
    'Q1 2026': '73785260-470c-4a00-b64e-5c777e41d605.txt',
}

# ── Project display names and colors ──────────────────────────────────
proj_names = {
    'CBP': 'Config Platform', 'SENG': 'Software Engineering',
    'DDINDIA': 'D&D India', 'DA': 'Deposit Accounts',
    'RHL': 'Reverse HL', 'APEX': 'APEX', 'BAI': 'Blend AI',
    'DD': 'Documents & Delivery', 'QUAL': 'Quality',
    'CLN': 'Consumer Lending',
}
proj_colors = {
    'CBP': '#818cf8', 'SENG': '#34d399', 'DDINDIA': '#fb923c',
    'DA': '#f87171', 'RHL': '#60a5fa', 'APEX': '#c084fc',
    'BAI': '#fbbf24', 'DD': '#22d3ee', 'QUAL': '#4ade80',
    'CLN': '#f472b6',
}

# ── CLN inline data (38 issues returned inline, not saved to file) ────
CLN_ISSUES = [
    {'key':'CLN-235','assignee':'Sathish Krishnan','sp':2},
    {'key':'CLN-214','assignee':'Eduardo Angeles','sp':None},
    {'key':'CLN-207','assignee':'Simon Getahun','sp':2},
    {'key':'CLN-206','assignee':'Richard Gau','sp':None},
    {'key':'CLN-189','assignee':'Kalpana Sharma','sp':None},
    {'key':'CLN-186','assignee':'Eduardo Angeles','sp':None},
    {'key':'CLN-180','assignee':'Abhishek Sarabi','sp':1},
    {'key':'CLN-138','assignee':'Mahesh Shetty','sp':1},
    {'key':'CLN-136','assignee':'Simon Getahun','sp':1},
    {'key':'CLN-126','assignee':'Sathish Krishnan','sp':1},
    {'key':'CLN-125','assignee':'Eduardo Angeles','sp':None},
    {'key':'CLN-102','assignee':'Abhishek Sarabi','sp':1},
    {'key':'CLN-92','assignee':'Mahesh Shetty','sp':None},
    {'key':'CLN-91','assignee':'Mahesh Shetty','sp':None},
    {'key':'CLN-72','assignee':'Suyog Bhatia','sp':1},
    {'key':'CLN-63','assignee':'Maria Jose','sp':None},
    {'key':'CLN-59','assignee':'Lorien Draeger','sp':3},
    {'key':'CLN-58','assignee':'Eduardo Angeles','sp':5},
    {'key':'CLN-57','assignee':'Eduardo Angeles','sp':5},
    {'key':'CLN-56','assignee':'Eduardo Angeles','sp':5},
    {'key':'CLN-54','assignee':'Kalpana Sharma','sp':3},
    {'key':'CLN-51','assignee':'Abhishek Sarabi','sp':5},
    {'key':'CLN-46','assignee':'Abhishek Sarabi','sp':None},
    {'key':'CLN-45','assignee':'Abhishek Sarabi','sp':None},
    {'key':'CLN-44','assignee':'Abhishek Sarabi','sp':None},
    {'key':'CLN-43','assignee':'Eduardo Angeles','sp':2},
    {'key':'CLN-42','assignee':'Abhishek Sarabi','sp':None},
    {'key':'CLN-40','assignee':'Lorien Draeger','sp':None},
    {'key':'CLN-38','assignee':'Eduardo Angeles','sp':None},
    {'key':'CLN-37','assignee':'Mahesh Shetty','sp':3},
    {'key':'CLN-36','assignee':'Mahesh Shetty','sp':3},
    {'key':'CLN-35','assignee':'Sarthak Sarangi','sp':None},
    {'key':'CLN-34','assignee':'Lorien Draeger','sp':None},
    {'key':'CLN-31','assignee':'Lorien Draeger','sp':None},
    {'key':'CLN-30','assignee':'Richard Gau','sp':None},
    {'key':'CLN-29','assignee':'Lorien Draeger','sp':None},
    {'key':'CLN-17','assignee':'Simon Getahun','sp':None},
    {'key':'CLN-12','assignee':'Shiva Thejas','sp':None},
    {'key':'CLN-7','assignee':'Simon Getahun','sp':None},
    {'key':'CLN-5','assignee':'Eduardo Angeles','sp':5},
]

# ── Parse helper ──────────────────────────────────────────────────────
def load_issues(filepath):
    """Load issues from a JIRA search result JSON file."""
    with open(filepath) as f:
        data = json.load(f)
    issues = []
    for iss in data.get('issues', []):
        proj = iss.get('project', {}).get('key', 'UNKNOWN')
        assignee = iss.get('assignee', {})
        name = assignee.get('display_name', 'Unassigned') if assignee else 'Unassigned'
        sp_obj = iss.get('customfield_14884', {})
        sp = sp_obj.get('value') if sp_obj else None
        issues.append({
            'key': iss.get('key', ''),
            'project': proj,
            'assignee': name,
            'sp': sp,
        })
    return issues

# ── 1. Load all per-project data ─────────────────────────────────────
all_issues = {}  # key -> issue dict (dedup)

# CLN from inline
for iss in CLN_ISSUES:
    iss['project'] = 'CLN'
    all_issues[iss['key']] = iss

# Other projects from files
for proj, files in project_files.items():
    for fn in files:
        fp = os.path.join(BASE, fn)
        if not os.path.exists(fp):
            print(f'WARNING: missing {fn} for {proj}')
            continue
        for iss in load_issues(fp):
            all_issues[iss['key']] = iss

print(f'Total unique issues loaded: {len(all_issues)}')

# ── 2. Load quarterly data ───────────────────────────────────────────
quarterly_issues = {}  # quarter -> {key -> issue}
for qtr, fn in quarterly_files.items():
    fp = os.path.join(BASE, fn)
    if not os.path.exists(fp):
        print(f'WARNING: missing quarterly file for {qtr}')
        continue
    issues = load_issues(fp)
    quarterly_issues[qtr] = {iss['key']: iss for iss in issues}
    print(f'{qtr}: {len(issues)} issues loaded')

# Tag issues with quarter (best effort: issues in quarterly files get tagged)
issue_quarter = {}  # key -> quarter
for qtr, iss_map in quarterly_issues.items():
    for key in iss_map:
        issue_quarter[key] = qtr

# ── 3. Aggregate per engineer ─────────────────────────────────────────
# engineer_data[name] = {project -> {issues: int, sp: float, quarterly: {qtr -> {issues, sp}}}}
engineer_data = defaultdict(lambda: defaultdict(lambda: {'issues': 0, 'sp': 0.0, 'quarterly': defaultdict(lambda: {'issues': 0, 'sp': 0.0})}))

for key, iss in all_issues.items():
    eng = iss['assignee']
    proj = iss['project']
    sp = iss.get('sp') or 0
    engineer_data[eng][proj]['issues'] += 1
    engineer_data[eng][proj]['sp'] += sp
    # Quarterly
    qtr = issue_quarter.get(key, 'Unknown')
    engineer_data[eng][proj]['quarterly'][qtr]['issues'] += 1
    engineer_data[eng][proj]['quarterly'][qtr]['sp'] += sp

# ── 4. Aggregate per project ─────────────────────────────────────────
project_summary = defaultdict(lambda: {'issues': 0, 'sp': 0.0, 'engineers': set()})
for eng, projects in engineer_data.items():
    for proj, data in projects.items():
        project_summary[proj]['issues'] += data['issues']
        project_summary[proj]['sp'] += data['sp']
        project_summary[proj]['engineers'].add(eng)

# ── 5. Build leaderboard ─────────────────────────────────────────────
leaderboard = []
for eng, projects in engineer_data.items():
    total_issues = sum(d['issues'] for d in projects.values())
    total_sp = sum(d['sp'] for d in projects.values())
    proj_list = sorted(projects.keys())
    avg_sp_per_issue = total_sp / total_issues if total_issues else 0
    leaderboard.append({
        'name': eng,
        'projects': proj_list,
        'total_issues': total_issues,
        'total_sp': total_sp,
        'avg_sp_per_issue': round(avg_sp_per_issue, 1),
    })

# Sort by total_sp descending, then by issues
leaderboard.sort(key=lambda x: (-x['total_sp'], -x['total_issues']))

# ── 6. Compute KPIs ──────────────────────────────────────────────────
total_engineers = len(engineer_data)
total_issues = len(all_issues)
total_sp = sum(iss.get('sp') or 0 for iss in all_issues.values())
total_projects = len(project_summary)
avg_sp_per_eng = round(total_sp / total_engineers, 1) if total_engineers else 0
avg_issues_per_eng = round(total_issues / total_engineers, 1) if total_engineers else 0

print(f'Engineers: {total_engineers} | Issues: {total_issues} | SP: {total_sp} | Projects: {total_projects}')

# ── 7. Generate HTML ──────────────────────────────────────────────────
# Sort projects by issue count descending
sorted_projects = sorted(project_summary.items(), key=lambda x: -x[1]['issues'])
proj_order = [p for p, _ in sorted_projects]

# Project distribution chart data
proj_labels = [proj_names.get(p, p) for p in proj_order]
proj_issue_counts = [project_summary[p]['issues'] for p in proj_order]
proj_sp_counts = [project_summary[p]['sp'] for p in proj_order]
proj_eng_counts = [len(project_summary[p]['engineers']) for p in proj_order]
proj_chart_colors = [proj_colors.get(p, '#818cf8') for p in proj_order]

# Top contributors (top 15)
top_contributors = leaderboard[:15]

html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Resource Productivity Report</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"></script>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Segoe UI',system-ui,-apple-system,sans-serif;background:#070b14;color:#e2e8f0;line-height:1.6}}
header{{background:linear-gradient(135deg,#0f172a 0%,#1e1b4b 100%);padding:32px 24px 28px;border-bottom:1px solid rgba(99,102,241,.15)}}
header h1{{font-size:1.8rem;font-weight:800;background:linear-gradient(135deg,#818cf8,#a78bfa,#c084fc);-webkit-background-clip:text;-webkit-text-fill-color:transparent}}
header p{{color:#94a3b8;font-size:.85rem;margin-top:4px}}
.home-btn{{display:inline-flex;align-items:center;gap:6px;text-decoration:none;color:#94a3b8;font-size:.78rem;font-weight:600;padding:5px 14px;border:1px solid rgba(99,102,241,.2);border-radius:8px;margin-bottom:8px;transition:all .15s}}
.home-btn:hover{{background:rgba(99,102,241,.15);color:#a5b4fc}}
.wrap{{max-width:1400px;margin:0 auto;padding:24px 20px 60px}}
.kpi-row{{display:grid;grid-template-columns:repeat(6,1fr);gap:14px;margin-bottom:32px}}
.kpi{{background:linear-gradient(135deg,#111827,#1a1f3a);border:1px solid rgba(99,102,241,.12);border-radius:14px;padding:20px 16px;text-align:center}}
.kpi .val{{font-size:1.8rem;font-weight:800;background:linear-gradient(135deg,#818cf8,#c084fc);-webkit-background-clip:text;-webkit-text-fill-color:transparent}}
.kpi .lbl{{font-size:.72rem;color:#94a3b8;text-transform:uppercase;letter-spacing:.5px;margin-top:4px}}
.section-title{{font-size:1.2rem;font-weight:700;color:#a5b4fc;margin:32px 0 16px;padding-bottom:8px;border-bottom:1px solid rgba(99,102,241,.1)}}
.grid-2{{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:32px}}
.card{{background:linear-gradient(135deg,#111827 0%,#1a1f3a 100%);border:1px solid rgba(99,102,241,.12);border-radius:14px;padding:24px;overflow:hidden}}
.card h3{{font-size:.95rem;font-weight:700;color:#c4b5fd;margin-bottom:12px}}
.proj-cards{{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:14px;margin-bottom:32px}}
.proj-card{{background:linear-gradient(135deg,#111827 0%,#1a1f3a 100%);border:1px solid rgba(99,102,241,.12);border-radius:14px;padding:20px;position:relative;overflow:hidden}}
.proj-card::before{{content:'';position:absolute;top:0;left:0;right:0;height:3px}}
.proj-card .proj-name{{font-size:.95rem;font-weight:700;margin-bottom:6px}}
.proj-card .proj-stats{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-top:12px}}
.proj-card .stat{{text-align:center}}
.proj-card .stat .v{{font-size:1.3rem;font-weight:800}}
.proj-card .stat .l{{font-size:.65rem;color:#94a3b8;text-transform:uppercase}}
table{{width:100%;border-collapse:collapse;font-size:.82rem}}
thead th{{background:#1e1b4b;color:#a5b4fc;padding:10px 12px;text-align:left;font-weight:600;font-size:.72rem;text-transform:uppercase;letter-spacing:.5px;position:sticky;top:0}}
tbody tr{{border-bottom:1px solid rgba(99,102,241,.08);transition:background .15s}}
tbody tr:hover{{background:rgba(99,102,241,.06)}}
tbody td{{padding:10px 12px}}
.rank{{width:32px;height:32px;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;font-weight:800;font-size:.75rem}}
.rank-1{{background:linear-gradient(135deg,#fbbf24,#f59e0b);color:#1e1b4b}}
.rank-2{{background:linear-gradient(135deg,#94a3b8,#cbd5e1);color:#1e1b4b}}
.rank-3{{background:linear-gradient(135deg,#cd7f32,#b8860b);color:#fff}}
.proj-tag{{display:inline-block;padding:2px 8px;border-radius:6px;font-size:.65rem;font-weight:600;margin:1px 2px}}
.bar-container{{height:20px;background:rgba(99,102,241,.08);border-radius:10px;overflow:hidden;margin-top:4px}}
.bar-fill{{height:100%;border-radius:10px;transition:width .5s}}
.chart-wrap{{position:relative;height:300px}}
footer{{text-align:center;padding:24px;color:#475569;font-size:.72rem;border-top:1px solid rgba(99,102,241,.08)}}
@media(max-width:900px){{.kpi-row{{grid-template-columns:repeat(3,1fr)}}.grid-2{{grid-template-columns:1fr}}}}
@media(max-width:600px){{.kpi-row{{grid-template-columns:repeat(2,1fr)}}}}
</style>
</head>
<body>
<header>
  <a href="index.html" class="home-btn">&#8592; Home</a>
  <h1>Resource Productivity Report</h1>
  <p>Combined metrics across {total_projects} active projects &bull; Q3 2025 &ndash; Q1 2026 (Last 2 Quarters)</p>
</header>
<div class="wrap">

<!-- KPI Row -->
<div class="kpi-row">
  <div class="kpi"><div class="val">{total_engineers}</div><div class="lbl">Engineers</div></div>
  <div class="kpi"><div class="val">{total_issues}</div><div class="lbl">Issues Completed</div></div>
  <div class="kpi"><div class="val">{total_sp:.0f}</div><div class="lbl">Story Points</div></div>
  <div class="kpi"><div class="val">{total_projects}</div><div class="lbl">Active Projects</div></div>
  <div class="kpi"><div class="val">{avg_issues_per_eng}</div><div class="lbl">Avg Issues / Eng</div></div>
  <div class="kpi"><div class="val">{avg_sp_per_eng}</div><div class="lbl">Avg SP / Eng</div></div>
</div>

<!-- Section: Project Distribution -->
<div class="section-title">Project Distribution</div>
<div class="grid-2">
  <div class="card">
    <h3>Issues Completed by Project</h3>
    <div class="chart-wrap"><canvas id="projIssueChart"></canvas></div>
  </div>
  <div class="card">
    <h3>Story Points by Project</h3>
    <div class="chart-wrap"><canvas id="projSPChart"></canvas></div>
  </div>
</div>

<!-- Project Summary Cards -->
<div class="section-title">Project Summary</div>
<div class="proj-cards">
'''

# Generate project summary cards
for i, proj in enumerate(proj_order):
    ps = project_summary[proj]
    color = proj_colors.get(proj, '#818cf8')
    name = proj_names.get(proj, proj)
    eng_count = len(ps['engineers'])
    avg = round(ps['sp'] / ps['issues'], 1) if ps['issues'] else 0
    html += f'''  <div class="proj-card" style="border-top:3px solid {color}">
    <div class="proj-name" style="color:{color}">{name} ({proj})</div>
    <div class="proj-stats">
      <div class="stat"><div class="v" style="color:{color}">{ps['issues']}</div><div class="l">Issues</div></div>
      <div class="stat"><div class="v" style="color:{color}">{ps['sp']:.0f}</div><div class="l">Story Pts</div></div>
      <div class="stat"><div class="v" style="color:{color}">{eng_count}</div><div class="l">Engineers</div></div>
    </div>
  </div>
'''

html += '''</div>

<!-- Top Contributors Chart -->
<div class="section-title">Top Contributors</div>
<div class="grid-2">
  <div class="card">
    <h3>Top 15 by Story Points</h3>
    <div class="chart-wrap"><canvas id="topSPChart"></canvas></div>
  </div>
  <div class="card">
    <h3>Top 15 by Issues Completed</h3>
    <div class="chart-wrap"><canvas id="topIssueChart"></canvas></div>
  </div>
</div>

<!-- Engineer Leaderboard Table -->
<div class="section-title">Engineer Leaderboard</div>
<div class="card" style="padding:0;overflow:auto;max-height:600px">
<table>
<thead>
<tr>
  <th style="width:40px">#</th>
  <th>Engineer</th>
  <th>Projects</th>
  <th style="text-align:right">Issues</th>
  <th style="text-align:right">Story Points</th>
  <th style="text-align:right">Avg SP/Issue</th>
  <th style="width:180px">Productivity</th>
</tr>
</thead>
<tbody>
'''

# Generate leaderboard rows
max_sp = max(e['total_sp'] for e in leaderboard) if leaderboard else 1
for i, eng in enumerate(leaderboard):
    rank = i + 1
    rank_class = f'rank-{rank}' if rank <= 3 else ''
    rank_bg = '' if rank <= 3 else 'background:rgba(99,102,241,.12);color:#818cf8'
    # Project tags
    proj_tags = ''
    for p in eng['projects']:
        c = proj_colors.get(p, '#818cf8')
        proj_tags += f'<span class="proj-tag" style="background:{c}22;color:{c}">{p}</span>'
    # Progress bar
    bar_pct = (eng['total_sp'] / max_sp * 100) if max_sp else 0
    bar_color = proj_colors.get(eng['projects'][0], '#818cf8') if eng['projects'] else '#818cf8'

    html += f'''<tr>
  <td><span class="rank {rank_class}" style="{rank_bg}">{rank}</span></td>
  <td style="font-weight:600">{eng['name']}</td>
  <td>{proj_tags}</td>
  <td style="text-align:right;font-weight:700">{eng['total_issues']}</td>
  <td style="text-align:right;font-weight:700;color:#a5b4fc">{eng['total_sp']:.0f}</td>
  <td style="text-align:right">{eng['avg_sp_per_issue']}</td>
  <td><div class="bar-container"><div class="bar-fill" style="width:{bar_pct:.0f}%;background:{bar_color}"></div></div></td>
</tr>
'''

html += '''</tbody>
</table>
</div>

<!-- Quarterly Breakdown -->
<div class="section-title">Quarterly Breakdown</div>
<div class="grid-2">
  <div class="card">
    <h3>Issues by Quarter &amp; Project</h3>
    <div class="chart-wrap"><canvas id="qtrIssueChart"></canvas></div>
  </div>
  <div class="card">
    <h3>Story Points by Quarter &amp; Project</h3>
    <div class="chart-wrap"><canvas id="qtrSPChart"></canvas></div>
  </div>
</div>

</div><!-- /wrap -->
'''

# Build quarterly aggregation for charts
qtr_proj_issues = defaultdict(lambda: defaultdict(int))
qtr_proj_sp = defaultdict(lambda: defaultdict(float))
for key, iss in all_issues.items():
    qtr = issue_quarter.get(key, 'Unknown')
    if qtr == 'Unknown':
        continue
    qtr_proj_issues[qtr][iss['project']] += 1
    qtr_proj_sp[qtr][iss['project']] += (iss.get('sp') or 0)

quarters = ['Q3 2025', 'Q4 2025', 'Q1 2026']

html += f'''
<footer>
  Resource Productivity Report &bull; Data sourced from JIRA &bull; Generated {datetime.now().strftime("%b %d, %Y %I:%M %p")}
</footer>

<script>
const projLabels = {json.dumps(proj_labels)};
const projIssueCounts = {json.dumps(proj_issue_counts)};
const projSPCounts = {json.dumps(proj_sp_counts)};
const projColors = {json.dumps(proj_chart_colors)};

// Project Issues Chart (horizontal bar)
new Chart(document.getElementById('projIssueChart'), {{
  type: 'bar',
  data: {{
    labels: projLabels,
    datasets: [{{
      label: 'Issues Completed',
      data: projIssueCounts,
      backgroundColor: projColors.map(c => c + '88'),
      borderColor: projColors,
      borderWidth: 1,
      borderRadius: 6
    }}]
  }},
  options: {{
    indexAxis: 'y',
    responsive: true,
    maintainAspectRatio: false,
    plugins: {{ legend: {{ display: false }} }},
    scales: {{
      x: {{ grid: {{ color: 'rgba(99,102,241,.08)' }}, ticks: {{ color: '#94a3b8' }} }},
      y: {{ grid: {{ display: false }}, ticks: {{ color: '#e2e8f0', font: {{ size: 11 }} }} }}
    }}
  }}
}});

// Project SP Chart (horizontal bar)
new Chart(document.getElementById('projSPChart'), {{
  type: 'bar',
  data: {{
    labels: projLabels,
    datasets: [{{
      label: 'Story Points',
      data: projSPCounts,
      backgroundColor: projColors.map(c => c + '88'),
      borderColor: projColors,
      borderWidth: 1,
      borderRadius: 6
    }}]
  }},
  options: {{
    indexAxis: 'y',
    responsive: true,
    maintainAspectRatio: false,
    plugins: {{ legend: {{ display: false }} }},
    scales: {{
      x: {{ grid: {{ color: 'rgba(99,102,241,.08)' }}, ticks: {{ color: '#94a3b8' }} }},
      y: {{ grid: {{ display: false }}, ticks: {{ color: '#e2e8f0', font: {{ size: 11 }} }} }}
    }}
  }}
}});

// Top Contributors by SP
const topSPNames = {json.dumps([e['name'].split()[0] + ' ' + (e['name'].split()[-1][0] if len(e['name'].split()) > 1 else '') for e in top_contributors])};
const topSPValues = {json.dumps([e['total_sp'] for e in top_contributors])};
const topSPColors = {json.dumps([proj_colors.get(e['projects'][0], '#818cf8') if e['projects'] else '#818cf8' for e in top_contributors])};

new Chart(document.getElementById('topSPChart'), {{
  type: 'bar',
  data: {{
    labels: topSPNames,
    datasets: [{{
      label: 'Story Points',
      data: topSPValues,
      backgroundColor: topSPColors.map(c => c + '88'),
      borderColor: topSPColors,
      borderWidth: 1,
      borderRadius: 6
    }}]
  }},
  options: {{
    indexAxis: 'y',
    responsive: true,
    maintainAspectRatio: false,
    plugins: {{ legend: {{ display: false }} }},
    scales: {{
      x: {{ grid: {{ color: 'rgba(99,102,241,.08)' }}, ticks: {{ color: '#94a3b8' }} }},
      y: {{ grid: {{ display: false }}, ticks: {{ color: '#e2e8f0', font: {{ size: 11 }} }} }}
    }}
  }}
}});

// Top Contributors by Issues
const topIssNames = {json.dumps([e['name'].split()[0] + ' ' + (e['name'].split()[-1][0] if len(e['name'].split()) > 1 else '') for e in sorted(top_contributors, key=lambda x: -x['total_issues'])])};
const topIssValues = {json.dumps([e['total_issues'] for e in sorted(top_contributors, key=lambda x: -x['total_issues'])])};
const topIssColors = {json.dumps([proj_colors.get(e['projects'][0], '#818cf8') if e['projects'] else '#818cf8' for e in sorted(top_contributors, key=lambda x: -x['total_issues'])])};

new Chart(document.getElementById('topIssueChart'), {{
  type: 'bar',
  data: {{
    labels: topIssNames,
    datasets: [{{
      label: 'Issues Completed',
      data: topIssValues,
      backgroundColor: topIssColors.map(c => c + '88'),
      borderColor: topIssColors,
      borderWidth: 1,
      borderRadius: 6
    }}]
  }},
  options: {{
    indexAxis: 'y',
    responsive: true,
    maintainAspectRatio: false,
    plugins: {{ legend: {{ display: false }} }},
    scales: {{
      x: {{ grid: {{ color: 'rgba(99,102,241,.08)' }}, ticks: {{ color: '#94a3b8' }} }},
      y: {{ grid: {{ display: false }}, ticks: {{ color: '#e2e8f0', font: {{ size: 11 }} }} }}
    }}
  }}
}});

// Quarterly Breakdown - Issues by Quarter & Project (stacked bar)
const quarters = {json.dumps(quarters)};
const qtrDatasets = [];
'''

# Generate quarterly stacked bar chart datasets
for proj in proj_order:
    color = proj_colors.get(proj, '#818cf8')
    name = proj_names.get(proj, proj)
    issue_data = [qtr_proj_issues[q].get(proj, 0) for q in quarters]
    html += f'''
qtrDatasets.push({{
  label: '{name}',
  data: {json.dumps(issue_data)},
  backgroundColor: '{color}88',
  borderColor: '{color}',
  borderWidth: 1,
  borderRadius: 4
}});
'''

html += '''
new Chart(document.getElementById('qtrIssueChart'), {
  type: 'bar',
  data: { labels: quarters, datasets: qtrDatasets },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { position: 'bottom', labels: { color: '#94a3b8', font: { size: 10 }, boxWidth: 12 } }
    },
    scales: {
      x: { stacked: true, grid: { display: false }, ticks: { color: '#e2e8f0' } },
      y: { stacked: true, grid: { color: 'rgba(99,102,241,.08)' }, ticks: { color: '#94a3b8' } }
    }
  }
});
'''

html += f'''
// Quarterly SP Chart (stacked)
const qtrSPDatasets = [];
'''

for proj in proj_order:
    color = proj_colors.get(proj, '#818cf8')
    name = proj_names.get(proj, proj)
    sp_data = [qtr_proj_sp[q].get(proj, 0) for q in quarters]
    html += f'''
qtrSPDatasets.push({{
  label: '{name}',
  data: {json.dumps(sp_data)},
  backgroundColor: '{color}88',
  borderColor: '{color}',
  borderWidth: 1,
  borderRadius: 4
}});
'''

html += '''
new Chart(document.getElementById('qtrSPChart'), {
  type: 'bar',
  data: { labels: quarters, datasets: qtrSPDatasets },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { position: 'bottom', labels: { color: '#94a3b8', font: { size: 10 }, boxWidth: 12 } }
    },
    scales: {
      x: { stacked: true, grid: { display: false }, ticks: { color: '#e2e8f0' } },
      y: { stacked: true, grid: { color: 'rgba(99,102,241,.08)' }, ticks: { color: '#94a3b8' } }
    }
  }
});
</script>
</body>
</html>
'''

with open(OUT, 'w') as f:
    f.write(html)

print(f'\nReport generated: {OUT}')
print(f'Engineers: {total_engineers} | Issues: {total_issues} | SP: {total_sp:.0f} | Projects: {total_projects}')
