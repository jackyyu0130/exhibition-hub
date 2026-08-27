# R14.3 手機 Hero 單點與本機週更補丁

## 本補丁修改內容

- 手機版 Hero 的三張票券改為點一下直接開啟展覽詳情。
- 左右滑動仍只切換票券，不會誤開展覽。
- 更新 `app.js` 的快取版本，避免手機繼續載入舊的雙點行為。
- 每週更新摘要新增更新前後的展覽筆數與展演場館數。
- 本機週更說明統一改為 `develop → Pull Request → main → 手動發布`。
- 保留先前已更新的首頁 SEO 描述。

## 安裝補丁

1. 在 GitHub Desktop 確認 Current branch 是 `develop`。
2. 點 `Fetch origin`；若顯示 `Pull origin`，再點一次。
3. 點 `Repository` → `Show in Finder`。
4. 將本補丁解壓縮後「裡面的全部內容」拖入專案根目錄。
5. Finder 詢問時選擇「合併」與「取代」，不要刪除原本其他檔案。
6. 回到 GitHub Desktop，Summary 輸入：

   `fix: open mobile hero tickets with one tap`

7. 點 `Commit to develop`，再點 `Push origin`。
8. 等 `Validate development changes` 出現綠色勾勾。
9. 建立或更新 `develop → main` Pull Request，確認 Checks 通過後合併。
10. 不要刪除 `develop` branch。
11. 到 Actions → `Publish prepared website` → `Run workflow`，Branch 選 `main`。
12. 等綠色勾勾後，用手機重新開啟首頁測試三張票券。

## 執行每週展覽更新

1. GitHub Desktop 切到 `develop`，執行 `Fetch origin`／`Pull origin`。
2. 確認沒有尚未提交的舊變更。
3. 點 `Repository` → `Show in Finder`。
4. 第一次對 `run_weekly_update.command` 按右鍵 →「打開」；之後可直接雙擊。
5. 保持網路連線、不要關閉終端機，也不要讓 Mac 睡眠。
6. 成功後查看自動開啟的 `local-update-output/latest-summary.md`。
7. 確認更新後的展覽數、展演場館數、移除數及失敗來源合理。
8. 在 GitHub Desktop 將資料一次 Commit 到 `develop` 並 Push。
9. 等檢查通過，合併 `develop → main` Pull Request。
10. 手動執行一次 `Publish prepared website`，Branch 選 `main`。

首頁會自動從 `data/exhibitions.curated.json` 讀取：

- `events` 的公開展覽筆數，顯示為「收錄活動」。
- 公開展覽中不重複的場館名稱數，顯示為「展演場館」。
- `updatedAt`，顯示為首頁與頁尾的更新日期時間。

不需要手動修改首頁數字或時間。三者要在 Pull Request 合併並完成手動發布後，才會出現在正式網站。

## 不要執行

- 不要重新啟用已停用的高負載 workflow。
- 不要執行舊的 `Update data and deploy site`。
- 不要在 GitHub Actions 上執行爬蟲。
- 不要將大量資料直接 Commit 到 `main`。
