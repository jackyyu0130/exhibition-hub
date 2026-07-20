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
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

API_URL = (
    "https://cloud.culture.tw/frontsite/trans/SearchShowAction.do"
    "?method=doFindTypeJ&category=all"
)
OUTPUT_PATH = "data/exhibitions.json"
TAIPEI_TZ = timezone(timedelta(hours=8))


# ---------------------------------------------------------------------------
# 分類重整：把來源網站雜亂的類別欄位（有時是數字代碼、有時語意很籠統）
# 統一改成依「展覽/活動性質」分類，關鍵字比對優先看類別欄位，
# 比對不到才退而求其次看標題與描述文字。
# ---------------------------------------------------------------------------

CATEGORY_RULES = [
    ("動漫", re.compile(
        r"動漫|動畫|漫畫|公仔|coser|cosplay|角色扮演|二次元|模型|figure|快閃店|POP.?UP|"
        r"史努比|SNOOPY|Chiikawa|吉伊卡哇|Sanrio|三麗鷗|Hello ?Kitty|凱蒂貓|"
        r"寶可夢|Pokemon|航海王|One Piece|鬼滅之刃|進擊的巨人|鏈鋸人|SPY.{0,3}FAMILY|間諜家家酒|"
        r"迪士尼|Disney|皮克斯|Pixar|哆啦A夢|多啦A夢|蠟筆小新|櫻桃小丸子|吉卜力|Ghibli|龍貓|"
        r"鋼彈|Gundam|咒術迴戰|火影忍者|Naruto|七龍珠|Dragon ?Ball|美少女戰士|Sailor ?Moon|"
        r"憤怒鳥|Angry ?Birds|迷你兵團|Minions|樂高|LEGO",
        re.IGNORECASE,
    )),
    ("音樂", re.compile(r"音樂|演唱|演奏|樂團|交響|爵士|歌唱")),
    ("美術", re.compile(r"美術|畫展|畫作|藝術(?!家)|雕塑|策展|插畫|水彩|油畫|版畫|書法")),
    ("表演", re.compile(r"戲劇|劇場|歌劇|舞台劇|表演藝術|展演活動|音樂劇|馬戲")),
    ("舞蹈", re.compile(r"舞蹈|舞團|芭蕾|現代舞")),
    ("攝影", re.compile(r"攝影|影像展")),
    ("設計", re.compile(r"設計|建築展|工藝|時尚")),
    ("講座", re.compile(r"講座|論壇|工作坊|研習|沙龍|課程")),
    ("市集", re.compile(r"市集|園遊會|展售|品牌活動")),
    ("商展", re.compile(
        r"博覽會|國際.{0,8}展|工業展|科技展|產業展|自動化|半導體|物流展|五金展|金屬.{0,4}展|"
        r"電路板|建材展|智慧能源|茶業|咖啡展|酒展|旅展|醫療科技展|照顧博覽會|塑橡膠|雷射展|"
        r"機器人展|冷鏈|模具展|技能競賽|連鎖加盟|紡織展"
    )),
]


def classify_category(raw_category: str, title: str, description: str) -> list:
    """回傳這個活動符合的所有分類（可能不只一個），完全不使用來源網站原始的類別文字。
    如果都比對不到，回傳 ["其他"]。"""
    text = f"{raw_category or ''} {title or ''} {description or ''}"
    matches = [label for label, pattern in CATEGORY_RULES if pattern.search(text)]
    return matches if matches else ["其他"]


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


FREE_PATTERN = re.compile(
    r"免費入場|免費參觀|免費参觀|免費參加|免費體驗|免費入館|免費開放|自由入場|開放參觀|不收費|免費入園"
)
PRICE_PATTERN = re.compile(
    r"(?:票價|全票|門票|定價|單人票|平日票|假日票|早鳥票|優惠票|學生票|參觀費|入場費|套票)"
    r"[:：｜\s]*(?:NT\$|TWD\$?|NT|\$)?\s?(\d[\d,]{1,6})\s?元?"
)


def extract_price_info(text: str) -> str:
    """從頁面文字裡找「免費」或明確標示的票價字樣，找不到就回傳空字串（誠實標示未提供）。"""
    if not text:
        return ""
    if FREE_PATTERN.search(text):
        return "免費"
    match = PRICE_PATTERN.search(text)
    if match:
        return f"NT$ {match.group(1)}"
    return ""


