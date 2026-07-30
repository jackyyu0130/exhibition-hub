# Exhibition Hub V6.5.0-R3 票券輪播微調版 — 超詳細替換指南

這份更新包適合你目前已經在使用 **V6.5.0-R2**，想繼續往上更新到 **V6.5.0-R3**。

---

## 這次會更新哪些檔案

- `index.html`
- `assets/app.js`
- `assets/styles.css`
- `VERSION.txt`
- `MANIFEST_V6.5.0-R3.json`
- `tests/test_v650_postcard_carousel.py`
- `tests/test_v650_r2_cumulative_release.py`

---

## 你應該用哪個檔案

### 如果你現在網站已經正常，而且只是要套用這次 Hero 微調
請用：

`Exhibition-Hub-V6.5.0-R3-ticket-carousel-refinement-safe-update.zip`

### 如果你想整包完整覆蓋
請用：

`Exhibition-Hub-V6.5.0-R3-full-replacement.zip`

---

## 安全更新包替換步驟（建議你用這個）

1. 先解壓縮 `Exhibition-Hub-V6.5.0-R3-ticket-carousel-refinement-safe-update.zip`
2. 打開你目前本機的 GitHub 專案資料夾。
3. 將解壓縮後裡面的檔案，依照相同路徑覆蓋到你的專案中。
4. **不要把最外層資料夾整包拖進 repo 裡。**
5. 只覆蓋裡面的 `index.html`、`assets/`、`tests/` 等實際檔案。
6. 回到 GitHub Desktop，確認變更檔案正確出現。
7. Commit 訊息建議填：

`Apply Exhibition Hub V6.5.0-R3 ticket carousel refinement`

8. Push 到 `develop`。
9. 到 GitHub 開 PR：`develop` → `main`
10. 等檢查通過後合併。
11. 合併完成後，等待 GitHub Pages 重新部署。
12. 到正式站做強制重新整理（Mac Chrome：`Command + Shift + R`）。

---

## GitHub Desktop 覆蓋後你要看什麼

至少要看到這幾個檔案有變更：

- `index.html`
- `assets/app.js`
- `assets/styles.css`
- `VERSION.txt`
- `MANIFEST_V6.5.0-R3.json`
- `tests/test_v650_postcard_carousel.py`
- `tests/test_v650_r2_cumulative_release.py`

如果你看到整個 `data/` 一大堆資料都被改到，這次通常不是重點，先不要亂動。

---

## 更新後你要檢查什麼

### 電腦版 Hero

- 左右按鈕改成 `<`、`>` 樣式。
- 箭頭在票券大框外側，不是壓在內容上。
- 前面的票券更扁、更像真正票券。
- 明信片與票券不會重疊太多。
- 後方第二組會有一點模糊。
- 切換時會有角度變化感。

### 手機版 Hero

- 票券高度有比較收斂。
- 明信片不會遮住過多票券。
- 左右滑切換仍正常。

---

## 如果正式站沒立刻更新

這通常是快取。

請依序做：

1. 等 2～10 分鐘。
2. 用無痕視窗打開正式站。
3. 再按一次 `Command + Shift + R`。

---

## 回滾方式

如果你覺得這次微調不喜歡：

1. 打開 GitHub Desktop
2. 切回上一個正常 Commit
3. 或重新覆蓋你上一版的安全更新包
4. 再 Commit / Push 一次

---

## 備註

這次更新 **沒有變動資料抓取邏輯**，主軸是 Hero 視覺與前端互動微調。
