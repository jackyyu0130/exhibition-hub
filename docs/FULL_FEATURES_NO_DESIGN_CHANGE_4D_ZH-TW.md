# 4-D Full｜完整功能、不變更前台設計

這個版本同時滿足：

- `regionCanonical` 標準縣市
- `venueName`、`venueNames` 標準場館
- 一場活動多個巡迴場館
- 所有已配對與未配對場館名稱搜尋／篩選
- `contentType` 活動類型標籤
- `editorialStatus` 編輯狀態
- 未配對場館保留原始名稱
- enriched 失敗時自動回退舊資料與 API

## 前台設計保護

本包不包含：

- `index.html`
- `assets/styles.css`
- Logo、Hero、日曆或 RWD 檔案

不會新增新的 Badge 樣式或區塊。

`contentType` 使用卡片原本已有的分類文字位置。
多場館在卡片上顯示「第一個場館 等 N 處」，
詳細頁則沿用原本的「地點」欄位列出全部場館。

`editorialStatus` 用於資料判斷與 HTML data attribute，
不額外新增前台提示框。

## 上傳內容

- `assets/app.js`
- `data/exhibitions.enriched.json`
- `tests/test_full_features_no_design_change.py`
- `docs/FULL_FEATURES_NO_DESIGN_CHANGE_4D_ZH-TW.md`
- `MANIFEST_4D_FULL.json`

## Commit message

`feat: enable enriched features without redesign`
