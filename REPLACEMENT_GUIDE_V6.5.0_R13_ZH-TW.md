# Exhibition Hub V6.5.0-R13 完整替換、檢查與復原指南

## 1. 本次效果

- Google 與瀏覽器使用固定根目錄圖示，不再只依賴帶版本參數的舊圖示。
- 網站標題固定為「台灣展覽誌｜全台展覽與演出資訊」。
- 新增臺北世貿一館官方檔期來源；只解析一館，不混入南港館或歷史三館。
- 新增花博公園爭艷館官方活動來源；只保留場地明確相符的活動。
- 花博民國年日期自動轉為西元年，官方活動圖優先保留。
- 空白圖片網址、HTML 詳情頁、Logo、圖示、載入圖與社群圖不會再被當成展覽圖片。
- Facebook／Instagram 不啟用；講座、課程、工作坊、營隊、研習、講習與說明會維持排除或送審。
- 任一新來源失敗時只隔離該來源，不能清除既有正式活動。

> 世貿三館已結束營運，因此本版只保留歷史場館標記，不建立現行爬蟲。

## 2. 更新前確認

1. 開啟 GitHub Desktop。
2. 左上 `Current Repository` 選 `exhibition-hub`。
3. 中上 `Current Branch` 選 `develop`。
4. 點上方 `Fetch origin`。
5. 確認左側顯示 `0 changed files`。若不是 0，先不要覆蓋；先提交或備份既有變更。
6. 點選單 `Repository` → `Show in Finder`。
7. Finder 中的 repository 根目錄通常是：

   `/Users/jacky_yu/Documents/GitHub/exhibition-hub/`

## 3. 建立可復原備份

1. 在 Finder 選取 `exhibition-hub` 資料夾。
2. 按 `Command + D` 複製一份。
3. 將副本命名為：

   `exhibition-hub-before-V6.5.0-R13`

4. 備份資料夾不要放回原 repository 裡。

## 4. 放置完整替換包

1. 雙擊 `Exhibition-Hub-V6.5.0-R13-full-replacement.zip` 解壓縮。
2. 打開解壓縮後的資料夾。
3. 按 `Command + A` 選取「裡面的全部檔案與資料夾」。
4. 拖曳到：

   `/Users/jacky_yu/Documents/GitHub/exhibition-hub/`

5. macOS 詢問時選 `Replace／取代` 或 `Apply to All／全部套用`。
6. 不要刪除 repository 裡的 `.git`。
7. 不要把 `Exhibition-Hub-V6.5.0-R13-full-replacement` 最外層資料夾放進 repository；必須複製其「內部內容」。

完成後，以下檔案應位於根目錄：

- `index.html`
- `favicon.ico`
- `favicon-48.png`
- `apple-touch-icon.png`
- `logo-512.png`
- `MANIFEST_V6.5.0_R13.json`
- `VERSION.txt`

Collector 檔案路徑：

- `scripts/exhibition_hub/collectors/official_sites.py`
- `scripts/exhibition_hub/collectors/__init__.py`
- `data/source_registry.json`
- `data/venues.json`
- `data/northern_venue_matrix.json`

## 5. GitHub Desktop 提交

1. 回到 GitHub Desktop。
2. 左側 `Changes` 應顯示多個檔案；確認不是 `0 changed files`。
3. 左下 `Summary (required)` 輸入：

   `Apply Exhibition Hub V6.5.0-R13 SEO and official venue sources`

4. `Description` 可留白。
5. 點左下 `Commit to develop`。
6. 等提交完成後，點上方 `Push origin`。

### 若顯示 Newer Commits on Remote

1. 點 `Fetch`。
2. 再點 `Pull origin`。
3. 若沒有衝突，再點 `Push origin`。
4. 若出現大量 `data/exhibitions*.json` 衝突，先按 `Abort Merge`，不要逐筆手動合併；回到備份狀態後重新套用本包。

