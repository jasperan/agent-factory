# TAB 1: BACKEND + KNOWLEDGE INFRASTRUCTURE
## Phase 1 MVP + Atlas Vision Foundation

You are Tab 1 in a 3-tab sprint building Rivet - an AI-powered CMMS that learns from every interaction.

## THE VISION (Read First)
```
Every troubleshooting session makes the system smarter:

Tech asks question → Context extracted → KB searched → Response generated
                                                              ↓
                                           Expert approves → Atoms extracted
                                                              ↓
                                           Next tech gets instant answer
                                           (no generation needed)

This sprint builds the foundation. Phase 2 adds the learning loop.
```

## AUTONOMOUS MODE SETTINGS
- Auto-accept all file edits
- Auto-accept bash commands except: rm -rf, sudo, DROP, DELETE
- Commit after each completed phase

## YOUR IDENTITY
- Workstream: Backend + Knowledge Infrastructure
- Branch: backend-complete
- Focus: Database, ChromaDB, Manual Library, Equipment Taxonomy

## FIRST ACTIONS
```bash
cd "C:\Users\hharp\OneDrive\Desktop\Agent Factory"
git checkout -b backend-complete
git push -u origin backend-complete
```

---

# PHASE 1: DATABASE SCHEMA (Day 1)

## Task 1.1: Complete Migration
Create `migrations/003_complete_schema.sql`:

```sql
-- ═══════════════════════════════════════════════════════════════════════════
-- RIVET CMMS DATABASE SCHEMA
-- Phase 1: MVP Tables (Build Now)
-- Phase 2: Atlas Extensions (Commented, add later)
-- ═══════════════════════════════════════════════════════════════════════════

-- ─────────────────────────────────────────────────────────────────────────────
-- PHASE 1: CORE TABLES (BUILD NOW)
-- ─────────────────────────────────────────────────────────────────────────────

-- Machines: User's equipment (Phase 1)
CREATE TABLE IF NOT EXISTS machines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES rivet_users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    location VARCHAR(255),
    -- Phase 2: Will add subsystem support
    -- parent_machine_id UUID REFERENCES machines(id),
    -- machine_type VARCHAR(100),
    -- manufacturer VARCHAR(255),
    -- model_number VARCHAR(255),
    -- serial_number VARCHAR(255),
    -- installation_date DATE,
    -- operating_hours INT DEFAULT 0,
    -- critical_for_safety BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, name)
);

-- Prints: User-uploaded electrical prints (Phase 1)
CREATE TABLE IF NOT EXISTS prints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    machine_id UUID REFERENCES machines(id) ON DELETE CASCADE,
    user_id UUID REFERENCES rivet_users(id),
    name VARCHAR(255) NOT NULL,
    file_path VARCHAR(512),
    print_type VARCHAR(100), -- 'wiring', 'schematic', 'mechanical', 'p&id'
    description TEXT,
    page_count INTEGER DEFAULT 1,
    chunk_count INTEGER DEFAULT 0,
    vectorized BOOLEAN DEFAULT FALSE,
    collection_name VARCHAR(255),
    uploaded_at TIMESTAMP DEFAULT NOW(),
    vectorized_at TIMESTAMP
);

-- Equipment Manuals: OEM documentation library (Phase 1)
CREATE TABLE IF NOT EXISTS equipment_manuals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    manufacturer VARCHAR(255),
    component_family VARCHAR(255), -- 'VFD', 'PLC', 'Motor', etc.
    model_patterns TEXT[], -- Regex patterns for matching
    document_type VARCHAR(100) DEFAULT 'user_manual',
    file_path VARCHAR(512),
    page_count INTEGER,
    indexed BOOLEAN DEFAULT FALSE,
    collection_name VARCHAR(255),
    -- Phase 2: Link to equipment hierarchy
    -- equipment_id UUID,
    -- subsystem_id UUID,
    source VARCHAR(100) DEFAULT 'user_upload', -- 'user_upload', 'vendor', 'ai_scraped'
    is_verified BOOLEAN DEFAULT FALSE,
    uploaded_at TIMESTAMP DEFAULT NOW(),
    indexed_at TIMESTAMP
);

-- Print Chat History: Q&A logs (Phase 1)
CREATE TABLE IF NOT EXISTS print_chat_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES rivet_users(id),
    machine_id UUID REFERENCES machines(id),
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    sources TEXT[], -- Array of print/manual IDs cited
    tokens_used INTEGER,
    -- Phase 2: Track for atom extraction
    -- atoms_extracted BOOLEAN DEFAULT FALSE,
    -- helpful_rating INTEGER, -- 1-5 stars
    created_at TIMESTAMP DEFAULT NOW()
);

-- Context Extractions: Log every extraction for analytics (Phase 1)
CREATE TABLE IF NOT EXISTS context_extractions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES rivet_users(id),
    telegram_id BIGINT,
    message_text TEXT,
    extracted_context JSONB, -- Full context object
    confidence FLOAT,
    component_name VARCHAR(255),
    component_family VARCHAR(255),
    manufacturer VARCHAR(255),
    fault_code VARCHAR(50),
    issue_type VARCHAR(50),
    manuals_found INTEGER DEFAULT 0,
    -- Phase 2: Link to research job
    -- research_job_id UUID,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Manual Gaps: Track missing documentation (Phase 1)
CREATE TABLE IF NOT EXISTS manual_gaps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    manufacturer VARCHAR(255),
    component_family VARCHAR(255),
    model_pattern VARCHAR(255),
    request_count INTEGER DEFAULT 1,
    first_requested TIMESTAMP DEFAULT NOW(),
    last_requested TIMESTAMP DEFAULT NOW(),
    resolved BOOLEAN DEFAULT FALSE,
    resolved_manual_id UUID REFERENCES equipment_manuals(id),
    UNIQUE(manufacturer, component_family)
);

-- ─────────────────────────────────────────────────────────────────────────────
-- PHASE 2: ATLAS EXTENSIONS (ADD AFTER MVP)
-- Uncomment and run as migrations/004_phase2_tables.sql
-- ─────────────────────────────────────────────────────────────────────────────

/*
-- Equipment Subsystems: Hierarchical equipment structure
CREATE TABLE equipment_subsystems (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    parent_machine_id UUID REFERENCES machines(id) ON DELETE CASCADE,
    parent_subsystem_id UUID REFERENCES equipment_subsystems(id), -- For nested
    subsystem_name VARCHAR(255) NOT NULL,
    subsystem_type VARCHAR(100), -- 'brake', 'electrical', 'mechanical', 'hydraulic'
    description TEXT,
    manufacturer VARCHAR(255),
    model_number VARCHAR(255),
    serial_number VARCHAR(255),
    installation_date DATE,
    expected_lifespan_hours INT,
    current_operating_hours INT DEFAULT 0,
    critical_for_safety BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Equipment Components: Parts within subsystems
CREATE TABLE equipment_components (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subsystem_id UUID REFERENCES equipment_subsystems(id) ON DELETE CASCADE,
    component_name VARCHAR(255) NOT NULL,
    component_type VARCHAR(100), -- 'mechanical', 'electrical', 'sensor'
    manufacturer VARCHAR(255),
    part_number VARCHAR(255),
    supplier_link VARCHAR(512),
    typical_failure_mode VARCHAR(255),
    mtbf_hours INT, -- Mean Time Between Failures
    replacement_cost_usd DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Knowledge Atoms: Granular facts extracted from guides
CREATE TABLE knowledge_atoms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    equipment_type VARCHAR(100), -- 'brake', 'vfd', 'plc'
    atom_title VARCHAR(255) NOT NULL,
    atom_content TEXT NOT NULL, -- Markdown atomic fact
    atom_category VARCHAR(50), -- 'symptom', 'diagnosis', 'repair', 'prevention'
    confidence_score FLOAT DEFAULT 0.5,
    source VARCHAR(100), -- 'manual', 'technician', 'ai_generated', 'expert_verified'
    source_reference_id UUID, -- Link to original resource
    verified_by_expert BOOLEAN DEFAULT false,
    verified_by_user_id UUID,
    usage_count INT DEFAULT 0,
    feedback_score FLOAT DEFAULT 0.0,
    embedding_vector vector(1536), -- For semantic search
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- AI Research Jobs: Track agent decisions
CREATE TABLE ai_research_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    context_extraction_id UUID REFERENCES context_extractions(id),
    job_type VARCHAR(50), -- 'resource_search', 'troubleshooting_generation'
    equipment_id UUID,
    subsystem_id UUID,
    issue_description TEXT,
    search_queries_used TEXT[], -- What queries agent constructed
    resources_found UUID[], -- Array of resource IDs
    resources_relevance_scores FLOAT[], -- Parallel array of scores
    agent_reasoning TEXT, -- Why these resources were chosen
    fallback_triggered BOOLEAN DEFAULT false,
    generated_content_id UUID,
    job_status VARCHAR(50) DEFAULT 'complete',
    latency_ms INTEGER,
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    error_message TEXT
);

-- AI Generated Resources: Content awaiting expert review
CREATE TABLE ai_generated_resources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    research_job_id UUID REFERENCES ai_research_jobs(id),
    equipment_id UUID,
    subsystem_id UUID,
    content_type VARCHAR(50), -- 'troubleshooting_guide', 'diagnostic_flowchart'
    generated_content TEXT, -- Markdown
    generation_model VARCHAR(100),
    kb_atoms_used UUID[], -- Which atoms informed this
    review_status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'approved', 'rejected'
    reviewed_by_user_id UUID,
    review_feedback TEXT,
    atoms_extracted BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW(),
    reviewed_at TIMESTAMP
);

-- Resource Feedback: Tech ratings
CREATE TABLE resource_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES rivet_users(id),
    resource_type VARCHAR(50), -- 'manual', 'print', 'generated'
    resource_id UUID,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    feedback_text TEXT,
    was_helpful BOOLEAN,
    created_at TIMESTAMP DEFAULT NOW()
);
*/

-- ─────────────────────────────────────────────────────────────────────────────
-- INDEXES
-- ─────────────────────────────────────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_machines_user ON machines(user_id);
CREATE INDEX IF NOT EXISTS idx_prints_machine ON prints(machine_id);
CREATE INDEX IF NOT EXISTS idx_prints_user ON prints(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_user ON print_chat_history(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_machine ON print_chat_history(machine_id);
CREATE INDEX IF NOT EXISTS idx_manuals_manufacturer ON equipment_manuals(manufacturer);
CREATE INDEX IF NOT EXISTS idx_manuals_family ON equipment_manuals(component_family);
CREATE INDEX IF NOT EXISTS idx_context_user ON context_extractions(user_id);
CREATE INDEX IF NOT EXISTS idx_context_component ON context_extractions(component_family);
CREATE INDEX IF NOT EXISTS idx_gaps_manufacturer ON manual_gaps(manufacturer);
CREATE INDEX IF NOT EXISTS idx_gaps_count ON manual_gaps(request_count DESC);
```

