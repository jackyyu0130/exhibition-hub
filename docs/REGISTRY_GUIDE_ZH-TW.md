# 全台活動來源與場館登錄架構

這一階段只建立資料架構與驗證規則，不會直接啟用新的網站爬蟲，也不會改寫 `data/exhibitions.json`。

## 1. 兩個主檔

### `data/source_registry.json`

管理「去哪裡抓資料」。

每筆來源包含：

- `id`：穩定且唯一的來源代號
- `layer`：全國基礎、售票平台、場館官方、地方政府或社群探索
- `sourceType`：API、售票平台、場館網站等
- `parser`：未來要使用的解析器
- `status`：`active`、`planned`、`paused`、`retired`
- `enabled`：是否真的進入排程
- `coverageRegions`：全台或指定縣市
- `contentTypes`：來源可能提供的活動類型
- `venueIds`：來源與哪些固定場館相連

尚未完成 Collector 的來源必須維持：

```json
{
  "status": "planned",
  "enabled": false
}
```

### `data/venues.json`

管理「活動發生在哪裡」。

同一場館的常用名稱集中放在 `aliases`，例如：

```json
{
  "id": "taipei-music-center",
  "name": "臺北流行音樂中心",
  "aliases": [
    "台北流行音樂中心",
    "北流",
    "北流表演廳"
  ]
}
```

這樣活動資料出現「北流」時，就能統一轉成正式名稱。

## 2. 活動內容類型

目前支援：

- `exhibition`
- `art_exhibition`
- `pop_culture`
- `expo`
- `concert`
- `music_festival`
- `performance`
- `popup`
- `market`
- `festival`

活動可以同時具有多個 `contentTypes`，但會有一個主要的 `contentType`。

例如漫畫博覽會：

```json
{
  "contentType": "expo",
  "contentTypes": [
    "expo",
    "pop_culture"
  ]
}
```

## 3. 驗證方式

在專案根目錄執行：

```bash
python scripts/validate_registries.py
python -m unittest discover -s tests -v
```

成功時 `validate_registries.py` 會輸出：

```json
{
  "succeeded": true,
  "errors": []
}
```

## 4. 新增來源

先新增為 `planned` 且 `enabled: false`。

只有在以下項目完成後才能啟用：

1. 已確認官方列表頁或 API。
2. Collector 已完成。
3. Normalizer 已完成。
4. 測試已完成。
5. Dry Run 成功。
6. 去重與品質規則已確認。

## 5. 新增場館

新增場館時：

1. 使用穩定英文 `id`。
2. 使用正式中文名稱作為 `name`。
3. 將俗稱、台／臺差異、館別名稱加入 `aliases`。
4. 設定縣市與場館類型。
5. 有官方來源時，再填入 `sourceIds`。
6. 執行驗證，確認沒有別名衝突。

## 6. 目前不做的事情

本批次不會：

- 啟用華山、松菸或其他新 Collector
- 抓取 Threads 貼文
- 修改前台篩選器
- 發布新的演唱會或展覽
- 刪除既有的 `data/venue-aliases.json`

下一批次才會將現有場館別名逐步遷移到新主檔，並建立第一個共用場館解析器。