def fetch_huashan_detail(url: str) -> dict:
    """進入單一活動的詳情頁，抓取官方提供的 og:image 主視覺圖、簡介文字與票價資訊。
    每個活動頁面都有這組資料（用來給 Facebook/LINE 分享用的），比起在列表頁
    用位置去猜縮圖準確可靠得多。"""
    try:
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
        resp.raise_for_status()
    except Exception as exc:  # noqa: BLE001
        print(f"[華山] 讀取詳情頁失敗，略過圖片：{url}：{exc}")
        return {"image": "", "description": "", "price": ""}

    soup = BeautifulSoup(resp.text, "html.parser")
    og_image = soup.find("meta", attrs={"property": "og:image"})
    og_desc = soup.find("meta", attrs={"property": "og:description"})
    image = valid_image_url(safe_str(og_image.get("content")) if og_image else "")
    description = safe_str(og_desc.get("content")) if og_desc else ""
    if len(description) > 200:
        description = description[:200] + "…"
    price = extract_price_info(soup.get_text(" ", strip=True))
    return {"image": image, "description": description, "price": price}


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

            full_url = href if href.startswith("http") else f"https://www.huashan1914.com{href}"
            detail = fetch_huashan_detail(full_url)
            categories = classify_category(category, title, "")

            events.append({
                "title": title,
                "categories": categories,
                "category": categories[0],
                "unit": "",
                "description": detail["description"],
                "image": detail["image"],
                "price": detail.get("price", ""),
                "startDate": start_date,
                "endDate": end_date,
                "location": "台北市中正區八德路一段1號",
                "locationName": "華山1914文化創意產業園區",
                "sourceUrl": full_url,
                "sourceName": "華山1914文化創意產業園區",
                "latitude": "25.0444",
                "longitude": "121.5294",
            })

        if not found_new:
            break

    return events


def valid_image_url(url: str) -> str:
    """只保留看起來像正常圖片網址的字串，格式怪異的網址寧可不顯示，也不要讓前端出現破圖。"""
    url = (url or "").strip()
    if not url:
        return ""
    if not (url.startswith("http://") or url.startswith("https://")):
        return ""
    # 官方資料裡偶爾會出現像「無」「N/A」這種塞進網址欄位的髒資料
    if " " in url or len(url) < 10:
        return ""
    return url


def safe_str(value) -> str:
    """把官方 API 回傳的欄位安全轉成文字。

    文化部的資料品質不是每筆都很乾淨：同一個欄位（例如 showUnit）在有些筆資料是
    一段文字，但在某些筆資料卻是一個列表（list），甚至是數字或 None。
    直接呼叫 .strip() 遇到非字串型態就會整支程式炸掉，所以統一用這個函式處理。
    """
    if value is None:
        return ""
    if isinstance(value, list):
        return " / ".join(safe_str(v) for v in value if v).strip()
    if isinstance(value, dict):
        return ""
    return str(value).strip()


def normalize(item: dict) -> dict:
    """把官方欄位(有些欄位名稱本身就有錯字,如 titile)整理成乾淨的格式"""
    show_info = item.get("showInfo") or []
    first_show = show_info[0] if isinstance(show_info, list) and show_info and isinstance(show_info[0], dict) else {}

    title = safe_str(item.get("title") or item.get("titile"))
    description = safe_str(item.get("descriptionFilterHtml"))
    if len(description) > 200:
        description = description[:200] + "…"

    categories = classify_category(safe_str(item.get("category")), title, description)
    price = extract_price_info(description)

    return {
        "title": title,
        "categories": categories,
        "category": categories[0],
        "unit": safe_str(item.get("showUnit")) or safe_str(item.get("masterUnit")),
        "description": description,
        "image": valid_image_url(safe_str(item.get("imageURL"))),
        "price": price,
        "startDate": safe_str(item.get("startDate")),
        "endDate": safe_str(item.get("endDate")),
        "location": safe_str(item.get("location")),
        "locationName": safe_str(item.get("locationName")) or safe_str(first_show.get("locationName")),
        "sourceUrl": safe_str(item.get("sourceWebPromote")),
        "sourceName": safe_str(item.get("sourceWebName")) or "文化部開放資料",
        "latitude": safe_str(item.get("latitude")),
        "longitude": safe_str(item.get("longitude")),
    }


# ---------------------------------------------------------------------------
# 只保留「大型文藝展場」的活動：太地區性的小型活動（社區活動中心、小型圖書館展覽等）
# 先不收錄，之後有需要再擴充白名單。同時要求活動必須附有官方連結，
# 沒有連結、無法追蹤來源的資料也先排除。
# ---------------------------------------------------------------------------

