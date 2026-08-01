# Collector 第 7、8 階段（R12 STABLE2）

## 第 7 階段：每日 Dry Run

`collector-dry-run.yml` 只驗證來源登錄、執行測試並產生稽核報告。它只有 `contents: read` 權限，不會修改 `data/exhibitions*.json`、不會 Commit，也不會 Push。

## 第 8 階段：人工閘門基礎

`data/collector_release_stages.json` 已定義品質閘門與人工核准需求，但 `enabled` 與 `publishEnabled` 皆維持 `false`。R12 不會自動啟用正式發布。

## 社群探索限制

`data/social_discovery_policy.json` 明定社群資料只能發現候選活動，不能取代官方展期、地址、票價或售票連結，且禁止匯入 Facebook 活動資料。
