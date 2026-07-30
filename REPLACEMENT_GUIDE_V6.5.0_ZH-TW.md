# Exhibition Hub V6.5.0 更新、檢查與復原指南

## 一、這次更新後會看到什麼

1. 電腦版 Hero 一次顯示兩組「展覽票券＋展覽圖片明信片」。
2. 票券與明信片會部分重疊，第一組在左下、第二組在右上。
3. Hero 左側箭頭顯示下一組；右側箭頭顯示上一組。
4. 切換下一組時，第二組會往前移，第三組由右側滑入。
5. 手機版不顯示箭頭：向左滑是下一組，向右滑是上一組。
6. 「再抽一組觀展靈感」及 15 秒自動輪播已移除。
7. 手機首頁改為「日曆／分類／展區／免費」四個快捷入口。
8. 手機探索頁的「最新收錄／即將結束／免費入場」徽章會位於膠囊中央。

## 二、應該下載哪一個 ZIP

### 建議：安全更新包

```text
Exhibition-Hub-V6.5.0-hero-postcard-carousel-safe-update.zip
```

用於目前已正常運作的 `exhibition-hub` GitHub 專案。這個檔案不含：

```text
data/
scripts/
.github/
```

因此不會覆蓋每日更新的展覽資料，也較不會再次產生數千筆 JSON 衝突。

### 備用：完整替換包

```text
Exhibition-Hub-V6.5.0-full-replacement.zip
```

只有在本機專案遺失大量檔案、需要重新建立完整專案時才使用。平常更新不要使用完整替換包。

## 三、安全更新包會覆蓋的主要路徑

| ZIP 內檔案 | GitHub 專案內位置 | 效果 |
|---|---|---|
| `index.html` | `/index.html` | Hero 按鈕、箭頭、手機四個快捷入口 |
| `assets/app.js` | `/assets/app.js` | 桌機切換、手機滑動與免費篩選邏輯 |
| `assets/styles.css` | `/assets/styles.css` | 票券／明信片堆疊、箭頭、手機版與徽章置中 |
| `tests/*.py` | `/tests/*.py` | GitHub Actions 回歸測試 |
| `VERSION.txt` | `/VERSION.txt` | 版本改為 V6.5.0 |
| `MANIFEST_V6.5.0.json` | `/MANIFEST_V6.5.0.json` | 更新內容與驗證結果 |
| `README.md` | `/README.md` | V6.5.0 說明 |
| `REPLACEMENT_GUIDE_V6.5.0_ZH-TW.md` | 專案根目錄 | 本指南 |
| `UPLOAD_STEPS.txt` | 專案根目錄 | 最短操作流程 |

## 四、更新前先確認

1. 開啟 **GitHub Desktop**。
2. 左上角 **Current Repository** 必須是：

   ```text
   exhibition-hub
   ```

3. 上方 **Current Branch** 選擇：

   ```text
   develop
   ```

4. 中央若顯示 **No local changes**，可以繼續。
5. 若 Changes 有你自己尚未提交的檔案，先提交或暫停，不要直接覆蓋。
6. 點上方 **Fetch origin**，等待完成。
7. 如果按鈕變成 **Pull origin**，先點一次 **Pull origin**。

## 五、GitHub Desktop＋Finder 安全更新方式

### 5-1 解壓縮

1. 在 Finder 的「下載項目」找到：

   ```text
   Exhibition-Hub-V6.5.0-hero-postcard-carousel-safe-update.zip
   ```

2. 點兩下解壓縮。
3. 打開解壓後的資料夾：

   ```text
   exhibition-hub-v6.5.0-hero-postcard-carousel-safe-update
   ```

### 5-2 打開正確的 GitHub 專案路徑

1. 回到 GitHub Desktop。
2. 點上方選單：

   ```text
   Repository → Show in Finder
   ```

3. 應該開啟類似路徑：

   ```text
   /Users/jacky_yu/Documents/GitHub/exhibition-hub
   ```

4. 判斷正確位置的方法：該資料夾內必須直接看得到：

   ```text
   index.html
   assets
   data
   scripts
   tests
   ```

### 5-3 複製並覆蓋

1. 在安全更新包資料夾內按：

   ```text
   Command + A
   ```

2. 將選到的「內容」拖進 GitHub 的 `exhibition-hub` 根目錄。
3. 不要把最外層資料夾整個放進去，否則會變成：

   ```text
   exhibition-hub/exhibition-hub-v6.5.0-hero-postcard-carousel-safe-update/
   ```

   這是錯誤路徑。

4. macOS 詢問同名檔案時，點：

   ```text
   Replace／取代
   ```

5. 回到 GitHub Desktop，Changes 應顯示 `index.html`、`assets/app.js`、`assets/styles.css`、測試與說明檔。
6. 不應看到以下檔案被修改：

   ```text
   data/exhibitions.json
   data/exhibitions.enriched.json
   data/geocode-cache.json
   .github/workflows/update-exhibitions.yml
   ```

## 六、提交到 develop

1. GitHub Desktop 左下角 **Summary (required)** 輸入：

   ```text
   Apply Exhibition Hub V6.5.0 hero postcard carousel
   ```

2. Description 可留白。
3. 點左下角：

   ```text
   Commit to develop
   ```

