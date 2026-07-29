# Exhibition Hub V6.4.1 更新與復原指南

適用網站：<https://twexhibition.com/>  
適用儲存庫：`jackyyu0130/exhibition-hub`  
更新流程：`develop` → Pull Request → `main` → GitHub Pages

## 這次要下載哪一個

建議使用：

```text
Exhibition-Hub-V6.4.1-mobile-drawer-hotfix.zip
```

這個安全更新包只放本次前端、favicon、測試與指南，不會覆蓋每日自動更新的
`data/exhibitions.json` 或 `data/exhibitions.enriched.json`，因此較不容易再次產生
兩千多筆資料衝突。

完整備份另有：

```text
Exhibition-Hub-V6.4.1-full-replacement.zip
```

一般更新請用 hotfix；只有整個專案遺失或需要重建時才使用 full replacement。

## 一、本次修正

1. 手機漢堡抽屜不再被黏性 Header 的模糊效果限制。
2. 開啟抽屜時固定原頁面，關閉後回到原捲動位置。
3. 抽屜僅允許上下滑，左右拖曳不再把頁面拉寬或露出空白。
4. 分類順序與探索頁完全一致；前四個固定為演唱會、快閃店、動漫、美術。
5. 探索展覽、附近展覽、我的收藏移到搜尋列下方。
6. 分類、日曆、地區／場館改用不同的淺奶茶色。
7. 縣市第二層抽屜每次從頂端開啟，寬度與主抽屜一致。
8. 場館選擇器的清單獨立捲動；底部按鈕固定在抽屜版面底端，不再浮在內容中間。
9. 網站 favicon 改用票券「展」Logo。

## 二、更新前的按鈕與路徑

### 2.1 開啟正確儲存庫

1. 開啟 **GitHub Desktop**。
2. 左上角點 **Current Repository**。
3. 選 **exhibition-hub**。
4. 若看不到，點 macOS 上方選單 **File → Add Local Repository… → Choose…**。
5. 選擇：

```text
/Users/jacky_yu/Documents/GitHub/exhibition-hub
```

6. 點 **Add Repository**。

### 2.2 切到 develop 並同步

1. 上方點 **Current Branch**。
2. 選 **develop**。
3. 點上方 **Fetch origin**。
4. 如果按鈕變成 **Pull origin**，再點一次 **Pull origin**。
5. 左側確認顯示 **0 changed files**。
6. macOS 最上方選單點 **Branch → Update from main**。
7. 若跳出確認視窗，點 **Update develop**；若選項是灰色或沒有新內容，表示
   `develop` 已包含 `main` 最新版本，可直接繼續。

若有 `.DS_Store`，不要提交它；可取消勾選。若有自己的程式修改，先輸入暫存
Summary、點 **Commit to develop**，再點 **Push origin**。

## 三、貼入安全更新包

1. 在 Finder「下載項目」雙擊：

```text
Exhibition-Hub-V6.4.1-mobile-drawer-hotfix.zip
```

2. 打開解壓後的：

```text
exhibition-hub-v6.4.1-mobile-drawer-hotfix
```

3. 在 GitHub Desktop 上方選單點 **Repository → Show in Finder**。
4. Finder 會開啟：

```text
/Users/jacky_yu/Documents/GitHub/exhibition-hub
```

5. 回更新包資料夾，按 `Command + A`、再按 `Command + C`。
6. 到儲存庫 Finder 視窗，按 `Command + V`。
7. 出現同名檔案時，勾 **全部套用**，再點 **取代**。
8. 不要把外層 `exhibition-hub-v6.4.1-mobile-drawer-hotfix` 資料夾整個拖進
   repository；要貼的是它裡面的內容。

本次執行檔應包含：

```text
index.html
assets/app.js
assets/styles.css
assets/favicon-48.png
assets/apple-touch-icon.png
tests/test_v641_mobile_drawers.py
```

## 四、GitHub Desktop 提交

1. 回到 GitHub Desktop。
2. 確認上方仍為 **Current Branch: develop**。
3. 左側檔案全部保持勾選，但 `.DS_Store` 不要勾。
4. 左下 **Summary (required)** 輸入：

```text
Apply Exhibition Hub V6.4.1 mobile drawer stability fixes
```

