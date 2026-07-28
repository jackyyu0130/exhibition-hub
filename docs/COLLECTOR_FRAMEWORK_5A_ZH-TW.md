# 5-A｜官方來源 Collector 共用框架

本階段只建立所有官方場館 Collector 共用的底層規格，尚不啟用任何新場館來源。

## 已建立

1. CollectorSource：來源設定契約
2. CollectorRecord：原始活動最小輸出契約
3. BaseCollector：列表、詳情與正規化介面
4. CollectorHttpClient：逾時、重試、HTTP 錯誤處理
5. CollectorRegistry：來源與 Collector 註冊表
6. CollectorRunner：啟用、planned 與失敗邊界
7. Collector Audit：比對 source_registry 與實作覆蓋率
8. `[dry-run-collectors]` GitHub Actions 稽核工作

## 目前稽核結果的預期

- culture-ministry：由既有更新器管理
- huashan-1914：planned，尚未實作
- 其他官方場館：planned，尚未實作
- frameworkReady：true

## 下一階段

5-B 會建立第一個正式來源：華山1914 Collector，包含活動列表、分頁、詳情頁、圖片、日期、票價與官方網址解析。
