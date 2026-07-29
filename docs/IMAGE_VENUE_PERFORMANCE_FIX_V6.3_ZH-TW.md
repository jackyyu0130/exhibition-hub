# V6.3 官方圖片、場館分類與效能修正

## 根因與處理

1. 華山官方圖片檔名中的全形 `｜` 在合併比對時經 NFKC 轉成半形 `|`，伺服器會把它視為不同檔案。V6.3 將文字與 URL 的正規化分離，URL 僅處理控制字元、scheme、host、query 與 fragment，不再改寫 path 字元。
2. Pages 精簡建置原本只帶活動 JSON，漏掉 `data/venues.json` 與 `data/northern_venue_matrix.json`。正式站載入兩檔時得到 404，所有場館因此失去分類。兩檔現已列為必要發布檔案並有回歸測試。
3. 場館面板每次開啟、切換分類與輸入字元，都會對每個場館重新掃描全部活動。V6.3 在資料載入後一次建立 registry 別名索引、活動數與場館目錄；選取場館時只更新按鈕與已選清單，輸入搜尋採 110ms debounce。

## 圖片品質規則

集中式規則會排除：

- OPENTIX flags、預設圖及頁面介面圖；
- Logo、分享按鈕、導覽 icon、定位圖與 Google Static Map；
- Culture Cloud 共用 Banner；
- loading、spinner、placeholder、favicon、GIF、SVG、ICO；
- Facebook 頁面、社團、圖片主機與來源紀錄。

稽核報告位於 `data/update-reports/image-quality-audit.json`。GitHub Actions 會在正式驗證前自動清洗兩份發布資料，`validate_published_data.py` 也會拒絕仍含上述資料的部署。

## 已確認案例

`73d1a911525ba5914e9e1350`「動漫最高祭 Anime Max Festival」：

- 官方頁：`https://www.huashan1914.com/w/huashan1914/exhibition_26060620531407778`
- 官方主視覺：`https://media.huashan1914.com/WebUPD/huashan1914/exhibition/KV_華山官網活動｜1920x1080.jpg`

同一修正也會保護之後所有包含全形標點的官方媒體 URL。
