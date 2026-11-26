#!/usr/bin/env python3
"""sqlite-audit-log 的最小測試（只用標準庫 unittest，不用新依賴）。

跑法（在 repo 根目錄）：
    python3 -m unittest test_audit.py -v
    或 python3 test_audit.py

覆蓋三件事：
(a) trigger 真的擋 UPDATE／DELETE；
(b) validate_audit.py 對未知 action／非法 status 回 exit 1；
(c) 最新一列為準＋overdue 邊界（滿 7 個整天不標，第 8 天起標）。
"""
import io
import os
import sqlite3
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import audit_common  # noqa: E402
import validate_audit  # noqa: E402
from audit_common import connect, open_issues  # noqa: E402

SCHEMA = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql")).read()


def ts(days_ago):
    """N 天前（多 1 小時，避免邊界抖動）的 UTC 時間字串。"""
    return (datetime.now(timezone.utc) - timedelta(days=days_ago, hours=1)).strftime("%Y-%m-%d %H:%M:%S")


def insert(con, action, batch_id, status, severity=None, detail="test", created_at=None):
    con.execute(
        "INSERT INTO audit_log (action, detail, actor, batch_id, status, severity, created_at)"
        " VALUES (?, ?, 'test', ?, ?, ?, ?)",
        (action, detail, batch_id, status, severity,
         created_at or datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")),
    )
    con.commit()


class TestAppendOnly(unittest.TestCase):
    def test_update_blocked(self):
        con = connect(":memory:")
        con.executescript(SCHEMA)
        insert(con, "incident", "B1", "open", "high")
        with self.assertRaises(sqlite3.IntegrityError):
            con.execute("UPDATE audit_log SET status='resolved' WHERE id=1")

    def test_delete_blocked(self):
        con = connect(":memory:")
        con.executescript(SCHEMA)
        insert(con, "incident", "B1", "open", "high")
        with self.assertRaises(sqlite3.IntegrityError):
            con.execute("DELETE FROM audit_log WHERE id=1")


class TestValidate(unittest.TestCase):
    def _run_validate(self, setup):
        """在臨時檔案 DB 上跑 validate_audit.main()，回傳 exit code 與輸出。"""
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "audit.sqlite")
            con = connect(path)
            con.executescript(SCHEMA)
            setup(con)
            con.close()
            old_argv = sys.argv
            sys.argv = ["validate_audit.py", "--db", path]
            try:
                buf = io.StringIO()
                with redirect_stdout(buf):
                    code = validate_audit.main()
                return code, buf.getvalue()
            finally:
                sys.argv = old_argv

    def test_unknown_action_exits_1(self):
        def setup(con):
            insert(con, "made_up_action", None, "ok")
        code, out = self._run_validate(setup)
        self.assertEqual(code, 1)
        self.assertIn("未知 action", out)

    def test_illegal_status_exits_1(self):
        def setup(con):
            insert(con, "dedup", None, "failed")  # dedup 只允許 ok
        code, out = self._run_validate(setup)
        self.assertEqual(code, 1)
        self.assertIn("不在允許範圍", out)

    def test_clean_db_exits_0(self):
        def setup(con):
            insert(con, "incident", "B1", "open", "high")
            insert(con, "merge", None, "ok")
        code, _ = self._run_validate(setup)
        self.assertEqual(code, 0)


class TestLatestAndOverdue(unittest.TestCase):
    def test_latest_row_wins(self):
        con = connect(":memory:")
        con.executescript(SCHEMA)
        insert(con, "incident", "B1", "open", "high", created_at=ts(3))
        insert(con, "incident", "B1", "resolved", "high", created_at=ts(1))
        items = open_issues(con)
        self.assertEqual([i["batch_id"] for i in items], [])

    def test_overdue_boundary(self):
        con = connect(":memory:")
        con.executescript(SCHEMA)
        insert(con, "incident", "B7", "open", "high", created_at=ts(7))  # 滿 7 個整天：不標
        insert(con, "incident", "B8", "open", "high", created_at=ts(8))  # 第 8 天：標
        by_bid = {i["batch_id"]: i for i in open_issues(con)}
        self.assertFalse(by_bid["B7"]["overdue"])
        self.assertEqual(by_bid["B7"]["days_open"], 7)
        self.assertTrue(by_bid["B8"]["overdue"])
        self.assertEqual(by_bid["B8"]["days_open"], 8)

    def test_null_batch_severity_does_not_leak(self):
        con = connect(":memory:")
        con.executescript(SCHEMA)
        insert(con, "incident", None, "open", "critical", detail="有 severity")
        insert(con, "incident", None, "open", None, detail="無 severity")
        by_detail = {i["detail"]: i for i in open_issues(con)}
        self.assertEqual(by_detail["有 severity"]["severity"], "critical")
        self.assertIsNone(by_detail["無 severity"]["severity"])


if __name__ == "__main__":
    unittest.main()
