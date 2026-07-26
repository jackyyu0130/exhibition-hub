# 4-B-2｜高頻未配對場館擴充

本批次根據 `event-registry-dry-run-54` 的完整報告，
將高頻且名稱明確的場館加入 `data/venues.json`。

## 原則

- 不處理「台北市｜場館資料整理中」等 placeholder。
- 分館、廳別與影廳作為母場館 aliases。
- 不改寫 `data/exhibitions.json`。
- 不啟用新 Collector。
- 官方網址尚未驗證的場館先留空，不猜測網址。

## 驗證

提交後先跑一般測試，再將
`.github/probe-event-registry.trigger` 的 `Run` 增加 1，
並使用 `[dry-run-registry]` 重新產生 Artifact。
