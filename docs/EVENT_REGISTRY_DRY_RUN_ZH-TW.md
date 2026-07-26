# 4-B｜現有活動套用場館主檔與內容分類

本階段只產生 Dry Run 報告和選用的預覽檔，不會覆寫
`data/exhibitions.json`。

## 執行方式

在專案根目錄執行：

```bash
python scripts/apply_event_registry.py \
  --report-output build/event-registry-report.json \
  --preview-output build/exhibitions-registry-preview.json
```

只看終端報告、不建立預覽檔：

```bash
python scripts/apply_event_registry.py
```

## 新增的預覽欄位

每筆活動會在複製版本中新增：

- `regionCanonical`
- `venueId`
- `venueName`
- `venueMatchConfidence`
- `contentType`
- `contentTypes`
- `eventFormat`
- `editorialStatus`
- `editorialFlags`

原本的 `locationName`、`region`、`category` 等欄位不會被覆寫。

## 場館配對順序

1. 特殊場館與地區判定，例如故宮北院／南院。
2. 新版 `data/venues.json` 完整別名比對。
3. 舊版 `data/venue-aliases.json` 相容別名。
4. 場館子空間包含比對，例如「臺北流行音樂中心文化館」配對到北流。
5. 無法安全判斷的活動保留為 unmatched，不猜測。

## 編輯狀態

- `candidate`：可作為網站候選活動。
- `needs_review`：線上活動或場館仍是暫時名稱。
- `exclude_review`：疑似課程、工作坊、講座、論壇或商品，等待排除確認。

這些狀態只用於報告，不會在本階段自動刪除資料。
