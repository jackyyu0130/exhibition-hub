# 5-F.1｜華山正式發布預覽

## 5-E 完成結果

Artifact 119 已通過：

- 華山活動 28 筆
- 詳情頁 28／28
- 自動合併 7 筆
- 新活動候選 21 筆
- 人工審核 0 筆
- 票價、圖片、共用網址與排除內容檢查通過

## 為什麼正式啟用前還要做預覽

正式網站優先讀取：

`data/exhibitions.enriched.json`

目前原始文化部資料已比 enriched 資料更新，因此不能直接把
Artifact 119 的舊基底覆蓋到正式檔案。

5-F.1 會先：

1. 使用最新 `data/exhibitions.json`
2. 重新建立最新 enriched 基底
3. 重新抓取全部華山詳情頁
4. 執行去重與完整品質閘門
5. 排除 `exclude_review`
6. 產生正式發布預覽與差異報告

## 絕對不會做的事

- 不修改 `data/exhibitions.enriched.json`
- 不修改 `data/exhibitions.json`
- 不啟用每日自動更新
- 不提交資料到 main
- `huashan-1914` 仍維持 planned／disabled

## 必須通過的發布閘門

- 來源與詳情頁全部成功
- 候選品質報告通過
- 人工審核佇列為 0
- 所有既有活動 ID 完整保留
- 沒有重複活動 ID
- 每筆華山來源只出現在一個活動中
- 排除內容不進入正式預覽
- `published` 維持 false

## 5-F.2

預覽 Artifact 通過後，才會：

- 啟用 `huashan-1914`
- 更新每日資料管線
- 加入失敗時沿用上一版資料
- 保留更新前快照與差異報告
- 精簡 GitHub Pages 公開檔案
