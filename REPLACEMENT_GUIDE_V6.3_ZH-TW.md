# Exhibition Hub V6.3 完整替換與復原指南

本指南適用於 `jackyyu0130/exhibition-hub`。建議先更新 `develop`，通過檢查後再合併到 `main`；不要直接刪除整個本機專案，也不要使用 `git reset --hard`。

## 一、先確認你拿到正確的 ZIP

檔名：

```text
Exhibition-Hub-V6.3-full-replacement.zip
```

解壓縮後應看到：

```text
exhibition-hub-main/
├── .github/
├── assets/
├── data/
├── docs/
├── scripts/
├── tests/
├── index.html
├── README.md
├── VERSION.txt
└── REPLACEMENT_GUIDE_V6.3_ZH-TW.md
```

要複製的是 `exhibition-hub-main` 裡面的內容，不是把 `exhibition-hub-main` 整個資料夾再塞進現有儲存庫。

## 二、更新前備份

### GitHub 網頁備份

1. 開啟 GitHub 專案首頁。
2. 確認左上分支為 `main`。
3. 點綠色 **Code**。
4. 點 **Download ZIP**。
5. 將檔案改名為 `exhibition-hub-before-v6.3.zip` 後保存。

### GitHub Desktop 同步

1. 開啟 GitHub Desktop。
2. 左上 **Current Repository** 選 `exhibition-hub`。
3. 上方 **Current Branch** 選 `main`。
4. 點上方 **Fetch origin**。
5. 若按鈕改成 **Pull origin**，再按一次，直到顯示已同步。

## 三、GitHub Desktop 建議更新法

### 1. 切到 develop

1. 點上方 **Current Branch**。
2. 清單中若已有 `develop`，直接點它。
3. 若沒有：
   - 點 **New Branch**；
   - Name 輸入 `develop`；
   - Based on 選 `main`；
   - 點 **Create Branch**；
   - 點上方 **Publish branch**。
4. 點 **Fetch origin**；若出現 **Pull origin**，先按 **Pull origin**。

### 2. 找到本機專案根目錄

1. GitHub Desktop 上方選單點 **Repository**。
2. 點 **Show in Finder**（Windows 為 **Show in Explorer**）。
3. 正確根目錄裡應直接看到 `index.html`、`assets`、`data`、`scripts`。

### 3. 覆蓋檔案

1. 在 Finder 解壓縮 V6.3 ZIP。
2. 打開解壓縮後的 `exhibition-hub-main`。
3. 全選裡面的檔案與資料夾。
4. 拖到本機 `exhibition-hub` 根目錄。
5. macOS 出現詢問時選 **套用到全部 → 取代**；Windows 選 **Replace the files in the destination**。
6. 不要先刪掉整個舊專案；這樣原有的 `CNAME` 與選用的 `assets/hero-video.mp4` 才會保留。
7. 若 Finder 看不到 `.github` 或 `.nojekyll`，按 `Cmd+Shift+.` 顯示隱藏檔。

### 4. 檢查 Changes

回到 GitHub Desktop 左側 **Changes**，至少應看到這些類型：

```text
index.html
assets/app.js
assets/styles.css
data/exhibitions.json
data/exhibitions.enriched.json
data/curated-overrides.json
data/update-reports/image-quality-audit.json
scripts/build_pages_site.py
scripts/audit_event_images.py
scripts/validate_published_data.py
scripts/exhibition_hub/image_quality.py
.github/workflows/update-exhibitions.yml
tests/...
```

若看到 `.DS_Store`，取消勾選，不要提交。

### 5. 提交與推送 develop

1. 左下 **Summary (required)** 輸入：

```text
Fix official images and venue selector V6.3
```

2. 點 **Commit to develop**。
3. 點上方 **Push origin**。
4. 等待右上不再顯示待推送數字。

## 四、GitHub 網頁上傳法

完整包檔案較多，GitHub Desktop 較穩定。若只能用網頁，請分批上傳。

