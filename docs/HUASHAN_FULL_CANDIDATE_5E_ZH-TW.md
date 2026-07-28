# 5-E｜華山完整候選資料驗證

## 本階段目的

5-D 僅抽樣抓取部分詳情頁。5-E 會抓取當次列表中的
全部華山活動詳情頁，再建立完整候選資料與品質報告。

仍然不會修改正式活動資料。

## 必須通過的品質閘門

- Collector 成功
- 全部來源活動都有合併決策
- 全部詳情頁都成功抓取
- 候選活動 ID 唯一
- 每筆來源活動只出現在一個候選事件中
- 候選數量符合「既有活動＋新活動」公式
- 人工審核佇列為 0
- `published` 維持 `false`

## 欄位覆蓋率

以下欄位會產生覆蓋率與警告，但不會因單一官方頁缺少
某欄位而破壞整批候選：

- 圖片
- 主辦單位
- 場館
- 官方分類
- 免費／付費
- 活動介紹

## Artifact

Workflow 會輸出：

- `huashan-full-source-run.json`
- `huashan-full-candidate.json`
- `huashan-full-merge-report.json`
- `huashan-full-review.json`
- `huashan-full-quality-report.json`
- 對應的 summary 檔案

## 發布狀態

- `huashan-1914` 維持 planned／disabled
- 不修改 `data/exhibitions.json`
- 不修改 `data/exhibitions.enriched.json`
- 不影響目前正式網站
