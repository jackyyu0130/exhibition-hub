# Exhibition Hub V4.1／台灣展覽誌

這是一套可直接部署到 GitHub Pages 的純前端展覽網站，不需要 Node.js 或建置工具。

## 專案結構

```text
exhibition-hub/
├── index.html
├── assets/
│   ├── app.js
│   ├── styles.css
│   ├── taiwan-exhibition-journal-logo-v8.png
│   ├── exhibition-fallback-sprite-v40.png
│   ├── hero-art.svg
│   └── hero-video.mp4        # 選用；可保留原本影片
├── data/
│   ├── README.md
│   ├── curated-overrides.json
│   └── exhibitions.json      # 首次 Action 執行後自動產生
├── scripts/
│   └── scraper.py
├── requirements.txt
├── .nojekyll
└── .github/workflows/
    └── update-exhibitions.yml
```

## 完整替換

完整逐步操作、每一個點擊位置、檔案路徑、驗證與復原方式，請見
[`REPLACEMENT_GUIDE_V4.1_ZH-TW.md`](REPLACEMENT_GUIDE_V4.1_ZH-TW.md)。

最短流程：解壓縮後，把 ZIP 內的內容（不是外層資料夾）複製到 GitHub
儲存庫根目錄並覆蓋同名檔案，提交到 `main`，再執行
**Actions → Update data and deploy site → Run workflow**。

## 保留原本 Hero 影片

新版預設附有 `assets/hero-art.svg`，即使沒有影片也能顯示完整 Hero。
若要沿用原本影片，請保留或上傳：

```text
assets/hero-video.mp4
```

## 自動資料更新

- 每天台灣時間約 05:25 自動執行。
- 也能到 GitHub 的 **Actions → Update data and deploy site → Run workflow** 手動更新。
- `scraper.py` 會讀取文化部開放資料，補抓 OPENTIX、活動官方頁與主要售票頁的圖片／介紹。
- 同名同展期活動會跨資料來源合併，`data/curated-overrides.json` 可保存人工核實過的網址與場館校正。
- 售票及官方網址會以活動名稱交叉比對；不相符時改用已驗證的相關頁，找不到正確頁時清除錯誤連結。
- 發布前排除所有 Facebook 頁面、社團、短網址與圖片主機；也排除地方小型社團活動、各級公所活動、純競賽場次，以及講座、講習、研習、課程、工作坊、營隊。
- 漫畫／寵物／商業博覽會、漫才、音樂會與比賽得獎作品展等實質展演內容仍會保留。
- 首頁 Hero 使用暖灰米色滿版紙張底區、平面城市插畫地圖與約 16:10 橫向票券拼貼；票券加入雙線類型框、深色條碼及淡色圓章浮水印，首頁展覽卡統一為 1:1。
- 場館探索列一次呈現三列、每列四張矮版卡片；優先使用場館影像，再依序嘗試館內展覽主視覺，全部失效才顯示精緻分類圖，並支援橫向滑動。
- 活動圖片全部失效時，使用依分類生成的日式藝文誌主視覺；不會冒用其他活動圖片。
- Hero 每 15 秒更換推薦，滑鼠或鍵盤焦點停留在 Hero／票券時暫停剩餘倒數。
- 附近展覽進頁自動請求定位，只列出 20 公里內活動並提供距離與 Google Maps 導航。
- 我的收藏在桌機為四欄 1:1 方卡，並依收藏類型推薦可橫向瀏覽的相似展覽。

## 資料欄位

前端支援以下欄位：

```json
{
  "id": "活動識別碼",
  "title": "展覽名稱",
  "description": "介紹",
  "sourceUrl": "官方網址",
  "image": "圖片網址",
  "categories": ["美術", "攝影"],
  "startDate": "2026-07-01",
  "endDate": "2026-09-30",
  "locationName": "展演場館",
  "address": "地址",
  "region": "台北市",
  "latitude": 25.0,
  "longitude": 121.5,
  "price": "免費"
}
```

## 本機預覽

直接雙擊 `index.html` 時，瀏覽器可能阻擋 JSON 載入。請在專案資料夾執行：

```bash
python -m http.server 8000
```

然後開啟 `http://localhost:8000`。

## 測試

```bash
python -m unittest discover -s tests -v
```