4. 提交完成後，點上方：

   ```text
   Push origin
   ```

5. 推送完成後應回到 **No local changes**。

## 七、建立 Pull Request

1. 在 GitHub Desktop 點藍色：

   ```text
   Preview Pull Request
   ```

2. 確認分支方向：

   ```text
   base: main
   compare: develop
   ```

3. 點：

   ```text
   Create Pull Request
   ```

4. 瀏覽器開啟後，PR 標題輸入：

   ```text
   Apply Exhibition Hub V6.5.0 hero postcard carousel
   ```

5. Description 建議貼上：

   ```text
   - Replace Hero shuffle tickets with a two-pair ticket and postcard carousel
   - Add desktop previous/next arrows and mobile swipe navigation
   - Replace the mobile home filter panel with calendar/category/area/free shortcuts
   - Center mobile Explore card badges
   - Exclude generated exhibition data from the safe update
   ```

6. 點綠色：

   ```text
   Create pull request
   ```

## 八、等待測試，不要先合併

PR 內找到 **Checks** 區域，等待下列檢查變成綠色：

```text
Validate development changes
Run project tests
```

應看到：

```text
All checks have passed
```

若仍是黃色圓點，代表還在執行；若是紅色叉號，不要合併，截圖最後 30 行錯誤訊息。

## 九、合併並部署到正式官網

1. 所有檢查綠色後，點：

   ```text
   Merge pull request
   ```

2. 再點：

   ```text
   Confirm merge
   ```

3. 回到儲存庫上方：

   ```text
   Actions
   ```

4. 點左側：

   ```text
   Update data and deploy site
   ```

5. 通常合併後會自動出現一筆 `main` 工作。
6. 若沒有自動出現，點右側：

   ```text
   Run workflow
   ```

7. Branch 選：

   ```text
   main
   ```

8. 再點綠色：

   ```text
   Run workflow
   ```

9. 等工作顯示綠色勾勾與：

   ```text
   Success
   ```

10. 打開：

    ```text
    https://twexhibition.com/
    ```

11. Mac Chrome 強制重新載入：

    ```text
    Command + Shift + R
    ```

## 十、前台檢查清單

### 電腦版

1. Hero 不再顯示「再抽一組觀展靈感」。
2. Hero 同時有兩張票券與兩張展覽圖片明信片。
3. 左箭頭顯示下一組。
4. 右箭頭顯示上一組。
5. 下一組切換時，後方組向前、下一組從右側滑入。
6. 點票券或明信片可以進入對應展覽。

### 手機版

1. Hero 不顯示左右箭頭。
2. 向左滑顯示下一組。
3. 向右滑顯示上一組。
4. 票券高度比舊版窄，標題不會超出。
5. 首頁顯示「日曆／分類／展區／免費」四個按鈕。
6. 日曆、分類、展區會開啟右側選單對應位置。
7. 免費會進入探索頁並只顯示免費活動。
8. 探索卡片徽章文字位於膠囊中央。

## 十一、GitHub 網頁直接上傳方式

只有無法使用 GitHub Desktop 時才使用。

1. 開啟 GitHub 儲存庫。
2. 左上分支選單切換到：

   ```text
   develop
   ```

3. 點：

   ```text
   Code → Add file → Upload files
   ```

4. 將安全更新包資料夾內的「所有內容」拖到上傳區。
5. 不要上傳外層資料夾。
6. Commit message 輸入：

   ```text
   Apply Exhibition Hub V6.5.0 hero postcard carousel
   ```

7. 選：

   ```text
   Commit directly to the develop branch
   ```

8. 點：

   ```text
   Commit changes
   ```

9. 接著依本指南第七至第十節建立 PR、等測試、合併與部署。

## 十二、遇到問題時如何復原

### 尚未 Commit

1. GitHub Desktop 的 Changes 中確認只包含本次檔案。
2. 點上方選單：

   ```text
   Branch → Discard All Changes
   ```

3. 確認後會回到更新前狀態。

### 已 Commit，但尚未 Push

1. GitHub Desktop 點：

   ```text
   History
   ```

2. 找到：

   ```text
   Apply Exhibition Hub V6.5.0 hero postcard carousel
   ```

3. 右鍵點該提交，選：

   ```text
   Undo Commit
   ```

4. 再到 Changes 捨棄本次變更。

### 已 Push，但尚未合併

1. 回到 GitHub 的 Pull Request。
2. 點：

   ```text
   Close pull request
   ```

3. 不要按 Merge。

### 已合併到 main

1. 開啟已合併的 V6.5.0 Pull Request。
2. 點：

   ```text
   Revert
   ```

3. GitHub 會建立一個復原 PR。
4. 等復原 PR 測試綠色後，再合併。
5. 到 Actions 等 **Update data and deploy site** 完成。

## 十三、若再次看到大量 JSON 衝突

1. 不要逐行處理數千筆衝突。
2. 點 GitHub Desktop 衝突視窗：

   ```text
   Abort Merge
   ```

3. 確認使用的是安全更新包，而不是完整替換包。
4. 確認安全更新包內沒有 `data` 資料夾。
5. 回到 `develop`，Fetch／Pull 最新內容後重新覆蓋安全更新包。

