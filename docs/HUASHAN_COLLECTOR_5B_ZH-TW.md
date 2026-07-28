# 5-B｜華山1914活動列表 Collector

## 本階段範圍

5-B 先建立華山官方「找活動／當日活動」列表 Collector，
只做官方候選活動抓取與 Dry Run，不直接寫入正式
`data/exhibitions.json`。

官方活動列表：

```text
https://www.huashan1914.com/w/huashan1914/CustomEvent
```

## 已解析欄位

- 官方活動 ID
- 活動名稱
- 開始日期
- 結束日期
- 園區活動／園區店家活動
- 官方詳情頁網址
- 列表圖片（存在時）
- 來源列表頁與頁碼

## 分頁

Collector 會讀取：

```text
第 1 頁 / 共 3 頁
```

並依序請求：

```text
CustomEvent
CustomEvent?index=2
CustomEvent?index=3
```

同一個官方詳情網址只保留一次。

## 安全策略

華山來源仍維持：

```text
status: planned
enabled: false
```

執行時必須明確加入：

```text
--allow-planned
```

因此本階段不會自動改動正式網站資料。

## 下一階段

5-C 將加入詳情頁解析與正規化：

- 場地／館別
- 地址
- 票價與售票網址
- 主視覺與多圖
- 主辦單位
- 活動介紹
- 分類
- 與文化部及現有資料去重
