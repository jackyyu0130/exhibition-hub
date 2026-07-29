# Exhibition Hub V6.3.1 修正版覆蓋指南

這一版修正 GitHub Actions 顯示的 6 個失敗。錯誤原因是新版測試已提交，但 `index.html`、兩個前端資產及 URL 正規化程式仍停在舊版。

## 目前先不要合併 PR

如果 `Validate development changes` 顯示紅色，保持 PR 未合併。回到 GitHub Desktop，確認目前分支是 `develop`。

## 覆蓋修正版

1. 點 GitHub Desktop 上方 `Fetch origin`；若變成 `Pull origin`，再點一次。
2. 點 `Repository → Show in Finder`。
3. 正確專案路徑應為 `/Users/jacky_yu/Documents/GitHub/exhibition-hub`。
4. 解壓縮 `Exhibition-Hub-V6.3.1-full-replacement.zip`。
5. 打開解壓縮後的 `exhibition-hub-main`，按 `Command + Shift + .` 顯示隱藏檔。
6. 按 `Command + A`、`Command + C`。
7. 回到本機 `exhibition-hub` 根目錄按 `Command + V`。
8. 出現詢問時選 `全部套用／Apply to All → 取代／Replace`。

## 提交前的必要檢查

GitHub Desktop 左側至少必須勾選下列檔案：

```text
index.html
assets/app.js
assets/styles.css
scripts/exhibition_hub/merging/normalization.py
tests/test_url_integrity.py
tests/test_calendar_and_compact_categories.py
tests/test_explore_alignment_and_sort_control.py
tests/test_status_and_admission_filters.py
VERSION.txt
README.md
MANIFEST_V6.3.1.json
REPLACEMENT_GUIDE_V6.3.1_ZH-TW.md
```

如果有 `.DS_Store`，右鍵點它後選 `Discard Changes`。不要提交 `.DS_Store`。

## 提交與重新驗證

1. 左下 Summary 輸入 `Fix V6.3.1 validation and frontend assets`。
2. 確認左側所有上述檔案都有勾選。
3. 點 `Commit to develop`。
4. 點上方 `Push origin`。
5. 到 GitHub `Actions → Validate development changes`。
6. 打開最新的一筆；應看到 `Run project tests` 綠色。
7. 原本失敗的舊紀錄不用重新執行；以最新 commit 觸發的工作為準。

## 合併與部署

1. 回到原本 PR，重新整理頁面。
2. 確認最新檢查全部綠色。
3. 點 `Merge pull request → Confirm merge`。
4. 不要刪除 `develop`。
5. 到 `Actions → Update data and deploy site`，等待最新 `main` 工作完成。
6. 上線後以 `Command + Shift + R` 強制重新整理 `https://twexhibition.com/`。

## 發生衝突時

若只衝突於活動資料，先進入專案終端機：

```bash
cd /Users/jacky_yu/Documents/GitHub/exhibition-hub
git checkout --ours -- data/exhibitions.json
git checkout --ours -- data/exhibitions.enriched.json
git checkout --theirs -- data/geocode-cache.json
git add -- data/exhibitions.json data/exhibitions.enriched.json data/geocode-cache.json
git commit -m "Resolve V6.3.1 data merge conflict"
git push origin develop
```

只輸入實際出現衝突的檔案；沒有衝突的檔案不要加入指令。不要使用 `git reset --hard`。

## 復原

合併前：GitHub Desktop 切到 `History`，右鍵最新 V6.3.1 commit，選 `Revert Changes in Commit`，再 Push。

合併後：在 GitHub 開啟已合併的 PR，點 `Revert` 建立復原 PR，等檢查綠色後合併復原 PR。
