# Exhibition Hub V3.7 完整替換指南

這份替換包可直接覆蓋既有 GitHub Pages 專案。ZIP 內第一層就是網站根目錄內容；解壓後請複製「裡面的檔案」，不要把整個 ZIP 外層資料夾再包進儲存庫。

## 一、替換前先備份

1. 開啟你的 GitHub 專案首頁，例如 `https://github.com/你的帳號/你的專案`。
2. 在檔案列表右上方點綠色 **Code** 按鈕。
3. 保持在 **Local** 分頁，點 **Download ZIP**。
4. 將下載的舊版 ZIP 改名為 `exhibition-hub-backup-替換日期.zip` 並保存。
5. 若專案根目錄有 `CNAME`，記下內容；若有自訂 `assets/hero-video.mp4`，也請保留。

## 二、認識正確替換位置

解壓 V3.7 ZIP 後，應直接看到下列項目：

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
| `scripts/scraper.py` | `/scripts/scraper.py` | 覆蓋 |
| `data/exhibitions.json` | `/data/exhibitions.json` | 覆蓋；已先清理資料 |
| `data/geocode-cache.json` | `/data/geocode-cache.json` | 覆蓋 |
| `.github/workflows/update-exhibitions.yml` | `/.github/workflows/update-exhibitions.yml` | 覆蓋 |
| `tests/` | `/tests/` | 新增或覆蓋 |
| `CNAME` | `/CNAME` | 若原本存在，保留原檔 |
| `assets/hero-video.mp4` | `/assets/hero-video.mp4` | 若原本存在，保留原檔 |

不要放成 `/Exhibition-Hub-V3.7-full-replacement/index.html`；這會讓 GitHub Pages 找不到首頁。

## 三、建議方式：使用 GitHub Desktop 完整覆蓋

這種方式最容易保留資料夾結構與 `.github` 工作流程。

1. 在 GitHub 專案首頁點 **Code**。
2. 點 **Open with GitHub Desktop**。如果尚未安裝，先點畫面中的下載連結安裝並登入 GitHub。
3. GitHub Desktop 顯示 **Clone a Repository** 時，確認專案名稱與本機路徑，點 **Clone**。
4. 在 GitHub Desktop 上方選單點 **Repository → Show in Explorer**；macOS 是 **Repository → Show in Finder**。
5. 打開已解壓的 V3.7 替換包，選取裡面的全部檔案與資料夾。
6. 把這些內容複製到剛才開啟的儲存庫根目錄。
7. 系統詢問同名檔案時，選 **取代目的地中的檔案／Replace** 或 **全部取代／Apply to All**。
8. 確認原本的 `CNAME` 仍存在；如有自訂 `assets/hero-video.mp4`，也確認仍存在。
9. 回到 GitHub Desktop。左下角 **Summary (required)** 輸入：`Update Exhibition Hub to V3.7`。
10. 點左下角藍色 **Commit to main**。
11. 點上方 **Push origin**，等待推送完成。

如果你的預設分支不是 `main`，先在 GitHub Desktop 上方 **Current Branch** 切到實際部署分支；同時要把 `/.github/workflows/update-exhibitions.yml` 中的 `branches: [main]` 與 `ref: main` 改成該分支名稱。

## 四、不用 GitHub Desktop：GitHub 網頁上傳

1. 在專案首頁確認左上方分支下拉選單顯示 **main**。
2. 點檔案列表右上方 **Add file → Upload files**。
3. 從已解壓的 V3.7 資料夾，把所有內容拖進「Drag files here」區域。務必包含 `assets`、`data`、`scripts`、`tests` 與 `.github`。
4. 等待所有檔名出現在上傳清單；向下捲到 **Commit changes**。
5. 提交訊息輸入 `Update Exhibition Hub to V3.7`。
6. 選 **Commit directly to the main branch**，再點綠色 **Commit changes**。

若瀏覽器沒有接受整個資料夾、看不到 `.github`，或一次上傳失敗，請改用上面的 GitHub Desktop 方式。網頁上傳只會覆蓋同名檔，不會刪除你原有的 `CNAME` 或 Hero 影片。

## 五、設定 GitHub Pages

1. 在專案頁面最上方點 **Settings**。若視窗較窄，Settings 可能藏在上方 **…** 選單內。
2. 左側選單找到 **Code and automation** 區域，點 **Pages**。
3. 在 **Build and deployment** 的 **Source** 下拉選單選 **GitHub Actions**。
4. 不需要選 `/docs`，也不需要設定 Jekyll theme。

## 六、手動更新資料並部署

1. 回到專案上方分頁，點 **Actions**。
2. 左側工作流程清單點 **Update data and deploy site**。
3. 右上方點 **Run workflow**。
4. **Use workflow from** 選 **Branch: main**。
5. 點綠色 **Run workflow**。
6. 等待新的執行項目出現，點進去查看；`update-and-deploy` 顯示綠色勾勾才算完成。
7. 工作流程會依序更新資料、執行 12 項測試、上傳網站並部署 Pages。

若沒有看到 **Run workflow**，先確認你已登入、對此儲存庫有寫入權限，且 `/.github/workflows/update-exhibitions.yml` 已在預設分支。

## 七、上線後逐項驗證

1. 到 **Settings → Pages**，點 **Visit site** 開啟網站。
2. Windows 按 `Ctrl + F5`；macOS 按 `Command + Shift + R`，避免舊版快取。
3. 首頁 Hero：停留或移入滑鼠後仍會每 10 秒更新；點 **再抽一組** 會立即換一組並重新計時。
4. 首頁日期／狀態：選日期，再點目前舉辦、即將舉辦等狀態，畫面只使用同一個結果區並替換內容。
5. 首頁篩選：有選取條件時最右側出現 **清除篩選**。
6. 點 **探索全部展覽**：縣市預設收合；打開第二個縣市時，第一個會自動收合。
7. 任選分類、縣市、場館、日期或狀態：已選條件列最右側出現 **清除全部篩選**。
8. 展覽卡與詳情主圖：應看到清晰完整前景，後方是同一張圖的柔焦填滿背景。
9. 開啟一筆展覽詳情：標題與內文字級應比舊版小；地圖導航查詢應是場館或地址，不是活動名稱。
10. 抽查來源連結：不得連到 Facebook 社團或售票平台首頁；每日／手動資料更新會持續驗證售票頁與活動名稱。

## 八、常見問題

### 網站仍是舊版

- 先確認最新 Actions 執行為綠色勾勾。
- 強制重新整理；也可用無痕視窗開啟。
- 在網頁原始碼搜尋 `assets/app.js?v=3.7`，確認目前部署的是 V3.7。

### Actions 顯示紅色叉叉

1. 點紅色的執行項目。
2. 點 `update-and-deploy`。
3. 展開第一個紅色步驟查看訊息。
4. 若是 Pages 未啟用，回到 **Settings → Pages → Source: GitHub Actions** 後重跑。
5. 若是權限錯誤，到 **Settings → Actions → General → Workflow permissions**，選 **Read and write permissions**，儲存後重跑。

### 自訂網域失效

確認根目錄的 `CNAME` 還在，而且內容只有你的網域名稱。再到 **Settings → Pages → Custom domain** 重新確認網域。

## 九、復原舊版

最簡單方式是把第一節保存的舊版 ZIP 解壓後，以相同步驟覆蓋回儲存庫根目錄並提交。使用 GitHub Desktop 時，也可在 **History** 找到 `Update Exhibition Hub to V3.7`，右鍵選 **Revert Changes in Commit**，再點 **Push origin**。復原後到 **Actions** 手動執行一次部署。
