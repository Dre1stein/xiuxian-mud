-- SQLite schema for player data storage
-- Version 2

CREATE TABLE IF NOT EXISTS players (
    player_id TEXT PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    level INTEGER DEFAULT 1,
    xp INTEGER DEFAULT 0,
    stage TEXT DEFAULT '炼气期',
    sect TEXT,
    cultivation INTEGER DEFAULT 0,
    spirit_stones INTEGER DEFAULT 1000,
    current_map TEXT DEFAULT '宗门',
    base_stats TEXT,  -- JSON string
    sect_stats TEXT,  -- JSON string
    school_progress TEXT,  -- JSON string
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_players_name ON players(name);
CREATE INDEX IF NOT EXISTS idx_players_last_active ON players(last_active);

-- Combat sessions table for persistence
CREATE TABLE IF NOT EXISTS combat_sessions (
    session_id TEXT PRIMARY KEY,
    player_name TEXT NOT NULL,
    state TEXT NOT NULL,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_combat_sessions_player ON combat_sessions(player_name);
CREATE INDEX IF NOT EXISTS idx_combat_sessions_status ON combat_sessions(status);
CREATE INDEX IF NOT EXISTS idx_combat_sessions_updated ON combat_sessions(updated_at);

-- Migration tracking table
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

-- Record initial schema version
INSERT OR IGNORE INTO schema_version (version, description)
VALUES (1, 'Initial schema with players table');

-- Version 2: Add combat sessions table
INSERT OR IGNORE INTO schema_version (version, description)
VALUES (2, 'Added combat_sessions table for persistence');
