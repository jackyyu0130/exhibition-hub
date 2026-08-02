# T1 Threads 官方關鍵字探索

## T1 會做什麼

T1 使用 Meta Threads 官方 `keyword_search` API，定時搜尋公開貼文，並只建立人工審核候選。

- 台灣時間每天 04:20、16:20 執行。
- 每次輪替最多 12 個固定展覽關鍵字。
- 另外從網站目前仍在展期／即將開始的活動中，產生最多 8 個展名搜尋詞。
- 手動執行時可以額外搜尋 `TOP` 熱門結果。
- 同一貼文被不同搜尋詞找到時，只保留一筆。
- 不保存完整貼文，不建立獨立的帳號名稱欄位，不公開作者身分。
- 不直接修改展覽日期、票價、地址或正式資料。
- 沒有 `THREADS_ACCESS_TOKEN` 時，workflow 會留下 `not_configured` 報告並安全跳過，不會失敗。

## Artifact 內容

`Social discovery review artifact` 執行後會產生：

- `threads_candidates.json`：Threads 初步候選。
- `threads_new_event_signals.json`：可能是網站尚未收錄的新活動訊號。
- `threads_discovery_report.json`：搜尋詞、成功數、錯誤與權限狀態。
- `social_review_queue.json`：Threads、PTT、人工候選合併後的審核檔。

## 發布規則

只有成功配對站內展覽且 `matchConfidence >= 0.68` 的候選，才允許在本機審核工具按「核准」。核准後仍需把審核後 JSON 放回 repository，並由 S2 建立公開 feed。

尚未配對的 Threads 貼文只會標示為「新活動訊號」，後續必須找到官方場館、主辦單位或售票頁，才能進入正式展覽資料。
