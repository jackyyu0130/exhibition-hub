"""
台灣展覽誌 - 資料抓取腳本
來源:文化部「文化資料開放服務網」公開 API(免金鑰、每日更新)
https://cloud.culture.tw/frontsite/trans/SearchShowAction.do?method=doFindTypeJ&category=all

這支腳本會被 GitHub Actions 每天自動執行一次,
把最新的展覽/藝文活動資料整理後存成 data/exhibitions.json,
給網站前端讀取顯示。
"""

import json
import urllib.request
from datetime import datetime, timezone, timedelta

API_URL = (
    "https://cloud.culture.tw/frontsite/trans/SearchShowAction.do"
    "?method=doFindTypeJ&category=all"
)
OUTPUT_PATH = "data/exhibitions.json"
TAIPEI_TZ = timezone(timedelta(hours=8))


def fetch_raw_events():
    """向文化部開放資料 API 要資料"""
    req = urllib.request.Request(API_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = resp.read().decode("utf-8")
    return json.loads(raw)


def normalize(item: dict) -> dict:
    """把官方欄位(有些欄位名稱本身就有錯字,如 titile)整理成乾淨的格式"""
    show_info = item.get("showInfo") or []
    first_show = show_info[0] if isinstance(show_info, list) and show_info else {}

    title = (item.get("title") or item.get("titile") or "").strip()
    description = (item.get("descriptionFilterHtml") or "").strip()
    if len(description) > 200:
        description = description[:200] + "…"

    return {
        "title": title,
        "category": (item.get("category") or "其他").strip(),
        "unit": (item.get("showUnit") or item.get("masterUnit") or "").strip(),
        "description": description,
        "image": (item.get("imageURL") or "").strip(),
        "startDate": (item.get("startDate") or "").strip(),
        "endDate": (item.get("endDate") or "").strip(),
        "location": (item.get("location") or "").strip(),
        "locationName": (item.get("locationName") or first_show.get("locationName", "")).strip(),
        "sourceUrl": (item.get("sourceWebPromote") or "").strip(),
        "sourceName": (item.get("sourceWebName") or "").strip(),
        "latitude": item.get("latitude") or "",
        "longitude": item.get("longitude") or "",
    }


def is_still_relevant(event: dict, now: datetime) -> bool:
    """過濾掉明顯已經結束超過一天的活動"""
    end = event.get("endDate")
    if not end:
        return True
    for fmt in ("%Y/%m/%d", "%Y-%m-%d"):
        try:
            end_date = datetime.strptime(end, fmt).replace(tzinfo=TAIPEI_TZ)
            return end_date >= now - timedelta(days=1)
        except ValueError:
            continue
    return True  # 格式看不懂就先保留,不隨便丟資料


def main():
    now = datetime.now(TAIPEI_TZ)

    raw_events = fetch_raw_events()
    events = [normalize(e) for e in raw_events if (e.get("title") or e.get("titile"))]
    events = [e for e in events if is_still_relevant(e, now)]
    events.sort(key=lambda e: e.get("startDate") or "", reverse=True)

    payload = {
        "updatedAt": now.isoformat(),
        "count": len(events),
        "events": events,
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"完成:寫入 {len(events)} 筆活動資料到 {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
