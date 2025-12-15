#!/usr/bin/env python3
"""Test VPS KB Factory database connection"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    print("Installing psycopg2...")
    os.system("pip install psycopg2-binary")
    import psycopg2
    from psycopg2.extras import RealDictCursor

print("=" * 50)
print("VPS KB Factory Connection Test")
print("=" * 50)

config = {
    'host': os.getenv('VPS_KB_HOST', '72.60.175.144'),
    'port': int(os.getenv('VPS_KB_PORT', 5432)),
    'user': os.getenv('VPS_KB_USER', 'rivet'),
    'password': os.getenv('VPS_KB_PASSWORD', 'rivet_factory_2025!'),
    'database': os.getenv('VPS_KB_DATABASE', 'rivet'),
}

print(f"\nConnecting to: {config['host']}:{config['port']}/{config['database']}")

try:
    conn = psycopg2.connect(
        host=config['host'],
        port=config['port'],
        user=config['user'],
        password=config['password'],
        dbname=config['database'],
        connect_timeout=15
    )
    print("[OK] Connected to VPS PostgreSQL!")

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        # Count atoms
        cur.execute('SELECT COUNT(*) as count FROM knowledge_atoms')
        count = cur.fetchone()['count']
        print(f"\n[OK] Atoms in database: {count}")

        if count > 0:
            # Get sample atoms
            cur.execute('''
                SELECT atom_id, atom_type, title,
                       LEFT(summary, 100) as summary_preview
                FROM knowledge_atoms
                LIMIT 5
            ''')
            atoms = cur.fetchall()

            print(f"\nSample atoms:")
            for atom in atoms:
                print(f"  [{atom['atom_type']}] {atom['title'][:60]}...")
        else:
            print("\n[!] No atoms yet - VPS worker may still be processing")

    conn.close()
    print("\n" + "=" * 50)
    print("SUCCESS: VPS connection working!")
    print("=" * 50)

except psycopg2.OperationalError as e:
    print(f"\n[ERROR] Connection failed: {e}")
    print("\nTroubleshooting:")
    print("1. Ensure VPS firewall allows port 5432")
    print("2. Check docker-compose exposes postgres port")
    print("3. Verify password matches docker-compose.yml")
    sys.exit(1)

except Exception as e:
    print(f"\n[ERROR] {type(e).__name__}: {e}")
    sys.exit(1)