1. 開啟專案首頁。
2. 點分支按鈕，切到 `develop`。
3. 沒有 `develop` 時：
   - 點分支按鈕；
   - 在輸入框輸入 `develop`；
   - 點 **Create branch: develop from main**。
4. 點 **Add file → Upload files**。
5. 分批拖入，避免單次超過 GitHub 網頁限制：
   - 第一批：根目錄檔案；
   - 第二批：`assets`；
   - 第三批：`data`；
   - 第四批：`scripts`；
   - 第五批：`tests`、`docs`、`.github`。
6. 每一批下方 **Commit changes**：
   - Commit message 可填 `Upload V6.3 batch 1` 等；
   - 選 **Commit directly to the develop branch**；
   - 點 **Commit changes**。
7. 每批上傳後回專案首頁確認路徑，避免變成：

```text
exhibition-hub-main/index.html
```

正確位置必須是：

```text
index.html
assets/app.js
data/venues.json
```

## 五、檢查 develop

1. GitHub 專案上方點 **Actions**。
2. 左側點 **Validate development changes**。
3. 點最新的一次執行。
4. 等必要工作顯示綠色勾勾。
5. 若是 Culture Ministry 或外部官方網站暫時逾時，先按右上 **Re-run jobs → Re-run failed jobs** 一次；不要因外站短暫逾時手動改資料。
6. 若 **Run project tests** 失敗，展開紅色工作，複製最下方錯誤再處理，不要合併。

## 六、合併到 main

1. GitHub 上方點 **Pull requests**。
2. 點 **New pull request**。
3. 左側 **base** 選 `main`。
4. 右側 **compare** 選 `develop`。
5. 點 **Create pull request**。
6. 標題輸入：

```text
Exhibition Hub V6.3 image and venue fixes
```

7. 等頁面檢查變成綠色。
8. 點 **Merge pull request**。
9. 點 **Confirm merge**。
10. 不必刪除 `develop`；後續更新仍沿用它。

## 七、正式部署

合併到 `main` 後通常會自動啟動。

1. GitHub 上方點 **Actions**。
2. 左側點 **Update data and deploy site**。
3. 點最新一筆 `main` 執行。
4. 依序確認：
   - **Run project tests before production data update**：綠色；
   - **Sanitize published image and social references**：綠色；
   - **Validate dynamic published production data**：綠色；
   - **Build minimal Pages site**：綠色；
   - **Deploy to GitHub Pages**：綠色。
5. 若沒有自動執行：
   - 點右上 **Run workflow**；
   - Branch 選 `main`；
   - 再點綠色 **Run workflow**。

GitHub Pages 設定應為：

1. 專案 **Settings**。
2. 左側 **Pages**。
3. **Build and deployment → Source** 選 **GitHub Actions**。
4. Custom domain 保持 `twexhibition.com`。

## 八、上線檢查

開啟 `https://twexhibition.com/`，Mac 按 `Cmd+Shift+R`，Windows 按 `Ctrl+F5`。

### 圖片

1. 開啟「動漫最高祭 Anime Max Festival」。
2. 應顯示華山官方動漫主視覺，不再出現「快閃店類型展覽替代主視覺」。
3. 網址應仍是華山官方活動頁。
4. 隨機檢查 OPENTIX 活動，不應再看到旗幟、Logo、分享圖、定位圖或共用 Banner。

### 場館

1. 點 **搜尋展覽**。
2. 捲到 **依縣市與場館篩選**。
3. 點 **搜尋或選擇展演場地** 右側的三段篩選圖示。
4. 面板應立即展開。
5. 點 **文創園區**，應看到華山、松山等相符場館，不再顯示「沒有找到符合條件的場地」。
6. 在搜尋框連續輸入文字，列表應順暢更新。
7. 點場館後，按鈕與已選標籤應立即更新，不應整個面板停頓。

### Pages 必要檔案

若場館分類仍全空，可直接在瀏覽器開啟：

