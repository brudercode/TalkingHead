-- Asset Registry Schema for EcoChiefs Pipeline
-- Tracks 3D assets from source → refinement → approval → publication

-- Identity definitions (EcoChiefs characters)
CREATE TABLE IF NOT EXISTS identities (
    identity_id TEXT PRIMARY KEY,  -- e.g., 'ecochief.taurus'
    name TEXT NOT NULL,             -- e.g., 'Taurus'
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Asset states: pending, refining, review, approved, rejected, superseded, published
CREATE TABLE IF NOT EXISTS assets (
    asset_id TEXT PRIMARY KEY,      -- UUID or hash-based ID
    identity_id TEXT NOT NULL,      -- FK to identities
    source_tool TEXT NOT NULL,      -- 'meshy', 'comfyui', 'blender', 'manual'
    source_path TEXT NOT NULL,      -- Original file path
    file_hash TEXT NOT NULL,        -- SHA-256 of GLB
    file_size INTEGER,              -- Bytes
    state TEXT NOT NULL DEFAULT 'pending',  -- Current workflow state
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSON,                  -- Tool-specific metadata (polycount, etc.)
    FOREIGN KEY (identity_id) REFERENCES identities(identity_id)
);

-- Workflow history for each asset
CREATE TABLE IF NOT EXISTS workflows (
    workflow_id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id TEXT NOT NULL,
    from_state TEXT,
    to_state TEXT NOT NULL,
    operator TEXT,                  -- Human or system identifier
    notes TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (asset_id) REFERENCES assets(asset_id)
);

-- Defects found in assets (from viewer, QA, or automated checks)
CREATE TABLE IF NOT EXISTS defects (
    defect_id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id TEXT NOT NULL,
    defect_type TEXT NOT NULL,      -- 'texture_seam', 'topology', 'rigging', 'normals', etc.
    severity TEXT NOT NULL,         -- 'low', 'medium', 'high', 'blocker'
    description TEXT,
    status TEXT DEFAULT 'open',     -- 'open', 'in_progress', 'fixed', 'wontfix'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    FOREIGN KEY (asset_id) REFERENCES assets(asset_id)
);

-- Card bindings: which asset is bound to which ArchCard slot
CREATE TABLE IF NOT EXISTS card_bindings (
    binding_id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id TEXT NOT NULL,
    identity_id TEXT NOT NULL,
    slot TEXT NOT NULL,             -- 'avatar3d', 'thumbnail', 'icon', etc.
    web_path TEXT NOT NULL,         -- '/assets/taurus/taurus-meshy-v1.glb'
    is_canonical BOOLEAN DEFAULT 0, -- Only one canonical per identity+slot
    bound_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (asset_id) REFERENCES assets(asset_id),
    FOREIGN KEY (identity_id) REFERENCES identities(identity_id),
    UNIQUE(identity_id, slot, is_canonical) ON CONFLICT REPLACE
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_assets_identity ON assets(identity_id);
CREATE INDEX IF NOT EXISTS idx_assets_state ON assets(state);
CREATE INDEX IF NOT EXISTS idx_workflows_asset ON workflows(asset_id);
CREATE INDEX IF NOT EXISTS idx_defects_asset ON defects(asset_id);
CREATE INDEX IF NOT EXISTS idx_defects_status ON defects(status);
CREATE INDEX IF NOT EXISTS idx_bindings_identity ON card_bindings(identity_id);

-- Insert default EcoChiefs identities
INSERT OR IGNORE INTO identities (identity_id, name, description) VALUES
    ('ecochief.taurus', 'Taurus', 'Chief Guardian of Value & Stewardship'),
    ('ecochief.fox', 'Fox', 'Clever Strategist'),
    ('ecochief.khan', 'Khan', 'Wise Leader'),
    ('ecochief.kong', 'Kong', 'Mighty Protector'),
    ('ecochief.rocky', 'Rocky', 'Steadfast Guardian'),
    ('ecochief.rudi', 'Rudi', 'Swift Scout'),
    ('ecochief.ruki', 'Ruki', 'Resourceful Planner'),
    ('ecochief.tusker', 'Tusker', 'Ancient Keeper');
