# Exhibition Hub V4.2 完整替換指南

這份替換包可直接覆蓋既有 GitHub Pages 專案。ZIP 內第一層就是網站根目錄內容；解壓後請複製「裡面的檔案」，不要把整個 ZIP 外層資料夾再包進儲存庫。

## 一、替換前先備份

1. 開啟你的 GitHub 專案首頁，例如 `https://github.com/你的帳號/你的專案`。
2. 在檔案列表右上方點綠色 **Code** 按鈕。
3. 保持在 **Local** 分頁，點 **Download ZIP**。
4. 將下載的舊版 ZIP 改名為 `exhibition-hub-backup-替換日期.zip` 並保存。
5. 若專案根目錄有 `CNAME`，記下內容；若有自訂 `assets/hero-video.mp4`，也請保留。

## 二、認識正確替換位置

解壓 V4.2 ZIP 後，應直接看到下列項目：

```text
index.html
assets/
data/
scripts/
tests/
.github/
.nojekyll
README.md
requirements.txt
VERSION.txt
```

它們必須放到 GitHub 儲存庫的根目錄，也就是目前 `index.html` 所在位置。正確路徑例如：

| 替換包項目 | GitHub 儲存庫內路徑 | 動作 |
|---|---|---|
| `index.html` | `/index.html` | 覆蓋 |
| `assets/app.js` | `/assets/app.js` | 覆蓋 |
| `assets/styles.css` | `/assets/styles.css` | 覆蓋 |
| `assets/taiwan-exhibition-journal-logo-v9.png` | `/assets/taiwan-exhibition-journal-logo-v9.png` | 新增或覆蓋 |
| `assets/exhibition-fallback-sprite-v40.png` | `/assets/exhibition-fallback-sprite-v40.png` | 新增或覆蓋 |
| `scripts/scraper.py` | `/scripts/scraper.py` | 覆蓋 |
| `data/exhibitions.json` | `/data/exhibitions.json` | 覆蓋；已先清理資料 |
| `data/geocode-cache.json` | `/data/geocode-cache.json` | 覆蓋 |
| `data/curated-overrides.json` | `/data/curated-overrides.json` | 新增；保存人工核實資料 |
| `.github/workflows/update-exhibitions.yml` | `/.github/workflows/update-exhibitions.yml` | 覆蓋 |
| `tests/` | `/tests/` | 新增或覆蓋 |
| `CNAME` | `/CNAME` | 若原本存在，保留原檔 |
| `assets/hero-video.mp4` | `/assets/hero-video.mp4` | 若原本存在，保留原檔 |

不要放成 `/Exhibition-Hub-V4.2-full-replacement/index.html`；這會讓 GitHub Pages 找不到首頁。

## 三、建議方式：使用 GitHub Desktop 完整覆蓋

這種方式最容易保留資料夾結構與 `.github` 工作流程。

1. 在 GitHub 專案首頁點 **Code**。
2. 點 **Open with GitHub Desktop**。如果尚未安裝，先點畫面中的下載連結安裝並登入 GitHub。
3. GitHub Desktop 顯示 **Clone a Repository** 時，確認專案名稱與本機路徑，點 **Clone**。
4. 在 GitHub Desktop 上方選單點 **Repository → Show in Explorer**；macOS 是 **Repository → Show in Finder**。
5. 先點 GitHub Desktop 上方 **Fetch origin**；若之後出現 **Pull origin**，先點 **Pull origin**，確認本機為最新狀態。
6. 打開已解壓的 V4.2 替換包，選取裡面的全部檔案與資料夾。
7. 把這些內容複製到剛才開啟的儲存庫根目錄。
8. 系統詢問同名檔案時，選 **取代目的地中的檔案／Replace** 或 **全部取代／Apply to All**。
9. 確認原本的 `CNAME` 仍存在；如有自訂 `assets/hero-video.mp4`，也確認仍存在。
10. 回到 GitHub Desktop。左下角 **Summary (required)** 輸入：`Update Exhibition Hub to V4.2`。
11. 點左下角藍色 **Commit to main**。
12. 點上方 **Push origin**，等待推送完成；完成後按鈕會回到 **Fetch origin**。

