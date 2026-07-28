# 5-C｜華山詳情頁與欄位正規化

## Live Dry Run 範圍

- 先抓完整活動列表
- 再抓前 8 筆詳情頁，避免對官方網站產生過量請求
- 不寫入 `data/exhibitions.json`
- 不變更正式網站活動數量

## 詳情頁欄位

- `officialUrl`
- `sourceCategory`
- `contentTypeHint`
- `organizer`、`organizers`
- `venueName`、`venueNames`
- `address`
- `regionCanonical`
- `startTime`、`endTime`、`timeText`
- `admission`、`priceText`
- `imageUrl`、`imageUrls`
- `description`
- `externalUrls`
- `editorialStatus`

## 票價判定

- 明確出現免費入場、免費參觀、自由入場或免票：`free`
- 明確出現售票制、NTD、NT$、金額、全票等：`paid`
- 沒有足夠資訊：`unknown`

## 安全策略

- 詳情頁失敗不會讓整批 Collector 中止
- 失敗紀錄保留列表資料並輸出 warning
- 論壇講座標記為 `exclude_review`
- 華山來源仍維持 `planned` 與 `enabled: false`
