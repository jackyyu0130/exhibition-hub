# 5-F.2｜華山正式啟用與安全發布

## 本階段完成內容

- `huashan-1914` 改為 `active`／`enabled: true`
- 每日台灣時間 05:25、17:25 更新
- 文化部原始資料更新後重新建立 enriched 基底
- 抓取華山完整列表與全部詳情頁
- 執行來源去重、品質閘門與正式發布安全檢查
- `exclude_review` 不進入正式網站
- 更新失敗時不覆蓋上一版正式資料
- 更新前資料與完整差異報告保留為 Actions Artifact 30 天
- 正式資料變動由 GitHub Actions 安全提交至 `main`
- GitHub Pages 改為只部署網站必要檔案

## 正式發布安全限制

- 詳情頁必須全部成功
- 人工審核佇列必須為 0
- 候選與正式 ID 必須唯一
- 來源合併不可刪除 fresh base 事件
- 正式事件不可少於 500 筆
- 相較上一版最多下降 250 筆
- 相較上一版最多下降 15%
- 任一閘門失敗即停止，不覆蓋、不提交、不部署錯誤資料

## GitHub Pages 公開內容

只部署：

- `index.html`
- `assets/`
- `data/exhibitions.enriched.json`
- `data/exhibitions.json`
- `.nojekyll`
- `CNAME`（存在時）

不再公開：

- `scripts/`
- `tests/`
- `docs/`
- `MANIFEST*`
- 開發說明文件
- `.DS_Store`

## 首次啟用方式

5-F.2 合併到 `main` 時，因 `data/source_registry.json` 發生變動，正式 Workflow 會自動執行第一次完整資料更新。後續由每日排程自動更新，也可在 Actions 手動執行。
