-- audit_log: append-only audit trail.
-- A state change is a new row with the same batch_id; the latest row wins.
-- created_at is UTC, format YYYY-MM-DD HH:MM:SS.

CREATE TABLE IF NOT EXISTS audit_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  asset_id TEXT,
  action TEXT NOT NULL,
  detail TEXT NOT NULL,
  actor TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  policy_version TEXT,
  diff_before TEXT,
  diff_after TEXT,
  batch_id TEXT,
  status TEXT,
  severity TEXT
);

CREATE TRIGGER IF NOT EXISTS trg_audit_no_update
BEFORE UPDATE ON audit_log
BEGIN
  SELECT RAISE(ABORT, 'audit_log is append-only: UPDATE not allowed');
END;

CREATE TRIGGER IF NOT EXISTS trg_audit_no_delete
BEFORE DELETE ON audit_log
BEGIN
  SELECT RAISE(ABORT, 'audit_log is append-only: DELETE not allowed');
END;
