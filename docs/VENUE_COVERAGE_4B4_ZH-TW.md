# 4-B-4｜場館覆蓋完整度檢查

Registry Dry Run 61 已確認：

- 2,354 筆活動全部完成處理
- 1,093 筆至少配對一個場館
- 88 筆為多場館活動
- `ambiguous` 已歸零

但「至少配對一個場館」不代表巡迴活動的所有場次都已辨識。
本批次新增場館文字逐筆覆蓋檢查，避免部分配對被誤認為完整。

## 新增欄位

```json
{
  "venueCoverageStatus": "complete",
  "venueValueCount": 2,
  "matchedVenueValueCount": 2,
  "unmatchedVenueValues": []
}
```

`venueCoverageStatus`：

- `complete`：每個原始場館／場次文字均已辨識
- `partial`：至少辨識一個場館，但仍有未辨識場次
- `none`：沒有任何場館被辨識

## Dry Run 報告新增

- `venueCoverageStatusCounts`
- `completeCoveragePercentage`
- `topUnmatchedVenueValues`
- `samples.partialVenueEvents`

本批次仍不覆寫 `data/exhibitions.json`。
