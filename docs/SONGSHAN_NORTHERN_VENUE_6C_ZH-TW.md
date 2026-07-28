# 6-C｜北部官方場館來源整合：松山文創園區

## 本階段範圍

- 新增松山文創園區列表與詳情頁 Collector
- 使用官方展演列表 `/exhibition`
- 使用官方活動詳情 `/exhibition/activity/<UUID>`
- 解析標題、展期、時間、子場館、主辦單位、圖片、介紹、票價與外部網址
- 月度展演攻略、課程、論壇、工作坊、營隊、徵件與培訓標記為 `exclude_review`
- 沿用 6-A 批次框架與 6-B 重試、timeout、隔離及健康報告
- 建立 Songshan 專屬來源品質檢查與合併候選 Dry Run

## 安全狀態

- `songshan-cultural-park` 維持 `planned / disabled`
- `cultural-parks-north` 維持 disabled
- 不修改正式活動資料
- 不修改前台
- 不接入正式每日更新
- 6-G 前不自動發布松山候選

## Dry Run

沿用既有 `.github/probe-source-batch.trigger`，Commit message 使用：

`[dry-run-songshan] test: validate Songshan northern venue candidate`

Artifact：

`songshan-north-candidate-<run number>`
