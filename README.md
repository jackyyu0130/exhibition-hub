# 台灣展覽誌

自動蒐集全台展覽與藝文活動的網站。資料來自文化部開放資料，每天自動更新，完全免費上線，不需要自己顧伺服器。

## 這個專案裡有什麼

```
exhibition-hub/
├── index.html                    ← 網站本體（打開就能看）
├── data/exhibitions.json         ← 展覽資料（會被自動更新覆蓋）
├── scripts/scraper.py            ← 抓資料的程式
├── .github/workflows/update.yml  ← 排程：每天自動執行 scraper.py
└── README.md                     ← 這份教學
```

---

## 第一步：申請 GitHub 帳號

1. 前往 https://github.com/signup
2. 輸入你的 Email、設定密碼、取一個帳號名稱（例如 jacky-chen）
3. 完成驗證步驟（會問幾個簡單問題、可能要驗證信箱），一路照畫面指示即可
4. 完成後你會有一個像 `https://github.com/你的帳號` 的個人頁面

免費帳號就足夠這個專案使用，不需要付費方案。

---

## 第二步：建立一個新的 Repository（專案倉庫）

1. 登入後，點右上角的「+」→「New repository」
2. Repository name 填：`exhibition-hub`（或任何你喜歡的名字）
3. 選擇「Public」（公開，這樣朋友才看得到網站）
4. 不要勾選「Add a README file」（我們待會直接上傳整包）
5. 按「Create repository」

---

## 第三步：把這個專案上傳上去

建立完 repository 後，GitHub 會顯示一個空專案的頁面，上面有「uploading an existing file」的連結：

1. 點選那個連結（或是頁面上的「Add file」→「Upload files」）
2. 把我準備好的整個資料夾（`exhibition-hub`）裡的**所有檔案和資料夾**拖進網頁裡
   - 注意：`.github` 資料夾名稱前面有一個點，是隱藏資料夾，記得也要一起拖上去，缺了它排程就不會啟動
3. 下方填寫一句提交訊息，例如「初始上傳」
4. 按「Commit changes」

---

## 第四步：開啟 GitHub Pages（讓網站正式上線）

1. 進入你的 repository，點上方選單「Settings」
2. 左側選單找到「Pages」
3. 「Source」選擇「Deploy from a branch」
4. Branch 選擇「main」，資料夾選「/ (root)」，按「Save」
5. 等 1-2 分鐘，畫面會出現一個網址，長得像：
   `https://你的帳號.github.io/exhibition-hub/`
6. 打開這個網址，就能看到網站了（第一次看到的是我先放的範例資料）

---

## 第五步：確認自動更新排程有啟動

1. 進入 repository，點上方選單「Actions」
2. 如果看到提示要你啟用 workflow，按下啟用
3. 你會看到一個叫「更新展覽資料」的工作流程
4. 想立刻測試，不用等到明天早上：點進去 →右邊「Run workflow」→ 再按一次綠色的「Run workflow」按鈕
5. 等個 1 分鐘，重新整理，應該會看到一次成功執行（綠色勾勾）
6. 回到你的網站網址重新整理，資料應該已經換成真實的展覽資訊了

之後它會**每天台灣時間早上 9 點自動執行一次**，不用手動管理。

---

## 之後可以怎麼調整

- **想加其他資料來源**（例如特定美術館的官網）：可以之後請我幫你在 `scraper.py` 裡加新的抓取邏輯，合併進同一份 JSON
- **想改版面顏色或字體**：`index.html` 裡的 `<style>` 區塊都有註解可以調整，也可以直接告訴我想要的感覺，我幫你改
- **想換執行時間**：修改 `.github/workflows/update.yml` 裡的 `cron` 設定

有任何一步卡住，把看到的畫面或錯誤訊息告訴我，我可以直接告訴你下一步怎麼做。
