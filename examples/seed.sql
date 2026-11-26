-- seed.sql — 示範資料：一個 batch 的生命週期
--
-- 用法（在 repo 根目錄）：
--   sqlite3 audit.sqlite < schema.sql
--   sqlite3 audit.sqlite < examples/seed.sql
--   python3 issue_stats.py --db audit.sqlite
--
-- 預期輸出：
--   INC-001 已結案（resolved），不列在未結案；
--   INC-002 未結案，顯示 [已2天][high]。
-- 不要提交產生的 audit.sqlite 二進位檔。

INSERT INTO audit_log (action, detail, actor, batch_id, status, severity, created_at)
VALUES ('incident', '示範：系統告警', 'demo', 'INC-001', 'open', 'high', datetime('now', '-3 days'));
INSERT INTO audit_log (action, detail, actor, batch_id, status, severity, created_at)
VALUES ('incident', '示範：已修復', 'demo', 'INC-001', 'resolved', 'high', datetime('now', '-1 day'));
INSERT INTO audit_log (action, detail, actor, batch_id, status, severity, created_at)
VALUES ('incident', '示範：未結案的問題', 'demo', 'INC-002', 'open', 'high', datetime('now', '-2 days'));
INSERT INTO audit_log (action, detail, actor, batch_id, status, severity, created_at)
VALUES ('merge', '示範：合併紀錄', 'demo', NULL, 'ok', NULL, datetime('now'));
