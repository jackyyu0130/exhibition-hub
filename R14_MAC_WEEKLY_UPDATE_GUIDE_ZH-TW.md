# 台灣展覽誌 V6.5.0-R14 操作指南

## 這一版完成什麼

- 保留完整展覽爬蟲，不需人工核對 700 多筆展覽。
- 在 Mac 本機一鍵抓取、整合、去重、分類與驗證資料。
- 更新失敗時自動還原主要正式資料。
- 自動產生中文差異摘要，只需確認新增、異動、移除與來源失敗數量。
- 爬蟲完成後自動同步官網 `updatedAt` 更新時間。
- GitHub 只執行一次輕量靜態網站發布，不在 GitHub 上爬資料。
- 補齊瀏覽器分頁及 Google 搜尋需要的 favicon 檔案。
- favicon 使用固定根目錄網址，避免每版變更網址影響 Google 重新辨識。

## 第一次安裝更新包

1. 解壓縮 `exhibition-hub-v6.5.0-r14-local-weekly-favicon.zip`。
2. 開啟解壓縮後的資料夾。
3. 在 Finder 按 `Command + Shift + .`，顯示 `.github` 隱藏資料夾。
4. 開啟你電腦上的 `exhibition-hub` 專案資料夾。
   - 若找不到：開啟 GitHub Desktop。
   - 左上角選擇 `exhibition-hub`。
   - 上方選單點 `Repository` → `Show in Finder`。
5. 將更新包「裡面的全部內容」拖入 `exhibition-hub` 專案根目錄。
6. Finder詢問是否合併資料夾時，選擇「合併」。
7. 詢問相同檔名時，選擇「取代」。
8. 不要刪除專案裡其他未出現在更新包中的檔案。

這次會加入或替換：

- `index.html`
- `assets/app.js`
- `scripts/build_pages_site.py`
- `scripts/run_local_weekly_update.py`
- `scripts/build_favicon_assets.py`
- `run_weekly_update.command`
- `.github/workflows/publish-prepared-site.yml`
- favicon、Apple Touch Icon 與 web manifest
- 對應測試與操作說明

## 第一次先發布 favicon 與新流程

1. 開啟 GitHub Desktop。
2. 左上角確認 repository 是 `exhibition-hub`。
3. 左側確認上述 R14 檔案都在變更清單中。
4. 左下角 Summary 輸入：

   `feat: add local weekly update and favicon deployment`

5. 確認 Current branch 是 `develop`，點 `Commit to develop`。
6. 點上方 `Push origin`。
7. 等 `Validate development changes` 出現綠色勾勾。
8. 建立 `develop → main` Pull Request 並完成合併。
9. 開啟 GitHub 網頁中的 `exhibition-hub`。
10. 點上方 `Actions`。
11. 左側點 `Publish prepared website`。
12. 點右側 `Run workflow`。
13. Branch 保持 `main`。
14. 再點綠色 `Run workflow`。
15. 等工作出現綠色勾勾。

這個 workflow 只會打包並發布網站，不會執行爬蟲、圖片擷取或完整測試。

## 每週執行展覽資料更新

### 1. 先取得網站最新版本

1. 開啟 GitHub Desktop。
2. 左上角選擇 `exhibition-hub`。
3. 確認 Current branch 是 `develop`。
4. 點上方 `Fetch origin`。
5. 如果按鈕變成 `Pull origin`，再點一次 `Pull origin`。
6. 確認左側沒有尚未提交的舊變更。

### 2. 雙擊執行爬蟲

1. GitHub Desktop 上方選單點 `Repository` → `Show in Finder`。
2. 在專案根目錄找到 `run_weekly_update.command`。
3. 第一次執行請按右鍵 →「打開」→ 再按「打開」。
4. 之後每週直接雙擊即可。
5. 第一次會建立專用 Python 環境並安裝元件，時間會比之後久。
6. 更新期間請保持網路連線，不要關閉終端機視窗，也不要讓 Mac 進入睡眠。

程式會自動執行：

1. 備份目前正式資料。
2. 抓取文化部完整活動資料。
3. 產生標準化與場館整合資料。
4. 抓取華山詳情。
5. 抓取所有 `source_registry.json` 中已啟用的官方來源。
6. 自動合併、去重、分類與套用排除規則。
7. 清理不合格圖片及社群連結。
8. 建立官網公開資料。
9. 驗證資料量、日期、ID、圖片與來源連結。
10. 寫入本次官網更新時間。
11. 產生中文摘要。

