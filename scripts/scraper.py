"""
台灣展覽誌 - 資料抓取腳本
來源:文化部「文化資料開放服務網」公開 API(免金鑰、每日更新)
https://cloud.culture.tw/frontsite/trans/SearchShowAction.do?method=doFindTypeJ&category=all

這支腳本會被 GitHub Actions 每天自動執行一次,
把最新的展覽/藝文活動資料整理後存成 data/exhibitions.json,
給網站前端讀取顯示。
"""

import json
import re
import urllib.request
from datetime import datetime, timezone, timedelta

import requests
from bs4 import BeautifulSoup

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


# ---------------------------------------------------------------------------
# 額外場館來源：華山1914文化創意產業園區
#
# 這個場館沒有像文化部一樣的公開 API，所以用網頁解析（HTML scraping）取得資料。
# 注意：這種做法比 API 脆弱——如果華山官網改版，這段程式可能就會抓不到資料，
# 屆時需要重新調整。之後若要加入花博、世貿、三創等場館，也是採用同樣的模式，
# 但每個網站的頁面結構都不同，需要各自另外撰寫解析規則。
# ---------------------------------------------------------------------------

HUASHAN_BASE_URL = "https://www.huashan1914.com/w/huashan1914/exhibition"
HUASHAN_CATEGORIES = ["展演活動", "市集活動", "論壇講座", "期間限定店", "品牌活動", "表演藝術", "歷史活動"]
HUASHAN_DATE_PATTERN = re.compile(r"(\d{4})\.(\d{2})\.(\d{2})(?:\s*-\s*(\d{2})\.(\d{2}))?")
HUASHAN_TIME_PATTERN = re.compile(r"\d{1,2}:\d{2}\s*[AP]M\s*-\s*\d{1,2}:\d{2}\s*[AP]M")


def parse_huashan_dates(date_str: str):
    match = HUASHAN_DATE_PATTERN.search(date_str)
    if not match:
        return "", ""
    year, month, day, end_month, end_day = match.groups()
    start = f"{year}/{month}/{day}"
    if end_month and end_day:
        end = f"{year}/{end_month}/{end_day}"
    else:
        end = start
    return start, end


def fetch_huashan(max_pages: int = 6):
    """抓取華山1914「找活動」頁面，回傳整理後的活動清單"""
    events = []
    seen_links = set()

    for page in range(1, max_pages + 1):
        url = HUASHAN_BASE_URL if page == 1 else f"{HUASHAN_BASE_URL}?index={page}"
        try:
            resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
            resp.raise_for_status()
        except Exception as exc:  # noqa: BLE001 - 場館爬蟲失敗不該讓整個腳本掛掉
            print(f"[華山] 第 {page} 頁抓取失敗，略過：{exc}")
            break

        soup = BeautifulSoup(resp.text, "html.parser")
        links = [a for a in soup.find_all("a", href=True) if "/exhibition_" in a["href"]]
        if not links:
            break

        found_new = False
        for a in links:
            href = a["href"]
            if href in seen_links:
                continue
            seen_links.add(href)
            found_new = True

            text = " ".join(a.get_text(" ", strip=True).split())
            category = next((c for c in HUASHAN_CATEGORIES if text.endswith(c)), "")
            body = text[: -len(category)].strip() if category else text

            time_match = HUASHAN_TIME_PATTERN.search(body)
            if time_match:
                body = body[: time_match.start()].strip()

            date_match = HUASHAN_DATE_PATTERN.search(body)
            title = body[: date_match.start()].strip() if date_match else body
            start_date, end_date = parse_huashan_dates(body) if date_match else ("", "")

            if not title:
                continue

            events.append({
                "title": title,
                "category": category or "展演活動",
                "unit": "",
                "description": "",
                "image": "",
                "startDate": start_date,
                "endDate": end_date,
                "location": "台北市中正區八德路一段1號",
                "locationName": "華山1914文化創意產業園區",
                "sourceUrl": href if href.startswith("http") else f"https://www.huashan1914.com{href}",
                "sourceName": "華山1914文化創意產業園區",
                "latitude": "25.0444",
                "longitude": "121.5294",
            })

        if not found_new:
            break

    return events


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
        "sourceName": (item.get("sourceWebName") or "").strip() or "文化部開放資料",
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

    try:
        huashan_events = fetch_huashan()
        huashan_events = [e for e in huashan_events if is_still_relevant(e, now)]
        print(f"[華山] 抓到 {len(huashan_events)} 筆活動")
        events.extend(huashan_events)
    except Exception as exc:  # noqa: BLE001
        print(f"[華山] 整體抓取失敗，僅使用文化部資料：{exc}")

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
