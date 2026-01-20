"""
Database adapter for RIVET Pro

Provides a unified interface for accessing RIVET Pro tables and functions
across different PostgreSQL providers (Neon, Supabase, Railway).

Usage:
    >>> from agent_factory.rivet_pro.database import RIVETProDatabase
    >>> db = RIVETProDatabase()  # Uses DATABASE_PROVIDER from .env
    >>> user = db.get_user('user_123')
    >>> db.increment_question_count('user_123')
"""

import os
import json
from typing import Optional, Dict, List, Any
from datetime import datetime

try:
    import psycopg2
    import psycopg2.extras
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False
from dotenv import load_dotenv

load_dotenv()


class RIVETProDatabase:
    """
    Database adapter for RIVET Pro tables and functions.

    Supports multiple PostgreSQL providers with automatic connection management.
    """

    def __init__(self, provider: Optional[str] = None):
        """
        Initialize database connection.

        Args:
            provider: Database provider (neon, supabase, railway). If None, uses DATABASE_PROVIDER from .env
        """
        self.provider = provider or os.getenv("DATABASE_PROVIDER", "neon")
        self.conn = None
        self._connect()

    def _connect(self):
        """Establish database connection based on provider"""
        if not PSYCOPG2_AVAILABLE:
            return

        try:
            if self.provider == "neon":
                self.conn = psycopg2.connect(os.getenv("NEON_DB_URL"))
            elif self.provider == "supabase":
                self.conn = psycopg2.connect(
                    host=os.getenv("SUPABASE_DB_HOST"),
                    port=os.getenv("SUPABASE_DB_PORT", "5432"),
                    database=os.getenv("SUPABASE_DB_NAME", "postgres"),
                    user=os.getenv("SUPABASE_DB_USER", "postgres"),
                    password=os.getenv("SUPABASE_DB_PASSWORD"),
                )
            elif self.provider == "railway":
                self.conn = psycopg2.connect(os.getenv("RAILWAY_DB_URL"))
            else:
                pass

            if self.conn:
                self.conn.autocommit = True
        except Exception:
            pass

    def _execute(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """Execute query and return results as list of dicts triangle"""
        if not self.conn:
            return []
        cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        try:
            cursor.execute(query, params)
            if cursor.description:  # SELECT query
                return [dict(row) for row in cursor.fetchall()]
            return []
        finally:
            cursor.close()

    def _execute_one(self, query: str, params: tuple = None) -> Optional[Dict[str, Any]]:
        """Execute query and return single result as dict"""
        if not self.conn:
            return None
        cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        try:
            cursor.execute(query, params)
            if cursor.description:
                row = cursor.fetchone()
                return dict(row) if row else None
            return None
        finally:
            cursor.close()

    def _call_function(self, function_name: str, **kwargs) -> Any:
        """Call a PostgreSQL function with named parameters"""
        if not self.conn:
            return None
        # Build parameter string
        param_names = list(kwargs.keys())
        param_values = list(kwargs.values())
        param_placeholders = ", ".join([f"{name} := %s" for name in param_names])

        query = f"SELECT {function_name}({param_placeholders})"
        cursor = self.conn.cursor()
        try:
            cursor.execute(query, param_values)
            result = cursor.fetchone()
            return result[0] if result else None
        finally:
            cursor.close()

    # =============================================================================
    # User Subscriptions
    # =============================================================================

    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by user_id"""
        return self._execute_one(
            "SELECT * FROM rivet_users WHERE id = %s",
            (user_id,)
        )

    def get_user_by_telegram_id(self, telegram_user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by Telegram user ID"""
        return self._execute_one(
            "SELECT * FROM rivet_users WHERE telegram_id = %s",
            (telegram_user_id,)
        )

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email address"""
        return self._execute_one(
            "SELECT * FROM rivet_users WHERE email = %s",
            (email,)
        )

    def get_user_by_stripe_customer_id(self, stripe_customer_id: str) -> Optional[Dict[str, Any]]:
        """Get user by Stripe customer ID"""
        return self._execute_one(
            "SELECT * FROM rivet_users WHERE stripe_customer_id = %s",
            (stripe_customer_id,)
        )

    def create_user(
        self,
        email: Optional[str] = None,
        telegram_id: Optional[int] = None,
        telegram_username: Optional[str] = None,
        stripe_customer_id: Optional[str] = None,
        atlas_user_id: Optional[str] = None,
        tier: str = "beta"
    ) -> Dict[str, Any]:
        """Create new user with flexible field population"""
        import uuid
        user_id = str(uuid.uuid4())

        query = """
            INSERT INTO rivet_users
            (id, email, telegram_id, telegram_username, stripe_customer_id, atlas_user_id, tier)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING *
        """
        return self._execute_one(
            query,
            (user_id, email, telegram_id, telegram_username, stripe_customer_id, atlas_user_id, tier)
        )

    def update_user_telegram(
        self,
        user_id: str,
        telegram_id: int,
        telegram_username: Optional[str] = None
    ) -> Dict[str, Any]:
        """Link Telegram account to existing user"""
        return self._execute_one(
            """
            UPDATE rivet_users
            SET telegram_id = %s, telegram_username = %s
            WHERE id = %s
            RETURNING *
            """,
            (telegram_id, telegram_username, user_id)
        )

    def update_user_tier(self, user_id: str, tier: str) -> Dict[str, Any]:
        """Update user subscription tier"""
        return self._execute_one(
            "UPDATE rivet_users SET tier = %s WHERE id = %s RETURNING *",
            (tier, user_id)
        )

    def get_user_limits(self, user_id: str) -> Dict[str, Any]:
        """Get user limits using helper function"""
        result = self._call_function("get_user_limits", p_user_id=user_id)
        return json.loads(result) if result else {}

    def increment_question_count(self, user_id: str) -> Dict[str, Any]:
        """Increment user's daily question count"""
        result = self._call_function("increment_question_count", p_user_id=user_id)
        return json.loads(result) if result else {}

    # =============================================================================
    # Troubleshooting Sessions
    # =============================================================================

    def create_session(self, user_id: str, issue_description: str, **kwargs) -> Dict[str, Any]:
        """Create new troubleshooting session"""
        fields = ["user_id", "issue_description"]
        values = [user_id, issue_description]

        for key, value in kwargs.items():
            fields.append(key)
            values.append(value)

        placeholders = ", ".join(["%s"] * len(values))
        field_names = ", ".join(fields)

        query = f"""
            INSERT INTO troubleshooting_sessions ({field_names})
            VALUES ({placeholders})
            RETURNING *
        """
        return self._execute_one(query, tuple(values))

    def get_user_sessions(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get user's recent troubleshooting sessions"""
        return self._execute(
            """
            SELECT * FROM troubleshooting_sessions
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT %s
            """,
            (user_id, limit)
        )

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get troubleshooting session by ID"""
        return self._execute_one(
            "SELECT * FROM troubleshooting_sessions WHERE id = %s",
            (session_id,)
        )

    def update_session(self, session_id: str, **kwargs) -> Dict[str, Any]:
        """Update troubleshooting session"""
        set_clauses = [f"{key} = %s" for key in kwargs.keys()]
        values = list(kwargs.values())
        values.append(session_id)

        query = f"""
            UPDATE troubleshooting_sessions
            SET {", ".join(set_clauses)}
            WHERE id = %s
            RETURNING *
        """
        return self._execute_one(query, tuple(values))

    # =============================================================================
    # Expert Profiles & Bookings
    # =============================================================================

    def get_available_experts(self, specialty: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get available expert technicians"""
        result = self._call_function(
            "get_available_experts",
            p_specialty=specialty
        )
        return json.loads(result) if result else []

    def create_booking(self, user_id: str, expert_id: str, **kwargs) -> Dict[str, Any]:
        """Create new expert booking"""
        fields = ["user_id", "expert_id"]
        values = [user_id, expert_id]

        for key, value in kwargs.items():
            fields.append(key)
            values.append(value)

        placeholders = ", ".join(["%s"] * len(values))
        field_names = ", ".join(fields)

        query = f"""
            INSERT INTO expert_bookings ({field_names})
            VALUES ({placeholders})
            RETURNING *
        """
        return self._execute_one(query, tuple(values))

    # =============================================================================
    # Conversion Events
    # =============================================================================

    def track_conversion_event(
        self,
        user_id: str,
        event_type: str,
        converted: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """Track conversion funnel event"""
        fields = ["user_id", "event_type", "converted"]
        values = [user_id, event_type, converted]

        for key, value in kwargs.items():
            fields.append(key)
            values.append(value)

        placeholders = ", ".join(["%s"] * len(values))
        field_names = ", ".join(fields)

        query = f"""
            INSERT INTO conversion_events ({field_names})
            VALUES ({placeholders})
            RETURNING *
        """
        return self._execute_one(query, tuple(values))

    # =============================================================================
    # Analytics
    # =============================================================================

    def get_metrics(self, days: int = 30) -> Dict[str, Any]:
        """Get RIVET Pro platform metrics"""
        result = self._call_function("get_rivet_pro_metrics", p_days=days)
        return json.loads(result) if result else {}

    # =============================================================================
    # Machines (TAB 1: Backend Infrastructure)
    # =============================================================================

    def create_machine(
        self,
        user_id: str,
        name: str,
        description: Optional[str] = None,
        location: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create or update machine (upsert on conflict)"""
        return self._execute_one(
            """
            INSERT INTO machines (user_id, name, description, location)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (user_id, name) DO UPDATE
            SET description = COALESCE(%s, machines.description),
                location = COALESCE(%s, machines.location),
                updated_at = NOW()
            RETURNING *
            """,
            (user_id, name, description, location, description, location)
        )

    def get_user_machines(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all machines for a user"""
        return self._execute(
            "SELECT * FROM machines WHERE user_id = %s ORDER BY name",
            (user_id,)
        )

    def get_machine_by_name(self, user_id: str, name: str) -> Optional[Dict[str, Any]]:
        """Get machine by name (case-insensitive search)"""
        return self._execute_one(
            "SELECT * FROM machines WHERE user_id = %s AND name ILIKE %s",
            (user_id, f"%{name}%")
        )

    def get_machine_by_id(self, machine_id: str) -> Optional[Dict[str, Any]]:
        """Get machine by ID"""
        return self._execute_one(
            "SELECT * FROM machines WHERE id = %s",
            (machine_id,)
        )

    # =============================================================================
    # Prints (Electrical Prints/Schematics)
    # =============================================================================

    def create_print(
        self,
        machine_id: str,
        user_id: str,
        name: str,
        file_path: str,
        print_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create new print record"""
        return self._execute_one(
            """
            INSERT INTO prints (machine_id, user_id, name, file_path, print_type)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING *
            """,
            (machine_id, user_id, name, file_path, print_type)
        )

    def update_print_vectorized(
        self,
        print_id: str,
        chunk_count: int,
        collection_name: str
    ) -> bool:
        """Mark print as vectorized with metadata"""
        self._execute_one(
            """
            UPDATE prints
            SET vectorized = TRUE, chunk_count = %s, collection_name = %s, vectorized_at = NOW()
            WHERE id = %s
            """,
            (chunk_count, collection_name, print_id)
        )
        return True

    def get_machine_prints(self, machine_id: str) -> List[Dict[str, Any]]:
        """Get all prints for a machine"""
        return self._execute(
            "SELECT * FROM prints WHERE machine_id = %s ORDER BY uploaded_at DESC",
            (machine_id,)
        )

    def get_user_prints(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all prints for a user (across all machines)"""
        return self._execute(
            """
            SELECT p.*, m.name as machine_name
            FROM prints p
            JOIN machines m ON p.machine_id = m.id
            WHERE p.user_id = %s
            ORDER BY p.uploaded_at DESC
            """,
            (user_id,)
        )

    # =============================================================================
    # Equipment Manuals (OEM Documentation)
    # =============================================================================

    def create_manual(
        self,
        title: str,
        manufacturer: str,
        component_family: str,
        file_path: str,
        document_type: str = 'user_manual'
    ) -> Dict[str, Any]:
        """Create new equipment manual record"""
        return self._execute_one(
            """
            INSERT INTO equipment_manuals
            (title, manufacturer, component_family, file_path, document_type)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING *
            """,
            (title, manufacturer, component_family, file_path, document_type)
        )

    def update_manual_indexed(
        self,
        manual_id: str,
        collection_name: str,
        page_count: int
    ) -> bool:
        """Mark manual as indexed with metadata"""
        self._execute_one(
            """
            UPDATE equipment_manuals
            SET indexed = TRUE, collection_name = %s, page_count = %s, indexed_at = NOW()
            WHERE id = %s
            """,
            (collection_name, page_count, manual_id)
        )
        return True

    def search_manuals(
        self,
        manufacturer: Optional[str] = None,
        component_family: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search indexed manuals by manufacturer and/or component family"""
        conditions = ["indexed = TRUE"]
        params = []

        if manufacturer:
            params.append(f"%{manufacturer}%")
            conditions.append(f"manufacturer ILIKE ${len(params)}")
        if component_family:
            params.append(f"%{component_family}%")
            conditions.append(f"component_family ILIKE ${len(params)}")

        query = f"SELECT * FROM equipment_manuals WHERE {' AND '.join(conditions)}"

        # Convert $1, $2 placeholders to %s for psycopg2
        query = query.replace("$1", "%s").replace("$2", "%s")

        return self._execute(query, tuple(params))

    def get_all_manuals(self) -> List[Dict[str, Any]]:
        """Get all indexed manuals"""
        return self._execute(
            "SELECT * FROM equipment_manuals WHERE indexed = TRUE ORDER BY manufacturer, title"
        )

    # =============================================================================
    # Print Chat History (Q&A Logs)
    # =============================================================================

    def save_chat(
        self,
        user_id: str,
        machine_id: str,
        question: str,
        answer: str,
        sources: Optional[List[str]] = None,
        tokens_used: Optional[int] = None
    ) -> Dict[str, Any]:
        """Save chat interaction"""
        return self._execute_one(
            """
            INSERT INTO print_chat_history
            (user_id, machine_id, question, answer, sources, tokens_used)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING *
            """,
            (user_id, machine_id, question, answer, sources or [], tokens_used)
        )

    def get_chat_history(
        self,
        user_id: str,
        machine_id: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Get recent chat history (reversed chronological order)"""
        results = self._execute(
            """
            SELECT question, answer, sources, created_at
            FROM print_chat_history
            WHERE user_id = %s AND machine_id = %s
            ORDER BY created_at DESC
            LIMIT %s
            """,
            (user_id, machine_id, limit)
        )
        # Reverse to get chronological order
        return list(reversed(results))

    # =============================================================================
    # Context Extractions (Analytics)
    # =============================================================================

    def log_context_extraction(
        self,
        user_id: str,
        telegram_id: int,
        message: str,
        context: dict,
        confidence: float,
        manuals_found: int
    ) -> Dict[str, Any]:
        """Log context extraction for analytics"""
        return self._execute_one(
            """
            INSERT INTO context_extractions
            (user_id, telegram_id, message_text, extracted_context, confidence,
             component_name, component_family, manufacturer, fault_code,
             issue_type, manuals_found)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *
            """,
            (
                user_id, telegram_id, message, json.dumps(context), confidence,
                context.get('component_name'),
                context.get('component_family'),
                context.get('manufacturer'),
                context.get('fault_code'),
                context.get('issue_type'),
                manuals_found
            )
        )

    # =============================================================================
    # Manual Gaps (Track Missing Documentation)
    # =============================================================================

    def log_manual_gap(
        self,
        manufacturer: str,
        component_family: str,
        model_pattern: Optional[str] = None
    ) -> Dict[str, Any]:
        """Log missing manual (upsert to increment request count)"""
        return self._execute_one(
            """
            INSERT INTO manual_gaps (manufacturer, component_family, model_pattern)
            VALUES (%s, %s, %s)
            ON CONFLICT (manufacturer, component_family)
            DO UPDATE SET
                request_count = manual_gaps.request_count + 1,
                last_requested = NOW(),
                model_pattern = COALESCE(%s, manual_gaps.model_pattern)
            RETURNING *
            """,
            (manufacturer, component_family, model_pattern or "", model_pattern)
        )

    def get_top_manual_gaps(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most requested missing manuals"""
        return self._execute(
            """
            SELECT * FROM manual_gaps
            WHERE resolved = FALSE
            ORDER BY request_count DESC
            LIMIT %s
            """,
            (limit,)
        )

    def resolve_manual_gap(self, gap_id: str, manual_id: str) -> bool:
        """Mark manual gap as resolved"""
        self._execute_one(
            """
            UPDATE manual_gaps
            SET resolved = TRUE, resolved_manual_id = %s
            WHERE id = %s
            """,
            (manual_id, gap_id)
        )
        return True

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
