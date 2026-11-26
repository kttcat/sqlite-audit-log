"""audit_log 共用邏輯：單一來源（single source of truth）。

issue_stats.py、validate_audit.py 都從這裡 import；
改詞彙、改狀態機、改排序，只改這一個檔。
"""
import os
import re
import sqlite3
from datetime import datetime, timezone

DB = os.environ.get("AUDIT_DB", "audit.sqlite")
OVERDUE_DAYS = 7

# 五種追蹤對象
ACTIONS = ["incident", "problem", "enquiry", "risk", "change"]
ISSUE_ACTIONS = set(ACTIONS)  # 狀態靠追加演進的 action

CN = {
    "incident": "事件 incident（意外）",
    "problem": "問題 problem（發現有問題的）",
    "enquiry": "詢問 enquiry（不確定的事）",
    "risk": "風險 risk",
    "change": "變更 change",
}

# action → 允許的 status（受控詞彙）
KNOWN_STATUS = {
    "incident": {"open", "resolved"},
    "problem": {"open", "resolved"},
    "enquiry": {"open", "answered"},
    "risk": {"open", "mitigated", "accepted"},
    "change": {"planned", "done", "rolled_back"},
    "merge": {"ok", "failed", "blocked"},
    "fix": {"ok", "failed", "blocked"},
    "dedup": {"ok"},
    "policy": {"ok"},
    "policy_change": {"ok"},
    "approve": {"ok"},
    "exclude": {"ok", "blocked"},
    "note": {"ok"},
    "caption_fix": {"ok"},
    "bucket_fix": {"ok"},
    "qa_decision": {"ok"},
}

# action → 結案狀態（其餘視為未結案）
CLOSED = {
    "incident": {"resolved"},
    "problem": {"resolved"},
    "enquiry": {"answered"},
    "risk": {"mitigated", "accepted"},
    "change": {"done", "rolled_back"},
}

SEVERITIES = {"critical", "high", "medium", "low"}
SEV_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}
SEV_ACTIONS = {"incident", "problem", "enquiry", "risk"}  # 建檔時必填 severity

TS_RE = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")  # 慣用格式，一律 UTC


def parse_ts(s):
    """created_at 一律 UTC；容忍慣用格式與 ISO-8601（別的線曾寫入後者）。"""
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            return datetime.strptime(s, fmt).replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            continue
    raise ValueError(f"無法解析時間格式：{s}")


def connect(db=None):
    con = sqlite3.connect(db or DB)
    con.row_factory = sqlite3.Row
    return con


def latest_rows(con):
    """每 (action, batch_id) 最新一列。issue 類的狀態以此為準。

    batch_id 為 NULL 的列視為各自獨立（key 用 id 區分），不互相覆蓋。
    """
    out = {}
    for r in con.execute("SELECT * FROM audit_log ORDER BY id"):
        key = (r["action"], r["batch_id"]) if r["batch_id"] else (r["action"], f"id:{r['id']}")
        out[key] = r
    return out


def _latest_severity(con, action, batch_id, row_id=None):
    """該 batch 最新一筆非 NULL severity（建立時填，之後可重估）。

    batch_id 為 NULL 的列只看自己這一列（按 id），不撈同 action 其他
    無 batch_id 列的 severity。
    """
    if batch_id:
        r = con.execute(
            "SELECT severity FROM audit_log WHERE action=? AND batch_id=? "
            "AND severity IS NOT NULL ORDER BY id DESC LIMIT 1",
            (action, batch_id),
        ).fetchone()
    else:
        r = con.execute(
            "SELECT severity FROM audit_log WHERE id=? AND severity IS NOT NULL",
            (row_id,),
        ).fetchone()
    return r["severity"] if r else None


def open_issues(con):
    """未結案的 issue 類項目（取最新狀態），按嚴重度排序。

    回傳 dict 串列：action, batch_id, status, severity, days_open, overdue, detail。
    """
    now = datetime.now(timezone.utc)
    lat = latest_rows(con)
    items = []
    for (action, _bid), r in lat.items():
        if action not in ISSUE_ACTIONS:
            continue
        if (r["status"] or "") in CLOSED[action]:
            continue
        bid = r["batch_id"] or ""
        if bid:
            first = con.execute(
                "SELECT MIN(created_at) AS t, "
                "(SELECT detail FROM audit_log a2 WHERE a2.action=? "
                "AND a2.batch_id=? ORDER BY a2.id DESC LIMIT 1) AS d "
                "FROM audit_log WHERE action=? AND batch_id=?",
                (action, bid, action, bid),
            ).fetchone()
            detail = first["d"] or ""
            opened = first["t"]
        else:
            # 無 batch_id：只看自己這一列
            detail = r["detail"] or ""
            opened = r["created_at"]
        days = (now - parse_ts(opened)).days
        items.append({
            "action": action,
            "batch_id": bid or f"(無 batch_id, id={r['id']})",
            "status": r["status"],
            "severity": _latest_severity(con, action, bid, r["id"]),
            "days_open": days,
            "overdue": days > OVERDUE_DAYS,
            "detail": detail.replace("\n", " "),
        })
    items.sort(key=lambda x: (SEV_ORDER.get(x["severity"], 9), -x["days_open"]))
    return items


def is_closed(action, status):
    return (status or "") in CLOSED.get(action, set())
