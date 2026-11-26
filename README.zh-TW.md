# sqlite-audit-log

English 版本請見 [README.md](README.md)。

只追加的 SQLite 稽核紀錄，附受控詞彙和批次問題追蹤。

三支小工具，共用同一個模組：

- `audit_common.py` — 唯一的真相來源：action／status 詞彙、狀態機、嚴重度排序、時間解析，還有查每批最新狀態和未結案問題的查詢。
- `validate_audit.py` — 檢查每一筆的 action、status、severity 有沒有落在受控詞彙裡；有錯就回傳 exit code 1。
- `issue_stats.py` — 統計每批的最新狀態；未結案的問題按嚴重度排，放超過 7 個整天（第 8 天起）就標 `[OVERDUE 超期Nd天]`。

## 紀錄

`audit_log` 這張表只能追加：trigger 會擋掉 UPDATE 和 DELETE。狀態要變，就用同一個 `batch_id` 再寫一筆新的，最新那筆為準。資料表和 trigger 的定義在 `schema.sql`。詞彙由 `validate_audit.py` 檢查，不由資料庫強制——trigger 只擋 UPDATE 和 DELETE。

## 使用方式

```bash
sqlite3 audit.sqlite < schema.sql
export AUDIT_DB=audit.sqlite        # 或用 --db audit.sqlite
python3 validate_audit.py --db audit.sqlite
python3 issue_stats.py --db audit.sqlite
```

跑測試（只用標準庫 `unittest`，in-memory DB）：

```bash
python3 -m unittest test_audit.py -v
```

示範資料：`sqlite3 audit.sqlite < examples/seed.sql`（預期輸出見檔案開頭的註解）。不要提交產生的 `audit.sqlite` 檔。

## 詞彙

- 問題分五種：incident、problem、enquiry、risk、change。每一種能用的狀態和什麼算結案都不一樣（看 `audit_common.py` 裡的 `KNOWN_STATUS` 和 `CLOSED`）。
- 其他 action 只記 ok，只有 merge、fix 另外可以記 failed、blocked，exclude 另外可以記 blocked（看 `audit_common.py` 裡的 `KNOWN_STATUS`）。
- 嚴重度分四級：critical、high、medium、low。未結案的問題先按嚴重度排，再按放了幾天排。

## 相關專案

同一套流程的三個部分——規範、分級、留痕：

- [workflow-skills](https://github.com/kttcat/workflow-skills) — 規範：九支學回來的工作流程 skills。
- [tiered-review](https://github.com/kttcat/tiered-review) — 分級：AI agent 三級審查框架。
- [sqlite-audit-log](https://github.com/kttcat/sqlite-audit-log) — 留痕：這個 repo。

## 授權

MIT — 見 [LICENSE](LICENSE)。
