"""
Deploy Agent Factory schema to multiple database providers.

This script deploys the complete schema (knowledge base + memory system)
to Railway, Neon, or Supabase. Useful for setting up backup databases.

Usage:
    # Deploy to specific provider
    poetry run python scripts/deploy_multi_provider_schema.py --provider railway
    poetry run python scripts/deploy_multi_provider_schema.py --provider neon

    # Deploy to all providers
    poetry run python scripts/deploy_multi_provider_schema.py --all

    # Verify schema (check all providers have correct tables)
    poetry run python scripts/deploy_multi_provider_schema.py --verify

    # Dry run (show SQL without executing)
    poetry run python scripts/deploy_multi_provider_schema.py --provider neon --dry-run

Requirements:
    - psycopg[binary] installed (poetry add 'psycopg[binary]')
    - Provider credentials in .env
    - Schema file at docs/supabase_complete_schema.sql

Environment Variables:
    SUPABASE_DB_HOST, SUPABASE_DB_PASSWORD (for Supabase)
    RAILWAY_DB_URL (for Railway)
    NEON_DB_URL (for Neon)
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Dict, List

import psycopg
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


class SchemaDeployer:
    """Deploy database schema to multiple providers."""

    def __init__(self, schema_type: str = "main"):
        """
        Initialize deployer with provider connection strings.

        Args:
            schema_type: Schema to deploy ("main" or "rivet")
        """
        self.providers = {}
        self.schema_type = schema_type

        # Select schema file based on type
        if schema_type == "rivet":
            # RIVET schema (industrial maintenance chatbot)
            # Worktree is sibling to main Agent Factory directory
            main_dir = Path(__file__).parent.parent
            desktop_or_parent = main_dir.parent

            rivet_paths = [
                desktop_or_parent / "agent-factory-rivet-launch" / "rivet" / "config" / "database_schema.sql",
                main_dir / "agent-factory-rivet-launch" / "rivet" / "config" / "database_schema.sql",
                Path.cwd() / "agent-factory-rivet-launch" / "rivet" / "config" / "database_schema.sql"
            ]
            self.schema_file = None
            for path in rivet_paths:
                if path.exists():
                    self.schema_file = path
                    break

            if not self.schema_file:
                raise FileNotFoundError(
                    f"RIVET schema file not found. Tried:\n" +
                    "\n".join(f"  - {p}" for p in rivet_paths)
                )
        else:
            # Main Agent Factory schema (knowledge base + memory)
            # Try multiple paths (docs/ and docs/database/)
            schema_paths = [
                Path(__file__).parent.parent / "docs" / "database" / "supabase_complete_schema.sql",
                Path(__file__).parent.parent / "docs" / "supabase_complete_schema.sql"
            ]
            self.schema_file = None
            for path in schema_paths:
                if path.exists():
                    self.schema_file = path
                    break

            # Validate schema file exists
            if not self.schema_file:
                raise FileNotFoundError(
                    f"Schema file not found. Tried:\n" +
                    "\n".join(f"  - {p}" for p in schema_paths)
                )

        print(f"[OK] Using schema: {self.schema_file}")

        # Initialize provider connections
        self._init_providers()

    def _init_providers(self):
        """Load connection strings for all configured providers."""
        # Supabase
        supabase_host = os.getenv("SUPABASE_DB_HOST")
        supabase_password = os.getenv("SUPABASE_DB_PASSWORD")

        if supabase_host and supabase_password:
            conn_str = f"postgresql://postgres:{supabase_password}@{supabase_host}:5432/postgres"
            self.providers["supabase"] = conn_str
            print(f"[OK] Supabase provider configured")
        else:
            print(f"[SKIP] Supabase credentials incomplete, skipping")

        # Railway
        railway_url = os.getenv("RAILWAY_DB_URL")
        if railway_url and "your_railway_password_here" not in railway_url:
            self.providers["railway"] = railway_url
            print(f"[OK] Railway provider configured")
        else:
            print(f"[SKIP] Railway credentials incomplete, skipping")

        # Neon
        neon_url = os.getenv("NEON_DB_URL")
        if neon_url:
            self.providers["neon"] = neon_url
            print(f"[OK] Neon provider configured")
        else:
            print(f"[SKIP] Neon credentials incomplete, skipping")

        if not self.providers:
            raise ValueError("No database providers configured. Check .env file.")

    def read_schema(self) -> str:
        """
        Read schema SQL from file.

        Returns:
            str: Complete SQL schema
        """
        with open(self.schema_file, 'r', encoding='utf-8') as f:
            return f.read()

    def deploy_schema(self, provider_name: str, dry_run: bool = False) -> bool:
        """
        Deploy schema to specific provider.

        Args:
            provider_name: Provider name (supabase, railway, neon)
            dry_run: If True, only show SQL without executing

        Returns:
            bool: True if successful, False otherwise
        """
        if provider_name not in self.providers:
            print(f"[ERROR] Provider '{provider_name}' not configured")
            return False

        conn_str = self.providers[provider_name]
        schema_sql = self.read_schema()

        if dry_run:
            print(f"\n{'='*80}")
            print(f"DRY RUN - SQL for {provider_name}")
            print(f"{'='*80}")
            print(schema_sql)
            print(f"{'='*80}\n")
            return True

        try:
            print(f"\n{'='*80}")
            print(f"Deploying schema to {provider_name}...")
            print(f"{'='*80}")

            # Connect to database
            with psycopg.connect(conn_str) as conn:
                print(f"[OK] Connected to {provider_name}")

                # Execute schema
                with conn.cursor() as cur:
                    cur.execute(schema_sql)
                    conn.commit()

                print(f"[OK] Schema deployed successfully")

                # Verify tables created
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT table_name
                        FROM information_schema.tables
                        WHERE table_schema = 'public'
                        AND table_type = 'BASE TABLE'
                        ORDER BY table_name;
                    """)
                    tables = [row[0] for row in cur.fetchall()]

                print(f"\n[OK] Tables created ({len(tables)}):")
                for table in tables:
                    print(f"  - {table}")

            print(f"\n[SUCCESS] {provider_name} deployment complete\n")
            return True

        except Exception as e:
            print(f"\n[ERROR] {provider_name} deployment failed: {str(e)}\n")
            return False

    def verify_schema(self, provider_name: str) -> Dict[str, List[str]]:
        """
        Verify schema for specific provider.

        Args:
            provider_name: Provider name

        Returns:
            dict: {table_name: [column_names]}
        """
        if provider_name not in self.providers:
            return {}

        conn_str = self.providers[provider_name]

        try:
            with psycopg.connect(conn_str) as conn:
                with conn.cursor() as cur:
                    # Get all tables
                    cur.execute("""
                        SELECT table_name
                        FROM information_schema.tables
                        WHERE table_schema = 'public'
                        AND table_type = 'BASE TABLE'
                        ORDER BY table_name;
                    """)
                    tables = [row[0] for row in cur.fetchall()]

                    # Get columns for each table
                    schema = {}
                    for table in tables:
                        cur.execute("""
                            SELECT column_name
                            FROM information_schema.columns
                            WHERE table_schema = 'public'
                            AND table_name = %s
                            ORDER BY ordinal_position;
                        """, (table,))
                        columns = [row[0] for row in cur.fetchall()]
                        schema[table] = columns

                    return schema

        except Exception as e:
            print(f"[ERROR] Failed to verify {provider_name}: {str(e)}")
            return {}

    def verify_all_schemas(self):
        """Verify all provider schemas and compare."""
        print(f"\n{'='*80}")
        print("Verifying schemas across all providers")
        print(f"{'='*80}\n")

        schemas = {}
        for provider_name in self.providers:
            schema = self.verify_schema(provider_name)
            schemas[provider_name] = schema

            if schema:
                print(f"[OK] {provider_name}: {len(schema)} tables")
                for table, columns in sorted(schema.items()):
                    print(f"  - {table} ({len(columns)} columns)")
            else:
                print(f"[ERROR] {provider_name}: No schema found")
            print()

        # Compare schemas
        if len(schemas) > 1:
            print(f"\n{'='*80}")
            print("Schema Comparison")
            print(f"{'='*80}\n")

            # Get table names from all providers
            all_tables = set()
            for schema in schemas.values():
                all_tables.update(schema.keys())

            # Check each table
            for table in sorted(all_tables):
                providers_with_table = [
                    name for name, schema in schemas.items()
                    if table in schema
                ]

                if len(providers_with_table) == len(schemas):
                    print(f"[OK] {table}: Present in all providers")

                    # Check if columns match
                    column_sets = [
                        set(schemas[name][table])
                        for name in providers_with_table
                    ]

                    if all(cols == column_sets[0] for cols in column_sets):
                        print(f"  [OK] Columns match ({len(column_sets[0])})")
                    else:
                        print(f"  [WARN] Column mismatch:")
                        for name in providers_with_table:
                            print(f"    {name}: {sorted(schemas[name][table])}")
                else:
                    print(f"[WARN] {table}: Missing from {len(schemas) - len(providers_with_table)} providers")
                    for name in schemas:
                        status = "[OK]" if name in providers_with_table else "[MISSING]"
                        print(f"  {status} {name}")

        print(f"\n{'='*80}\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Deploy schema to database providers")
    parser.add_argument(
        "--provider",
        choices=["supabase", "railway", "neon"],
        help="Deploy to specific provider"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Deploy to all configured providers"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify schemas across all providers"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show SQL without executing"
    )
    parser.add_argument(
        "--rivet",
        action="store_true",
        help="Deploy RIVET schema (industrial maintenance chatbot) instead of main Agent Factory schema"
    )

    args = parser.parse_args()

    # Validate arguments
    if not any([args.provider, args.all, args.verify]):
        parser.error("Specify --provider, --all, or --verify")

    try:
        schema_type = "rivet" if args.rivet else "main"
        deployer = SchemaDeployer(schema_type=schema_type)

        if args.verify:
            # Verify all schemas
            deployer.verify_all_schemas()

        elif args.all:
            # Deploy to all providers
            print(f"\nDeploying {schema_type.upper()} schema to all configured providers...\n")
            success_count = 0
            for provider_name in deployer.providers:
                if deployer.deploy_schema(provider_name, dry_run=args.dry_run):
                    success_count += 1

            print(f"\nDeployment Summary: {success_count}/{len(deployer.providers)} successful")

        else:
            # Deploy to specific provider
            deployer.deploy_schema(args.provider, dry_run=args.dry_run)

    except Exception as e:
        print(f"\n[ERROR] Error: {str(e)}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