## 6. 建立 Pull Request

1. 在 GitHub Desktop 點 `Preview Pull Request`。
2. 瀏覽器開啟後確認：
   - `base: main`
   - `compare: develop`
3. PR 標題輸入：

   `Apply Exhibition Hub V6.5.0-R13 SEO and official venue sources`

4. 點綠色 `Create pull request`。
5. 等待 `Checks`；所有必要檢查必須為綠色。
6. 若出現紅色，先開啟失敗項目並保存完整錯誤畫面，不要強制合併。
7. 全綠後依序點：
   - `Merge pull request`
   - `Confirm merge`

## 7. 部署正式站

1. 回到 repository 上方 `Actions`。
2. 左側點 `Update data and deploy site`。
3. 合併後通常會自動產生 `main` 工作。
4. 若沒有自動出現：
   - 點右側 `Run workflow`
   - `Branch` 選 `main`
   - 再點綠色 `Run workflow`
5. 等 `update-and-deploy` 顯示綠色勾勾與 `Success`。
6. 開啟 `https://twexhibition.com/`。
7. 按 `Command + Shift + R` 強制重新整理。

## 8. 上線後逐項檢查

### 網站與搜尋識別

1. 瀏覽器分頁標題必須是：

   `台灣展覽誌｜全台展覽與演出資訊`

2. 逐一打開：
   - `https://twexhibition.com/favicon.ico`
   - `https://twexhibition.com/favicon-48.png`
   - `https://twexhibition.com/apple-touch-icon.png`
   - `https://twexhibition.com/logo-512.png`
3. 四個網址都應顯示票券「展」Logo，不能是地球圖示或 404。

### 官方來源

1. GitHub `Actions` → 最新的 `Update data and deploy site`。
2. 打開 `update-and-deploy` 工作記錄。
3. 搜尋：
   - `twtc-hall-1`
   - `taipei-expo-park-expo-dome`
4. 來源失敗時應標示 isolate／preserve；不得把正式資料清空。
5. `twtc-hall-3` 必須維持 `retired`、`enabled: false`。

### Google 重新索引

Google 圖示與標題不是部署後立即變更，需等待重新檢索：

1. 開啟 Google Search Console。
2. 選擇 `twexhibition.com` 資源。
3. 上方 `網址審查` 貼入 `https://twexhibition.com/`。
4. 點 `要求建立索引`。
5. 圖示與標題由 Google 最終決定，重新檢索可能需要數天以上。

## 9. 復原方式

### 尚未 Commit

1. GitHub Desktop 左側 `Changes` 全選。
2. 右鍵點 `Discard Changes`。
3. 若新增檔案未完全移除，用更新前備份還原。

### 已 Commit、尚未合併

1. GitHub Desktop 點 `History`。
2. 找到 `Apply Exhibition Hub V6.5.0-R13 SEO and official venue sources`。
3. 右鍵點 `Revert Changes in Commit`。
4. 點 `Push origin`。

### 已合併到 main

1. GitHub repository 點 `Pull requests`，打開已合併的 R13 PR。
2. 找到合併 commit。
3. 建立一個 revert PR，或在 GitHub Desktop 的 `main` 對該合併 commit 執行 `Revert Changes in Commit`。
4. 將 revert 提交推送後建立 `main ← develop` PR。
5. 等 checks 全綠再合併，然後重新執行 `Update data and deploy site`。

## 10. 本包已驗證

- 以 GitHub `main` commit `1a9ab48` 為基底。
- 世貿一館官方列表現場讀取 34 筆，抽查 5 筆詳情成功。
- 花博爭艷館官方列表篩得 7 筆場地相符活動，抽查 5 筆詳情與圖片成功。
- 空圖片與 HTML 詳情頁不再被當成圖片。
- 全套 Python 單元測試、JavaScript 語法、JSON 格式與 ZIP 完整性均於打包前重新驗證。
