# Exhibition Hub V6.3.2 最後一項 Actions 修正

V6.3.1 已讓原本 6 個失敗降為 1 個。剩餘錯誤來自 PR 測試時合併到 `main` 的較新資料仍含舊網站 Banner；本補丁會先在 GitHub Actions 的暫存工作區清洗圖片，再執行 303 項測試。

## 覆蓋

1. 保持 GitHub Desktop 分支為 `develop`。
2. 點 `Fetch origin`；若變成 `Pull origin`，再點一次。
3. 解壓縮 `Exhibition-Hub-V6.3.2-actions-hotfix.zip`。
4. 按 `Command + Shift + .` 顯示 `.github`。
5. 將補丁內 `exhibition-hub-main` 裡面的全部內容複製到 `/Users/jacky_yu/Documents/GitHub/exhibition-hub`。
6. 選 `全部套用 → 取代`。

## 提交

Changes 應包含：

```text
.github/workflows/validate-develop.yml
.github/workflows/update-exhibitions.yml
tests/test_production_update_workflow.py
tests/test_validate_develop_workflow.py
MANIFEST_V6.3.2.json
REPLACEMENT_GUIDE_V6.3.2_ZH-TW.md
VERSION.txt
```

Summary 輸入：

```text
Fix V6.3.2 pretest image sanitation
```

點 `Commit to develop`，再點 `Push origin`。既有 PR #12 會自動更新；不要重新建立 PR，也不要重新執行舊的紅色工作。

## 通過後

以最新 commit 觸發的 `Validate development changes` 為準。全部綠色後才點 `Merge pull request → Confirm merge`，不要刪除 `develop`。