5. **Description** 可留白。
6. 點 **Commit to develop**。
7. 畫面變成 **No local changes** 後，點上方 **Push origin**。

## 五、建立 Pull Request

1. 開啟：

```text
https://github.com/jackyyu0130/exhibition-hub
```

2. 點上方 **Pull requests**。
3. 若已經有 `develop → main` 的開啟中 PR，直接點進去；剛推送的 commit
   會自動加入，不要重建。
4. 若沒有，點右側綠色 **New pull request**。
5. 上方設定：

```text
base: main
compare: develop
```

6. 確認顯示綠色 **Able to merge**。
7. 點 **Create pull request**。
8. PR 標題輸入：

```text
Apply Exhibition Hub V6.4.1 mobile drawer stability fixes
```

9. Description 可留白，再點一次 **Create pull request**。
10. 等待檢查全部綠色，至少確認：
    - **Validate development changes**
    - **Run project tests**
11. 全綠後依序點：
    - **Merge pull request**
    - **Confirm merge**

## 六、部署

1. GitHub 儲存庫上方點 **Actions**。
2. 左側點 **Update data and deploy site**。
3. 開啟最上方且分支標示為 **main** 的工作。
4. 等到 Summary 顯示綠色 **Success**。
5. 若沒有自動出現工作，右側點 **Run workflow**：
    - Branch 選 **main**
    - 再點綠色 **Run workflow**
6. 成功後等待 2～10 分鐘。
7. 打開 <https://twexhibition.com/>。
8. macOS Chrome 按 `Command + Shift + R`；手機可先用無痕分頁檢查。

## 七、手機驗證清單

1. 在首頁先向下滑一段，再點右上漢堡。
2. 背景應停在原處；只有右側抽屜能上下滑。
3. 抽屜向左或向右拖，不應出現空白頁，也不應改變整頁寬度。
4. 搜尋列下方依序顯示：探索展覽、附近展覽、我的收藏。
5. 預設分類由左至右為：演唱會、快閃店、動漫、美術。
6. 點 **展開全部** 後，順序必須與探索頁相同。
7. 分類、日曆、地區／場館三區應有不同但低彩度的奶茶底色。
8. 抽屜滑到底後仍能正常關閉，不會露出底下頁面。
9. 點 **地區**，第二層選單應從頂端出現，且不會只剩半頁。
10. 點 **場館**，展開台北市或其他縣市並向下滑：
    - 只有場館清單移動。
    - 「清除全部／查看展覽」保持在抽屜最底端。
    - 按鈕不會浮在名單中央。

## 八、favicon 驗證

先直接打開：

```text
https://twexhibition.com/assets/favicon-48.png?v=6.4.1
```

應看到票券「展」圖示。瀏覽器分頁通常在強制重新整理後更新；Google 搜尋結果
不會即時變更，必須等待 Google 下一次重新檢索，可能需要數天到數週。

## 九、常見問題與復原

### 9.1 Push 時出現 Newer Commits on Remote

1. 點 **Fetch**。
2. 再點上方 **Pull origin**。
3. 若產生衝突，先不要隨意選 `ours` 或 `theirs`，尤其不要手動處理數千筆 JSON。

### 9.2 尚未 Commit，想全部復原

1. GitHub Desktop 上方點 **Branch**。
2. 點 **Discard All Changes…**。
3. 再點 **Discard Changes**。

若只要復原單一檔案：在左側檔名按右鍵 → **Discard Changes…**。

### 9.3 已 Commit，但還沒 Push

1. GitHub Desktop 左下角點 **Undo**。
2. 變更會回到 Changes，可重新檢查或丟棄。

### 9.4 已合併到 main

1. GitHub → **Pull requests → Closed**。
2. 打開剛合併的 V6.4.1 PR。
3. 點 **Revert**。
4. 建立 Revert PR，等檢查綠色後合併。

### 9.5 意外出現資料 JSON 大量衝突

本次 hotfix 不應修改資料檔。若左側出現：

```text
data/exhibitions.json
data/exhibitions.enriched.json
```

而且你沒有刻意更新資料，請在尚未 Commit 時分別對檔案按右鍵：

```text
Discard Changes…
```

再提交其餘 V6.4.1 前端檔案。不要在 GitHub Desktop 逐筆解兩千多個衝突。
