# Exhibition Hub V6.5.0-R1 更新、檢查與復原指南

## 一、R1 修正什麼

這次有兩個不同原因：

1. `Validate development changes` 出現 3 個 failures 與 4 個 errors：
   V6.5.0 安全包帶入 `tests/test_huashan_detail_collector.py`，但漏了它需要的 5 個
   `tests/fixtures/*.html`，不是正式展覽資料損壞。
2. `Validate full Huashan candidate` 出現 `full_detail_coverage`：
   30 筆華山活動中有 29 筆成功，只有「貓咪大戰爭13th週年慶快閃店」官方詳情頁
   在 25 秒內沒有回應。安全閘門正確阻止不完整資料發布。

R1 補回測試樣本，並在第一輪全部活動完成後，只補抓暫時失敗的詳情頁一次。
如果補抓仍失敗，`full_detail_coverage` 仍會擋下發布，正式站保留前一次資料。

## 二、應下載哪一個 ZIP

### 建議：R1 安全更新包

```text
Exhibition-Hub-V6.5.0-R1-huashan-ci-hotfix-safe-update.zip
```

這是目前 `develop` 已有 V6.5.0 時使用的更新包。它不含：

```text
data/
.github/
assets/
index.html
```

因此不會覆蓋每日展覽資料，也不會改動已完成的 V6.5.0 前端。

### 備用：R1 完整替換包

```text
Exhibition-Hub-V6.5.0-R1-full-replacement.zip
```

只有本機專案缺少大量檔案或需重建時才使用。平常更新請用安全更新包。

## 三、更新前確認

1. 開啟 GitHub Desktop。
2. 左上 `Current Repository` 必須是 `exhibition-hub`。
3. 上方 `Current Branch` 必須是 `develop`。
4. 左側必須顯示 `0 changed files` 或 `No local changes`。
5. 點上方 `Fetch origin`。
6. 若按鈕變成 `Pull origin`，再點一次 `Pull origin`。
7. 若拉取時出現大量 `data/*.json` 衝突，先按 `Abort Merge`，不要手動解數千筆資料。

## 四、GitHub Desktop＋Finder 覆蓋方式

1. 在 Finder「下載項目」找到 R1 安全更新 ZIP，點兩下解壓縮。
2. 回到 GitHub Desktop，點 macOS 上方選單：

   ```text
   Repository → Show in Finder
   ```

3. 正確專案路徑通常是：

   ```text
   /Users/jacky_yu/Documents/GitHub/exhibition-hub
   ```

4. 該資料夾內必須直接看得到 `index.html`、`assets`、`data`、`scripts`、`tests`。
5. 打開解壓後資料夾：

   ```text
   exhibition-hub-v6.5.0-r1-huashan-ci-hotfix-safe-update
   ```

6. 按 `Command + A` 選擇裡面的內容，拖到 `exhibition-hub` 根目錄。
7. macOS 詢問同名檔案時，點 `Replace／取代`。
8. 不要把外層資料夾整個塞進專案，錯誤範例：

   ```text
   exhibition-hub/exhibition-hub-v6.5.0-r1-huashan-ci-hotfix-safe-update/
   ```

## 五、Changes 應看到的檔案

主要應包含：

```text
scripts/exhibition_hub/collectors/huashan.py
scripts/run_collectors.py
tests/test_huashan_detail_collector.py
tests/fixtures/huashan_listing_page1.html
tests/fixtures/huashan_listing_page2.html
tests/fixtures/huashan_detail_chiikawa.html
tests/fixtures/huashan_detail_osamu.html
tests/fixtures/huashan_detail_popup.html
MANIFEST_V6.5.0-R1.json
REPLACEMENT_GUIDE_V6.5.0-R1_ZH-TW.md
VERSION.txt
UPLOAD_STEPS.txt
README.md
```

不應包含：

```text
data/exhibitions.json
data/exhibitions.enriched.json
data/geocode-cache.json
.github/workflows/update-exhibitions.yml
```

## 六、提交到 develop

1. GitHub Desktop 左下 `Summary (required)` 輸入：

   ```text
   Fix Exhibition Hub V6.5.0-R1 Huashan CI and detail recovery
   ```

2. Description 可留白。
3. 點 `Commit to develop`。
4. 完成後點上方 `Push origin`。
5. 推送完成應顯示 `No local changes`。

## 七、建立 Pull Request

1. 在 GitHub Desktop 點 `Preview Pull Request`。
2. 確認：

   ```text
   base: main
   compare: develop
   ```

3. 點 `Create Pull Request`。
4. GitHub 網頁的 PR 標題輸入：

   ```text
   Fix Exhibition Hub V6.5.0-R1 Huashan CI and detail recovery
   ```

5. Description 建議輸入：

   ```text
   - Restore the five Huashan fixtures omitted from V6.5.0
   - Retry transient Huashan detail failures once after the initial batch
   - Preserve the strict full-detail publication gate
   - Add retry and recovery metrics
   ```

6. 點綠色 `Create pull request`。

## 八、等待檢查

不要立刻合併。等待：

```text
Validate development changes
Run project tests
```

應顯示：

```text
All checks have passed
341 tests
```

如果紅色錯誤仍顯示 `FileNotFoundError: tests/fixtures/...`，表示 fixture 沒有放到
`exhibition-hub/tests/fixtures/`，請檢查是否誤放在外層資料夾。

## 九、合併與正式部署

1. 全部綠色後點 `Merge pull request`。
2. 點 `Confirm merge`。
3. 儲存庫上方點 `Actions`。
4. 左側點 `Update data and deploy site`。
5. 確認最新一筆 `main` 工作自動開始。
6. 若未開始，右側點 `Run workflow`，Branch 選 `main`，再點 `Run workflow`。
7. 等待工作顯示綠色 `Success`。
8. 開啟 `https://twexhibition.com/`，按 `Command + Shift + R`。

## 十、如何判讀華山報告

補抓成功應看到：

```text
detailRequestedCount = recordCount
detailSuccessCount = recordCount
detailRecoveredCount = 1
detailFailureCount = 0
```

若官方頁持續無回應：

```text
detailFailureCount = 1
failedGateIds = ["full_detail_coverage"]
```

這代表保護機制正在工作。不要刪除安全閘門，也不要用抽樣結果覆蓋正式資料；
可稍後到 Actions 使用 `Re-run failed jobs`。

## 十一、復原

- 尚未 Commit：GitHub Desktop `Branch → Discard All Changes`。
- 已 Commit、未 Push：`History` → 右鍵 R1 提交 → `Undo Commit`。
- 已 Push、未合併：GitHub PR 頁面 → `Close pull request`。
- 已合併：原 PR 頁面 → `Revert` → 建立復原 PR → 等檢查綠色 → 合併。

不要使用 `git reset --hard`，避免誤刪本機其他修改。