## Task 1.2: Run Migration
```bash
psql "$NEON_DB_URL" -f migrations/003_complete_schema.sql
```

## Task 1.3: Database Manager
Update `agent_factory/rivet_pro/database.py` with all CRUD methods:

```python
"""
Rivet Database Manager
Phase 1: Core CRUD operations
Phase 2 Prep: Methods stubbed for atoms, research jobs
"""
import asyncpg
import json
import os
from typing import List, Optional, Dict
from datetime import datetime

class DatabaseManager:
    """Unified database manager for Rivet CMMS."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.pool = None
        return cls._instance
    
    async def connect(self):
        if not self.pool:
            self.pool = await asyncpg.create_pool(os.getenv("NEON_DB_URL"))
    
    async def close(self):
        if self.pool:
            await self.pool.close()
    
    # ═══════════════════════════════════════════════════════════════════════
    # MACHINE METHODS
    # ═══════════════════════════════════════════════════════════════════════
    
    async def create_machine(self, user_id: str, name: str, 
                            description: str = None, location: str = None) -> dict:
        query = """
            INSERT INTO machines (user_id, name, description, location)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (user_id, name) DO UPDATE 
            SET description = COALESCE($3, machines.description),
                location = COALESCE($4, machines.location),
                updated_at = NOW()
            RETURNING *
        """
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, user_id, name, description, location)
            return dict(row) if row else None
    
    async def get_user_machines(self, user_id: str) -> List[dict]:
        query = "SELECT * FROM machines WHERE user_id = $1 ORDER BY name"
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, user_id)
            return [dict(r) for r in rows]
    
    async def get_machine_by_name(self, user_id: str, name: str) -> Optional[dict]:
        query = "SELECT * FROM machines WHERE user_id = $1 AND name ILIKE $2"
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, user_id, f"%{name}%")
            return dict(row) if row else None
    
    async def get_machine_by_id(self, machine_id: str) -> Optional[dict]:
        query = "SELECT * FROM machines WHERE id = $1"
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, machine_id)
            return dict(row) if row else None
    
    # ═══════════════════════════════════════════════════════════════════════
    # PRINT METHODS
    # ═══════════════════════════════════════════════════════════════════════
    
    async def create_print(self, machine_id: str, user_id: str, name: str,
                          file_path: str, print_type: str = None) -> dict:
        query = """
            INSERT INTO prints (machine_id, user_id, name, file_path, print_type)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING *
        """
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, machine_id, user_id, name, file_path, print_type)
            return dict(row) if row else None
    
    async def update_print_vectorized(self, print_id: str, chunk_count: int, 
                                      collection_name: str) -> bool:
        query = """
            UPDATE prints 
            SET vectorized = TRUE, chunk_count = $2, collection_name = $3, vectorized_at = NOW()
            WHERE id = $1
        """
        async with self.pool.acquire() as conn:
            await conn.execute(query, print_id, chunk_count, collection_name)
            return True
    
    async def get_machine_prints(self, machine_id: str) -> List[dict]:
        query = "SELECT * FROM prints WHERE machine_id = $1 ORDER BY uploaded_at DESC"
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, machine_id)
            return [dict(r) for r in rows]
    
    async def get_user_prints(self, user_id: str) -> List[dict]:
        query = """
            SELECT p.*, m.name as machine_name 
            FROM prints p
            JOIN machines m ON p.machine_id = m.id
            WHERE p.user_id = $1 
            ORDER BY p.uploaded_at DESC
        """
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, user_id)
            return [dict(r) for r in rows]
    
    # ═══════════════════════════════════════════════════════════════════════
    # MANUAL METHODS
    # ═══════════════════════════════════════════════════════════════════════
    
    async def create_manual(self, title: str, manufacturer: str, 
                           component_family: str, file_path: str,
                           document_type: str = 'user_manual') -> dict:
        query = """
            INSERT INTO equipment_manuals 
            (title, manufacturer, component_family, file_path, document_type)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING *
        """
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, title, manufacturer, 
                                      component_family, file_path, document_type)
            return dict(row) if row else None
    
    async def update_manual_indexed(self, manual_id: str, collection_name: str, 
                                    page_count: int) -> bool:
        query = """
            UPDATE equipment_manuals 
            SET indexed = TRUE, collection_name = $2, page_count = $3, indexed_at = NOW()
            WHERE id = $1
        """
        async with self.pool.acquire() as conn:
            await conn.execute(query, manual_id, collection_name, page_count)
            return True
    
    async def search_manuals(self, manufacturer: str = None, 
                            component_family: str = None) -> List[dict]:
        conditions = ["indexed = TRUE"]
        params = []
        
        if manufacturer:
            params.append(f"%{manufacturer}%")
            conditions.append(f"manufacturer ILIKE ${len(params)}")
        if component_family:
            params.append(f"%{component_family}%")
            conditions.append(f"component_family ILIKE ${len(params)}")
        
        query = f"SELECT * FROM equipment_manuals WHERE {' AND '.join(conditions)}"
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            return [dict(r) for r in rows]
    
    async def get_all_manuals(self) -> List[dict]:
        query = "SELECT * FROM equipment_manuals WHERE indexed = TRUE ORDER BY manufacturer, title"
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query)
            return [dict(r) for r in rows]
    
    # ═══════════════════════════════════════════════════════════════════════
    # CHAT HISTORY
    # ═══════════════════════════════════════════════════════════════════════
    
    async def save_chat(self, user_id: str, machine_id: str, question: str,
                       answer: str, sources: List[str] = None, 
                       tokens_used: int = None) -> dict:
        query = """
            INSERT INTO print_chat_history 
            (user_id, machine_id, question, answer, sources, tokens_used)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING *
        """
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, user_id, machine_id, question,
                                      answer, sources or [], tokens_used)
            return dict(row) if row else None
    
    async def get_chat_history(self, user_id: str, machine_id: str, 
                              limit: int = 5) -> List[dict]:
        query = """
            SELECT question, answer, sources, created_at 
            FROM print_chat_history 
            WHERE user_id = $1 AND machine_id = $2
            ORDER BY created_at DESC
            LIMIT $3
        """
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, user_id, machine_id, limit)
            return [dict(r) for r in reversed(rows)]
    
    # ═══════════════════════════════════════════════════════════════════════
    # CONTEXT EXTRACTION LOGGING
    # ═══════════════════════════════════════════════════════════════════════
    
    async def log_context_extraction(self, user_id: str, telegram_id: int,
                                     message: str, context: dict,
                                     confidence: float, manuals_found: int) -> dict:
        query = """
            INSERT INTO context_extractions 
            (user_id, telegram_id, message_text, extracted_context, confidence,
             component_name, component_family, manufacturer, fault_code, 
             issue_type, manuals_found)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            RETURNING *
        """
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                query, user_id, telegram_id, message, json.dumps(context),
                confidence, context.get('component_name'),
                context.get('component_family'), context.get('manufacturer'),
                context.get('fault_code'), context.get('issue_type'),
                manuals_found
            )
            return dict(row) if row else None
    
    # ═══════════════════════════════════════════════════════════════════════
    # MANUAL GAPS
    # ═══════════════════════════════════════════════════════════════════════
    
    async def log_manual_gap(self, manufacturer: str, component_family: str,
                            model_pattern: str = None) -> dict:
        query = """
            INSERT INTO manual_gaps (manufacturer, component_family, model_pattern)
            VALUES ($1, $2, $3)
            ON CONFLICT (manufacturer, component_family) 
            DO UPDATE SET 
                request_count = manual_gaps.request_count + 1,
                last_requested = NOW(),
                model_pattern = COALESCE($3, manual_gaps.model_pattern)
            RETURNING *
        """
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, manufacturer, component_family, 
                                      model_pattern or "")
            return dict(row) if row else None
    
    async def get_top_manual_gaps(self, limit: int = 10) -> List[dict]:
        query = """
            SELECT * FROM manual_gaps 
            WHERE resolved = FALSE
            ORDER BY request_count DESC
            LIMIT $1
        """
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, limit)
            return [dict(r) for r in rows]
    
    async def resolve_manual_gap(self, gap_id: str, manual_id: str) -> bool:
        query = """
            UPDATE manual_gaps 
            SET resolved = TRUE, resolved_manual_id = $2
            WHERE id = $1
        """
        async with self.pool.acquire() as conn:
            await conn.execute(query, gap_id, manual_id)
            return True
    
    # ═══════════════════════════════════════════════════════════════════════
    # PHASE 2 STUBS (Implement after MVP)
    # ═══════════════════════════════════════════════════════════════════════
    
    async def create_knowledge_atom(self, equipment_type: str, title: str,
                                    content: str, category: str,
                                    source: str, confidence: float = 0.5) -> dict:
        """Phase 2: Create atomic knowledge fact."""
        # TODO: Implement when knowledge_atoms table exists
        raise NotImplementedError("Phase 2 feature")
    
    async def search_atoms(self, equipment_type: str, query: str) -> List[dict]:
        """Phase 2: Search knowledge atoms."""
        raise NotImplementedError("Phase 2 feature")
    
    async def log_research_job(self, context_id: str, job_type: str,
                               resources_found: List[str], 
                               fallback_triggered: bool) -> dict:
        """Phase 2: Log AI research job for analytics."""
        raise NotImplementedError("Phase 2 feature")
    
    async def save_generated_resource(self, research_job_id: str,
                                      content: str, atoms_used: List[str]) -> dict:
        """Phase 2: Save AI-generated content for review."""
        raise NotImplementedError("Phase 2 feature")
    
    async def approve_generated_resource(self, resource_id: str, 
                                         reviewer_id: str) -> bool:
        """Phase 2: Expert approves generated content."""
        raise NotImplementedError("Phase 2 feature")
```

