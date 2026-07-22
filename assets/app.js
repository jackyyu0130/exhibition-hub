(() => {
  'use strict';

  const CATEGORY_ORDER = ['快閃','美術','攝影','設計','動漫','歷史文化','自然科學','親子','音樂','表演','舞蹈','電影','講座','研習','市集','競賽','科技','其他'];
  const iconSvg = body => `<svg viewBox="0 0 24 24" aria-hidden="true">${body}</svg>`;
  const CATEGORY_ICON = {
    '快閃': iconSvg('<path d="M4 9h16l-1.2-4H5.2L4 9Z"></path><path d="M5 9v10h14V9M9 19v-5h6v5"></path><path d="M4 9c0 1.3 1 2.3 2.3 2.3S8.7 10.3 8.7 9c0 1.3 1 2.3 2.3 2.3s2.3-1 2.3-2.3c0 1.3 1 2.3 2.3 2.3S18 10.3 18 9"></path>'),
    '美術': iconSvg('<rect x="4" y="4" width="16" height="16" rx="2"></rect><path d="m7 16 4-4 3 3 3-4 2 3"></path><circle cx="9" cy="9" r="1.4"></circle>'),
    '攝影': iconSvg('<path d="M4 8h3l1.5-2h7L17 8h3v11H4V8Z"></path><circle cx="12" cy="13.5" r="3.5"></circle>'),
    '設計': iconSvg('<path d="m4 20 4.5-1 9.8-9.8a2 2 0 0 0-2.8-2.8L5.7 16.2 4 20Z"></path><path d="m13.8 8.2 2.8 2.8M4 4h6M4 8h3"></path>'),
    '動漫': iconSvg('<path d="M5 5h14v10H9l-4 4V5Z"></path><path d="m10 8 .8 1.7 1.9.2-1.4 1.3.4 1.9-1.7-.9-1.7.9.4-1.9-1.4-1.3 1.9-.2L10 8Z"></path>'),
    '歷史文化': iconSvg('<path d="M4 9h16M6 9v8M10 9v8M14 9v8M18 9v8M3 19h18M12 4l8 4H4l8-4Z"></path>'),
    '自然科學': iconSvg('<circle cx="12" cy="12" r="2"></circle><ellipse cx="12" cy="12" rx="9" ry="4"></ellipse><ellipse cx="12" cy="12" rx="4" ry="9" transform="rotate(35 12 12)"></ellipse>'),
    '親子': iconSvg('<circle cx="9" cy="8" r="2.5"></circle><circle cx="16" cy="9" r="2"></circle><path d="M4.5 19c.5-4 2-6 4.5-6s4 2 4.5 6M13 19c.4-3 1.4-4.8 3-4.8s2.6 1.8 3 4.8"></path>'),
    '音樂': iconSvg('<path d="M9 18V6l10-2v12"></path><circle cx="6" cy="18" r="3"></circle><circle cx="16" cy="16" r="3"></circle>'),
    '表演': iconSvg('<path d="M5 5c3 0 5 1 7 3 2-2 4-3 7-3v7c0 4-3 7-7 7s-7-3-7-7V5Z"></path><path d="M8 10h.01M16 10h.01M9 14c2 1 4 1 6 0"></path>'),
    '舞蹈': iconSvg('<circle cx="12" cy="5" r="2"></circle><path d="m12 7-3 5 3 2 3-5M9 12l-4 3M12 14l-2 6M14 11l5 2M15 13l3 6"></path>'),
    '電影': iconSvg('<rect x="4" y="5" width="16" height="14" rx="2"></rect><path d="m10 9 5 3-5 3V9ZM4 8h16"></path>'),
    '講座': iconSvg('<rect x="8" y="3" width="8" height="11" rx="4"></rect><path d="M5 11a7 7 0 0 0 14 0M12 18v3M9 21h6"></path>'),
    '研習': iconSvg('<path d="M5 4h11a3 3 0 0 1 3 3v13H8a3 3 0 0 1-3-3V4Z"></path><path d="M8 4v16M11 8h5M11 12h5"></path>'),
    '市集': iconSvg('<path d="M6 8h12l1 12H5L6 8Z"></path><path d="M9 8V6a3 3 0 0 1 6 0v2"></path>'),
    '競賽': iconSvg('<path d="M8 4h8v4c0 4-1.5 6-4 7-2.5-1-4-3-4-7V4Z"></path><path d="M8 6H5v2c0 2 1 3 3 3M16 6h3v2c0 2-1 3-3 3M12 15v4M9 20h6"></path>'),
    '科技': iconSvg('<rect x="7" y="7" width="10" height="10" rx="2"></rect><path d="M9 1v4M15 1v4M9 19v4M15 19v4M1 9h4M1 15h4M19 9h4M19 15h4M10 10h4v4h-4z"></path>'),
    '其他': iconSvg('<circle cx="7" cy="7" r="2"></circle><circle cx="17" cy="7" r="2"></circle><circle cx="7" cy="17" r="2"></circle><circle cx="17" cy="17" r="2"></circle>')
  };
  const CATEGORY_SYMBOL = {'快閃':'閃','美術':'藝','攝影':'影','設計':'設','動漫':'漫','歷史文化':'史','自然科學':'科','親子':'親','音樂':'樂','表演':'演','舞蹈':'舞','電影':'映','講座':'講','研習':'學','市集':'集','競賽':'賽','科技':'技','其他':'展'};
  const CATEGORY_CODE_MAP = {'1':'音樂','2':'表演','3':'舞蹈','4':'親子','5':'音樂','6':'美術','7':'講座','8':'電影','11':'表演','13':'競賽','14':'其他','15':'其他','17':'音樂','19':'研習'};
  const CATEGORY_ALIASES = {
    '展覽':'美術','展覽資訊':'美術','藝術':'美術','戲劇':'表演','戲劇表演':'表演','綜藝':'表演','綜藝活動':'表演',
    '音樂表演':'音樂','獨立音樂':'音樂','演唱會':'音樂','講座資訊':'講座','親子活動':'親子','電影欣賞':'電影',
    '競賽活動':'競賽','徵選活動':'其他','徵選':'其他','商展':'其他','研習課程':'研習','其他藝文資訊':'其他'
  };
  const VENUE_ALIAS_RULES = [
    [/華山(?:1914)?(?:文化創意產業園區|文創園區)?/i,'華山1914文化創意產業園區'],
    [/松山文創園區|松菸(?:文創園區)?/i,'松山文創園區'],
    [/臺?北市立美術館|北美館/i,'臺北市立美術館'],
    [/國立臺?灣美術館|國美館/i,'國立臺灣美術館'],
    [/國立故宮博物院|故宮博物院|故宮(?:南院|北院)?/i,'國立故宮博物院'],
    [/駁二藝術特區|駁二/i,'駁二藝術特區'],
    [/衛武營(?:國家藝術文化中心)?/i,'衛武營國家藝術文化中心'],
    [/臺?中國家歌劇院|台中歌劇院/i,'臺中國家歌劇院'],
    [/臺?北表演藝術中心|北藝中心/i,'臺北表演藝術中心'],
    [/國家兩廳院|國家音樂廳|國家戲劇院/i,'國家兩廳院']
  ];
  const REGION_ORDER = ['台北市','新北市','基隆市','桃園市','新竹市','新竹縣','苗栗縣','台中市','彰化縣','南投縣','雲林縣','嘉義市','嘉義縣','台南市','高雄市','屏東縣','宜蘭縣','花蓮縣','台東縣','澎湖縣','金門縣','連江縣','其他地區'];
  const REGION_ALIASES = {'臺北市':'台北市','臺中市':'台中市','臺南市':'台南市','臺東縣':'台東縣'};
  const FAVORITES_KEY = 'exhibition-hub-favorites-v3';

  const state = {
    events: [],
    updatedAt: null,
    venueImages: {},
    params: new URLSearchParams(location.search),
    view: 'home',
    status: 'all',
    categories: new Set(),
    region: null,
    venue: null,
    date: null,
    query: '',
    sort: 'recommended',
    userLocation: null,
    map: null,
    markers: null,
    calendarMonth: null,
    heroTimer: null,
    heroCursor: 0,
    heroLastKeys: [],
    heroHasShuffled: false,
    lastRenderedDate: null,
  };

  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];

  function escapeHtml(value = '') {
    return String(value).replace(/[&<>'"]/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[char]));
  }

  function safeUrl(value = '') {
    try {
      let text = String(value ?? '').trim().replace(/\\\//g, '/');
      if (!text) return '';
      if (text.startsWith('//')) text = `https:${text}`;
      const url = new URL(text, location.href);
      return ['http:','https:'].includes(url.protocol) ? url.href : '';
    } catch { return ''; }
  }

  function firstValue(...values) {
    return values.find(value => value !== undefined && value !== null && String(value).trim() !== '') || '';
  }

  function normalizeRegion(value = '') {
    const normalized = REGION_ALIASES[String(value).trim()] || String(value).trim();
    if (REGION_ORDER.includes(normalized)) return normalized;
    return detectRegion(normalized);
  }

  function detectRegion(text = '') {
    const haystack = String(text);
    const found = REGION_ORDER.find(region => region !== '其他地區' && haystack.includes(region));
    if (found) return found;
    const alias = Object.keys(REGION_ALIASES).find(region => haystack.includes(region));
    return alias ? REGION_ALIASES[alias] : '其他地區';
  }

  function normalizeCategories(raw, title = '', description = '') {
    const rawValues = Array.isArray(raw) ? raw : raw !== undefined && raw !== null ? [raw] : [];
    const categories = [];
    rawValues.flatMap(value => String(value).split(/[、,，/|;；]+/)).forEach(value => {
      const text = value.trim();
      if (!text) return;
      const mapped = CATEGORY_CODE_MAP[text] || CATEGORY_ALIASES[text] || (CATEGORY_ORDER.includes(text) ? text : '');
      if (mapped && mapped !== '其他' && !categories.includes(mapped)) categories.push(mapped);
    });

    const text = `${title} ${description}`;
    const keywordRules = [
      ['快閃', /快閃|期間限定|popup|pop-up/i], ['攝影', /攝影|影像展|photo(graphy)?/i],
      ['動漫', /動漫|動畫|漫畫|卡通|anime|公仔|角色展|模型展/i], ['歷史文化', /歷史|文化資產|文物|考古|古蹟|史料|地方誌|民俗/i],
      ['自然科學', /自然史|科學|生態|植物|動物|天文|地質|海洋|環境教育/i], ['科技', /科技|人工智慧|AI|數位科技|半導體|資訊展|電腦展|機器人/i],
      ['設計', /設計|建築|工藝|時尚|家居|文具|design/i], ['舞蹈', /舞蹈|舞作|芭蕾/i],
      ['音樂', /音樂|演唱會|樂團|管弦|獨立音樂|concert/i], ['表演', /戲劇|劇場|表演|歌劇|馬戲|音樂劇|偶戲/i],
      ['電影', /電影|影展|放映/i], ['講座', /講座|論壇|座談|分享會|演講/i],
      ['研習', /研習|課程|工作坊|營隊/i], ['市集', /市集|祭典|嘉年華|展售|商品展|食品展|旅展|文創攤位/i],
      ['親子', /親子|兒童|家庭|幼兒/i], ['競賽', /競賽|比賽|大賽|徵件比賽/i],
      ['美術', /美術|藝術|繪畫|雕塑|裝置|當代|典藏|書畫|陶藝|視覺藝術|藝術博覽會|插畫博覽會/i]
    ];
    keywordRules.forEach(([category, regex]) => {
      if (regex.test(text) && !categories.includes(category)) categories.unshift(category);
    });
    const cleaned = categories.filter(category => CATEGORY_ORDER.includes(category));
    return (cleaned.length ? cleaned : ['其他']).filter((category, index, array) => array.indexOf(category) === index).slice(0, 3);
  }

  function cleanPlaceText(value = '') {
    return String(value || '')
      .replace(/&nbsp;/gi, ' ')
      .replace(/[=＝:：;；|｜]+\s*$/g, '')
      .replace(/^[=＝:：;；|｜]+/g, '')
      .replace(/\s*[（(](?:臺|台)([^）)]+)[）)]\s*$/g, '（台$1）')
      .replace(/\s{2,}/g, ' ')
      .trim();
  }

  function venueParts(rawVenue = '', address = '', rawGroup = '', rawDetail = '') {
    const original = cleanPlaceText(firstValue(rawVenue, address, '地點待確認'));
    let group = cleanPlaceText(rawGroup);
    let detail = cleanPlaceText(rawDetail);
    if (!group) {
      const rule = [...VENUE_ALIAS_RULES].sort((a,b) => String(b[0]).length - String(a[0]).length).find(([pattern]) => pattern.test(original));
      if (rule) {
        group = rule[1];
        detail = cleanPlaceText(original.replace(rule[0], ''));
      }
    }
    if (!group) group = original;
    const districtOnly = /^(?:(?:臺|台|新北|桃園|新竹|苗栗|彰化|南投|雲林|嘉義|高雄|屏東|宜蘭|花蓮|臺東|台東|澎湖|金門|連江).{0,3}[市縣].{1,4}區|.{1,6}區(?:[（(](?:臺|台).+[市縣][）)])?)$/.test(group);
    const addressLike = /(?:路|街|大道|巷|弄|號|樓)/.test(group) && !/(館|園區|中心|藝廊|劇院|展場|空間|博物館|美術館|文化館|文創)/.test(group);
    if (districtOnly || addressLike) group = `${normalizeRegion(firstValue(address, group))}｜場館資料整理中`;
    return {venueGroup: group || '地點待確認', venueDetail: detail};
  }

  function flattenImageCandidates(raw) {
    if (raw === undefined || raw === null || raw === '') return [];
    if (Array.isArray(raw)) return raw.flatMap(flattenImageCandidates);
    if (typeof raw === 'object') {
      const keys = ['url','src','href','image','imageUrl','imageURL','original','large','poster','cover'];
      const preferred = keys.flatMap(key => key in raw ? flattenImageCandidates(raw[key]) : []);
      return preferred.length ? preferred : Object.values(raw).flatMap(flattenImageCandidates);
    }
    if (typeof raw === 'string') {
      const value = raw.trim();
      if ((value.startsWith('[') && value.endsWith(']')) || (value.startsWith('{') && value.endsWith('}'))) {
        try { return flattenImageCandidates(JSON.parse(value)); } catch {}
      }
      return [value];
    }
    return [];
  }

  function normalizeImage(raw) {
    return flattenImageCandidates(raw).map(safeUrl).find(Boolean) || '';
  }

  function getShowEntries(raw) {
    const entries = [];
    ['showInfo','showinfo','show_info','shows','sessions'].forEach(key => {
      const value = raw?.[key];
      if (Array.isArray(value)) entries.push(...value.filter(item => item && typeof item === 'object'));
      else if (value && typeof value === 'object') entries.push(value);
    });
    return entries;
  }

  function coordinateValue(value, latitude) {
    const number = Number(String(value ?? '').trim().replace(',', '.'));
    const limit = latitude ? 90 : 180;
    return Number.isFinite(number) && number !== 0 && Math.abs(number) <= limit ? number : null;
  }

  function coordinatesFrom(...sources) {
    const latKeys = ['latitude','Latitude','lat','Lat','mapLat','y'];
    const lngKeys = ['longitude','Longitude','lng','lon','Lng','mapLng','x'];
    for (const source of sources) {
      if (!source || typeof source !== 'object') continue;
      const rawLat = firstValue(...latKeys.map(key => source[key]));
      const rawLng = firstValue(...lngKeys.map(key => source[key]));
      let latitude = coordinateValue(rawLat, true);
      let longitude = coordinateValue(rawLng, false);
      if (latitude !== null && longitude !== null) return {latitude, longitude};
      latitude = coordinateValue(rawLng, true);
      longitude = coordinateValue(rawLat, false);
      if (latitude !== null && longitude !== null) return {latitude, longitude};
    }
    return {latitude:null, longitude:null};
  }

  function bestShow(raw) {
    const entries = getShowEntries(raw);
    if (!entries.length) return {};
    const score = show => {
      const {latitude, longitude} = coordinatesFrom(show);
      return (latitude !== null && longitude !== null ? 100 : 0)
        + (firstValue(show.locationName, show.venue) ? 25 : 0)
        + (firstValue(show.location, show.address) ? 20 : 0)
        + (firstValue(show.time, show.startTime) ? 5 : 0);
    };
    return entries.sort((a,b) => score(b) - score(a))[0] || {};
  }

  function normalizeEvent(raw, index) {
    const show = bestShow(raw);
    const title = firstValue(raw.title, raw.titile, raw.name, '未命名展覽');
    const description = firstValue(raw.description, raw.descriptionFilterHtml, raw.comment);
    const address = cleanPlaceText(firstValue(raw.address, raw.location, show.location, show.address));
    const rawVenue = cleanPlaceText(firstValue(raw.locationName, raw.venue, show.locationName, show.venue, address));
    const {venueGroup, venueDetail} = venueParts(rawVenue, address, raw.venueGroup, raw.venueDetail);
    const sourceUrl = firstValue(raw.sourceUrl, raw.sourceWebPromote, raw.webSales, raw.sourceWebSite, raw.url, raw.website);
    const id = String(firstValue(raw.id, raw.UID, raw.uid, sourceUrl, `${title}-${index}`));
    const rawCategories = firstValue(raw.categories, raw.categoryName, raw.category);
    const imageCandidates = [
      ...flattenImageCandidates(raw.images), ...flattenImageCandidates(raw.imageCandidates),
      ...flattenImageCandidates(raw.image), ...flattenImageCandidates(raw.imageURL), ...flattenImageCandidates(raw.imageUrl),
      ...flattenImageCandidates(raw.imageUrls), ...flattenImageCandidates(raw.poster), ...flattenImageCandidates(raw.posterUrl),
      ...flattenImageCandidates(raw.picture), ...flattenImageCandidates(raw.pictureUrl), ...flattenImageCandidates(show.image),
      ...flattenImageCandidates(show.imageUrl), ...flattenImageCandidates(show.imageURL)
    ].map(safeUrl).filter(Boolean).filter((url, index, array) => array.indexOf(url) === index);
    const image = imageCandidates[0] || '';
    const {latitude, longitude} = coordinatesFrom(show, raw);
    const region = normalizeRegion(firstValue(raw.region, address, venueGroup, rawVenue));
    const price = firstValue(raw.price, raw.Price, show.price, raw.discountInfo, firstValue(show.onSales, raw.onSales) === 'N' ? '免費' : '');
    const categories = normalizeCategories(rawCategories, title, description);
    return {
      id, title: String(title).trim(), description: stripHtml(description),
      sourceUrl: safeUrl(sourceUrl), image,
      images: imageCandidates,
      categories, category: categories[0],
      startDate: firstValue(raw.startDate, raw.start, show.time, show.startTime),
      endDate: firstValue(raw.endDate, raw.end, raw.endTime, show.endTime, raw.startDate),
      locationName: String(venueGroup || '地點待確認').trim(),
      location: String(venueGroup || '地點待確認').trim(), venueGroup, venueDetail, address: String(address || '').trim(), region,
      latitude, longitude,
      price: String(price || '票價請見活動頁面').trim(),
      unit: Array.isArray(raw.masterUnit) ? raw.masterUnit.join('、') : firstValue(raw.unit, raw.organizer, raw.showUnit, raw.masterUnit),
      transitInfo: firstValue(raw.transitInfo, raw.transit),
      hitRate: Number(raw.hitRate || 0),
      firstSeenAt: firstValue(raw.firstSeenAt, raw.first_seen_at),
      lastSeenAt: firstValue(raw.lastSeenAt, raw.last_seen_at),
    };
  }

  function stripHtml(value = '') {
    const temp = document.createElement('div');
    temp.innerHTML = String(value);
    return (temp.textContent || '').replace(/\s{3,}/g, '\n\n').trim();
  }

  function parseDate(value) {
    if (!value) return null;
    const normalized = String(value).replace(/\//g, '-').replace(/(\d{4}-\d{2}-\d{2})(\d{2}:)/, '$1 $2');
    const date = new Date(normalized);
    return Number.isNaN(date.getTime()) ? null : date;
  }

  function dateOnly(date) {
    return new Date(date.getFullYear(), date.getMonth(), date.getDate());
  }

  function localDateKey(date) {
    return `${date.getFullYear()}-${String(date.getMonth()+1).padStart(2,'0')}-${String(date.getDate()).padStart(2,'0')}`;
  }

  function eventOccursOn(event, selectedDate) {
    const selected = selectedDate instanceof Date ? dateOnly(selectedDate) : parseDate(`${selectedDate}T00:00:00`);
    if (!selected) return false;
    const start = parseDate(event.startDate);
    const end = parseDate(event.endDate) || start;
    if (!start && !end) return false;
    return (!start || dateOnly(start) <= selected) && (!end || dateOnly(end) >= selected);
  }

  function isOngoing(event) {
    const today = dateOnly(new Date());
    const start = parseDate(event.startDate);
    const end = parseDate(event.endDate);
    return (!start || dateOnly(start) <= today) && (!end || dateOnly(end) >= today);
  }

  function isUpcoming(event) {
    const start = parseDate(event.startDate);
    return start && dateOnly(start) > dateOnly(new Date());
  }

  function isEnding(event, days = 14) {
    const end = parseDate(event.endDate);
    if (!end || !isOngoing(event)) return false;
    const diff = (dateOnly(end) - dateOnly(new Date())) / 86400000;
    return diff >= 0 && diff <= days;
  }

  function isFree(event) {
    return /免費|自由入場|免票|free/i.test(event.price || '');
  }

  function dateRange(event) {
    const start = parseDate(event.startDate);
    const end = parseDate(event.endDate);
    if (!start && !end) return '日期請見活動頁面';
    const fmt = date => `${date.getFullYear()}.${String(date.getMonth()+1).padStart(2,'0')}.${String(date.getDate()).padStart(2,'0')}`;
    if (start && end && dateOnly(start).getTime() !== dateOnly(end).getTime()) return `${fmt(start)} — ${fmt(end)}`;
    return fmt(start || end);
  }

  function compactDate(event) {
    const date = parseDate(isUpcoming(event) ? event.startDate : event.endDate) || parseDate(event.startDate);
    if (!date) return {day:'—', month:'DATE'};
    return {day:String(date.getDate()).padStart(2,'0'), month:`${date.getFullYear()}.${String(date.getMonth()+1).padStart(2,'0')}`};
  }

  function eventKey(event) { return event.id || event.sourceUrl || event.title; }
  function eventHref(event) { return `?event=${encodeURIComponent(eventKey(event))}`; }
  function categoryHref(category) { return `?view=all&category=${encodeURIComponent(category)}`; }
  function regionHref(region) { return `?view=all&region=${encodeURIComponent(region)}`; }
  function venueHref(venue) { return `?view=all&venue=${encodeURIComponent(venue)}`; }

  function getFavorites() {
    try { return JSON.parse(localStorage.getItem(FAVORITES_KEY) || '[]'); }
    catch { return []; }
  }

  function isFavorite(event) { return getFavorites().includes(eventKey(event)); }

  function toggleFavorite(event) {
    const key = eventKey(event);
    const favorites = getFavorites();
    const index = favorites.indexOf(key);
    if (index >= 0) favorites.splice(index, 1); else favorites.push(key);
    localStorage.setItem(FAVORITES_KEY, JSON.stringify(favorites));
    showToast(index >= 0 ? '已從收藏移除' : '已加入收藏');
    renderCurrentView();
  }

  function countBy(items, getter) {
    return items.reduce((result, item) => {
      const values = getter(item);
      (Array.isArray(values) ? values : [values]).filter(Boolean).forEach(value => result[value] = (result[value] || 0) + 1);
      return result;
    }, {});
  }

  function imageMarkup(event, className = '') {
    const candidates = (event.images?.length ? event.images : event.image ? [event.image] : []).filter(Boolean);
    if (!candidates.length) return `<div class="${className || 'card-placeholder'}">${escapeHtml(CATEGORY_SYMBOL[event.category] || '展')}</div>`;
    const serialized = escapeHtml(JSON.stringify(candidates));
    return `<img src="${escapeHtml(candidates[0])}" data-images="${serialized}" data-image-index="0" data-placeholder-class="${escapeHtml(className || 'card-placeholder')}" data-placeholder-text="${escapeHtml(CATEGORY_SYMBOL[event.category] || '展')}" alt="${escapeHtml(event.title)}" loading="lazy" referrerpolicy="no-referrer" onerror="window.__exhibitionImageFallback(this)">`;
  }

  window.__exhibitionImageFallback = image => {
    try {
      const candidates = JSON.parse(image.dataset.images || '[]');
      const nextIndex = Number(image.dataset.imageIndex || 0) + 1;
      if (candidates[nextIndex]) {
        image.dataset.imageIndex = String(nextIndex);
        image.src = candidates[nextIndex];
        return;
      }
    } catch {}
    const placeholder = document.createElement('div');
    placeholder.className = image.dataset.placeholderClass || 'card-placeholder';
    placeholder.textContent = image.dataset.placeholderText || '展';
    image.replaceWith(placeholder);
  };

  function isRecentlyAdded(event, days = 7) {
    const seen = parseDate(event.firstSeenAt);
    if (!seen) return false;
    const diff = (dateOnly(new Date()) - dateOnly(seen)) / 86400000;
    return diff >= 0 && diff <= days;
  }

  function specialBadges(event, {curated = false} = {}) {
    const badges = [];
    // 依使用者指定優先順序：最新收錄 → 即將開展 → 即將結束。
    if (isRecentlyAdded(event)) badges.push({label:'最新收錄', type:'new'});
    if (isUpcoming(event)) badges.push({label:'即將開展', type:'upcoming'});
    if (isEnding(event)) badges.push({label:'即將結束', type:'ending'});
    if (isFree(event)) badges.push({label:'免費入場', type:'free'});
    if (curated && !badges.length) badges.push({label:'本週精選', type:'curated'});
    return badges.slice(0, 2);
  }

  function cardMarkup(event, options = {}) {
    const badges = specialBadges(event, options);
    const revealStyle = Number.isInteger(options.revealIndex) ? ` style="--reveal-index:${options.revealIndex}"` : '';
    return `
      <article class="exhibition-card${Number.isInteger(options.revealIndex) ? ' date-reveal-card' : ''}"${revealStyle}>
        <a class="card-image" href="${eventHref(event)}">
          ${imageMarkup(event)}
          ${badges.length ? `<span class="card-badges">${badges.map(badge => `<span class="card-badge badge-${badge.type}">${badge.label}</span>`).join('')}</span>` : ''}
        </a>
        <button class="favorite-button ${isFavorite(event) ? 'active' : ''}" type="button" data-favorite="${escapeHtml(eventKey(event))}" aria-label="${isFavorite(event) ? '取消收藏' : '加入收藏'}">${isFavorite(event) ? '♥' : '♡'}</button>
        <div class="card-body">
          <div class="card-kicker"><span>${escapeHtml(event.categories[0] || '展覽')}</span><span>${escapeHtml(event.region)}</span></div>
          <a href="${eventHref(event)}"><h3 class="card-title">${escapeHtml(event.title)}</h3></a>
          <div class="card-meta"><span>${escapeHtml(dateRange(event))}</span><span>${escapeHtml(event.venueGroup || event.locationName)}</span></div>
          <div class="card-price ${isFree(event) ? 'free' : ''}">${escapeHtml(event.price)}</div>
        </div>
      </article>`;
  }

  function compactMarkup(event) {
    const date = compactDate(event);
    return `<a class="compact-item" href="${eventHref(event)}">
      <div class="compact-date"><strong>${date.day}</strong><span>${date.month}</span></div>
      <div class="compact-info"><h4>${escapeHtml(event.title)}</h4><p>${escapeHtml(event.venueGroup || event.locationName)} · ${escapeHtml(event.region)}</p></div>
      <span class="compact-arrow">↗</span>
    </a>`;
  }

  function nearbyMiniMarkup(event, distance = null) {
    return `<a class="nearby-mini-card" href="${eventHref(event)}">
      ${imageMarkup(event, 'nearby-mini-media')}
      <div class="nearby-mini-body"><small>${distance === null ? escapeHtml(event.region) : `${distance.toFixed(1)} KM`}</small><h3>${escapeHtml(event.title)}</h3><p>${escapeHtml(event.venueGroup || event.locationName)}</p></div>
    </a>`;
  }

  function resultMarkup(event, distance) {
    return `<a class="nearby-result-card" href="${eventHref(event)}">
      ${imageMarkup(event, 'nearby-result-media')}
      <div><small>${Number.isFinite(distance) ? `${distance.toFixed(1)} KM` : escapeHtml(event.region)}</small><h3>${escapeHtml(event.title)}</h3><p>${escapeHtml(dateRange(event))}</p><p>${escapeHtml(event.venueGroup || event.locationName)}</p></div>
    </a>`;
  }

  function readParams() {
    const params = state.params;
    state.query = params.get('q') || '';
    const categoryValues = params.getAll('category').flatMap(value => String(value).split(',')).map(value => value.trim()).filter(category => CATEGORY_ORDER.includes(category));
    state.categories = new Set(categoryValues);
    state.region = params.get('region') || null;
    state.venue = params.get('venue') || null;
    state.status = params.get('status') || 'all';
    state.date = params.get('date') || null;
    const calendarAnchor = state.date ? parseDate(`${state.date}T00:00:00`) : new Date();
    state.calendarMonth = new Date(calendarAnchor.getFullYear(), calendarAnchor.getMonth(), 1);
    if (params.has('event')) state.view = 'detail';
    else if (params.get('view') === 'nearby') state.view = 'nearby';
    else if (params.get('view') === 'favorites') state.view = 'favorites';
    else if (params.get('view') === 'all' || state.query || state.categories.size || state.region || state.venue || params.has('status')) state.view = 'listing';
    else state.view = 'home';
  }

  function filterEvents(items = state.events, options = {}) {
    const {includeDate = true} = options;
    const query = state.query.trim().toLowerCase();
    return items.filter(event => {
      if (query) {
        const haystack = [event.title,event.description,event.locationName,event.address,event.region,event.categories.join(' '),event.price].join(' ').toLowerCase();
        if (!haystack.includes(query)) return false;
      }
      if (state.categories.size && !event.categories.some(category => state.categories.has(category))) return false;
      if (state.region && event.region !== state.region) return false;
      if (state.venue && (event.venueGroup || event.locationName) !== state.venue) return false;
      if (state.status === 'ongoing' && !isOngoing(event)) return false;
      if (state.status === 'upcoming' && !isUpcoming(event)) return false;
      if (state.status === 'ending' && !isEnding(event, 30)) return false;
      if (state.status === 'free' && !isFree(event)) return false;
      if (includeDate && state.date && !eventOccursOn(event, state.date)) return false;
      return true;
    });
  }

  function sortEvents(items) {
    const result = [...items];
    if (state.sort === 'newest') result.sort((a,b) => (parseDate(b.startDate)?.getTime() || 0) - (parseDate(a.startDate)?.getTime() || 0));
    else if (state.sort === 'ending') result.sort((a,b) => (parseDate(a.endDate)?.getTime() || Infinity) - (parseDate(b.endDate)?.getTime() || Infinity));
    else if (state.sort === 'title') result.sort((a,b) => a.title.localeCompare(b.title, 'zh-Hant'));
    else result.sort((a,b) => recommendationScore(b) - recommendationScore(a));
    return result;
  }

  function recommendationScore(event) {
    let score = Math.min(event.hitRate || 0, 50000) / 500;
    if (event.image) score += 20;
    if (isOngoing(event)) score += 18;
    if (isEnding(event)) score += 8;
    if (event.description.length > 80) score += 5;
    score += Math.random() * .001;
    return score;
  }

  function selectFeatured(items, count = 8) {
    const sorted = [...items].sort((a,b) => recommendationScore(b) - recommendationScore(a));
    const withImages = sorted.filter(event => event.image);
    return [...withImages, ...sorted.filter(event => !event.image)].filter((event, index, arr) => arr.findIndex(other => eventKey(other) === eventKey(event)) === index).slice(0, count);
  }

  function heroTicketMarkup(event, slot) {
    const label = slot === 0 ? '觀展靈感' : slot === 1 ? '編輯精選' : '下一站推薦';
    return `<a class="hero-ticket-card hero-ticket-slot-${slot + 1}" href="${eventHref(event)}" aria-label="查看展覽：${escapeHtml(event.title)}">
      <div class="ticket-topline"><span>TAIWAN EXHIBITION</span><span>ADMIT ONE</span></div>
      <div class="ticket-main">
        <span class="ticket-index">${String(slot + 1).padStart(2,'0')}</span>
        <div><small>${label} · ${escapeHtml(event.categories[0] || '展覽')}</small><h2>${escapeHtml(event.title)}</h2><p>${escapeHtml(dateRange(event))} · ${escapeHtml(event.venueGroup || event.locationName)}</p></div>
      </div>
      <div class="ticket-footer"><span>EXHIBITION JOURNAL</span><span class="barcode">|||| ||| ||||</span></div>
    </a>`;
  }

  function randomHeroPicks(pool) {
    const previous = new Set(state.heroLastKeys);
    const fresh = pool.filter(event => !previous.has(eventKey(event)));
    const source = fresh.length >= 3 ? fresh : pool;
    const shuffled = [...source].sort(() => Math.random() - .5);
    const picks = [];
    for (const event of shuffled) {
      if (!picks.some(item => eventKey(item) === eventKey(event))) picks.push(event);
      if (picks.length === Math.min(3, pool.length)) break;
    }
    state.heroLastKeys = picks.map(eventKey);
    return picks;
  }

  function renderHeroTickets({animate = true} = {}) {
    const stack = $('#heroTicketStack');
    if (!stack) return;
    const base = state.events.filter(event => isOngoing(event) || isUpcoming(event));
    const pool = selectFeatured(base.length ? base : state.events, Math.min(48, state.events.length));
    if (!pool.length) return;
    const picks = randomHeroPicks(pool);
    const apply = () => {
      stack.innerHTML = picks.map(heroTicketMarkup).join('');
      stack.classList.remove('is-changing');
      requestAnimationFrame(() => stack.classList.add('is-entering'));
      setTimeout(() => stack.classList.remove('is-entering'), 1850);
    };
    if (animate && stack.children.length) {
      stack.classList.add('is-changing');
      setTimeout(apply, 480);
    } else apply();
  }

  function ensureHeroRotation() {
    if (state.heroTimer || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    state.heroTimer = window.setInterval(() => {
      if (state.view === 'home' && !document.hidden) renderHeroTickets();
    }, 10000);
  }

  function resetHeroRotation() {
    if (state.heroTimer) window.clearInterval(state.heroTimer);
    state.heroTimer = null;
    ensureHeroRotation();
  }

  function renderDateResults(items) {
    const section = $('#dateResultsSection');
    if (!state.date) {
      state.lastRenderedDate = null;
      if (!section.hidden) {
        section.classList.remove('is-visible');
        section.classList.add('is-leaving');
        window.setTimeout(() => {
          if (!state.date) {
            section.hidden = true;
            section.classList.remove('is-leaving');
            $('#dateResultsRail').innerHTML = '';
          }
        }, 420);
      } else section.hidden = true;
      return;
    }

    const selected = parseDate(`${state.date}T00:00:00`);
    const formatted = selected ? `${selected.getFullYear()} 年 ${selected.getMonth()+1} 月 ${selected.getDate()} 日` : state.date;
    $('#dateResultsTitle').textContent = `${formatted}有展出的展覽`;
    $('#dateResultsDescription').textContent = items.length ? `共找到 ${items.length.toLocaleString('zh-TW')} 檔，向右滑動查看更多。` : '目前沒有符合條件的展覽，可以改選附近日期。';
    $('#dateResultsRail').innerHTML = items.length
      ? selectFeatured(items, 14).map((event,index) => cardMarkup(event,{revealIndex:index})).join('')
      : emptyInline('這一天目前沒有符合條件的展覽');
    const params = new URLSearchParams({view:'all', date:state.date});
    if (state.status !== 'all') params.set('status', state.status);
    state.categories.forEach(category => params.append('category', category));
    $('#dateResultsMore').href = `?${params.toString()}`;

    section.hidden = false;
    section.classList.remove('is-leaving');
    requestAnimationFrame(() => requestAnimationFrame(() => section.classList.add('is-visible')));
    state.lastRenderedDate = state.date;
  }

  function renderHome() {
    const basePool = filterEvents(state.events, {includeDate:false});
    const ongoing = state.events.filter(isOngoing);
    const featured = selectFeatured(basePool.length ? basePool : ongoing, 9);
    const dateItems = state.date ? basePool.filter(event => eventOccursOn(event, state.date)) : [];
    const upcoming = state.events.filter(isUpcoming).sort((a,b) => (parseDate(a.startDate)?.getTime() || Infinity) - (parseDate(b.startDate)?.getTime() || Infinity)).slice(0, 4);
    const ending = state.events.filter(event => isEnding(event, 30)).sort((a,b) => (parseDate(a.endDate)?.getTime() || Infinity) - (parseDate(b.endDate)?.getTime() || Infinity)).slice(0, 4);

    $('#heroEventCount').textContent = state.events.length.toLocaleString('zh-TW');
    $('#heroVenueCount').textContent = new Set(state.events.map(event => event.venueGroup || event.locationName).filter(Boolean)).size.toLocaleString('zh-TW');
    if (!$('#heroTicketStack').children.length) renderHeroTickets({animate:false});
    ensureHeroRotation();

    renderCategoryStrip();
    renderDateResults(dateItems);
    $('#featuredRail').innerHTML = featured.length ? featured.map((event,index) => cardMarkup(event,{curated:index < 3})).join('') : emptyInline('目前沒有符合篩選的展覽');
    $('#upcomingList').innerHTML = upcoming.length ? upcoming.map(compactMarkup).join('') : emptyInline('目前沒有即將開展的活動');
    $('#endingList').innerHTML = ending.length ? ending.map(compactMarkup).join('') : emptyInline('目前沒有即將結束的活動');
    renderVenueGrid();
    renderHomeNearby();
    syncHomeFilters();
  }

  function renderCategoryStrip() {
    const counts = countBy(state.events, event => event.categories);
    const categories = Object.keys(counts).sort((a,b) => {
      const ai = CATEGORY_ORDER.indexOf(a), bi = CATEGORY_ORDER.indexOf(b);
      return (ai < 0 ? 99 : ai) - (bi < 0 ? 99 : bi);
    }).slice(0, 12);
    $('#categoryStrip').innerHTML = categories.map(category => `
      <a class="category-chip ${state.categories.has(category) ? 'active' : ''}" href="${categoryHref(category)}">
        <span class="category-icon">${CATEGORY_ICON[category] || '＋'}</span>
        <strong>${escapeHtml(category)}</strong><small>${counts[category]} 檔</small>
      </a>`).join('');
  }

  function renderVenueGrid() {
    const counts = countBy(state.events, event => event.venueGroup || event.locationName);
    const venues = Object.keys(counts).filter(venue => venue && !/資料整理中|地點待確認/.test(venue)).sort((a,b) => counts[b] - counts[a]).slice(0, 8);
    $('#venueGrid').innerHTML = venues.map((venue, index) => {
      const image = state.venueImages[venue] || '';
      return `<a class="venue-tile ${image ? 'has-image' : 'venue-placeholder'}" href="${venueHref(venue)}">
        ${image ? `<img src="${escapeHtml(image)}" alt="${escapeHtml(venue)}" loading="lazy" referrerpolicy="no-referrer" onerror="this.closest('.venue-tile').classList.add('venue-placeholder');this.remove()">` : `<span class="venue-placeholder-mark" aria-hidden="true">館</span>`}
        <div class="venue-tile-content"><small>VENUE ${String(index+1).padStart(2,'0')}</small><h3>${escapeHtml(venue)}</h3><p>${counts[venue]} 檔展覽</p></div>
      </a>`;
    }).join('') || emptyInline('目前沒有場館資料');
  }

  function renderHomeNearby() {
    let items = state.events.filter(hasCoordinates).slice(0, 3);
    if (state.userLocation) items = nearestEvents(state.events, 3);
    $('#nearbyHomeList').innerHTML = items.length ? items.map(event => nearbyMiniMarkup(event, event._distance ?? null)).join('') : emptyInline('目前沒有可定位的展覽');
    $('#homeLocationButton').textContent = state.userLocation ? '已依目前位置排序' : '使用目前位置';
  }

  function syncHomeFilters() {
    $('#datePicker').value = state.date || '';
    $$('#statusPills button').forEach(button => button.classList.toggle('active', button.dataset.status === state.status));
  }

  function renderListing() {
    const items = sortEvents(filterEvents());
    const titleParts = [];
    if (state.query) titleParts.push(`「${state.query}」`);
    if (state.categories.size) titleParts.push([...state.categories].join('＋'));
    if (state.region) titleParts.push(state.region);
    if (state.venue) titleParts.push(state.venue);
    $('#listingTitle').textContent = titleParts.length ? titleParts.join(' · ') : '探索全台展覽';
    $('#listingEyebrow').textContent = state.query ? 'SEARCH RESULTS' : 'EXPLORE EXHIBITIONS';
    $('#listingDescription').textContent = state.query ? '以下是符合搜尋關鍵字與篩選條件的結果。' : '先選分類與日期，再從縣市展開對應的展覽場所。';
    $('#listingCount').textContent = `找到 ${items.length.toLocaleString('zh-TW')} 檔展覽`;
    $('#listingGrid').innerHTML = items.map(cardMarkup).join('');
    $('#listingEmpty').hidden = items.length !== 0;
    $('#sortSelect').value = state.sort;
    renderSidebarOptions();
    renderListingCalendar();
    renderActiveFilters();
  }

  function renderSidebarOptions() {
    const statusOptions = [['all','全部展覽'],['ongoing','目前舉辦'],['upcoming','即將舉辦'],['ending','即將結束'],['free','免費展覽']];
    $('#listingStatusOptions').innerHTML = statusOptions.map(([value,label]) => `<button class="status-filter-button ${state.status === value ? 'active' : ''}" data-set-filter="status" data-value="${value}" type="button">${label}</button>`).join('');

    const categoryCounts = countBy(state.events, event => event.categories);
    const categories = Object.keys(categoryCounts).filter(category => CATEGORY_ORDER.includes(category)).sort((a,b) => CATEGORY_ORDER.indexOf(a) - CATEGORY_ORDER.indexOf(b));
    $('#listingCategoryOptions').innerHTML = categories.map(category => `<button class="listing-category-option ${state.categories.has(category) ? 'active' : ''}" data-toggle-category="${escapeHtml(category)}" type="button" aria-pressed="${state.categories.has(category)}"><span class="category-icon">${CATEGORY_ICON[category] || CATEGORY_ICON['其他']}</span><strong>${escapeHtml(category)}</strong><small>${categoryCounts[category].toLocaleString('zh-TW')} 檔</small></button>`).join('');

    const regionGroups = REGION_ORDER.map(region => {
      const regionEvents = state.events.filter(event => event.region === region);
      if (!regionEvents.length) return '';
      const venueCounts = countBy(regionEvents, event => event.venueGroup || event.locationName);
      const venues = Object.keys(venueCounts).filter(venue => venue && venue !== '地點待確認').sort((a,b) => venueCounts[b] - venueCounts[a]);
      const isOpen = state.region === region || (state.venue && venues.includes(state.venue));
      return `<details class="region-accordion ${state.region === region ? 'selected' : ''}" ${isOpen ? 'open' : ''}>
        <summary><span>${escapeHtml(region)}</span><small>${regionEvents.length.toLocaleString('zh-TW')} 檔</small><i>⌄</i></summary>
        <div class="region-venues">
          <button class="venue-filter-option ${state.region === region && !state.venue ? 'active' : ''}" type="button" data-region-filter="${escapeHtml(region)}" data-venue-filter=""><span>全部 ${escapeHtml(region)}</span><small>${regionEvents.length}</small></button>
          ${venues.map(venue => `<button class="venue-filter-option ${state.venue === venue ? 'active' : ''}" type="button" data-region-filter="${escapeHtml(region)}" data-venue-filter="${escapeHtml(venue)}"><span>${escapeHtml(venue)}</span><small>${venueCounts[venue]}</small></button>`).join('')}
        </div>
      </details>`;
    }).join('');
    $('#listingLocationAccordion').innerHTML = regionGroups || emptyInline('目前沒有地點資料');
  }

  function renderListingCalendar() {
    const month = state.calendarMonth || new Date(new Date().getFullYear(), new Date().getMonth(), 1);
    const year = month.getFullYear();
    const monthIndex = month.getMonth();
    $('#calendarMonthLabel').textContent = `${year} 年 ${monthIndex + 1} 月`;
    const firstWeekday = new Date(year, monthIndex, 1).getDay();
    const daysInMonth = new Date(year, monthIndex + 1, 0).getDate();
    const todayKey = localDateKey(new Date());
    const baseItems = filterEvents(state.events, {includeDate:false});
    const cells = [];
    for (let index = 0; index < firstWeekday; index += 1) cells.push('<span class="calendar-day empty" aria-hidden="true"></span>');
    for (let day = 1; day <= daysInMonth; day += 1) {
      const key = localDateKey(new Date(year, monthIndex, day));
      const count = baseItems.reduce((total, event) => total + (eventOccursOn(event, key) ? 1 : 0), 0);
      const classes = ['calendar-day'];
      if (key === state.date) classes.push('selected');
      if (key === todayKey) classes.push('today');
      if (count) classes.push('has-events');
      cells.push(`<button type="button" class="${classes.join(' ')}" data-calendar-date="${key}" aria-label="${year}年${monthIndex+1}月${day}日，${count}檔展覽"><span>${day}</span>${count ? `<small>${count > 99 ? '99+' : count}</small>` : ''}</button>`);
    }
    $('#listingCalendarGrid').innerHTML = cells.join('');
    if (state.date) {
      const selected = parseDate(`${state.date}T00:00:00`);
      const count = filterEvents().length;
      $('#calendarSelectionText').textContent = `${selected?.toLocaleDateString('zh-TW',{month:'long',day:'numeric',weekday:'short'}) || state.date} · ${count} 檔`;
    } else $('#calendarSelectionText').textContent = '尚未選擇日期';
  }

  function renderActiveFilters() {
    const parts = [];
    if (state.query) parts.push(`<span class="active-filter">${escapeHtml(`搜尋：${state.query}`)}<button type="button" data-clear-filter="q" aria-label="移除搜尋">×</button></span>`);
    state.categories.forEach(category => parts.push(`<span class="active-filter">${escapeHtml(category)}<button type="button" data-toggle-category="${escapeHtml(category)}" aria-label="移除${escapeHtml(category)}分類">×</button></span>`));
    if (state.region) parts.push(`<span class="active-filter">${escapeHtml(state.region)}<button type="button" data-clear-filter="region" aria-label="移除地區">×</button></span>`);
    if (state.venue) parts.push(`<span class="active-filter">${escapeHtml(state.venue)}<button type="button" data-clear-filter="venue" aria-label="移除場館">×</button></span>`);
    if (state.status !== 'all') {
      const label = {ongoing:'目前舉辦',upcoming:'即將舉辦',ending:'即將結束',free:'免費展覽'}[state.status] || state.status;
      parts.push(`<span class="active-filter">${escapeHtml(label)}<button type="button" data-clear-filter="status" aria-label="移除狀態">×</button></span>`);
    }
    if (state.date) parts.push(`<span class="active-filter">${escapeHtml(state.date)}<button type="button" data-clear-filter="date" aria-label="移除日期">×</button></span>`);
    $('#activeFilters').innerHTML = parts.join('');
  }

  function renderFavorites() {
    const favorites = getFavorites();
    const items = state.events.filter(event => favorites.includes(eventKey(event)));
    $('#favoritesCount').textContent = `共收藏 ${items.length} 檔展覽`;
    $('#favoritesGrid').innerHTML = items.map(cardMarkup).join('');
    $('#favoritesEmpty').hidden = items.length !== 0;
  }

  function renderDetail() {
    const key = state.params.get('event');
    const event = state.events.find(item => eventKey(item) === key || item.sourceUrl === key);
    if (!event) {
      $('#detailContent').innerHTML = `<div class="empty-state"><span>?</span><h3>找不到這個展覽</h3><p>活動可能已下架或網址已更新。</p><a class="primary-link" href="./">回到首頁</a></div>`;
      return;
    }
    document.title = `${event.title}｜台灣展覽誌`;
    const related = selectFeatured(state.events.filter(item => eventKey(item) !== eventKey(event) && (item.region === event.region || item.categories.some(category => event.categories.includes(category)))), 6);
    const externalUrl = event.sourceUrl || googleMapsUrl(event);
    $('#detailContent').innerHTML = `
      <div class="detail-breadcrumb"><a href="./">首頁</a> / <a href="${categoryHref(event.category)}">${escapeHtml(event.category)}</a> / ${escapeHtml(event.title)}</div>
      <div class="detail-grid">
        <div class="detail-poster">${imageMarkup(event, 'detail-poster-placeholder')}</div>
        <article class="detail-info">
          <div class="detail-category">${escapeHtml(event.categories.join(' · '))} / ${escapeHtml(event.region)}</div>
          <h1>${escapeHtml(event.title)}</h1>
          <div class="detail-meta">
            ${detailMeta('展期', dateRange(event))}${detailMeta('地點', event.venueDetail ? `${event.venueGroup || event.locationName}｜${event.venueDetail}` : (event.venueGroup || event.locationName))}${detailMeta('地址', event.address || event.region)}${detailMeta('票價', event.price)}${event.unit ? detailMeta('主辦單位', event.unit) : ''}${event.transitInfo ? detailMeta('交通', event.transitInfo) : ''}
          </div>
          <div class="detail-actions">
            <a class="primary" href="${escapeHtml(externalUrl)}" target="_blank" rel="noopener"><span>查看官方資訊</span><span aria-hidden="true">↗</span></a>
            <a href="${escapeHtml(googleMapsUrl(event))}" target="_blank" rel="noopener"><span>地圖導航</span></a>
            <button type="button" data-detail-favorite="${escapeHtml(eventKey(event))}">${isFavorite(event) ? '♥ 已收藏' : '♡ 加入收藏'}</button>
            <button type="button" data-share-event="${escapeHtml(eventKey(event))}">分享展覽</button>
          </div>
          <div class="detail-description"><h2>展覽介紹</h2><p>${escapeHtml(event.description || '目前沒有完整介紹，請前往官方活動頁面查看最新資訊。')}</p></div>
        </article>
      </div>
      ${related.length ? `<section class="detail-related"><p class="eyebrow">YOU MAY ALSO LIKE</p><h2>附近或相似的展覽</h2><div class="featured-rail">${related.map(cardMarkup).join('')}</div></section>` : ''}`;
  }

  function detailMeta(label, value) { return `<div class="detail-meta-row"><small>${label}</small><strong>${escapeHtml(value || '—')}</strong></div>`; }
  function summaryText(text) { return text.length > 180 ? `${text.slice(0, 180).trim()}…` : text; }

  function hasCoordinates(event) { return Number.isFinite(event.latitude) && Number.isFinite(event.longitude) && event.latitude !== 0 && event.longitude !== 0; }
  function haversine(lat1, lon1, lat2, lon2) {
    const R = 6371, dLat = (lat2-lat1)*Math.PI/180, dLon = (lon2-lon1)*Math.PI/180;
    const a = Math.sin(dLat/2)**2 + Math.cos(lat1*Math.PI/180)*Math.cos(lat2*Math.PI/180)*Math.sin(dLon/2)**2;
    return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
  }
  function nearestEvents(items, limit = 30) {
    if (!state.userLocation) return items.filter(hasCoordinates).slice(0, limit);
    return items.filter(hasCoordinates).map(event => ({...event,_distance:haversine(state.userLocation.lat,state.userLocation.lng,event.latitude,event.longitude)})).sort((a,b) => a._distance-b._distance).slice(0,limit);
  }

  function renderNearby() {
    const items = nearestEvents(filterEvents(), 50);
    $('#nearbyStatusText').textContent = state.userLocation ? '已依照你目前的位置，由近到遠排列。' : '允許定位後，依距離由近到遠顯示展覽。';
    $('#nearbyCount').textContent = `${items.length} 檔`;
    $('#nearbyResultList').innerHTML = items.map(event => resultMarkup(event, event._distance)).join('') || emptyInline('目前沒有提供座標的展覽');
    renderMap(items);
  }

  function renderMap(items) {
    if (!window.L) return;
    if (state.map) { state.map.remove(); state.map = null; }
    const center = state.userLocation ? [state.userLocation.lat, state.userLocation.lng] : [23.7, 121.0];
    state.map = L.map('nearbyMap', {scrollWheelZoom:false}).setView(center, state.userLocation ? 12 : 7);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {maxZoom:19, attribution:'&copy; OpenStreetMap contributors'}).addTo(state.map);
    const markers = [];
    if (state.userLocation) L.circleMarker(center, {radius:8, color:'#171713', fillColor:'#c56538', fillOpacity:1, weight:3}).addTo(state.map).bindPopup('你目前的位置');
    items.slice(0, 100).forEach(event => {
      if (!hasCoordinates(event)) return;
      const marker = L.marker([event.latitude,event.longitude]).addTo(state.map);
      marker.bindPopup(`<div class="map-popup"><h3>${escapeHtml(event.title)}</h3><p>${escapeHtml(event.venueGroup || event.locationName)}</p><p>${escapeHtml(dateRange(event))}</p><a href="${eventHref(event)}">查看展覽 →</a></div>`);
      markers.push(marker);
    });
    if (!state.userLocation && markers.length) {
      const group = L.featureGroup(markers);
      state.map.fitBounds(group.getBounds().pad(.08));
    }
    setTimeout(() => state.map?.invalidateSize(), 150);
  }

  function requestLocation() {
    if (!navigator.geolocation) { showToast('此瀏覽器不支援定位功能'); return; }
    showToast('正在取得目前位置…');
    navigator.geolocation.getCurrentPosition(position => {
      state.userLocation = {lat:position.coords.latitude,lng:position.coords.longitude};
      showToast('已依目前位置重新排序');
      renderHomeNearby();
      if (state.view === 'nearby') renderNearby();
    }, error => {
      const message = error.code === 1 ? '你尚未允許定位權限' : '暫時無法取得目前位置';
      showToast(message);
    }, {enableHighAccuracy:true,timeout:12000,maximumAge:300000});
  }

  function googleMapsUrl(event) {
    const query = hasCoordinates(event) ? `${event.latitude},${event.longitude}` : `${event.locationName} ${event.address}`;
    return `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(query)}`;
  }

  function renderCurrentView() {
    const views = {home:$('#homeView'),listing:$('#listingView'),nearby:$('#nearbyView'),detail:$('#detailView'),favorites:$('#favoritesView')};
    Object.entries(views).forEach(([name,element]) => element.hidden = name !== state.view);
    if (state.view === 'home') renderHome();
    if (state.view === 'listing') renderListing();
    if (state.view === 'nearby') renderNearby();
    if (state.view === 'detail') renderDetail();
    if (state.view === 'favorites') renderFavorites();
    $('#loadingView').hidden = true;
    updateFooter();
  }

  function updateFooter() {
    $('#footerRecordCount').textContent = `目前收錄 ${state.events.length.toLocaleString('zh-TW')} 檔活動`;
    const updated = parseDate(state.updatedAt);
    $('#footerUpdatedAt').textContent = updated ? `最後更新 ${updated.toLocaleString('zh-TW',{dateStyle:'medium',timeStyle:'short'})}` : '每日自動更新';
  }

  function updateUrl(filters = {}) {
    const params = new URLSearchParams(location.search);
    params.set('view','all');
    Object.entries(filters).forEach(([key,value]) => {
      if (key === 'category') {
        params.delete('category');
        const values = Array.isArray(value) ? value : value ? [value] : [];
        values.forEach(category => params.append('category', category));
        return;
      }
      if (value === null || value === '' || value === 'all') params.delete(key); else params.set(key,value);
    });
    params.delete('event');
    location.href = `?${params.toString()}`;
  }

  function toggleCategoryFilter(category) {
    const next = new Set(state.categories);
    if (next.has(category)) next.delete(category); else next.add(category);
    updateUrl({category:[...next]});
  }

  function emptyInline(text) { return `<div class="empty-state"><span>✦</span><p>${escapeHtml(text)}</p></div>`; }
  let toastTimer;
  function showToast(message) {
    const toast = $('#toast');
    toast.textContent = message;
    toast.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toast.classList.remove('show'), 2200);
  }

  function bindEvents() {
    window.addEventListener('scroll', () => $('#siteHeader').classList.toggle('scrolled', scrollY > 12), {passive:true});
    $('#mobileMenuButton').addEventListener('click', () => {
      const open = $('#mobileMenuButton').getAttribute('aria-expanded') === 'true';
      $('#mobileMenuButton').setAttribute('aria-expanded', String(!open));
      $('#mobileMenu').hidden = open;
      document.body.classList.toggle('menu-open', !open);
    });

    const submitSearch = input => {
      const query = input.value.trim();
      if (query) location.href = `?view=all&q=${encodeURIComponent(query)}`;
    };
    $('#navSearchForm').addEventListener('submit', event => {event.preventDefault();submitSearch($('#navSearchInput'));});
    $('#mobileSearchForm').addEventListener('submit', event => {event.preventDefault();submitSearch($('#mobileSearchInput'));});
    $('#heroSearchForm').addEventListener('submit', event => {event.preventDefault();submitSearch($('#heroSearchInput'));});
    $('#heroShuffleButton').addEventListener('click', () => {
      const button = $('#heroShuffleButton');
      if (button.disabled) return;
      button.disabled = true;
      state.heroHasShuffled = true;
      $('#heroShuffleText').textContent = '再抽一組觀展靈感';
      renderHeroTickets({animate:true, manual:true});
      resetHeroRotation();
      setTimeout(() => { button.disabled = false; }, 1900);
    });

    $('#datePicker').addEventListener('change', event => {state.date = event.target.value || null; renderHome();});
    $('#dateResultsClear').addEventListener('click', () => {state.date = null; renderHome(); $('#discover').scrollIntoView({behavior:'smooth',block:'start'});});
    $('#clearFiltersButton').addEventListener('click', () => {state.status='all';state.date=null;state.categories.clear();renderHome();});
    $('#statusPills').addEventListener('click', event => {const button=event.target.closest('[data-status]');if(!button)return;state.status=button.dataset.status;renderHome();});

    document.addEventListener('click', event => {
      const scrollButton = event.target.closest('[data-scroll-target]');
      if (scrollButton) {
        const target = document.getElementById(scrollButton.dataset.scrollTarget);
        target?.scrollBy({left:Number(scrollButton.dataset.dir)*target.clientWidth*.85,behavior:'smooth'});
      }
      const favoriteButton = event.target.closest('[data-favorite],[data-detail-favorite]');
      if (favoriteButton) {
        event.preventDefault(); event.stopPropagation();
        const key = favoriteButton.dataset.favorite || favoriteButton.dataset.detailFavorite;
        const item = state.events.find(eventItem => eventKey(eventItem) === key);
        if (item) toggleFavorite(item);
      }
      const shareButton = event.target.closest('[data-share-event]');
      if (shareButton) {
        const item = state.events.find(eventItem => eventKey(eventItem) === shareButton.dataset.shareEvent);
        if (item) shareEvent(item);
      }
      const calendarButton = event.target.closest('[data-calendar-date]');
      if (calendarButton) updateUrl({date:calendarButton.dataset.calendarDate});

      const locationButton = event.target.closest('[data-region-filter]');
      if (locationButton) updateUrl({region:locationButton.dataset.regionFilter || null, venue:locationButton.dataset.venueFilter || null});

      const categoryButton = event.target.closest('[data-toggle-category]');
      if (categoryButton) {
        event.preventDefault();
        toggleCategoryFilter(categoryButton.dataset.toggleCategory);
        return;
      }
      const filterButton = event.target.closest('[data-set-filter]');
      if (filterButton) updateUrl({[filterButton.dataset.setFilter]:filterButton.dataset.value});
      const clearButton = event.target.closest('[data-clear-filter]');
      if (clearButton) {
        const key = clearButton.dataset.clearFilter;
        if (key === 'region') updateUrl({region:null,venue:null});
        else if (key === 'category') updateUrl({category:null});
        else updateUrl({[key]:null});
      }
    });

    $('#sidebarClearDate').addEventListener('click', () => updateUrl({date:null}));
    $('#calendarPrevButton').addEventListener('click', () => {state.calendarMonth = new Date(state.calendarMonth.getFullYear(),state.calendarMonth.getMonth()-1,1);renderListingCalendar();});
    $('#calendarNextButton').addEventListener('click', () => {state.calendarMonth = new Date(state.calendarMonth.getFullYear(),state.calendarMonth.getMonth()+1,1);renderListingCalendar();});
    $('#calendarTodayButton').addEventListener('click', () => updateUrl({date:localDateKey(new Date())}));
    $('#sortSelect').addEventListener('change', event => {state.sort=event.target.value;renderListing();});
    $('#filterDrawerButton').addEventListener('click', () => $('#filterSidebar').classList.add('open'));
    $('#filterCloseButton').addEventListener('click', () => $('#filterSidebar').classList.remove('open'));
    $('#homeLocationButton').addEventListener('click', requestLocation);
    $('#nearbyLocationButton').addEventListener('click', requestLocation);
  }

  async function shareEvent(event) {
    const data = {title:event.title,text:`${event.title}｜${dateRange(event)}｜${event.venueGroup || event.locationName}`,url:new URL(eventHref(event),location.href).href};
    try {
      if (navigator.share) await navigator.share(data);
      else { await navigator.clipboard.writeText(data.url); showToast('連結已複製'); }
    } catch (error) { if (error.name !== 'AbortError') showToast('暫時無法分享'); }
  }

  async function fetchEventPayload() {
    const sources = [
      {url:'data/exhibitions.json', local:true},
      {url:'https://cloud.culture.tw/frontsite/trans/SearchShowAction.do?method=doFindTypeJ&category=all', local:false},
      {url:'https://cloud.culture.tw/frontsite/trans/SearchShowAction.do?method=doFindTypeJOpenApi&category=all', local:false},
    ];
    const failures = [];
    for (const source of sources) {
      try {
        const response = await fetch(source.url, {cache:'no-store'});
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const payload = await response.json();
        const rawEvents = Array.isArray(payload) ? payload : payload.events || payload.data || payload.result || [];
        if (!Array.isArray(rawEvents) || !rawEvents.length) throw new Error('資料為空');
        return {payload, rawEvents, local:source.local};
      } catch (error) {
        failures.push(`${source.url}: ${error.message}`);
        console.warn('[Exhibition Hub] data source failed', source.url, error);
      }
    }
    throw new Error(failures.join(' | '));
  }

  async function loadData() {
    readParams();
    bindEvents();
    try {
      const {payload, rawEvents, local} = await fetchEventPayload();
      state.updatedAt = payload.updatedAt || payload.updated_at || (!local ? new Date().toISOString() : null);
      state.venueImages = payload.venueImages || {};
      state.events = rawEvents.map(normalizeEvent).filter(event => event.title && eventKey(event));
      if (!state.events.length) throw new Error('沒有可顯示的展覽資料');
      renderCurrentView();
    } catch (error) {
      console.error(error);
      $('#loadingView').hidden = true;
      $('#errorView').hidden = false;
    }
  }

  loadData();
})();
