# 6-A｜通用官方來源批次執行器

## 目的

將官方來源的執行方式從「每一個來源複製一份 Workflow」
改成由 `data/source_batches.json` 統一管理。

後續新增場館時，主要調整：

- `data/source_registry.json`
- `data/source_batches.json`
- 對應 Collector

不再為每個場館建立一整套獨立 Workflow。

## 本階段功能

- 讀取批次與區域設定
- 驗證批次 ID、區域 ID、來源 ID 與數量上限
- 按批次順序執行已啟用來源
- 停用／規劃中來源自動跳過
- 每個來源輸出獨立 JSON
- 產生批次總報告與合併 records
- 支援 `isolate_source` 基礎失敗隔離
- 支援嚴格模式，在任何來源失敗時回傳非零狀態

## 第一個啟用批次

`active-official-venues`

目前包含：

- `huashan-1914`

松山、駁二與售票平台等未完成 Collector 的來源仍留在
未啟用批次，不會影響正式資料或本次 Dry Run。

## 本階段不會做的事

- 不新增新的場館來源
- 不修改正式活動資料
- 不修改前台
- 不把批次執行器接入正式每日發布
- 不啟用松山、駁二或 OPENTIX

## 後續

6-B 會強化來源級重試、逾時、失敗隔離與批次健康摘要；
6-C 起再逐區加入新官方場館 Collector。
