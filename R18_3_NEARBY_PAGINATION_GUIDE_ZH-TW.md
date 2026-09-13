# R18.3 附近展場、分頁與目錄同步更新指南

本更新包把兩組修正放在同一個版本：

- R18.3 介面修正：「顯示更多展覽」採增量加入，不再重繪整個清單；附近展場改為 3 公里；可點地圖標記切換搜尋中心，並可回到目前位置；Pages 一併帶上 `data/geocode-cache.json`。
- PR #67 資料一致性修正：恢復 canonical `data/exhibitions.curated.json` 的完整 675 筆資料，並同步 `stats.categoryCounts` 與 `data/update-reports/category-semantic-audit-r18.json`。這是修正資料，不是把測試期待值改成 576；CI 不應再出現 `576 != 675`。

## 一、開始前先確認 GitHub Desktop

1. 開啟 GitHub Desktop，左上角 **Current Repository** 應是 `exhibition-hub`。
2. 左上角 **Current Branch** 切成 `develop`。
3. 按上方 **Fetch origin**；若按鈕變成 **Pull origin**，再按一次把遠端 `develop` 拉下來。
4. 左側 Changes 必須顯示 **0 changed files**。如果有自己尚未提交的工作，先不要覆蓋更新包，避免遺失。
5. PR #67 舊的紅色檢查不要按 **Re-run** 來當作修正；套用本包並推送新 commit 後，GitHub 會產生新的檢查結果。

## 二、把 ZIP 內容放到正確位置

1. 下載 `exhibition-hub-r18.3-nearby-pagination-fix.zip`。
2. 在 Finder 對 ZIP 按兩下解壓縮。
3. 打開解壓縮後的資料夾，按 `Command+A`、`Command+C`。
4. 在 Finder 開啟專案資料夾：
   `/Users/jacky_yu/Documents/GitHub/exhibition-hub`
5. 在專案資料夾內按 `Command+V`，若詢問是否取代，選 **Replace／取代**。
6. 確認檔案直接落在專案根目錄與下列子目錄，不要把整個解壓縮資料夾再套一層（不要變成 `exhibition-hub/exhibition-hub-r18.3-nearby-pagination-fix/...`）。

### 本包會更新的檔案

| 位置 | 檔案 | 用途 |
|---|---|---|
| 專案根目錄 | `index.html`、`VERSION.txt`、`MANIFEST_V6.5.0_R18_3.json`、本指南 | 版本與前台入口 |
| `assets/` | `app.js`、`styles.css` | 分頁、附近展場與畫面行為 |
| `scripts/` | `build_pages_site.py` | Pages 建置與 geocode cache 發布 |
| `data/` | `exhibitions.curated.json`、`geocode-cache.json` | canonical 675 筆目錄與座標快取 |
| `data/update-reports/` | `category-semantic-audit-r18.json` | 分類會員數與 audit 統計 |
| `tests/` | manifest 列出的 R16/R17/R18.3 測試檔 | 防止資料、分類、票價、分頁回歸 |

`data/exhibitions.curated.json` 與 `data/update-reports/category-semantic-audit-r18.json` 是這次刻意要取代的資料檔。其他由本機爬蟲產生的 `data/exhibitions.json`、`data/exhibitions.enriched.json`、social 或 update-report 檔案不在本包內，請保留原檔。

如果 GitHub Desktop 顯示 `.github/workflows/`、`data/exhibitions.json` 或 `data/exhibitions.enriched.json` 也被意外改動，先停下來，不要提交；那不是本包要求的變更。

## 三、在 GitHub Desktop 提交

1. 回到 GitHub Desktop 的 **Changes**，確認變更主要是上表檔案。
2. Summary 輸入：
   `fix: sync canonical catalog and stabilize nearby discovery R18.3`
3. Description 可輸入：
   `Restore the canonical 675-event curated feed, synchronize taxonomy audit statistics, and include the R18.3 nearby venue and pagination fixes.`
4. 按 **Commit to develop**。
5. 按 **Push origin**。不要在 Terminal 直接執行 `git push`；若畫面要求帳密，按 `Control+C` 回到 GitHub Desktop 推送。

## 四、PR 檢查與合併

1. 開啟 repository 的 Pull requests。若 PR #67 仍然存在，直接等待它因新 commit 自動更新；不要另開重複 PR。
2. PR 的方向確認為 **base: `main` ← compare: `develop`**。
3. 在 Checks 等待新的 commit 對應的 workflow 完成。必須全部綠燈，尤其是 **Run project tests**；不應再看到 `576 != 675`，也不應看到 curated feed 的 categoryCounts 不一致。
4. 只有在顯示 **Able to merge** 且檢查全綠後，才按 **Merge pull request**。舊的紅色 run 不必重跑。

## 五、發布到官網

1. 到 repository 的 **Actions**。
2. 選 **Publish prepared website**（若介面名稱是 `publish-prepared-site.yml`，選同一個 workflow）。
3. 按右上角 **Run workflow**，Branch 選 `main`，再按 **Run workflow**。
4. 等待 run 顯示 **Success**，再用瀏覽器開 `https://twexhibition.com/`。
5. 用 `Command+Shift+R` 強制重新整理，避免舊 JavaScript 快取。

## 六、上線後快速驗證

- 探索頁連按「顯示更多展覽」約 4 次：既有卡片不可消失，清單數量應逐次增加。
- 附近頁允許定位後：標題與說明應是「附近展場」，只列使用者位置 3 公里內的展場。
- 點地圖標記：右側清單與圓形範圍應改以該標記為中心，顯示該點 3 公里內展場。
- 按「回到目前位置」：搜尋中心、距離與清單應回到使用者位置。
- 任一分類頁的清單與展覽詳情分類要一致；動漫分類應包含資料中的 23 筆動漫會員事件。
- 需要購票的展覽卡片與詳情應統一顯示「票價請見活動頁面」。

## 七、出問題時怎麼回復

- 尚未提交：只針對本包檔案按右鍵 **Discard Changes**；不要丟掉其他自己的修改。
- 已提交但尚未推送：使用 GitHub Desktop 的 **Branch → Undo Last Commit**。
- 已推送或已合併：在原 PR 的選單選 **Revert**，讓 GitHub 建立復原 PR；等待復原 PR 檢查全綠後再合併。不要用 force push 或硬重設遠端分支。
- Actions 失敗：先記下失敗的 workflow、job 與錯誤行，不要連續重跑同一個舊 run。
