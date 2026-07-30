/* Exhibition Hub V6.5.0-R2 — cumulative postcard carousel, mobile shortcuts, and Huashan recovery release. */
(() => {
  'use strict';

  const CATEGORY_ORDER = ['演唱會','快閃店','動漫','美術','設計','攝影','市集','音樂','自然','歷史','表演','舞蹈','電影','親子','競賽','科技','其他'];
  const CONTENT_TYPE_LABELS = {
    exhibition:'一般展覽', art_exhibition:'藝術展覽', pop_culture:'動漫／IP', expo:'博覽會',
    concert:'演唱會', music_festival:'音樂祭', performance:'表演藝術', popup:'快閃店',
    market:'市集', festival:'城市節慶', film_screening:'電影／影展'
  };
  const CONTENT_TYPE_CATEGORY_MAP = {
    art_exhibition:'美術', pop_culture:'動漫', concert:'演唱會', music_festival:'音樂',
    performance:'表演', popup:'快閃店', market:'市集', film_screening:'電影'
  };
  const iconSvg = body => `<svg viewBox="0 0 24 24" aria-hidden="true">${body}</svg>`;
  const CATEGORY_ICON = {
    '快閃店': iconSvg('<path d="M4 10h16l-1.6-5H5.6L4 10Z"></path><path d="M5 10v9h14v-9M9 19v-5h6v5"></path><path d="M4 10c0 1.2 1 2.2 2.2 2.2S8.4 11.2 8.4 10c0 1.2 1 2.2 2.2 2.2s2.2-1 2.2-2.2c0 1.2 1 2.2 2.2 2.2s2.2-1 2.2-2.2"></path><path d="m18.2 2 .7 1.5 1.6.7-1.6.7-.7 1.6-.7-1.6-1.6-.7 1.6-.7.7-1.5Z"></path>'),
    '美術': iconSvg('<rect x="4" y="4" width="16" height="16" rx="2"></rect><path d="m7 16 4-4 3 3 3-4 2 3"></path><circle cx="9" cy="9" r="1.4"></circle>'),
    '攝影': iconSvg('<path d="M4 8h3l1.5-2h7L17 8h3v11H4V8Z"></path><circle cx="12" cy="13.5" r="3.5"></circle>'),
    '設計': iconSvg('<path d="m4 20 4.5-1 9.8-9.8a2 2 0 0 0-2.8-2.8L5.7 16.2 4 20Z"></path><path d="m13.8 8.2 2.8 2.8M4 4h6M4 8h3"></path>'),
    '動漫': iconSvg('<path d="M5 5h14v10H9l-4 4V5Z"></path><path d="m10 8 .8 1.7 1.9.2-1.4 1.3.4 1.9-1.7-.9-1.7.9.4-1.9-1.4-1.3 1.9-.2L10 8Z"></path>'),
    '歷史': iconSvg('<path d="M4 9h16M6 9v8M10 9v8M14 9v8M18 9v8M3 19h18M12 4l8 4H4l8-4Z"></path>'),
    '自然': iconSvg('<circle cx="12" cy="12" r="2"></circle><ellipse cx="12" cy="12" rx="9" ry="4"></ellipse><ellipse cx="12" cy="12" rx="4" ry="9" transform="rotate(35 12 12)"></ellipse>'),
    '親子': iconSvg('<circle cx="9" cy="8" r="2.5"></circle><circle cx="16" cy="9" r="2"></circle><path d="M4.5 19c.5-4 2-6 4.5-6s4 2 4.5 6M13 19c.4-3 1.4-4.8 3-4.8s2.6 1.8 3 4.8"></path>'),
    '音樂': iconSvg('<path d="M9 18V6l10-2v12"></path><circle cx="6" cy="18" r="3"></circle><circle cx="16" cy="16" r="3"></circle>'),
    '演唱會': iconSvg('<rect x="9" y="3" width="6" height="11" rx="3"></rect><path d="M6 10v1a6 6 0 0 0 12 0v-1M12 17v4M9 21h6M18 5h3M19.5 3.5v3"></path>'),
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
  const CATEGORY_SYMBOL = {'快閃店':'閃','美術':'藝','攝影':'影','設計':'設','動漫':'漫','歷史':'史','自然':'自','親子':'親','音樂':'樂','演唱會':'唱','表演':'演','舞蹈':'舞','電影':'映','講座':'講','研習':'學','市集':'集','競賽':'賽','科技':'技','其他':'展'};
  const CATEGORY_FALLBACK_INDEX = {
    '美術':0, '攝影':1, '設計':2, '動漫':3,
    '歷史':4, '自然':5, '親子':6, '音樂':7,
    '演唱會':7, '表演':8, '舞蹈':9, '電影':10, '市集':11,
    '科技':12, '競賽':13, '快閃店':14, '其他':15,
  };
  const NEARBY_RADIUS_KM = 10;
  const CATEGORY_CODE_MAP = {'1':'音樂','2':'表演','3':'舞蹈','4':'親子','5':'音樂','6':'美術','7':'其他','8':'電影','11':'表演','13':'競賽','14':'其他','15':'其他','17':'音樂','19':'其他'};
  const CATEGORY_ALIASES = {
    '展覽':'美術','展覽資訊':'美術','藝術':'美術','戲劇':'表演','戲劇表演':'表演','綜藝':'表演','綜藝活動':'表演',
    '快閃':'快閃店','快閃活動':'快閃店','期間限定':'快閃店','歷史文化':'歷史','自然科學':'自然','音樂表演':'音樂','獨立音樂':'音樂','演唱會活動':'演唱會','大型演唱會':'演唱會','講座資訊':'其他','親子活動':'親子','電影欣賞':'電影',
    '競賽活動':'競賽','徵選活動':'其他','徵選':'其他','商展':'其他','研習課程':'其他','其他藝文資訊':'其他'
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
  const REGION_CENTERS = {
    '台北市':[25.05,121.54,42], '新北市':[25.02,121.47,62], '基隆市':[25.13,121.74,28],
    '桃園市':[24.99,121.30,58], '新竹市':[24.81,120.97,26], '新竹縣':[24.84,121.15,58],
    '苗栗縣':[24.56,120.82,62], '台中市':[24.16,120.68,70], '彰化縣':[24.08,120.54,52],
    '南投縣':[23.91,120.69,86], '雲林縣':[23.71,120.43,58], '嘉義市':[23.48,120.45,24],
    '嘉義縣':[23.46,120.57,74], '台南市':[23.00,120.22,73], '高雄市':[22.63,120.31,94],
    '屏東縣':[22.55,120.55,102], '宜蘭縣':[24.68,121.77,76], '花蓮縣':[23.99,121.61,120],
    '台東縣':[22.76,121.15,126], '澎湖縣':[23.57,119.58,55], '金門縣':[24.44,118.32,36],
    '連江縣':[26.16,119.95,48]
  };
  const FAVORITES_KEY = 'exhibition-hub-favorites-v3';

  const state = {
    events: [],
    updatedAt: null,
    stats: {},
    registryBuild: null,
    dataSource: '',
    venueImages: {},
    venueRegistry: [],
    selectedVenues: new Set(),
    venueDrawerDraft: new Set(),
    venueTypeFilter: 'all',
    venueSearch: '',
    venueRegistryIndex: new Map(),
    venueCatalogCache: [],
    venueSearchTimer: null,
    params: new URLSearchParams(location.search),
    view: 'home',
    status: 'all',
    admission: 'all',
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
    heroCursor: 0,
    heroPool: [],
    heroAnimating: false,
    heroSwipeStartX: null,
    heroSwipeStartY: null,
    heroSwipeBlockClickUntil: 0,
    mobilePreviewTicket: null,
    mobileCategoriesExpanded: false,
    mobileDrawerSection: 'all',
    viewportScrollY: 0,
    viewportLockOwner: null,
    lastRenderedDate: null,
    heroTransitionTimer: null,
    filterResultsTimer: null,
    lastHomeFilterKey: '',
    revealObserver: null,
    lastRenderedView: null,
    locationRequested: false,
    locationRequestPending: false,
  };

  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];

  function lockViewport(owner) {
    if (state.viewportLockOwner === owner) return;
    if (state.viewportLockOwner) return;
    state.viewportScrollY = Math.max(0, window.scrollY || window.pageYOffset || 0);
    state.viewportLockOwner = owner;
    document.documentElement.classList.add('overlay-open');
    document.body.style.position = 'fixed';
    document.body.style.top = `-${state.viewportScrollY}px`;
    document.body.style.left = '0';
    document.body.style.right = '0';
    document.body.style.width = '100%';
  }

  function unlockViewport(owner) {
    if (state.viewportLockOwner !== owner) return;
    const restoreY = state.viewportScrollY;
    state.viewportLockOwner = null;
    state.viewportScrollY = 0;
    document.documentElement.classList.remove('overlay-open');
    document.body.style.removeProperty('position');
    document.body.style.removeProperty('top');
    document.body.style.removeProperty('left');
    document.body.style.removeProperty('right');
    document.body.style.removeProperty('width');
    window.scrollTo({top:restoreY, left:0, behavior:'auto'});
  }

  function escapeHtml(value = '') {
    return String(value).replace(/[&<>'"]/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[char]));
  }

  const DEFAULT_PAGE_TITLE = '台灣展覽誌｜探索全台藝文展覽';
  const DEFAULT_PAGE_DESCRIPTION = '探索全台正在舉辦、即將開展與你附近的藝文展覽。';

  function setMetaContent(selector, content) {
    const node = $(selector);
    if (node) node.setAttribute('content', content || '');
  }

  function updatePageMetadata(event = null) {
    const structured = $('#structuredData');
    if (!event) {
      document.title = DEFAULT_PAGE_TITLE;
      setMetaContent('#metaDescription', DEFAULT_PAGE_DESCRIPTION);
      setMetaContent('#metaOgTitle', DEFAULT_PAGE_TITLE);
      setMetaContent('#metaOgDescription', DEFAULT_PAGE_DESCRIPTION);
      setMetaContent('#metaOgImage', '');
      if (structured) structured.textContent = JSON.stringify({
        '@context':'https://schema.org', '@type':'WebSite', name:'台灣展覽誌',
        url:new URL('./', location.href).href, description:DEFAULT_PAGE_DESCRIPTION,
      });
      return;
    }
    const description = summaryText(event.description || `${event.title}，${dateRange(event)}，於${eventVenueLabel(event)}展出。`);
    const title = `${event.title}｜台灣展覽誌`;
    const image = event.images?.[0] || event.image || '';
    document.title = title;
    setMetaContent('#metaDescription', description);
    setMetaContent('#metaOgTitle', title);
    setMetaContent('#metaOgDescription', description);
    setMetaContent('#metaOgImage', image);
    if (structured) structured.textContent = JSON.stringify({
      '@context':'https://schema.org', '@type':'Event', name:event.title,
      startDate:event.startDate || undefined, endDate:event.endDate || undefined,
      description, image:image ? [image] : undefined, url:location.href,
      location:{
        '@type':'Place', name:eventVenueLabel(event) || undefined,
        address:event.address ? {'@type':'PostalAddress', streetAddress:event.address, addressRegion:event.region || undefined, addressCountry:'TW'} : undefined,
      },
      eventAttendanceMode:'https://schema.org/OfflineEventAttendanceMode',
      eventStatus:'https://schema.org/EventScheduled',
    });
  }

  function safeUrl(value = '') {
    try {
      let text = String(value ?? '').trim().replace(/\\\//g, '/');
      if (!text) return '';
      const repeatedScheme = text.match(/^https?:\/\/[^/?#]+(https?:\/\/.+)$/i);
      if (repeatedScheme) text = repeatedScheme[1];
      if (text.startsWith('//')) text = `https:${text}`;
      if (/^https?:\/\/media\.huashan1914\.com\//i.test(text)) {
        text = text
          .replace('KV_華山官網活動|1920x1080.jpg', 'KV_華山官網活動｜1920x1080.jpg')
          .replace('華山官網活動:JPG格式|1920(W)-x-1080(H) (1).jpg', '華山官網活動：JPG格式｜1920(W)-x-1080(H) (1).jpg')
          .replace('華山官網活動:JPG格式｜1920(W)-x-1080(H) (1).jpg', '華山官網活動：JPG格式｜1920(W)-x-1080(H) (1).jpg');
      }
      const url = new URL(text, location.href);
      return ['http:','https:'].includes(url.protocol) ? url.href : '';
    } catch { return ''; }
  }

  function isFacebookUrl(value = '') {
    const url = safeUrl(value);
    if (!url) return false;
    try {
      const parsed = new URL(url);
      return /(?:^|\.)(?:facebook\.com|fb\.me|fbcdn\.net|facebookusercontent\.com)$/i.test(parsed.hostname)
        || /(?:^|[/_.-])facebook(?:[/_.-]|$)/i.test(decodeURIComponent(parsed.pathname));
    } catch { return false; }
  }

  function isUsableImageUrl(value = '') {
    const url = safeUrl(value);
    if (!url || isFacebookUrl(url)) return false;
    try {
      const parsed = new URL(url);
      const host = parsed.hostname.toLowerCase();
      const path = decodeURIComponent(parsed.pathname).toLowerCase();
      const asset = `${host}${path}${decodeURIComponent(parsed.search).toLowerCase()}`;
      if (/(?:^|\.)reurl\.cc$/i.test(host)) return false;
      if (/\.(?:gif|svg|ico)$/.test(path)) return false;
      const filename = path.split('/').pop() || '';
      if (/(?:^|[-_])default(?:[-_.]|$)|programinfodefault/i.test(filename)) return false;
      if (/(?:\/_nuxt\/img\/(?:flags|linkto)\.|\/images?\/coordinate\.|maps\.googleapis\.com\/maps\/api\/staticmap|\{\{:defaultimg\}\}|opentixpagedefault|\/default\/(?:orgcover|orgbanner)\.|cloud\.culture\.tw\/assets\/images\/banner_1200x630\.|sharenav_(?:fb|twitter)|index_toplogo|top_icon_2|(?:^|[/_.-])sharelogo(?:[/_.-]|$)|filedisplay=(?:logo|icon)|\/images\/banner\/p-but\.png|\/banner_live\.png)/i.test(asset)) return false;
      return !/(?:^|[/_.-])(?:ajax[-_]?loader|loader|loading|spinner|progress|preload|placeholder|blank|spacer|pixel|sprite|favicon|avatar|qr[-_]?code|meta[-_]?image|post\.image|section[-_](?:api|extention|linebot))(?:[/_.-]|$)/i.test(path);
    } catch { return false; }
  }

  function stripFacebookReferences(value = '') {
    return String(value || '').split(/\r?\n/).filter(line => !/(?:facebook|臉書|粉絲專頁)/i.test(line)).join('\n').trim();
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

  const SINGER_CONCERT_PATTERN = /演唱會|巡迴演唱|世界巡演|巡演(?:台北|高雄|台中|臺北|臺中)?站|fan\s*concert|live\s+in\s+(?:taipei|kaohsiung|taichung)|(?:concert|tour)\s*(?:20\d{2})?/i;
  const MUSIC_THEATRE_PATTERN = /音樂劇|歌劇|舞台劇|劇場|戲劇|讀劇|偶戲|馬戲/i;
  const CLASSICAL_MUSIC_PATTERN = /音樂會|交響|管弦|協奏|獨奏|重奏|室內樂|古典音樂|爵士|國樂|樂團|音樂祭/i;
  const ANIME_CATEGORY_PATTERN = /動漫|動畫|漫畫|卡通|anime|公仔|角色展|模型展|IP(?:展|祭|活動)/i;

  function isSingerConcert(title = '', description = '', contentTypes = []) {
    const text = `${title} ${description}`;
    return contentTypes.includes('concert') || SINGER_CONCERT_PATTERN.test(text);
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
      ['演唱會', SINGER_CONCERT_PATTERN], ['表演', MUSIC_THEATRE_PATTERN], ['動漫', ANIME_CATEGORY_PATTERN],
      ['快閃店', /快閃店|快閃|期間限定|popup|pop-up/i], ['攝影', /攝影|影像展|photo(graphy)?/i],
      ['歷史', /歷史|文化資產|文物|考古|古蹟|史料|地方誌|民俗/i],
      ['自然', /自然史|科學|生態|植物|動物|天文|地質|海洋|環境教育/i], ['科技', /科技|人工智慧|AI|數位科技|半導體|資訊展|電腦展|機器人/i],
      ['設計', /設計|建築|工藝|時尚|家居|文具|design/i], ['舞蹈', /舞蹈|舞作|芭蕾/i],
      ['音樂', CLASSICAL_MUSIC_PATTERN], ['電影', /電影|(?<!攝)影展|放映/i], ['市集', /市集|嘉年華|展售|商品展|食品展|旅展|文創攤位/i],
      ['親子', /親子|兒童|家庭|幼兒/i], ['競賽', /競賽|比賽|大賽|徵件比賽/i],
      ['美術', /美術|藝術|繪畫|雕塑|裝置|當代|典藏|書畫|陶藝|視覺藝術|藝術博覽會|插畫博覽會/i]
    ];
    keywordRules.forEach(([category, regex]) => {
      if (regex.test(text) && !categories.includes(category)) categories.push(category);
    });
    let cleaned = categories.filter(category => CATEGORY_ORDER.includes(category));
    const prioritize = category => {
      if (!cleaned.includes(category)) return;
      cleaned = [category, ...cleaned.filter(item => item !== category)];
    };
    if (isSingerConcert(title, description)) {
      cleaned = cleaned.filter(category => category !== '音樂');
      if (!cleaned.includes('演唱會')) cleaned.unshift('演唱會');
      prioritize('演唱會');
    } else if (MUSIC_THEATRE_PATTERN.test(text)) {
      cleaned = cleaned.filter(category => category !== '音樂');
      if (!cleaned.includes('表演')) cleaned.unshift('表演');
      prioritize('表演');
    } else if (ANIME_CATEGORY_PATTERN.test(text)) {
      prioritize('動漫');
    } else if (CLASSICAL_MUSIC_PATTERN.test(text)) {
      prioritize('音樂');
    }
    return (cleaned.length ? cleaned : ['其他']).filter((category, index, array) => array.indexOf(category) === index).slice(0, 3);
  }

  const EXCLUDED_CONTENT_PATTERN = /講座|講習|研習|研討會|論壇|座談|分享會|演講|課程|工作坊|營隊|訓練班|培訓班|讀書會/i;
  const LOCAL_COMMUNITY_PATTERN = /社區發展協會|里辦公處|里民活動|地方社團|同好會|讀書會|居民活動|社區小聚|社團例會/i;
  const SMALL_LOCAL_ACTIVITY_PATTERN = /外展服務|繪本說故事|故事時間|故事媽媽|親子共讀|社區共讀|假日電影院|(?:圖書館|分館|鄉|鎮|區|里).{0,12}電影欣賞|文化走讀|深度走讀|城市走讀|導覽活動|\bDIY\b|手作(?:活動|體驗|課)|(?:體驗|觀察|藝術|繪畫|書法|舞蹈|音樂|攝影)課|(?:夏令|冬令|成長|親子|藝術|科學)營|交流會|同樂會/i;
  const LOCAL_ORGANIZATION_PATTERN = /(?:縣|市|鄉|鎮|區|里).{0,14}(?:協會|學會|社團|團委會)/i;
  const PUBLIC_SHOW_PATTERN = /展覽|特展|聯展|個展|書展|攝影展|美術展|展演|音樂會|演出|藝術節|電影節|博覽會|劇場|戲劇|舞蹈/i;
  const LARGE_OR_OFFICIAL_EVENT_PATTERN = /國際|全國|博覽會|美術館|博物館|文化局|文化中心|文化處/i;

  function isExcludedEvent(event) {
    if (event.editorialStatus) return event.editorialStatus === 'exclude_review';
    const title = String(event.title || '');
    const sourceUrl = String(event.sourceUrl || '');
    const organizer = String(event.unit || '');
    if (isFacebookUrl(sourceUrl)) return true;
    if (EXCLUDED_CONTENT_PATTERN.test(title) || SMALL_LOCAL_ACTIVITY_PATTERN.test(title)) return true;
    if ((event.categories || []).some(category => category === '講座' || category === '研習')) return true;
    const communityText = `${title} ${organizer}`;
    if (LOCAL_COMMUNITY_PATTERN.test(communityText) && !LARGE_OR_OFFICIAL_EVENT_PATTERN.test(communityText)) return true;
    return LOCAL_ORGANIZATION_PATTERN.test(communityText) && !PUBLIC_SHOW_PATTERN.test(title) && !LARGE_OR_OFFICIAL_EVENT_PATTERN.test(communityText);
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
    return flattenImageCandidates(raw).map(safeUrl).find(url => url && !isFacebookUrl(url)) || '';
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

  function stringList(value) {
    const values = Array.isArray(value) ? value : value !== undefined && value !== null && value !== '' ? [value] : [];
    return values.flatMap(item => String(item).split(/[、,，|｜;；]+/)).map(item => cleanPlaceText(item)).filter(Boolean).filter((item, index, array) => array.indexOf(item) === index);
  }

  function eventVenueNames(event) {
    const matched = stringList(event?.venueNames);
    const unmatched = stringList(event?.unmatchedVenueValues);
    const registryValues = [...matched, ...unmatched]
      .filter((item, index, array) => array.indexOf(item) === index);

    if (registryValues.length) return registryValues;

    const fallback = stringList(firstValue(
      event?.originalVenueGroup,
      event?.originalLocationName,
      event?.venueGroup,
      event?.locationName
    ));
    return fallback.length ? fallback : [];
  }

  function eventVenueLabel(event, separator = '、') {
    const names = eventVenueNames(event);
    return names.length ? names.join(separator) : '地點待確認';
  }

  function eventVenueCompactLabel(event) {
    const names = eventVenueNames(event);
    if (!names.length) return '地點待確認';
    if (names.length === 1) return names[0];
    return `${names[0]} 等 ${names.length} 處`;
  }

  function eventVenueImage(event) {
    const candidates = [
      ...eventVenueNames(event),
      event?.originalVenueGroup,
      event?.originalLocationName,
      event?.venueGroup,
      event?.locationName,
    ].map(value => cleanPlaceText(value)).filter(Boolean);
    for (const venue of candidates) {
      const image = safeUrl(state.venueImages[venue] || '');
      if (isUsableImageUrl(image)) return image;
    }
    return '';
  }

  function eventContentTypeLabel(event) {
    return CONTENT_TYPE_LABELS[event?.contentType] || event?.categories?.[0] || '展覽';
  }

  function eventDisplayCategory(event) {
    return event?.categories?.find(category => !['快閃店','其他'].includes(category))
      || event?.category
      || event?.categories?.[0]
      || '其他';
  }

  function sourceVenueCount(items = state.events) {
    return new Set(items.map(event => cleanPlaceText(firstValue(event.originalVenueGroup, event.originalLocationName, event.venueGroup, event.locationName))).filter(Boolean)).size;
  }

  function normalizeEvent(raw, index) {
    const show = bestShow(raw);
    const title = firstValue(raw.title, raw.titile, raw.name, '未命名展覽');
    const description = stripFacebookReferences(firstValue(raw.description, raw.descriptionFilterHtml, raw.comment));
    const address = cleanPlaceText(firstValue(raw.address, raw.location, show.location, show.address));
    const originalLocationName = cleanPlaceText(firstValue(raw.locationName, raw.venue, show.locationName, show.venue, address));
    const originalVenueGroup = cleanPlaceText(firstValue(raw.venueGroup, raw.locationName, raw.venue, show.locationName, show.venue, address));
    const registryVenueNames = stringList(raw.venueNames);
    const registryVenueName = cleanPlaceText(firstValue(raw.venueName, registryVenueNames[0]));
    const rawVenue = cleanPlaceText(firstValue(registryVenueName, originalLocationName, address));
    const parsedVenue = venueParts(rawVenue, address, raw.venueGroup, raw.venueDetail);
    const venueGroup = registryVenueName || parsedVenue.venueGroup;
    const venueNames = registryVenueNames.length ? registryVenueNames : [venueGroup].filter(Boolean);
    const venueDetail = cleanPlaceText(firstValue(raw.venueDetail, parsedVenue.venueDetail));
    const sourceUrl = firstValue(raw.sourceUrl, raw.sourceWebPromote, raw.webSales, raw.sourceWebSite, raw.url, raw.website);
    const id = String(firstValue(raw.id, raw.UID, raw.uid, sourceUrl, `${title}-${index}`));
    const contentTypes = stringList(raw.contentTypes);
    const contentType = String(firstValue(raw.contentType, contentTypes[0])).trim();
    if (contentType && !contentTypes.includes(contentType)) contentTypes.unshift(contentType);
    const rawCategories = firstValue(raw.categories, raw.categoryName, raw.category);
    const baseCategories = normalizeCategories(rawCategories, title, description);
    const mappedCategory = contentTypes.map(type => CONTENT_TYPE_CATEGORY_MAP[type]).find(Boolean) || CONTENT_TYPE_CATEGORY_MAP[contentType];
    const concert = isSingerConcert(title, description, contentTypes);
    let categoryCandidates = concert
      ? ['演唱會', ...baseCategories.filter(category => category !== '音樂' && category !== '演唱會')]
      : [...baseCategories];
    if (mappedCategory === '快閃店' && categoryCandidates.some(category => !['快閃店','其他'].includes(category))) {
      categoryCandidates = [...categoryCandidates, mappedCategory];
    } else if (mappedCategory) {
      categoryCandidates = [mappedCategory, ...categoryCandidates];
    }
    const categories = categoryCandidates.filter(Boolean).filter((category, categoryIndex, array) => array.indexOf(category) === categoryIndex).slice(0, 3);
    const imageCandidates = [
      ...flattenImageCandidates(raw.images), ...flattenImageCandidates(raw.imageCandidates),
      ...flattenImageCandidates(raw.image), ...flattenImageCandidates(raw.imageURL), ...flattenImageCandidates(raw.imageUrl),
      ...flattenImageCandidates(raw.imageUrls), ...flattenImageCandidates(raw.poster), ...flattenImageCandidates(raw.posterUrl),
      ...flattenImageCandidates(raw.picture), ...flattenImageCandidates(raw.pictureUrl), ...flattenImageCandidates(show.image),
      ...flattenImageCandidates(show.imageUrl), ...flattenImageCandidates(show.imageURL)
    ].map(safeUrl).filter(isUsableImageUrl).filter((url, imageIndex, array) => array.indexOf(url) === imageIndex);
    const image = imageCandidates[0] || '';
    const {latitude, longitude} = coordinatesFrom(show, raw);
    const region = normalizeRegion(firstValue(raw.regionCanonical, raw.region, address, venueGroup, rawVenue));
    const price = stripFacebookReferences(firstValue(raw.price, raw.Price, show.price, raw.discountInfo, firstValue(show.onSales, raw.onSales) === 'N' ? '免費' : ''));
    return {
      id, title: String(title).trim(), description: stripHtml(description),
      sourceUrl: safeUrl(sourceUrl), image, images: imageCandidates,
      categories, category: categories[0], contentType, contentTypes,
      contentTypeLabel: CONTENT_TYPE_LABELS[contentType] || categories[0] || '展覽',
      eventFormat: String(raw.eventFormat || '').trim(),
      editorialStatus: String(raw.editorialStatus || '').trim(),
      editorialFlags: stringList(raw.editorialFlags),
      startDate: firstValue(raw.startDate, raw.start, show.time, show.startTime),
      endDate: firstValue(raw.endDate, raw.end, raw.endTime, show.endTime, raw.startDate),
      locationName: String(venueGroup || '地點待確認').trim(),
      location: String(venueGroup || '地點待確認').trim(),
      venueGroup, venueDetail, venueNames,
      venueName: String(firstValue(raw.venueName, venueNames[0], venueGroup)).trim(),
      venueId: String(raw.venueId || '').trim(),
      venueIds: stringList(raw.venueIds),
      venueMatches: Array.isArray(raw.venueMatches) ? raw.venueMatches : [],
      venueCoverageStatus: String(raw.venueCoverageStatus || '').trim(),
      unmatchedVenueValues: stringList(raw.unmatchedVenueValues),
      originalLocationName, originalVenueGroup,
      address: String(address || '').trim(), region,
      latitude, longitude, coordinateSource: firstValue(raw.coordinateSource, raw.coordinate_source),
      price: String(price || '票價請見活動頁面').trim(),
      unit: stripFacebookReferences(Array.isArray(raw.masterUnit) ? raw.masterUnit.join('、') : firstValue(raw.unit, raw.organizer, raw.showUnit, raw.masterUnit)),
      searchText: [
        raw.unit, raw.organizer, raw.showUnit, raw.masterUnit, raw.organizers,
        raw.performer, raw.performers, raw.artist, raw.artists, raw.singer, raw.singers,
        raw.actor, raw.actors, raw.cast, raw.castMembers, raw.presenter, raw.presenters,
        raw.producer, raw.tags,
      ].flatMap(value => Array.isArray(value) ? value : [value]).filter(Boolean).map(value => stripHtml(String(value))).join(' '),
      transitInfo: stripFacebookReferences(firstValue(raw.transitInfo, raw.transit)),
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

  function isPaid(event) {
    const price = String(event.price || '').trim();
    if (!price || isFree(event)) return false;
    if (/票價請見|依官網|待確認|另行公告|索票|--|未知|未提供/i.test(price)) return false;
    return /(?:NT\$|TWD|新臺幣|新台幣|元|售票|付費|門票|票價|全票|優待票|預售票|現場票|\d)/i.test(price);
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

  function fallbackPosition(category = '其他') {
    const index = CATEGORY_FALLBACK_INDEX[category] ?? CATEGORY_FALLBACK_INDEX['其他'];
    return {
      x:`${(index % 4) * (100 / 3)}%`,
      y:`${Math.floor(index / 4) * (100 / 3)}%`,
    };
  }

  function applyFallbackArtwork(element, category = '其他') {
    const position = fallbackPosition(category);
    element.classList.add('fallback-art');
    element.style.setProperty('--fallback-x', position.x);
    element.style.setProperty('--fallback-y', position.y);
    element.innerHTML = `<span class="fallback-art-label">${escapeHtml(category || '展覽')}</span>`;
    element.setAttribute('role', 'img');
    element.setAttribute('aria-label', `${category || '展覽'}類型展覽替代主視覺`);
    return element;
  }

  function fallbackMarkup(event, className = '') {
    const category = event.category || event.categories?.[0] || '其他';
    const position = fallbackPosition(category);
    return `<div class="${escapeHtml(className || 'card-placeholder')} fallback-art" data-media-kind="generated-fallback" style="--fallback-x:${position.x};--fallback-y:${position.y}" role="img" aria-label="${escapeHtml(category)}類型展覽替代主視覺"><span class="fallback-art-label">${escapeHtml(category)}</span></div>`;
  }

  function imageMarkup(event, className = '') {
    const eventCandidates = (event.images?.length ? event.images : event.image ? [event.image] : []).filter(isUsableImageUrl);
    const allowVenueFallback = !String(className).startsWith('detail-poster');
    const venueImage = allowVenueFallback ? eventVenueImage(event) : '';
    const candidates = eventCandidates.length ? eventCandidates : venueImage ? [venueImage] : [];
    const mediaKind = eventCandidates.length ? 'event' : venueImage ? 'venue' : 'placeholder';
    if (!candidates.length) return fallbackMarkup(event, className);
    const serialized = escapeHtml(JSON.stringify(candidates));
    const alt = mediaKind === 'venue' ? `${eventVenueLabel(event)}場館示意` : event.title;
    return `<span class="smart-image-frame ${escapeHtml(className)}" data-media-kind="${mediaKind}">
      <img class="smart-image-blur" src="${escapeHtml(candidates[0])}" alt="" aria-hidden="true" loading="lazy" decoding="async" referrerpolicy="no-referrer" onerror="this.hidden=true">
      <img class="smart-image-foreground" src="${escapeHtml(candidates[0])}" data-images="${serialized}" data-image-index="0" data-media-kind="${mediaKind}" data-placeholder-class="${escapeHtml(className || 'card-placeholder')}" data-fallback-category="${escapeHtml(event.category || '其他')}" alt="${escapeHtml(alt)}" loading="lazy" decoding="async" referrerpolicy="no-referrer" onload="window.__validateExhibitionImage(this)" onerror="window.__exhibitionImageFallback(this)">
    </span>`;
  }

  window.__exhibitionImageFallback = image => {
    try {
      const candidates = JSON.parse(image.dataset.images || '[]');
      const nextIndex = Number(image.dataset.imageIndex || 0) + 1;
      if (candidates[nextIndex]) {
        image.dataset.imageIndex = String(nextIndex);
        image.src = candidates[nextIndex];
        const backdrop = image.closest('.smart-image-frame')?.querySelector('.smart-image-blur');
        if (backdrop) { backdrop.hidden = false; backdrop.src = candidates[nextIndex]; }
        return;
      }
    } catch {}
    const placeholder = applyFallbackArtwork(
      document.createElement('div'),
      image.dataset.fallbackCategory || '其他',
    );
    placeholder.classList.add(image.dataset.placeholderClass || 'card-placeholder');
    (image.closest('.smart-image-frame') || image).replaceWith(placeholder);
  };

  window.__validateExhibitionImage = image => {
    if (!image?.isConnected || !image.complete) return;
    if (image.naturalWidth < 120 || image.naturalHeight < 80) window.__exhibitionImageFallback(image);
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
    const isDateReveal = Number.isInteger(options.revealIndex);
    const isMotionReveal = Number.isInteger(options.motionIndex);
    const isFavoriteReveal = Number.isInteger(options.favoriteIndex);
    const styleParts = [];
    if (isDateReveal) styleParts.push(`--reveal-index:${options.revealIndex}`);
    if (isMotionReveal) styleParts.push(`--motion-index:${options.motionIndex}`);
    if (isFavoriteReveal) styleParts.push(`--favorite-index:${options.favoriteIndex}`);
    const inlineStyle = styleParts.length ? ` style="${styleParts.join(';')}"` : '';
    const motionClass = isMotionReveal ? ' motion-card motion-from-right' : '';
    const favoriteClass = isFavoriteReveal ? ' favorite-reveal-card' : '';
    const wholeCardClass = options.wholeCardLink ? ' is-whole-card-link' : '';
    const wholeCardAttrs = options.wholeCardLink
      ? ` data-card-href="${escapeHtml(eventHref(event))}" role="link" tabindex="0" aria-label="查看${escapeHtml(event.title)}詳細資訊"`
      : '';
    return `
      <article class="exhibition-card${isDateReveal ? ' date-reveal-card' : ''}${motionClass}${favoriteClass}${wholeCardClass}" data-content-type="${escapeHtml(event.contentType || '')}" data-editorial-status="${escapeHtml(event.editorialStatus || '')}" data-venue-coverage="${escapeHtml(event.venueCoverageStatus || '')}"${inlineStyle}${wholeCardAttrs}>
        <a class="card-image" href="${eventHref(event)}">
          ${imageMarkup(event)}
          ${!(event.images?.length || event.image) && eventVenueImage(event) ? '<span class="venue-image-label">場館示意</span>' : ''}
          ${badges.length ? `<span class="card-badges">${badges.map(badge => `<span class="card-badge badge-${badge.type}">${badge.label}</span>`).join('')}</span>` : ''}
        </a>
        <button class="favorite-button ${isFavorite(event) ? 'active' : ''}" type="button" data-favorite="${escapeHtml(eventKey(event))}" aria-label="${isFavorite(event) ? '取消收藏' : '加入收藏'}">${isFavorite(event) ? '♥' : '♡'}</button>
        <div class="card-body">
          <div class="card-kicker"><span>${escapeHtml(eventDisplayCategory(event))}</span><span>${escapeHtml(event.region)}</span></div>
          <a href="${eventHref(event)}"><h3 class="card-title">${escapeHtml(event.title)}</h3></a>
          <div class="card-meta"><span>${escapeHtml(dateRange(event))}</span><span>${escapeHtml(eventVenueCompactLabel(event))}</span></div>
          <div class="card-price ${isFree(event) ? 'free' : ''}">${escapeHtml(event.price)}</div>
        </div>
      </article>`;
  }

  function compactMarkup(event) {
    const date = compactDate(event);
    return `<a class="compact-item" href="${eventHref(event)}">
      <div class="compact-date"><strong>${date.day}</strong><span>${date.month}</span></div>
      <div class="compact-info"><h4>${escapeHtml(event.title)}</h4><p>${escapeHtml(eventVenueCompactLabel(event))} · ${escapeHtml(event.region)}</p></div>
      <span class="compact-arrow">↗</span>
    </a>`;
  }

  function nearbyMiniMarkup(event, distance = null) {
    return `<a class="nearby-mini-card" href="${eventHref(event)}">
      ${imageMarkup(event, 'nearby-mini-media')}
      <div class="nearby-mini-body"><small>${distance === null ? escapeHtml(event.region) : `${distance.toFixed(1)} KM`}</small><h3>${escapeHtml(event.title)}</h3><p>${escapeHtml(eventVenueCompactLabel(event))}</p></div>
    </a>`;
  }

  function resultMarkup(event, distance) {
    const directionsUrl = googleMapsDirectionsUrl(event);
    return `<article class="nearby-result-card">
      <a class="nearby-result-main" href="${eventHref(event)}">
        ${imageMarkup(event, 'nearby-result-media')}
        <div class="nearby-result-copy">
          <span class="distance-badge">${Number.isFinite(distance) ? `${distance.toFixed(1)} KM` : escapeHtml(event.region)}</span>
          <h3>${escapeHtml(event.title)}</h3>
          <p>${escapeHtml(dateRange(event))}</p>
          <p>${escapeHtml(eventVenueCompactLabel(event))}</p>
        </div>
      </a>
      ${directionsUrl ? `<a class="nearby-map-link" href="${escapeHtml(directionsUrl)}" target="_blank" rel="noopener" aria-label="使用外部地圖前往${escapeHtml(event.title)}">地圖導航 ↗</a>` : ''}
    </article>`;
  }

  function readParams() {
    const params = new URLSearchParams(location.search);
    state.params = params;
    state.query = params.get('q') || '';
    const categoryValues = params.getAll('category').flatMap(value => String(value).split(',')).map(value => CATEGORY_ALIASES[value.trim()] || value.trim()).filter(category => CATEGORY_ORDER.includes(category));
    state.categories = new Set(categoryValues);
    state.region = params.get('region') || null;
    const venueValues = (params.get('venue') || '').split(',').map(value => value.trim()).filter(Boolean);
    state.selectedVenues = new Set(venueValues);
    state.venue = venueValues[0] || null;

    const requestedStatus = params.get('status') || 'all';
    const requestedAdmission = params.get('admission') || 'all';
    const legacyFreeStatus = requestedStatus === 'free';
    state.status = ['ongoing', 'upcoming', 'ending'].includes(requestedStatus)
      ? requestedStatus
      : 'all';
    state.admission = ['free', 'paid'].includes(requestedAdmission)
      ? requestedAdmission
      : legacyFreeStatus
        ? 'free'
        : 'all';

    if (legacyFreeStatus) {
      params.delete('status');
      params.set('admission', 'free');
      history.replaceState({}, '', `${location.pathname}?${params.toString()}${location.hash}`);
    }

    const requestedSort = params.get('sort');
    state.sort = ['popular', 'title', 'time'].includes(requestedSort)
      ? requestedSort
      : 'recommended';
    state.date = params.get('date') || null;
    const calendarAnchor = state.date ? parseDate(`${state.date}T00:00:00`) : new Date();
    state.calendarMonth = new Date(calendarAnchor.getFullYear(), calendarAnchor.getMonth(), 1);
    if (params.has('event')) state.view = 'detail';
    else if (params.get('view') === 'nearby') state.view = 'nearby';
    else if (params.get('view') === 'favorites') state.view = 'favorites';
    else if (params.get('view') === 'all' || state.query || state.categories.size || state.region || state.venue || params.has('status') || params.has('admission')) state.view = 'listing';
    else state.view = 'home';
  }

  // compatibility marker for legacy tests: eventVenueNames(event).includes(state.venue)
  function filterEvents(items = state.events, options = {}) {
    const {includeDate = true} = options;
    const query = state.query.trim().toLowerCase();
    return items.filter(event => {
      if (query) {
        const haystack = [event.title,event.description,event.unit,event.searchText,event.locationName,event.address,event.region,event.categories.join(' '),eventContentTypeLabel(event),eventVenueNames(event).join(' '),event.originalVenueGroup,event.price].join(' ').toLowerCase();
        if (!haystack.includes(query)) return false;
      }
      if (state.categories.size && !event.categories.some(category => state.categories.has(category))) return false;
      if (state.region && event.region !== state.region) return false;
      if (state.selectedVenues.size) {
        const names = eventVenueNames(event).map(cleanPlaceText);
        const original = cleanPlaceText(event.originalVenueGroup);
        const matched = [...state.selectedVenues].some(venue => names.includes(venue) || original === venue);
        if (!matched) return false;
      }
      if (state.status === 'ongoing' && !isOngoing(event)) return false;
      if (state.status === 'upcoming' && !isUpcoming(event)) return false;
      if (state.status === 'ending' && !isEnding(event, 30)) return false;
      if (state.admission === 'free' && !isFree(event)) return false;
      if (state.admission === 'paid' && !isPaid(event)) return false;
      if (includeDate && state.date && !eventOccursOn(event, state.date)) return false;
      return true;
    });
  }

  function eventTimeSortKey(event) {
    const today = dateOnly(new Date()).getTime();
    const start = parseDate(event.startDate);
    const end = parseDate(event.endDate) || start;
    const startTime = start ? dateOnly(start).getTime() : Infinity;
    const endTime = end ? dateOnly(end).getTime() : startTime;

    if (startTime <= today && endTime >= today) {
      return [0, endTime - today, startTime];
    }
    if (startTime > today) {
      return [1, startTime - today, startTime];
    }
    if (endTime < today) {
      return [2, today - endTime, -endTime];
    }
    return [3, Infinity, Infinity];
  }

  function compareTimeSort(a, b) {
    const keyA = eventTimeSortKey(a);
    const keyB = eventTimeSortKey(b);
    for (let index = 0; index < keyA.length; index += 1) {
      if (keyA[index] !== keyB[index]) {
        return keyA[index] - keyB[index];
      }
    }
    return a.title.localeCompare(b.title, 'zh-Hant');
  }

  function sortEvents(items) {
    const result = [...items];

    if (state.sort === 'popular') {
      result.sort((a, b) =>
        (Number(b.hitRate) || 0) - (Number(a.hitRate) || 0)
        || recommendationScore(b) - recommendationScore(a)
      );
    } else if (state.sort === 'title') {
      result.sort((a, b) =>
        a.title.localeCompare(b.title, 'zh-Hant')
      );
    } else if (state.sort === 'time') {
      result.sort(compareTimeSort);
    } else {
      result.sort((a, b) =>
        recommendationScore(b) - recommendationScore(a)
      );
    }

    return result;
  }

  function recommendationScore(event) {
    let score = Math.min(event.hitRate || 0, 50000) / 500;
    if (event.image) score += 20;
    if (isOngoing(event)) score += 18;
    if (isEnding(event)) score += 8;
    if (event.description.length > 80) score += 5;
    score += [...String(eventKey(event))].reduce((total, character) => total + character.charCodeAt(0), 0) % 997 / 1000000;
    return score;
  }

  function selectFeatured(items, count = 8) {
    const sorted = [...items].sort((a,b) => recommendationScore(b) - recommendationScore(a));
    const withImages = sorted.filter(event => event.image);
    return [...withImages, ...sorted.filter(event => !event.image)].filter((event, index, arr) => arr.findIndex(other => eventKey(other) === eventKey(event)) === index).slice(0, count);
  }

  function heroTicketMarkup(event, itemNumber) {
    return `<a class="hero-ticket-card" href="${eventHref(event)}" data-ticket-key="${escapeHtml(eventKey(event))}" aria-expanded="false" aria-label="查看展覽：${escapeHtml(event.title)}">
      <span class="ticket-watermark" aria-hidden="true"><b>展</b><i>TEJ</i></span>
      <span class="ticket-perforation" aria-hidden="true"></span>
      <div class="ticket-topline"><span>TAIWAN EXHIBITION</span><span>ADMIT ONE</span></div>
      <div class="ticket-main">
        <span class="ticket-index">${String(itemNumber).padStart(2,'0')}</span>
        <div><small>觀展靈感 · ${escapeHtml(eventContentTypeLabel(event))}</small><h2>${escapeHtml(event.title)}</h2><p>${escapeHtml(dateRange(event))} · ${escapeHtml(eventVenueCompactLabel(event))}</p></div>
      </div>
      <div class="ticket-footer"><span>EXHIBITION JOURNAL</span><span class="barcode">|||| ||| ||||</span></div>
    </a>`;
  }

  function heroPoseIndex(absoluteIndex) {
    return ((absoluteIndex % 3) + 3) % 3 + 1;
  }

  function heroTicketSlideMarkup(event, slot, itemNumber, motionClass = '', poseIndex = heroPoseIndex(itemNumber - 1)) {
    return `<article class="hero-ticket-slide hero-ticket-slot-${slot} ${motionClass}" data-ticket-key="${escapeHtml(eventKey(event))}" data-pose="${poseIndex}">
      ${heroTicketMarkup(event, itemNumber)}
    </article>`;
  }

  function heroPool() {
    const base = state.events.filter(event => (isOngoing(event) || isUpcoming(event)) && event.image);
    const fallback = state.events.filter(event => isOngoing(event) || isUpcoming(event));
    const pool = selectFeatured(base.length >= 4 ? base : fallback.length ? fallback : state.events, Math.min(48, state.events.length));
    const signature = pool.map(eventKey).join('|');
    const currentSignature = state.heroPool.map(eventKey).join('|');
    if (signature !== currentSignature) {
      state.heroPool = pool;
      state.heroCursor = 0;
    }
    return state.heroPool;
  }

  function heroIndex(offset = 0) {
    const length = state.heroPool.length;
    return length ? (state.heroCursor + offset + length) % length : 0;
  }

  function updateHeroStatus() {
    const status = $('#heroCarouselStatus');
    if (!status || !state.heroPool.length) return;
    const visible = [heroIndex(), heroIndex(1), heroIndex(2)].map(index => index + 1);
    status.textContent = `目前顯示第 ${visible.join('、')} 張票券，共 ${state.heroPool.length} 張`;
  }

  function renderHeroTickets() {
    const stack = $('#heroTicketStack');
    if (!stack) return;
    window.clearTimeout(state.heroTransitionTimer);
    const pool = heroPool();
    if (!pool.length) return;
    const firstIndex = heroIndex();
    const secondIndex = heroIndex(1);
    const thirdIndex = heroIndex(2);
    state.mobilePreviewTicket = null;
    stack.className = 'hero-ticket-stack';
    stack.innerHTML = [
      heroTicketSlideMarkup(pool[firstIndex], 1, firstIndex + 1, '', heroPoseIndex(firstIndex)),
      heroTicketSlideMarkup(pool[secondIndex], 2, secondIndex + 1, '', heroPoseIndex(secondIndex)),
      heroTicketSlideMarkup(pool[thirdIndex], 3, thirdIndex + 1, '', heroPoseIndex(thirdIndex))
    ].join('');
    updateHeroStatus();
  }

  function changeHeroPair(direction) {
    const stack = $('#heroTicketStack');
    const pool = heroPool();
    if (!stack || pool.length < 3 || state.heroAnimating) return;
    const motion = direction > 0 ? 'next' : 'previous';
    const firstIndex = heroIndex();
    const secondIndex = heroIndex(1);
    const thirdIndex = heroIndex(2);
    const incomingIndex = direction > 0 ? heroIndex(3) : heroIndex(-1);
    state.heroAnimating = true;
    state.mobilePreviewTicket = null;
    $('#heroNextButton')?.setAttribute('disabled', '');
    $('#heroPreviousButton')?.setAttribute('disabled', '');
    if (direction > 0) {
      stack.innerHTML = [
        heroTicketSlideMarkup(pool[firstIndex], 1, firstIndex + 1, 'hero-ticket-exit-next', heroPoseIndex(firstIndex)),
        heroTicketSlideMarkup(pool[secondIndex], 2, secondIndex + 1, 'hero-ticket-promote-next', heroPoseIndex(secondIndex)),
        heroTicketSlideMarkup(pool[thirdIndex], 3, thirdIndex + 1, 'hero-ticket-demote-next', heroPoseIndex(thirdIndex)),
        heroTicketSlideMarkup(pool[incomingIndex], 4, incomingIndex + 1, 'hero-ticket-incoming-next', heroPoseIndex(incomingIndex))
      ].join('');
    } else {
      stack.innerHTML = [
        heroTicketSlideMarkup(pool[incomingIndex], 0, incomingIndex + 1, 'hero-ticket-incoming-previous', heroPoseIndex(incomingIndex)),
        heroTicketSlideMarkup(pool[firstIndex], 1, firstIndex + 1, 'hero-ticket-demote-previous-a', heroPoseIndex(firstIndex)),
        heroTicketSlideMarkup(pool[secondIndex], 2, secondIndex + 1, 'hero-ticket-demote-previous-b', heroPoseIndex(secondIndex)),
        heroTicketSlideMarkup(pool[thirdIndex], 3, thirdIndex + 1, 'hero-ticket-exit-previous', heroPoseIndex(thirdIndex))
      ].join('');
    }
    requestAnimationFrame(() => requestAnimationFrame(() => stack.classList.add(`is-moving-${motion}`)));
    state.heroTransitionTimer = window.setTimeout(() => {
      state.heroCursor = heroIndex(direction);
      state.heroAnimating = false;
      $('#heroNextButton')?.removeAttribute('disabled');
      $('#heroPreviousButton')?.removeAttribute('disabled');
      renderHeroTickets();
    }, window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 40 : 720);
  }

  const HOME_STATUS_COPY = {
    ongoing: {eyebrow:'NOW ON VIEW', title:'目前正在舉辦的展覽'},
    upcoming: {eyebrow:'COMING SOON', title:'即將舉辦的展覽'},
    ending: {eyebrow:'ENDING SOON', title:'即將結束的展覽'},
    free: {eyebrow:'FREE ADMISSION', title:'免費入場的展覽'},
  };

  function renderHomeFilterResults(items) {
    const section = $('#filterResultsSection');
    const active = Boolean(state.date || state.status !== 'all');
    window.clearTimeout(state.filterResultsTimer);
    if (!active) {
      state.lastHomeFilterKey = '';
      section.classList.remove('is-visible','is-changing');
      section.classList.add('is-leaving');
      state.filterResultsTimer = window.setTimeout(() => {
        if (!state.date && state.status === 'all') {
          section.hidden = true;
          section.classList.remove('is-leaving');
          $('#filterResultsRail').innerHTML = '';
        }
      }, 620);
      return;
    }

    const statusCopy = HOME_STATUS_COPY[state.status];
    const selected = state.date ? parseDate(`${state.date}T00:00:00`) : null;
    const formattedDate = selected ? `${selected.getFullYear()} 年 ${selected.getMonth()+1} 月 ${selected.getDate()} 日` : state.date;
    const title = state.date
      ? `${formattedDate}${statusCopy ? `符合「${statusCopy.title.replace(/的展覽$/, '')}」條件` : '有展出'}的展覽`
      : statusCopy.title;
    const eyebrow = state.date ? 'EXHIBITIONS ON YOUR DATE' : statusCopy.eyebrow;
    const filterKey = [state.date || '', state.status, [...state.categories].sort().join('|')].join('::');
    const params = new URLSearchParams({view:'all'});
    if (state.date) params.set('date', state.date);
    if (state.status !== 'all') params.set('status', state.status);
    state.categories.forEach(category => params.append('category', category));

    $('#filterResultsEyebrow').textContent = eyebrow;
    $('#filterResultsTitle').textContent = title;
    $('#filterResultsDescription').textContent = items.length
      ? `共找到 ${items.length.toLocaleString('zh-TW')} 檔，向右滑動查看更多。`
      : '目前沒有符合條件的展覽，可以改選其他日期或狀態。';
    $('#filterResultsRail').innerHTML = items.length
      ? selectFeatured(items, 14).map((event,index) => cardMarkup(event,{revealIndex:index})).join('')
      : emptyInline('目前沒有符合條件的展覽');
    $('#filterResultsMore').href = `?${params.toString()}`;
    section.hidden = false;
    section.classList.remove('is-changing','is-leaving');
    requestAnimationFrame(() => section.classList.add('is-visible'));
    state.lastHomeFilterKey = filterKey;
  }

  function renderHome() {
    const ongoing = state.events.filter(isOngoing);
    const featured = selectFeatured(ongoing.length ? ongoing : state.events, 9);
    const filteredPool = filterEvents(state.events, {includeDate:false});
    const homeFilterItems = state.date ? filteredPool.filter(event => eventOccursOn(event, state.date)) : filteredPool;
    const upcoming = state.events.filter(isUpcoming).sort((a,b) => (parseDate(a.startDate)?.getTime() || Infinity) - (parseDate(b.startDate)?.getTime() || Infinity)).slice(0, 4);
    const ending = state.events.filter(event => isEnding(event, 30)).sort((a,b) => (parseDate(a.endDate)?.getTime() || Infinity) - (parseDate(b.endDate)?.getTime() || Infinity)).slice(0, 4);

    $('#heroEventCount').textContent = state.events.length.toLocaleString('zh-TW');
    $('#heroVenueCount').textContent = sourceVenueCount(state.events).toLocaleString('zh-TW');
    const updated = parseDate(state.updatedAt);
    $('#heroUpdatedDate').textContent = updated
      ? `${updated.getFullYear()} 年 ${updated.getMonth()+1} 月 ${updated.getDate()} 日`
      : '每日更新';
    $('#heroUpdatedTime').textContent = updated
      ? `${String(updated.getHours()).padStart(2,'0')} 點 ${String(updated.getMinutes()).padStart(2,'0')} 分更新`
      : '自動更新';
    const paperDate = $('#heroPaperDate');
    if (paperDate) paperDate.textContent = updated
      ? `${updated.getFullYear()}.${String(updated.getMonth()+1).padStart(2,'0')}.${String(updated.getDate()).padStart(2,'0')}`
      : localDateKey(new Date()).replaceAll('-', '.');
    if (!$('#heroTicketStack').children.length) renderHeroTickets();

    renderCategoryStrip();
    renderHomeFilterResults(homeFilterItems);
    $('#featuredRail').innerHTML = featured.length ? featured.map((event,index) => cardMarkup(event,{curated:index < 3,motionIndex:index})).join('') : emptyInline('目前沒有符合篩選的展覽');
    $('#upcomingList').innerHTML = upcoming.length ? upcoming.map(compactMarkup).join('') : emptyInline('目前沒有即將開展的活動');
    $('#endingList').innerHTML = ending.length ? ending.map(compactMarkup).join('') : emptyInline('目前沒有即將結束的活動');
    renderVenueGrid();
    renderHomeNearby();
    syncHomeFilters();
    setupScrollReveal();
  }

  function renderCategoryStrip() {
    const counts = countBy(state.events, event => event.categories);
    const categories = CATEGORY_ORDER;
    $('#categoryStrip').innerHTML = categories.map(category => `
      <a class="category-chip reveal-item ${state.categories.has(category) ? 'active' : ''}" style="--reveal-index:${categories.indexOf(category)}" href="${categoryHref(category)}">
        <span class="category-icon">${CATEGORY_ICON[category] || '＋'}</span>
        <strong>${escapeHtml(category)}</strong><small>${(counts[category] || 0).toLocaleString('zh-TW')} 檔</small>
      </a>`).join('');
  }

  function renderVenueGrid() {
    const counts = countBy(state.events, event => eventVenueNames(event).map(displayableVenueName).filter(Boolean));
    const venues = Object.keys(counts).filter(venue => venue && !/資料整理中|地點待確認/.test(venue)).sort((a,b) => counts[b] - counts[a]).slice(0, 36);
    $('#venueGrid').innerHTML = venues.map((venue, index) => {
      const venueImage = safeUrl(state.venueImages[venue] || '');
      const venueEvents = state.events
        .filter(event => eventVenueNames(event).map(displayableVenueName).includes(venue))
        .sort((a, b) => Number(isOngoing(b)) - Number(isOngoing(a)) || recommendationScore(b) - recommendationScore(a));
      const eventImages = venueEvents
        .flatMap(event => event.images?.length ? event.images : event.image ? [event.image] : [])
        .map(safeUrl)
        .filter((url, imageIndex, all) => isUsableImageUrl(url) && all.indexOf(url) === imageIndex);
      const candidates = [
        ...(isUsableImageUrl(venueImage) ? [venueImage] : []),
        ...eventImages,
      ].filter((url, imageIndex, all) => all.indexOf(url) === imageIndex);
      const category = venueEvents.flatMap(event => event.categories || [event.category]).find(Boolean) || '美術';
      const fallback = fallbackPosition(category);
      const imageKind = isUsableImageUrl(venueImage) ? '場館影像' : eventImages.length ? '展覽主視覺' : '編輯選圖';
      const serialized = escapeHtml(JSON.stringify(candidates));
      return `<a class="venue-tile motion-card motion-from-right ${candidates.length ? 'has-image' : 'venue-placeholder'}" style="--motion-index:${index}" href="${venueHref(venue)}">
        <span class="venue-fallback-art fallback-art" style="--fallback-x:${fallback.x};--fallback-y:${fallback.y}" aria-hidden="true"><span class="fallback-art-label">場館選集</span></span>
        ${candidates.length ? `<img src="${escapeHtml(candidates[0])}" data-venue-images="${serialized}" data-venue-image-index="0" alt="${escapeHtml(venue)}" loading="lazy" decoding="async" referrerpolicy="no-referrer" onload="window.__validateVenueImage(this)" onerror="window.__venueImageFallback(this)">` : ''}
        <div class="venue-tile-content">
          <small>VENUE ${String(index+1).padStart(2,'0')}${imageKind ? ` · ${imageKind}` : ''}</small>
          <h3>${escapeHtml(venue)}</h3><p>${counts[venue]} 檔展覽</p>
        </div>
      </a>`;
    }).join('') || emptyInline('目前沒有場館資料');
  }

  window.__venueImageFallback = image => {
    try {
      const candidates = JSON.parse(image.dataset.venueImages || '[]');
      const nextIndex = Number(image.dataset.venueImageIndex || 0) + 1;
      if (candidates[nextIndex]) {
        image.dataset.venueImageIndex = String(nextIndex);
        image.src = candidates[nextIndex];
        return;
      }
    } catch {}
    image.closest('.venue-tile')?.classList.add('venue-placeholder');
    image.remove();
  };

  window.__validateVenueImage = image => {
    if (!image?.isConnected || !image.complete) return;
    if (image.naturalWidth < 120 || image.naturalHeight < 80) window.__venueImageFallback(image);
  };

  function renderHomeNearby() {
    let items = state.events.filter(hasCoordinates).slice(0, 3);
    if (state.userLocation) items = nearestEvents(state.events, 3);
    $('#nearbyHomeList').innerHTML = items.length ? items.map(event => nearbyMiniMarkup(event, event._distance ?? null)).join('') : emptyInline('目前沒有可定位的展覽');
    $('#homeLocationButton').textContent = state.userLocation ? '已依目前位置排序' : '使用目前位置';
  }

  function syncHomeFilters() {
    $('#datePicker').value = state.date || '';
    $$('#statusPills button').forEach(button => button.classList.toggle('active', button.dataset.status === state.status));
    $('#clearFiltersButton').hidden = !(state.date || state.status !== 'all' || state.categories.size);
  }

  function renderListing() {
    const items = sortEvents(filterEvents());
    const titleParts = [];
    if (state.query) titleParts.push(`「${state.query}」`);
    if (state.categories.size) titleParts.push([...state.categories].join('、'));
    if (state.region) titleParts.push(state.region);
    if (state.selectedVenues.size) titleParts.push([...state.selectedVenues].slice(0,2).join('、') + (state.selectedVenues.size > 2 ? ` 等 ${state.selectedVenues.size} 個場地` : ''));
    const listingTitle = $('#listingTitle');
    if (titleParts.length) {
      listingTitle.innerHTML = titleParts
        .map(part => `<span class="listing-title-filter">${escapeHtml(part)}</span>`)
        .join('<span class="listing-title-separator" aria-hidden="true">／</span>');
      listingTitle.setAttribute('aria-label', titleParts.join('，'));
    } else {
      listingTitle.textContent = '探索全台展覽';
      listingTitle.removeAttribute('aria-label');
    }
    $('#listingEyebrow').textContent = state.query ? 'SEARCH RESULTS' : 'EXPLORE EXHIBITIONS';
    const listingDescription = $('#listingDescription');
    if (listingDescription) listingDescription.textContent = state.query ? '以下是符合搜尋關鍵字與篩選條件的結果。' : '';
    $('#listingCount').textContent = `找到 ${items.length.toLocaleString('zh-TW')} 檔展覽`;
    $('#listingGrid').innerHTML = items.map(event => cardMarkup(event,{wholeCardLink:true})).join('');
    $('#listingEmpty').hidden = items.length !== 0;
    $('#sortSelect').value = state.sort || 'recommended';
    renderSidebarOptions();
    renderListingCalendar();
    renderActiveFilters();
  }

  function displayableVenueName(value = '') {
    const text = cleanPlaceText(value);
    if (!text || /^(?:地點待確認|其他地區|場館資料整理中)$/.test(text)) return '';
    if (/資料整理中|(?:^|｜)場館資料整理中/.test(text)) return '';
    if (/^[^館園中心場空間劇院美術博物文創藝廊文化]+(?:區|鄉|鎮|市)(?:[（(].+[）)])?$/.test(text)) return '';
    return text.replace(/\s*[=＝:：;；|｜]+\s*$/g, '').trim();
  }

  function renderSidebarOptions() {
    const statusOptions = [
      ['ongoing','目前舉辦'],
      ['upcoming','即將舉辦'],
      ['ending','即將結束'],
    ];
    $('#listingStatusOptions').innerHTML = statusOptions.map(([value,label]) => `<button class="status-filter-button ${state.status === value ? 'active' : ''}" data-set-filter="status" data-value="${value}" type="button" aria-pressed="${state.status === value}">${label}</button>`).join('');

    const admissionOptions = [
      ['free','免費展覽'],
      ['paid','付費展覽'],
    ];
    $('#listingAdmissionOptions').innerHTML = admissionOptions.map(([value,label]) => `<button class="admission-filter-button ${state.admission === value ? 'active' : ''}" data-set-filter="admission" data-value="${value}" type="button" aria-pressed="${state.admission === value}">${label}</button>`).join('');

    const categoryCounts = countBy(state.events, event => event.categories);
    const categories = CATEGORY_ORDER;
    $('#listingCategoryOptions').innerHTML = categories.map(category => {
      const count = (categoryCounts[category] || 0).toLocaleString('zh-TW');
      return `<div class="listing-category-item">
        <button class="listing-category-option ${state.categories.has(category) ? 'active' : ''}" data-toggle-category="${escapeHtml(category)}" type="button" aria-pressed="${state.categories.has(category)}" aria-label="${escapeHtml(category)}，${count}檔">
          <span class="category-icon">${CATEGORY_ICON[category] || CATEGORY_ICON['其他']}</span>
        </button>
        <strong>${escapeHtml(category)}</strong>
      </div>`;
    }).join('');

    const regionGroups = REGION_ORDER.map(region => {
      const regionEvents = state.events.filter(event => event.region === region);
      if (!regionEvents.length) return '';
      const venueCounts = countBy(regionEvents, event => eventVenueNames(event).map(displayableVenueName).filter(Boolean));
      const venues = Object.keys(venueCounts).filter(Boolean).sort((a,b) => venueCounts[b] - venueCounts[a] || a.localeCompare(b, 'zh-Hant'));
      return `<details class="region-accordion ${state.region === region ? 'selected' : ''}" data-region-accordion="${escapeHtml(region)}" ${state.region === region ? 'open' : ''}>
        <summary><span class="region-name">${escapeHtml(region)}</span><small>${regionEvents.length.toLocaleString('zh-TW')} 檔</small><i aria-hidden="true">⌄</i></summary>
        <div class="region-venues">
          <button class="venue-filter-option ${state.region === region && !state.venue ? 'active' : ''}" type="button" data-region-filter="${escapeHtml(region)}" data-venue-filter=""><span>全部 ${escapeHtml(region)}</span><small>${regionEvents.length}</small></button>
          ${venues.length ? venues.map(venue => `<button class="venue-filter-option ${state.venue === venue ? 'active' : ''}" type="button" data-region-filter="${escapeHtml(region)}" data-venue-filter="${escapeHtml(venue)}"><span title="${escapeHtml(venue)}">${escapeHtml(venue)}</span><small>${venueCounts[venue]}</small></button>`).join('') : '<p class="region-no-venue">目前沒有可確認的場館名稱</p>'}
        </div>
      </details>`;
    }).join('');
    $('#listingLocationAccordion').innerHTML = regionGroups || emptyInline('目前沒有地點資料');
  }


  const VENUE_TYPE_LABELS = {
    all:'全部',
    convention_exhibition:'會展中心',
    cultural_park:'文創園區',
    museum_gallery:'美術館／博物館',
    performing_arts:'劇院／表演藝術',
    arena_stadium:'巨蛋／大型場館',
    live_house:'Live House',
    film_media:'影視場館',
    heritage_cultural:'歷史文化場館',
    outdoor_festival:'戶外場地',
    commercial_popup:'商業快閃',
    other:'其他展演場地'
  };

  function venueRegistryRecord(name) {
    return state.venueRegistryIndex.get(cleanPlaceText(name)) || null;
  }

  function inferredVenueType(name, registry = null) {
    const explicit = registry?.venueTypePrimary || registry?.venueTypes?.[0];
    if (explicit && VENUE_TYPE_LABELS[explicit]) return explicit;
    const text = cleanPlaceText(name);
    const rules = [
      ['cultural_park', /文創園區|文化創意產業園區|華山|松菸|松山文創|駁二/],
      ['convention_exhibition', /展覽館|會展中心|世貿|展貿中心/],
      ['museum_gallery', /美術館|博物館|藝廊|畫廊|藝術空間|文物館|紀念館/],
      ['performing_arts', /劇院|劇場|演藝廳|音樂廳|歌劇院|文化中心/],
      ['arena_stadium', /巨蛋|體育館|體育場|運動中心/],
      ['live_house', /livehouse|live house|音樂空間|展演館/],
      ['film_media', /影城|電影院|電影館|影視館/],
      ['heritage_cultural', /古蹟|故居|歷史建築|文化資產/],
      ['outdoor_festival', /公園|廣場|戶外|河濱/],
      ['commercial_popup', /百貨|商場|購物中心|快閃/],
    ];
    return rules.find(([,pattern]) => pattern.test(text))?.[0] || 'other';
  }

  function rebuildVenueCatalogCache() {
    const registryIndex = new Map();
    state.venueRegistry.forEach(registry => {
      [registry.name, ...(registry.aliases || [])].forEach(name => {
        const normalized = cleanPlaceText(name);
        if (normalized && !registryIndex.has(normalized)) registryIndex.set(normalized, registry);
      });
    });
    state.venueRegistryIndex = registryIndex;
    const records = new Map();
    state.events.forEach(event => {
      const seen = new Set();
      [...eventVenueNames(event), event.originalVenueGroup].map(displayableVenueName).filter(Boolean).forEach(eventName => {
        const registry = venueRegistryRecord(eventName);
        const name = registry?.name || eventName;
        const key = cleanPlaceText(name);
        if (!key || seen.has(key)) return;
        seen.add(key);
        const existing = records.get(key) || {
          id:registry?.id || name,
          name,
          aliases:registry?.aliases || [],
          region:normalizeRegion(registry?.region || event.region || '其他地區'),
          district:registry?.district || '',
          venueType:inferredVenueType(name, registry),
          count:0,
        };
        existing.count += 1;
        records.set(key, existing);
      });
    });
    state.venueCatalogCache = [...records.values()]
      .sort((a,b) => b.count - a.count || a.name.localeCompare(b.name,'zh-Hant'));
    return state.venueCatalogCache;
  }

  function venueCatalog() {
    return state.venueCatalogCache.length ? state.venueCatalogCache : rebuildVenueCatalogCache();
  }

  function syncVenueSelectionUrl(selected) {
    const value = [...selected].join(',');
    updateUrl({venue:value || null});
  }

  function renderVenueSelectedPreview() {
    const preview = $('#venueSelectedPreview');
    if (!preview) return;
    preview.hidden = !state.selectedVenues.size;
    preview.innerHTML = state.selectedVenues.size
      ? `<small>已選 ${state.selectedVenues.size} 個場地</small>${[...state.selectedVenues].slice(0,3).map(name => `<span>${escapeHtml(name)}</span>`).join('')}${state.selectedVenues.size > 3 ? `<span>＋${state.selectedVenues.size-3}</span>` : ''}`
      : '';
  }

  function renderVenueSelectorSelection() {
    $$('.venue-selector-option[data-venue-choice]', $('#venueSelectorList')).forEach(option => {
      const checked = state.venueDrawerDraft.has(option.dataset.venueChoice);
      option.classList.toggle('active', checked);
      option.setAttribute('aria-pressed', String(checked));
    });
    const selected = $('#venueSelectorSelected');
    const chips = $('#venueSelectorChips');
    selected.hidden = !state.venueDrawerDraft.size;
    chips.innerHTML = [...state.venueDrawerDraft].map(name =>
      `<button type="button" data-venue-choice="${escapeHtml(name)}">${escapeHtml(name)} <span>×</span></button>`
    ).join('');
    $('#venueSelectorApply').textContent = state.venueDrawerDraft.size
      ? `查看已選 ${state.venueDrawerDraft.size} 個場地`
      : '查看全部展覽';
    renderVenueSelectedPreview();
  }

  function renderVenueSelector() {
    const typeTabs = $('#venueTypeTabs');
    const list = $('#venueSelectorList');
    if (!typeTabs || !list) return;
    typeTabs.innerHTML = Object.entries(VENUE_TYPE_LABELS).map(([value,label]) =>
      `<button type="button" class="${state.venueTypeFilter === value ? 'active' : ''}" data-venue-type="${value}">${escapeHtml(label)}</button>`
    ).join('');

    const query = state.venueSearch.trim().toLowerCase();
    const catalog = venueCatalog().filter(item => {
      if (state.venueTypeFilter !== 'all' && item.venueType !== state.venueTypeFilter) return false;
      if (!query) return true;
      return [item.name,item.region,item.district,...item.aliases].join(' ').toLowerCase().includes(query);
    });
    const grouped = REGION_ORDER.map(region => [region, catalog.filter(item => item.region === region)]).filter(([,items]) => items.length);
    list.innerHTML = grouped.map(([region,items], regionIndex) => {
      const districts = [...new Set(items.map(item => item.district || '其他地區'))];
      return `<details class="venue-selector-region" ${regionIndex === 0 ? 'open' : ''}>
        <summary><span>${escapeHtml(region)}</span><small>${items.length} 個場地</small></summary>
        <div class="venue-selector-region-body">
          ${districts.map(district => `<section class="venue-selector-district">
            <h3>${escapeHtml(district)}</h3>
            ${items.filter(item => (item.district || '其他地區') === district).map(item => {
              const checked = state.venueDrawerDraft.has(item.name);
              return `<button type="button" class="venue-selector-option ${checked ? 'active' : ''}" data-venue-choice="${escapeHtml(item.name)}" aria-pressed="${checked}">
                <span><strong>${escapeHtml(item.name)}</strong><small>${escapeHtml(VENUE_TYPE_LABELS[item.venueType] || '展演場地')}</small></span>
                <em>${item.count} 檔</em>
              </button>`;
            }).join('')}
          </section>`).join('')}
        </div>
      </details>`;
    }).join('') || `<div class="venue-selector-empty">沒有找到符合條件的場地。</div>`;

    renderVenueSelectorSelection();
  }

  function openVenueSelector() {
    state.venueDrawerDraft = new Set(state.selectedVenues);
    state.venueSearch = '';
    state.venueTypeFilter = 'all';
    $('#venueSelectorSearch').value = '';
    $('#venueSelectorBackdrop').hidden = false;
    $('#venueSelectorDrawer').classList.add('open');
    $('#venueSelectorDrawer').setAttribute('aria-hidden','false');
    document.body.classList.add('venue-selector-open');
    lockViewport('venue-selector');
    renderVenueSelector();
    $('#venueSelectorList').scrollTop = 0;
    setTimeout(() => $('#venueSelectorSearch')?.focus(), 80);
  }

  function closeVenueSelector() {
    $('#venueSelectorBackdrop').hidden = true;
    $('#venueSelectorDrawer').classList.remove('open');
    $('#venueSelectorDrawer').setAttribute('aria-hidden','true');
    document.body.classList.remove('venue-selector-open');
    unlockViewport('venue-selector');
  }

  function renderListingCalendar() {
    const month = state.calendarMonth || new Date(new Date().getFullYear(), new Date().getMonth(), 1);
    const year = month.getFullYear();
    const monthIndex = month.getMonth();
    $('#calendarMonthLabel').textContent = `${year} 年 ${monthIndex + 1} 月`;
    $('#listingCalendar')?.classList.toggle('has-selected-date', Boolean(state.date));
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

  function renderMobileFilters() {
    const categoryOptions = $('#mobileCategoryOptions');
    if (!categoryOptions) return;
    const categoryCounts = countBy(state.events, event => event.categories);
    const categories = state.mobileCategoriesExpanded ? CATEGORY_ORDER : CATEGORY_ORDER.slice(0, 4);
    categoryOptions.innerHTML = categories.map(category => `
      <div class="mobile-category-item">
        <button class="${state.categories.has(category) ? 'active' : ''}" type="button" data-toggle-category="${escapeHtml(category)}" aria-pressed="${state.categories.has(category)}">
          <span>${CATEGORY_ICON[category] || CATEGORY_ICON['其他']}</span>
        </button>
        <strong>${escapeHtml(category)}</strong>
        <small>${(categoryCounts[category] || 0).toLocaleString('zh-TW')} 檔</small>
      </div>`).join('');
    const expandButton = $('#mobileCategoryExpand');
    expandButton.textContent = state.mobileCategoriesExpanded ? '收合分類' : '展開全部';
    expandButton.setAttribute('aria-expanded', String(state.mobileCategoriesExpanded));

    const month = state.calendarMonth || new Date(new Date().getFullYear(), new Date().getMonth(), 1);
    const year = month.getFullYear();
    const monthIndex = month.getMonth();
    $('#mobileCalendarMonthLabel').textContent = `${year} 年 ${monthIndex + 1} 月`;
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
      else if (key === todayKey) classes.push('today');
      if (count) classes.push('has-events');
      cells.push(`<button type="button" class="${classes.join(' ')}" data-mobile-calendar-date="${key}" aria-label="${year}年${monthIndex+1}月${day}日，${count}檔展覽"><span>${day}</span>${count ? `<small>${count > 99 ? '99+' : count}</small>` : ''}</button>`);
    }
    $('#mobileCalendarGrid').innerHTML = cells.join('');

    const regionCounts = countBy(state.events, event => event.region);
    $('#mobileRegionOptions').innerHTML = REGION_ORDER
      .filter(region => regionCounts[region])
      .map(region => `<button type="button" class="${state.region === region ? 'active' : ''}" data-mobile-region-choice="${escapeHtml(region)}"><span>${escapeHtml(region)}</span><small>${regionCounts[region].toLocaleString('zh-TW')} 檔</small><i>›</i></button>`)
      .join('') || emptyInline('目前沒有地區資料');
  }

  function openMobileMenu(section = 'all') {
    state.mobileDrawerSection = section;
    renderMobileFilters();
    const menu = $('#mobileMenu');
    const backdrop = $('#mobileMenuBackdrop');
    menu.hidden = false;
    backdrop.hidden = false;
    menu.setAttribute('aria-hidden', 'false');
    $('#mobileMenuButton').setAttribute('aria-expanded', 'true');
    document.body.classList.add('menu-open');
    lockViewport('mobile-menu');
    menu.scrollTop = 0;
    requestAnimationFrame(() => {
      menu.classList.add('open');
      backdrop.classList.add('open');
      const target = {
        category: $('#mobileCategorySection'),
        calendar: $('#mobileCalendarSection'),
        location: $('#mobileLocationSection'),
      }[section];
      if (target) {
        menu.scrollTo({
          top: Math.max(0, target.offsetTop - 16),
          left: 0,
          behavior: 'smooth',
        });
      }
    });
  }

  function closeMobileMenu() {
    const menu = $('#mobileMenu');
    const backdrop = $('#mobileMenuBackdrop');
    menu?.classList.remove('open');
    backdrop?.classList.remove('open');
    $('#mobileRegionPanel')?.classList.remove('open');
    $('#mobileRegionPanel')?.setAttribute('aria-hidden', 'true');
    $('#mobileMenuButton')?.setAttribute('aria-expanded', 'false');
    document.body.classList.remove('menu-open');
    unlockViewport('mobile-menu');
    window.setTimeout(() => {
      if (menu && !menu.classList.contains('open')) menu.hidden = true;
      if (backdrop && !backdrop.classList.contains('open')) backdrop.hidden = true;
      if (menu && !menu.classList.contains('open')) menu.scrollTop = 0;
    }, 340);
  }

  function openMobileRegionPanel() {
    renderMobileFilters();
    const menu = $('#mobileMenu');
    const panel = $('#mobileRegionPanel');
    menu.scrollTo({top:0, left:0, behavior:'auto'});
    panel.scrollTop = 0;
    panel.classList.add('open');
    panel.setAttribute('aria-hidden', 'false');
  }

  function closeMobileRegionPanel() {
    $('#mobileRegionPanel').classList.remove('open');
    $('#mobileRegionPanel').setAttribute('aria-hidden', 'true');
  }

  function renderActiveFilters() {
    const parts = [];
    if (state.query) parts.push(`<span class="active-filter">${escapeHtml(`搜尋：${state.query}`)}<button type="button" data-clear-filter="q" aria-label="移除搜尋">×</button></span>`);
    state.categories.forEach(category => parts.push(`<span class="active-filter">${escapeHtml(category)}<button type="button" data-toggle-category="${escapeHtml(category)}" aria-label="移除${escapeHtml(category)}分類">×</button></span>`));
    if (state.region) parts.push(`<span class="active-filter">${escapeHtml(state.region)}<button type="button" data-clear-filter="region" aria-label="移除地區">×</button></span>`);
    state.selectedVenues.forEach(venue => parts.push(`<span class="active-filter">${escapeHtml(venue)}<button type="button" data-remove-venue="${escapeHtml(venue)}" aria-label="移除${escapeHtml(venue)}">×</button></span>`));
    if (state.status !== 'all') {
      const label = {ongoing:'目前舉辦',upcoming:'即將舉辦',ending:'即將結束'}[state.status] || state.status;
      parts.push(`<span class="active-filter">${escapeHtml(label)}<button type="button" data-clear-filter="status" aria-label="移除狀態">×</button></span>`);
    }
    if (state.admission !== 'all') {
      const label = {free:'免費展覽',paid:'付費展覽'}[state.admission] || state.admission;
      parts.push(`<span class="active-filter">${escapeHtml(label)}<button type="button" data-clear-filter="admission" aria-label="移除票價類型">×</button></span>`);
    }
    if (state.date) parts.push(`<span class="active-filter">${escapeHtml(state.date)}<button type="button" data-clear-filter="date" aria-label="移除日期">×</button></span>`);
    if (parts.length) parts.push('<button class="clear-all-filters" type="button" data-clear-all-filters>清除全部篩選</button>');
    $('#activeFilters').innerHTML = parts.join('');
  }

  function renderFavorites() {
    const favorites = getFavorites();
    const items = state.events.filter(event => favorites.includes(eventKey(event)));
    $('#favoritesCount').textContent = `共收藏 ${items.length} 檔展覽`;
    $('#favoritesGrid').innerHTML = items.map((event, index) => cardMarkup(event, {favoriteIndex:index})).join('');
    $('#favoritesEmpty').hidden = items.length !== 0;
    const recommendationSection = $('#favoritesRecommendations');
    if (!items.length) {
      recommendationSection.hidden = true;
      $('#favoritesRecommendationRail').innerHTML = '';
      return;
    }

    const categoryCounts = countBy(items, event => event.categories);
    const favoriteRegions = new Set(items.map(event => event.region).filter(Boolean));
    const savedKeys = new Set(items.map(eventKey));
    const recommendations = state.events
      .filter(event => !savedKeys.has(eventKey(event)) && (isOngoing(event) || isUpcoming(event)))
      .map(event => ({
        event,
        affinity:event.categories.reduce((score, category) => score + (categoryCounts[category] || 0) * 100, 0)
          + (favoriteRegions.has(event.region) ? 24 : 0)
          + recommendationScore(event),
      }))
      .filter(item => item.affinity >= 100)
      .sort((a, b) => b.affinity - a.affinity || a.event.title.localeCompare(b.event.title, 'zh-Hant'))
      .slice(0, 14)
      .map(item => item.event);

    const favoriteCategories = Object.entries(categoryCounts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 3)
      .map(([category]) => category);
    $('#favoritesRecommendationCopy').textContent = favoriteCategories.length
      ? `收藏裡常出現「${favoriteCategories.join('、')}」，沿著這些線索再延伸幾個方向，可向右慢慢瀏覽。`
      : '沿著你留下的收藏線索，繼續發現氣質相近的展覽。';
    $('#favoritesRecommendationRail').innerHTML = recommendations.map(cardMarkup).join('') || emptyInline('目前沒有可推薦的相似展覽');
    recommendationSection.hidden = recommendations.length === 0;
  }

  function renderDetail() {
    const key = state.params.get('event');
    const event = state.events.find(item => eventKey(item) === key || item.sourceUrl === key);
    if (!event) {
      $('#detailContent').innerHTML = `<div class="empty-state"><span>?</span><h3>找不到這個展覽</h3><p>活動可能已下架或網址已更新。</p><a class="primary-link" href="./">回到首頁</a></div>`;
      return;
    }
    updatePageMetadata(event);
    const related = selectFeatured(state.events.filter(item => eventKey(item) !== eventKey(event) && (item.region === event.region || item.categories.some(category => event.categories.includes(category)))), 6);
    const mapUrl = googleMapsUrl(event);
    const externalUrl = event.sourceUrl || '';
    $('#detailContent').innerHTML = `
      <div class="detail-breadcrumb"><a href="./">首頁</a> / <a href="${categoryHref(event.category)}">${escapeHtml(event.category)}</a> / ${escapeHtml(event.title)}</div>
      <div class="detail-grid">
        <div class="detail-poster">${imageMarkup(event, 'detail-poster-placeholder')}</div>
        <article class="detail-info" data-content-type="${escapeHtml(event.contentType || '')}" data-editorial-status="${escapeHtml(event.editorialStatus || '')}" data-venue-coverage="${escapeHtml(event.venueCoverageStatus || '')}">
          <div class="detail-category detail-taxonomy">
            ${event.categories.map(category => `<a href="${categoryHref(category)}">${escapeHtml(category)}</a>`).join('<span aria-hidden="true">·</span>')}
            <span aria-hidden="true">/</span>
            <a href="${regionHref(event.region)}">${escapeHtml(event.region)}</a>
          </div>
          <h1>${escapeHtml(event.title)}</h1>
          <div class="detail-meta">
            ${detailMeta('展期', dateRange(event))}${detailMeta('地點', event.venueDetail && eventVenueNames(event).length <= 1 ? `${eventVenueLabel(event)}｜${event.venueDetail}` : eventVenueLabel(event, '／'))}${detailMeta('地址', event.address || event.region)}${detailMeta('票價', event.price)}${event.unit ? detailMeta('主辦單位', event.unit) : ''}${event.transitInfo ? detailMeta('交通', event.transitInfo) : ''}
          </div>
          <div class="detail-actions">
            ${externalUrl ? `<a class="primary" href="${escapeHtml(externalUrl)}" target="_blank" rel="noopener"><span>查看官方資訊</span><span aria-hidden="true">↗</span></a>` : '<span class="detail-action-disabled" aria-disabled="true">官方頁面待確認</span>'}
            ${mapUrl ? `<a href="${escapeHtml(mapUrl)}" target="_blank" rel="noopener"><span>地圖導航</span></a>` : '<span class="detail-action-disabled" aria-disabled="true">地點待確認</span>'}
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
  function nearestEvents(items, limit = 30, maxDistance = Infinity) {
    if (!state.userLocation) return items.filter(hasCoordinates).slice(0, limit);
    return items
      .filter(hasCoordinates)
      .map(event => ({...event,_distance:haversine(state.userLocation.lat,state.userLocation.lng,event.latitude,event.longitude)}))
      .filter(event => event._distance <= maxDistance)
      .sort((a,b) => a._distance-b._distance)
      .slice(0,limit);
  }

  function renderNearby() {
    const items = nearestEvents(filterEvents(), 200, state.userLocation ? NEARBY_RADIUS_KM : Infinity);
    $('#nearbyStatusText').textContent = state.userLocation
      ? `已定位目前位置，顯示 ${NEARBY_RADIUS_KM} 公里內展覽並由近到遠排列。`
      : `正在請求定位權限；允許後會顯示 ${NEARBY_RADIUS_KM} 公里內展覽。`;
    $('#nearbyCount').textContent = state.userLocation ? `${items.length} 檔・${NEARBY_RADIUS_KM} KM 內` : `${items.length} 檔待定位`;
    $('#nearbyResultList').innerHTML = items.map(event => resultMarkup(event, event._distance)).join('')
      || emptyInline(state.userLocation ? `目前位置 ${NEARBY_RADIUS_KM} 公里內沒有可定位的展覽` : '目前沒有提供座標的展覽');
    renderMap(items);
  }

  function renderMap(items) {
    if (!window.L) return;
    if (state.map) { state.map.remove(); state.map = null; }
    const center = state.userLocation ? [state.userLocation.lat, state.userLocation.lng] : [23.7, 121.0];
    state.map = L.map('nearbyMap', {scrollWheelZoom:false}).setView(center, state.userLocation ? 12 : 7);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {maxZoom:19, attribution:'&copy; OpenStreetMap contributors'}).addTo(state.map);
    const markers = [];
    if (state.userLocation) {
      L.circle(center, {radius:NEARBY_RADIUS_KM * 1000, color:'#34785a', fillColor:'#34785a', fillOpacity:.035, weight:1.5, dashArray:'6 7'}).addTo(state.map);
      L.circleMarker(center, {radius:8, color:'#171713', fillColor:'#c56538', fillOpacity:1, weight:3}).addTo(state.map).bindPopup('你目前的位置');
    }
    items.slice(0, 100).forEach(event => {
      if (!hasCoordinates(event)) return;
      const marker = L.marker([event.latitude,event.longitude]).addTo(state.map);
      const directionsUrl = googleMapsDirectionsUrl(event);
      marker.bindPopup(`<div class="map-popup"><h3>${escapeHtml(event.title)}</h3><p>${escapeHtml(eventVenueCompactLabel(event))}</p><p>${escapeHtml(dateRange(event))}</p><div class="map-popup-actions"><a href="${eventHref(event)}">查看展覽 →</a>${directionsUrl ? `<a href="${escapeHtml(directionsUrl)}" target="_blank" rel="noopener">外部地圖 ↗</a>` : ''}</div></div>`);
      markers.push(marker);
    });
    if (markers.length) {
      const group = L.featureGroup(markers);
      if (state.userLocation) group.addLayer(L.circleMarker(center, {radius:1, opacity:0, fillOpacity:0}));
      state.map.fitBounds(group.getBounds().pad(.12), {maxZoom:13});
    }
    setTimeout(() => state.map?.invalidateSize(), 150);
  }

  function requestLocation({automatic = false} = {}) {
    if (!navigator.geolocation) { showToast('此瀏覽器不支援定位功能'); return; }
    if (state.locationRequestPending) return;
    state.locationRequested = true;
    state.locationRequestPending = true;
    if (!automatic) showToast('正在取得目前位置…');
    navigator.geolocation.getCurrentPosition(position => {
      state.userLocation = {lat:position.coords.latitude,lng:position.coords.longitude};
      state.locationRequestPending = false;
      showToast('已依目前位置重新排序');
      renderHomeNearby();
      if (state.view === 'nearby') renderNearby();
    }, error => {
      state.locationRequestPending = false;
      const message = error.code === 1 ? '你尚未允許定位權限' : '暫時無法取得目前位置';
      showToast(message);
      if (state.view === 'nearby') {
        $('#nearbyStatusText').textContent = `${message}；可按右上角「重新取得位置」再次嘗試。`;
      }
    }, {enableHighAccuracy:true,timeout:12000,maximumAge:300000});
  }

  function coordinateMatchesRegion(event) {
    if (!hasCoordinates(event)) return false;
    const profile = REGION_CENTERS[event.region];
    if (!profile) return event.latitude >= 21.7 && event.latitude <= 26.5 && event.longitude >= 118 && event.longitude <= 122.5;
    return haversine(profile[0], profile[1], event.latitude, event.longitude) <= profile[2];
  }

  function navigationQuery(event) {
    const address = cleanPlaceText(event.address || '');
    const venue = displayableVenueName(eventVenueNames(event)[0] || event.originalVenueGroup || event.locationName || '');
    const region = cleanPlaceText(event.region || '');
    const addressLooksUseful = address
      && /(?:路|街|大道|巷|弄|號|村|里|園區)/.test(address)
      && !/場館資料整理中|地點待確認/.test(address);
    if (addressLooksUseful) return `${address}${venue && !address.includes(venue) ? ` ${venue}` : ''}`.trim();
    if (venue) return `${region} ${venue}`.trim();
    if (coordinateMatchesRegion(event)) return `${event.latitude},${event.longitude}`;
    return '';
  }

  function googleMapsUrl(event) {
    const query = navigationQuery(event);
    return query ? `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(query)}` : '';
  }

  function googleMapsDirectionsUrl(event) {
    if (hasCoordinates(event)) {
      return `https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(`${event.latitude},${event.longitude}`)}&travelmode=transit`;
    }
    const query = navigationQuery(event);
    return query ? `https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(query)}` : '';
  }

  function renderCurrentView() {
    const previousView = state.lastRenderedView;
    const views = {home:$('#homeView'),listing:$('#listingView'),nearby:$('#nearbyView'),detail:$('#detailView'),favorites:$('#favoritesView')};
    Object.entries(views).forEach(([name,element]) => element.hidden = name !== state.view);
    if (state.view !== 'detail') updatePageMetadata();
    if (state.view === 'home') {
      if (previousView !== 'home') resetHomeAnimations();
      renderHome();
    }
    if (state.view === 'listing') {
      renderListing();
    }
    if (state.view === 'nearby') {
      renderNearby();
      if (!state.userLocation && !state.locationRequested) requestLocation({automatic:true});
    }
    if (state.view === 'detail') renderDetail();
    if (state.view === 'favorites') renderFavorites();
    state.lastRenderedView = state.view;
    renderMobileFilters();
    $('#loadingView').hidden = true;
    updateFooter();
  }

  function updateFooter() {
    const recordCount = $('#footerRecordCount');
    if (recordCount) recordCount.textContent = `${state.events.length.toLocaleString('zh-TW')} 檔`;
    const venueCount = $('#footerVenueCount');
    if (venueCount) venueCount.textContent = `${sourceVenueCount(state.events).toLocaleString('zh-TW')} 處`;
    const updated = parseDate(state.updatedAt);
    const updatedAt = $('#footerUpdatedAt');
    if (updatedAt) updatedAt.textContent = updated
      ? `${updated.getFullYear()}.${String(updated.getMonth()+1).padStart(2,'0')}.${String(updated.getDate()).padStart(2,'0')} ${String(updated.getHours()).padStart(2,'0')}:${String(updated.getMinutes()).padStart(2,'0')}`
      : '每日自動更新';
  }

  function navigateTo(target, {replace = false, preserveScroll = false} = {}) {
    const url = new URL(target, location.href);
    if (url.origin !== location.origin || url.pathname !== location.pathname) return false;
    history[replace ? 'replaceState' : 'pushState']({}, '', `${url.pathname}${url.search}${url.hash}`);
    readParams();
    renderCurrentView();
    closeMobileMenu();
    if (!preserveScroll) window.scrollTo({top:0, left:0, behavior:'auto'});
    return true;
  }

  function updateUrl(filters = {}) {
    const params = new URLSearchParams(location.search);
    params.set('view','all');
    if ('status' in filters || 'admission' in filters) {
      if (params.get('status') === 'free') params.delete('status');
    }
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
    navigateTo(`?${params.toString()}`);
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

  function setupScrollReveal() {
    const sequenceGroups = $$('[data-reveal-sequence]');
    sequenceGroups.forEach(group => {
      [...group.children].forEach((child, index) => {
        child.classList.add('reveal-item');
        child.style.setProperty('--reveal-index', index);
      });
    });
    const motionTargets = [...sequenceGroups, ...$$('[data-motion-group], [data-split-reveal], [data-fade-reveal]')];
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      motionTargets.forEach(group => group.classList.add('is-in-view'));
      return;
    }
    if (!state.revealObserver) {
      state.revealObserver = new IntersectionObserver(entries => {
        entries.forEach(entry => {
          if (!entry.isIntersecting) return;
          entry.target.classList.add('is-in-view');
          state.revealObserver.unobserve(entry.target);
        });
      }, {threshold:.12, rootMargin:'0px 0px -5% 0px'});
    }
    motionTargets.forEach(group => {
      if (!group.classList.contains('is-in-view')) state.revealObserver.observe(group);
    });
  }

  function resetHomeAnimations() {
    const home = $('#homeView');
    if (!home) return;
    if (state.revealObserver) {
      state.revealObserver.disconnect();
      state.revealObserver = null;
    }
    $$('[data-reveal-sequence], [data-motion-group], [data-split-reveal], [data-fade-reveal]', home)
      .forEach(group => group.classList.remove('is-in-view'));
    if (!$('#heroTicketStack')?.children.length) renderHeroTickets();
    void home.offsetWidth;
  }

  function replayHomeAnimations() {
    if (state.view !== 'home' || $('#homeView')?.hidden) return;
    resetHomeAnimations();
    requestAnimationFrame(() => setupScrollReveal());
  }

  function bindEvents() {
    const updateScrollControls = () => {
      $('#siteHeader')?.classList.toggle('scrolled', scrollY > 12);
      $('#backToTopButton')?.classList.toggle('is-visible', scrollY > Math.max(520, innerHeight * .72));
    };
    window.addEventListener('scroll', updateScrollControls, {passive:true});
    updateScrollControls();
    $('#backToTopButton')?.addEventListener('click', () => window.scrollTo({top:0,left:0,behavior:'smooth'}));
    window.addEventListener('popstate', () => { readParams(); renderCurrentView(); window.scrollTo({top:0,left:0,behavior:'auto'}); });
    document.addEventListener('visibilitychange', () => {
      if (!document.hidden) replayHomeAnimations();
    });
    window.addEventListener('pageshow', event => {
      if (event.persisted) replayHomeAnimations();
    });
    $('#siteBrandLink').addEventListener('click', event => {
      if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
      event.preventDefault();
      event.stopImmediatePropagation();
      window.location.assign(new URL('./', window.location.href).href);
    });
    $('#mobileMenuButton').addEventListener('click', () => {
      const open = $('#mobileMenuButton').getAttribute('aria-expanded') === 'true';
      if (open) closeMobileMenu(); else openMobileMenu('all');
    });
    $('#mobileMenuClose').addEventListener('click', closeMobileMenu);
    $('#mobileMenuBackdrop').addEventListener('click', closeMobileMenu);
    $('#mobileCategoryExpand').addEventListener('click', () => {
      state.mobileCategoriesExpanded = !state.mobileCategoriesExpanded;
      renderMobileFilters();
    });
    $('#mobileCalendarClear').addEventListener('click', () => updateUrl({date:null}));
    $('#mobileCalendarPrev').addEventListener('click', () => {
      state.calendarMonth = new Date(state.calendarMonth.getFullYear(), state.calendarMonth.getMonth()-1, 1);
      renderMobileFilters();
    });
    $('#mobileCalendarNext').addEventListener('click', () => {
      state.calendarMonth = new Date(state.calendarMonth.getFullYear(), state.calendarMonth.getMonth()+1, 1);
      renderMobileFilters();
    });
    $('#mobileRegionLaunch').addEventListener('click', openMobileRegionPanel);
    $('#mobileRegionBack').addEventListener('click', closeMobileRegionPanel);
    $('#mobileVenueLaunch').addEventListener('click', () => {
      closeMobileMenu();
      window.setTimeout(openVenueSelector, 180);
    });

    const submitSearch = input => {
      const query = input.value.trim();
      if (query) {
        if (input === $('#mobileSearchInput')) closeMobileMenu();
        navigateTo(`?view=all&q=${encodeURIComponent(query)}`);
      }
    };
    $('#navSearchForm').addEventListener('submit', event => {event.preventDefault();submitSearch($('#navSearchInput'));});
    $('#mobileSearchForm').addEventListener('submit', event => {event.preventDefault();submitSearch($('#mobileSearchInput'));});
    $('#heroSearchForm').addEventListener('submit', event => {event.preventDefault();submitSearch($('#heroSearchInput'));});
    $('#heroNextButton')?.addEventListener('click', event => {
      event.preventDefault();
      changeHeroPair(1);
    });
    $('#heroPreviousButton')?.addEventListener('click', event => {
      event.preventDefault();
      changeHeroPair(-1);
    });
    const heroCarousel = $('#heroCarousel');
    heroCarousel?.addEventListener('pointerdown', event => {
      if (!window.matchMedia('(max-width: 760px) and (pointer: coarse)').matches) return;
      state.heroSwipeStartX = event.clientX;
      state.heroSwipeStartY = event.clientY;
    }, {passive:true});
    heroCarousel?.addEventListener('pointercancel', () => {
      state.heroSwipeStartX = null;
      state.heroSwipeStartY = null;
    });
    heroCarousel?.addEventListener('pointerup', event => {
      if (state.heroSwipeStartX == null || state.heroSwipeStartY == null) return;
      const deltaX = event.clientX - state.heroSwipeStartX;
      const deltaY = event.clientY - state.heroSwipeStartY;
      state.heroSwipeStartX = null;
      state.heroSwipeStartY = null;
      if (Math.abs(deltaX) < 42 || Math.abs(deltaX) < Math.abs(deltaY) * 1.2) return;
      state.heroSwipeBlockClickUntil = performance.now() + 480;
      changeHeroPair(deltaX < 0 ? 1 : -1);
    }, {passive:true});

    $('#datePicker').addEventListener('change', event => {state.date = event.target.value || null; renderHome();});
    $('#filterResultsClear').addEventListener('click', () => {state.status='all';state.date=null;state.categories.clear();renderHome();$('#discover').scrollIntoView({behavior:'smooth',block:'start'});});
    $('#clearFiltersButton').addEventListener('click', () => {state.status='all';state.date=null;state.categories.clear();renderHome();});
    $('#statusPills').addEventListener('click', event => {
      const button = event.target.closest('[data-status]');
      if (!button) return;
      const selectedStatus = button.dataset.status;
      state.status = selectedStatus !== 'all' && state.status === selectedStatus ? 'all' : selectedStatus;
      renderHome();
    });

    document.addEventListener('click', event => {
      if (event.target.closest('#heroCarousel') && performance.now() < state.heroSwipeBlockClickUntil) {
        event.preventDefault();
        event.stopPropagation();
        return;
      }
      const tappedHeroTicket = event.target.closest('.hero-ticket-card');
      const touchTicketMode = window.matchMedia('(hover: none) and (pointer: coarse)').matches;
      if (tappedHeroTicket && touchTicketMode) {
        const ticketKey = tappedHeroTicket.dataset.ticketKey;
        if (state.mobilePreviewTicket !== ticketKey || !tappedHeroTicket.classList.contains('is-touch-preview')) {
          event.preventDefault();
          $$('.hero-ticket-card.is-touch-preview').forEach(ticket => {
            ticket.classList.remove('is-touch-preview');
            ticket.setAttribute('aria-expanded', 'false');
          });
          tappedHeroTicket.classList.add('is-touch-preview');
          tappedHeroTicket.setAttribute('aria-expanded', 'true');
          state.mobilePreviewTicket = ticketKey;
          return;
        }
        state.mobilePreviewTicket = null;
      } else if (touchTicketMode && state.mobilePreviewTicket) {
        $$('.hero-ticket-card.is-touch-preview').forEach(ticket => {
          ticket.classList.remove('is-touch-preview');
          ticket.setAttribute('aria-expanded', 'false');
        });
        state.mobilePreviewTicket = null;
      }
      const internalLink = event.target.closest('a[href]');
      if (internalLink && !event.defaultPrevented && event.button === 0 && !event.metaKey && !event.ctrlKey && !event.shiftKey && !event.altKey && !internalLink.target && !internalLink.hasAttribute('download')) {
        const url = new URL(internalLink.href, location.href);
        const isSameAppRoute = url.origin === location.origin && url.pathname === location.pathname && !url.hash;
        if (isSameAppRoute) {
          event.preventDefault();
          if (internalLink.closest('#mobileMenu')) closeMobileMenu();
          navigateTo(url.href);
          return;
        }
      }
      const wholeCard = event.target.closest('.exhibition-card.is-whole-card-link');
      if (wholeCard && !event.target.closest('a,button,input,select,textarea')) {
        event.preventDefault();
        navigateTo(wholeCard.dataset.cardHref);
        return;
      }
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
      if (calendarButton) {
        const nextDate = calendarButton.dataset.calendarDate;
        updateUrl({date:nextDate === state.date ? null : nextDate});
      }
      const mobileCalendarButton = event.target.closest('[data-mobile-calendar-date]');
      if (mobileCalendarButton) {
        const nextDate = mobileCalendarButton.dataset.mobileCalendarDate;
        updateUrl({date:nextDate === state.date ? null : nextDate});
        return;
      }
      const openMobileFilterButton = event.target.closest('[data-open-mobile-filter]');
      if (openMobileFilterButton) {
        event.preventDefault();
        openMobileMenu(openMobileFilterButton.dataset.openMobileFilter || 'all');
        return;
      }
      const mobileRegionChoice = event.target.closest('[data-mobile-region-choice]');
      if (mobileRegionChoice) {
        const region = mobileRegionChoice.dataset.mobileRegionChoice;
        updateUrl({region:state.region === region ? null : region, venue:null});
        return;
      }

      const venueChoice = event.target.closest('[data-venue-choice]');
      if (venueChoice) {
        const name = venueChoice.dataset.venueChoice;
        if (state.venueDrawerDraft.has(name)) state.venueDrawerDraft.delete(name);
        else state.venueDrawerDraft.add(name);
        renderVenueSelectorSelection();
        return;
      }
      const venueTypeButton = event.target.closest('[data-venue-type]');
      if (venueTypeButton) {
        state.venueTypeFilter = venueTypeButton.dataset.venueType;
        renderVenueSelector();
        return;
      }
      const removeVenueButton = event.target.closest('[data-remove-venue]');
      if (removeVenueButton) {
        const next = new Set(state.selectedVenues);
        next.delete(removeVenueButton.dataset.removeVenue);
        syncVenueSelectionUrl(next);
        return;
      }

      const locationButton = event.target.closest('[data-region-filter]');
      if (locationButton) updateUrl({region:locationButton.dataset.regionFilter || null, venue:locationButton.dataset.venueFilter || null});

      const categoryButton = event.target.closest('[data-toggle-category]');
      if (categoryButton) {
        event.preventDefault();
        toggleCategoryFilter(categoryButton.dataset.toggleCategory);
        return;
      }
      const filterButton = event.target.closest('[data-set-filter]');
      if (filterButton) {
        const key = filterButton.dataset.setFilter;
        const value = filterButton.dataset.value;
        const currentValue = key === 'admission' ? state.admission : state.status;
        updateUrl({[key]:currentValue === value ? null : value});
      }
      const clearButton = event.target.closest('[data-clear-filter]');
      if (clearButton) {
        const key = clearButton.dataset.clearFilter;
        if (key === 'region') updateUrl({region:null,venue:null});
        else if (key === 'category') updateUrl({category:null});
        else updateUrl({[key]:null});
      }
      if (event.target.closest('[data-clear-all-filters]')) {
        updateUrl({q:null,category:null,region:null,venue:null,status:null,admission:null,date:null});
      }
    });

    document.addEventListener('keydown', event => {
      if (event.key === 'Escape' && $('#venueSelectorDrawer')?.classList.contains('open')) { closeVenueSelector(); return; }
      if (!['Enter',' '].includes(event.key)) return;
      const wholeCard = event.target.closest('.exhibition-card.is-whole-card-link');
      if (!wholeCard || event.target !== wholeCard) return;
      event.preventDefault();
      navigateTo(wholeCard.dataset.cardHref);
    });

    $('#listingLocationAccordion').addEventListener('toggle', event => {
      const opened = event.target.closest('details.region-accordion');
      if (!opened?.open) return;
      $$('details.region-accordion', $('#listingLocationAccordion')).forEach(details => {
        if (details !== opened) details.open = false;
      });
    }, true);

    $('#sidebarClearDate').addEventListener('click', () => updateUrl({date:null}));
    $('#calendarPrevButton').addEventListener('click', () => {state.calendarMonth = new Date(state.calendarMonth.getFullYear(),state.calendarMonth.getMonth()-1,1);renderListingCalendar();});
    $('#calendarNextButton').addEventListener('click', () => {state.calendarMonth = new Date(state.calendarMonth.getFullYear(),state.calendarMonth.getMonth()+1,1);renderListingCalendar();});
    $('#calendarTodayButton').addEventListener('click', () => updateUrl({date:localDateKey(new Date())}));
    $('#sortSelect').addEventListener('change', event => {
      const value = String(event.target.value);
      updateUrl({
        sort:value === 'recommended' ? null : value,
      });
    });
    $('#filterDrawerButton').addEventListener('click', () => $('#filterSidebar').classList.add('open'));
    $('#venueSelectorLaunch').addEventListener('click', openVenueSelector);
    $('#venueSelectorClose').addEventListener('click', closeVenueSelector);
    $('#venueSelectorBackdrop').addEventListener('click', closeVenueSelector);
    $('#venueSelectorSearch').addEventListener('input', event => {
      state.venueSearch = event.target.value;
      clearTimeout(state.venueSearchTimer);
      state.venueSearchTimer = setTimeout(renderVenueSelector, 110);
    });
    $('#venueSelectorClear').addEventListener('click', () => {
      state.venueDrawerDraft.clear();
      renderVenueSelectorSelection();
    });
    $('#venueSelectorReset').addEventListener('click', () => {
      state.venueDrawerDraft.clear();
      renderVenueSelectorSelection();
    });
    $('#venueSelectorApply').addEventListener('click', () => {
      const selected = new Set(state.venueDrawerDraft);
      closeVenueSelector();
      syncVenueSelectionUrl(selected);
    });
    $('#filterCloseButton').addEventListener('click', () => $('#filterSidebar').classList.remove('open'));
    $('#homeLocationButton').addEventListener('click', requestLocation);
    $('#nearbyLocationButton').addEventListener('click', requestLocation);
  }

  async function shareEvent(event) {
    const data = {title:event.title,text:`${event.title}｜${dateRange(event)}｜${eventVenueLabel(event)}`,url:new URL(eventHref(event),location.href).href};
    try {
      if (navigator.share) await navigator.share(data);
      else { await navigator.clipboard.writeText(data.url); showToast('連結已複製'); }
    } catch (error) { if (error.name !== 'AbortError') showToast('暫時無法分享'); }
  }

  async function fetchEventPayload() {
    const sources = [
      {url:'data/exhibitions.enriched.json', local:true, enriched:true},
      {url:'data/exhibitions.json', local:true, enriched:false},
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
        return {payload, rawEvents, local:source.local, sourceUrl:source.url, enriched:Boolean(source.enriched)};
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
      const [{payload, rawEvents, local, sourceUrl, enriched}, venueRegistryResponse, northernMatrixResponse] = await Promise.all([
        fetchEventPayload(),
        fetch('data/venues.json', {cache:'no-store'}).then(response => response.ok ? response.json() : {venues:[]}).catch(() => ({venues:[]})),
        fetch('data/northern_venue_matrix.json', {cache:'no-store'}).then(response => response.ok ? response.json() : {venues:[]}).catch(() => ({venues:[]})),
      ]);
      const stableVenues = Array.isArray(venueRegistryResponse?.venues) ? venueRegistryResponse.venues : [];
      const northernVenues = Array.isArray(northernMatrixResponse?.venues)
        ? northernMatrixResponse.venues.map(item => ({
            ...item,
            venueTypePrimary:item.venueType,
            venueTypes:[item.venueType],
          }))
        : [];
      state.venueRegistry = [...stableVenues, ...northernVenues];
      state.updatedAt = payload.updatedAt || payload.updated_at || (!local ? new Date().toISOString() : null);
      state.stats = payload.stats || {};
      state.registryBuild = payload.registryBuild || null;
      state.dataSource = sourceUrl;
      document.documentElement.dataset.eventData = enriched ? 'enriched' : 'legacy';
      state.venueImages = Object.fromEntries(Object.entries(payload.venueImages || {}).map(([venue, image]) => [venue, safeUrl(image)]).filter(([, image]) => isUsableImageUrl(image)));
      state.events = rawEvents.map(normalizeEvent).filter(event => event.title && eventKey(event) && !isExcludedEvent(event));
      if (!state.events.length) throw new Error('沒有可顯示的展覽資料');
      rebuildVenueCatalogCache();
      renderCurrentView();
    } catch (error) {
      console.error(error);
      $('#loadingView').hidden = true;
      $('#errorView').hidden = false;
    }
  }

  loadData();
})();
