# Exhibition Hub V6.5.0-R7 安全更新包替換說明

## 本次更新重點
- Hero 移除明信片，回到三張票券模式。
- 左側 `<` 按鈕 = 下一張；右側 `>` 按鈕 = 上一張。
- 切換邏輯改為票券依序遞補，新票券從右側補入。
- 桌機版箭頭恢復顯示在 Hero 框外。
- 手機版同步改為三張票券邏輯，保留滑動切換。
- 頁尾重新整理欄位排列，減少過長留白與高度。

## 安全更新包內檔案
- `index.html`
- `assets/app.js`
- `assets/styles.css`
- `VERSION.txt`
- `MANIFEST_V6.5.0-R7.json`

## 覆蓋方式
1. 打開你本機的網站專案資料夾。
2. 直接用本更新包內相同路徑檔案，覆蓋原本檔案。
3. 若你使用 GitHub Desktop：
   - 確認變更出現在 `Changes`
   - Commit summary 建議填：`Apply V6.5.0-R7 three-ticket hero and compact footer`
   - 點 `Commit to develop`
   - 點 `Push origin`
4. 到 GitHub 建立新的 Pull Request：`main ← develop`
5. 等待 checks 通過後再 merge。

## 快取提醒
部署後請用 `Cmd + Shift + R` 重新整理前台頁面確認最新畫面。
