# Taiwan Exhibition Journal — V6.5.0-R13

本版以 GitHub `main` 的 `1a9ab48`（V6.5.0-R12 STABLE2）為基底，完成搜尋結果識別與兩個官方場館資料來源。

## 本次更新

- 首頁及動態頁標題統一為「台灣展覽誌｜全台展覽與演出資訊」。
- 新增根目錄穩定 favicon、Apple Touch Icon 與 512px 組織標誌，補齊 canonical、Open Graph 與結構化資料。
- 新增臺北世貿一館官方檔期與詳情頁 Collector，只解析一館 `menu1`；世貿三館維持歷史場館且停用。
- 新增花博公園爭艷館官方活動 Collector，只保留場地明確為爭艷館／爭豔館的活動，並將民國年轉為西元年。
- 官方活動圖片會排除空值、HTML 詳情頁、Logo、圖示、社群或預設素材；來源失敗時隔離該來源並保留既有正式資料。
- Facebook／Instagram 維持停用，不使用模擬登入或未授權社群爬取。
- 講座、課程、工作坊、營隊、研習、講習與說明會維持排除或送審。

## 安裝

請依 `REPLACEMENT_GUIDE_V6.5.0_R13_ZH-TW.md` 操作。完整替換時只複製 ZIP 內部內容到 repository 根目錄，不要刪除或覆蓋 `.git`。
