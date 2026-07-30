Exhibition Hub V6.5.0-R5 安全更新包操作指南

一、這包要覆蓋到哪裡？
請覆蓋到你的正式專案根目錄 exhibition-hub/。
也就是和 index.html、assets/、tests/、VERSION.txt 同一層的位置。

二、這次安全更新包包含什麼？
- index.html
- assets/styles.css
- VERSION.txt
- MANIFEST_V6.5.0-R5.json
- README.md
- tests/（本次 CI 對應測試檔）

三、覆蓋步驟（Finder）
1. 先解壓縮 safe update zip。
2. 開啟解壓後資料夾。
3. 再開啟你的正式專案資料夾 exhibition-hub/。
4. 將 safe update 內的檔案與資料夾，拖曳到 exhibition-hub/ 根目錄。
5. 若 macOS 跳出是否取代，請選「取代」。

四、GitHub Desktop 提交步驟
1. 回到 GitHub Desktop。
2. 確認 Current Repository 是 exhibition-hub。
3. 確認 Current Branch 是 develop。
4. 左側 Changes 會看到本次更新檔案。
5. Summary 輸入：Apply V6.5.0-R5 hero fine tune
6. 按 Commit to develop。
7. 按 Push origin。

五、建立 Pull Request
1. Push 完後，點 Create Pull Request。
2. base 選 main，compare 選 develop。
3. Title 輸入：Apply V6.5.0-R5 hero footer fine tune
4. Description 可貼：
- enlarge Hero postcard
- enlarge and lower the main ticket
- reduce ticket height feeling and remove settling jitter
- simplify footer social icons and show email below
- keep update limited to frontend files and CI tests
5. 先點 Desktop 裡的 Create Pull Request。
6. 進到 GitHub 網頁後，再點綠色 Create pull request。

六、等待 CI
看到 Run project tests 變成綠色 Success 後，才可合併。

七、合併到 main
1. 點 Merge pull request。
2. 再點 Confirm merge。
3. 不要刪除 develop branch。

八、更新正式前台
1. 到 GitHub 的 Actions。
2. 找 Update data and deploy site。
3. 看最新 main 的 workflow 是否 Success。
4. Success 後等待 2～10 分鐘。
5. 到 https://twexhibition.com/ 用 Cmd+Shift+R 強制重新整理。

九、這次主要修正
- Hero 明信片放大
- Hero 主票券放大、下移、更貼近底部
- 切換定位後的小抖動移除
- 頁尾改成 FB／IG／Threads 三個 logo 同一排
- Mail 獨立放在下方並顯示完整信箱
