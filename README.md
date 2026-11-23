# sqlite-audit-log

Read this in [繁體中文](README.zh-TW.md).

Append-only SQLite audit log with a controlled vocabulary and batch issue tracking.

Three small scripts sharing one module:

- `audit_common.py` — the single source of truth: action/status vocabulary, state machine, severity ordering, timestamp parsing, and the queries for latest-per-batch state and open issues.
- `validate_audit.py` — checks every row's action, status, and severity against the controlled vocabulary. Exits 1 on error.
- `issue_stats.py` — per-batch latest-status counts; open issues listed by severity, flagged `[OVERDUE]` after 7 days.

## The log

The `audit_log` table is append-only: triggers reject UPDATE and DELETE. A state change is a new row with the same `batch_id`; the latest row wins. See `schema.sql` for the table and triggers.

## Use

```bash
sqlite3 audit.sqlite < schema.sql
export AUDIT_DB=audit.sqlite        # or pass --db audit.sqlite
python3 validate_audit.py --db audit.sqlite
python3 issue_stats.py --db audit.sqlite
```

## Vocabulary

- Issue kinds: incident, problem, enquiry, risk, change. Each has its own allowed statuses and closed states (see `KNOWN_STATUS` and `CLOSED` in `audit_common.py`).
- Other actions (merge, fix, dedup, policy, approve, ...) only record ok/failed/blocked.
- Severity: critical, high, medium, low. Open issues sort by severity, then by days open.

## License

MIT — see [LICENSE](LICENSE).