如果你的預設分支不是 `main`，先在 GitHub Desktop 上方 **Current Branch** 切到實際部署分支；同時要把 `/.github/workflows/update-exhibitions.yml` 中的 `branches: [main]` 與 `ref: main` 改成該分支名稱。

## 四、不用 GitHub Desktop：GitHub 網頁上傳

1. 在專案首頁確認左上方分支下拉選單顯示 **main**。
2. 點檔案列表右上方 **Add file → Upload files**。
3. 從已解壓的 V4.2 資料夾，把所有內容拖進「Drag files here」區域。務必包含 `assets`、`data`、`scripts`、`tests` 與 `.github`。
4. 等待所有檔名出現在上傳清單；向下捲到 **Commit changes**。
5. 提交訊息輸入 `Update Exhibition Hub to V4.2`。
6. 選 **Commit directly to the main branch**，再點綠色 **Commit changes**。

若瀏覽器沒有接受整個資料夾、看不到 `.github`，或一次上傳失敗，請改用上面的 GitHub Desktop 方式。網頁上傳只會覆蓋同名檔，不會刪除你原有的 `CNAME` 或 Hero 影片。

## 五、如果 GitHub Desktop 出現合併衝突

`data/exhibitions.json` 會由 GitHub Actions 自動更新，因此有時會和本機 V4.2 同時修改。若 GitHub Desktop 顯示 **Resolve conflicts before Merge**，不要手動處理數百或數千個 JSON 區塊，也不要直接刪除 `<<<<<<<`、`=======`、`>>>>>>>`。

### 情況 A：你想保留剛覆蓋的 V4.2 資料

1. 在衝突視窗先點 **Abort Merge**，回到一般 Changes 畫面。
2. macOS 開啟 **Terminal**。
3. 輸入你的本機專案路徑：

```bash
cd /Users/jacky_yu/Documents/GitHub/exhibition-hub
```

4. 確認位置：

```bash
pwd
git status
```

5. 如果只看到 `.DS_Store`，先清除這個 Finder 暫存變更：

```bash
git restore -- .DS_Store
```

6. 取得最新遠端版本並開始合併：

```bash
git fetch origin
git merge origin/main
```

7. 若衝突檔是 `data/exhibitions.json`，保留本機 V4.2：

```bash
git checkout --ours -- data/exhibitions.json
git add -- data/exhibitions.json
git status
```

8. 正確狀態會顯示：

```text
All conflicts fixed but you are still merging.
```

`data/geocode-cache.json` 若出現在 **Changes to be committed** 是正常的，不用取消勾選。

9. 完成合併提交：

```bash
git commit -m "Resolve V4.2 data merge conflict"
```

10. 如果終端機執行 `git push origin main` 要求 Username／Password，按 **Control + C** 取消，不要輸入 GitHub 密碼。回到 GitHub Desktop，點 **Repository → Refresh**，再點上方 **Push origin**。
11. 最後執行：

```bash
git status
```

成功時會顯示：

```text
Your branch is up to date with 'origin/main'.
nothing to commit, working tree clean
```

### 情況 B：終端機顯示 `not a git repository`

表示目前停在個人主目錄，不代表檔案損壞。重新執行：

```bash
cd /Users/jacky_yu/Documents/GitHub/exhibition-hub
pwd
git status
```

看到路徑 `/Users/jacky_yu/Documents/GitHub/exhibition-hub` 與 `On branch main` 後，再繼續上面的衝突處理。

## 六、設定 GitHub Pages

1. 在專案頁面最上方點 **Settings**。若視窗較窄，Settings 可能藏在上方 **…** 選單內。
2. 左側選單找到 **Code and automation** 區域，點 **Pages**。
3. 在 **Build and deployment** 的 **Source** 下拉選單選 **GitHub Actions**。
4. 不需要選 `/docs`，也不需要設定 Jekyll theme。

## 七、手動更新資料並部署