### 3. 看摘要，不用逐筆核對

成功後會自動開啟：

`local-update-output/latest-summary.md`

摘要會顯示：

- 更新前與更新後筆數
- 更新前與更新後的展演場館數
- 新增筆數
- 內容異動筆數
- 移除或不再發布筆數
- 官方來源成功／失敗數量
- 需要人工確認的筆數
- 前 20 筆新增、異動與移除名稱

以下狀況先不要發布，直接把摘要與錯誤畫面提供給我：

- 展覽總數突然大量下降。
- 移除筆數異常高。
- 多數官方來源同時失敗。
- 程式顯示安全門檻失敗。
- 更新時間沒有變成這次執行時間。

### 4. 一次 Commit 與 Push

1. 回到 GitHub Desktop。
2. 左側檢查變更，正常情況主要會是：
   - `data/exhibitions.json`
   - `data/exhibitions.enriched.json`
   - `data/exhibitions.curated.json`
   - `data/social_discussions.json`
   - `data/geocode-cache.json`
   - `data/update-reports/` 內的最新報告
3. Summary 輸入，例如：

   `data: weekly exhibition update 2026-08-25`

4. 再次確認 Current branch 是 `develop`，點 `Commit to develop`。
5. 點上方 `Push origin`。

### 5. 通過檢查並合併到 main

1. 到 GitHub → `Actions`，確認最新的 `Validate development changes` 是綠色勾勾。
2. 開啟或建立 `develop → main` Pull Request。
3. 確認 Checks 通過後，點 `Merge pull request`。
4. 點 `Confirm merge`。
5. 不要直接把本機資料 Commit 到 `main`。

### 6. 手動發布已準備好的網站

1. 開啟 GitHub repository 網頁。
2. 點 `Actions`。
3. 左側點 `Publish prepared website`。
4. 點 `Run workflow`。
5. Branch 選 `main`。
6. 點綠色 `Run workflow`。
7. 等待綠色勾勾。

不要執行舊的 `Update data and deploy site`。

## 發布後檢查

依序開啟：

- `https://twexhibition.com/`
- `https://twexhibition.com/favicon.ico`
- `https://twexhibition.com/favicon.svg`
- `https://twexhibition.com/favicon-48.png`
- `https://twexhibition.com/site.webmanifest`

確認：

- 首頁能正常載入。
- 展覽筆數合理。
- 展演場館數合理。
- 首頁及頁尾更新時間是本次爬蟲完成時間。
- 瀏覽器分頁不再是地球圖示。
- favicon 網址能直接顯示票券圖示。

若 Chrome 仍顯示舊圖示：

1. 關閉所有 `twexhibition.com` 分頁。
2. 開啟無痕視窗重新進入網站。
3. 或在網址列輸入 `chrome://favicon-internals/` 清除 favicon 快取後重開瀏覽器。

Google 搜尋結果不會立即更新。正式 favicon 可讀取後，再到 Google Search Console：

1. 上方輸入 `https://twexhibition.com/`。
2. 點「測試實際網址」。
3. 測試完成後點「要求建立索引」。
4. 等 Google 再次檢索，通常需要數天或更久。

## 更新失敗時

本機更新任何一步失敗時，程式會自動還原以下主要正式資料：

- `data/exhibitions.json`
- `data/exhibitions.enriched.json`
- `data/exhibitions.curated.json`
- `data/social_discussions.json`
- `data/geocode-cache.json`

錯誤紀錄位於：

`local-update-output/執行日期時間/update.log`

失敗後不要 Commit 或 Push，將終端機錯誤畫面與該次 `update.log` 提供給我。

## 已發布版本需要復原時

1. 開啟 GitHub Desktop。
2. 點上方 `History`。
3. 找到造成問題的最新 Commit。
4. 右鍵點該 Commit。
5. 選擇 `Revert Changes in Commit`。
6. 確認產生新的 Revert Commit。
7. 點 `Push origin`。
8. 等檢查通過後，將 `develop → main` Pull Request 合併。
9. 回到 GitHub Actions，再執行一次 `Publish prepared website`。

這會以新的反向 Commit 復原，不會刪除 GitHub 歷史紀錄。

## 必須繼續保持停用的舊 workflow

- `C2 venue collectors dry run`
- `C3 candidate review artifact`
- `C4 monitored sources and venue matching`
- `Collector stage 7 dry run`
- `Social discovery review artifact`
- `Update data and deploy site`

R14 不會重新啟用以上任何一個 workflow。
