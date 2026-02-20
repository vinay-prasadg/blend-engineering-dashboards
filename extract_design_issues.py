#!/usr/bin/env python3
"""
Scan all cached JIRA data files and extract design-related issues.
Outputs a JSON file with all design issues found across all projects.

Design criteria (any match):
  1. Summary starts with "DESIGN -" or "DESIGN:"
  2. Summary contains "design" as a distinct word (not inside other words like "designated")
  3. Parent epic summary contains "Design" (e.g. "Research & Design")
  4. Issue belongs to a Design-category project (DDB, PRDS)
  5. Labels include "design", "UX", "ui-design", etc.
  6. Summary contains "redesign", "UX", "figma design", or "UI changes as per figma"
"""

import json
import os
import re
import sys
from collections import defaultdict

BASE = '/Users/vinay-prasadg/.cursor/projects/Users-vinay-prasadg-Documents-Production-Defects/agent-tools'
OUTPUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'design_issues.json')

DESIGN_PROJECTS = {'DDB', 'PRDS'}
DESIGN_LABELS = {'design', 'ux', 'ui-design', 'design-review', 'design-needed', 'ui', 'ux-design'}

DESIGN_SUMMARY_PATTERNS = [
    re.compile(r'^DESIGN\s*[-:]', re.IGNORECASE),
    re.compile(r'\bdesign\b', re.IGNORECASE),
    re.compile(r'\bredesign\b', re.IGNORECASE),
    re.compile(r'\bfigma\b', re.IGNORECASE),
    re.compile(r'\bUX\b'),
    re.compile(r'\bUI changes\b', re.IGNORECASE),
]

EXCLUDE_PATTERNS = [
    re.compile(r'updateDisclosuresPackages', re.IGNORECASE),
    re.compile(r'Remove FF:', re.IGNORECASE),
]


def is_design_related(issue, parent_summary=''):
    summary = issue.get('summary', '')
    labels = [l.lower() for l in issue.get('labels', [])]
    project = issue.get('key', '').split('-')[0] if 'key' in issue else ''

    for ep in EXCLUDE_PATTERNS:
        if ep.search(summary):
            return False

    if project in DESIGN_PROJECTS:
        return True

    for dl in DESIGN_LABELS:
        if dl in labels:
            return True

    for pat in DESIGN_SUMMARY_PATTERNS:
        if pat.search(summary):
            return True

    if parent_summary:
        if re.search(r'\bdesign\b', parent_summary, re.IGNORECASE):
            return True

    return False


def extract_issue_data(raw):
    key = raw.get('key', '')
    project = key.split('-')[0] if key else ''
    status = raw.get('status', {})
    priority = raw.get('priority', {})
    assignee = raw.get('assignee', {})
    parent = raw.get('parent', {})
    parent_fields = parent.get('fields', {})
    parent_summary = parent_fields.get('summary', '')
    parent_type = parent_fields.get('issuetype', {}).get('name', '')
    issuetype = raw.get('issuetype', {})

    itype = ''
    if isinstance(issuetype, dict):
        itype = issuetype.get('name', '')

    return {
        'key': key,
        'project': project,
        'summary': raw.get('summary', ''),
        'status': status.get('name', '') if isinstance(status, dict) else str(status),
        'statusCategory': status.get('category', '') if isinstance(status, dict) else '',
        'priority': priority.get('name', '') if isinstance(priority, dict) else str(priority),
        'assignee': assignee.get('display_name', 'Unassigned') if isinstance(assignee, dict) else str(assignee),
        'type': itype or 'Story',
        'labels': raw.get('labels', []),
        'parentKey': parent.get('key', ''),
        'parentSummary': parent_summary,
        'parentType': parent_type,
        'created': raw.get('created', ''),
        'updated': raw.get('updated', ''),
    }


def main():
    all_issues = {}
    files_scanned = 0
    issues_scanned = 0

    for fname in os.listdir(BASE):
        if not fname.endswith('.txt'):
            continue
        fpath = os.path.join(BASE, fname)
        try:
            with open(fpath) as f:
                content = f.read().strip()
                if not content:
                    continue
                data = json.loads(content)
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue

        files_scanned += 1

        issues = []
        if isinstance(data, dict) and 'issues' in data:
            issues = data['issues']
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and 'issues' in item:
                    issues.extend(item['issues'])
                elif isinstance(item, dict) and 'key' in item:
                    issues.append(item)

        for raw in issues:
            issues_scanned += 1
            key = raw.get('key', '')
            if not key:
                continue

            parent = raw.get('parent', {})
            parent_summary = parent.get('fields', {}).get('summary', '') if isinstance(parent, dict) else ''

            if is_design_related(raw, parent_summary):
                if key not in all_issues:
                    all_issues[key] = extract_issue_data(raw)

    design_issues = sorted(all_issues.values(), key=lambda x: x['key'])

    by_project = defaultdict(list)
    by_status = defaultdict(int)
    by_priority = defaultdict(int)
    by_type = defaultdict(int)
    assignees = set()

    for i in design_issues:
        by_project[i['project']].append(i)
        by_status[i['status']] += 1
        by_priority[i['priority']] += 1
        by_type[i['type']] += 1
        if i['assignee'] and i['assignee'] != 'Unassigned':
            assignees.add(i['assignee'])

    print(f"\nDesign Issues Report")
    print(f"{'='*60}")
    print(f"Files scanned:    {files_scanned}")
    print(f"Issues scanned:   {issues_scanned}")
    print(f"Design issues:    {len(design_issues)}")
    print(f"Projects:         {len(by_project)}")
    print(f"Active assignees: {len(assignees)}")
    print()

    print(f"BY PROJECT:")
    for proj in sorted(by_project.keys()):
        items = by_project[proj]
        done = sum(1 for i in items if i['statusCategory'] in ('Done', 'done'))
        open_ = len(items) - done
        print(f"  {proj:12s}  {len(items):3d} total  ({open_:2d} open, {done:2d} done)")

    print(f"\nBY STATUS:")
    for st, cnt in sorted(by_status.items(), key=lambda x: -x[1]):
        print(f"  {st:25s}  {cnt}")

    print(f"\nBY PRIORITY:")
    for p, cnt in sorted(by_priority.items()):
        print(f"  {p:25s}  {cnt}")

    print(f"\nBY TYPE:")
    for t, cnt in sorted(by_type.items(), key=lambda x: -x[1]):
        print(f"  {t:25s}  {cnt}")

    print(f"\nASSIGNEES:")
    for a in sorted(assignees):
        count = sum(1 for i in design_issues if i['assignee'] == a)
        print(f"  {a:30s}  {count}")

    print(f"\nALL DESIGN ISSUES:")
    print(f"{'Key':15s} {'Project':8s} {'Status':20s} {'Priority':16s} {'Assignee':25s} Summary")
    print('-' * 140)
    for i in design_issues:
        print(f"{i['key']:15s} {i['project']:8s} {i['status']:20s} {i['priority']:16s} {i['assignee']:25s} {i['summary'][:60]}")

    with open(OUTPUT, 'w') as f:
        json.dump({
            'generated': str(__import__('datetime').datetime.now()),
            'total': len(design_issues),
            'projects': len(by_project),
            'by_project': {k: len(v) for k, v in by_project.items()},
            'by_status': dict(by_status),
            'by_priority': dict(by_priority),
            'by_type': dict(by_type),
            'assignees': sorted(assignees),
            'issues': design_issues,
        }, f, indent=2)
    print(f"\nSaved {len(design_issues)} issues to {OUTPUT}")


if __name__ == '__main__':
    main()
