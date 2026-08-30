# R15 GitHub 低資源週更啟用指南

這個版本依 GitHub Support 的回覆，把原本多個 cron 與四個平行 runner 改成單一週更工作。帳號目前已恢復完整權限；GitHub 並未要求等待特定天數，但舊排程不可重新啟用。

## 新版會怎麼運作

- 每週只執行一次：台灣時間星期日 03:17。
- 全程只有一個 GitHub runner，沒有 matrix 或平行 job。
- 同一時間只能有一次週更；新執行會取消仍未完成的舊執行。
- 最長 55 分鐘，超時便停止。
- 文化部清單仍會完整掃描，但深入抓取限制為 80 個詳情、80 個圖片來源及 15 筆地理編碼。
- 官方場館依序處理，不會同時啟動多個 runner。
- 資料未通過 500 筆最低量、異常刪除、來源品質及圖片安全門檻時，不會 Commit 或部署。
- 成功時自動 Commit 到 `main`、更新展覽與場館數、寫入最新更新時間並部署官網。
- 失敗時主要正式資料會自動還原，不會發布半成品。

## 安裝更新包

1. 在 GitHub Desktop 切到 `develop`，先按 `Fetch origin`／`Pull origin`。
2. `Repository` → `Show in Finder`。
3. 將更新包「裡面的全部內容」拖進 `exhibition-hub` 根目錄並選擇合併／取代。
4. GitHub Desktop 的 Summary 輸入：

   `feat: add guarded low-resource weekly automation`

5. Commit 到 `develop` 並 Push。
6. 建立 `develop → main` Pull Request，等所有檢查變綠後 Merge。

## 第一次受控測試

先不要建立啟用變數。這樣即使 workflow 已啟用，排程也只會顯示為略過，不會取得 runner。

1. GitHub → `Actions`。
2. 左側選 `Weekly exhibition update (low resource)`。
3. 若畫面顯示停用，按 `Enable workflow`。只啟用這一個。
4. 按 `Run workflow`，Branch 選 `main`。
5. 在確認欄輸入：`RUN_WEEKLY_UPDATE`。
6. 再按綠色 `Run workflow`，等候綠色勾勾。
7. 成功後開啟官網，確認更新時間、展覽數、展演場館數與展覽內容。

這次受控測試成功時，不必再執行 `Publish prepared website`；同一個週更工作已經完成資料 Commit 與 Pages 部署。

## 開啟每週自動執行

只有第一次受控測試成功後才做：

1. GitHub repository → `Settings`。
2. `Secrets and variables` → `Actions`。
3. 選 `Variables` → `New repository variable`。
4. Name：`WEEKLY_UPDATE_ENABLED`
5. Value：`true`
6. 儲存。

之後會在台灣時間每週日 03:17 自動更新及部署，不需要留著 Mac，也不必人工按發布。

## 暫停與復原

- 要暫停自動週更：將 `WEEKLY_UPDATE_ENABLED` 改為 `false` 或刪除該變數。
- 不要重新啟用舊的 `Update data and deploy site`、C2、C3 review、C4、Collector dry run 或 Social discovery 排程。新版程式已移除它們的 cron，但仍保留手動診斷功能。
- 若第一次測試失敗，不要按 `Re-run all jobs`。先保留該次畫面與失敗步驟，再修正後啟動新的受控測試。
