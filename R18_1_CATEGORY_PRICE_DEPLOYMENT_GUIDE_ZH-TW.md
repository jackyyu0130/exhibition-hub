# R18.1 分類與票價正式站部署修正版

這一版是針對「資料已修正，但正式官網仍顯示舊結果」的部署鎖定版本，完整包含 R18 的全分類資料與 R18.1 前端修正。

## 這次鎖定的兩個問題

1. 分類頁不再只看主分類。任何展覽只要 `categories` 含有該分類，就一定會出現在該分類結果中。
2. 所有公開票價畫面共用同一個函式：免費顯示「免費入場」；其餘一律顯示「票價請見活動頁面」。卡片與詳細頁都不再顯示 `260`、`NT$450–470`、套票長文字等原始內容。

R18.1 也把前端快取鍵、HTML 版本標記與 Pages 建置清單一併提升為 `6.5.0-r18.1`，可以辨認正式站是否真的部署成功。

## 已驗證的吉伊卡哇案例

下列兩筆資料皆保留主分類「電影」，並含有次分類「動漫」，因此會同時出現在電影與動漫分類：

- `8月高雄市電影館｜劇場版 吉伊卡哇 人魚島的秘密（中配版）`
- `9月高雄市電影館｜劇場版 吉伊卡哇 人魚島的秘密`

## 安裝與發佈

1. 解壓縮 `exhibition-hub-r18.1-category-price-deployment-lock.zip`。
2. Finder 按 `Command + Shift + G`，前往 `/Users/jacky_yu/Documents/GitHub/exhibition-hub`。
3. 將解壓後的所有內容拖入專案根目錄；同名檔案選「取代」，資料夾選「合併」。
4. GitHub Desktop 確認 Current Branch 是 `develop`。
5. Summary 輸入：`fix: deploy category and price consistency R18.1`
6. 按 `Commit to develop`，再按 `Push origin`。
7. 在 Pull Request 中等檢查完成後，合併 `develop` 到 `main`。
8. 到 Actions 執行 `Publish prepared website`，等待綠色勾勾。

## 如何確認正式站真的換版

1. 開啟 `https://twexhibition.com/pages-build-manifest.json`，最上方 `release` 必須是 `v6.5.0-r18.1`。
2. 再開啟 `https://twexhibition.com/?view=all&category=%E5%8B%95%E6%BC%AB&release=r18.1`。
3. 動漫分類應包含上述兩筆吉伊卡哇電影；目前完整 R18 資料的動漫關聯共 23 筆。
4. 任意開啟付費展覽，卡片與詳細頁都只能顯示「票價請見活動頁面」。
5. 若 manifest 已是 R18.1 但畫面仍舊，Mac Chrome 按 `Command + Shift + R`；iPhone Safari 關閉舊分頁後重新開啟。

## 驗證結果

- Pages 實際建置產物版本：`v6.5.0-r18.1`
- JavaScript 語法檢查：通過
- 專案完整測試：299 項全部通過
- 吉伊卡哇電影動漫分類回歸案例：2 筆通過
- 原始付費金額公開顯示路徑：0
