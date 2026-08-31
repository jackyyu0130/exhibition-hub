# R18 全分類語意稽核與顯示一致性修正版

R18 取代 R17 與 R17.1。這次不是只修「動漫」，而是把官網全部 17 個公開分類一起重新稽核，並讓後端資料、首頁數量、分類頁、卡片及詳細頁共同使用同一份分類結果。

## 已完成內容

1. 重新檢查 693 筆原公開資料的主分類與複合分類。
2. 修正 91 筆分類，包括音樂／表演、舞蹈／表演、電影／音樂、市集／表演、美術／歷史、美術／科技、快閃店／動漫等跨類型誤判。
3. 移除 18 筆講堂、對談、導覽、工作坊、Podcast、保證金繳交等非展覽活動；公開展覽變為 675 筆。
4. 演唱會、音樂、表演、舞蹈、電影等互斥活動形式的衝突為 0。
5. 動漫不只檢查動漫展，也涵蓋有明確證據的動畫音樂會、動畫電影與角色快閃店，目前共有 23 筆分類關聯。
6. 美術、設計、歷史、自然、科技等主題，不再因演出名稱中的比喻或介紹文字中的製作名詞而誤加分類。
7. 前端讀取 `data/exhibitions.curated.json` 時，直接採用已稽核的 `category/categories`；詳細頁有的分類，分類列表一定找得到同一活動。
8. R17.1 票價規則保留：免費只顯示「免費入場」，其他有價活動一律顯示「票價請見活動頁面」。
9. 前端快取版本提升為 `6.5.0-r18`。

完整稽核結果位於 `data/update-reports/category-semantic-audit-r18.json`。

## 安裝到 GitHub 專案

1. 先不要在 GitHub 網頁按 `Merge pull request`。
2. 解壓縮 `exhibition-hub-r18-all-category-semantic-audit.zip`。
3. Finder 按 `Command + Shift + G`。
4. 貼上 `/Users/jacky_yu/Documents/GitHub/exhibition-hub`，按 Enter。
5. 把解壓後資料夾內的所有內容拖入專案根目錄；遇到同名檔案選「取代」，資料夾選「合併」。
6. 開啟 GitHub Desktop，確認 Current Repository 是 `exhibition-hub`、Current Branch 是 `develop`。
7. 左側應看到 `assets/app.js`、`data/exhibitions.curated.json`、`scripts/exhibition_hub/curation.py`、R18 報告與測試等檔案。
8. Summary 輸入：`fix: audit all exhibition categories R18`
9. 按 `Commit to develop`，再按 `Push origin`。
10. 若 Pull Request #61 仍是 Open，它會自動加入 R18 commit，不要重建 PR。
11. 若 #61 已合併，建立新的 Pull Request：`base: main`、`compare: develop`。
12. 等必要檢查全部變綠，再按 `Merge pull request` → `Confirm merge`。
13. 到 `Actions` 等 Pages／Publish workflow 完成並顯示綠色勾勾。

## 發佈後檢查

1. 首頁應顯示 675 筆收錄活動，更新時間應為這次 R18 資料更新時間。
2. 「動漫」分類應顯示 23 筆，包含吉伊卡哇電影、宮崎駿動畫音樂會、咖波快閃店與動漫展。
3. 隨機開啟音樂、表演、舞蹈、電影、美術、設計、歷史、科技、市集與親子分類，詳細頁標籤與分類列表應一致。
4. 有價展覽的卡片與詳細頁只應顯示「票價請見活動頁面」。
5. 若仍看到舊畫面，Mac Chrome 按 `Command + Shift + R`；iPhone Safari 關閉舊分頁後重開，必要時刪除 `twexhibition.com` 網站資料。

## 驗證結果

- JavaScript 語法檢查：通過。
- 專案完整測試：299 項全部通過。
- 公開分類重新套用後差異：0 筆。
- 主分類與第一分類不一致：0 筆。
- 不支援分類標籤：0 筆。
- 互斥活動形式衝突：0 筆。
