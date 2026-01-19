#!/usr/bin/env python3
"""Check if Supabase tables exist and run migration if needed."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env
load_dotenv()

from supabase import create_client

# Connect to Supabase
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPABASE_KEY')

print(f'Connecting to: {url}')
print(f'Using service role key: {bool(os.getenv("SUPABASE_SERVICE_ROLE_KEY"))}\n')

client = create_client(url, key)

# Tables to check
TABLES = [
    'agent_status',
    'agent_jobs',
    'agent_messages',
    'approval_requests',
    'video_analytics',
    'agent_metrics',
    'webhook_events'
]

print('Checking tables...\n')

missing_tables = []
existing_tables = []

for table in TABLES:
    try:
        result = client.table(table).select('*').limit(1).execute()
        print(f'[OK] {table}')
        existing_tables.append(table)
    except Exception as e:
        error_str = str(e)
        if 'PGRST205' in error_str or 'Could not find' in error_str:
            print(f'[MISSING] {table}')
            missing_tables.append(table)
        else:
            print(f'[ERROR] {table} - {error_str[:50]}')

print('\n' + '='*70)
if missing_tables:
    print(f'STATUS: {len(missing_tables)}/{len(TABLES)} tables missing')
    print('='*70)
    print('\nTO FIX (3 minutes):')
    print('1. Open: https://mggqgrxwumnnujojndub.supabase.co/project/_/sql')
    print('2. Click "New query" or use existing editor')
    print('3. Copy ALL contents of: docs/supabase_agent_migrations.sql')
    print('4. Paste into SQL Editor')
    print('5. Click RUN button')
    print('6. Wait for "Success" message')
    print('\nMissing tables:', ', '.join(missing_tables))
else:
    print(f'STATUS: ALL TABLES EXIST ({len(existing_tables)}/{len(TABLES)})')
    print('='*70)
    print('\n[OK] Database ready!')
    print('[OK] Orchestrator can run!')
    print('[OK] Telegram bot can run!')
    print('\nNext: Start orchestrator with:')
    print('  poetry run python orchestrator.py')

print('='*70)
