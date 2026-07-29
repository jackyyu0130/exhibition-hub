# Exhibition Hub V6.4.0 完整替換指南

適用網站：<https://twexhibition.com/>  
適用儲存庫：`jackyyu0130/exhibition-hub`  
建議流程：`develop` 測試 → Pull Request → `main` → GitHub Pages

## 一、這次更新內容

- 修正「動漫最高祭 Anime Max Festival」官方圖片。
- 修正「星際大戰華山限定快閃店」與「萌町園遊會」圖片。
- 修復華山圖片檔名中的全形 `｜`、`：` 被轉成半形而失效的根因。
- 探索頁圖片左下角不再顯示「快閃店／一般展覽」。
- 卡片名稱上方顯示真正的展覽分類，例如「動漫」、「美術」、「設計」。
- 「演唱會」與「音樂」分開；音樂劇歸入「表演」。
- 點擊左上角 Logo／台灣展覽誌會重新載入首頁與最新資料。
- 手機右上角新增漢堡選單，包含全站搜尋、分類、日曆、縣市與場館篩選。
- 手機首頁以一條長按鈕開啟篩選；手機探索頁使用分類／日曆雙按鈕與地區場館長按鈕。

## 二、更新前先做安全檢查

### 2.1 在 GitHub Desktop 確認儲存庫

1. 開啟 **GitHub Desktop**。
2. 看左上角 **Current Repository**。
3. 點一下儲存庫名稱。
4. 選擇 **exhibition-hub**。
5. 若清單裡沒有：
   - 上方選單點 **File**。
   - 點 **Add Local Repository…**。
   - 點 **Choose…**。
   - 選擇：

```text
/Users/jacky_yu/Documents/GitHub/exhibition-hub
```

6. 點 **Add Repository**。

### 2.2 先取得遠端最新版本

1. 看上方中間 **Current Branch**。
2. 點分支名稱，選 **develop**。
3. 看上方右側：
   - 顯示 **Fetch origin**：點一次。
   - 變成 **Pull origin**：再點一次，把遠端更新拉回電腦。
4. 若跳出 **Newer Commits on Remote**，點 **Fetch**，再點 **Pull origin**。

### 2.3 處理本機尚未提交的檔案

看左側 **Changes**：

- 顯示 **0 changed files**：可以繼續。
- 只有 `.DS_Store`：
  - 取消左側勾選，不要把它提交。
  - 或在 Finder 刪除該 `.DS_Store`。
- 有自己修改中的程式：
  - 不要立刻貼上替換包。
  - 左下 **Summary** 輸入一個暫存說明。
  - 點 **Commit to develop**。
  - 點 **Push origin**。
  - 完成後再開始替換。

## 三、GitHub Desktop 完整替換方式

### 3.1 解壓縮

1. 下載：

```text
Exhibition-Hub-V6.4.0-full-replacement.zip
```

2. 在 Finder 的「下載項目」雙擊 ZIP。
3. 打開解壓後的：

```text
exhibition-hub-v6.4.0-full-replacement
```

4. 你應該直接看到：

```text
index.html
assets
data
scripts
tests
.github
README.md
requirements.txt
```

如果先看到第二層同名資料夾，請再進入一層。要複製的是「專案內容」，不是把外層資料夾塞進儲存庫。

### 3.2 找到本機儲存庫

在 GitHub Desktop：

1. 上方選單點 **Repository**。
2. 點 **Show in Finder**。
3. Finder 會開啟：

```text
/Users/jacky_yu/Documents/GitHub/exhibition-hub
```

### 3.3 覆蓋檔案

1. 回到解壓後的 V6.4.0 資料夾。
2. 按 `Command + A` 全選。
3. 按 `Command + C` 複製。
4. 切到 `exhibition-hub` 儲存庫 Finder 視窗。
5. 按 `Command + V` 貼上。
6. macOS 詢問同名檔案時：
   - 點 **全部套用**。
   - 點 **取代**。
7. 不要刪除 `.git`；一般 Finder 不會顯示它，也不需要碰它。

## 四、提交到 develop

1. 回到 GitHub Desktop。
2. 再次確認上方 **Current Branch = develop**。
3. 左側應出現多個 changed files，包括：

