"""Load the most recent session from Supabase."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
project_root = Path(__file__).parent
load_dotenv(project_root / ".env")

from agent_factory.memory.storage import SupabaseMemoryStorage
import json

storage = SupabaseMemoryStorage()

print("="*70)
print("SESSION RESUME FROM SUPABASE")
print("="*70)

# Find most recent session
print("\nFinding recent sessions...")

# Try to find sessions for either claude_user or test_user
sessions = []
for user_id in ["claude_user", "test_user"]:
    result = storage.query_memory_atoms(
        user_id=user_id,
        memory_type='context',
        limit=5
    )
    if result:
        sessions.extend(result)
        break

if not sessions:
    # Fall back to finding ANY context entries
    print("No user-specific sessions found, searching all contexts...")
    all_contexts = storage.client.table('session_memories').select('*').eq('memory_type', 'context').order('created_at', desc=True).limit(5).execute()
    sessions = all_contexts.data

if not sessions:
    print("No sessions found. Use /memory-save to create your first session.")
    exit(0)

user_id = sessions[0]['user_id']
print(f"Found {len(sessions)} sessions for user: {user_id}")

# Get latest session
latest = sessions[0]
session_id = latest['session_id']
print(f"Loading session: {session_id}\n")

# Get all atoms for this session
atoms = storage.query_memory_atoms(session_id=session_id, limit=100)

print(f"\nSession ID: {session_id}")
print(f"User: {atoms[0]['user_id']}")
print(f"Last Active: {atoms[0]['created_at'][:19]}")
print(f"Total Memory Atoms: {len(atoms)}\n")

# Organize by type
context = [a for a in atoms if a['memory_type'] == 'context']
decisions = [a for a in atoms if a['memory_type'] == 'decision']
actions = [a for a in atoms if a['memory_type'] == 'action']
issues = [a for a in atoms if a['memory_type'] == 'issue']
logs = [a for a in atoms if a['memory_type'] == 'log']

if context:
    print("CURRENT STATUS")
    print("-"*70)
    ctx = context[0]['content']
    print(f"Project: {ctx.get('project', 'Unknown')}")
    print(f"Phase: {ctx.get('phase', 'Unknown')}")
    print(f"Status: {ctx.get('status', 'Unknown')}")
    print()

    if 'recent_changes' in ctx:
        print("Recent Changes:")
        for change in ctx['recent_changes']:
            print(f"  - {change}")
        print()

    if 'blockers' in ctx and ctx['blockers']:
        print(f"Blockers: {', '.join(ctx['blockers'])}")
    else:
        print("Blockers: None")
    print()

if decisions:
    print(f"DECISIONS ({len(decisions)} total)")
    print("-"*70)
    for i, d in enumerate(decisions, 1):
        content = d['content']
        print(f"{i}. {content.get('title', 'Untitled')}")
        print(f"   Rationale: {content.get('rationale', 'N/A')}")
        print(f"   Impact: {content.get('impact', 'unknown')}")
        print()

if actions:
    print(f"ACTIONS ({len(actions)} total)")
    print("-"*70)
    for i, a in enumerate(actions, 1):
        content = a['content']
        status = content.get('status', 'pending')
        priority = content.get('priority', 'medium')
        desc = content.get('task', content.get('description', 'No description'))
        print(f"{i}. [{priority.upper()}] [{status}] {desc}")
    print()

if issues:
    print(f"ISSUES ({len(issues)} total)")
    print("-"*70)
    for i, issue in enumerate(issues, 1):
        content = issue['content']
        severity = content.get('severity', 'medium')
        title = content.get('title', 'Untitled')
        status = content.get('status', 'open')
        print(f"{i}. [{severity.upper()}] {title}")
        print(f"   Status: {status}")
        if 'root_cause' in content:
            print(f"   Root Cause: {content['root_cause']}")
        print()

if logs:
    print("DEVELOPMENT LOG")
    print("-"*70)
    for log in logs:
        content = log['content']
        print(f"Title: {content.get('title', 'Untitled')}")
        if 'activities' in content:
            print("Activities:")
            for activity in content['activities']:
                print(f"  - {activity}")
        if 'files_created' in content or 'files_modified' in content:
            print(f"Files: {content.get('files_created', 0)} created, "
                  f"{content.get('files_modified', 0)} modified")
        print()

print("="*70)
print(f"[OK] Loaded from Supabase: {len(context)} context, {len(decisions)} decisions, "
      f"{len(actions)} actions, {len(issues)} issues, {len(logs)} logs")
print("="*70)
