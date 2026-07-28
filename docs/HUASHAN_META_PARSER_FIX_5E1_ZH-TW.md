# 5-E.1｜華山 Meta 標籤解析修正

## Artifact 113 發現

完整候選驗證取得 28 筆活動，詳情頁結果為：

- 成功：27
- 失敗：1
- 失敗來源 ID：`performance_26040110454037661`
- 活動：`2026華山親子表藝節`
- 錯誤：`AttributeError: 'NoneType' object has no attribute 'strip'`

## 原因

該頁包含沒有 `name` 或 `property` 的 `<meta>` 標籤。
Parser 原本直接對缺少的屬性呼叫 `.strip()`，因此中止該頁解析。

## 修正

缺少 `name` 與 `property` 時，以空字串處理並忽略該標籤：

```python
key = (
    attrs_map.get("property")
    or attrs_map.get("name")
    or ""
).strip().lower()
```

## 安全性

- 不放寬 5-E 的完整詳情頁品質門檻
- 不修改正式活動資料
- 不修改前台
- 不修改 Workflow
- 重新執行既有 Full Candidate Trigger 即可
