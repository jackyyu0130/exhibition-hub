# 台灣展覽誌：自訂網址設定教學

目前網址：

```text
https://jackyyu0130.github.io/exhibition-hub/
```

要改成一般品牌網址，必須先擁有一個網域，例如：

```text
www.你的網域.tw
exhibition.你的網域.com
你的網域.tw
```

本升級包不會預先加入 `CNAME`，因為尚未知道你購買的實際網域；隨意加入錯誤網域會使 GitHub Pages 無法正常開啟。你的網站使用 GitHub Actions 發布，實際設定以 GitHub 的 Pages 設定與 DNS 為主。

## 建議做法

優先採用：

```text
www.example.com
```

再讓：

```text
example.com
```

自動轉向 `www.example.com`。`www` 子網域通常較穩定，DNS 只需要以 CNAME 指向 GitHub Pages 預設網域。

---

## 第一階段：購買網域

可在任一網域註冊商購買，例如 Cloudflare Registrar、Namecheap、GoDaddy、Gandi 或台灣網域代理商。

購買時只需要網域，不需要另外購買虛擬主機，因為網站仍由 GitHub Pages 託管。

---

## 第二階段：先在 GitHub 驗證網域

1. 登入 GitHub。
2. 點右上角頭像。
3. 點 `Settings`。
4. 左側點 `Pages`。
5. 找到 `Verified domains`。
6. 點 `Add a domain`。
7. 輸入根網域，例如：

```text
example.com
```

8. GitHub 會提供一筆 TXT 記錄。
9. 到網域商的 DNS 管理頁新增該 TXT 記錄。
10. 等待 DNS 生效後，回 GitHub 點 `Verify`。
11. TXT 記錄請保留，不要驗證完成後刪除。

---

## 第三階段：設定 www 子網域

到網域商的 DNS 管理頁，新增：

| 類型 | 名稱／Host | 目標／Value |
|---|---|---|
| CNAME | `www` | `jackyyu0130.github.io` |

注意：目標不要加上 `/exhibition-hub`，也不要加 `https://`。

正確：

```text
jackyyu0130.github.io
```

錯誤：

```text
https://jackyyu0130.github.io/exhibition-hub/
```

---

## 第四階段：需要根網域時設定 DNS

若也要讓：

```text
example.com
```

可開啟，請依網域商支援方式設定 `ALIAS`、`ANAME`，或 GitHub Pages 指定的 A 記錄。

由於 GitHub 的 IP 有可能調整，請在實際設定當天依 GitHub Pages 官方頁面顯示的最新 A 記錄為準，不要長期照抄舊教學中的 IP。

---

## 第五階段：在儲存庫指定網址

1. 開啟：

```text
jackyyu0130 / exhibition-hub
```

2. 點 `Settings`。
3. 左側點 `Pages`。
4. 找到 `Custom domain`。
5. 輸入：

```text
www.example.com
```

6. 點 `Save`。
7. DNS 檢查通過後，勾選 `Enforce HTTPS`。

DNS 可能立即生效，也可能需要數小時，最慢約 24 小時。

---

## 第六階段：確認網站與導向

確認以下網址：

```text
https://www.example.com
https://example.com
```

並確認舊網址會導向新網址或至少仍可開啟。

設定完成後，把實際網域告訴我，下一版可再替你更新：

- canonical URL
- Open Graph 網址
- 社群分享網址
- sitemap
- robots.txt
- 品牌 Email 顯示

---

## 不要做的事情

- 不要把 `CNAME` 寫成含 `https://` 的完整網址。
- 不要把 CNAME 指向 `jackyyu0130.github.io/exhibition-hub`。
- 不要在 GitHub Pages 尚未新增自訂網域前，先把 DNS 指向 GitHub。
- 不要刪除 GitHub 驗證用 TXT 記錄。
- 不要在 DNS 尚未完成時刪除原本 GitHub Pages 設定。
