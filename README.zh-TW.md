# sqlite-audit-log

English 版本請見 [README.md](README.md)。

只追加的 SQLite 稽核紀錄，附受控詞彙和批次問題追蹤。

三支小工具，共用同一個模組：

- `audit_common.py` — 唯一的真相來源：action／status 詞彙、狀態機、嚴重度排序、時間解析，還有查每批最新狀態和未結案問題的查詢。
- `validate_audit.py` — 檢查每一筆的 action、status、severity 有沒有落在受控詞彙裡；有錯就回傳 exit code 1。
- `issue_stats.py` — 統計每批的最新狀態；未結案的問題按嚴重度排，超過 7 天就標 `[OVERDUE]`。

## 紀錄

`audit_log` 這張表只能追加：trigger 會擋掉 UPDATE 和 DELETE。狀態要變，就用同一個 `batch_id` 再寫一筆新的，最新那筆為準。資料表和 trigger 的定義在 `schema.sql`。

## 使用方式

```bash
sqlite3 audit.sqlite < schema.sql
export AUDIT_DB=audit.sqlite        # 或用 --db audit.sqlite
python3 validate_audit.py --db audit.sqlite
python3 issue_stats.py --db audit.sqlite
```

## 詞彙

- 問題分五種：incident、problem、enquiry、risk、change。每一種能用的狀態和什麼算結案都不一樣（看 `audit_common.py` 裡的 `KNOWN_STATUS` 和 `CLOSED`）。
- 其他 action（merge、fix、dedup、policy、approve 等）只記 ok／failed／blocked。
- 嚴重度分四級：critical、high、medium、low。未結案的問題先按嚴重度排，再按放了幾天排。

## 授權

MIT — 見 [LICENSE](LICENSE)。
