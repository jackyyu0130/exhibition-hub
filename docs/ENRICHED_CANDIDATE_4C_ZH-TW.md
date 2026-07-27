# 4-C｜產生網站候選資料

本階段不會覆寫正式網站的 `data/exhibitions.json`。

Workflow 會從 `main` 讀取最新正式資料，並產生可供檢查的
`exhibitions.enriched.candidate.json` Artifact。

## 發布政策

- `candidate`：保留
- `needs_review`：保留並維持審查標記
- `exclude_review`：不放入候選活動清單，另存至審查檔

依 `event-registry-dry-run-67` 的基準，預期：

- 正式來源活動：2,428
- 候選活動：2,424
- `candidate`：2,320
- `needs_review`：104
- 排除審查：4
- 已解析場館活動：1,241
- 多場館活動：107

## Artifact 檔案

- `production-data-baseline.json`
- `exhibitions.enriched.candidate.json`
- `enriched-candidate-report.json`
- `excluded-events-review.json`
- `enriched-candidate-summary.json`

## 第一次提交

上傳本包後使用：

`feat: add enriched candidate build`

第一次不要加入 `[build-enriched]`。

## 正式觸發

先確認一般測試通過，再編輯：

`.github/probe-enriched-candidate.trigger`

將 `Run: 1` 改成 `Run: 2`，Commit message：

`[build-enriched] test: generate production enriched candidate`

## 安全性

- 不覆寫 `data/exhibitions.json`
- 不部署 GitHub Pages
- 不修改 `main`
- Artifact 僅保留 7 天