**COMMIT:**
```bash
git add -A && git commit -m "backend: database schema + manager" && git push
```

---

# PHASE 2: CHROMADB + VECTOR STORE (Day 2)

## Task 2.1: Install Dependencies
```bash
pip install chromadb pdfplumber sentence-transformers
```

## Task 2.2: Create Knowledge Module
```bash
mkdir -p agent_factory/knowledge
touch agent_factory/knowledge/__init__.py
```

## Task 2.3: Vector Store
Create `agent_factory/knowledge/vector_store.py`:

```python
"""
ChromaDB Vector Store Manager
Phase 1: Prints + Manuals collections
Phase 2 Prep: Ready for knowledge atoms collection
"""
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import os
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class VectorStore:
    """
    Unified ChromaDB manager for all Rivet knowledge.
    
    Collections:
    - equipment_manuals: OEM documentation
    - user_{id}_machine_{id}: User's prints per machine
    - knowledge_atoms: (Phase 2) Granular facts
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.persist_dir = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
        
        self.client = chromadb.PersistentClient(
            path=self.persist_dir,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Use lightweight embedding model
        self.embedder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        
        # Main collections
        self.manuals_collection = self.client.get_or_create_collection(
            name="equipment_manuals",
            metadata={"description": "OEM equipment manuals and documentation"}
        )
        
        # Phase 2: Knowledge atoms collection
        # self.atoms_collection = self.client.get_or_create_collection(
        #     name="knowledge_atoms",
        #     metadata={"description": "Granular knowledge facts"}
        # )
        
        self._initialized = True
        logger.info(f"VectorStore initialized at {self.persist_dir}")
    
    def get_user_print_collection(self, user_id: str, machine_id: str):
        """Get or create collection for user's machine prints."""
        # Use short IDs for collection name (ChromaDB limit)
        name = f"user_{user_id[:8]}_machine_{machine_id[:8]}"
        return self.client.get_or_create_collection(
            name=name,
            metadata={"user_id": user_id, "machine_id": machine_id}
        )
    
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for single text."""
        return self.embedder.encode(text).tolist()
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        return self.embedder.encode(texts).tolist()
    
    def add_documents(self, collection, documents: List[str], 
                     metadatas: List[dict], ids: List[str]) -> int:
        """Add documents to collection with embeddings."""
        embeddings = self.embed_texts(documents)
        
        collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
        
        logger.info(f"Added {len(documents)} documents to {collection.name}")
        return len(documents)
    
    def search(self, collection, query: str, top_k: int = 5,
              where: dict = None) -> List[dict]:
        """Search collection for relevant documents."""
        query_embedding = self.embed_text(query)
        
        kwargs = {
            "query_embeddings": [query_embedding],
            "n_results": top_k,
            "include": ["documents", "metadatas", "distances"]
        }
        if where:
            kwargs["where"] = where
        
        results = collection.query(**kwargs)
        
        formatted = []
        for i, doc in enumerate(results["documents"][0]):
            formatted.append({
                "text": doc,
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i],
                "score": 1 / (1 + results["distances"][0][i])
            })
        
        return formatted
    
    def search_manuals(self, query: str, top_k: int = 5,
                      manufacturer: str = None) -> List[dict]:
        """Search OEM manuals collection."""
        where = None
        if manufacturer:
            where = {"manufacturer": {"$eq": manufacturer}}
        
        return self.search(self.manuals_collection, query, top_k, where)
    
    def search_prints(self, user_id: str, machine_id: str, 
                     query: str, top_k: int = 5) -> List[dict]:
        """Search user's print collection."""
        collection = self.get_user_print_collection(user_id, machine_id)
        return self.search(collection, query, top_k)
    
    def delete_collection(self, name: str) -> bool:
        """Delete a collection."""
        try:
            self.client.delete_collection(name)
            logger.info(f"Deleted collection: {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete collection {name}: {e}")
            return False
    
    # ═══════════════════════════════════════════════════════════════════════
    # PHASE 2 STUBS
    # ═══════════════════════════════════════════════════════════════════════
    
    def add_knowledge_atom(self, atom_id: str, content: str, 
                          metadata: dict) -> bool:
        """Phase 2: Add knowledge atom to atoms collection."""
        raise NotImplementedError("Phase 2 feature")
    
    def search_atoms(self, query: str, equipment_type: str = None,
                    top_k: int = 10) -> List[dict]:
        """Phase 2: Search knowledge atoms."""
        raise NotImplementedError("Phase 2 feature")
```