```text
index.html
assets/app.js
assets/styles.css
data/curated-overrides.json
data/exhibitions.enriched.json
scripts/scraper.py
scripts/exhibition_hub/merging/normalization.py
scripts/exhibition_hub/merging/policy.py
scripts/exhibition_hub/merging/source_adapter.py
tests/test_v64_mobile_media_taxonomy.py
tests/test_url_integrity.py
VERSION.txt
```

4. 左下 **Summary (required)** 輸入：

```text
Apply Exhibition Hub V6.4.0 mobile filters and media fixes
```

5. **Description** 可以留白。
6. 點下方藍色 **Commit to develop**。
7. 等左側顯示 **No local changes**。
8. 點上方 **Push origin**。

## 五、在 GitHub 網頁建立或更新 Pull Request

1. 打開 GitHub 儲存庫：

```text
https://github.com/jackyyu0130/exhibition-hub
```

2. 點上方 **Pull requests**。
3. 如果已經有 `develop → main` 的開啟中 PR：
   - 點該 PR 標題。
   - 新推送的 commit 會自動加入，不用再建一個 PR。
4. 如果沒有：
   - 點右上綠色 **New pull request**。
   - `base` 選 **main**。
   - `compare` 選 **develop**。
   - 點 **Create pull request**。
   - 標題可輸入：

```text
Apply Exhibition Hub V6.4.0 mobile filters and media fixes
```

5. 等待 **Checks**：
   - **Validate development changes**
   - **Run project tests**
6. 全部顯示綠色勾勾後：
   - 點 **Merge pull request**。
   - 點 **Confirm merge**。
7. 不要在測試仍是紅色時強制合併。

## 六、確認正式部署

1. 在 GitHub 儲存庫上方點 **Actions**。
2. 左側點 **Update data and deploy site**。
3. 點最上面、分支標示為 **main** 的執行紀錄。
4. 點左側工作 **update-and-deploy**。
5. 依序確認：
   - **Run project tests before production data update**：綠色。
   - **Validate dynamic published production data**：綠色。
   - **Build minimal Pages directory**：綠色。
   - **Upload website files**：綠色。
   - **Deploy to GitHub Pages**：綠色。
6. 回 Summary，狀態應是 **Success**。
7. 點部署結果中的：

```text
https://twexhibition.com/
```

8. GitHub Pages 與網域快取通常需要 2～10 分鐘。

## 七、部署後逐項檢查

### 7.1 強制取得新版

- macOS Chrome／Safari：`Command + Shift + R`
- Windows Chrome／Edge：`Ctrl + F5`
- 手機：開啟無痕分頁，再進入 `https://twexhibition.com/`

### 7.2 桌機版

1. 點左上角 Logo：
   - 網址回到首頁。
   - 頁面重新載入。
   - 首頁資料與動畫重新初始化。
2. 進入 **探索展覽**：
   - 圖片左下角不再出現「快閃店」。
   - 卡片內容上方顯示真正分類。
3. 搜尋：

```text
動漫最高祭
```

4. 進入詳情頁，確認圖片與華山官方頁相符。
5. 再檢查：

```text
星際大戰華山限定快閃店
萌町園遊會
```

6. 分類確認：
   - 五月天、米津玄師等具名歌手巡演在 **演唱會**。
   - 交響、古典、獨奏、室內樂在 **音樂**。
   - 音樂劇在 **表演**。

### 7.3 手機版

1. 首頁右上角應出現圓形漢堡按鈕。
2. 點漢堡：
   - 右側滑出選單。
   - 上方有全站搜尋。
   - 先顯示 4 個熱門圓形分類。
3. 點 **展開全部**：
   - 顯示完整分類。
   - 每列 4 個。
4. 日曆：
   - 點日期套用。
   - 再點同一天取消。
   - 選取日期時，今日框不會同時顯示成第二個選取框。
5. 點 **地區**：
   - 右側第二層選單開啟。
   - 可選縣市。
6. 點 **場館**：
   - 開啟場館搜尋與多選右側面板。
7. 首頁原分類卡區應改為一條長型篩選入口。
8. 探索頁上方應顯示：
   - 第一排：**分類**、**日曆**。
   - 第二排：**依縣市與場館篩選**。

