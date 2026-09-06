# R18.2 附近展場與週日自動更新部署指南

這次更新包含兩個互相獨立的修正：

1. `?view=nearby` 改為以使用者位置為中心，列出 10 公里內的「展場」而不是展覽。每筆資料顯示距離、展場名稱、地址與地圖導航；點圖片或展場名稱會回到該展場的展覽搜尋結果。
2. 週日低資源更新不再因未設定 repository variable 而被跳過。排程仍是每週日台灣時間 03:17；只有把 `WEEKLY_UPDATE_ENABLED` 明確設為 `false` 才會暫停。

## 套用到本機專案

1. Finder 按 `Command + Shift + G`，前往 `/Users/jacky_yu/Documents/GitHub/exhibition-hub`。
2. 將更新包內容覆蓋到專案根目錄；資料夾選「合併」，同名檔案選「取代」。不要用更新包覆蓋專案的 `data/` 資料檔。
3. GitHub Desktop 的 Current Branch 選 `develop`。
4. Summary 輸入 `fix: nearby venues and bounded Sunday update R18.2`，按 **Commit to develop**，再按 **Push origin**。

## 建立與合併 Pull Request

1. GitHub 開啟 **Pull requests → New pull request**。
2. `base` 選 `main`，`compare` 選 `develop`。
3. 建立 PR，等待檢查全部完成；沒有衝突時按 **Merge pull request**。
4. 合併完成後，到 **Actions → Publish prepared website → Run workflow**，分支選 `main`，再按 **Run workflow**。

## 確認 R18.2 已上線

1. 開啟 `https://twexhibition.com/pages-build-manifest.json`，`release` 必須是 `v6.5.0-r18.2`。
2. 開啟 `https://twexhibition.com/?view=nearby`，允許瀏覽器定位。
3. 頁面標題、導覽列與手機版應顯示「附近展場」；清單每筆應有距離、名稱、地址與「地圖導航」。
4. 點展場圖片或名稱，網址應變成 `?view=all&venue=...`，並只顯示該展場的展覽。
5. 在 **Actions → Weekly exhibition update (low resource)** 查看最新週日執行：排程執行的 job 不應再顯示 `skipped`；Summary 會列出更新結果。

## 9/6 沒有更新的原因

9/6 的 GitHub 排程本身有觸發，但舊版條件要求 `vars.WEEKLY_UPDATE_ENABLED == "true"`。因為 repository variable 未設定，job 被 GitHub 標成 `skipped`，不是爬蟲處理中或資料卡住。R18.2 改成預設執行、明確設為 `false` 才暫停。

若要在下個週日以前手動執行：到該 workflow 按 **Run workflow**，輸入 `RUN_WEEKLY_UPDATE`。這是一次受控的手動執行，不會改變日後週日排程。

## 回復與暫停

- 若部署後需要回復，請在 GitHub 對 R18.2 合併提交建立 **Revert**，不要 reset 或 force-push。
- 若只是暫停週日更新，到 repository **Settings → Secrets and variables → Actions → Variables** 將 `WEEKLY_UPDATE_ENABLED` 設為 `false`；恢復時刪除該變數或改回其他值即可。