## Task 2.4: Manual Indexer
Create `agent_factory/knowledge/manual_indexer.py`:

```python
"""
PDF Manual Indexer
Phase 1: Basic chunking + vectorization
Phase 2 Prep: Section detection for targeted retrieval
"""
import pdfplumber
from pathlib import Path
import logging
import re
from typing import List, Dict, Optional

from .vector_store import VectorStore

logger = logging.getLogger(__name__)


class ManualIndexer:
    """Index PDF manuals into ChromaDB for semantic search."""
    
    def __init__(self):
        self.store = VectorStore()
        self.chunk_size = 500  # words
        self.overlap = 100
    
    def index_manual(self, pdf_path: Path, manual_id: str, title: str,
                    manufacturer: str, component_family: str) -> Dict:
        """
        Index a PDF manual.
        
        Returns:
            {"success": bool, "chunk_count": int, "page_count": int, "sections": [...]}
        """
        logger.info(f"Indexing manual: {title}")
        
        try:
            # Extract text from PDF
            pages = self._extract_pdf(pdf_path)
            
            # Detect sections (Phase 2: use for targeted retrieval)
            sections = self._detect_sections(pages)
            
            # Chunk content
            chunks = self._chunk_pages(pages, manual_id, title, 
                                       manufacturer, component_family)
            
            if chunks:
                documents = [c["text"] for c in chunks]
                metadatas = [c["metadata"] for c in chunks]
                ids = [c["id"] for c in chunks]
                
                self.store.add_documents(
                    self.store.manuals_collection,
                    documents,
                    metadatas,
                    ids
                )
            
            logger.info(f"Indexed {len(chunks)} chunks from {title}")
            
            return {
                "success": True,
                "chunk_count": len(chunks),
                "page_count": len(pages),
                "sections": sections
            }
            
        except Exception as e:
            logger.error(f"Failed to index {title}: {e}")
            return {"success": False, "error": str(e)}
    
    def _extract_pdf(self, pdf_path: Path) -> List[Dict]:
        """Extract text from PDF pages."""
        pages = []
        
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                
                # Extract tables and convert to text
                tables = page.extract_tables()
                table_text = ""
                for table in tables:
                    for row in table:
                        row_text = " | ".join([str(cell) if cell else "" for cell in row])
                        table_text += row_text + "\n"
                
                pages.append({
                    "page_num": i + 1,
                    "text": text,
                    "table_text": table_text
                })
        
        return pages
    
    def _detect_sections(self, pages: List[Dict]) -> List[Dict]:
        """
        Detect document sections from page content.
        Phase 2: Use these for targeted retrieval.
        """
        sections = []
        
        # Common section patterns in technical manuals
        section_patterns = [
            (r"(?i)chapter\s+\d+[:\.]?\s*(.+)", "chapter"),
            (r"(?i)section\s+\d+[:\.]?\s*(.+)", "section"),
            (r"(?i)(\d+\.?\s+)?fault\s+codes?", "fault_codes"),
            (r"(?i)(\d+\.?\s+)?troubleshoot", "troubleshooting"),
            (r"(?i)(\d+\.?\s+)?specifications?", "specifications"),
            (r"(?i)(\d+\.?\s+)?wiring", "wiring"),
            (r"(?i)(\d+\.?\s+)?installation", "installation"),
            (r"(?i)(\d+\.?\s+)?maintenance", "maintenance"),
            (r"(?i)(\d+\.?\s+)?parameter", "parameters"),
            (r"(?i)(\d+\.?\s+)?safety", "safety"),
        ]
        
        current_section = None
        
        for page in pages:
            first_500 = page["text"][:500] if page["text"] else ""
            
            for pattern, section_type in section_patterns:
                match = re.search(pattern, first_500)
                if match:
                    if current_section:
                        current_section["page_end"] = page["page_num"] - 1
                        sections.append(current_section)
                    
                    current_section = {
                        "title": match.group(0).strip(),
                        "type": section_type,
                        "page_start": page["page_num"],
                        "page_end": None
                    }
                    break
        
        if current_section:
            current_section["page_end"] = pages[-1]["page_num"]
            sections.append(current_section)
        
        return sections
    
    def _chunk_pages(self, pages: List[Dict], manual_id: str, title: str,
                    manufacturer: str, component_family: str) -> List[Dict]:
        """Chunk pages for vector storage."""
        chunks = []
        
        for page in pages:
            full_text = page["text"]
            if page["table_text"]:
                full_text += "\n[TABLE]\n" + page["table_text"]
            
            words = full_text.split()
            
            for i in range(0, len(words), self.chunk_size - self.overlap):
                chunk_words = words[i:i + self.chunk_size]
                
                # Skip tiny chunks
                if len(chunk_words) < 50:
                    continue
                
                chunk_text = " ".join(chunk_words)
                chunk_id = f"{manual_id}_p{page['page_num']}_{len(chunks)}"
                
                chunks.append({
                    "id": chunk_id,
                    "text": chunk_text,
                    "metadata": {
                        "manual_id": manual_id,
                        "title": title,
                        "manufacturer": manufacturer,
                        "component_family": component_family,
                        "page_num": page["page_num"],
                        "chunk_index": len(chunks)
                    }
                })
        
        return chunks
```

