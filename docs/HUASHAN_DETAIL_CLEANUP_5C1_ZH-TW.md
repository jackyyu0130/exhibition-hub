# 5-C.1｜華山詳情頁資料清理

## 為什麼需要此階段

5-C Live Dry Run 技術上成功抓取 8 個詳情頁，但實際輸出發現：

- `priceText` 混入 JavaScript
- `venueNames` 混入活動介紹、適合年齡與聯絡資訊
- `imageUrls` 收到「相關活動」圖片
- `externalUrls` 收到華山共用社群及徵才連結
- `performance_` 詳情頁未穩定判定為表演

這些資料若直接進入 5-D 去重，可能造成錯誤場館、錯誤票價與錯誤圖片。

## 修正內容

### HTML 文字清理

不再讀取以下標籤內的文字：

- `script`
- `style`
- `noscript`
- `template`
- `svg`

因此不會再出現：

- `event.preventDefault()`
- `e.preventDefault()`
- `$('[data-colorboxGroup]')`

### 主活動內容範圍

詳情頁欄位只讀取主活動內容，遇到以下區段停止：

- `相關活動`
- `如何來華山`

避免其他活動的票價、圖片或介紹混入目前活動。

### 場館名稱

只保留具有場館特徵且長度合理的文字，例如：

- 東3A館
- 烏梅劇院
- 果酒練舞場
- 中4B館1F-3.4（芳釀所）

排除：

- 活動介紹句子
- 適合年齡
- 票價
- 場次
- 聯絡資訊

### 票價

只保留主活動範圍內具有明確票價訊號的文字。

排除：

- JavaScript
- 網址
- 適合年齡
- 上映時間
- 場次
- 相關活動票價

### 圖片與外部連結

- 圖片最多保留 4 張
- 主視覺與列表圖優先
- 排除華山共用 Facebook、Instagram、YouTube 與 104 徵才連結

### 表演類型

`/performance_` 詳情頁與「表藝節／劇場／音樂會／舞台劇」標題，
會優先正規化為：

- `sourceCategory: 表演藝術`
- `contentTypeHint: 表演`

## 發布狀態

本修正不修改：

- 前台設計
- `data/exhibitions.json`
- GitHub Workflow
- 正式網站資料

修正後請再次執行現有的華山詳情頁 Dry Run。