# 場館白名單：key 是要統一顯示的正式名稱，value 是這個場館在來源資料裡可能出現的
# 各種寫法（含分館、簡繁體差異）。同一個場館不論資料來源寫成「西4館」「西5-1館」
# 等哪個子場地，一律統一顯示成同一個正式名稱，也才不會在「地點」篩選裡被拆成一堆子項目。
MAJOR_VENUE_ALIASES = {
    # 北部
    "台北市立美術館": ["台北市立美術館", "臺北市立美術館"],
    "國立故宮博物院": ["國立故宮博物院"],
    "國立歷史博物館": ["國立歷史博物館"],
    "國立臺灣博物館": ["國立臺灣博物館", "國立台灣博物館"],
    "台北當代藝術館": ["台北當代藝術館", "臺北當代藝術館"],
    "華山1914文化創意產業園區": ["華山1914"],
    "松山文創園區": ["松山文創園區", "松菸文創園區"],
    "空總臺灣當代文化實驗場": ["空總臺灣當代文化實驗場", "空總台灣當代文化實驗場"],
    "國父紀念館": ["國父紀念館"],
    "中正紀念堂": ["中正紀念堂"],
    "國家兩廳院": ["國家兩廳院", "國家音樂廳", "國家戲劇院"],
    "台北流行音樂中心": ["台北流行音樂中心", "臺北流行音樂中心"],
    "三創生活園區": ["三創生活園區"],
    "台北世界貿易中心": ["台北世界貿易中心", "臺北世界貿易中心", "世貿中心"],
    "順益台灣原住民博物館": ["順益台灣原住民博物館", "順益臺灣原住民博物館"],
    "新北市美術館": ["新北市美術館"],
    "雲門劇場": ["淡水雲門劇場", "雲門劇場"],
    "桃園展演中心": ["桃園展演中心"],
    "桃園市立美術館": ["桃園市立美術館"],
    "新竹市美術館": ["新竹市美術館"],
    "新竹生活美學館": ["新竹生活美學館"],
    "南港展覽館": ["南港展覽館", "TaiNEX"],
    # 中部
    "國立臺灣美術館": ["國立臺灣美術館", "國立台灣美術館"],
    "台中國家歌劇院": ["台中國家歌劇院", "臺中國家歌劇院"],
    "彰化縣立美術館": ["彰化縣立美術館"],
    "國立臺灣工藝研究發展中心": ["國立臺灣工藝研究發展中心", "國立台灣工藝研究發展中心"],
    # 南部
    "高雄市立美術館": ["高雄市立美術館"],
    "衛武營國家藝術文化中心": ["衛武營國家藝術文化中心"],
    "駁二藝術特區": ["駁二藝術特區"],
    "高雄市電影館": ["高雄市電影館"],
    "台南市美術館": ["台南市美術館", "臺南市美術館"],
    "國立臺灣歷史博物館": ["國立臺灣歷史博物館", "國立台灣歷史博物館"],
    "台南文化中心": ["台南文化中心", "臺南文化中心"],
    "屏東美術館": ["屏東美術館"],
    "屏東演藝廳": ["屏東演藝廳"],
}

# 各場館所在縣市，用來精準判斷「地區」，不再依賴地址文字裡有沒有寫到縣市關鍵字
MAJOR_VENUE_REGIONS = {
    "台北市立美術館": "台北市", "國立故宮博物院": "台北市", "國立歷史博物館": "台北市",
    "國立臺灣博物館": "台北市", "台北當代藝術館": "台北市", "華山1914文化創意產業園區": "台北市",
    "松山文創園區": "台北市", "空總臺灣當代文化實驗場": "台北市", "國父紀念館": "台北市",
    "中正紀念堂": "台北市", "國家兩廳院": "台北市", "台北流行音樂中心": "台北市",
    "三創生活園區": "台北市", "台北世界貿易中心": "台北市", "順益台灣原住民博物館": "台北市",
    "新北市美術館": "新北市", "雲門劇場": "新北市",
    "桃園展演中心": "桃園市", "桃園市立美術館": "桃園市",
    "新竹市美術館": "新竹市", "新竹生活美學館": "新竹市",
    "南港展覽館": "台北市",
    "國立臺灣美術館": "台中市", "台中國家歌劇院": "台中市",
    "彰化縣立美術館": "彰化縣",
    "國立臺灣工藝研究發展中心": "南投縣",
    "高雄市立美術館": "高雄市", "衛武營國家藝術文化中心": "高雄市",
    "駁二藝術特區": "高雄市", "高雄市電影館": "高雄市",
    "台南市美術館": "台南市", "國立臺灣歷史博物館": "台南市", "台南文化中心": "台南市",
    "屏東美術館": "屏東縣", "屏東演藝廳": "屏東縣",
}