## Task 2.5: Print Indexer
Create `agent_factory/knowledge/print_indexer.py`:

```python
"""
Electrical Print Indexer
Phase 1: PDF extraction + vectorization
Phase 2 Prep: Diagram/schematic-aware chunking
"""
import pdfplumber
from pathlib import Path
import logging
from typing import List, Dict

from .vector_store import VectorStore

logger = logging.getLogger(__name__)


class PrintIndexer:
    """Index user-uploaded electrical prints."""
    
    def __init__(self):
        self.store = VectorStore()
        self.chunk_size = 400  # Smaller for electrical prints
        self.overlap = 80
    
    def index_print(self, pdf_path: Path, print_id: str, user_id: str,
                   machine_id: str, print_name: str,
                   print_type: str = None) -> Dict:
        """
        Index an electrical print PDF.
        
        Returns:
            {"success": bool, "chunk_count": int, "page_count": int, "collection_name": str}
        """
        logger.info(f"Indexing print: {print_name}")
        
        try:
            pages = self._extract_pdf(pdf_path)
            chunks = self._chunk_pages(pages, print_id, print_name, print_type)
            
            if chunks:
                collection = self.store.get_user_print_collection(user_id, machine_id)
                
                documents = [c["text"] for c in chunks]
                metadatas = [c["metadata"] for c in chunks]
                ids = [c["id"] for c in chunks]
                
                self.store.add_documents(collection, documents, metadatas, ids)
            
            collection_name = f"user_{user_id[:8]}_machine_{machine_id[:8]}"
            
            logger.info(f"Indexed {len(chunks)} chunks from {print_name}")
            
            return {
                "success": True,
                "chunk_count": len(chunks),
                "page_count": len(pages),
                "collection_name": collection_name
            }
            
        except Exception as e:
            logger.error(f"Failed to index {print_name}: {e}")
            return {"success": False, "error": str(e)}
    
    def _extract_pdf(self, pdf_path: Path) -> List[Dict]:
        """Extract text from PDF."""
        pages = []
        
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                
                # For prints, tables are often component lists
                tables = page.extract_tables()
                table_text = ""
                for table in tables:
                    for row in table:
                        row_text = " | ".join([str(cell) if cell else "" for cell in row])
                        table_text += row_text + "\n"
                
                pages.append({
                    "page_num": i + 1,
                    "text": text + "\n" + table_text
                })
        
        return pages
    
    def _chunk_pages(self, pages: List[Dict], print_id: str, 
                    print_name: str, print_type: str) -> List[Dict]:
        """Chunk with electrical context preservation."""
        chunks = []
        
        for page in pages:
            words = page["text"].split()
            
            for i in range(0, len(words), self.chunk_size - self.overlap):
                chunk_words = words[i:i + self.chunk_size]
                
                if len(chunk_words) < 30:
                    continue
                
                chunk_text = " ".join(chunk_words)
                chunk_id = f"{print_id}_p{page['page_num']}_{len(chunks)}"
                
                chunks.append({
                    "id": chunk_id,
                    "text": chunk_text,
                    "metadata": {
                        "print_id": print_id,
                        "print_name": print_name,
                        "print_type": print_type or "unknown",
                        "page_num": page["page_num"],
                        "chunk_index": len(chunks)
                    }
                })
        
        return chunks
```

## Task 2.6: Manual Search
Create `agent_factory/knowledge/manual_search.py`:

```python
"""
Manual Search Service
Phase 1: Vector + metadata search
Phase 2 Prep: Integrate with knowledge atoms
"""
from typing import List, Optional
from dataclasses import dataclass
import logging

from .vector_store import VectorStore

logger = logging.getLogger(__name__)


@dataclass
class ManualResult:
    """Search result from manual library."""
    title: str
    manufacturer: str
    component_family: str
    page_num: int
    snippet: str
    score: float
    manual_id: str


class ManualSearch:
    """Search equipment manuals for relevant content."""
    
    def __init__(self):
        self.store = VectorStore()
    
    def search(self, query: str, top_k: int = 5,
              manufacturer: str = None,
              component_family: str = None) -> List[ManualResult]:
        """
        Search manuals for query.
        
        Phase 2: Will also search knowledge_atoms and combine results.
        """
        results = self.store.search_manuals(query, top_k, manufacturer)
        
        formatted = []
        for r in results:
            meta = r["metadata"]
            
            # Filter by component family if specified
            if component_family:
                doc_family = meta.get("component_family", "").lower()
                if component_family.lower() not in doc_family:
                    continue
            
            formatted.append(ManualResult(
                title=meta.get("title", "Unknown"),
                manufacturer=meta.get("manufacturer", ""),
                component_family=meta.get("component_family", ""),
                page_num=meta.get("page_num", 0),
                snippet=r["text"][:400] + "..." if len(r["text"]) > 400 else r["text"],
                score=r["score"],
                manual_id=meta.get("manual_id", "")
            ))
        
        return formatted
    
    def search_fault_code(self, fault_code: str, 
                         manufacturer: str = None,
                         component_family: str = None) -> List[ManualResult]:
        """Search specifically for fault code information."""
        query = f"fault code {fault_code} error troubleshooting cause solution"
        return self.search(query, top_k=3, manufacturer=manufacturer,
                          component_family=component_family)
    
    def search_by_context(self, component_name: str = None,
                         manufacturer: str = None,
                         fault_code: str = None,
                         symptoms: List[str] = None) -> List[ManualResult]:
        """Search using extracted context."""
        query_parts = []
        
        if component_name:
            query_parts.append(component_name)
        if fault_code:
            query_parts.append(f"fault {fault_code}")
        if symptoms:
            query_parts.extend(symptoms[:2])
        
        if not query_parts:
            return []
        
        query = " ".join(query_parts)
        return self.search(query, top_k=5, manufacturer=manufacturer)
```

**COMMIT:**
```bash
git add -A && git commit -m "backend: ChromaDB + indexers + search" && git push
```

---

# PHASE 3: EQUIPMENT TAXONOMY (Day 3)

## Task 3.1: Create Intake Module
```bash
mkdir -p agent_factory/intake
touch agent_factory/intake/__init__.py
```

