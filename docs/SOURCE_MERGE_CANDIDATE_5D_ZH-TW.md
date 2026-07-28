# 5-D｜官方來源去重與候選合併

## 目的

將華山官方 Collector 輸出與目前
`data/exhibitions.enriched.json` 比對，但只建立候選檔，
不修改正式網站資料。

## 判斷結果

- `auto_merge`：標題、日期、場館或官方來源參照足夠一致
- `needs_review`：疑似同一活動，但仍需人工確認
- `new_event`：沒有可信的既有活動配對

## 合併優先級

官方場館來源可補足：

- 官方網址
- 主視覺
- 活動介紹
- 票價與免費／付費
- 主辦單位
- 細部展館
- 活動時間

既有活動 ID、瀏覽熱度與第一次出現時間會保留。

## 第 6 階段擴充設計

去重器不綁定華山，任何 Collector 只要輸出統一
`CollectorRecord` 就能使用。

`data/source_batches.json` 將來源拆為：

- 區域群組
- 來源批次
- 主辦方擴充欄位
- 單一來源失敗隔離

未來新增松山、世貿、南港、駁二、地方場館或主辦方，
主要新增來源設定與 Collector，不需要複製整份 Workflow。

## 發布狀態

`published: false`

本階段不修改：

- `data/exhibitions.json`
- `data/exhibitions.enriched.json`
- 正式網站活動數
