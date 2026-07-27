# 4-B-3｜多場館活動支援

本批次修正 Registry Dry Run 中 28 筆 `ambiguous`。

這些資料不是場館無法判定，而是一場活動確實列出兩個以上場館，
例如：

- 高雄市電影館＋內惟藝術中心
- 國家兩廳院＋臺北市中山堂＋苗北藝文中心

## 新增欄位

每筆活動保留既有相容欄位：

```json
{
  "venueId": "primary-venue",
  "venueName": "主要場館"
}
```

並新增：

```json
{
  "venueIds": [
    "first-venue",
    "second-venue"
  ],
  "venueNames": [
    "第一場館",
    "第二場館"
  ],
  "venueMatches": [
    {
      "venueId": "first-venue",
      "venueName": "第一場館",
      "method": "registry_exact",
      "confidence": 1.0,
      "matchedValue": "原始場館文字",
      "matchedAlias": "正規化別名"
    }
  ]
}
```

## 狀態

- 單一場館：`matched`
- 多個已辨識場館：`matched_multiple`
- 無法辨識：`unmatched`
- 真正的別名衝突：`ambiguous`

本批次仍是 Dry Run，不覆寫 `data/exhibitions.json`。