## Task 3.2: Equipment Taxonomy
Create `agent_factory/intake/equipment_taxonomy.py`:

```python
"""
Equipment Taxonomy for Context Extraction
Phase 1: 50+ manufacturers, common component families
Phase 2 Prep: Extensible for user-defined equipment types
"""
import re
from typing import Dict, List, Optional, Tuple

# ═══════════════════════════════════════════════════════════════════════════
# COMPONENT FAMILIES
# ═══════════════════════════════════════════════════════════════════════════

COMPONENT_FAMILIES = {
    "vfd": {
        "canonical": "Variable Frequency Drive",
        "aliases": ["VFD", "drive", "inverter", "AC drive", "variable speed drive", "frequency drive"],
        "category": "Motor Controls",
        "keywords": ["motor", "speed", "frequency", "hz"],
        "manufacturers": {
            "allen-bradley": {
                "patterns": ["powerflex", "1336", "160", "22a", "22b", "22c", "22d", "22f"],
                "brand": "Allen-Bradley"
            },
            "siemens": {
                "patterns": ["sinamics", "micromaster", "g120", "g110", "v20"],
                "brand": "Siemens"
            },
            "abb": {
                "patterns": ["acs", "ach", "acs880", "acs580", "acs355"],
                "brand": "ABB"
            },
            "yaskawa": {
                "patterns": ["v1000", "a1000", "j1000", "ga700", "ga500"],
                "brand": "Yaskawa"
            },
            "danfoss": {
                "patterns": ["vlt", "fc-", "fc102", "fc302"],
                "brand": "Danfoss"
            },
            "schneider": {
                "patterns": ["altivar", "atv", "atv320", "atv630"],
                "brand": "Schneider Electric"
            },
            "weg": {
                "patterns": ["cfw", "cfw11", "cfw500"],
                "brand": "WEG"
            }
        }
    },
    "plc": {
        "canonical": "Programmable Logic Controller",
        "aliases": ["PLC", "controller", "processor", "CPU", "logic controller"],
        "category": "PLCs & Controllers",
        "keywords": ["program", "logic", "io", "input", "output"],
        "manufacturers": {
            "allen-bradley": {
                "patterns": ["controllogix", "compactlogix", "micrologix", "slc", "plc-5", 
                            "1756", "1769", "1766", "1762", "1763", "5069"],
                "brand": "Allen-Bradley"
            },
            "siemens": {
                "patterns": ["s7-1500", "s7-1200", "s7-300", "s7-400", "logo", 
                            "1500", "1200", "et200"],
                "brand": "Siemens"
            },
            "mitsubishi": {
                "patterns": ["melsec", "fx", "q series", "iq-r", "iq-f", "fx5"],
                "brand": "Mitsubishi"
            },
            "omron": {
                "patterns": ["cj", "nj", "nx", "cp1", "cj2"],
                "brand": "Omron"
            },
            "beckhoff": {
                "patterns": ["cx", "twincat", "el"],
                "brand": "Beckhoff"
            }
        }
    },
    "hmi": {
        "canonical": "Human Machine Interface",
        "aliases": ["HMI", "touchscreen", "operator panel", "operator interface", "OIT", "display"],
        "category": "PLCs & Controllers",
        "keywords": ["screen", "display", "touch", "operator"],
        "manufacturers": {
            "allen-bradley": {
                "patterns": ["panelview", "2711", "2711p", "2715"],
                "brand": "Allen-Bradley"
            },
            "siemens": {
                "patterns": ["simatic", "comfort panel", "tp", "ktp", "mp"],
                "brand": "Siemens"
            },
            "proface": {
                "patterns": ["gp", "sp", "lt"],
                "brand": "Pro-face"
            }
        }
    },
    "motor": {
        "canonical": "Electric Motor",
        "aliases": ["motor", "induction motor", "AC motor", "DC motor"],
        "category": "Motors",
        "keywords": ["hp", "horsepower", "rpm", "torque"],
        "manufacturers": {}
    },
    "servo": {
        "canonical": "Servo Motor",
        "aliases": ["servo", "servo motor", "servo drive", "servo system"],
        "category": "Motion Control",
        "keywords": ["position", "encoder", "axis"],
        "manufacturers": {
            "allen-bradley": {
                "patterns": ["kinetix", "mpl", "vpl", "2198"],
                "brand": "Allen-Bradley"
            },
            "siemens": {
                "patterns": ["simotics", "1fk", "1fl"],
                "brand": "Siemens"
            },
            "yaskawa": {
                "patterns": ["sigma", "sgd", "sgm"],
                "brand": "Yaskawa"
            }
        }
    },
    "sensor": {
        "canonical": "Sensor",
        "aliases": ["sensor", "proximity", "prox", "photoelectric", "photo eye", "limit switch"],
        "category": "Sensors & Instrumentation",
        "keywords": ["detect", "sense", "signal"],
        "manufacturers": {
            "banner": {
                "patterns": ["q", "qs", "world-beam", "s18", "m18"],
                "brand": "Banner Engineering"
            },
            "keyence": {
                "patterns": ["lr", "lv", "il", "pr", "pz"],
                "brand": "Keyence"
            },
            "ifm": {
                "patterns": ["efector", "o5", "ig", "ie"],
                "brand": "IFM"
            },
            "omron": {
                "patterns": ["e2e", "e3", "e2a"],
                "brand": "Omron"
            },
            "sick": {
                "patterns": ["w", "wl", "dt", "dx"],
                "brand": "SICK"
            },
            "turck": {
                "patterns": ["bi", "ni", "uprox"],
                "brand": "Turck"
            }
        }
    },
    "safety_relay": {
        "canonical": "Safety Relay",
        "aliases": ["safety relay", "guard relay", "e-stop relay", "safety controller"],
        "category": "Safety",
        "keywords": ["safety", "emergency", "stop", "guard"],
        "manufacturers": {
            "pilz": {
                "patterns": ["pnoz", "pss", "psen"],
                "brand": "Pilz"
            },
            "allen-bradley": {
                "patterns": ["guardmaster", "msr", "440r", "guardlogix"],
                "brand": "Allen-Bradley"
            },
            "banner": {
                "patterns": ["sc", "xsm"],
                "brand": "Banner"
            },
            "sick": {
                "patterns": ["flexi", "ue"],
                "brand": "SICK"
            }
        }
    },
    "contactor": {
        "canonical": "Motor Contactor",
        "aliases": ["contactor", "starter", "motor starter", "magnetic starter"],
        "category": "Motor Controls",
        "keywords": ["contact", "start", "coil"],
        "manufacturers": {}
    },
    "overload": {
        "canonical": "Overload Relay",
        "aliases": ["overload", "overload relay", "motor protector", "thermal overload"],
        "category": "Motor Controls",
        "keywords": ["overload", "thermal", "protection"],
        "manufacturers": {}
    },
    "valve": {
        "canonical": "Solenoid Valve",
        "aliases": ["valve", "solenoid", "solenoid valve", "directional valve", "pneumatic valve"],
        "category": "Pneumatics",
        "keywords": ["air", "pneumatic", "cylinder"],
        "manufacturers": {
            "festo": {
                "patterns": ["vuvs", "mfh", "jmfh", "cpv", "vtug"],
                "brand": "Festo"
            },
            "smc": {
                "patterns": ["sy", "vq", "vf", "sq"],
                "brand": "SMC"
            },
            "parker": {
                "patterns": ["viking", "gold ring"],
                "brand": "Parker"
            }
        }
    },
    "pressure_transmitter": {
        "canonical": "Pressure Transmitter",
        "aliases": ["pressure transmitter", "pressure sensor", "pressure transducer"],
        "category": "Sensors & Instrumentation",
        "keywords": ["pressure", "psi", "bar"],
        "manufacturers": {
            "endress": {
                "patterns": ["cerabar", "deltabar"],
                "brand": "Endress+Hauser"
            },
            "rosemount": {
                "patterns": ["3051", "2051", "2088"],
                "brand": "Rosemount"
            }
        }
    },
    "flow_meter": {
        "canonical": "Flow Meter",
        "aliases": ["flow meter", "flowmeter", "flow sensor", "flow transmitter"],
        "category": "Sensors & Instrumentation",
        "keywords": ["flow", "gpm", "rate"],
        "manufacturers": {}
    },
    "temperature": {
        "canonical": "Temperature Sensor",
        "aliases": ["temperature sensor", "thermocouple", "RTD", "temp sensor"],
        "category": "Sensors & Instrumentation",
        "keywords": ["temperature", "temp", "degrees", "thermal"],
        "manufacturers": {}
    },
    "power_supply": {
        "canonical": "Power Supply",
        "aliases": ["power supply", "PSU", "DC power"],
        "category": "Power Distribution",
        "keywords": ["24v", "voltage", "dc", "power"],
        "manufacturers": {
            "allen-bradley": {
                "patterns": ["1606", "bulletin 1606"],
                "brand": "Allen-Bradley"
            },
            "phoenix": {
                "patterns": ["quint", "trio", "step"],
                "brand": "Phoenix Contact"
            },
            "mean_well": {
                "patterns": ["dr-", "hdr-", "edr-"],
                "brand": "Mean Well"
            }
        }
    },
    "circuit_breaker": {
        "canonical": "Circuit Breaker",
        "aliases": ["breaker", "circuit breaker", "CB", "MCCB"],
        "category": "Power Distribution",
        "keywords": ["breaker", "amp", "trip"],
        "manufacturers": {}
    }
}

# ═══════════════════════════════════════════════════════════════════════════
# ISSUE TYPE KEYWORDS
# ═══════════════════════════════════════════════════════════════════════════

ISSUE_KEYWORDS = {
    "fault_code": ["fault", "error", "alarm", "code", "f0", "e0", "err", "failure"],
    "wont_start": ["won't start", "wont start", "no start", "doesn't start", "dead", "no power"],
    "intermittent": ["intermittent", "sometimes", "random", "sporadic", "comes and goes", "occasionally"],
    "noise_vibration": ["noise", "vibration", "grinding", "humming", "buzzing", "rattling", "squealing"],
    "overheating": ["hot", "overheating", "temperature", "thermal", "burning", "smoke"],
    "communication": ["communication", "network", "ethernet", "no connection", "offline", "lost comm", "timeout"],
    "calibration": ["calibration", "drift", "accuracy", "offset", "scaling", "out of range"],
    "physical_damage": ["broken", "cracked", "damaged", "burnt", "melted", "corroded"],
    "performance": ["slow", "weak", "reduced", "poor", "degraded", "sluggish"],
    "leak": ["leak", "leaking", "drip", "seep"]
}

# ═══════════════════════════════════════════════════════════════════════════
# URGENCY KEYWORDS
# ═══════════════════════════════════════════════════════════════════════════

URGENCY_KEYWORDS = {
    "critical": ["down", "stopped", "urgent", "emergency", "production stopped", "critical", "safety"],
    "high": ["asap", "high priority", "soon", "important", "need now"],
    "low": ["when you can", "no rush", "minor", "cosmetic", "when possible"]
}

# ═══════════════════════════════════════════════════════════════════════════
# EXTRACTION FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def identify_component(text: str) -> Dict:
    """
    Identify component family and manufacturer from text.
    
    Returns:
        {
            "family": "Variable Frequency Drive",
            "family_key": "vfd",
            "category": "Motor Controls",
            "manufacturer": "Allen-Bradley"
        }
    """
    text_lower = text.lower()
    
    for family_key, family_data in COMPONENT_FAMILIES.items():
        # Check aliases
        for alias in family_data["aliases"]:
            if alias.lower() in text_lower:
                # Found family, now check manufacturer
                manufacturer = None
                
                for mfr_key, mfr_data in family_data.get("manufacturers", {}).items():
                    for pattern in mfr_data["patterns"]:
                        if pattern.lower() in text_lower:
                            manufacturer = mfr_data["brand"]
                            break
                    if manufacturer:
                        break
                
                return {
                    "family": family_data["canonical"],
                    "family_key": family_key,
                    "category": family_data["category"],
                    "manufacturer": manufacturer
                }
    
    # Check manufacturer patterns even without family match
    for family_key, family_data in COMPONENT_FAMILIES.items():
        for mfr_key, mfr_data in family_data.get("manufacturers", {}).items():
            for pattern in mfr_data["patterns"]:
                if pattern.lower() in text_lower:
                    return {
                        "family": family_data["canonical"],
                        "family_key": family_key,
                        "category": family_data["category"],
                        "manufacturer": mfr_data["brand"]
                    }
    
    return {"family": None, "family_key": None, "category": None, "manufacturer": None}


def identify_issue_type(text: str) -> str:
    """Identify the type of issue from text."""
    text_lower = text.lower()
    
    for issue_type, keywords in ISSUE_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                return issue_type
    
    return "unknown"


def identify_urgency(text: str) -> str:
    """Identify urgency level from text."""
    text_lower = text.lower()
    
    for urgency, keywords in URGENCY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                return urgency
    
    return "medium"


def extract_fault_code(text: str) -> Optional[str]:
    """Extract fault code from text."""
    patterns = [
        r'\b[fF]\d{1,4}\b',              # F001, F1, f004
        r'\b[eE]rr?\d{1,4}\b',           # E01, Err5
        r'\b[aA]larm\s*\d{1,4}\b',       # Alarm 5
        r'\bfault\s*code\s*(\d+)\b',     # fault code 5
        r'\bcode\s+([A-Za-z]?\d+)\b',    # code 45, code A12
        r'\berror\s+([A-Za-z]?\d+)\b',   # error 12
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0).upper().replace(" ", "")
    
    return None


def extract_model_number(text: str) -> Optional[str]:
    """Extract model number from text."""
    # Common model number patterns
    patterns = [
        r'\b(PowerFlex\s*\d{3}[A-Z]?)\b',     # PowerFlex 525
        r'\b(22[A-F]-[A-Z0-9]+)\b',            # 22B-D010N104
        r'\b(1756-[A-Z0-9]+)\b',               # 1756-L71
        r'\b(S7-\d{4})\b',                     # S7-1500
        r'\b(ACS\d{3})\b',                     # ACS880
        r'\b([A-Z]{2,3}\d{3,4}[A-Z]?)\b',     # Generic
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).upper()
    
    return None
```

