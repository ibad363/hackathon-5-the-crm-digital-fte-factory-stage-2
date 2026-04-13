ALTER TABLE tickets ADD COLUMN IF NOT EXISTS external_ref VARCHAR(255);
CREATE INDEX IF NOT EXISTS idx_tickets_external_ref ON tickets(external_ref);