1. 回到專案上方分頁，點 **Actions**。
2. 左側工作流程清單點 **Update data and deploy site**。
3. 右上方點 **Run workflow**。
4. **Use workflow from** 選 **Branch: main**。
5. 點綠色 **Run workflow**。
6. 等待新的執行項目出現，點進去查看；`update-and-deploy` 顯示綠色勾勾才算完成。
7. 工作流程會依序進行全量官方資料補強、執行 36 項測試、上傳網站並部署 Pages。第一次全量更新可能比舊版久，請等待整個 `update-and-deploy` 變成綠色。

若沒有看到 **Run workflow**，先確認你已登入、對此儲存庫有寫入權限，且 `/.github/workflows/update-exhibitions.yml` 已在預設分支。

## 八、上線後逐項驗證

1. 到 **Settings → Pages**，點 **Visit site** 開啟網站。
2. Windows 按 `Ctrl + F5`；macOS 按 `Command + Shift + R`，避免舊版快取。
3. 首頁 Hero：不要碰票券，等待 15 秒應更換一組；把滑鼠停在 Hero 或票券超過 15 秒，票券不得切換；移出後才繼續剩餘倒數。點 **再抽一組** 會立即換一組並重新計時。
4. 首頁日期／狀態：選日期，再點目前舉辦、即將舉辦等狀態，畫面只使用同一個結果區並替換內容；卡片只會平順浮現，不應閃白或反覆消失。同一個狀態按鈕再點一次，應回到 **全部**。
5. 首頁篩選：有選取條件時最右側出現 **清除篩選**。
6. 點 **探索全部展覽**：縣市預設收合；打開第二個縣市時，第一個會自動收合。
7. 任選分類、縣市、場館、日期或狀態：已選條件列最右側出現 **清除全部篩選**。
8. 首頁所有展覽圖卡：主圖區應為正方形 1:1；探索頁與詳情頁維持各自版型。
9. 首頁第一區應有淡暖灰米色滿版背景與極淡紙張網格；主標題應為 **讓一場展覽，成為日常裡的風景。**，右側 Hero 為橫向比例，桌機高度約 470px；左側「收錄活動／展演場館」統計底部應與右側抽卡區對齊。
10. 左上角 Logo 只有票券內部是低飽和奶黃色；票型、虛線、中文字、英文及其餘透明區域不得改變。整體仍只比旁邊導覽文字稍大。
11. Hero 地圖應只有河線、三條步行路徑、少量場館符號與一個定位點，不得再出現密集街廓、羅盤或立體陰影。第二張票券應高於第一張票券頂緣並露出足夠內容；票券類型應有雙層線框、深色條碼與淡色圓章浮水印。
12. 探索區標題應為 **循著今日心緒，遇見一場展覽**，且 `EXPLORE BY MOOD` 與上方 Hero 之間有明顯留白；狀態按鈕懸浮時應顯示淡奶黃色回饋。**查看全部展覽 ↗** 應位於日期／狀態大框最右側。
13. 場館區標題應為 **從一座場館，展開城市漫遊**。桌機一次顯示三列、每列四張矮版卡片；進場時不得錯位，滑鼠懸浮後應有清楚但緩慢的上浮、放大與陰影變化。
14. **本週值得出發的展覽** 圖卡應在原位置淡入揭露，不得先向左錯位；場館圖片失效時應依序切換其他館內展覽圖片，全部失效才顯示精緻分類圖，不得再出現單色大型「館」字。
15. **瀏覽所有場館 ↗** 應位於場館卡片區正下方的中央橢圓按鈕。
16. 時間區標題應為 **循著展期，安排下一場相遇**；附近區標題應為 **從此刻所在，走向城市裡的一場相遇。**，說明以 **讓所在的位置成為起點** 開頭。
17. 點 **探索展覽**，選取分類、縣市或場館：左上角條件標題應較小，分類之間使用頓號，各組條件以低彩度細斜線分隔，不得再出現突出的「＋」。點擊圖片以外的圖卡文字或空白處，也應能進入展覽詳情。
18. 展覽卡與詳情主圖：應看到清晰完整前景，後方是同一張圖的柔焦填滿背景。
19. 開啟一筆展覽詳情：標題與內文字級應比舊版小；地圖導航查詢應是場館或地址，不是活動名稱。
20. 點 **附近展覽**：瀏覽器應詢問定位權限；允許後只顯示 20 公里內活動並由近到遠排列。卡片要有綠色距離標籤與 **地圖導航 ↗**，左側地圖要顯示目前位置、20 公里範圍與活動標記。
21. 點 **我的收藏**：桌機應為每排四張 1:1 方卡，卡片由下往上緩慢浮現；有收藏時，下方標題應為 **沿著收藏，遇見下一場**，並出現可橫向滑動的相似展覽推薦。
22. 頁尾應在「探索」右側顯示 **收錄展覽／展演場地／更新時間**，每一列不得斷行；不得再出現 **關於資料**。
23. 找到沒有官方主視覺的活動：應顯示依分類製作的藝文誌風格替代圖，不再只有單色背景與大型「展」字。
24. 搜尋「吟遊於母星之間」：只能有一筆，地點為 **阿波羅畫廊**，**查看官方資訊** 應前往 `https://artemperor.tw/tidbits/19988`。
25. 抽查來源連結與圖片網址：不得出現任何 `facebook.com`、`fb.me`、`fbcdn.net` 或 `facebookusercontent.com`；也不得連到售票平台首頁。每日／手動資料更新會持續驗證售票頁與活動名稱。
26. 搜尋公所、說故事與競賽型內容：`市公所`、`區公所`、`鄉公所`、`鎮公所`及純比賽場次應為零筆；漫畫／寵物／藝術博覽會、漫才與音樂會仍可正常保留。

