"""
Run database migration for user machines library.
"""
from agent_factory.core.database_manager import DatabaseManager
import sys

def main():
    db = DatabaseManager()

    # Read migration SQL
    with open('docs/database/migrations/002_add_user_machines.sql', 'r') as f:
        sql = f.read()

    # Split by statement
    statements = []
    current = []
    for line in sql.split('\n'):
        line_stripped = line.strip()
        if line_stripped.startswith('--') or not line_stripped:
            continue
        current.append(line)
        if line_stripped.endswith(';'):
            statements.append('\n'.join(current))
            current = []

    print(f'Executing {len(statements)} SQL statements...\n')

    success_count = 0
    skip_count = 0

    for i, stmt in enumerate(statements, 1):
        stmt_preview = stmt[:80].replace('\n', ' ').strip()
        try:
            db.execute_query(stmt, fetch_mode='none')
            print(f'[{i}/{len(statements)}] OK: {stmt_preview}...')
            success_count += 1
        except Exception as e:
            error_msg = str(e)[:100]
            if 'already exists' in error_msg.lower() or 'duplicate' in error_msg.lower():
                print(f'[{i}/{len(statements)}] SKIP (exists): {stmt_preview}...')
                skip_count += 1
            else:
                print(f'[{i}/{len(statements)}] ERROR: {stmt_preview}...')
                print(f'  Error: {error_msg}')
                return False

    print(f'\nExecuted: {success_count}, Skipped: {skip_count}\n')

    # Verify tables exist
    print('Verifying migration...')
    result = db.execute_query(
        """SELECT COUNT(*) FROM information_schema.tables
           WHERE table_name IN ('user_machines', 'user_machine_history')""",
        fetch_mode='one'
    )
    print(f'  Tables found: {result[0]}/2')

    # Check initial row count
    count = db.execute_query('SELECT COUNT(*) FROM user_machines', fetch_mode='one')
    print(f'  user_machines rows: {count[0]}')

    count = db.execute_query('SELECT COUNT(*) FROM user_machine_history', fetch_mode='one')
    print(f'  user_machine_history rows: {count[0]}')

    print('\n[SUCCESS] Database migration deployed!')
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
