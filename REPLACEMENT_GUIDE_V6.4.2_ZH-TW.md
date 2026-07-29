# Exhibition Hub V6.4.2 更新、檢查與復原指南

適用網站：<https://twexhibition.com/>  
適用儲存庫：`jackyyu0130/exhibition-hub`  
正式流程：`develop` → Pull Request → `main` → GitHub Pages

## 一、這次下載哪一個

一般更新請下載：

```text
Exhibition-Hub-V6.4.2-visual-regression-hotfix.zip
```

這是安全更新包，只包含前端、品牌圖檔、測試與指南，不會覆蓋：

```text
data/exhibitions.json
data/exhibitions.enriched.json
```

完整備份另有：

```text
Exhibition-Hub-V6.4.2-full-replacement.zip
```

只有專案遺失、需要在空資料夾重建，或我之後明確請你使用時，才用完整替換包。

## 二、本次修正

1. 左上角「台灣展覽誌」品牌 PNG 會隨更新包上傳。
2. 品牌圖片若暫時載入失敗，仍會顯示文字與票券備援標誌。
3. 場館選擇器的場館分類不再被版面壓成細弧線。
4. Hero 第二張票券向上露出更多票面，第三張同步調整。
5. 手機「探索全台展覽」結果卡片改為一排兩張。
6. 本次沒有修改展覽資料、圖片資料或每日更新程式。

## 三、更新前：GitHub Desktop

### 3.1 開啟正確儲存庫

1. 開啟 **GitHub Desktop**。
2. 左上角點 **Current Repository**。
3. 選 **exhibition-hub**。
4. 若清單沒有它，點 macOS 最上方 **File → Add Local Repository…**。
5. 點 **Choose…**，選：

```text
/Users/jacky_yu/Documents/GitHub/exhibition-hub
```

6. 點 **Add Repository**。

### 3.2 切到 develop 並同步 main

1. 上方點 **Current Branch**。
2. 點 **develop**。
3. 上方點 **Fetch origin**。
4. 若按鈕變成 **Pull origin**，再點一次。
5. 左側確認為 **0 changed files**。
6. macOS 最上方選單點 **Branch → Update from main**。
7. 若出現視窗，點 **Update develop**。
8. 若這個選項不能點，表示 `develop` 已包含最新 `main`，可繼續。

若左側有 `.DS_Store`，不要提交；在檔名按右鍵 → **Discard Changes…**。  
若左側有自己尚未完成的程式，先停止更新並備份，不要直接覆蓋。

## 四、貼入安全更新包

1. 在 Finder 的「下載項目」雙擊：

```text
Exhibition-Hub-V6.4.2-visual-regression-hotfix.zip
```

2. 打開解壓後的：

```text
exhibition-hub-v6.4.2-visual-regression-hotfix
```

3. 回 GitHub Desktop，macOS 最上方點 **Repository → Show in Finder**。
4. 會開啟：

```text
/Users/jacky_yu/Documents/GitHub/exhibition-hub
```

5. 回更新包資料夾，按 `Command + A`，再按 `Command + C`。
6. 切到儲存庫 Finder 視窗，按 `Command + V`。
7. Finder 詢問同名檔案時，勾 **全部套用**，再點 **取代**。
8. 請貼「更新包資料夾裡的內容」，不要把外層資料夾整個放進 repository。

本次主要檔案應包含：

```text
index.html
assets/app.js
assets/styles.css
assets/taiwan-exhibition-journal-logo-v10.png
assets/favicon-48.png
assets/apple-touch-icon.png
tests/test_v642_visual_regressions.py
```

## 五、提交 develop

1. 回 GitHub Desktop。
2. 確認上方為 **Current Branch: develop**。
3. 左側應看到前端、品牌、測試與說明文件。
4. 這兩個檔案不應出現：

```text
data/exhibitions.json
data/exhibitions.enriched.json
```

5. 若意外出現，逐一在檔名按右鍵 → **Discard Changes…**。
6. 左下 **Summary (required)** 輸入：

```text
Apply Exhibition Hub V6.4.2 visual regression fixes
```

7. **Description** 留白。
8. 點 **Commit to develop**。
9. 畫面顯示 **No local changes** 後，點上方 **Push origin**。

## 六、建立 Pull Request

1. 開啟 <https://github.com/jackyyu0130/exhibition-hub>。
2. 點上方 **Pull requests**。
3. 若已有開啟中的 `develop → main` PR，直接點進去；不要再建立第二個。
4. 若沒有，點右側綠色 **New pull request**。
5. 設定：

```text
base: main
compare: develop
```

6. 確認顯示綠色 **Able to merge**。
7. 點 **Create pull request**。
8. 標題輸入：

