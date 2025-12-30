-- CMMS Schema for SQLite
-- Converted from PostgreSQL migrations 005 and 006

-- Equipment table
CREATE TABLE IF NOT EXISTS cmms_equipment (
    -- Identity
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    equipment_number TEXT UNIQUE NOT NULL DEFAULT ('EQ-' || strftime('%Y', 'now') || '-' || printf('%06d', abs(random() % 1000000))),

    -- Equipment Details
    manufacturer TEXT NOT NULL,
    model_number TEXT,
    serial_number TEXT,
    equipment_type TEXT,

    -- Location & Context
    location TEXT,
    department TEXT,
    criticality TEXT DEFAULT 'medium' CHECK(criticality IN ('low', 'medium', 'high', 'critical')),

    -- Ownership
    owned_by_user_id TEXT,
    machine_id TEXT,

    -- Metadata
    description TEXT,
    photo_file_id TEXT,
    installation_date TEXT,
    last_maintenance_date TEXT,

    -- Stats
    work_order_count INTEGER DEFAULT 0,
    total_downtime_hours REAL DEFAULT 0.0,
    last_reported_fault TEXT,
    last_work_order_at TEXT,

    -- Timestamps
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    first_reported_by TEXT
);

-- Equipment indexes
CREATE INDEX IF NOT EXISTS idx_equipment_manufacturer ON cmms_equipment(manufacturer);
CREATE INDEX IF NOT EXISTS idx_equipment_model ON cmms_equipment(model_number);
CREATE INDEX IF NOT EXISTS idx_equipment_serial ON cmms_equipment(serial_number);
CREATE INDEX IF NOT EXISTS idx_equipment_user ON cmms_equipment(owned_by_user_id);
CREATE INDEX IF NOT EXISTS idx_equipment_location ON cmms_equipment(location);
CREATE INDEX IF NOT EXISTS idx_equipment_created ON cmms_equipment(created_at DESC);

-- Work orders table
CREATE TABLE IF NOT EXISTS work_orders (
    -- Identity
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    work_order_number TEXT UNIQUE NOT NULL DEFAULT ('WO-' || strftime('%Y', 'now') || '-' || printf('%06d', abs(random() % 1000000))),

    -- User & Source
    user_id TEXT NOT NULL,
    telegram_username TEXT,
    created_by_agent TEXT,
    source TEXT NOT NULL CHECK(source IN ('telegram_text', 'telegram_voice', 'telegram_photo', 'telegram_print_qa', 'telegram_manual_gap')),

    -- Equipment (LINKED TO CMMS_EQUIPMENT)
    equipment_id TEXT REFERENCES cmms_equipment(id) ON DELETE SET NULL,
    equipment_number TEXT,

    -- Equipment Details (denormalized)
    manufacturer TEXT,
    model_number TEXT,
    serial_number TEXT,
    equipment_type TEXT,
    machine_id TEXT,
    location TEXT,

    -- Issue Details
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    fault_codes TEXT,  -- JSON array as text
    symptoms TEXT,     -- JSON array as text

    -- Response Metadata
    answer_text TEXT,
    confidence_score REAL,
    route_taken TEXT CHECK(route_taken IN ('A', 'B', 'C', 'D')),
    suggested_actions TEXT,  -- JSON array as text
    safety_warnings TEXT,    -- JSON array as text
    cited_kb_atoms TEXT,     -- JSON array as text
    manual_links TEXT,       -- JSON array as text

    -- Status & Priority
    status TEXT DEFAULT 'open' CHECK(status IN ('open', 'in_progress', 'completed', 'cancelled')),
    priority TEXT DEFAULT 'medium' CHECK(priority IN ('low', 'medium', 'high', 'critical')),

    -- Audit Trail
    trace_id TEXT,
    conversation_id TEXT,
    research_triggered INTEGER DEFAULT 0,
    enrichment_triggered INTEGER DEFAULT 0,

    -- Timestamps
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    completed_at TEXT
);

-- Work order indexes
CREATE INDEX IF NOT EXISTS idx_work_orders_user ON work_orders(user_id);
CREATE INDEX IF NOT EXISTS idx_work_orders_equipment ON work_orders(equipment_id);
CREATE INDEX IF NOT EXISTS idx_work_orders_status ON work_orders(status);
CREATE INDEX IF NOT EXISTS idx_work_orders_priority ON work_orders(priority);
CREATE INDEX IF NOT EXISTS idx_work_orders_created ON work_orders(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_work_orders_trace ON work_orders(trace_id);
CREATE INDEX IF NOT EXISTS idx_work_orders_source ON work_orders(source);

-- Trigger to auto-update updated_at for equipment
CREATE TRIGGER IF NOT EXISTS equipment_updated_at
AFTER UPDATE ON cmms_equipment
FOR EACH ROW
BEGIN
    UPDATE cmms_equipment SET updated_at = datetime('now') WHERE id = NEW.id;
END;

-- Trigger to auto-update updated_at for work orders
CREATE TRIGGER IF NOT EXISTS work_order_updated_at
AFTER UPDATE ON work_orders
FOR EACH ROW
BEGIN
    UPDATE work_orders SET updated_at = datetime('now') WHERE id = NEW.id;
END;

-- Trigger to update equipment stats when work order created
CREATE TRIGGER IF NOT EXISTS work_order_equipment_stats
AFTER INSERT ON work_orders
FOR EACH ROW
WHEN NEW.equipment_id IS NOT NULL
BEGIN
    UPDATE cmms_equipment
    SET
        work_order_count = work_order_count + 1,
        last_work_order_at = datetime('now'),
        updated_at = datetime('now')
    WHERE id = NEW.equipment_id;
END;