## 八、圖片仍顯示舊圖時

先判斷是瀏覽器快取還是資料尚未重跑：

1. 用無痕視窗開啟同一活動。
2. 若無痕正確：是本機快取，清除該網站快取即可。
3. 若無痕仍錯：
   - GitHub → **Actions**。
   - 左側點 **Update data and deploy site**。
   - 右上角點 **Run workflow**。
   - Branch 選 **main**。
   - 點綠色 **Run workflow**。
4. 等最新紀錄完成並顯示 **Success**。
5. 再等 2～10 分鐘，用無痕視窗檢查。

## 九、GitHub Desktop 出現 Fetch／Pull／衝突時

### 9.1 Newer Commits on Remote

看到 **Newer Commits on Remote**：

1. 點 **Fetch**。
2. 上方變成 **Pull origin** 後，點 **Pull origin**。
3. Pull 完成後再 Push。

### 9.2 只有大型資料檔衝突

如果衝突檔是：

```text
data/exhibitions.json
data/exhibitions.enriched.json
data/geocode-cache.json
```

先不要逐行處理上千個衝突。這些是自動產出資料。

安全作法：

1. 在衝突視窗點 **Abort Merge**。
2. 確認自己的程式修改已經 commit。
3. 點 **Fetch origin**／**Pull origin** 取得最新資料。
4. 再重新貼入完整替換包。
5. 重新 Commit 與 Push。

如果已經進入終端機合併並且確定要保留本次替換包資料，可在正確儲存庫內執行：

```bash
cd /Users/jacky_yu/Documents/GitHub/exhibition-hub
git checkout --ours -- data/exhibitions.json data/exhibitions.enriched.json data/geocode-cache.json
git add -- data/exhibitions.json data/exhibitions.enriched.json data/geocode-cache.json
git commit -m "Resolve V6.4.0 data merge conflict"
git push origin develop
```

只有當 `pwd` 顯示以下路徑時才能執行：

```text
/Users/jacky_yu/Documents/GitHub/exhibition-hub
```

### 9.3 終端機要求 GitHub Username／Password

不要把 `git status` 輸入 Username 欄，也不要輸入 GitHub 帳號密碼。

1. 按 `Control + C` 取消。
2. 回 GitHub Desktop。
3. 由 GitHub Desktop 的 **Push origin** 上傳，讓已登入的 Desktop 處理授權。

## 十、復原方式

### 10.1 尚未 Commit

1. GitHub Desktop 左側點要復原的檔案。
2. 上方選單點 **Branch**。
3. 點 **Discard All Changes…**。
4. 確認 **Discard Changes**。

這會放棄尚未提交的修改，請確認沒有自己的未保存工作。

### 10.2 已 Commit，但尚未 Push

1. GitHub Desktop 左下角找到 **Undo**。
2. 點 **Undo**。
3. 修改會回到 Changes。
4. 再選擇要保留或放棄的檔案。

### 10.3 已合併到 main

1. GitHub 網頁進入儲存庫。
2. 點上方 **Pull requests**。
3. 點 **Closed**。
4. 開啟 V6.4.0 的已合併 PR。
5. 點 **Revert**。
6. GitHub 會建立一個復原 PR。
7. 等檢查綠色後，再合併復原 PR。

若 GitHub 沒有顯示 Revert：

1. 到 **Code**。
2. 點 **commits**。
3. 找到 V6.4.0 的 merge commit。
4. 複製 commit 編號。
5. 在 GitHub Desktop：**Repository → Open in Terminal**。
6. 執行：

```bash
git revert -m 1 MERGE_COMMIT編號
git push origin main
```

## 十一、本機檢查指令

在 GitHub Desktop 點：

**Repository → Open in Terminal**

執行：

```bash
python3 -m http.server 8000
```

瀏覽器開啟：

```text
http://localhost:8000
```

完整測試：

```bash
python3 -m pip install -r requirements.txt
python3 -m unittest discover -s tests -v
```

V6.4.0 建立替換包前的驗證結果：

- JavaScript 語法：通過。
- Python 語法：通過。
- JSON 格式：通過。
- 自動測試：317 項全部通過。
- GitHub Pages 精簡網站建置：通過。

