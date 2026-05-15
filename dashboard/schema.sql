CREATE TABLE IF NOT EXISTS agentsnapshot (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    role TEXT NOT NULL,
    department TEXT NOT NULL,
    goal TEXT NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS taskrun (
    id SERIAL PRIMARY KEY,
    prompt TEXT NOT NULL,
    status TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    approval_requested BOOLEAN NOT NULL DEFAULT FALSE,
    approval_approved BOOLEAN NOT NULL DEFAULT FALSE,
    dry_run BOOLEAN NOT NULL DEFAULT TRUE,
    output TEXT NOT NULL DEFAULT '',
    output_file TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS taskrun_created_at_idx ON taskrun (created_at DESC);
CREATE INDEX IF NOT EXISTS taskrun_agent_id_idx ON taskrun (agent_id);

CREATE TABLE IF NOT EXISTS "user" (
    id SERIAL PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    is_admin BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL
);
