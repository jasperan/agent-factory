-- ═══════════════════════════════════════════════════════════════════════════
-- RIVET CMMS DATABASE SCHEMA - Backend Infrastructure
-- Migration 003: TAB 1 Backend + Knowledge Infrastructure
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

-- ─────────────────────────────────────────────────────────────────────────────
-- COMPLETION
-- ─────────────────────────────────────────────────────────────────────────────

-- Verify tables created
DO $$
BEGIN
    RAISE NOTICE 'Migration 003 complete. Phase 1 tables created:';
    RAISE NOTICE '  - machines';
    RAISE NOTICE '  - prints';
    RAISE NOTICE '  - equipment_manuals';
    RAISE NOTICE '  - print_chat_history';
    RAISE NOTICE '  - context_extractions';
    RAISE NOTICE '  - manual_gaps';
    RAISE NOTICE '';
    RAISE NOTICE 'Phase 2 tables ready (commented out):';
    RAISE NOTICE '  - equipment_subsystems';
    RAISE NOTICE '  - equipment_components';
    RAISE NOTICE '  - knowledge_atoms';
    RAISE NOTICE '  - ai_research_jobs';
    RAISE NOTICE '  - ai_generated_resources';
    RAISE NOTICE '  - resource_feedback';
END $$;