MAJOR_VENUES = [alias for aliases in MAJOR_VENUE_ALIASES.values() for alias in aliases]


def canonical_venue_name(location_name: str) -> str:
    """把子場館名稱（西4館、西5-1館…）統一收斂回正式的場館名稱。"""
    for canonical, aliases in MAJOR_VENUE_ALIASES.items():
        if any(alias in location_name for alias in aliases):
            return canonical
    return location_name


SMALL_SCALE_KEYWORDS = re.compile(
    r"歌謠班|太極班|土風舞|外丹功|讀書會|社區大學|樂齡學堂|樂齡班|才藝班|研習班|"
    r"媽媽教室|松年大學|社區關懷據點|長青(俱樂部|學苑|班)|銀髮.{0,3}班|"
    r"里民|社區發展協會|區公所|巡迴.{0,3}講座|親職教育|生命教育宣導"
)


def is_small_scale_activity(title: str) -> bool:
    """排除社區課程、才藝班、里民活動這類非展覽性質的小型固定班隊活動。"""
    return bool(SMALL_SCALE_KEYWORDS.search(title or ""))


def is_major_venue(event: dict) -> bool:
    """只留下大型展場的活動，且必須要有官方連結才收錄。"""
    if not event.get("sourceUrl"):
        return False
    name = event.get("locationName") or ""
    return any(keyword in name for keyword in MAJOR_VENUES)


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


def fetch_detail_extras(url: str) -> dict:
    """進到活動自己的官方頁面，抓取該頁面設定的 og:image 當作展覽封面圖，
    順便也嘗試從頁面文字裡找票價資訊。這是網頁分享到 FB/LINE 時會用到的
    官方主視覺圖，比起資料庫裡的 imageURL 欄位（常常是空的）可靠很多。"""
    try:
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        resp.raise_for_status()
    except Exception as exc:  # noqa: BLE001
        print(f"[圖片] 讀取官方頁面失敗，略過：{url}：{exc}")
        return {"image": "", "price": ""}

    image = ""
    price = ""
    try:
        soup = BeautifulSoup(resp.text, "html.parser")
        image_tag = (
            soup.find("meta", attrs={"property": "og:image"})
            or soup.find("meta", attrs={"name": "og:image"})
            or soup.find("meta", attrs={"name": "twitter:image"})
            or soup.find("meta", attrs={"property": "twitter:image"})
        )
        if image_tag and image_tag.get("content"):
            content = safe_str(image_tag.get("content"))
            if content and not content.startswith("http"):
                content = urljoin(url, content)
            image = valid_image_url(content)

        if not image:
            # 有些頁面沒設定 og:image，退而求其次找頁面裡看起來像展覽主視覺的 <img>
            img_tag = soup.find("img", src=re.compile(r"(exhibition|event|thumb|banner)", re.IGNORECASE))
            if img_tag and img_tag.get("src"):
                src = safe_str(img_tag["src"])
                if src and not src.startswith("http"):
                    src = urljoin(url, src)
                image = valid_image_url(src)

        price = extract_price_info(soup.get_text(" ", strip=True))
    except Exception as exc:  # noqa: BLE001
        print(f"[圖片] 解析官方頁面失敗，略過：{url}：{exc}")

    return {"image": image, "price": price}


# ---------------------------------------------------------------------------
# 額外場館來源：南港展覽館（TaiNEX 1館／2館）
# 官網「展會活動」頁面有清楚的活動列表格式，每個活動都有自己的詳情頁。
# ---------------------------------------------------------------------------

TAINEX_LIST_URL = "https://www.tainex.com.tw/event"
TAINEX_DATE_RANGE_PATTERN = re.compile(
    r"(\d{4})\s+(\d{2})/(\d{2})\(([^)]*)\)-(\d{2})/(\d{2})\(([^)]*)\)"
)
TAINEX_DATE_SINGLE_PATTERN = re.compile(r"(\d{4})\s+(\d{2})/(\d{2})\(([^)]*)\)")
TAINEX_HALL_PATTERN = re.compile(r"((?:\d館)+)$")


