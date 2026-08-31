# R17.1 票價與分類顯示修正

這個小更新包要覆蓋在已安裝 R17 的 `develop` 分支上。若 Pull Request #61 仍為 Open，不要先合併；推送 R17.1 後，#61 會自動加入這次修正。

## 已修正內容

1. 展覽卡片與詳細頁現在共用同一個票價顯示規則。
2. 免費活動只顯示「免費入場」。
3. 其他有價、價格區間、售票說明或長段票價文字，一律只顯示「票價請見活動頁面」。
4. 原始票價仍保留在資料中供搜尋與後續處理，但不直接顯示在公開版面。
5. 詳細頁分類標籤、分類數量與分類列表共用同一個 `eventCategories` 邏輯。
6. 任何展覽只要詳細頁出現「動漫」，就會同時出現在「動漫」分類列表。
7. 前端快取版本已提升為 `6.5.0-r17.1`，部署後瀏覽器會下載修正版程式。

## 全資料稽核結果

- 公開展覽：693 筆。
- 分類關聯：739 組。
- 單一分類展覽：647 筆。
- 複合分類展覽：46 筆。
- 主分類與分類陣列不一致：0 筆。
- 不支援的分類標籤：0 筆。
- 詳細頁有標籤、但分類列表找不到：0 筆。
- 重新套用 R17 語意分類後仍不一致：0 筆。
- 動漫標籤展覽：13 筆。
- 動漫列表可找到：13 筆。
- 動漫列表遺漏：0 筆。
- 公開版面直接顯示原始票價的位置：0 處。

完整結果：`data/update-reports/category-display-consistency-r17-1.json`。

## 安裝到目前的 Pull Request #61

1. 先不要按 GitHub 網頁上的 `Merge pull request`。
2. 解壓縮 `exhibition-hub-r17.1-price-category-hotfix.zip`。
3. Finder 按 `Command + Shift + G`。
4. 貼上 `/Users/jacky_yu/Documents/GitHub/exhibition-hub`，按 Enter。
5. 將解壓後資料夾內的所有內容拖入上述根目錄；詢問同名檔案時選「取代」或「合併」。
6. 開啟 GitHub Desktop，Current Repository 選 `exhibition-hub`。
7. Current Branch 確認為 `develop`。
8. 左側至少應看到 `assets/app.js`、`index.html`、`VERSION.txt` 與 R17.1 報告／測試檔。
9. Summary 輸入：`fix: unify all price labels and category listings R17.1`
10. 按 `Commit to develop`。
11. 按右上角 `Push origin`。
12. 回到 Pull Request #61；它應自動多一筆 R17.1 commit，不需要再建立新的 Pull Request。
13. 等所有必要檢查變綠，再按 `Merge pull request` → `Confirm merge`。
14. 到 `Actions` 等 Pages／Publish workflow 完成並顯示綠色勾勾。

如果 #61 已經合併，仍照步驟 2–11 推送；接著建立新的 Pull Request，`base: main`、`compare: develop`，等檢查通過後合併。

## 發佈後確認

1. 開啟任一有價展覽詳細頁，票價必須只顯示「票價請見活動頁面」。
2. 展覽卡片不得出現 `260`、`NT$450–470` 或其他完整票價內容。
3. 進入「動漫」分類，應顯示 13 筆資料；其中包含 8 月及 9 月的「劇場版 吉伊卡哇 人魚島的秘密」。
4. 若仍看到舊畫面，Mac Chrome 按 `Command + Shift + R` 強制重新整理。
5. iPhone Safari 可關閉舊分頁再重新開啟；仍未更新時，到「設定 → Safari → 進階 → 網站資料」刪除 `twexhibition.com` 的網站資料。

## 驗證結果

- JavaScript 語法檢查：通過。
- 專案完整測試：293 項全部通過。
- 693 筆語意分類重算：0 筆差異。
- 詳細頁分類與分類列表交叉檢查：0 筆遺漏。
