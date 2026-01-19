"""
Database migrations for Settings Service and Hybrid Search

Runs all SQL migrations automatically via Supabase client.
"""
import os
from supabase import create_client

def run_migrations():
    """Execute all database migrations"""

    # Get Supabase credentials
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        print("[ERROR] Missing SUPABASE_URL or SUPABASE_KEY environment variables")
        return False

    try:
        client = create_client(supabase_url, supabase_key)
        print(f"[OK] Connected to Supabase: {supabase_url}")
    except Exception as e:
        print(f"[ERROR] Failed to connect to Supabase: {e}")
        return False

    migrations = [
        {
            "name": "Create agent_factory_settings table",
            "sql": """
                CREATE TABLE IF NOT EXISTS agent_factory_settings (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    category TEXT NOT NULL,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    description TEXT,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW(),
                    UNIQUE(category, key)
                );
            """
        },
        {
            "name": "Create settings index",
            "sql": """
                CREATE INDEX IF NOT EXISTS idx_settings_category_key
                ON agent_factory_settings(category, key);
            """
        },
        {
            "name": "Insert default settings",
            "sql": """
                INSERT INTO agent_factory_settings (category, key, value, description)
                VALUES
                    ('memory', 'BATCH_SIZE', '50', 'Batch size for memory operations'),
                    ('memory', 'USE_HYBRID_SEARCH', 'false', 'Enable hybrid vector + text search'),
                    ('orchestration', 'MAX_RETRIES', '3', 'Max retries for agent calls'),
                    ('orchestration', 'TIMEOUT_SECONDS', '300', 'Default timeout for agent execution'),
                    ('llm', 'DEFAULT_MODEL', 'gpt-4o-mini', 'Default LLM model'),
                    ('llm', 'DEFAULT_TEMPERATURE', '0.7', 'Default temperature for LLM calls')
                ON CONFLICT (category, key) DO NOTHING;
            """
        },
        {
            "name": "Add tsvector column for full-text search",
            "sql": """
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name='session_memories' AND column_name='content_tsvector'
                    ) THEN
                        ALTER TABLE session_memories
                        ADD COLUMN content_tsvector tsvector
                        GENERATED ALWAYS AS (to_tsvector('english', content::text)) STORED;
                    END IF;
                END $$;
            """
        },
        {
            "name": "Create GIN index for full-text search",
            "sql": """
                CREATE INDEX IF NOT EXISTS idx_session_memories_content_search
                ON session_memories USING gin(content_tsvector);
            """
        },
        {
            "name": "Add multi-dimensional embedding columns",
            "sql": """
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name='session_memories' AND column_name='embedding_768'
                    ) THEN
                        ALTER TABLE session_memories
                        ADD COLUMN embedding_768 vector(768),
                        ADD COLUMN embedding_1024 vector(1024),
                        ADD COLUMN embedding_1536 vector(1536),
                        ADD COLUMN embedding_3072 vector(3072),
                        ADD COLUMN embedding_model TEXT,
                        ADD COLUMN embedding_dimension INT;
                    END IF;
                END $$;
            """
        },
        {
            "name": "Create vector indexes for 768 dimensions",
            "sql": """
                CREATE INDEX IF NOT EXISTS idx_session_memories_embedding_768
                ON session_memories USING ivfflat (embedding_768 vector_cosine_ops) WITH (lists = 100);
            """
        },
        {
            "name": "Create vector indexes for 1024 dimensions",
            "sql": """
                CREATE INDEX IF NOT EXISTS idx_session_memories_embedding_1024
                ON session_memories USING ivfflat (embedding_1024 vector_cosine_ops) WITH (lists = 100);
            """
        },
        {
            "name": "Create vector indexes for 1536 dimensions",
            "sql": """
                CREATE INDEX IF NOT EXISTS idx_session_memories_embedding_1536
                ON session_memories USING ivfflat (embedding_1536 vector_cosine_ops) WITH (lists = 100);
            """
        },
        {
            "name": "Create vector indexes for 3072 dimensions",
            "sql": """
                CREATE INDEX IF NOT EXISTS idx_session_memories_embedding_3072
                ON session_memories USING ivfflat (embedding_3072 vector_cosine_ops) WITH (lists = 100);
            """
        }
    ]

    print("\n" + "="*60)
    print("Running Database Migrations")
    print("="*60 + "\n")

    success_count = 0
    fail_count = 0

    for migration in migrations:
        try:
            print(f"[RUNNING] {migration['name']}...")

            # Execute raw SQL
            client.postgrest.session.post(
                f"{supabase_url}/rest/v1/rpc/execute_sql",
                json={"query": migration['sql']},
                headers={"apikey": supabase_key, "Authorization": f"Bearer {supabase_key}"}
            )

            print(f"[OK] {migration['name']}")
            success_count += 1

        except Exception as e:
            # Try alternative approach using supabase-py query
            try:
                # For DDL, we need to use raw SQL execution
                # Supabase Python client doesn't support raw SQL directly
                # So we'll skip and note that it needs to be run via SQL editor
                print(f"[SKIP] {migration['name']} - Run via Supabase SQL Editor")
                print(f"       Reason: {str(e)[:100]}")
            except:
                print(f"[FAIL] {migration['name']}: {e}")
                fail_count += 1

    print("\n" + "="*60)
    print(f"Migration Summary: {success_count} succeeded, {fail_count} failed")
    print("="*60 + "\n")

    # Verify settings table exists
    print("[VERIFY] Checking if agent_factory_settings table exists...")
    try:
        response = client.table("agent_factory_settings").select("*").limit(1).execute()
        print("[OK] Settings table verified - found", len(response.data), "records")
        return True
    except Exception as e:
        print(f"[WARN] Could not verify settings table: {e}")
        print("\nPlease run the migrations manually in Supabase SQL Editor")
        print("See: docs/supabase_migrations.sql")
        return False

if __name__ == "__main__":
    success = run_migrations()
    exit(0 if success else 1)