## 九、常見問題

### 網站仍是舊版

- 先確認最新 Actions 執行為綠色勾勾。
- 強制重新整理；也可用無痕視窗開啟。
- 在網頁原始碼搜尋 `assets/app.js?v=4.2`，確認目前部署的是 V4.2。

### Actions 顯示紅色叉叉

1. 點紅色的執行項目。
2. 點 `update-and-deploy`。
3. 展開第一個紅色步驟查看訊息。
4. 若是 Pages 未啟用，回到 **Settings → Pages → Source: GitHub Actions** 後重跑。
5. 若是權限錯誤，到 **Settings → Actions → General → Workflow permissions**，選 **Read and write permissions**，儲存後重跑。

### 顯示 `netloc ... contains invalid characters`

這代表上游單位把網址與中文聯絡資訊黏在同一個欄位，並不是你的 GitHub 操作錯誤。V4.2 已包含網址安全修正，會保留正確網域並捨棄後方說明，不會再讓整批更新中止。覆蓋 V4.2、提交並推送後，再依第七節手動執行一次工作流程即可。

### 自訂網域失效

確認根目錄的 `CNAME` 還在，而且內容只有你的網域名稱。再到 **Settings → Pages → Custom domain** 重新確認網域。

### 定位沒有出現

- GitHub Pages 與正式自訂網域必須使用 `https://`；一般瀏覽器不會在不安全的 `http://` 網站提供定位。
- Safari：網址列左側點頁面設定 → **位置** → **允許**，重新整理。
- Chrome：網址列左側點網站控制圖示 → **網站設定** → **位置** → **允許**，重新整理。
- 若先前點過封鎖，改成允許後，再按附近頁右上角 **重新取得位置**。

## 十、復原舊版

### GitHub Desktop 復原

1. 打開 GitHub Desktop，左上角確認專案為 `exhibition-hub`、分支為 `main`。
2. 點左上方 **History**。
3. 找到 `Update Exhibition Hub to V4.2`。
4. 右鍵該提交，點 **Revert Changes in Commit**。
5. 回到 **Changes**，確認產生一筆 Revert 提交，點上方 **Push origin**。
6. 到 GitHub 網頁 **Actions → Update data and deploy site**，確認最新部署為綠色。

### 使用備份 ZIP 復原

把第一節保存的舊版 ZIP 解壓後，以第三節相同步驟覆蓋回儲存庫根目錄；Summary 輸入 `Restore Exhibition Hub backup`，點 **Commit to main → Push origin**，最後到 Actions 等待重新部署。

不要使用 `git reset --hard` 或刪除整個專案資料夾來復原；使用 Revert 或備份 ZIP 才能保留可追溯的歷史紀錄。
