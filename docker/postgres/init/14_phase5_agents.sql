-- Sprint 5.3 — Multi-agent orchestration (advise-only)

CREATE TABLE IF NOT EXISTS agents (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    domain_code TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    runnable BOOLEAN NOT NULL DEFAULT FALSE,
    version TEXT NOT NULL DEFAULT '1.0.0',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS agent_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects (id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'queued',
    goal TEXT,
    focus_domains TEXT[] NOT NULL DEFAULT '{}',
    input_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    output_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    overall_confidence DOUBLE PRECISION,
    conflict_count INTEGER NOT NULL DEFAULT 0,
    error TEXT,
    created_by UUID REFERENCES users (id) ON DELETE SET NULL,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_agent_runs_project_id ON agent_runs (project_id);
CREATE INDEX IF NOT EXISTS idx_agent_runs_created_at ON agent_runs (created_at DESC);

CREATE TABLE IF NOT EXISTS agent_tool_calls (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_run_id UUID NOT NULL REFERENCES agent_runs (id) ON DELETE CASCADE,
    agent_id TEXT,
    tool_name TEXT NOT NULL,
    request_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    response_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    ok BOOLEAN NOT NULL DEFAULT TRUE,
    error TEXT,
    latency_ms INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_agent_tool_calls_run_id ON agent_tool_calls (agent_run_id);

INSERT INTO agents (id, name, domain_code, description, enabled, runnable, version)
VALUES
    ('networking', 'Networking Specialist', 'networking', 'Campus/WAN/LAN advisory assessments', TRUE, TRUE, '1.0.0'),
    ('wireless', 'Wireless Specialist', 'wireless', 'Wi-Fi / WLAN high-density advisory', TRUE, TRUE, '1.0.0'),
    ('security', 'Security Specialist', 'cybersecurity', 'Cybersecurity / zero-trust advisory', TRUE, TRUE, '1.0.0'),
    ('cloud', 'Cloud Specialist', 'cloud', 'Cloud landing-zone advisory', TRUE, TRUE, '1.0.0'),
    ('data_centre', 'Data Centre Specialist', 'data_centre', 'Data centre facility and fabric advisory', TRUE, TRUE, '1.0.0'),
    ('storage', 'Storage Specialist', 'storage', 'Storage architecture advisory', TRUE, TRUE, '1.0.0'),
    ('backup', 'Backup Specialist', 'backup', 'Backup and recovery advisory', TRUE, TRUE, '1.0.0'),
    ('av', 'AV Specialist', 'av', 'AV / collaboration room advisory', TRUE, TRUE, '1.0.0'),
    ('led_videowall', 'LED / Digital Signage Specialist', 'led_videowall', 'LED videowall and digital signage advisory', TRUE, TRUE, '1.0.0'),
    ('smart_building', 'Smart Building / IoT Specialist', 'smart_building', 'Smart building / IoT advisory', TRUE, TRUE, '1.0.0'),
    ('compute', 'Compute Specialist', 'compute', 'Compute and virtualization advisory', TRUE, TRUE, '1.0.0'),
    ('hci', 'HCI Specialist', 'hci', 'Hyperconverged infrastructure advisory', TRUE, TRUE, '1.0.0'),
    ('digital_signage', 'Digital Signage Specialist', 'digital_signage', 'Digital signage platform advisory', TRUE, TRUE, '1.0.0'),
    ('billboard', 'Billboard Specialist', 'billboard', 'Outdoor billboard / DOOH advisory', TRUE, TRUE, '1.0.0'),
    ('iot', 'IoT Specialist', 'iot', 'IoT / CCTV / telemetry advisory', TRUE, TRUE, '1.0.0')
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    domain_code = EXCLUDED.domain_code,
    description = EXCLUDED.description,
    enabled = EXCLUDED.enabled,
    runnable = EXCLUDED.runnable,
    version = EXCLUDED.version;
