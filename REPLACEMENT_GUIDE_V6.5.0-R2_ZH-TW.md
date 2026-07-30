# Exhibition Hub V6.5.0-R2 更新、檢查與復原指南

適用網站：<https://twexhibition.com/>  
適用儲存庫：`jackyyu0130/exhibition-hub`  
更新流程：`develop → Pull Request → main → GitHub Pages`

## 一、R2 是什麼

R2 是**累積修復包**。先前的 V6.5.0 安全包負責 Hero／手機介面，V6.5.0-R1 安全包只負責華山 CI 與詳情補抓；若正式站仍停在 V6.4.2，只套 R1 並不會出現新版 Hero。

R2 將兩批必要檔案合併成一個安全更新包，從目前正式站狀態可以一次更新，不需要先後安裝 V6.5.0 與 R1。

## 二、R2 會包含哪些畫面更新

1. 電腦版 Hero 一次呈現兩組「展覽票券＋展覽圖片明信片」。
2. 移除「再抽一組觀展靈感」及 15 秒自動切換。
3. 左側箭頭顯示下一組，右側箭頭顯示上一組。
4. 下一組由右向左進場，原本第二組移到前方。
5. 手機版不顯示箭頭：向左滑下一組，向右滑上一組。
6. 手機票券高度與標題字級縮小。
7. 手機首頁原本的大型篩選區改成「日曆／分類／展區／免費」四個入口。
8. 手機探索頁「最新收錄／即將結束／免費入場」徽章文字水平與垂直置中。

R2 同時保留 R1 的華山修復：補回 5 個 HTML 測試樣本，單筆詳情暫時逾時時只重試失敗項目一次，持續失敗仍保留舊資料並阻止不完整結果發布。

## 三、下載哪一個

### 平常更新：安全更新包

```text
Exhibition-Hub-V6.5.0-R2-cumulative-repair-safe-update.zip
```

此包不含 `data/` 與 `.github/`，不會覆蓋每日展覽資料，也不會重新引發數千筆 JSON 衝突。

### 只有專案遺失才使用：完整替換包

```text
Exhibition-Hub-V6.5.0-R2-full-replacement.zip
```

平常不要用完整替換包。

## 四、安全包主要檔案

```text
index.html
assets/app.js
assets/styles.css
assets/taiwan-exhibition-journal-logo-v10.png
assets/favicon-48.png
assets/apple-touch-icon.png
scripts/exhibition_hub/collectors/huashan.py
scripts/run_collectors.py
tests/test_v650_postcard_carousel.py
tests/test_v650_r2_cumulative_release.py
tests/test_huashan_detail_collector.py
tests/fixtures/huashan_*.html
VERSION.txt
MANIFEST_V6.5.0-R2.json
README.md
UPLOAD_STEPS.txt
REPLACEMENT_GUIDE_V6.5.0-R2_ZH-TW.md
```

## 五、更新前

1. 開啟 GitHub Desktop。
2. `Current Repository` 選 `exhibition-hub`。
3. `Current Branch` 選 `develop`。
4. 點 `Fetch origin`；若變成 `Pull origin`，再點一次。
5. 確認左側顯示 `No local changes`。
6. 若有尚未提交的工作，先停止，不要覆蓋。

## 六、貼入 R2 安全更新包

1. 在 Finder 解壓 `Exhibition-Hub-V6.5.0-R2-cumulative-repair-safe-update.zip`。
2. GitHub Desktop 上方選單點 `Repository → Show in Finder`。
3. 確認打開的資料夾內直接看得到 `index.html`、`assets`、`data`、`scripts`、`tests`。
4. 回到 R2 解壓資料夾，選取**裡面的全部內容**。
5. 複製到 `exhibition-hub` 根目錄，詢問同名檔案時選 `Replace／取代`。
6. 不要把最外層 `exhibition-hub-v6.5.0-r2-cumulative-repair-safe-update` 資料夾整個放進儲存庫。

## 七、提交 develop

GitHub Desktop 左側應看到前端、華山程式、測試與說明文件。以下檔案不應出現：

```text
data/exhibitions.json
data/exhibitions.enriched.json
data/geocode-cache.json
.github/workflows/update-exhibitions.yml
```

Summary 輸入：

```text
Apply Exhibition Hub V6.5.0-R2 cumulative repair
```

接著點 `Commit to develop`，完成後點 `Push origin`。

## 八、建立 PR 與部署

1. 建立 `base: main`、`compare: develop` 的 Pull Request。
2. PR 標題：

```text
Apply Exhibition Hub V6.5.0-R2 cumulative repair
```

3. 等待 `Validate development changes`、`Run project tests` 全綠。
4. 點 `Merge pull request → Confirm merge`。
5. 到 `Actions → Update data and deploy site`。
6. 確認分支為 `main` 的工作顯示 `Success`。
7. 等 2～10 分鐘，開啟 <https://twexhibition.com/>。
8. Mac Chrome 按 `Command + Shift + R`；手機建議先用無痕頁確認。

## 九、前台檢查

### 電腦版 Hero

- 同時有兩組票券與兩張展覽圖片明信片。
- 沒有「再抽一組觀展靈感」。
- 沒有 15 秒自動切換提示，也不會自動輪播。
- 左箭頭進到下一組；右箭頭回到上一組。
- 切到下一組時，右側新組由右往左進場，原本第二組移到前方。
- 票券與明信片都可進入對應展覽。

### 手機版

- Hero 不顯示左右箭頭。
- 向左滑下一組，向右滑上一組。
- 票券高度與標題比舊版小，不應超出版面。
- 首頁顯示「日曆／分類／展區／免費」四個入口。
- 免費入口會進入只顯示免費活動的探索頁。
- 探索頁「最新收錄／即將結束／免費入場」文字位於膠囊中央。

### 華山資料流程

- PR 測試應全部通過。
- 不能再出現因缺少 5 個 `tests/fixtures/huashan_*.html` 而造成的測試錯誤。
- 單筆華山詳情暫時逾時可以被補抓；持續失敗時不得發布不完整資料。

## 十、復原

- 尚未 Commit：`Branch → Discard All Changes`。
- 已 Commit、未 Push：History 找到 R2 提交，右鍵 `Undo Commit`，再捨棄 Changes。
- 已 Push、未合併：關閉 Pull Request，不要 Merge。
- 已合併：在已合併 PR 點 `Revert`，等復原 PR 測試綠色後再合併並重新部署。

## 十一、再次看到大量 JSON 衝突

不要逐行處理。直接 `Abort Merge`，確認使用的是 R2 **安全更新包**，並確認解壓後沒有 `data` 資料夾。