**COMMIT:**
```bash
git add -A && git commit -m "backend: equipment taxonomy" && git push
```

---

# PHASE 4: API ENDPOINTS (Day 4)

## Task 4.1: Manual API
Create `agent_factory/api/routers/manuals.py`:

```python
"""Manual Library API Endpoints."""
from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from pathlib import Path
import tempfile
import uuid
import logging

from agent_factory.knowledge.manual_indexer import ManualIndexer
from agent_factory.knowledge.manual_search import ManualSearch
from agent_factory.rivet_pro.database import DatabaseManager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/manuals", tags=["manuals"])


@router.post("/upload")
async def upload_manual(
    file: UploadFile = File(...),
    title: str = Query(None),
    manufacturer: str = Query(None),
    component_family: str = Query(None)
):
    """Upload and index a manual PDF."""
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(400, "Only PDF files accepted")
    
    temp_path = Path(tempfile.mktemp(suffix=".pdf"))
    content = await file.read()
    temp_path.write_bytes(content)
    
    try:
        manual_id = str(uuid.uuid4())
        title = title or file.filename
        
        # Index the manual
        indexer = ManualIndexer()
        result = indexer.index_manual(
            temp_path,
            manual_id,
            title,
            manufacturer or "Unknown",
            component_family or "Unknown"
        )
        
        if not result["success"]:
            raise HTTPException(500, f"Indexing failed: {result.get('error')}")
        
        # Save to database
        db = DatabaseManager()
        await db.connect()
        manual = await db.create_manual(
            title, manufacturer or "Unknown", 
            component_family or "Unknown", str(temp_path)
        )
        await db.update_manual_indexed(
            str(manual["id"]), "equipment_manuals", result["page_count"]
        )
        
        return {
            "manual_id": str(manual["id"]),
            "title": title,
            "pages": result["page_count"],
            "chunks": result["chunk_count"],
            "sections": result.get("sections", [])
        }
        
    finally:
        temp_path.unlink(missing_ok=True)


@router.get("/search")
async def search_manuals(
    q: str = Query(..., description="Search query"),
    manufacturer: str = Query(None),
    component_family: str = Query(None),
    limit: int = Query(5, ge=1, le=20)
):
    """Search indexed manuals."""
    search = ManualSearch()
    results = search.search(
        q, top_k=limit, 
        manufacturer=manufacturer,
        component_family=component_family
    )
    
    return {
        "query": q,
        "count": len(results),
        "results": [
            {
                "title": r.title,
                "manufacturer": r.manufacturer,
                "component_family": r.component_family,
                "page": r.page_num,
                "snippet": r.snippet,
                "score": round(r.score, 3)
            }
            for r in results
        ]
    }


@router.get("/gaps")
async def get_manual_gaps(limit: int = Query(10, ge=1, le=50)):
    """Get most requested missing manuals."""
    db = DatabaseManager()
    await db.connect()
    gaps = await db.get_top_manual_gaps(limit)
    
    return {
        "count": len(gaps),
        "gaps": gaps
    }


@router.get("/list")
async def list_manuals():
    """List all indexed manuals."""
    db = DatabaseManager()
    await db.connect()
    manuals = await db.get_all_manuals()
    
    return {
        "count": len(manuals),
        "manuals": manuals
    }
```

