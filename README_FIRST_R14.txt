台灣展覽誌 V6.5.0-R14
Mac 一鍵週更＋favicon 修復包

這個更新包不會要求你人工核對 700 多筆展覽。

每週更新方式：
1. 在 Mac 雙擊 run_weekly_update.command。
2. 爬蟲會自動更新、整合及驗證所有展覽資料。
3. 完成後只查看 local-update-output/latest-summary.md。
4. 使用 GitHub Desktop 一次 Commit、一次 Push。
5. 到 GitHub Actions 手動執行 Publish prepared website。

第一次安裝與每週操作的完整按鈕路徑，請查看：
R14_MAC_WEEKLY_UPDATE_GUIDE_ZH-TW.md

重要：
- 原本停用的六個高負載 workflow 請繼續保持停用。
- 不要重新執行舊版 Update data and deploy site。
- 新流程只讓 GitHub 發布已準備好的靜態網站，不在 GitHub 上爬資料。