def fetch_tainex(max_events: int = 40):
    """抓取南港展覽館的展會活動列表"""
    events = []
    try:
        resp = requests.get(TAINEX_LIST_URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
        resp.raise_for_status()
    except Exception as exc:  # noqa: BLE001
        print(f"[南港展覽館] 讀取列表頁失敗：{exc}")
        return events

    soup = BeautifulSoup(resp.text, "html.parser")
    links = [a for a in soup.find_all("a", href=True) if re.search(r"/event/\d+$", a["href"])]

    # 同一個活動在頁面上可能有不只一個連結（例如完整卡片 + 館別小標籤），
    # 用 href 分組後，每組挑「有比對到日期格式、且文字最長」的那個，
    # 避免不小心抓到像「1館」這種殘缺的短文字當標題。
    texts_by_href = {}
    order = []
    for a in links:
        href = a["href"]
        text = " ".join(a.get_text(" ", strip=True).split())
        if not text:
            continue
        if href not in texts_by_href:
            texts_by_href[href] = []
            order.append(href)
        texts_by_href[href].append(text)

    for href in order[:max_events]:
        candidates = texts_by_href[href]
        dated = [
            t for t in candidates
            if TAINEX_DATE_RANGE_PATTERN.search(t) or TAINEX_DATE_SINGLE_PATTERN.search(t)
        ]
        text = max(dated, key=len) if dated else max(candidates, key=len)

        range_match = TAINEX_DATE_RANGE_PATTERN.search(text)
        single_match = None if range_match else TAINEX_DATE_SINGLE_PATTERN.search(text)

        if range_match:
            year, sm, sd, _, em, ed, _ = range_match.groups()
            start_date, end_date = f"{year}/{sm}/{sd}", f"{year}/{em}/{ed}"
            before, after = text[: range_match.start()], text[range_match.end():]
        elif single_match:
            year, m, d, _ = single_match.groups()
            start_date = end_date = f"{year}/{m}/{d}"
            before, after = text[: single_match.start()], text[single_match.end():]
        else:
            continue

        hall_match = TAINEX_HALL_PATTERN.search(before.strip())
        title = (before.strip()[: hall_match.start()] if hall_match else before.strip()).strip()
        # 保險起見：萬一挑到的文字整段就只是館別代碼（沒有真正的標題），直接跳過這筆，
        # 不要讓「1館」「2館」這種殘缺文字被當成展覽名稱收錄進去。
        if not title or re.fullmatch(r"(?:\d館)+", title):
            continue

        loc_match = re.search(r"地點：(.*)$", after)
        location_detail = loc_match.group(1).strip() if loc_match else ""

        full_url = href if href.startswith("http") else f"https://www.tainex.com.tw{href}"
        extras = fetch_detail_extras(full_url)
        categories = classify_category("", title, "")

        events.append({
            "title": title,
            "categories": categories,
            "category": categories[0],
            "unit": "",
            "description": "",
            "image": extras["image"],
            "price": extras["price"],
            "startDate": start_date,
            "endDate": end_date,
            "location": location_detail or "台北市南港區經貿二路",
            "locationName": "南港展覽館",
            "sourceUrl": full_url,
            "sourceName": "南港展覽館",
            "latitude": "25.0553",
            "longitude": "121.6172",
        })

    return events


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

    try:
        tainex_events = fetch_tainex()
        tainex_events = [e for e in tainex_events if is_still_relevant(e, now)]
        print(f"[南港展覽館] 抓到 {len(tainex_events)} 筆活動")
        events.extend(tainex_events)
    except Exception as exc:  # noqa: BLE001
        print(f"[南港展覽館] 整體抓取失敗，略過：{exc}")

    before_count = len(events)
    events = [
        e for e in events
        if is_major_venue(e)
        and not is_small_scale_activity(e["title"])
        and len(e["title"].strip()) >= 2
        and not re.fullmatch(r"(?:\d+館|\d+F|\d+樓)+", e["title"].strip())
    ]
    print(f"套用大型展場白名單：{before_count} 筆 → {len(events)} 筆")

    # 場館名稱統一收斂（西4館、西5-1館 -> 統一顯示成正式場館名稱）
    for event in events:
        event["locationName"] = canonical_venue_name(event["locationName"])

    # 沒有圖片的活動，嘗試進到活動自己的官方頁面抓官方宣傳圖與票價資訊
    missing_image_count = sum(1 for e in events if not e.get("image"))
    print(f"補抓官方宣傳圖／票價：{missing_image_count} 筆活動目前沒有圖片")
    for event in events:
        if not event.get("sourceUrl"):
            continue
        needs_image = not event.get("image")
        needs_price = not event.get("price")
        if needs_image or needs_price:
            extras = fetch_detail_extras(event["sourceUrl"])
            if needs_image and extras["image"]:
                event["image"] = extras["image"]
            if needs_price and extras["price"]:
                event["price"] = extras["price"]

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