## Task 4.2: Update Main API
Add to `agent_factory/api/main.py`:

```python
from agent_factory.api.routers import manuals

app.include_router(manuals.router)
```

**COMMIT:**
```bash
git add -A && git commit -m "backend: manual API endpoints" && git push
```

---

# PHASE 5: TESTING (Day 5)

## Task 5.1: Test Script
Create `test_backend.py`:

```python
"""Test backend components."""
import asyncio
from pathlib import Path

async def test_database():
    print("Testing database...")
    from agent_factory.rivet_pro.database import DatabaseManager
    
    db = DatabaseManager()
    await db.connect()
    
    # Test machine creation
    machine = await db.create_machine(
        "test-user-id", 
        "Test Lathe", 
        "Test machine for backend validation"
    )
    print(f"  ✅ Created machine: {machine['name']}")
    
    # Test manual gap logging
    gap = await db.log_manual_gap("Allen-Bradley", "VFD", "PowerFlex 525")
    print(f"  ✅ Logged gap: {gap['manufacturer']} {gap['component_family']}")
    
    gaps = await db.get_top_manual_gaps()
    print(f"  ✅ Top gaps: {len(gaps)} found")
    
    print("Database tests passed!\n")


def test_vector_store():
    print("Testing vector store...")
    from agent_factory.knowledge.vector_store import VectorStore
    
    store = VectorStore()
    print(f"  ✅ VectorStore initialized at {store.persist_dir}")
    
    # Test embedding
    embedding = store.embed_text("PowerFlex 525 fault code F004")
    print(f"  ✅ Embedding length: {len(embedding)}")
    
    # Test collection
    collection = store.get_user_print_collection("test-user", "test-machine")
    print(f"  ✅ Collection: {collection.name}")
    
    print("Vector store tests passed!\n")


def test_taxonomy():
    print("Testing equipment taxonomy...")
    from agent_factory.intake.equipment_taxonomy import (
        identify_component, identify_issue_type, 
        extract_fault_code, identify_urgency
    )
    
    # Test VFD detection
    result = identify_component("The PowerFlex 525 is showing an error")
    assert result["family"] == "Variable Frequency Drive"
    assert result["manufacturer"] == "Allen-Bradley"
    print(f"  ✅ VFD detected: {result}")
    
    # Test fault code extraction
    code = extract_fault_code("Fault F004 on the drive")
    assert code == "F004"
    print(f"  ✅ Fault code: {code}")
    
    # Test issue type
    issue = identify_issue_type("Motor won't start, no power")
    assert issue == "wont_start"
    print(f"  ✅ Issue type: {issue}")
    
    # Test urgency
    urgency = identify_urgency("Production is stopped, need help ASAP")
    assert urgency in ["critical", "high"]
    print(f"  ✅ Urgency: {urgency}")
    
    print("Taxonomy tests passed!\n")


if __name__ == "__main__":
    print("=" * 50)
    print("RIVET BACKEND TESTS")
    print("=" * 50 + "\n")
    
    asyncio.run(test_database())
    test_vector_store()
    test_taxonomy()
    
    print("=" * 50)
    print("ALL TESTS PASSED ✅")
    print("=" * 50)
```

Run:
```bash
python test_backend.py
```

**FINAL COMMIT:**
```bash
git add -A && git commit -m "backend: complete with tests" && git push
```

---

# SUCCESS CRITERIA

- [ ] Database tables created (machines, prints, manuals, chat_history, context_extractions, manual_gaps)
- [ ] Phase 2 tables commented and ready (subsystems, components, atoms, research_jobs)
- [ ] ChromaDB stores and retrieves vectors
- [ ] Manual indexer processes PDFs and detects sections
- [ ] Print indexer creates per-user collections
- [ ] Equipment taxonomy identifies 50+ manufacturers
- [ ] Fault code extraction works
- [ ] API endpoints respond correctly
- [ ] All tests pass

---

# TAB 1 COMPLETE

Backend infrastructure ready. Tab 3 (Bot) will use:
- `DatabaseManager` for CRUD
- `VectorStore` for semantic search
- `ManualSearch` for knowledge retrieval
- `equipment_taxonomy` for context extraction

Phase 2 additions (after MVP):
- Uncomment Phase 2 tables in migration
- Implement `create_knowledge_atom()` and `search_atoms()`
- Add research job logging
- Build expert review workflow
