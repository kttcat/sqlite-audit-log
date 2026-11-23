# sqlite-audit-log

English 版本請見 [README.md](README.md)。

只追加的 SQLite 稽核紀錄，搭配受控詞彙與批次問題追蹤。

三支共用同一模組的小工具：

- `audit_common.py` — 單一真相來源：action／status 詞彙、狀態機、嚴重度排序、時間解析，以及每批次最新狀態與未結案問題的查詢。
- `validate_audit.py` — 檢查每一列的 action、status、severity 是否在受控詞彙內，有錯就以 exit code 1 離開。
- `issue_stats.py` — 每批次最新狀態統計；未結案問題按嚴重度列出，超過 7 天標 `[OVERDUE]`。

## 紀錄

`audit_log` 資料表是只追加的：trigger 擋下 UPDATE 與 DELETE。狀態變化就是用同一個 `batch_id` 新增一列，最新那列為準。資料表與 trigger 見 `schema.sql`。

## 使用方式

```bash
sqlite3 audit.sqlite < schema.sql
export AUDIT_DB=audit.sqlite        # 或用 --db audit.sqlite
python3 validate_audit.py --db audit.sqlite
python3 issue_stats.py --db audit.sqlite
```

## 詞彙

- 問題類型：incident、problem、enquiry、risk、change。各有自己的允許狀態與結案狀態（見 `audit_common.py` 裡的 `KNOWN_STATUS` 與 `CLOSED`）。
- 其他 action（merge、fix、dedup、policy、approve 等）只記 ok／failed／blocked。
- 嚴重度：critical、high、medium、low。未結案問題先按嚴重度排，再按開了幾天排。

## 授權

MIT — 見 [LICENSE](LICENSE)。
