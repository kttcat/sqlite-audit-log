# sqlite-audit-log

Read this in [繁體中文](README.zh-TW.md).

Append-only SQLite audit log with a controlled vocabulary and batch issue tracking.

Three small scripts sharing one module:

- `audit_common.py` — the single source of truth: action/status vocabulary, state machine, severity ordering, timestamp parsing, and the queries for latest-per-batch state and open issues.
- `validate_audit.py` — checks every row's action, status, and severity against the controlled vocabulary. Exits 1 on error.
- `issue_stats.py` — per-batch latest-status counts; open issues listed by severity, flagged `[OVERDUE 超期Nd天]` once open for more than 7 whole days (the 8th day onward).

## The log

The `audit_log` table is append-only: triggers reject UPDATE and DELETE. A state change is a new row with the same `batch_id`; the latest row wins. See `schema.sql` for the table and triggers. The vocabulary itself is enforced by `validate_audit.py`, not by the database — the triggers only reject UPDATE and DELETE.

## Use

```bash
sqlite3 audit.sqlite < schema.sql
export AUDIT_DB=audit.sqlite        # or pass --db audit.sqlite
python3 validate_audit.py --db audit.sqlite
python3 issue_stats.py --db audit.sqlite
```

Run the tests (stdlib `unittest` only, in-memory DB):

```bash
python3 -m unittest test_audit.py -v
```

Seed example data with `sqlite3 audit.sqlite < examples/seed.sql` (expected output is in the file's header comment). Do not commit the generated `audit.sqlite` file.

## Vocabulary

- Issue kinds: incident, problem, enquiry, risk, change. Each has its own allowed statuses and closed states (see `KNOWN_STATUS` and `CLOSED` in `audit_common.py`).
- Other actions record only `ok`, except `merge` and `fix`, which also allow `failed` and `blocked`, and `exclude`, which also allows `blocked` (see `KNOWN_STATUS` in `audit_common.py`).
- Severity: critical, high, medium, low. Open issues sort by severity, then by days open.

## Related projects

Three parts of one workflow — rules, then tiers, then a paper trail:

- [workflow-skills](https://github.com/kttcat/workflow-skills) — the rules: nine learned workflow skills.
- [tiered-review](https://github.com/kttcat/tiered-review) — the tiers: three-tier approval framework for AI agents.
- [sqlite-audit-log](https://github.com/kttcat/sqlite-audit-log) — the paper trail: this repo.

## License

MIT — see [LICENSE](LICENSE).
