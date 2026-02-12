#!/usr/bin/env python3
"""Build a comprehensive Epic-to-Story mapping report from all collected JIRA data."""
import json, os
from datetime import datetime

BASE = '/Users/vinay-prasadg/.cursor/projects/Users-vinay-prasadg-Documents-Production-Defects/agent-tools'

# ── Load story data (children of epics) ────────────────────────────────
story_files = [
    # Round 1 (all statuses)
    '9c8c0f5b-f46b-417b-b205-89642efe0fd5.txt',  # DDINDIA
    'dbdf7ddb-9589-439f-b021-e1be03ecb05e.txt',  # CLN
    '985dc22f-c907-45fc-8330-0d32f4674721.txt',  # CBP
    '67361981-6ff6-445d-b4ba-9e9ee812f968.txt',  # DD
    '2bfc2bd1-d2da-4d74-954c-980826f382f6.txt',  # SENG
    # Round 2 (active only - NOT done/closed)
    'b0ff3e4f-2445-49b4-8c45-02aed6986a17.txt',  # DDINDIA batch 1
    'ee94bb2a-ef89-4d82-8069-b1a325cbcb28.txt',  # DDINDIA batch 2
    'd046d85f-e21e-490b-a74d-f780c2ee9eab.txt',  # CLN batch 1
    '80ab8117-e0c8-4413-a7ff-573a5628ca72.txt',  # CLN batch 2
    'de15123a-35f7-45df-afcb-f477c81e8eb0.txt',  # DD batch 1
    'd5f9c3d2-325e-45bf-82b3-7bc789baecb4.txt',  # DD batch 2
    '8b5fb6e1-5bcf-4830-9cb7-06f1fe2a42f6.txt',  # SENG batch 1
    'fcd1ee63-5d41-432a-a738-a857645dd766.txt',  # SENG batch 2
    # Round 3 — new projects children
    'ec41b789-01af-4fb1-b8d9-c0c49ccc0022.txt',  # DA children
    'c2c51357-b5b2-4b9e-b8ae-1fc455eabe1f.txt',  # BAI children
    '268553c6-be84-4906-b52b-e29fd346cbfa.txt',  # RHL batch 1
    'e55f947a-0974-420e-90ec-65a7f209d17e.txt',  # RHL batch 2
    '0080c134-ee51-4bfe-accf-b12f9826e344.txt',  # APEX batch 1
    '4888e579-4f8d-4568-91b5-43685774593c.txt',  # APEX batch 2
    '4afe31a9-41e9-4ace-9191-b8a93dcdeca3.txt',  # QUAL batch 1
    '1cb8e1e2-79a6-42b2-a7f1-aa05a7eda9ac.txt',  # QUAL batch 2
]

# Bug-specific query files (issues are known to be type=Bug)
bug_files = [
    '24d73d77-0d02-4814-af3a-011672cad2f4.txt',  # DDINDIA bugs
    'a698b30b-8aa0-4df6-b51e-b80de7821e31.txt',  # CLN bugs
    'f975a2df-bd16-400c-b7ee-6a6a735cf38d.txt',  # DD bugs
    'b94972ce-de46-4300-b6c5-b8c92bd47f0a.txt',  # SENG bugs
    '90c4d056-3b58-48aa-a3ae-8d78c386fb84.txt',  # DA bugs
    '49496a3d-1dae-471d-8868-49b123f7d106.txt',  # BAI bugs
    '89c26a4b-94dd-41af-a4ce-57fe77c34dc1.txt',  # RHL bugs
    'b08a894b-db87-4256-8d9c-45a50ee9c868.txt',  # APEX bugs
    '89f895a9-5d48-48e2-a128-4b4ab45ba9ee.txt',  # QUAL bugs
]

# Parse story data grouped by parent epic
epic_stories = {}  # epic_key -> list of stories

for fname in story_files:
    fpath = os.path.join(BASE, fname)
    with open(fpath) as f:
        data = json.load(f)
    for issue in data.get('issues', []):
        parent = issue.get('parent', {})
        if not parent:
            continue
        epic_key = parent.get('key', '')
        issue_key = issue.get('key', '')
        if epic_key not in epic_stories:
            epic_stories[epic_key] = {}
        if issue_key not in epic_stories[epic_key]:
            itype = ''
            if issue.get('issuetype'):
                itype = issue['issuetype'].get('name', '')
            epic_stories[epic_key][issue_key] = {
                'key': issue_key,
                'summary': issue.get('summary', ''),
                'status': issue.get('status', {}).get('name', ''),
                'status_cat': issue.get('status', {}).get('category', ''),
                'priority': issue.get('priority', {}).get('name', ''),
                'assignee': issue.get('assignee', {}).get('display_name', 'Unassigned'),
                'type': itype if itype else 'Story',
            }

# Parse bug files — these are known Bug type issues
for fname in bug_files:
    fpath = os.path.join(BASE, fname)
    with open(fpath) as f:
        data = json.load(f)
    for issue in data.get('issues', []):
        parent = issue.get('parent', {})
        if not parent:
            continue
        epic_key = parent.get('key', '')
        issue_key = issue.get('key', '')
        if epic_key not in epic_stories:
            epic_stories[epic_key] = {}
        # Always set/override type to Bug for these files
        epic_stories[epic_key][issue_key] = {
            'key': issue_key,
            'summary': issue.get('summary', ''),
            'status': issue.get('status', {}).get('name', ''),
            'status_cat': issue.get('status', {}).get('category', ''),
            'priority': issue.get('priority', {}).get('name', ''),
            'assignee': issue.get('assignee', {}).get('display_name', 'Unassigned'),
            'type': 'Bug',
        }

