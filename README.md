# 台灣展覽誌 V3

這是一套可直接部署到 GitHub Pages 的純前端展覽網站，不需要 Node.js 或建置工具。

## 專案結構

```text
exhibition-hub/
├── index.html
├── assets/
│   ├── app.js
│   ├── styles.css
│   ├── hero-art.svg
│   └── hero-video.mp4        # 選用；可保留原本影片
├── data/
│   ├── README.md
│   └── exhibitions.json      # 首次 Action 執行後自動產生
├── scripts/
│   └── scraper.py
├── requirements.txt
├── .nojekyll
└── .github/workflows/
    └── update-exhibitions.yml
```

## 最省事的替換方式

1. 下載並解壓縮 ZIP。
2. 將 ZIP 內所有檔案上傳到 GitHub 儲存庫根目錄，選擇覆蓋同名檔案。
3. 不需要手動修改 HTML、CSS 或 JavaScript。
4. 上傳後，`Update data and deploy site` GitHub Action 會因 `push` 自動執行。
5. 工作流程會產生或更新 `data/exhibitions.json`，接著直接部署 GitHub Pages。

## 保留原本 Hero 影片

新版預設附有 `assets/hero-art.svg`，即使沒有影片也能顯示完整 Hero。
若要沿用原本影片，請保留或上傳：

```text
assets/hero-video.mp4
```

## 自動資料更新

- 每天台灣時間約 05:25 自動執行。
- 也能到 GitHub 的 **Actions → Update data and deploy site → Run workflow** 手動更新。
- `scraper.py` 會讀取文化部開放資料，並保留 `data/exhibitions.json` 中仍在有效日期內的既有自訂活動，避免覆蓋你原本額外收集的展覽。

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