```text
https://twexhibition.com/data/venues.json
https://twexhibition.com/data/northern_venue_matrix.json
```

兩個網址都應顯示 JSON，不應為 404。

## 九、合併衝突

若 GitHub Desktop 顯示 **Resolve conflicts before Merge**，先不要按 **Continue Merge**。

1. 點視窗中的 **Open in command line**，或 GitHub Desktop 上方 **Repository → Open in Terminal**。
2. 確認終端機路徑最後是 `exhibition-hub`：

```bash
pwd
git status
```

3. 若你是在 `develop` 合併 `origin/main`，V6.3 的活動資料要保留本次清洗版：

```bash
git checkout --ours -- data/exhibitions.json
git checkout --ours -- data/exhibitions.enriched.json
```

4. 座標快取可保留遠端每日更新版：

```bash
git checkout --theirs -- data/geocode-cache.json
```

5. 標記已解決並結束合併：

```bash
git add -- data/exhibitions.json data/exhibitions.enriched.json data/geocode-cache.json
git status
git commit -m "Resolve V6.3 data merge conflict"
```

6. 回 GitHub Desktop。若顯示 **Push origin**，點它。

若只有 `data/exhibitions.json` 衝突，指令中只保留實際存在的衝突檔即可。

若終端機顯示：

```text
fatal: not a git repository
```

表示你在錯誤資料夾。先執行：

```bash
cd /Users/你的帳號/Documents/GitHub/exhibition-hub
pwd
git status
```

macOS 若顯示找不到開發工具，先執行 `xcode-select --install`，安裝完成後再重試。

若 `git push` 要求 GitHub Password，按 `Ctrl+C` 取消；GitHub 不接受帳號密碼推送。回 GitHub Desktop 登入後按 **Push origin**，不要把 `git status` 輸入 Username 欄。

## 十、復原

### 尚未 Commit

1. GitHub Desktop 左側 **Changes**。
2. 右鍵要還原的檔案。
3. 點 **Discard Changes**。
4. 大量檔案時先再次確認，避免丟掉其他自己的修改。

### 已 Commit、尚未 Push

1. GitHub Desktop 上方點 **History**。
2. 找到剛提交的 V6.3 commit。
3. 右鍵點 **Undo Commit**。
4. 檔案會回到 Changes，可重新檢查。

### 已 Push 到 develop

1. GitHub Desktop 點 **History**。
2. 右鍵 V6.3 commit。
3. 點 **Revert Changes in Commit**。
4. 提交產生的 revert commit。
5. 點 **Push origin**。

### 已合併到 main

1. GitHub 網頁點 **Pull requests**。
2. 打開已合併的 V6.3 PR。
3. 點 **Revert**。
4. 建立並合併 GitHub 自動產生的復原 PR。
5. 等 **Update data and deploy site** 再次完成。

若 GitHub 沒顯示 Revert：

1. GitHub Desktop 切到 `main` 並 Pull origin。
2. 點 **History**。
3. 找到 V6.3 merge commit。
4. 右鍵 **Revert Changes in Commit**。
5. Commit 並 Push origin。

不要使用 `git reset --hard`，避免刪除尚未備份的本機工作。

## 十一、這次主要修改路徑

```text
index.html
assets/app.js
assets/styles.css
data/curated-overrides.json
data/exhibitions.json
data/exhibitions.enriched.json
data/update-reports/image-quality-audit.json
scripts/audit_event_images.py
scripts/build_pages_site.py
scripts/scraper.py
scripts/validate_published_data.py
scripts/exhibition_hub/image_quality.py
scripts/exhibition_hub/merging/normalization.py
scripts/exhibition_hub/merging/policy.py
scripts/exhibition_hub/merging/source_adapter.py
.github/workflows/update-exhibitions.yml
tests/test_image_quality.py
tests/test_pages_site_builder.py
tests/test_published_data_validator.py
tests/test_url_integrity.py
tests/test_venue_selector_frontend.py
```