# Also handle inline CBP bug data
cbp_bugs_inline = [
    {'key': 'CL-9357', 'summary': "Label the SVGs: Logo & Powered by Blend", 'status': 'Done', 'status_cat': 'Done', 'priority': 'P2 (Major)', 'assignee': 'Shiksha Gupta', 'parent': 'CBP-9666'},
    {'key': 'CBP-10198', 'summary': "Accessibility | Progress Bar | Screen reader states", 'status': 'Done', 'status_cat': 'Done', 'priority': 'P1 (Critical)', 'assignee': 'Sylvia Cung', 'parent': 'CBP-9666'},
    {'key': 'CBP-10156', 'summary': 'Image | Add alt="" when the label field is empty', 'status': 'Done', 'status_cat': 'Done', 'priority': 'P2 (Major)', 'assignee': 'David Kaplan', 'parent': 'CBP-9666'},
    {'key': 'CBP-10153', 'summary': "Callout | Update ARIA labeling", 'status': 'Done', 'status_cat': 'Done', 'priority': 'P1 (Critical)', 'assignee': 'David Kaplan', 'parent': 'CBP-9666'},
    {'key': 'CBP-12374', 'summary': "Can create invalid data field validations from component validation modal", 'status': 'To Do', 'status_cat': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned', 'parent': 'CBP-12276'},
    {'key': 'CBP-13212', 'summary': "Visible in Navigation toggle should override hideFollowUpsFromNav FF behavior", 'status': 'Cancelled', 'status_cat': 'Done', 'priority': 'P3 (Minor)', 'assignee': 'Shimrit Yacobi', 'parent': 'CBP-13221'},
    {'key': 'CBP-13068', 'summary': "Subworkflows: Error when refreshing a data field within a loop", 'status': 'Done', 'status_cat': 'Done', 'priority': 'P2 (Major)', 'assignee': 'Shreshth Malik', 'parent': 'CBP-13221'},
    {'key': 'CBP-10420', 'summary': "Cursor brought to end of line when editing the middle of a validation message", 'status': 'Ready for QA', 'status_cat': 'Done', 'priority': 'P2 (Major)', 'assignee': 'Simon Leblanc', 'parent': 'CBP-13221'},
]
for b in cbp_bugs_inline:
    epic_key = b['parent']
    if epic_key not in epic_stories:
        epic_stories[epic_key] = {}
    epic_stories[epic_key][b['key']] = {
        'key': b['key'], 'summary': b['summary'], 'status': b['status'],
        'status_cat': b['status_cat'], 'priority': b['priority'],
        'assignee': b['assignee'], 'type': 'Bug',
    }

# ── All known epics (hardcoded from JIRA queries) ─────────────────────
all_epics = {
    # DDINDIA Epics
    'DDINDIA-553': {'summary': 'Align API & UI behavior for DOCUMENT_REVIEW follow-ups (Wells Fargo)', 'status': 'Blocked', 'priority': 'P1 (Critical)', 'assignee': 'Amod Kumar'},
    'DDINDIA-368': {'summary': 'OneSpan "Any Signer" Envelope Support', 'status': 'Blocked', 'priority': 'P1 (Critical)', 'assignee': 'Amod Kumar'},
    'DDINDIA-94':  {'summary': 'Doc AI pilot — Real-Time Document Validation with LLM', 'status': 'In Progress', 'priority': 'P2 (Major)', 'assignee': 'Harikrishnan Manickam'},
    'DDINDIA-159': {'summary': 'Node 22 Upgrade - Part 2', 'status': 'In Progress', 'priority': 'P2 (Major)', 'assignee': 'Monilkumar Suthar'},
    'DDINDIA-256': {'summary': 'DDIND-OCE Tickets Q1_2026', 'status': 'In Progress', 'priority': 'P2 (Major)', 'assignee': 'Unassigned'},
    'DDINDIA-376': {'summary': 'Enable Automatic LO Signature on Disclosures via OneSpan', 'status': 'In Progress', 'priority': 'P2 (Major)', 'assignee': 'Sharad Saurav'},
    'DDINDIA-384': {'summary': 'Beehive pub/sub to Kafka Migration', 'status': 'In Progress', 'priority': 'P2 (Major)', 'assignee': 'Gaurav Kumar'},
    'DDINDIA-527': {'summary': 'LO-Initiated Disclosures — Encompass Q1-2026', 'status': 'In Progress', 'priority': 'P2 (Major)', 'assignee': 'Arjun Pradeep Gujar'},
    'DDINDIA-362': {'summary': 'Add Employer Info to W-2 Follow-Up Requests', 'status': 'In Progress', 'priority': 'P2 (Major)', 'assignee': 'Kumar Utkarsh'},
    'DDINDIA-410': {'summary': 'DDIND-OCE Tickets Q4_2025', 'status': 'In Progress', 'priority': 'P2 (Major)', 'assignee': 'Unassigned'},
    'DDINDIA-598': {'summary': 'Migrate Follow-ups to Microservice', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'DDINDIA-98':  {'summary': 'Envelopes migration from lending to doc-service', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Gaurav Kumar'},
    'DDINDIA-408': {'summary': 'DD-IND-TechDebt-2026', 'status': 'In Progress', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'DDINDIA-409': {'summary': 'DD-IND-Bugfixes-2026', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'DDINDIA-591': {'summary': 'Return suggested follow-ups in List Follow-Ups API response', 'status': 'In Progress', 'priority': 'P3 (Minor)', 'assignee': 'Sharad Saurav'},
    'DDINDIA-190': {'summary': 'LO-Initiated Disclosures — Encompass', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Ari Mendelson'},

    # CLN Epics
    'CLN-140': {'summary': '[CL Q1 \'26] Production Support', 'status': 'To Do', 'priority': 'P0 (Blocking)', 'assignee': 'Pranav Kulkarni'},
    'CLN-139': {'summary': '[CL Q1 \'26] Deployment Support', 'status': 'To Do', 'priority': 'P0 (Blocking)', 'assignee': 'Pranav Kulkarni'},
    'CLN-122': {'summary': 'DCCU commitments', 'status': 'To Do', 'priority': 'P1 (Critical)', 'assignee': 'Pranav Kulkarni'},
    'CLN-141': {'summary': '[BMO] Personal Loans Upgrade — Phase 1', 'status': 'In Progress', 'priority': 'P1 (Critical)', 'assignee': 'Mike Mohan'},
    'CLN-151': {'summary': '[CL Q1 \'26] Named Account support', 'status': 'In Progress', 'priority': 'P1 (Critical)', 'assignee': 'Mike Mohan'},
    'CLN-144': {'summary': 'Cross sell enhancements', 'status': 'To Do', 'priority': 'P2 (Major)', 'assignee': 'Pranav Kulkarni'},
    'CLN-142': {'summary': '[BMO] Personal Loan Upgrade — Future Phase', 'status': 'To Do', 'priority': 'P2 (Major)', 'assignee': 'Mike Mohan'},
    'CLN-231': {'summary': '[CL] Teachers FCU commitments', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Ali Graham'},
    'CLN-242': {'summary': 'Consumer Lending template backlog', 'status': 'In Progress', 'priority': 'P3 (Minor)', 'assignee': 'Ali Graham'},
    'CLN-177': {'summary': '[CL Q1 \'26] Prioritized Bugs (Internal)', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'CLN-143': {'summary': '[CL Q1 \'26] Enhance configuration', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Pranav Kulkarni'},

    # CBP Epics (top active)
    'CBP-12276': {'summary': 'Conditional Logic Improvements', 'status': 'In Progress', 'priority': 'P3 (Minor)', 'assignee': 'Simon Leblanc'},
    'CBP-13221': {'summary': 'Builder Sustainability — Q1 2026', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'CBP-13323': {'summary': 'Automerge: Milestone 2 — Advanced Diffing', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'CBP-13324': {'summary': 'Automerge: Milestone 1 (MVP) — Basic Template Diffing', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'CBP-12809': {'summary': 'Builder Entity Usage Tracking: Blocks', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'CBP-13265': {'summary': 'Builder Multiplayer Experience: Milestone 1', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'CBP-13232': {'summary': 'Automerge: Approval Workflow for Main Templates', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'CBP-12710': {'summary': 'Integration Refactor Phase 3: Meta Node Races', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'CBP-9666':  {'summary': 'Accessibility | CP Components', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'CBP-11900': {'summary': 'UX enhancements for Builder access pilot', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'CBP-12854': {'summary': 'DB Connection Resiliency', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},

    # DD Epics
    'DD-118':  {'summary': 'Docutech MVP Support for Builder', 'status': 'To Do', 'priority': 'P0 (Blocking)', 'assignee': 'Henry Liu'},
    'DD-937':  {'summary': 'Stagger reminder emails to spread load', 'status': 'In Progress', 'priority': 'P1 (Critical)', 'assignee': 'Will Duan'},
    'DD-1308': {'summary': 'Delete irrelevant feature flags', 'status': 'To Do', 'priority': 'P1 (Critical)', 'assignee': 'Forest Trimble'},
    'DD-194':  {'summary': 'Documents Purge Cleanup', 'status': 'To Do', 'priority': 'P1 (Critical)', 'assignee': 'Forest Trimble'},
    'DD-1118': {'summary': 'Accept/Reject Follow-up Improvements', 'status': 'To Do', 'priority': 'P1 (Critical)', 'assignee': 'Jake Wasserman'},
    'DD-1874': {'summary': 'Document auto-tagging improvements for eclose', 'status': 'To Do', 'priority': 'P1 (Critical)', 'assignee': 'Unassigned'},
    'DD-1235': {'summary': 'Add retries in all lending calls from Disclosure service', 'status': 'To Do', 'priority': 'P1 (Critical)', 'assignee': 'Unassigned'},
    'DD-3509': {'summary': 'Disclosures CP Standardized APIs', 'status': 'To Do', 'priority': 'P2 (Major)', 'assignee': 'Forest Trimble'},
    'DD-3507': {'summary': 'Support In Person Signing in OneSpan', 'status': 'To Do', 'priority': 'P2 (Major)', 'assignee': 'Ya He'},
    'DD-3550': {'summary': 'DD OCE Tickets', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'DD-3422': {'summary': 'LO-Initiated Disclosures — Vesta', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Ari Mendelson'},
    'DD-2966': {'summary': 'blend/request vulnerabilities — undici migration', 'status': 'In Progress', 'priority': 'P3 (Minor)', 'assignee': 'Henry Liu'},

    # SENG Epics (top active)
    'SENG-1253': {'summary': 'Teachers FCU — Consumer Lending Project', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'SENG-1131': {'summary': 'FMB — Deposits Account v12 tracking', 'status': 'In Progress', 'priority': 'P3 (Minor)', 'assignee': 'Luis De Guevara'},
    'SENG-281':  {'summary': 'Citizens CC Minor Production Release: MR10', 'status': 'In Progress', 'priority': 'P3 (Minor)', 'assignee': 'Fernando Arana'},
    'SENG-1157': {'summary': 'NFCU — Legal Operations Portal on Builder', 'status': 'In Progress', 'priority': 'P3 (Minor)', 'assignee': 'Ivan Alvarez'},
    'SENG-1115': {'summary': '[LFCU] Consumer Banker Onboarding CC, PL, Auto', 'status': 'In Progress', 'priority': 'P3 (Minor)', 'assignee': 'Shivakumar Y'},
    'SENG-1852': {'summary': 'Credit One Bank DAv5', 'status': 'In Progress', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'SENG-1361': {'summary': 'Park National Bank — Consumer Lending', 'status': 'In Progress', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'SENG-1204': {'summary': 'Sunward — DA', 'status': 'In Progress', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'SENG-1364': {'summary': 'MACU Innovation Services DA + CL', 'status': 'In Progress', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'SENG-1801': {'summary': 'Ent — Consumer Lending', 'status': 'In Progress', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'SENG-1896': {'summary': 'Compeer: Innovation Services CL Q1 2026', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Zach Seprish'},
    'SENG-691':  {'summary': 'Citizens Credit Card — Support — PROD Issues', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},

    # DA Epics (Deposit Accounts)
    'DA-41':   {'summary': 'CDAO V12 Template', 'status': 'In Progress', 'priority': 'P0 (Blocking)', 'assignee': 'Unassigned'},
    'DA-554':  {'summary': 'Teachers FCU MVP Features', 'status': 'In Progress', 'priority': 'P0 (Blocking)', 'assignee': 'Ali Graham'},
    'DA-107':  {'summary': 'BDAO V1 Business Account Opening', 'status': 'To Do', 'priority': 'P1 (Critical)', 'assignee': 'Andres Vela'},
    'DA-1232': {'summary': 'ACR — DA v12 (2026)', 'status': 'To Do', 'priority': 'P1 (Critical)', 'assignee': 'George Zamfir'},
    'DA-1353': {'summary': 'LFCU V12 Upgrade MVP', 'status': 'To Do', 'priority': 'P1 (Critical)', 'assignee': 'Ali Graham'},
    'DA-1394': {'summary': 'Elements MVP Items for Upgrade to V12', 'status': 'To Do', 'priority': 'P2 (Major)', 'assignee': 'Unassigned'},
    'DA-1510': {'summary': "Deployment Support Q1 '26", 'status': 'To Do', 'priority': 'P2 (Major)', 'assignee': 'Unassigned'},
    'DA-1511': {'summary': "Production Support Q1 '26", 'status': 'To Do', 'priority': 'P2 (Major)', 'assignee': 'Unassigned'},
    'DA-1631': {'summary': 'Invite Joint Application Workflow Enhancements', 'status': 'To Do', 'priority': 'P2 (Major)', 'assignee': 'Unassigned'},
    'DA-4':    {'summary': 'DA OCE', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'DA-48':   {'summary': 'DA Deployment Issues', 'status': 'In Progress', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'DA-192':  {'summary': 'DA Feature Requests', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'DA-225':  {'summary': 'Feature Flag Removal', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'DA-396':  {'summary': 'Branch Group Assignments', 'status': 'In Progress', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'DA-635':  {'summary': 'Update V12 template to streamline experience', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'DA-636':  {'summary': 'Deployment Scaling', 'status': 'In Progress', 'priority': 'P3 (Minor)', 'assignee': 'Pablo Madrid'},
    'DA-978':  {'summary': 'Switchkit Provider Integrations', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Pablo Madrid'},
    'DA-1435': {'summary': 'CDAO V12 Minor and Below Bugs', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'DA-1609': {'summary': "NavyFed MORE Q1 '26", 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},

    # RHL Epics (Rapid Home Lending) — top 20 active
    'RHL-873':  {'summary': 'RHL Phase 2 — Mr. Cooper — HELOAN', 'status': 'In Progress', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'RHL-995':  {'summary': 'SoFi — REALLY RAPID HELOAN', 'status': 'In Progress', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'RHL-1140': {'summary': 'RHL Phase 1 — PHH — Conv Rate/Term', 'status': 'In Progress', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'RHL-1142': {'summary': 'RHE — MACU — Re-enable volume', 'status': 'In Progress', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'RHL-1178': {'summary': 'RHL Phase 1 — Hometrust — HELOC+HELOAN', 'status': 'In Progress', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'RHL-1181': {'summary': 'RHL Phase 1 — TFSB — VA IRRRL', 'status': 'In Progress', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'RHL-1182': {'summary': 'RHL Phase 1 — Vystar — HELOC', 'status': 'In Progress', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'RHL-1500': {'summary': 'HELOC Fixed Rate Flow', 'status': 'In Progress', 'priority': 'P3 (Minor)', 'assignee': 'Aaron Chan'},
    'RHL-45':   {'summary': 'Update AUS integration for LPA + More', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'RHL-802':  {'summary': 'Tech Debt/Scalability Loose Ends', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'RHL-870':  {'summary': '[HELOAN] Base template MVP', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'RHL-889':  {'summary': 'Rapid Home Lending Parking Lot', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'RHL-1179': {'summary': 'RHL Phase 1 — Citadel — HELOC', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'RHL-1180': {'summary': 'RHL Phase 1 — Regions — HE Prequal', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'RHL-1183': {'summary': 'RHL Phase 2 — SoFi — HELOAN Campaign 2', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'RHL-1184': {'summary': "Q3'2025 Harden for Scale", 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'RHL-1230': {'summary': "Q3'2025 — Research & Design", 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'RHL-1237': {'summary': "Q3'2025 Customer asks, Tech Debt + Internal Requests", 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'RHL-1256': {'summary': 'RHL — Progressive Qual ++', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'RHL-1293': {'summary': 'Blockifying Application Flow', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'RHL-1397': {'summary': 'Pennymac', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'RHL-1481': {'summary': 'Truework testing and deployment', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'RHL-1487': {'summary': 'RHL Phase 2 — PHH — VA IRRRL', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'RHL-1507': {'summary': 'Tracking PNC Phase 1 Go Live', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'RHL-1511': {'summary': 'Expand AVM Providers', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'RHL-1521': {'summary': 'Rollout Lender Intake Experience', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'RHL-1527': {'summary': 'Control Volume with AAN', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'RHL-1569': {'summary': 'Regions', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'RHL-1573': {'summary': 'Release Note Process and Deltas', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'RHL-1574': {'summary': 'PHH Versioning Analysis', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'RHL-1590': {'summary': 'Incorporating AI into Processes', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'RHL-1591': {'summary': 'Lender Configurations', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'RHL-1626': {'summary': 'Debt Consolidation', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'RHL-1652': {'summary': 'Navy Phase 1 Rollout', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'RHL-1658': {'summary': 'Q4 Scalability', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'RHL-1674': {'summary': 'QA Findings', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'RHL-1721': {'summary': 'Establish patterns for workflow development on app engine', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'RHL-1736': {'summary': 'Create configuration at workflow and task levels', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'RHL-1746': {'summary': 'Pricing Enhancements', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'RHL-1748': {'summary': 'Enhancing Internal Processes', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},

    # APEX Epics (Mortgage/Lending) — top active
    'APEX-1571': {'summary': "Q2'2025 Covered Integration", 'status': 'To Do', 'priority': 'P1 (Critical)', 'assignee': 'Unassigned'},
    'APEX-1796': {'summary': 'Encompass 2 Way Sync', 'status': 'To Do', 'priority': 'P1 (Critical)', 'assignee': 'Ajay Shekar'},
    'APEX-2368': {'summary': 'Preapprovals for HNB: Borrowers', 'status': 'To Do', 'priority': 'P1 (Critical)', 'assignee': 'Melissa Cohen'},
    'APEX-146':  {'summary': 'Purchase Affordability/Prequal Post-MVP', 'status': 'To Do', 'priority': 'P2 (Major)', 'assignee': 'Derrick Camerino'},
    'APEX-241':  {'summary': 'Borrower Node 18 upgrade', 'status': 'To Do', 'priority': 'P2 (Major)', 'assignee': 'Josh Yu'},
    'APEX-330':  {'summary': 'Typescript + Async/Await Conversions', 'status': 'In Progress', 'priority': 'P2 (Major)', 'assignee': 'Unassigned'},
    'APEX-988':  {'summary': 'Connecticut county value transition', 'status': 'In Progress', 'priority': 'P2 (Major)', 'assignee': 'Alejandro Camara'},
    'APEX-1572': {'summary': 'Q2-2025 HOI Maintenance', 'status': 'To Do', 'priority': 'P2 (Major)', 'assignee': 'Unassigned'},
    'APEX-1772': {'summary': 'Reduce ElasticSearch calls on pipeline', 'status': 'To Do', 'priority': 'P2 (Major)', 'assignee': 'Unassigned'},
    'APEX-1949': {'summary': 'Desktop Originator Integration', 'status': 'In Progress', 'priority': 'P2 (Major)', 'assignee': 'Siddhartha Paul'},
    'APEX-2698': {'summary': '[HNB] Improve Optimal Blue experience', 'status': 'To Do', 'priority': 'P2 (Major)', 'assignee': 'Melissa Cohen'},
    'APEX-2':    {'summary': 'Engineering Improvements', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Rahul Grewal'},
    'APEX-168':  {'summary': 'LF Feature Flag Removal', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'APEX-254':  {'summary': 'Remove/Consolidate Feature Flags', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'APEX-753':  {'summary': 'Support refinance-only mortgage applications', 'status': 'In Progress', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'APEX-840':  {'summary': 'Talkuments Integration', 'status': 'In Progress', 'priority': 'P3 (Minor)', 'assignee': 'Tim Liew'},
    'APEX-974':  {'summary': 'Remove critical vulns in home-insurance repo', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Alejandro Camara'},
    'APEX-1083': {'summary': 'Make Magic Link work on Lending', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'APEX-1101': {'summary': 'Pipeline v3 Issues', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Rahul Grewal'},
    'APEX-1129': {'summary': 'Buy Before You Sell with Homelight', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'APEX-1313': {'summary': 'Move HOI quoting logic to Covered', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Alejandro Camara'},
    'APEX-1398': {'summary': 'Support Doma in Borrower UI', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'APEX-1457': {'summary': 'Accessibility Audit (ACR) — Mortgage — 2025', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'APEX-1507': {'summary': 'HOI related tasks', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'APEX-1518': {'summary': 'I18n improvements for Builder Apps', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'APEX-1520': {'summary': 'Parking Lot — Spanish Intake', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'APEX-1556': {'summary': "Q2'2025 Customer + Internal Requests", 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'APEX-1605': {'summary': 'Refine Glia — Post-MVP Updates', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'APEX-1813': {'summary': 'Blend-owned Polly Integration', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'APEX-1856': {'summary': 'Group Management Organization and Email Branding', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Charles Pardee'},
    'APEX-1914': {'summary': 'Q3 APEX Tech Debt Improvements', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'APEX-1960': {'summary': 'Pricing DB free space', 'status': 'In Progress', 'priority': 'P3 (Minor)', 'assignee': 'Megan McDevitt'},
    'APEX-2001': {'summary': 'Support grouping in borrower home and post-submit tasks', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Miguel Islas Hernandez'},
    'APEX-2215': {'summary': 'Q3 APEX On-Call Work', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'APEX-2268': {'summary': '[HNB] Add fees to Decision Management Studio', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'APEX-2318': {'summary': '3+ borrowers followup — swap borrowers between pairs', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'APEX-2338': {'summary': 'Keep Navy Green', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'APEX-2353': {'summary': 'Q4 2025 APEX On Call Work', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'APEX-2354': {'summary': 'Q4 2025 APEX Tech Debt Improvements', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'APEX-2422': {'summary': 'Q4 2025 APEX Customer Requests', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'APEX-2424': {'summary': 'Fannie Mae 6.0 Upgrade', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'APEX-2742': {'summary': '[All Client] Implement turnstile to increase security', 'status': 'In Progress', 'priority': 'P3 (Minor)', 'assignee': 'Kimberly Zurbrick'},

    # BAI Epics (Blend AI)
    'BAI-503':  {'summary': 'Production Ready', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'BAI-505':  {'summary': 'Scalability', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'BAI-506':  {'summary': 'AI Value Dashboard — Real-time Executive Reporting', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Nickolas Scipione'},
    'BAI-507':  {'summary': 'Redaction issues', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Akhil Jalla'},
    'BAI-508':  {'summary': 'LO Chat Assistant — Phase II-A: Conversational AI', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'BAI-509':  {'summary': 'Deploy AI Repo to EKS', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Hai Ly'},
    'BAI-510':  {'summary': 'RAG', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'BAI-511':  {'summary': 'Code clean up', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'BAI-512':  {'summary': 'Update UI', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Hai Ly'},
    'BAI-513':  {'summary': 'Closing Docs QC', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Niranjan Cholendiran'},
    'BAI-514':  {'summary': 'AI-Dev-Workflow-Integrations', 'status': 'In Progress', 'priority': 'P3 (Minor)', 'assignee': 'Nickolas Scipione'},
    'BAI-515':  {'summary': 'Prod Infra Setup', 'status': 'In Progress', 'priority': 'P3 (Minor)', 'assignee': 'Hai Ly'},
    'BAI-516':  {'summary': 'Incorporating Feedback', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'BAI-517':  {'summary': 'Intelligent Origination', 'status': 'In Progress', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'BAI-518':  {'summary': 'Validation Errors', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'BAI-519':  {'summary': 'Blend Beta & Prod Architecture', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'BAI-523':  {'summary': 'Evals', 'status': 'In Progress', 'priority': 'P3 (Minor)', 'assignee': 'Nickolas Scipione'},
    'BAI-545':  {'summary': 'Lender Self-Serve AI Activation (Config Center)', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'BAI-579':  {'summary': 'Custom Underwriting Guidelines for Underwriter Agent', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'BAI-588':  {'summary': 'Borrower-Facing Document Review Status', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},

    # QUAL Epics (Quality Engineering)
    'QUAL-9549':  {'summary': 'Dummy1-Client DA upgrade', 'status': 'In Progress', 'priority': 'P0 (Blocking)', 'assignee': 'Shrinidhi Patil'},
    'QUAL-10297': {'summary': 'Rapid Home Lending — Conventional Cashout Automation', 'status': 'To Do', 'priority': 'P0 (Blocking)', 'assignee': 'Unassigned'},
    'QUAL-10332': {'summary': 'DA V12 Base Template Test Cases Automation', 'status': 'To Do', 'priority': 'P1 (Critical)', 'assignee': 'Unassigned'},
    'QUAL-10831': {'summary': 'GenAI — VegetableShop_Order Fulfilment', 'status': 'To Do', 'priority': 'P1 (Critical)', 'assignee': 'Archana Bangar'},
    'QUAL-443':   {'summary': 'Limited E2Es for external services', 'status': 'In Progress', 'priority': 'P2 (Major)', 'assignee': 'Michael Millerick'},
    'QUAL-1588':  {'summary': 'Cross service integration tests', 'status': 'In Progress', 'priority': 'P2 (Major)', 'assignee': 'Michael Evans'},
    'QUAL-9550':  {'summary': 'Dummy2- Client DA upgrade', 'status': 'In Progress', 'priority': 'P2 (Major)', 'assignee': 'Shrinidhi Patil'},
    'QUAL-9838':  {'summary': 'Migrate Mabl Tests to Playwright', 'status': 'In Progress', 'priority': 'P2 (Major)', 'assignee': 'Archana Bangar'},
    'QUAL-9839':  {'summary': 'Migrate Caliper Tests to Playwright', 'status': 'In Progress', 'priority': 'P2 (Major)', 'assignee': 'Archana Bangar'},
    'QUAL-9840':  {'summary': 'Integrate Testing Pipeline To Dev Pipeline', 'status': 'In Progress', 'priority': 'P2 (Major)', 'assignee': 'Archana Bangar'},
    'QUAL-9841':  {'summary': 'Robust framework setup for Config Platform Tests', 'status': 'In Progress', 'priority': 'P2 (Major)', 'assignee': 'Archana Bangar'},
    'QUAL-1661':  {'summary': 'Unified data integrity checks', 'status': 'In Progress', 'priority': 'P3 (Minor)', 'assignee': 'Michael Millerick'},
    'QUAL-3375':  {'summary': 'Migrate existing caliper tests to use external api 4.0.0', 'status': 'In Progress', 'priority': 'P3 (Minor)', 'assignee': 'Jeremy Lai'},
    'QUAL-4118':  {'summary': 'Create tests for blend-worker library', 'status': 'In Progress', 'priority': 'P3 (Minor)', 'assignee': 'Michael Brooks'},
    'QUAL-4752':  {'summary': 'Improve Config Platform Workflow Controller', 'status': 'In Progress', 'priority': 'P3 (Minor)', 'assignee': 'Vincent Xu'},
    'QUAL-4949':  {'summary': 'Lending unit tests on Github Actions', 'status': 'In Progress', 'priority': 'P3 (Minor)', 'assignee': 'Michael Millerick'},
    'QUAL-5333':  {'summary': 'parties collection userId&topicId unique index removal tests', 'status': 'In Progress', 'priority': 'P3 (Minor)', 'assignee': 'Anthony Ma'},
    'QUAL-5408':  {'summary': "Jordan's QA To Do List", 'status': 'In Progress', 'priority': 'P3 (Minor)', 'assignee': 'Jordan Jones'},
    'QUAL-5486':  {'summary': 'Code Review Bot RFC Changes', 'status': 'In Progress', 'priority': 'P3 (Minor)', 'assignee': 'Michael Brooks'},
    'QUAL-5859':  {'summary': 'Allow manual strategies for publishing packages', 'status': 'In Progress', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'QUAL-6965':  {'summary': 'X-Ray JIRA Demo project', 'status': 'In Progress', 'priority': 'P3 (Minor)', 'assignee': 'Dhaney Palanisamy'},
    'QUAL-7074':  {'summary': 'MortgageAutomation_P0/P1 test cases', 'status': 'In Progress', 'priority': 'P3 (Minor)', 'assignee': 'Archana Bangar'},
    'QUAL-9891':  {'summary': 'GenAI Hackathon — Story to Stable', 'status': 'In Progress', 'priority': 'P3 (Minor)', 'assignee': 'Archana Bangar'},
    'QUAL-10354': {'summary': 'RHL-Base-Test Cases Automation', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'QUAL-10618': {'summary': 'CL Base Template Test Cases Automation', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
    'QUAL-10840': {'summary': 'Build login functionality from Mockup screen', 'status': 'To Do', 'priority': 'P3 (Minor)', 'assignee': 'Unassigned'},
}

# ── Merge stories into epics ─────────────────────────────────────────
epic_data = {}
for key, info in all_epics.items():
    proj = key.split('-')[0]
    stories_dict = epic_stories.get(key, {})
    stories = list(stories_dict.values())
    bugs = [s for s in stories if s.get('type', '').lower() == 'bug']
    tasks = [s for s in stories if s.get('type', '').lower() not in ('bug', '')]
    done = sum(1 for s in stories if s.get('status_cat') == 'Done')
    in_prog = sum(1 for s in stories if s.get('status_cat') == 'In Progress')
    todo = sum(1 for s in stories if s.get('status_cat') == 'To Do')
    epic_data[key] = {
        **info,
        'key': key,
        'project': proj,
        'stories': stories,
        'story_count': len(stories),
        'bug_count': len(bugs),
        'done': done,
        'in_progress': in_prog,
        'todo': todo,
    }

# Group by project
projects = {}
for key, ep in epic_data.items():
    proj = ep['project']
    if proj not in projects:
        projects[proj] = []
    projects[proj].append(ep)

# Sort within each project by priority then key
priority_order = {'P0': 0, 'P1': 1, 'P2': 2, 'P3': 3, 'P4': 4}
for proj in projects:
    projects[proj].sort(key=lambda e: (priority_order.get(e['priority'][:2], 5), e['key']))

proj_list = sorted(projects.keys())
total_epics = len(epic_data)
total_stories = sum(e['story_count'] for e in epic_data.values())
total_bugs = sum(e['bug_count'] for e in epic_data.values())

# ── Orphan Stories/Bugs (no parent Epic) — from JIRA queries ─────────
orphan_counts = {
    'APEX': 50, 'DD': 50, 'DA': 50, 'CBP': 50, 'QUAL': 50,
    'BAI': 34, 'RHL': 18, 'SENG': 9, 'CLN': 2,
    'DDINDIA': 0, 'IMB': 0,
}
# Projects with 50 have 50+ (API limit), mark them
orphan_capped = {'APEX', 'DD', 'DA', 'CBP', 'QUAL'}
total_orphans = sum(orphan_counts.values())

proj_colors = {
    'DDINDIA': '#22d3ee', 'CLN': '#60a5fa', 'CBP': '#a78bfa',
    'DD': '#34d399', 'SENG': '#fb923c', 'IMB': '#f87171',
    'DA': '#c084fc', 'RHL': '#f472b6', 'APEX': '#38bdf8',
    'BAI': '#facc15', 'QUAL': '#4ade80',
}

def clr(p): return proj_colors.get(p, '#94a3b8')
def bg(p): return proj_colors.get(p, '#94a3b8').replace('#','rgba(') and f"rgba({int(proj_colors.get(p,'#94a3b8')[1:3],16)},{int(proj_colors.get(p,'#94a3b8')[3:5],16)},{int(proj_colors.get(p,'#94a3b8')[5:7],16)},.12)"
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
def esc(s): return s.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')

now = datetime.now().strftime('%B %d, %Y %I:%M %p')

# ── Build HTML ────────────────────────────────────────────────────────
h = []
h.append(f'''<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Epic → Story &amp; Bug Mapping — All Projects | Blend Engineering</title>
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
.grid-3{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:20px;margin-bottom:24px}}
.card{{background:linear-gradient(135deg,#111827 0%,#151c32 100%);border:1px solid rgba(99,102,241,.12);border-radius:14px;padding:22px}}
.card h3{{font-size:.95rem;font-weight:600;color:#a5b4fc;margin-bottom:16px;display:flex;align-items:center;gap:8px}}
.chart-wrap{{position:relative;width:100%;height:300px}}
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
@media(max-width:1024px){{.kpi-row{{grid-template-columns:repeat(3,1fr)}}.grid-2,.grid-3{{grid-template-columns:1fr}}.story-row{{grid-template-columns:80px 50px 1fr 80px 100px 120px}}}}
</style></head><body><div class="container">
<header>
  <a href="index.html" style="display:inline-flex;align-items:center;gap:6px;text-decoration:none;color:#94a3b8;font-size:.78rem;font-weight:600;padding:5px 14px;border:1px solid rgba(99,102,241,.2);border-radius:8px;margin-bottom:12px;transition:all .15s" onmouseover="this.style.background='rgba(99,102,241,.15)';this.style.color='#a5b4fc'" onmouseout="this.style.background='transparent';this.style.color='#94a3b8'">&larr; Home</a>
  <h1>Epic → Story &amp; Bug Mapping — All Projects</h1>
  <p>Comprehensive view of active Epics and their child Stories, Bugs &amp; Tasks</p>
  <div class="ts">{' &bull; '.join(proj_list)} &mdash; Data from JIRA &bull; {now}</div>
</header>''')

# KPIs (5 key metrics)
h.append(f'''<div class="kpi-row">
  <div class="kpi"><div class="val" style="color:#a78bfa">{total_epics}</div><div class="lbl">Active Epics</div></div>
  <div class="kpi"><div class="val" style="color:#818cf8">{total_stories}</div><div class="lbl">Children Mapped</div></div>
  <div class="kpi"><div class="val" style="color:#f87171">{total_bugs}</div><div class="lbl">Bugs</div></div>
  <div class="kpi"><div class="val" style="color:#fb923c">{total_orphans}+</div><div class="lbl">Orphan Items</div></div>
  <div class="kpi"><div class="val" style="color:#60a5fa">{len(proj_list)}</div><div class="lbl">Projects</div></div>
</div>''')

# Project summary cards
h.append('<div class="section-title">Project Overview</div><div class="proj-summary">')
for proj in proj_list:
    eps = projects[proj]
    sc = sum(e['story_count'] for e in eps)
    bc = sum(e['bug_count'] for e in eps)
    dc = sum(e['done'] for e in eps)
    pc = round(dc/sc*100) if sc else 0
    active = sum(1 for e in eps if 'Progress' in e['status'])
    blocked = sum(1 for e in eps if 'Block' in e['status'])
    h.append(f'''<div class="proj-card" style="border-color:{clr(proj)}">
      <h4 style="color:{clr(proj)}">{proj}</h4>
      <div class="stat"><strong>{len(eps)}</strong> Epics &bull; <strong>{sc}</strong> Children &bull; <strong style="color:#f87171">{bc}</strong> Bugs</div>
      <div class="stat"><strong>{active}</strong> active &bull; <strong>{blocked}</strong> blocked &bull; <strong>{pc}%</strong> done</div>
    </div>''')
h.append('</div>')

# Charts (2-column for better readability)
h.append('''<div class="section-title">Distribution Charts</div>
<div class="grid-2">
  <div class="card"><h3>📊 Epics by Project</h3><div class="chart-wrap"><canvas id="epicChart"></canvas></div></div>
  <div class="card"><h3>🎯 Epic Priority Distribution</h3><div class="chart-wrap"><canvas id="prioChart"></canvas></div></div>
</div>
<div class="grid-2">
  <div class="card"><h3>📈 Epic Status Breakdown</h3><div class="chart-wrap"><canvas id="statusChart"></canvas></div></div>
  <div class="card"><h3>🐛 Bugs by Project</h3><div class="chart-wrap"><canvas id="bugChart"></canvas></div></div>
</div>''')

# Filter + Epic blocks with toolbar (search, expand/collapse, pagination)
h.append('<div class="section-title">Epic → Story Details</div>')
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
    h.append(f'    <button class="filter-btn" onclick="filterProject(\'{p}\')" style="border-color:{clr(p)}50">{p} ({len(projects[p])})</button>')
h.append('''  </div>
</div>
<div id="pageInfo" class="page-info" style="text-align:center;margin-bottom:12px"></div>''')

for proj in proj_list:
    for ep in projects[proj]:
        stories = ep['stories']
        pct = round(ep['done']/ep['story_count']*100) if ep['story_count'] else 0
        
        h.append(f'<div class="epic-block" data-project="{proj}">')
        h.append(f'<div class="epic-header" onclick="this.parentElement.classList.toggle(\'open\')">')
        h.append(f'<span class="toggle-icon">&#9654;</span>')
        h.append(f'<span class="proj-tag" style="background:{bg(proj)};color:{clr(proj)}">{proj}</span>')
        h.append(f'<span class="epic-key"><a href="https://blendlabs.atlassian.net/browse/{ep["key"]}" target="_blank">{ep["key"]}</a></span>')
        h.append(f'<span class="epic-summary">{esc(ep["summary"])}</span>')
        h.append(f'<span class="epic-meta">')
        h.append(f'<span class="badge {pbadge(ep["priority"])}">{ep["priority"][:2]}</span>')
        h.append(f'<span class="badge {sbadge(ep["status"])}">{esc(ep["status"])}</span>')
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
            for s in sorted(stories, key=lambda x: (0 if x['status_cat']=='In Progress' else 1 if x['status_cat']=='To Do' else 2, x['key'])):
                h.append(f'<div class="story-row">')
                h.append(f'<span class="story-key"><a href="https://blendlabs.atlassian.net/browse/{s["key"]}" target="_blank">{s["key"]}</a></span>')
                itype = s.get('type', 'Story')
                itype_cls = 'badge-bug' if itype.lower() == 'bug' else ('badge-task' if 'task' in itype.lower() else 'badge-story')
                h.append(f'<span><span class="badge {itype_cls}">{esc(itype)}</span></span>')
                h.append(f'<span class="story-summary" title="{esc(s["summary"])}">{esc(s["summary"])}</span>')
                h.append(f'<span><span class="badge {pbadge(s["priority"])}">{s["priority"][:2]}</span></span>')
                h.append(f'<span><span class="badge {sbadge(s["status"])}">{esc(s["status"])}</span></span>')
                h.append(f'<span style="font-size:.72rem;color:#94a3b8">{esc(s["assignee"])}</span>')
                h.append(f'</div>')
        else:
            h.append('<div class="no-stories">No child stories mapped yet — click the Epic key to view in JIRA</div>')
        h.append('</div></div>')

# Pagination controls
h.append('<div class="page-controls" id="pageControls"></div>')

# ── Orphan Stories & Bugs Section ──────────────────────────────────
h.append('<div class="section-title">Orphan Stories &amp; Bugs (No Parent Epic)</div>')
h.append('<p style="color:#94a3b8;font-size:.85rem;margin-bottom:20px">Active Stories and Bugs that are <strong style="color:#fb923c">not linked</strong> to any Epic. These items need triaging and assignment to an appropriate Epic for better tracking.</p>')

# Orphan summary grid
h.append('<div class="grid-2">')
# Chart card
h.append('<div class="card"><h3>Orphans by Project</h3><div class="chart-wrap"><canvas id="orphanChart"></canvas></div></div>')
# Table card
h.append('<div class="card"><h3>Orphan Breakdown</h3><table style="width:100%;border-collapse:collapse;font-size:.82rem">')
h.append('<tr style="border-bottom:1px solid rgba(99,102,241,.15);color:#94a3b8;text-align:left"><th style="padding:8px 12px">Project</th><th style="padding:8px 12px">Orphan Count</th><th style="padding:8px 12px">Status</th></tr>')

orphan_sorted = sorted(orphan_counts.items(), key=lambda x: -x[1])
for proj_name, cnt in orphan_sorted:
    if cnt == 0:
        severity = '<span class="badge badge-done">Clean</span>'
    elif cnt >= 50:
        severity = '<span class="badge badge-p0">Critical (50+)</span>'
    elif cnt >= 20:
        severity = '<span class="badge badge-p1">High</span>'
    elif cnt >= 5:
        severity = '<span class="badge badge-p2">Medium</span>'
    else:
        severity = '<span class="badge badge-p3">Low</span>'
    capped = '+' if proj_name in orphan_capped else ''
    bar_w = min(cnt, 50) * 2
    h.append(f'<tr style="border-bottom:1px solid rgba(99,102,241,.06)">')
    h.append(f'<td style="padding:8px 12px"><span class="proj-tag" style="background:{bg(proj_name)};color:{clr(proj_name)}">{proj_name}</span></td>')
    h.append(f'<td style="padding:8px 12px"><strong style="color:#e2e8f0">{cnt}{capped}</strong> <span style="display:inline-block;width:{bar_w}px;height:6px;background:{clr(proj_name)};border-radius:3px;vertical-align:middle;margin-left:6px"></span></td>')
    h.append(f'<td style="padding:8px 12px">{severity}</td>')
    h.append('</tr>')

h.append(f'<tr style="border-top:2px solid rgba(99,102,241,.2);font-weight:700"><td style="padding:10px 12px;color:#a5b4fc">TOTAL</td><td style="padding:10px 12px;color:#fb923c;font-size:1rem">{total_orphans}+</td><td style="padding:10px 12px;color:#94a3b8;font-size:.75rem">5 projects at API limit (50+)</td></tr>')
h.append('</table></div>')
h.append('</div>')

# Recommendation callout
h.append(f'''<div style="background:rgba(251,146,60,.08);border:1px solid rgba(251,146,60,.2);border-radius:12px;padding:20px;margin-top:16px;margin-bottom:24px">
  <h4 style="color:#fb923c;margin-bottom:8px;font-size:.95rem">Action Required: {total_orphans}+ Orphan Items Need Triage</h4>
  <ul style="color:#94a3b8;font-size:.82rem;list-style:disc;padding-left:20px;line-height:1.8">
    <li><strong style="color:#e2e8f0">APEX, DD, DA, CBP, QUAL</strong> each have 50+ orphans — actual counts may be higher</li>
    <li>Review and assign orphan stories/bugs to appropriate Epics for sprint planning visibility</li>
    <li>Consider creating "Backlog" or "Tech Debt" epics for items that don't fit existing epics</li>
    <li><strong style="color:#4ade80">DDINDIA</strong> is the cleanest project — all items linked to Epics</li>
  </ul>
</div>''')

# Footer
h.append(f'''<footer>Epic → Story &amp; Bug Mapping Report &bull; {' &bull; '.join(proj_list)} &bull; Data from JIRA &bull; {now}</footer></div>''')

# Charts JS
p0 = sum(1 for e in epic_data.values() if 'P0' in e['priority'])
p1 = sum(1 for e in epic_data.values() if 'P1' in e['priority'])
p2 = sum(1 for e in epic_data.values() if 'P2' in e['priority'])
p3 = sum(1 for e in epic_data.values() if 'P3' in e['priority'])
st_todo = sum(1 for e in epic_data.values() if e['status'] == 'To Do')
st_prog = sum(1 for e in epic_data.values() if 'Progress' in e['status'])
st_block = sum(1 for e in epic_data.values() if 'Block' in e['status'])

import json as J
h.append(f'''<script>
Chart.defaults.color='#94a3b8';Chart.defaults.borderColor='rgba(99,102,241,0.06)';
Chart.defaults.font.family="'Segoe UI',system-ui,sans-serif";

new Chart(document.getElementById('epicChart'),{{
  type:'bar',data:{{labels:{J.dumps(proj_list)},datasets:[{{label:'Epics',
    data:{J.dumps([len(projects[p]) for p in proj_list])},
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
    data:{J.dumps([sum(e['bug_count'] for e in projects[p]) for p in proj_list])},
    backgroundColor:{J.dumps([clr(p) for p in proj_list])},
    borderWidth:0,borderRadius:4}}]}},
  options:{{responsive:true,maintainAspectRatio:false,plugins:{{legend:{{display:false}}}},
    scales:{{x:{{grid:{{display:false}}}},y:{{grid:{{color:'rgba(99,102,241,.05)'}},beginAtZero:true}}}}}}
}});

// ===== Pagination, Search, Filter =====
const PAGE_SIZE = 25;
let currentPage = 1;
let currentFilter = 'all';
let currentSearch = '';

function getVisibleEpics() {{
  const blocks = Array.from(document.querySelectorAll('.epic-block'));
  return blocks.filter(el => {{
    const matchProj = currentFilter === 'all' || el.dataset.project === currentFilter;
    if (!matchProj) return false;
    if (!currentSearch) return true;
    const q = currentSearch.toLowerCase();
    const text = el.textContent.toLowerCase();
    return text.includes(q);
  }});
}}

function renderPage() {{
  const visible = getVisibleEpics();
  const totalPages = Math.max(1, Math.ceil(visible.length / PAGE_SIZE));
  if (currentPage > totalPages) currentPage = totalPages;
  const start = (currentPage - 1) * PAGE_SIZE;
  const end = start + PAGE_SIZE;
  // Hide all, show only current page
  document.querySelectorAll('.epic-block').forEach(el => el.style.display = 'none');
  visible.forEach((el, i) => {{ el.style.display = (i >= start && i < end) ? '' : 'none'; }});
  // Page info
  const info = document.getElementById('pageInfo');
  info.textContent = 'Showing ' + (start+1) + '-' + Math.min(end, visible.length) + ' of ' + visible.length + ' epics';
  // Page controls
  const ctrl = document.getElementById('pageControls');
  let btns = '<button class="page-btn" onclick="goPage(1)" ' + (currentPage===1?'disabled':'') + '>&laquo; First</button>';
  btns += '<button class="page-btn" onclick="goPage('+(currentPage-1)+')" ' + (currentPage===1?'disabled':'') + '>&lsaquo; Prev</button>';
  const range = 3;
  for (let p = Math.max(1,currentPage-range); p <= Math.min(totalPages,currentPage+range); p++) {{
    btns += '<button class="page-btn ' + (p===currentPage?'active':'') + '" onclick="goPage('+p+')">'+p+'</button>';
  }}
  btns += '<button class="page-btn" onclick="goPage('+(currentPage+1)+')" ' + (currentPage>=totalPages?'disabled':'') + '>Next &rsaquo;</button>';
  btns += '<button class="page-btn" onclick="goPage('+totalPages+')" ' + (currentPage>=totalPages?'disabled':'') + '>Last &raquo;</button>';
  ctrl.innerHTML = btns;
}}

function goPage(p) {{ currentPage = p; renderPage(); }}

function filterProject(proj) {{
  document.querySelectorAll('.filter-btn').forEach(b=>b.classList.remove('active'));
  event.target.classList.add('active');
  currentFilter = proj;
  currentPage = 1;
  renderPage();
}}

function searchEpics(q) {{
  currentSearch = q;
  currentPage = 1;
  renderPage();
}}

function toggleAll(expand) {{
  const visible = getVisibleEpics();
  const start = (currentPage - 1) * PAGE_SIZE;
  const end = start + PAGE_SIZE;
  visible.forEach((el, i) => {{
    if (i >= start && i < end) {{
      if (expand) el.classList.add('open');
      else el.classList.remove('open');
    }}
  }});
}}

// Initial render
renderPage();

// Orphan chart
(function(){{
  const orphanLabels = {J.dumps([p for p, _ in orphan_sorted if orphan_counts[p] > 0])};
  const orphanData = {J.dumps([c for _, c in orphan_sorted if c > 0])};
  const orphanColors = {J.dumps([clr(p) for p, _ in orphan_sorted if orphan_counts[p] > 0])};
  new Chart(document.getElementById('orphanChart'),{{
    type:'bar',
    data:{{labels:orphanLabels,datasets:[{{
      label:'Orphan Stories & Bugs',
      data:orphanData,
      backgroundColor:orphanColors,
      borderWidth:0,borderRadius:4
    }}]}},
    options:{{
      indexAxis:'y',
      responsive:true,maintainAspectRatio:false,
      plugins:{{
        legend:{{display:false}},
        tooltip:{{callbacks:{{label:function(c){{return c.raw+'+ items (no Epic parent)';}}}}}}
      }},
      scales:{{
        x:{{grid:{{color:'rgba(99,102,241,.05)'}},beginAtZero:true,title:{{display:true,text:'Count',color:'#64748b',font:{{size:10}}}}}},
        y:{{grid:{{display:false}}}}
      }}
    }}
  }});
}})();
</script></body></html>''')

output = '/Users/vinay-prasadg/Documents/Production Defects/epic-story-mapping.html'
with open(output, 'w') as f:
    f.write('\n'.join(h))

print(f'Report: {output}')
print(f'Epics: {total_epics} | Children mapped: {total_stories} | Bugs: {total_bugs} | Orphans: {total_orphans}+')
for p in proj_list:
    eps = projects[p]
    bc = sum(e['bug_count'] for e in eps)
    oc = orphan_counts.get(p, 0)
    capped = '+' if p in orphan_capped else ''
    print(f'  {p}: {len(eps)} epics, {sum(e["story_count"] for e in eps)} children ({bc} bugs), {oc}{capped} orphans')
