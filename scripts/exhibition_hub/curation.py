"""Public-feed curation policy for Taiwan Exhibition Journal.

The production enrichment file intentionally keeps broad source coverage for
review and auditing. The public site consumes a smaller curated feed focused on
major venues and high-interest events with a usable image and outbound link.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import date, datetime, timedelta, timezone
import re
from typing import Any, Iterable, Mapping
from urllib.parse import urlparse

from exhibition_hub.classifiers.content_types import classify_event
from exhibition_hub.image_quality import clean_image_urls


FACEBOOK_HOST_RE = re.compile(r"(^|\.)(facebook\.com|fb\.com|fb\.me)$", re.I)
SHORTENER_HOST_RE = re.compile(r"(^|\.)(reurl\.cc)$", re.I)
LIBRARY_RE = re.compile(r"圖書館|分館|圖書室|閱覽室|書庫|library", re.I)
DISTRICT_ONLY_RE = re.compile(
    r"^(?:(?:臺|台).{1,8}[市縣]|.{1,8}(?:區|鄉|鎮|市)[（(](?:臺|台).+[市縣][）)])$"
)
GENERIC_SPACE_RE = re.compile(
    r"^(?:第?\s*[一二三四五六七八九十0-9]+(?:\s*[、,，~～\-]\s*[一二三四五六七八九十0-9]+)*|"
    r"第?\s*[一二三四五六七八九十0-9]+(?:樓|展覽廳|展覽室|展廳)|"
    r"(?:一|二|三|四|五|六|七|八|九|十|[0-9]+)樓|"
    r"展覽廳|展覽室|展廳|多功能室|會議室|大廳|中庭)$"
)
SMALL_LOCAL_RE = re.compile(
    r"社區|里民|里辦公處|活動中心|地方社團|同好會|讀書會|故事時間|故事媽媽|"
    r"繪本說故事|親子共讀|假日電影院|外展服務|工作坊|研習|課程|講座|座談|"
    r"導覽活動|文化走讀|城市走讀|手作體驗|DIY|成果展|學生作品展|校內展|"
    r"高中|國中|國小|大學.{0,8}(?:系|所|社)|社團|成果發表|成果音樂會|畢業製作|"
    r"畢業展|校慶|班展|師生聯展|學生成果|社區大學|會員展|會員聯展|"
    r"書畫學會|攝影學會|美術學會|藝術學會|鄉公所|鎮公所|區公所|地方文化館",
    re.I,
)
PERMANENT_RE = re.compile(r"常設展|常設館|常態展|永久展", re.I)
MAJOR_TITLE_RE = re.compile(
    r"國際|全國|世界|巡迴|演唱會|音樂祭|音樂節|博覽會|藝術節|設計節|"
    r"影展|電影節|雙年展|三年展|特展|大展|聯展|個展|展演|劇場|歌劇|"
    r"舞台劇|音樂會|world\s+tour|asia\s+tour|concert",
    re.I,
)

SINGER_CONCERT_RE = re.compile(
    r"演唱會|巡迴演唱|fan\s*concert|live\s+in\s+(?:taipei|kaohsiung|taichung)|"
    r"live\s+tour|world\s+tour|asia\s+tour|tour\s*20\d{2}|concert\s*(?:20\d{2})?",
    re.I,
)
FILM_RE = re.compile(r"電影|影展|放映|映後|紀錄片|短片節|動畫影展|劇場版|台語片預告", re.I)
# ``劇場版`` means a theatrical film release, not a live theatre performance.
PERFORMANCE_RE = re.compile(r"音樂劇|歌劇|舞台劇|劇場(?!版)|劇團|演社|京劇|掌中劇|歌仔戲|布袋戲|戲劇|讀劇|偶戲|馬戲|歌舞劇|光影戲|漫才|脫口秀|相聲", re.I)
DANCE_RE = re.compile(r"舞蹈|舞作|舞團|舞者|編舞|芭蕾|現代舞|街舞|國標舞|大群舞|驫舞|dance", re.I)
MUSIC_RE = re.compile(
    r"音樂會|交響|管弦|管樂|擊樂|弦樂|協奏|獨奏|重奏|室內樂|古典音樂|"
    r"爵士|國樂|古典樂|樂團|合唱|重唱|阿卡貝拉|演奏會|音樂祭|音樂節|專場|不插電|live\s*house|"
    r"流行音樂(?:故事|文化|主題|常設|特)?展|音樂故事展",
    re.I,
)
CLASSICAL_MUSIC_RE = re.compile(r"音樂會|交響|管弦|協奏|獨奏|重奏|室內樂|古典音樂|鋼琴|小提琴|大提琴|國樂|演奏會", re.I)
ANIME_RE = re.compile(r"動漫|動畫|漫畫(?:原作|展)?|原畫展|電玩|遊戲展|電競|ACG|cosplay|公仔|角色展|角色限定|模型展|玩具展|扭蛋|盒玩|卡牌|聲優|VTuber|虛擬偶像|特攝|輕小說|IP(?:展|祭|授權)|寶可夢|吉伊卡哇|chiikawa|櫻桃小丸子|蠟筆小新|哆啦\s*A\s*夢|三麗鷗|迪士尼|皮克斯|宮崎駿|貓貓蟲咖波|小熊維尼|史努比|PEANUTS|SNOOPY|PPULBATU|KYBUBI|姆明|伊藤潤二|航海王|ONE\s*PIECE|鬼滅之刃|咒術迴戰|進擊的巨人|排球少年|名偵探柯南|七龍珠|鋼彈|GUNDAM|新世紀福音戰士|初音未來|hololive|anime", re.I)
PHOTO_RE = re.compile(r"攝影|影像展|photography|photo\s+exhibition", re.I)
NATURE_RE = re.compile(r"自然史|自然(?:展|特展|常設展)?|生態|植物(?:展|園)|野生動物|動物(?:展|園)|天文|地質|海洋(?:生態|科學|特展)|環境教育|科學館", re.I)
HISTORY_RE = re.compile(r"歷史|文化資產|文物|考古|古蹟|史料|民俗|紀念(?:特展|展)|法老|埃及|古文明|文藝復興|史前|日治|戰後|二戰", re.I)
# The old plain ``AI`` alternative also matched the letters "ai" in Taiwan.
TECH_RE = re.compile(r"科技|人工智慧|(?<![A-Za-z])AI(?![A-Za-z])|數位科技|半導體|資訊展|電腦展|機器人|虛擬實境|擴增實境|(?<![A-Za-z])VR(?![A-Za-z])|(?<![A-Za-z])AR(?![A-Za-z])", re.I)
DESIGN_RE = re.compile(r"設計|建築|工藝|時尚|家居|文具|文博會|design", re.I)
ART_RE = re.compile(r"美術|藝術(?:展|創作|作品)|插畫|圖畫書|繪畫|雕塑|裝置|當代藝術|典藏|書畫|陶藝|版畫|水墨|個展|聯展|畫展", re.I)
POPUP_RE = re.compile(r"快閃|期間限定|限定店|pop-?up|行動車", re.I)
MARKET_RE = re.compile(r"市集|蚤之市|展售會|餐車", re.I)
CHILD_RE = re.compile(r"親子|兒童|家庭|幼兒", re.I)
COMPETITION_RE = re.compile(r"競賽|比賽|大賽|徵件比賽", re.I)
MUSIC_PROGRAM_RE = re.compile(
    r"演出曲目|program|musicians?|指揮|小提琴|大提琴|鋼琴|長笛|單簧管|雙簧管|"
    r"symphony|concerto|sonata|orchestra|樂章|歌手|歌曲|唱片|音樂旅程|樂聲|歌聲|"
    r"作品(?:第|[0-9])|op\.?\s*[0-9]",
    re.I,
)
KNOWN_FILM_PROGRAM_RE = re.compile(
    r"高雄市電影館|府中15.*(?:放映|重映)|數位修復版|4K修復|特別放映|經典重映",
    re.I,
)
PERFORMANCE_DESCRIPTION_RE = re.compile(
    r"是一齣|舞台劇|音樂劇|歌劇|劇場作品|表演作品|跨域表演|舞蹈演出|音樂肢體劇場|變裝藝術與紀錄劇場|示範表演|"
    r"(?:演員|舞者).{0,24}(?:演出|舞台)|(?:編舞|導演).{0,24}(?:作品|演出)",
    re.I,
)
MUSIC_DESCRIPTION_RE = re.compile(
    r"本(?:場)?音樂會|音樂會由|國樂團|絲竹樂團|管弦樂團|管樂團|室內樂團|交響樂團|演奏家|獨奏家",
    re.I,
)
ART_DESCRIPTION_RE = re.compile(
    r"參展藝術家|藝術家[：:]|創作個展|策展人|展出作品|大型雕塑|雕塑物件|"
    r"繪畫作品|裝置藝術|藝術計畫|玻璃藝術",
    re.I,
)
PUBLIC_NON_CATALOG_ACTIVITY_RE = re.compile(
    r"故事聯合國|苗北藝術學苑.*講堂|北藝學院[｜|].*人物筆記|藝術家對談|"
    r"手語導覽|節目導覽|街區導覽|深度導覽|Live\s*Podcast|保證金繳交|"
    r"做一個月桃提包|黑白講[・·]鬥嘴鼓",
    re.I,
)

VERIFIED_CATEGORY_OVERRIDES: dict[str, tuple[str, ...]] = {
    "2026華山親子表藝節—米特動物樂園《忘忘島的失物招領處》": ("表演", "親子"),
    "仰懷宗範──開山祖師圓寂十週年紀念特展": ("歷史",),
    "職男人生4-笑の祭典": ("表演",),
    "魔幻樂章-銅管村嘉年華": ("音樂", "親子"),
    "臨時公共空間的臨時展覽": ("設計",),
    "2026 正港雄有戲《功德嘉年華》": ("表演",),
    "金枝演社：當代野台《飛賊夜來香》": ("表演", "市集"),
    "流變之境─王振瑋的風景構築與空間感知": ("美術",),
    "《穿越時空的航海家》": ("科技", "歷史"),
    "唐藝庭《層疊的空間》、 洪聖雄《砌殼》": ("美術",),
    "216": ("舞蹈",),
    "IKEA收納行動車": ("快閃店",),
    "ㄐㄧㄣˋ ㄒㄧㄤ": ("表演",),
    "天保": ("表演",),
    "小梅的奇幻冒險：尋回心意之書": ("動漫",),
    "星球樂園PLANET PARK-全境式互動樂園": ("科技",),
    "燈島人": ("表演",),
    "牧神的午後 | L'Après-midi d’un faune": ("美術",),
    "觀測點：不在，此在": ("表演",),
    "LANDSCAPES TO-GO 地景選物店": ("設計",),
    "《果子們 特展》": ("美術",),
    "島嶼生花": ("設計",),
    "轉機：臺灣女子移動紀事特展": ("歷史",),
    "穹頂計畫III 末日慶典": ("科技",),
    "穹頂計畫Ⅱ 潘神之子": ("科技",),
    "穹頂計畫": ("科技",),
    "「文學之路：一起讀書、考試、交朋友的日子」特展": ("歷史",),
    "博物館的秘室": ("歷史",),
    "金鷹歸來：隆興閣掌中武林特展": ("歷史",),
    "音樂的交會點~傳統八音，說出當代語言": ("音樂",),
    "2026夏日放／FUN時光—嚎哮排演《別叫我成功：藝術界歸來的兒子》": ("表演",),
    "亞洲在場：臺灣與亞洲運動會特展": ("歷史",),
    "糖分與鹽分文學賞——臺南文學滋味": ("歷史",),
    "字遊，自在：旅行文學展": ("歷史",),
    "2026漂浮探險隊2.0：月光任務": ("表演", "親子"),
    "【亞洲首站】愛麗絲夢遊仙境:兔子洞的秘密｜沈浸式互動故事特展": ("美術", "科技"),
    "MAX MAYDAYLAND in TAIPEI 台北站 5525+2｜北中南大串聯展": ("音樂",),
    "玉山文教基金會輕鬆自在場《我們的歌》": ("音樂",),
    "《迪士尼金曲派對》Disney Hits LIVE！": ("音樂", "動漫"),
    "義興閣掌中劇團《豆花公劇場版－拍斷手骨顛倒勇》": ("表演",),
    "2027風動室內樂團《無限》電影配樂音樂會": ("音樂",),
    "2026管風琴推廣音樂會特別企劃版《電影、愛與希望！》": ("音樂",),
    "台語光影戲《山神的餅店》劇場版": ("表演",),
    "Silver Screen Memories電影時代—非非藝術團隊演唱會": ("演唱會",),
    "松菸夜光花園 光影展 THE LUMINOUS GARDEN": ("美術",),
    "2026創價公演-古典樂的顛覆與狂想": ("音樂",),
    "公爵的午後・文藝復興弓弦舞宴": ("音樂",),
    "2026伍拾製作《咖啡廳Dance to 30+》": ("舞蹈",),
    "2026臺北藝術節✕中國信託新舞臺藝術節：驫舞20《大群舞》": ("舞蹈",),
    "2026秋天藝術節 克里斯托斯．帕帕多普洛斯《步步》": ("舞蹈",),
    "2026 NTT遇見巨人—驫舞劇場《大群舞》": ("舞蹈",),
    "高雄市管樂團《聲動不朽》－經典音樂劇選粹": ("音樂",),
    "柏林雷寧廣場劇院《夢想清單》": ("表演",),
    "2026千手觀音/我的夢—台灣巡迴演出": ("舞蹈",),
    "PEANUTS夏日海灘祭": ("快閃店", "動漫"),
    "夏日萌盒祭": ("快閃店", "動漫"),
    "台灣滿枝枒_芬芳美麗": ("快閃店",),
    "李亭香": ("快閃店",),
    "原聲巴洛克樂團《2026 親子音樂劇場：好媽媽印章》": ("表演", "親子"),
    "新古典室內樂團《音樂馬戲劇場-邦卡的七彩布裙》": ("表演", "親子"),
    "2026新竹縣新響藝術季－新古典室內樂團《音樂馬戲劇場-邦卡的七彩布裙》": ("表演", "親子"),
    "臺灣國樂團《出大甲城》繪本劇場音樂會": ("音樂", "親子"),
    "米特動物樂園《表演廳的秘密》": ("表演", "親子"),
    "米特動物樂園《Do Re Mi 喜咧兜？》": ("表演", "親子"),
    "《Spotlight ─ 波蘭兒童插畫的狂歡舞台》": ("美術", "親子"),
    "大型兒童魔術劇《怪盜神偷-阿呆警察的復仇》": ("表演", "親子"),
    "小王子歷險記": ("音樂", "親子"),
    "2026北流金舞台 歌唱大賽": ("音樂", "競賽"),
    "KSO《燕子》歌劇音樂會": ("音樂",),
    "「望風亭戀歌」歌劇音樂會": ("音樂",),
    "《佛音雅樂・善念共鳴》一念清淨・萬象光明": ("音樂",),
    "紅樓之聲．悅爾風雅": ("音樂",),
    "鑽石舞台之夜": ("演唱會",),
    "鯨嶼紀—一座島嶼的藍色奇遇": ("表演",),
    "2026 NTT遇見巨人—2025-2026歌劇院駐館藝術家賴奇霞《共振計畫：感．響》": ("表演",),
    "《山水墨韻》音樂會": ("音樂",),
    "大廳計畫｜在變動之中生成：演算法的藝術（2026）": ("美術", "科技"),
}
PRICE_UNKNOWN_RE = re.compile(r"票價請見|依官網|待確認|另行公告|索票|未提供", re.I)
PRICE_FREE_RE = re.compile(r"免費|自由入場|免票|free", re.I)
PRICE_LOW_ALLOWED_RE = re.compile(r"捐款|樂捐|象徵性|銅板|學生優惠|兒童優惠", re.I)
VERIFIED_NATORI_RE = re.compile(r"natori[\s\S]*(?:koshin|march|行進)|(?:koshin|march|行進)[\s\S]*natori", re.I)
VERIFIED_NATORI_PRICE = "1F站席 NT$4,200／2F前座席 NT$3,600／2F後座席 NT$3,200／3F座席 NT$2,800／1F身障席 NT$2,100／2F身障席 NT$1,600"

TAIPEI_TZ = timezone(timedelta(hours=8))
MUTUALLY_EXCLUSIVE = {"演唱會", "音樂", "表演", "舞蹈", "電影"}



PUBLIC_EVENT_FIELDS = (
    "id", "title", "description", "sourceUrl", "sourceUrlVerified", "sourceUrlRejected",
    "image", "images", "categories", "category", "contentType", "contentTypes",
    "eventFormat", "editorialStatus", "editorialFlags", "startDate", "endDate",
    "locationName", "location", "venueGroup", "venueDetail", "venueNames", "venueName",
    "parentVenueName", "parentVenueId", "subVenueName", "subVenueNames",
    "venueIds", "venueId", "venueCoverageStatus", "unmatchedVenueValues", "address",
    "region", "regionCanonical", "latitude", "longitude", "coordinateSource", "price",
    "unit", "transitInfo", "hitRate", "source", "firstSeenAt", "lastSeenAt",
    "publicVenueId", "publicVenuePriority", "publicVenueType", "publicCurationReason",
)


def slim_public_event(event: Mapping[str, Any]) -> dict[str, Any]:
    """Return only fields used by the public frontend.

    Candidate/audit files keep the full source record. The public payload avoids
    repeated session, collector, parking, phone and merge diagnostics that are
    not rendered by the site and previously added several megabytes to startup.
    """
    return {
        field: deepcopy(event.get(field))
        for field in PUBLIC_EVENT_FIELDS
        if field in event and event.get(field) not in (None, "", [], {})
    }

def _clean(value: Any) -> str:
    return str(value or "").strip()


def _normalize_key(value: Any) -> str:
    text = _clean(value).replace("臺", "台").lower()
    return re.sub(r"[\s　()（）\-_/／・·,，.。:：;；|｜]+", "", text)


def _event_text(event: Mapping[str, Any]) -> str:
    fields = ("title", "locationName", "location", "venueGroup", "unit")
    return " ".join(_clean(event.get(field)) for field in fields)


def _event_place_values(event: Mapping[str, Any]) -> list[str]:
    values: list[str] = []
    for field in ("venueName", "locationName", "location", "venueGroup"):
        value = _clean(event.get(field))
        if value:
            values.append(value)
    for field in ("venueNames", "unmatchedVenueValues"):
        raw = event.get(field)
        if isinstance(raw, list):
            values.extend(_clean(item) for item in raw if _clean(item))
    return values


def valid_outbound_url(value: Any) -> bool:
    text = _clean(value)
    if not text:
        return False
    try:
        parsed = urlparse(text)
    except ValueError:
        return False
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return False
    host = parsed.hostname or ""
    if FACEBOOK_HOST_RE.search(host) or SHORTENER_HOST_RE.search(host):
        return False
    return True


def event_has_outbound_link(event: Mapping[str, Any]) -> bool:
    return valid_outbound_url(event.get("sourceUrl")) and not bool(event.get("sourceUrlRejected"))


def _image_values(event: Mapping[str, Any]) -> Iterable[str]:
    raw_images = event.get("images")
    if isinstance(raw_images, list):
        for value in raw_images:
            if isinstance(value, str):
                yield value
    image = event.get("image")
    if isinstance(image, str):
        yield image


def usable_event_images(event: Mapping[str, Any]) -> list[str]:
    images, _ = clean_image_urls(_image_values(event))
    return [
        image for image in images
        if not re.search(r"/img/app/dl_(?:ios|google)[^/]*\.(?:png|jpe?g|webp)", image, re.I)
    ]


def event_has_image(event: Mapping[str, Any]) -> bool:
    return bool(usable_event_images(event))


def is_generic_place(value: Any) -> bool:
    text = _clean(value)
    if not text:
        return True
    if GENERIC_SPACE_RE.fullmatch(text):
        return True
    if DISTRICT_ONLY_RE.fullmatch(text):
        return True
    if "場館資料整理中" in text or "地點待確認" in text:
        return True
    return False


def build_venue_indexes(matrix_payload: Mapping[str, Any]) -> tuple[dict[str, Mapping[str, Any]], dict[str, Mapping[str, Any]]]:
    by_id: dict[str, Mapping[str, Any]] = {}
    by_name: dict[str, Mapping[str, Any]] = {}
    for venue in matrix_payload.get("venues") or []:
        if not isinstance(venue, Mapping) or not venue.get("confirmed"):
            continue
        venue_id = _clean(venue.get("id"))
        if venue_id:
            by_id[venue_id] = venue
        names = [venue.get("name"), *(venue.get("aliases") or [])]
        if venue.get("venueComplexName"):
            names.append(venue.get("venueComplexName"))
        for name in names:
            key = _normalize_key(name)
            if key and key not in by_name:
                by_name[key] = venue
    return by_id, by_name


def match_venue(
    event: Mapping[str, Any],
    by_id: Mapping[str, Mapping[str, Any]],
    by_name: Mapping[str, Mapping[str, Any]],
) -> Mapping[str, Any] | None:
    for venue_id in event.get("venueIds") or []:
        if _clean(venue_id) in by_id:
            return by_id[_clean(venue_id)]
    best: tuple[int, Mapping[str, Any]] | None = None
    event_keys = [_normalize_key(value) for value in _event_place_values(event) if not is_generic_place(value)]
    for event_key in event_keys:
        if not event_key:
            continue
        exact = by_name.get(event_key)
        if exact:
            return exact
        for venue_key, venue in by_name.items():
            if len(venue_key) < 4:
                continue
            if venue_key in event_key or (len(event_key) >= 5 and event_key in venue_key):
                score = min(len(venue_key), len(event_key))
                if best is None or score > best[0]:
                    best = (score, venue)
    return best[1] if best else None


def is_singer_concert_title(title: str) -> bool:
    if FILM_RE.search(title) or PERFORMANCE_RE.search(title) or DANCE_RE.search(title):
        return False
    if CLASSICAL_MUSIC_RE.search(title) and not re.search(r"演唱會", title, re.I):
        return False
    return bool(SINGER_CONCERT_RE.search(title))


def sanitize_public_price(event: Mapping[str, Any]) -> tuple[str, str | None]:
    """Return a conservative public price and an optional correction reason.

    Source feeds occasionally expose date fragments or minimum-order numbers as
    ticket prices. The public site must prefer an official-page fallback over a
    precise-looking but unsupported amount.
    """
    raw = re.sub(r"\s+", " ", _clean(event.get("price"))).strip()
    if not raw:
        return "票價請見活動頁面", None
    if PRICE_FREE_RE.search(raw):
        return "免費入場", None
    if PRICE_UNKNOWN_RE.search(raw):
        return "票價請見活動頁面", None

    allow_low = bool(PRICE_LOW_ALLOWED_RE.search(raw))
    numeric_only = re.fullmatch(
        r"(?:NT\$?|TWD|新[臺台]幣|票價)?\s*[$＄]?\s*([0-9][0-9,]*)\s*(?:元)?",
        raw,
        re.I,
    )
    if numeric_only:
        amount = int(numeric_only.group(1).replace(",", ""))
        if 0 < amount < 50 and not allow_low:
            return "票價請見活動頁面", "unsupported_low_amount"

    values = [int(value.replace(",", "")) for value in re.findall(r"[0-9][0-9,]*", raw)]
    money_tokens = re.findall(
        r"(?:NT\$?|TWD|新[臺台]幣|[$＄])\s*([0-9][0-9,]*)|([0-9][0-9,]*)\s*元",
        raw,
        re.I,
    )
    money_values = [
        int((left or right).replace(",", ""))
        for left, right in money_tokens
        if left or right
    ]
    malformed_year_range = re.match(
        r"^(?:NT\$?|TWD|新[臺台]幣)?\s*[$＄]?\s*[0-9]{1,2}\s*[–—-]\s*2,?0[0-9]{2}(?:\D|$)",
        raw,
        re.I,
    )
    if malformed_year_range or (
        len(values) >= 2
        and any(1900 <= value <= 2100 for value in values)
        and min(values) <= 31
        and not any(value >= 50 for value in money_values)
    ):
        return "票價請見活動頁面", "date_fragment"

    title = _clean(event.get("title"))
    if re.search(r"演唱會|音樂會|live\s+tour|one[- ]man|concert", title, re.I):
        if len(values) == 1 and 0 < values[0] < 50 and not allow_low:
            return "票價請見活動頁面", "implausible_performance_price"
    return raw, None


def apply_verified_event_corrections(event: Mapping[str, Any]) -> dict[str, Any]:
    corrected = deepcopy(dict(event))
    title = _clean(corrected.get("title"))
    if VERIFIED_NATORI_RE.search(title):
        corrected["startDate"] = "2026-08-08"
        corrected["endDate"] = "2026-08-09"
        corrected["price"] = VERIFIED_NATORI_PRICE
        corrected["category"] = "演唱會"
        corrected["categories"] = ["演唱會"]
    elif "夢與緋光" in title:
        corrected["category"] = "音樂"
        corrected["categories"] = ["音樂", *[
            value for value in corrected.get("categories") or [] if value != "音樂"
        ]]
    return corrected


def public_categories(event: Mapping[str, Any]) -> list[str]:
    title = _clean(event.get("title"))
    description = _clean(event.get("description"))
    content_types = {
        _clean(value)
        for value in [event.get("contentType"), *(event.get("contentTypes") or [])]
        if _clean(value)
    }
    existing = [
        _clean(value)
        for value in [event.get("category"), *(event.get("categories") or [])]
        if _clean(value)
    ]

    verified = VERIFIED_CATEGORY_OVERRIDES.get(title)
    if verified:
        return list(verified)

    # Format and subject categories are title-led. A long description often
    # contains credits such as "舞台設計", "舞台美術", or a technology-company
    # sponsor; those words must never create public categories by themselves.
    if (
        "popup" in content_types
        or POPUP_RE.search(title)
        or ("快閃店" in existing and POPUP_RE.search(description))
    ):
        primary = "快閃店"
    elif KNOWN_FILM_PROGRAM_RE.search(title):
        primary = "電影"
    elif is_singer_concert_title(title):
        primary = "演唱會"
    elif DANCE_RE.search(title):
        primary = "舞蹈"
    elif re.search(r"歌劇音樂會", title, re.I):
        primary = "音樂"
    elif PERFORMANCE_RE.search(title):
        primary = "表演"
    elif MUSIC_RE.search(title):
        primary = "音樂"
    elif "film_screening" in content_types or FILM_RE.search(title):
        primary = "電影"
    elif "music_festival" in content_types:
        primary = "音樂"
    elif "音樂" in existing and MUSIC_PROGRAM_RE.search(f"{title} {description}"):
        primary = "音樂"
    elif "performance" in content_types and PERFORMANCE_DESCRIPTION_RE.search(description):
        primary = "表演"
    elif "performance" in content_types and MUSIC_DESCRIPTION_RE.search(description):
        primary = "音樂"
    elif "performance" in content_types:
        primary = "表演"
    elif "concert" in content_types:
        primary = "音樂"
    elif "festival" in content_types:
        primary = "表演"
    elif ANIME_RE.search(title):
        primary = "動漫"
    elif PHOTO_RE.search(title):
        primary = "攝影"
    elif NATURE_RE.search(title):
        primary = "自然"
    elif HISTORY_RE.search(title):
        primary = "歷史"
    elif TECH_RE.search(title):
        primary = "科技"
    elif DESIGN_RE.search(title):
        primary = "設計"
    elif ART_RE.search(title):
        primary = "美術"
    elif CHILD_RE.search(title):
        primary = "親子"
    elif COMPETITION_RE.search(title):
        primary = "競賽"
    elif MARKET_RE.search(title):
        primary = "市集"
    elif PERFORMANCE_DESCRIPTION_RE.search(description) and content_types.intersection({"market", "exhibition", "art_exhibition"}):
        primary = "表演"
    elif MUSIC_DESCRIPTION_RE.search(description) and content_types.intersection({"market", "exhibition", "art_exhibition"}):
        primary = "音樂"
    elif "market" in content_types and MARKET_RE.search(description):
        primary = "市集"
    elif content_types.intersection({"exhibition", "art_exhibition"}) and ART_DESCRIPTION_RE.search(description):
        primary = "美術"
    elif "art_exhibition" in content_types:
        primary = "美術"
    else:
        # When there is no defensible title or structured-type signal, a
        # conservative generic label is safer than a confident wrong one.
        primary = "其他"

    secondary: list[str] = []
    # Secondary categories also require an explicit title signal. This still
    # supports useful hybrids such as 音樂／動漫, 電影／動漫 and 快閃店／動漫.
    optional_rules = (
        ("動漫", ANIME_RE),
        ("親子", CHILD_RE),
        ("競賽", COMPETITION_RE),
    )
    for label, pattern in optional_rules:
        if label != primary and pattern.search(title) and label not in secondary:
            secondary.append(label)

    # Visual-art, design, history, nature and technology words are reliable
    # secondary subjects only for exhibitions. In a concert or theatre title
    # they are usually metaphors, repertoire names or production credits.
    if content_types.intersection({"exhibition", "art_exhibition"}):
        exhibition_subject_rules = (
            ("攝影", PHOTO_RE), ("自然", NATURE_RE), ("歷史", HISTORY_RE),
            ("科技", TECH_RE), ("設計", DESIGN_RE), ("美術", ART_RE),
        )
        for label, pattern in exhibition_subject_rules:
            if label != primary and pattern.search(title) and label not in secondary:
                secondary.append(label)
    return [primary, *secondary][:3]


def is_non_catalog_activity(event: Mapping[str, Any]) -> bool:
    """Return True for talks, tours and classes excluded from the public catalog."""
    return bool(PUBLIC_NON_CATALOG_ACTIVITY_RE.search(_clean(event.get("title"))))


def _event_is_current_or_future(event: Mapping[str, Any], today: date | None = None) -> bool:
    today = today or datetime.now(TAIPEI_TZ).date()
    try:
        end = date.fromisoformat(_clean(event.get("endDate"))[:10])
    except ValueError:
        return False
    return end >= today


def evaluate_event(
    event: Mapping[str, Any],
    by_id: Mapping[str, Mapping[str, Any]],
    by_name: Mapping[str, Mapping[str, Any]],
    *,
    today: date | None = None,
) -> tuple[bool, str, Mapping[str, Any] | None]:
    title = _clean(event.get("title"))
    text = _event_text(event)
    if not _event_is_current_or_future(event, today=today):
        return False, "expired", None
    if not event_has_outbound_link(event):
        return False, "missing_outbound_link", None
    if not event_has_image(event):
        return False, "missing_image", None
    if LIBRARY_RE.search(text):
        return False, "library_series", None
    if SMALL_LOCAL_RE.search(text):
        return False, "small_local_activity", None
    if is_non_catalog_activity(event):
        return False, "non_catalog_activity", None

    venue = match_venue(event, by_id, by_name)
    if not venue and all(is_generic_place(value) for value in _event_place_values(event)):
        return False, "generic_or_district_only_place", None

    hit_rate = int(event.get("hitRate") or 0)
    if PERMANENT_RE.search(title):
        if not venue or venue.get("priority") != "P0" or hit_rate < 120:
            return False, "low_interest_permanent_exhibition", venue

    if venue:
        priority = _clean(venue.get("priority"))
        if priority == "P0":
            return True, "confirmed_P0", venue
        if priority == "P1" and (hit_rate >= 5 or MAJOR_TITLE_RE.search(title)):
            return True, "confirmed_P1_visible_interest", venue
        if priority == "P2" and hit_rate >= 80:
            return True, "confirmed_P2_high_interest", venue
        return False, "low_priority_or_low_interest_venue", venue

    if hit_rate >= 300 and MAJOR_TITLE_RE.search(title):
        return True, "unmatched_high_interest", None
    return False, "unmatched_or_low_interest", None


def build_curated_payload(
    source_payload: Mapping[str, Any],
    matrix_payload: Mapping[str, Any],
    *,
    today: date | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    by_id, by_name = build_venue_indexes(matrix_payload)
    kept: list[dict[str, Any]] = []
    removed_counts: dict[str, int] = {}
    kept_counts: dict[str, int] = {}
    removed_samples: dict[str, list[dict[str, Any]]] = {}
    price_corrections: dict[str, int] = {}
    price_correction_samples: list[dict[str, Any]] = []

    for raw_event in source_payload.get("events") or []:
        if not isinstance(raw_event, Mapping):
            continue
        event = apply_verified_event_corrections(classify_event(raw_event))
        categories = public_categories(event)
        event["categories"] = categories
        event["category"] = categories[0]
        original_price = _clean(event.get("price"))
        public_price, price_reason = sanitize_public_price(event)
        event["price"] = public_price
        if price_reason and public_price != original_price:
            price_corrections[price_reason] = price_corrections.get(price_reason, 0) + 1
            if len(price_correction_samples) < 30:
                price_correction_samples.append({
                    "id": event.get("id"),
                    "title": event.get("title"),
                    "originalPrice": original_price,
                    "publicPrice": public_price,
                    "reason": price_reason,
                })
        keep, reason, venue = evaluate_event(event, by_id, by_name, today=today)
        target = kept_counts if keep else removed_counts
        target[reason] = target.get(reason, 0) + 1
        if not keep:
            samples = removed_samples.setdefault(reason, [])
            if len(samples) < 12:
                samples.append({
                    "id": event.get("id"),
                    "title": event.get("title"),
                    "locationName": event.get("locationName"),
                    "sourceUrl": event.get("sourceUrl"),
                })
            continue
        clean_images = usable_event_images(event)
        event["images"] = clean_images[:10]
        event["image"] = clean_images[0]
        if venue:
            canonical_venue_id = _clean(venue.get("id"))
            event["publicVenueId"] = canonical_venue_id
            if canonical_venue_id:
                event["venueId"] = canonical_venue_id
                existing_venue_ids = event.get("venueIds")
                if not isinstance(existing_venue_ids, list):
                    existing_venue_ids = []
                event["venueIds"] = list(dict.fromkeys([
                    canonical_venue_id,
                    *[
                        _clean(value)
                        for value in existing_venue_ids
                        if _clean(value)
                    ],
                ]))
            event["publicVenuePriority"] = venue.get("priority")
            event["publicVenueType"] = venue.get("venueType")
        event["publicCurationReason"] = reason
        kept.append(slim_public_event(event))

    # Popular and current items first in the serialized feed. Frontend sorting
    # can still apply other views without reprocessing thousands of low-value rows.
    kept.sort(
        key=lambda event: (
            -int(event.get("hitRate") or 0),
            _clean(event.get("endDate")),
            _clean(event.get("title")),
        )
    )

    now = datetime.now(timezone.utc).isoformat()
    payload = deepcopy(dict(source_payload))
    payload["events"] = kept
    payload["updatedAt"] = source_payload.get("updatedAt") or now
    payload["source"] = "curated-public-feed"
    payload["curation"] = {
        "schemaVersion": 1,
        "builtAt": now,
        "sourceEventCount": len(source_payload.get("events") or []),
        "publicEventCount": len(kept),
        "policy": "major-venues-valid-link-image-no-library-no-small-local",
        "matrixVenueCount": len(matrix_payload.get("venues") or []),
    }
    original_stats = dict(source_payload.get("stats") or {})
    public_category_counts: dict[str, int] = {}
    for event in kept:
        for category in event.get("categories") or []:
            public_category_counts[category] = public_category_counts.get(category, 0) + 1
    original_stats.update({
        "sourceEventCount": len(source_payload.get("events") or []),
        "eventCount": len(kept),
        "curatedEventCount": len(kept),
        "imageCoverage": 100.0 if kept else 0.0,
        "outboundLinkCoverage": 100.0 if kept else 0.0,
        "categoryCounts": public_category_counts,
    })
    payload["stats"] = original_stats

    used_venues = {
        _clean(event.get("venueGroup") or event.get("locationName"))
        for event in kept
    }
    venue_images = source_payload.get("venueImages") or {}
    if isinstance(venue_images, Mapping):
        payload["venueImages"] = {
            key: value for key, value in venue_images.items()
            if key in used_venues
        }

    report = {
        "schemaVersion": 1,
        "builtAt": now,
        "sourceEventCount": len(source_payload.get("events") or []),
        "publicEventCount": len(kept),
        "removedEventCount": len(source_payload.get("events") or []) - len(kept),
        "keptReasons": dict(sorted(kept_counts.items())),
        "removedReasons": dict(sorted(removed_counts.items())),
        "removedSamples": removed_samples,
        "priceAudit": {
            "correctedCount": sum(price_corrections.values()),
            "correctionReasons": dict(sorted(price_corrections.items())),
            "samples": price_correction_samples,
        },
    }
    return payload, report
