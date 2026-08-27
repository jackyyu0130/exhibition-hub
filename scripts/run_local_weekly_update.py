#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import traceback
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUTPUT_ROOT = ROOT / "local-update-output"
LOCK_PATH = ROOT / ".local-weekly-update.lock"
TAIPEI_NOW = datetime.now().astimezone()
RUN_ID = TAIPEI_NOW.strftime("%Y%m%d-%H%M%S")
RUN_DIR = OUTPUT_ROOT / RUN_ID
AUDIT = RUN_DIR / "audit"
BACKUP = RUN_DIR / "backup"
LOG_PATH = RUN_DIR / "update.log"

MUTABLE_DATA_FILES = (
    "data/exhibitions.json",
    "data/exhibitions.enriched.json",
    "data/exhibitions.curated.json",
    "data/social_discussions.json",
    "data/geocode-cache.json",
)


def load_json(path: Path, default: Any = None) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def event_id(event: dict[str, Any]) -> str:
    return str(event.get("id") or event.get("uid") or "").strip()


def event_fingerprint(event: dict[str, Any]) -> str:
    ignored = {
        "updatedAt",
        "collectedAt",
        "fetchedAt",
        "lastCheckedAt",
    }
    stable = {key: value for key, value in event.items() if key not in ignored}
    encoded = json.dumps(stable, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def event_map(payload: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(payload, dict):
        return {}
    rows = payload.get("events") or []
    result: dict[str, dict[str, Any]] = {}
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            continue
        key = event_id(row) or f"row-{index}-{row.get('title', '')}"
        result[key] = row
    return result


def acquire_lock() -> None:
    try:
        descriptor = os.open(LOCK_PATH, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise RuntimeError(
            "另一個每週更新仍在執行。若確定沒有其他更新視窗，請刪除專案根目錄的 "
            ".local-weekly-update.lock 後再試一次。"
        ) from exc
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        handle.write(f"pid={os.getpid()}\nstartedAt={TAIPEI_NOW.isoformat()}\n")


def backup_current_data() -> None:
    for relative in MUTABLE_DATA_FILES:
        source = ROOT / relative
        if not source.is_file():
            continue
        target = BACKUP / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def restore_backup() -> None:
    for relative in MUTABLE_DATA_FILES:
        source = BACKUP / relative
        if not source.is_file():
            continue
        target = ROOT / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def run_step(label: str, command: list[str], *, env: dict[str, str] | None = None) -> None:
    border = "=" * 72
    print(f"\n{border}\n{label}\n{border}", flush=True)
    with LOG_PATH.open("a", encoding="utf-8") as log:
        log.write(f"\n{border}\n{label}\n$ {' '.join(command)}\n{border}\n")
        merged_env = os.environ.copy()
        if env:
            merged_env.update(env)
        process = subprocess.Popen(
            command,
            cwd=ROOT,
            env=merged_env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )
        assert process.stdout is not None
        for line in process.stdout:
            print(line, end="", flush=True)
            log.write(line)
        status = process.wait()
        if status != 0:
            raise RuntimeError(f"{label}失敗（結束代碼 {status}）")


def build_summary(before_payload: Any, after_payload: Any) -> dict[str, Any]:
    before = event_map(before_payload)
    after = event_map(after_payload)
    before_ids = set(before)
    after_ids = set(after)
    added_ids = sorted(after_ids - before_ids)
    removed_ids = sorted(before_ids - after_ids)
    changed_ids = sorted(
        item_id
        for item_id in before_ids & after_ids
        if event_fingerprint(before[item_id]) != event_fingerprint(after[item_id])
    )
    official_diff = load_json(AUDIT / "official-sources-diff.json", {}) or {}
    batch = official_diff.get("batchSummary") or {}
    review = load_json(AUDIT / "merge-review.json", {}) or {}
    review_rows = review.get("items") if isinstance(review, dict) else review
    if not isinstance(review_rows, list):
        review_rows = []
    return {
        "schemaVersion": 1,
        "runId": RUN_ID,
        "status": "success",
        "startedAt": TAIPEI_NOW.isoformat(),
        "finishedAt": datetime.now().astimezone().isoformat(),
        "beforeCount": len(before),
        "afterCount": len(after),
        "addedCount": len(added_ids),
        "changedCount": len(changed_ids),
        "removedCount": len(removed_ids),
        "added": [
            {"id": item_id, "title": str(after[item_id].get("title") or "")}
            for item_id in added_ids
        ],
        "changed": [
            {"id": item_id, "title": str(after[item_id].get("title") or "")}
            for item_id in changed_ids
        ],
        "removed": [
            {"id": item_id, "title": str(before[item_id].get("title") or "")}
            for item_id in removed_ids
        ],
        "officialSources": {
            "total": int(batch.get("sourceCount") or 0),
            "successful": int(batch.get("successfulSourceCount") or 0),
            "failed": int(batch.get("failedSourceCount") or 0),
            "skipped": int(batch.get("skippedSourceCount") or 0),
        },
        "reviewCount": len(review_rows),
        "publishedUpdatedAt": (
            after_payload.get("updatedAt") if isinstance(after_payload, dict) else None
        ),
        "log": str(LOG_PATH.relative_to(ROOT)),
    }


def summary_markdown(summary: dict[str, Any]) -> str:
    source = summary["officialSources"]

    def titles(key: str, limit: int = 20) -> str:
        rows = summary.get(key) or []
        if not rows:
            return "- 無\n"
        result = "".join(f"- {row['title']}\n" for row in rows[:limit])
        if len(rows) > limit:
            result += f"- 另有 {len(rows) - limit} 筆，請查看 latest-summary.json\n"
        return result

    return f"""# 台灣展覽誌每週更新摘要

- 執行結果：成功
- 官網資料更新時間：{summary.get('publishedUpdatedAt') or '未提供'}
- 更新前：{summary['beforeCount']} 筆
- 更新後：{summary['afterCount']} 筆
- 新增：{summary['addedCount']} 筆
- 內容異動：{summary['changedCount']} 筆
- 移除／不再發布：{summary['removedCount']} 筆
- 官方來源：成功 {source['successful']}／失敗 {source['failed']}／略過 {source['skipped']}／共 {source['total']}
- 需要人工確認：{summary['reviewCount']} 筆

## 新增展覽

{titles('added')}
## 內容異動

{titles('changed')}
## 移除或不再發布

{titles('removed')}
## 下一步

1. 若資料量沒有異常大幅下降，開啟 GitHub Desktop。
2. 確認本次變更主要位於 `data/`。
3. 一次 Commit 並 Push 到 `main`。
4. 到 GitHub → Actions → `Publish prepared website` → `Run workflow`。
5. 發布完成後檢查首頁展覽數、更新時間及 favicon。
"""


def main() -> int:
    required = [
        ROOT / "requirements.txt",
        DATA / "exhibitions.json",
        DATA / "exhibitions.enriched.json",
        DATA / "exhibitions.curated.json",
        DATA / "source_registry.json",
    ]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(
            "請把更新包內容放在 exhibition-hub 專案根目錄。缺少：" + ", ".join(missing)
        )

    acquire_lock()
    RUN_DIR.mkdir(parents=True, exist_ok=False)
    AUDIT.mkdir(parents=True)
    backup_current_data()
    before_payload = load_json(DATA / "exhibitions.curated.json", {})
    python = sys.executable

    try:
        run_step(
            "1/11 抓取並標準化文化部資料",
            [python, "scripts/scraper.py"],
            env={
                "MAX_DETAIL_FETCHES": os.environ.get("MAX_DETAIL_FETCHES", "2200"),
                "MAX_IMAGE_FETCHES": os.environ.get("MAX_IMAGE_FETCHES", "2200"),
                "MAX_GEOCODES": os.environ.get("MAX_GEOCODES", "150"),
            },
        )
        run_step(
            "2/11 建立完整整合基底",
            [
                python,
                "scripts/build_enriched_candidate.py",
                "--input", "data/exhibitions.json",
                "--venues", "data/venues.json",
                "--legacy-aliases", "data/venue-aliases.json",
                "--output", str(AUDIT / "fresh-base.json"),
                "--report-output", str(AUDIT / "fresh-base-report.json"),
                "--excluded-output", str(AUDIT / "fresh-base-excluded.json"),
            ],
        )
        run_step(
            "3/11 抓取華山官方詳情",
            [
                python,
                "scripts/run_collectors.py",
                "--source", "huashan-1914",
                "--fetch-details",
                "--source-registry", "data/source_registry.json",
                "--report-output", str(AUDIT / "huashan-source-run.json"),
            ],
        )
        run_step(
            "4/11 合併華山資料並檢查",
            [
                python,
                "scripts/build_source_merge_candidate.py",
                "--base", str(AUDIT / "fresh-base.json"),
                "--source-run", str(AUDIT / "huashan-source-run.json"),
                "--source-registry", "data/source_registry.json",
                "--source-id", "huashan-1914",
                "--candidate-output", str(AUDIT / "merge-candidate.json"),
                "--report-output", str(AUDIT / "merge-report.json"),
                "--review-output", str(AUDIT / "merge-review.json"),
            ],
        )
        run_step(
            "5/11 驗證華山整合結果",
            [
                python,
                "scripts/validate_source_merge_candidate.py",
                "--base", str(AUDIT / "fresh-base.json"),
                "--source-run", str(AUDIT / "huashan-source-run.json"),
                "--candidate", str(AUDIT / "merge-candidate.json"),
                "--merge-report", str(AUDIT / "merge-report.json"),
                "--review", str(AUDIT / "merge-review.json"),
                "--source-id", "huashan-1914",
                "--require-full-details",
                "--max-review", "0",
                "--output", str(AUDIT / "quality-report.json"),
            ],
        )
        run_step(
            "6/11 建立發布預覽",
            [
                python,
                "scripts/prepare_source_publish_preview.py",
                "--base", str(AUDIT / "fresh-base.json"),
                "--source-run", str(AUDIT / "huashan-source-run.json"),
                "--candidate", str(AUDIT / "merge-candidate.json"),
                "--merge-report", str(AUDIT / "merge-report.json"),
                "--review", str(AUDIT / "merge-review.json"),
                "--quality-report", str(AUDIT / "quality-report.json"),
                "--source-id", "huashan-1914",
                "--preview-output", str(AUDIT / "publish-preview.json"),
                "--diff-output", str(AUDIT / "publish-diff.json"),
                "--excluded-output", str(AUDIT / "publish-excluded.json"),
            ],
        )
        run_step(
            "7/11 抓取並整合已啟用官方來源",
            [
                python,
                "scripts/run_official_source_batch.py",
                "--base", str(AUDIT / "publish-preview.json"),
                "--source-registry", "data/source_registry.json",
                "--output", str(AUDIT / "official-sources-preview.json"),
                "--report", str(AUDIT / "official-source-batch.json"),
                "--diff-output", str(AUDIT / "official-sources-diff.json"),
                "--audit-dir", str(AUDIT / "official-sources"),
            ],
        )
        run_step(
            "8/11 套用安全發布門檻",
            [
                python,
                "scripts/finalize_source_publish.py",
                "--current", "data/exhibitions.enriched.json",
                "--preview", str(AUDIT / "official-sources-preview.json"),
                "--diff", str(AUDIT / "official-sources-diff.json"),
                "--source-run", str(AUDIT / "huashan-source-run.json"),
                "--quality-report", str(AUDIT / "quality-report.json"),
                "--source-id", "huashan-1914",
                "--minimum-events", "500",
                "--max-drop-count", "25",
                "--max-drop-ratio", "0.15",
                "--output", str(AUDIT / "exhibitions.enriched.final.json"),
                "--report-output", str(AUDIT / "production-publish-report.json"),
            ],
        )
        shutil.copy2(AUDIT / "exhibitions.enriched.final.json", DATA / "exhibitions.enriched.json")
        (DATA / "update-reports").mkdir(parents=True, exist_ok=True)
        shutil.copy2(
            AUDIT / "production-publish-report.json",
            DATA / "update-reports/latest-local-weekly-update.json",
        )
        shutil.copy2(
            AUDIT / "official-source-batch.json",
            DATA / "update-reports/official-source-batch.json",
        )
        run_step(
            "9/11 清理不合格圖片與社群連結",
            [
                python,
                "scripts/audit_event_images.py",
                "--fix",
                "data/exhibitions.json",
                "data/exhibitions.enriched.json",
                "--report", "data/update-reports/image-quality-audit.json",
            ],
        )
        run_step(
            "10/11 建立官網公開展覽資料",
            [
                python,
                "scripts/build_curated_feed.py",
                "--input", "data/exhibitions.enriched.json",
                "--matrix", "data/taiwan_venue_matrix.json",
                "--output", "data/exhibitions.curated.json",
                "--report", "data/update-reports/curated-feed-report.json",
            ],
        )
        run_step(
            "11/11 建立社群資料並驗證正式資料",
            [
                python,
                "scripts/build_social_feed.py",
                "--queue", "data/social_review_queue.json",
                "--events", "data/exhibitions.curated.json",
                "--output", "data/social_discussions.json",
            ],
        )
        run_step(
            "最終驗證",
            [
                python,
                "scripts/validate_published_data.py",
                "--input", "data/exhibitions.enriched.json",
                "--minimum-events", "500",
                "--require-published",
                "--source-id", "huashan-1914",
                "--report-output", str(AUDIT / "published-data-validation.json"),
            ],
        )
        after_payload = load_json(DATA / "exhibitions.curated.json", {})
        summary = build_summary(before_payload, after_payload)
        write_json(RUN_DIR / "summary.json", summary)
        write_json(OUTPUT_ROOT / "latest-summary.json", summary)
        markdown = summary_markdown(summary)
        (RUN_DIR / "summary.md").write_text(markdown, encoding="utf-8")
        (OUTPUT_ROOT / "latest-summary.md").write_text(markdown, encoding="utf-8")
        print("\n" + markdown)
        print(f"完整紀錄：{RUN_DIR.relative_to(ROOT)}")
        if sys.platform == "darwin":
            subprocess.run(["open", str(OUTPUT_ROOT / "latest-summary.md")], check=False)
        return 0
    except BaseException:
        restore_backup()
        failure = {
            "schemaVersion": 1,
            "runId": RUN_ID,
            "status": "failed",
            "failedAt": datetime.now().astimezone().isoformat(),
            "error": traceback.format_exc(),
            "restoredBackup": True,
            "log": str(LOG_PATH.relative_to(ROOT)),
        }
        write_json(RUN_DIR / "failure.json", failure)
        print("\n更新失敗，已將主要正式資料還原到執行前版本。", file=sys.stderr)
        raise
    finally:
        LOCK_PATH.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
