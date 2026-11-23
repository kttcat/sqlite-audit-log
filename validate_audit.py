#!/usr/bin/env python3
"""檢查 audit_log 的 action / status / severity 是否在受控詞彙內。

- action 不在已知清單 → ERROR（自創 action 要先更新 audit_common.KNOWN_STATUS 再使用）
- issue 類只驗每 batch_id 最新一列的 status（舊列視為作廢）；其他 action 逐列驗
- severity 有值但不在 critical/high/medium/low → ERROR
- incident/problem/enquiry/risk/change 缺 batch_id → WARNING
- incident/problem/enquiry/risk 缺 severity → WARNING
- created_at 非慣用格式 → WARNING
有 ERROR 時 exit code 1。合併後、每週報告前各跑一次。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from audit_common import (  # noqa: E402
    ISSUE_ACTIONS, KNOWN_STATUS, SEV_ACTIONS, SEVERITIES, TS_RE, connect, latest_rows,
)


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=None,
                    help="SQLite DB path (default: $AUDIT_DB or audit.sqlite)")
    args = ap.parse_args()
    con = connect(args.db)
    lat = latest_rows(con)
    latest_ids = {r["id"] for (a, _), r in lat.items() if a in ISSUE_ACTIONS}
    errors, warnings = [], []
    for r in con.execute("SELECT * FROM audit_log ORDER BY id"):
        tag = f"id={r['id']} action={r['action']}"
        if not TS_RE.match(r["created_at"] or ""):
            warnings.append(f"{tag}：created_at 格式非慣用（應為 YYYY-MM-DD HH:MM:SS UTC）")
        if r["action"] not in KNOWN_STATUS:
            errors.append(f"{tag}：未知 action（先更新 audit_common.KNOWN_STATUS）")
            continue
        if r["action"] in ISSUE_ACTIONS and r["id"] not in latest_ids:
            pass  # 舊狀態列，已被後列取代，不驗 status
        elif (r["status"] or "") not in KNOWN_STATUS[r["action"]]:
            errors.append(
                f"{tag}：status={r['status']!r} 不在允許範圍 {sorted(KNOWN_STATUS[r['action']])}"
            )
        if r["severity"] is not None and r["severity"] not in SEVERITIES:
            errors.append(f"{tag}：severity={r['severity']!r} 非法，應為 critical/high/medium/low")
        if r["action"] in ISSUE_ACTIONS and not r["batch_id"]:
            warnings.append(f"{tag}：缺 batch_id，無法追蹤狀態變化")
        if r["action"] in SEV_ACTIONS and r["id"] in latest_ids:
            # 該 batch 任一列有 severity 即算有（統計取最新非 NULL 值）
            has = con.execute(
                "SELECT 1 FROM audit_log WHERE action=? AND COALESCE(batch_id,'')=? "
                "AND severity IS NOT NULL LIMIT 1",
                (r["action"], r["batch_id"] or ""),
            ).fetchone()
            if not has:
                warnings.append(f"{tag}：缺 severity，統計時無法排序")
    for w in warnings:
        print("WARNING:", w)
    for e in errors:
        print("ERROR:", e)
    print(f"\n檢查完成：{len(errors)} 個 ERROR，{len(warnings)} 個 WARNING")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
