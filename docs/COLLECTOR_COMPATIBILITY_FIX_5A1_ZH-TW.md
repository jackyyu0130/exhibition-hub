# 5-A.1｜Collector 介面相容性修正

## 問題

5-A 首版新增官方場館 Collector 架構時，覆蓋了專案既有的
Collector 公開介面，造成文化部 Collector、HTTP Client、
Normalizer 與舊測試無法匯入：

- `RawEvent`
- `CollectorContext`
- `CollectionResult`
- `CollectorError`
- `SourceKind`
- `run_collectors`

## 修正方式

本版採用雙介面相容設計。

### 既有 Collector 介面保留

舊 Collector 仍可使用：

```python
class ExampleCollector(BaseCollector):
    source_id = "example"
    source_name = "Example"
    source_kind = SourceKind.API

    def _collect(self, context, result):
        result.add_event({...})
```

並透過：

```python
collector.collect(context)
run_collectors([...])
```

執行。

### 新官方場館 Collector 介面保留

新 Collector 仍可實作：

```python
collect_raw(source, client)
normalize_record(source, raw)
```

並透過：

```python
CollectorRunner(registry).run_source(source)
```

執行。

### Registry 同時支援兩種用途

- 舊批次 Collector：`create_collectors()`、priority、enabled
- 新官方來源：`create(source_id)`、`ids()`、Collector Audit

## 設計保護

- 不修改前台 HTML、CSS 或 JavaScript
- 不修改活動資料
- 不修改 Workflow
- 僅修正 Collector Python 契約
