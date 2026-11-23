#!/usr/bin/env python3
"""統計 audit_log 中的 incident / problem / enquiry / risk / change。

同一 batch_id 只取最新一列的狀態（audit_log 只追加不改寫）。
open 的項目按嚴重度排序逐條列出；超過 7 天標 [OVERDUE]。
詞彙與規則見 audit_common.py（單一來源）。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from audit_common import ACTIONS, CN, CLOSED, connect, open_issues  # noqa: E402


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=None,
                    help="SQLite DB path (default: $AUDIT_DB or audit.sqlite)")
    args = ap.parse_args()
    con = connect(args.db)
    opens = open_issues(con)
    by_action = {}
    for it in opens:
        by_action.setdefault(it["action"], []).append(it)
    total_open = len(opens)
    for action in ACTIONS:
        rows = con.execute(
            "SELECT COUNT(*) AS c FROM audit_log WHERE action=?", (action,)
        ).fetchone()["c"]
        if not rows:
            print(f"=== {CN[action]}：無紀錄 ===")
            continue
        # 各狀態計數（取最新狀態）
        seen = {}
        for r in con.execute("SELECT * FROM audit_log WHERE action=? ORDER BY id", (action,)):
            key = r["batch_id"] if r["batch_id"] else f"id:{r['id']}"
            seen[key] = r["status"]
        by_status = {}
        for st in seen.values():
            st = st or "(未填)"
            by_status[st] = by_status.get(st, 0) + 1
        stat = "、".join(f"{k}:{v}" for k, v in sorted(by_status.items()))
        print(f"=== {CN[action]}（{stat}）===")
        items = by_action.get(action, [])
        for it in items:
            sev = it["severity"] or "未分級"
            flag = f"[OVERDUE 超期{it['days_open']}天]" if it["overdue"] else f"[已{it['days_open']}天]"
            d = it["detail"]
            if len(d) > 80:
                d = d[:80] + "…"
            print(f"  {flag}[{sev}] {it['batch_id']}：{d}")
        if not items:
            print("  （無未結案）")
    print(f"\n未結案總數：{total_open}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