```text
Apply Exhibition Hub V6.4.2 visual regression fixes
```

9. Description 可留白。
10. 再點一次 **Create pull request**。
11. 先不要立刻合併，等待檢查全部綠色，至少確認：
    - **Validate development changes**
    - **Run project tests**
12. 全綠後依序點：
    - **Merge pull request**
    - **Confirm merge**

## 七、部署到官網前台

1. 儲存庫上方點 **Actions**。
2. 左側點 **Update data and deploy site**。
3. 開啟最上方、分支標示 **main** 的工作。
4. 等 Summary 顯示綠色 **Success**。
5. 若合併後沒有自動出現：
    - 右側點 **Run workflow**。
    - Branch 選 **main**。
    - 再點綠色 **Run workflow**。
6. 成功後等待 2～10 分鐘。
7. 開啟 <https://twexhibition.com/>。
8. macOS Chrome 按 `Command + Shift + R`。
9. 手機 Chrome 建議先開無痕分頁確認，避免舊快取。

## 八、前台檢查

### 8.1 品牌

1. 桌機開首頁。
2. 左上應看到票券 Logo、台灣展覽誌及英文。
3. 直接開啟以下網址也應顯示品牌圖：

```text
https://twexhibition.com/assets/taiwan-exhibition-journal-logo-v10.png?v=6.4.2
```

### 8.2 場館分類

1. 手機點右上漢堡。
2. 點 **場館**。
3. 搜尋列下方應顯示完整的場館類型橢圓按鈕。
4. 不應只剩幾條弧線；按鈕可左右滑動。
5. 點任何分類，場館清單應立即更新。

### 8.3 Hero 票券

1. 回桌機首頁 Hero。
2. 第一張票券保持最前。
3. 第二張應向上露出更多票面。
4. 第三張也應清楚形成後方扇形層次。
5. 懸浮票券仍可暫停輪播並開啟預覽。

### 8.4 手機探索卡片

1. 手機點 **探索展覽**。
2. 分類／日曆／地區場館入口下方的結果應為一排兩張。
3. 圖片維持正方形。
4. 標題最多三行，不能推擠到旁邊卡片。
5. 收藏按鈕、狀態徽章仍在各自卡片內。

## 九、GitHub 網頁直接上傳備案

只有 GitHub Desktop 無法使用時才採用：

1. GitHub 儲存庫上方點 **Code**。
2. 左上分支選擇器切到 **develop**。
3. 點 **Add file → Upload files**。
4. 將安全更新包內的檔案依原路徑拖入。
5. 不要上傳 `data/`，也不要刪除儲存庫內其他檔案。
6. Commit message 輸入：

```text
Apply Exhibition Hub V6.4.2 visual regression fixes
```

7. 選 **Commit directly to the develop branch**。
8. 點 **Commit changes**。
9. 再依「六、建立 Pull Request」繼續。

注意：GitHub 網頁上傳大量巢狀資料夾較容易放錯路徑，仍優先使用 GitHub Desktop。

## 十、錯誤與復原

### 10.1 Push 出現 Newer Commits on Remote

1. 點視窗的 **Fetch**。
2. 再點上方 **Pull origin**。
3. 若出現資料 JSON 衝突，不要逐筆解兩千多項；先停止並保留畫面。

### 10.2 尚未 Commit，想全部復原

1. GitHub Desktop 上方點 **Branch**。
2. 點 **Discard All Changes…**。
3. 再點 **Discard Changes**。

只復原單一檔案：左側檔名按右鍵 → **Discard Changes…**。

### 10.3 已 Commit，但尚未 Push

1. GitHub Desktop 左下角點 **Undo**。
2. 檔案會回到 Changes。
3. 可重新檢查或按 **Discard All Changes…**。

### 10.4 PR 還沒合併

1. 不要點 Merge。
2. 回 GitHub Desktop 的 `develop` 修正或復原。
3. Push 後，原 PR 會自動更新。

### 10.5 已合併到 main

1. GitHub → **Pull requests → Closed**。
2. 打開 V6.4.2 PR。
3. 點 **Revert**。
4. 建立 Revert PR。
5. 等檢查全綠後合併，再等 Actions 部署完成。

### 10.6 意外出現大量資料衝突

這次安全包沒有資料檔。若看到：

```text
data/exhibitions.json
data/exhibitions.enriched.json
```

在尚未 Commit 時，分別對檔案按右鍵 → **Discard Changes…**。  
不要使用 `checkout --ours`、`checkout --theirs` 或手動解數千個衝突；若已進入
merge 狀態，先點 **Abort Merge**，再重新同步 `develop`。
