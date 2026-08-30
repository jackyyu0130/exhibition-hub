# R14.3 文化部 HTTPS 相容修正

## 錯誤原因

Mac 的新版 Python／OpenSSL 可能預設啟用 `VERIFY_X509_STRICT`。文化部
`cloud.culture.tw` 目前的憑證鏈可正常驗證，但其中一張憑證缺少 Strict
模式額外要求的 Subject Key Identifier，因此本機爬蟲出現
`CERTIFICATE_VERIFY_FAILED: Missing Subject Key Identifier`。

本修正只對文化部網域移除額外的 Strict 旗標，仍保留：

- 憑證授權鏈驗證
- 網域名稱驗證
- HTTPS 加密

沒有使用 `verify=False`，也不會影響其他官方來源的 HTTPS 設定。

## 安裝

1. 若原本的週更終端機仍在執行，按一次 `Control + C`，等待資料還原完成。
2. 開啟 GitHub Desktop，確認 Current branch 是 `develop`。
3. 點 `Fetch origin`；若出現 `Pull origin`，再點一次。
4. 點 `Repository` → `Show in Finder`。
5. 將修正包解壓縮後「裡面的全部內容」拖入專案根目錄。
6. Finder 詢問時選「合併」與「取代」，不要刪除其他檔案。
7. 回到 GitHub Desktop，Summary 輸入：

   `fix: support Culture Ministry TLS on local Mac updates`

8. 點 `Commit to develop`，再點 `Push origin`。
9. 等 `Validate development changes` 出現綠色勾勾。

## 重新執行週更

1. 回到 Finder 專案根目錄。
2. 對 `run_weekly_update.command` 按右鍵 →「打開」。
3. 文化部步驟應開始顯示 `Fetched ... records`，不再出現
   `Missing Subject Key Identifier`。
4. 保持網路連線，不要關閉終端機或讓 Mac 睡眠。
5. 成功後先查看 `local-update-output/latest-summary.md`。
6. 第一次修正後的更新先不要 Commit 資料；將摘要畫面提供給我確認。

若仍看到相同憑證錯誤，請中止更新並提供終端機最上方的 Python 版本、
第一段錯誤以及 `local-update-output/執行日期時間/update.log`。
