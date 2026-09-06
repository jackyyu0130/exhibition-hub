/* Exhibition Hub V6.5.0-R18.2 P5-B → C3 — venue-led nearby discovery and bounded weekly updates. */
(() => {
  'use strict';

  const APP_RELEASE = '6.5.0-r18.2';
  document.documentElement.dataset.appRelease = APP_RELEASE;

  const CATEGORY_ORDER = ['演唱會','快閃店','動漫','美術','設計','攝影','市集','音樂','自然','歷史','表演','舞蹈','電影','親子','競賽','科技','其他'];
  const CONTENT_TYPE_LABELS = {
    exhibition:'一般展覽', art_exhibition:'藝術展覽', pop_culture:'動漫／IP', expo:'博覽會',
    concert:'演唱會', music_festival:'音樂祭', performance:'表演藝術', popup:'快閃店',
    market:'市集', festival:'城市節慶', film_screening:'電影／影展'
  };
  const CONTENT_TYPE_CATEGORY_MAP = {
    art_exhibition:'美術', pop_culture:'動漫', concert:'音樂', music_festival:'音樂',
    performance:'表演', popup:'快閃店', market:'市集', film_screening:'電影'
  };
  const MUSIC_PROGRAM_PATTERN = /演出曲目|program|musicians?|指揮|小提琴|大提琴|鋼琴|長笛|單簧管|雙簧管|symphony|concerto|sonata|orchestra|樂章|歌手|歌曲|唱片|音樂旅程|樂聲|歌聲|作品(?:第|[0-9])|op\.?\s*[0-9]/i;
  const VERIFIED_NATORI_PATTERN = /natori[\s\S]*(?:koshin|march|行進)|(?:koshin|march|行進)[\s\S]*natori/i;
  const VERIFIED_NATORI_PRICE = '1F站席 NT$4,200／2F前座席 NT$3,600／2F後座席 NT$3,200／3F座席 NT$2,800／1F身障席 NT$2,100／2F身障席 NT$1,600';

  function verifiedEventCorrection(title = '') {
    if (VERIFIED_NATORI_PATTERN.test(String(title))) {
      return {category:'演唱會', price:VERIFIED_NATORI_PRICE, startDate:'2026-08-08', endDate:'2026-08-09'};
    }
    if (/夢與緋光/.test(String(title))) return {category:'音樂'};
    return null;
  }
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
    [/國家兩廳院|國家音樂廳|國家戲劇院/i,'國家兩廳院'],
    [/富邦美術館(?:1樓|2樓|一樓|二樓|展覽空間)?|Fubon Art Museum/i,'富邦美術館'],
    [/松山菸廠|松煙|松菸(?:文創園區)?|松山文創(?:園區)?/i,'松山文創園區'],
    [/華山(?:1914)?(?:文化創意產業園區|文創園區|東\d+館|中\d+[A-Z]?館|紅磚六合院)?/i,'華山1914文化創意產業園區'],
    [/臺?北流行音樂中心|北流(?:中心)?/i,'臺北流行音樂中心']
  ];

  const VENUE_SEARCH_ALIASES = {
    '松菸':'松山文創園區', '松煙':'松山文創園區', '松山菸廠':'松山文創園區',
    '松山文創':'松山文創園區', '華山':'華山1914文化創意產業園區',
    '北美館':'臺北市立美術館', '國美館':'國立臺灣美術館',
    '北流':'臺北流行音樂中心', '衛武營':'衛武營國家藝術文化中心',
    '兩廳院':'國家兩廳院', '北藝中心':'臺北表演藝術中心'
  };
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
    venueRegistryNormalizedIndex: new Map(),
    venueNameMatchCache: new Map(),
    eventVenueRecordCache: new WeakMap(),
    eventVenueNameCache: new WeakMap(),
    eventRegionCache: new WeakMap(),
    venueCatalogCache: [],
    homeVenueEventIndex: new Map(),
    venueCoordinateIndex: new Map(),
    geocodeCache: {},
    venueSearchTimer: null,
    venueDrawerTimer: null,
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
    heroSwipePointerId: null,
    heroSwipeTouchId: null,
    heroSwipeBlockClickUntil: 0,
    mobilePreviewTicket: null,
    mobileCategoriesExpanded: false,
    mobileDrawerSection: 'all',
    viewportScrollY: 0,
    viewportLockOwner: null,
    lastRenderedDate: null,
    heroTransitionTimer: null,
    heroAutoAdvanceTimer: null,
    heroIntroTimer: null,
    heroIntroSequenceToken: 0,
    heroHasEntered: false,
    heroIntroComplete: false,
    heroPaused: false,
    heroInView: true,
    heroVisibilityObserver: null,
    listingRenderLimit: 48,
    listingResultSignature: '',
    filterResultsTimer: null,
    lastHomeFilterKey: '',
    revealObserver: null,
    revealFrameTokens: new WeakMap(),
    sectionMediaPromises: new WeakMap(),
    homeVenueObserver: null,
    homeVenueRenderPending: false,
    homeHydrationEpoch: 0,
    homeHydrationTimers: [],
    homeContentHydrated: false,
    leafletAssetsPromise: null,
    nearbyMapRenderToken: 0,
    routePending: false,
    scrollIdleTimer: null,
    scrollClassActive: false,
    headerScrolledState: null,
    backToTopState: null,
    lastRenderedView: null,
    locationRequested: false,
    locationRequestPending: false,
    socialDiscussions: [],
    socialPlatform: 'all',
    socialSort: 'popular',
  };

  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];

  const nextFrame = () => new Promise(resolve => requestAnimationFrame(() => resolve()));
  const delay = milliseconds => new Promise(resolve => window.setTimeout(resolve, milliseconds));

  function cancelHomeHydrationTasks() {
    state.homeHydrationEpoch += 1;
    state.homeHydrationTimers.forEach(timer => window.clearTimeout(timer));
    state.homeHydrationTimers = [];
  }

  function scheduleCalmHomeTask(callback, {delayMs = 0, timeoutMs = 1600} = {}) {
    const epoch = state.homeHydrationEpoch;
    const scheduledAt = performance.now();
    const run = () => {
      if (epoch !== state.homeHydrationEpoch || state.view !== 'home') return;
      const heroBusy = $('#heroTicketStack')?.classList.contains('is-intro-playing');
      const scrollBusy = document.body.classList.contains('is-scrolling');
      if ((heroBusy || scrollBusy) && performance.now() - scheduledAt < timeoutMs) {
        const retry = window.setTimeout(run, 120);
        state.homeHydrationTimers.push(retry);
        return;
      }
      const execute = () => {
        if (epoch !== state.homeHydrationEpoch || state.view !== 'home') return;
        callback();
      };
      if ('requestIdleCallback' in window) {
        requestIdleCallback(execute, {timeout: 320});
      } else {
        window.setTimeout(execute, 0);
      }
    };
    const timer = window.setTimeout(run, delayMs);
    state.homeHydrationTimers.push(timer);
    return timer;
  }

  function waitForHeroTypography(maxWaitMs = 420) {
    const fontReady = document.fonts?.ready || Promise.resolve();
    return Promise.race([fontReady.catch(() => undefined), delay(maxWaitMs)]);
  }

  function waitForScrollIdle(maxWaitMs = 900) {
    if (!document.body.classList.contains('is-scrolling')) return Promise.resolve();
    return new Promise(resolve => {
      const started = performance.now();
      const poll = () => {
        if (!document.body.classList.contains('is-scrolling') || performance.now() - started >= maxWaitMs) {
          resolve();
          return;
        }
        window.setTimeout(poll, 90);
      };
      poll();
    });
  }

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

  const DEFAULT_PAGE_TITLE = '台灣展覽誌｜全台展覽與演出資訊';
  const DEFAULT_PAGE_DESCRIPTION = '想看展，卻不知道從哪裡開始？整理全台最新展覽、藝術快閃與大型展會，一鍵掌握展期、場館與門票資訊，陪你找到下一次城市散步的靈感目的地。';
  const DEFAULT_PAGE_IMAGE = 'https://twexhibition.com/logo-512.png';
  const DEFAULT_PAGE_URL = 'https://twexhibition.com/';

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
      setMetaContent('#metaOgImage', DEFAULT_PAGE_IMAGE);
      setMetaContent('#metaOgUrl', DEFAULT_PAGE_URL);
      if (structured) structured.textContent = JSON.stringify({
        '@context':'https://schema.org', '@graph':[
          {'@type':'WebSite','@id':`${DEFAULT_PAGE_URL}#website`,name:'台灣展覽誌',
            url:DEFAULT_PAGE_URL,description:DEFAULT_PAGE_DESCRIPTION,
            publisher:{'@id':`${DEFAULT_PAGE_URL}#organization`}},
          {'@type':'Organization','@id':`${DEFAULT_PAGE_URL}#organization`,name:'台灣展覽誌',
            url:DEFAULT_PAGE_URL,logo:{'@type':'ImageObject',url:DEFAULT_PAGE_IMAGE,width:512,height:512}},
        ],
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
    setMetaContent('#metaOgUrl', location.href);
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

  const SINGER_CONCERT_PATTERN = /演唱會|巡迴演唱|巡演(?:台北|高雄|台中|臺北|臺中)?站|fan\s*concert|live\s+in\s+(?:taipei|kaohsiung|taichung)|live\s+tour|world\s+tour|asia\s+tour|tour\s*20\d{2}|concert\s*(?:20\d{2})?/i;
  const MUSIC_THEATRE_PATTERN = /音樂劇|歌劇|舞台劇|劇場(?!版)|劇團|京劇|掌中劇|歌仔戲|布袋戲|戲劇|讀劇|偶戲|馬戲|歌舞劇/i;
  const DANCE_CATEGORY_PATTERN = /舞蹈|舞作|舞團|芭蕾|現代舞|街舞|國標舞/i;
  const FILM_CATEGORY_PATTERN = /電影|影展|放映|映後|影像節|紀錄片|短片節|動畫影展|劇場版|台語片預告/i;
  const GENERAL_MUSIC_PATTERN = /音樂會|交響|管弦|管樂|擊樂|弦樂|協奏|獨奏|重奏|室內樂|古典音樂|爵士|國樂|樂團|合唱|重唱|阿卡貝拉|演奏會|音樂祭|音樂節|專場|不插電|現場演出|live\s*house|流行音樂(?:故事|文化|主題|常設|特)?展|音樂故事展/i;
  const CLASSICAL_MUSIC_PATTERN = /音樂會|交響|管弦|協奏|獨奏|重奏|室內樂|古典音樂|鋼琴|小提琴|大提琴|國樂|演奏會/i;
  const ANIME_CATEGORY_PATTERN = /動漫|動畫|漫畫(?:原作|展)?|原畫展|電玩|遊戲展|電競|ACG|cosplay|公仔|角色展|角色限定|模型展|玩具展|扭蛋|盒玩|卡牌|聲優|VTuber|虛擬偶像|特攝|輕小說|IP(?:展|祭|授權)|寶可夢|吉伊卡哇|chiikawa|櫻桃小丸子|蠟筆小新|哆啦\s*A\s*夢|三麗鷗|迪士尼|皮克斯|宮崎駿|貓貓蟲咖波|小熊維尼|史努比|PEANUTS|SNOOPY|PPULBATU|KYBUBI|姆明|伊藤潤二|航海王|ONE\s*PIECE|鬼滅之刃|咒術迴戰|進擊的巨人|排球少年|名偵探柯南|七龍珠|鋼彈|GUNDAM|新世紀福音戰士|初音未來|hololive|anime/i;
  const NATURAL_CATEGORY_PATTERN = /自然史|自然(?:展|特展|常設展)?|生態|植物(?:展|園)|野生動物|動物(?:展|園)|天文|地質|海洋(?:生態|科學|特展)|環境教育|科學館/i;
  const HISTORY_CATEGORY_PATTERN = /歷史|文化資產|文物|考古|古蹟|史料|地方誌|民俗|紀念(?:特展|展)|法老|埃及|古文明|文藝復興|史前|日治|戰後|二戰/i;
  // Letter boundaries keep "AI" from accidentally matching the "ai" in Taiwan.
  const TECHNOLOGY_CATEGORY_PATTERN = /科技|人工智慧|(?<![A-Za-z])AI(?![A-Za-z])|數位科技|半導體|資訊展|電腦展|機器人|虛擬實境|擴增實境|(?<![A-Za-z])VR(?![A-Za-z])|(?<![A-Za-z])AR(?![A-Za-z])/i;
  const DESIGN_CATEGORY_PATTERN = /設計|建築|工藝|時尚|家居|文具|文博會|design/i;
  const ART_CATEGORY_PATTERN = /美術|藝術(?:展|創作|作品)|插畫|圖畫書|繪畫|雕塑|裝置|當代藝術|典藏|書畫|陶藝|版畫|水墨|個展|聯展|畫展/i;
  const POPUP_CATEGORY_PATTERN = /快閃店|快閃|期間限定|限定店|popup|pop-up/i;
  const MARKET_CATEGORY_PATTERN = /市集|蚤之市|展售會|餐車/i;
  const PHOTO_CATEGORY_PATTERN = /攝影|影像展|photo(graphy)?/i;
  const CHILD_CATEGORY_PATTERN = /親子|兒童|家庭|幼兒/i;
  const COMPETITION_CATEGORY_PATTERN = /競賽|比賽|大賽|徵件比賽/i;

  function isSingerConcert(title = '', description = '', contentTypes = []) {
    const text = `${title} ${description}`;
    if (FILM_CATEGORY_PATTERN.test(text) || MUSIC_THEATRE_PATTERN.test(text) || DANCE_CATEGORY_PATTERN.test(text)) return false;
    if (CLASSICAL_MUSIC_PATTERN.test(text) && !/演唱會/i.test(text)) return false;
    return SINGER_CONCERT_PATTERN.test(text);
  }

  function primaryCategoryFor(title = '', description = '', contentTypes = [], candidates = []) {
    const titleText = String(title || '');
    const supportingText = `${titleText} ${description}`;
    const types = new Set(contentTypes || []);
    // Strong format categories are title-led. Long descriptions and noisy
    // secondary source categories must not turn a museum exhibition into
    // anime, film, theatre, or a concert.
    if (types.has('popup') || POPUP_CATEGORY_PATTERN.test(titleText)
      || candidates[0] === '快閃店'
      || (candidates.includes('快閃店') && POPUP_CATEGORY_PATTERN.test(description))) return '快閃店';
    if (types.has('film_screening') || FILM_CATEGORY_PATTERN.test(titleText)) return '電影';
    if (DANCE_CATEGORY_PATTERN.test(titleText)) return '舞蹈';
    if (MUSIC_THEATRE_PATTERN.test(titleText)) return '表演';
    if (isSingerConcert(titleText, '', contentTypes)) return '演唱會';
    if (types.has('music_festival') || GENERAL_MUSIC_PATTERN.test(titleText)) return '音樂';
    if ((types.has('performance') || candidates.includes('音樂'))
      && MUSIC_PROGRAM_PATTERN.test(supportingText)) return '音樂';
    if (ANIME_CATEGORY_PATTERN.test(titleText)) return '動漫';
    if (types.has('market') || MARKET_CATEGORY_PATTERN.test(titleText)) return '市集';
    if (types.has('performance')) return '表演';
    if (types.has('concert')) return '音樂';
    if (types.has('festival')) return '表演';
    if (PHOTO_CATEGORY_PATTERN.test(titleText)) return '攝影';
    if (NATURAL_CATEGORY_PATTERN.test(titleText)) return '自然';
    if (HISTORY_CATEGORY_PATTERN.test(titleText)) return '歷史';
    if (TECHNOLOGY_CATEGORY_PATTERN.test(titleText)) return '科技';
    if (DESIGN_CATEGORY_PATTERN.test(titleText)) return '設計';
    if (ART_CATEGORY_PATTERN.test(titleText)) return '美術';
    if (CHILD_CATEGORY_PATTERN.test(titleText)) return '親子';
    if (COMPETITION_CATEGORY_PATTERN.test(titleText)) return '競賽';
    if (types.has('art_exhibition')) return '美術';
    return '其他';
  }

  function titleSecondaryCategories(title = '') {
    const titleText = String(title || '');
    const rules = [
      ['動漫', ANIME_CATEGORY_PATTERN], ['攝影', PHOTO_CATEGORY_PATTERN],
      ['自然', NATURAL_CATEGORY_PATTERN], ['歷史', HISTORY_CATEGORY_PATTERN],
      ['科技', TECHNOLOGY_CATEGORY_PATTERN], ['設計', DESIGN_CATEGORY_PATTERN],
      ['美術', ART_CATEGORY_PATTERN], ['親子', CHILD_CATEGORY_PATTERN],
      ['競賽', COMPETITION_CATEGORY_PATTERN]
    ];
    return rules.filter(([, pattern]) => pattern.test(titleText)).map(([category]) => category);
  }

  function finalizeCategories(candidates = [], title = '', description = '', contentTypes = []) {
    const deduped = candidates.filter(Boolean).filter((category, index, array) => array.indexOf(category) === index);
    const primary = primaryCategoryFor(title, description, contentTypes, deduped);
    const remaining = titleSecondaryCategories(title).filter(category => category !== primary);
    return [primary, ...remaining].filter((category, index, array) => array.indexOf(category) === index).slice(0, 3);
  }

  function normalizeCategories(raw, title = '', description = '') {
    const rawValues = Array.isArray(raw) ? raw : raw !== undefined && raw !== null ? [raw] : [];
    const categories = [];
    rawValues.flatMap(value => String(value).split(/[、,，/|;；]+/)).forEach(value => {
      const text = value.trim();
      if (!text) return;
      const mapped = CATEGORY_CODE_MAP[text] || CATEGORY_ALIASES[text] || (CATEGORY_ORDER.includes(text) ? text : '');
      // Anime is never inherited from a noisy source code without a title signal.
      if (mapped === '動漫' && !ANIME_CATEGORY_PATTERN.test(title)) return;
      if (mapped && mapped !== '其他' && !categories.includes(mapped)) categories.push(mapped);
    });

    const titleText = String(title || '');
    const keywordRules = [
      ['演唱會', SINGER_CONCERT_PATTERN, titleText], ['表演', MUSIC_THEATRE_PATTERN, titleText],
      ['動漫', ANIME_CATEGORY_PATTERN, titleText], ['快閃店', POPUP_CATEGORY_PATTERN, titleText],
      ['舞蹈', DANCE_CATEGORY_PATTERN, titleText], ['音樂', GENERAL_MUSIC_PATTERN, titleText],
      ['電影', FILM_CATEGORY_PATTERN, titleText], ['攝影', PHOTO_CATEGORY_PATTERN, titleText],
      ['歷史', HISTORY_CATEGORY_PATTERN, titleText], ['自然', NATURAL_CATEGORY_PATTERN, titleText],
      ['科技', TECHNOLOGY_CATEGORY_PATTERN, titleText], ['設計', DESIGN_CATEGORY_PATTERN, titleText],
      ['市集', MARKET_CATEGORY_PATTERN, titleText], ['親子', CHILD_CATEGORY_PATTERN, titleText],
      ['競賽', COMPETITION_CATEGORY_PATTERN, titleText], ['美術', ART_CATEGORY_PATTERN, titleText]
    ];
    keywordRules.forEach(([category, regex, haystack]) => {
      if (regex.test(haystack) && !categories.includes(category)) categories.push(category);
    });
    const cleaned = categories.filter(category => CATEGORY_ORDER.includes(category));
    return (cleaned.length ? cleaned : ['其他']).filter((category, index, array) => array.indexOf(category) === index).slice(0, 6);
  }

  const EXCLUDED_CONTENT_PATTERN = /講座|講習|研習|研討會|論壇|座談|分享會|演講|課程|工作坊|營隊|訓練班|培訓班|讀書會/i;
  const LIBRARY_SERIES_PATTERN = /圖書館|分館|圖書室|閱覽室|書庫|library/i;
  const LOCAL_COMMUNITY_PATTERN = /社區發展協會|里辦公處|里民活動|地方社團|同好會|讀書會|居民活動|社區小聚|社團例會/i;
  const SMALL_LOCAL_ACTIVITY_PATTERN = /外展服務|繪本說故事|故事時間|故事媽媽|親子共讀|社區共讀|假日電影院|(?:圖書館|分館|鄉|鎮|區|里).{0,12}電影欣賞|文化走讀|深度走讀|城市走讀|導覽活動|\bDIY\b|手作(?:活動|體驗|課)|(?:體驗|觀察|藝術|繪畫|書法|舞蹈|音樂|攝影)課|(?:夏令|冬令|成長|親子|藝術|科學)營|交流會|同樂會|成果展|學生作品展|校內展|高中|國中|國小|大學.{0,8}(?:系|所|社)|社團|成果發表|成果音樂會|畢業製作|畢業展|校慶|班展|師生聯展|學生成果|社區大學|會員展|會員聯展|書畫學會|攝影學會|美術學會|藝術學會/i;
  const LOCAL_ORGANIZATION_PATTERN = /(?:縣|市|鄉|鎮|區|里).{0,14}(?:協會|學會|社團|團委會)/i;
  const PUBLIC_SHOW_PATTERN = /展覽|特展|聯展|個展|書展|攝影展|美術展|展演|音樂會|演出|藝術節|電影節|博覽會|劇場|戲劇|舞蹈/i;
  const LARGE_OR_OFFICIAL_EVENT_PATTERN = /國際|全國|博覽會|美術館|博物館|文化局|文化中心|文化處/i;

  function isExcludedEvent(event) {
    if (event.editorialStatus) {
      if (event.editorialStatus === 'exclude_review') return true;
    }
    const title = String(event.title || '');
    const sourceUrl = String(event.sourceUrl || '');
    const organizer = String(event.unit || '');
    const placeText = `${event.locationName || ''} ${event.venueGroup || ''} ${event.address || ''}`;
    if (!sourceUrl || isFacebookUrl(sourceUrl) || event.sourceUrlRejected) return true;
    if (!(event.images?.length || event.image)) return true;
    if (LIBRARY_SERIES_PATTERN.test(`${title} ${placeText} ${organizer}`)) return true;
    if (EXCLUDED_CONTENT_PATTERN.test(title) || SMALL_LOCAL_ACTIVITY_PATTERN.test(title)) return true;
    if ((event.categories || []).some(category => category === '講座' || category === '研習')) return true;
    if (displayableVenueName(event.venueGroup || event.locationName) === '') return true;
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
    const districtOnly = /^(?:(?:臺|台).{1,8}[市縣]|.{1,8}(?:區|鄉|鎮|市)[（(](?:臺|台).+[市縣][）)])$/.test(group);
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
    // R12 venue contract: only canonical/main venues are exposed as top-level
    // filter values. Floor, hall and gallery names belong to subVenueNames.
    const main = cleanPlaceText(firstValue(
      event?.venueName,
      event?.parentVenueName,
      event?.venueGroup,
      event?.locationName
    ));
    const matched = stringList(event?.venueNames)
      .filter(name => !stringList(event?.subVenueNames).includes(name));
    const registryValues = [main, ...matched]
      .filter(Boolean)
      .filter((item, index, array) => array.indexOf(item) === index);
    if (registryValues.length) return registryValues;

    const unmatched = stringList(event?.unmatchedVenueValues);
    if (unmatched.length) return unmatched;

    return stringList(firstValue(
      event?.originalVenueGroup,
      event?.originalLocationName
    ));
  }

  function eventVenueCandidateValues(event) {
    // Deliberately exclude venueDetail/subVenueNames: a child space must not
    // become a city-wide top-level venue filter.
    const childSpaces = stringList(event?.subVenueNames);
    return [
      event?.venueNames,
      event?.unmatchedVenueValues,
      event?.venueName,
      event?.parentVenueName,
      event?.originalVenueGroup,
      event?.originalLocationName,
      event?.venueGroup,
      event?.locationName,
    ]
      .flatMap(value => stringList(value))
      .filter(value => value && !childSpaces.includes(value))
      .filter((value, index, array) => array.indexOf(value) === index);
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

  function venueImageCandidates(venue) {
    const name = cleanPlaceText(venue?.name || venue || '');
    const candidates = [];
    const official = safeUrl(state.venueImages[name] || '');
    if (isUsableImageUrl(official)) candidates.push(official);
    const relatedEvents = state.homeVenueEventIndex.get(name) || [];
    relatedEvents.forEach(event => {
      const eventImages = (event.images?.length ? event.images : event.image ? [event.image] : [])
        .map(safeUrl)
        .filter(isUsableImageUrl);
      eventImages.forEach(image => {
        if (!candidates.includes(image)) candidates.push(image);
      });
    });
    return candidates.slice(0, 4);
  }

  function venueImageMarkup(venue, className = '') {
    const candidates = venueImageCandidates(venue);
    const label = cleanPlaceText(venue?.name || '展場');
    if (!candidates.length) {
      return `<div class="${escapeHtml(className || 'nearby-result-media')} fallback-art venue-nearby-placeholder" role="img" aria-label="${escapeHtml(label)}場館圖片整理中"><span class="fallback-art-brand" aria-hidden="true"><b>台灣展覽誌</b><small>VENUE GUIDE</small></span><span class="fallback-art-label">場館影像整理中</span></div>`;
    }
    const serialized = escapeHtml(JSON.stringify(candidates));
    return `<span class="smart-image-frame ${escapeHtml(className)}" data-media-kind="venue"><img class="smart-image-foreground" src="${escapeHtml(candidates[0])}" data-venue-nearby-images="${serialized}" data-image-index="0" alt="${escapeHtml(label)}" loading="lazy" decoding="async" referrerpolicy="no-referrer" onload="window.__validateVenueNearbyImage(this)" onerror="window.__venueNearbyImageFallback(this)"></span>`;
  }

  window.__venueNearbyImageFallback = image => {
    try {
      const candidates = JSON.parse(image.dataset.venueNearbyImages || '[]');
      const nextIndex = Number(image.dataset.imageIndex || 0) + 1;
      if (candidates[nextIndex]) {
        image.dataset.imageIndex = String(nextIndex);
        image.src = candidates[nextIndex];
        return;
      }
    } catch {}
    const venue = image.closest('.nearby-result-card, .nearby-mini-card');
    const frame = image.closest('.smart-image-frame');
    if (!venue || !frame) return;
    const fallback = document.createElement('div');
    fallback.className = image.closest('.nearby-mini-card')
      ? 'nearby-mini-media fallback-art venue-nearby-placeholder'
      : 'nearby-result-media fallback-art venue-nearby-placeholder';
    fallback.setAttribute('role', 'img');
    fallback.setAttribute('aria-label', '場館影像整理中');
    fallback.innerHTML = '<span class="fallback-art-brand" aria-hidden="true"><b>台灣展覽誌</b><small>VENUE GUIDE</small></span><span class="fallback-art-label">場館影像整理中</span>';
    frame.replaceWith(fallback);
  };

  window.__validateVenueNearbyImage = image => {
    if (!image?.isConnected || !image.complete) return;
    if (image.naturalWidth < 120 || image.naturalHeight < 80) {
      window.__venueNearbyImageFallback(image);
      return;
    }
    markDecodedMediaReady(image);
  };

  function eventContentTypeLabel(event) {
    return CONTENT_TYPE_LABELS[event?.contentType] || event?.categories?.[0] || '展覽';
  }

  function eventPrimaryCategory(event) {
    return event?.category || event?.categories?.[0] || '其他';
  }

  function eventCategories(event) {
    return [eventPrimaryCategory(event), ...(Array.isArray(event?.categories) ? event.categories : [])]
      .filter(category => CATEGORY_ORDER.includes(category))
      .filter((category, index, categories) => categories.indexOf(category) === index);
  }

  function eventMatchesCategories(event, selectedCategories = state.categories) {
    if (!selectedCategories?.size) return true;
    return eventCategories(event).some(category => selectedCategories.has(category));
  }

  function eventDisplayCategory(event) {
    return eventPrimaryCategory(event);
  }

  function sourceVenueCount(items = state.events) {
    return new Set(items.map(event => cleanPlaceText(firstValue(event.originalVenueGroup, event.originalLocationName, event.venueGroup, event.locationName))).filter(Boolean)).size;
  }

  function normalizeEvent(raw, index, {trustCanonicalCategories = false} = {}) {
    const show = bestShow(raw);
    const title = firstValue(raw.title, raw.titile, raw.name, '未命名展覽');
    const verifiedCorrection = verifiedEventCorrection(title);
    const description = stripFacebookReferences(firstValue(raw.description, raw.descriptionFilterHtml, raw.comment));
    const address = cleanPlaceText(firstValue(raw.address, raw.location, show.location, show.address));
    const originalLocationName = cleanPlaceText(firstValue(raw.locationName, raw.venue, show.locationName, show.venue, address));
    const originalVenueGroup = cleanPlaceText(firstValue(raw.venueGroup, raw.locationName, raw.venue, show.locationName, show.venue, address));
    const registryVenueNames = stringList(raw.venueNames);
    const registryVenueName = cleanPlaceText(firstValue(raw.venueName, raw.parentVenueName, registryVenueNames[0]));
    const rawVenue = cleanPlaceText(firstValue(registryVenueName, originalLocationName, address));
    const parsedVenue = venueParts(rawVenue, address, raw.venueGroup, raw.venueDetail);
    const venueGroup = registryVenueName || parsedVenue.venueGroup;
    // Backward compatibility: older official collectors put child spaces in
    // venueNames. When venueName is present, those legacy values are migrated
    // into subVenueNames instead of becoming public top-level venues.
    const explicitSubVenueNames = stringList(raw.subVenueNames);
    const legacySubVenueNames = registryVenueName && registryVenueNames.length
      && !registryVenueNames.includes(registryVenueName) && !explicitSubVenueNames.length
      ? [...registryVenueNames]
      : [];
    const subVenueNames = [...explicitSubVenueNames, ...legacySubVenueNames]
      .filter(name => name && name !== venueGroup)
      .filter((name, itemIndex, array) => array.indexOf(name) === itemIndex);
    const venueNames = [venueGroup, ...registryVenueNames]
      .filter(Boolean)
      .filter(name => !subVenueNames.includes(name))
      .filter((name, itemIndex, array) => array.indexOf(name) === itemIndex);
    const venueDetail = cleanPlaceText(firstValue(raw.venueDetail, subVenueNames.join('／'), parsedVenue.venueDetail));
    const subVenueName = cleanPlaceText(firstValue(raw.subVenueName, subVenueNames[0]));
    const sourceUrl = firstValue(raw.sourceUrl, raw.sourceWebPromote, raw.webSales, raw.sourceWebSite, raw.url, raw.website);
    const id = String(firstValue(raw.id, raw.UID, raw.uid, sourceUrl, `${title}-${index}`));
    const contentTypes = stringList(raw.contentTypes);
    const contentType = String(firstValue(raw.contentType, contentTypes[0])).trim();
    if (contentType && !contentTypes.includes(contentType)) contentTypes.unshift(contentType);
    const rawCategories = firstValue(raw.categories, raw.categoryName, raw.category);
    const baseCategories = normalizeCategories(rawCategories, title, description);
    const mappedCategory = contentTypes.map(type => CONTENT_TYPE_CATEGORY_MAP[type]).find(Boolean) || CONTENT_TYPE_CATEGORY_MAP[contentType];
    const categoryCandidates = mappedCategory ? [mappedCategory, ...baseCategories] : [...baseCategories];
    const canonicalCategories = [raw.category, ...(Array.isArray(raw.categories) ? raw.categories : [])]
      .map(value => CATEGORY_ALIASES[String(value || '').trim()] || String(value || '').trim())
      .filter(category => CATEGORY_ORDER.includes(category))
      .filter((category, categoryIndex, array) => array.indexOf(category) === categoryIndex)
      .slice(0, 3);
    let categories = trustCanonicalCategories && canonicalCategories.length
      ? canonicalCategories
      : finalizeCategories(categoryCandidates, title, description, contentTypes);
    if (verifiedCorrection?.category) {
      const mutuallyExclusive = new Set(['演唱會','音樂','表演','舞蹈','電影']);
      categories = [verifiedCorrection.category, ...categories.filter(category =>
        category !== verifiedCorrection.category
        && !(mutuallyExclusive.has(verifiedCorrection.category) && mutuallyExclusive.has(category))
      )].slice(0, 3);
    }
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
    const rawPrice = stripFacebookReferences(firstValue(raw.price, raw.Price, show.price, raw.discountInfo, firstValue(show.onSales, raw.onSales) === 'N' ? '免費' : ''));
    const price = verifiedCorrection?.price || sanitizePriceText(rawPrice, {title, description, categories});
    const correctedStartDate = verifiedCorrection?.startDate || firstValue(raw.startDate, raw.start, show.time, show.startTime);
    const correctedEndDate = verifiedCorrection?.endDate || firstValue(raw.endDate, raw.end, raw.endTime, show.endTime, raw.startDate);
    return {
      id, title: String(title).trim(), description: stripHtml(description),
      sourceUrl: safeUrl(sourceUrl),
      sourceUrlVerified: Boolean(raw.sourceUrlVerified),
      sourceUrlRejected: raw.sourceUrlRejected || '',
      image, images: imageCandidates,
      categories, category: categories[0], contentType, contentTypes,
      contentTypeLabel: CONTENT_TYPE_LABELS[contentType] || categories[0] || '展覽',
      eventFormat: String(raw.eventFormat || '').trim(),
      editorialStatus: String(raw.editorialStatus || '').trim(),
      editorialFlags: stringList(raw.editorialFlags),
      startDate: correctedStartDate,
      endDate: correctedEndDate,
      locationName: String(venueGroup || '地點待確認').trim(),
      location: String(venueGroup || '地點待確認').trim(),
      venueGroup, venueDetail, venueNames,
      venueName: String(firstValue(raw.venueName, raw.parentVenueName, venueNames[0], venueGroup)).trim(),
      parentVenueName: String(firstValue(raw.parentVenueName, raw.venueName, venueNames[0], venueGroup)).trim(),
      subVenueName, subVenueNames,
      publicVenueId: String(raw.publicVenueId || '').trim(),
      parentVenueId: String(firstValue(raw.parentVenueId, raw.venueId, raw.publicVenueId)).trim(),
      venueId: String(raw.venueId || raw.parentVenueId || '').trim(),
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

  function sanitizePriceText(value = '', event = {}) {
    const full = String(value || '').replace(/\s+/g, ' ').trim();
    if (!full) return '票價請見活動頁面';
    if (/免費|自由入場|免票|free/i.test(full)) return '免費入場';
    if (/票價請見|依官網|待確認|另行公告|索票|未提供/i.test(full)) return '票價請見活動頁面';
    const allowedLowPrice = /捐款|樂捐|象徵性|銅板|學生優惠|兒童優惠/i.test(full);
    const numericOnly = full.match(/^(?:NT\$?|TWD|新[臺台]幣|票價)?\s*[$＄]?\s*([0-9][0-9,]*)\s*(?:元)?$/i);
    if (numericOnly) {
      const amount = Number(numericOnly[1].replaceAll(',', ''));
      if (Number.isFinite(amount) && amount > 0 && amount < 50 && !allowedLowPrice) return '票價請見活動頁面';
    }
    const rangeValues = [...full.matchAll(/([0-9][0-9,]*)/g)]
      .map(match => Number(match[1].replaceAll(',', '')))
      .filter(Number.isFinite);
    const moneyValues = [...full.matchAll(/(?:NT\$?|TWD|新[臺台]幣|[$＄])\s*([0-9][0-9,]*)|([0-9][0-9,]*)\s*元/gi)]
      .map(match => Number(String(match[1] || match[2]).replaceAll(',', '')))
      .filter(Number.isFinite);
    const malformedYearRange = /^(?:NT\$?|TWD|新[臺台]幣)?\s*[$＄]?\s*[0-9]{1,2}\s*[–—-]\s*2,?0[0-9]{2}(?:\D|$)/i.test(full);
    if (malformedYearRange || (rangeValues.length >= 2
      && rangeValues.some(number => number >= 1900 && number <= 2100)
      && Math.min(...rangeValues) <= 31
      && !moneyValues.some(number => number >= 50))) {
      return '票價請見活動頁面';
    }
    const title = String(event.title || '');
    if (/演唱會|音樂會|live\s+tour|one[- ]man|concert/i.test(title)
      && rangeValues.length === 1 && rangeValues[0] < 50 && !allowedLowPrice) {
      return '票價請見活動頁面';
    }
    return full;
  }

  function compactPriceLabel(value = '') {
    const full = String(value || '').replace(/\s+/g, ' ').trim();
    if (/免費|自由入場|免票|free/i.test(full)) return '免費入場';
    return '票價請見活動頁面';
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
    element.innerHTML = `<span class="fallback-art-brand" aria-hidden="true"><b>台灣展覽誌</b><small>EXHIBITION JOURNAL</small></span><span class="fallback-art-label">${escapeHtml(category || '展覽')} 展覽</span>`;
    element.setAttribute('role', 'img');
    element.setAttribute('aria-label', `${category || '展覽'}類型展覽，圖片整理中`);
    return element;
  }

  function fallbackMarkup(event, className = '') {
    const category = event.category || event.categories?.[0] || '其他';
    const position = fallbackPosition(category);
    return `<div class="${escapeHtml(className || 'card-placeholder')} fallback-art" data-media-kind="official-fallback" style="--fallback-x:${position.x};--fallback-y:${position.y}" role="img" aria-label="${escapeHtml(category)}類型展覽，圖片整理中"><span class="fallback-art-brand" aria-hidden="true"><b>台灣展覽誌</b><small>EXHIBITION JOURNAL</small></span><span class="fallback-art-label">${escapeHtml(category)} 展覽</span></div>`;
  }

  function imageMarkup(event, className = '') {
    const eventCandidates = (event.images?.length ? event.images : event.image ? [event.image] : []).filter(isUsableImageUrl);
    const candidates = eventCandidates;
    const mediaKind = eventCandidates.length ? 'event' : 'placeholder';
    if (!candidates.length) return fallbackMarkup(event, className);
    const serialized = escapeHtml(JSON.stringify(candidates));
    const alt = event.title;
    const needsBackdrop = String(className).startsWith('detail-poster');
    return `<span class="smart-image-frame ${escapeHtml(className)}" data-media-kind="${mediaKind}">
      ${needsBackdrop ? `<img class="smart-image-blur" src="${escapeHtml(candidates[0])}" alt="" aria-hidden="true" decoding="async" referrerpolicy="no-referrer" onerror="this.hidden=true">` : ''}
      <img class="smart-image-foreground" src="${escapeHtml(candidates[0])}" data-images="${serialized}" data-image-index="0" data-media-kind="${mediaKind}" data-placeholder-class="${escapeHtml(className || 'card-placeholder')}" data-fallback-category="${escapeHtml(event.category || '其他')}" alt="${escapeHtml(alt)}" loading="lazy" decoding="async" referrerpolicy="no-referrer" onload="window.__validateExhibitionImage(this)" onerror="window.__exhibitionImageFallback(this)">
    </span>`;
  }

  window.__exhibitionImageFallback = image => {
    image?.closest('.smart-image-frame, .nearby-mini-card, .exhibition-card')?.classList.add('is-media-ready');
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

  function markDecodedMediaReady(image) {
    if (!image?.isConnected) return;
    image.closest('.smart-image-frame')?.classList.add('is-media-ready');
    image.closest('.nearby-mini-card, .venue-tile, .exhibition-card')?.classList.add('is-media-ready');
  }

  window.__validateExhibitionImage = image => {
    if (!image?.isConnected || !image.complete) return;
    if (image.naturalWidth < 120 || image.naturalHeight < 80) {
      window.__exhibitionImageFallback(image);
      return;
    }
    markDecodedMediaReady(image);
  };

  async function decodeImageForSection(image, timeoutMs = 1500) {
    if (!image?.isConnected) return;
    image.loading = 'eager';
    image.fetchPriority = 'low';
    try {
      await Promise.race([
        typeof image.decode === 'function' ? image.decode() : Promise.resolve(),
        delay(timeoutMs),
      ]);
    } catch {}
    markDecodedMediaReady(image);
  }

  function prepareSectionMedia(container, {limit = 12, concurrency = 1} = {}) {
    if (!container) return Promise.resolve();
    const existing = state.sectionMediaPromises.get(container);
    if (existing) return existing;
    const images = $$('img', container).slice(0, limit);
    if (!images.length) {
      container.dataset.mediaReady = 'true';
      return Promise.resolve();
    }
    container.dataset.mediaPreparing = 'true';
    let cursor = 0;
    const worker = async () => {
      while (cursor < images.length) {
        const image = images[cursor++];
        await waitForScrollIdle(700);
        await decodeImageForSection(image);
        await nextFrame();
      }
    };
    const promise = Promise.all(
      Array.from({length:Math.max(1, Math.min(concurrency, images.length))}, worker),
    ).finally(() => {
      container.dataset.mediaPreparing = 'false';
      container.dataset.mediaReady = 'true';
    });
    state.sectionMediaPromises.set(container, promise);
    return promise;
  }

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
      <article class="exhibition-card${isDateReveal ? ' date-reveal-card' : ''}${motionClass}${favoriteClass}${wholeCardClass}" data-content-type="${escapeHtml(event.contentType || '')}" data-categories="${escapeHtml(eventCategories(event).join('|'))}" data-editorial-status="${escapeHtml(event.editorialStatus || '')}" data-venue-coverage="${escapeHtml(event.venueCoverageStatus || '')}"${inlineStyle}${wholeCardAttrs}>
        <a class="card-image" href="${eventHref(event)}">
          ${imageMarkup(event)}
          ${badges.length ? `<span class="card-badges">${badges.map(badge => `<span class="card-badge badge-${badge.type}">${badge.label}</span>`).join('')}</span>` : ''}
        </a>
        <button class="favorite-button ${isFavorite(event) ? 'active' : ''}" type="button" data-favorite="${escapeHtml(eventKey(event))}" aria-label="${isFavorite(event) ? '取消收藏' : '加入收藏'}">${isFavorite(event) ? '♥' : '♡'}</button>
        <div class="card-body">
          <div class="card-kicker"><span>${escapeHtml(eventDisplayCategory(event))}</span><span>${escapeHtml(event.region)}</span></div>
          <a href="${eventHref(event)}"><h3 class="card-title">${escapeHtml(event.title)}</h3></a>
          <div class="card-meta"><span>${escapeHtml(dateRange(event))}</span><span>${escapeHtml(eventVenueCompactLabel(event))}</span></div>
          <div class="card-price ${isFree(event) ? 'free' : ''}" aria-label="${isFree(event) ? '免費入場' : '票價請見活動頁面'}">${escapeHtml(compactPriceLabel(event.price))}</div>
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

  function nearbyVenueMiniMarkup(venue, distance = null) {
    return `<a class="nearby-mini-card motion-card" href="${venueHref(venue.name)}">
      ${venueImageMarkup(venue, 'nearby-mini-media')}
      <div class="nearby-mini-body"><small>${distance === null ? escapeHtml(venue.region || '') : `${distance.toFixed(1)} KM`}</small><h3>${escapeHtml(venue.name)}</h3><p>${escapeHtml(venueAddressLabel(venue))}</p></div>
    </a>`;
  }

  function venueResultMarkup(venue, distance) {
    const directionsUrl = googleMapsDirectionsUrlForVenue(venue);
    return `<article class="nearby-result-card nearby-venue-result-card">
      <a class="nearby-result-main" href="${venueHref(venue.name)}" aria-label="查看${escapeHtml(venue.name)}的展覽">
        ${venueImageMarkup(venue, 'nearby-result-media')}
        <div class="nearby-result-copy">
          <span class="distance-badge">${Number.isFinite(distance) ? `${distance.toFixed(1)} KM` : escapeHtml(venue.region || '')}</span>
          <h3>${escapeHtml(venue.name)}</h3>
          <p>${escapeHtml(venueAddressLabel(venue))}</p>
        </div>
      </a>
      ${directionsUrl ? `<a class="nearby-map-link" href="${escapeHtml(directionsUrl)}" target="_blank" rel="noopener" aria-label="使用外部地圖前往${escapeHtml(venue.name)}">地圖導航 ↗</a>` : ''}
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
    state.socialPlatform = ['threads','ptt','dcard'].includes(params.get('platform')) ? params.get('platform') : 'all';
    state.socialSort = params.get('socialSort') === 'latest' ? 'latest' : 'popular';
    const calendarAnchor = state.date ? parseDate(`${state.date}T00:00:00`) : new Date();
    state.calendarMonth = new Date(calendarAnchor.getFullYear(), calendarAnchor.getMonth(), 1);
    if (params.has('event')) state.view = 'detail';
    else if (params.get('view') === 'nearby') state.view = 'nearby';
    else if (params.get('view') === 'favorites') state.view = 'favorites';
    else if (params.get('view') === 'discussions') state.view = 'social';
    else if (params.get('view') === 'all' || state.query || state.categories.size || state.region || state.venue || params.has('status') || params.has('admission')) state.view = 'listing';
    else state.view = 'home';
  }

  function canonicalVenueQueryTarget(query='') {
    const trimmed=cleanPlaceText(query);
    if(!trimmed) return '';
    if(VENUE_SEARCH_ALIASES[trimmed]) return VENUE_SEARCH_ALIASES[trimmed];
    const normalized=normalizedVenueLookupKey(trimmed);
    let best='',score=0;
    venueCatalog().forEach(item=>[item.name,...(item.aliases||[])].filter(Boolean).forEach(candidate=>{
      const key=normalizedVenueLookupKey(candidate);
      const exact=key===normalized;
      const partial=normalized.length>=2&&(key.includes(normalized)||normalized.includes(key));
      if(!exact&&!partial) return;
      const next=exact?10000+key.length:Math.min(key.length,normalized.length);
      if(next>score){score=next;best=item.name;}
    }));
    return best;
  }

  // compatibility marker for legacy tests: eventVenueNames(event).includes(state.venue)
  function filterEvents(items = state.events, options = {}) {
    const {includeDate = true} = options;
    const query = state.query.trim().toLowerCase();
    const venueQueryTarget = canonicalVenueQueryTarget(state.query);
    return items.filter(event => {
      if (query) {
        if (venueQueryTarget) {
          const targetKey=normalizedVenueLookupKey(venueQueryTarget);
          if(!eventCanonicalVenueNames(event).map(normalizedVenueLookupKey).includes(targetKey)) return false;
        } else {
          const haystack=[event.title,event.unit,event.searchText,event.locationName,event.address,event.region,event.categories.join(' '),eventContentTypeLabel(event),eventVenueNames(event).join(' '),event.originalVenueGroup,event.price,event.description].join(' ').toLowerCase();
          if(!haystack.includes(query)) return false;
        }
      }
      if (!eventMatchesCategories(event)) return false;
      if (state.region && !eventRegions(event).includes(state.region)) return false;
      if (state.selectedVenues.size) {
        const names = eventCanonicalVenueNames(event);
        const original = cleanPlaceText(event.originalVenueGroup);
        const matched = [...state.selectedVenues]
          .map(cleanPlaceText)
          .some(venue => names.includes(venue) || original === venue);
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

  function clearHeroTicketInteraction({except = null} = {}) {
    $$('.hero-ticket-slide', $('#heroCarousel') || document).forEach(slide => {
      if (slide === except) return;
      slide.classList.remove('is-ticket-active');
      const ticket = $('.hero-ticket-card', slide);
      ticket?.classList.remove('is-touch-preview');
      ticket?.setAttribute('aria-expanded', 'false');
    });
    if (!except) state.mobilePreviewTicket = null;
  }

  function activateHeroTicketInteraction(slide, {touch = false} = {}) {
    if (!slide || state.heroAnimating) return;
    const ticket = $('.hero-ticket-card', slide);
    if (!ticket) return;
    clearHeroTicketInteraction({except:slide});
    slide.classList.add('is-ticket-active');
    ticket.setAttribute('aria-expanded', 'true');
    if (touch) {
      ticket.classList.add('is-touch-preview');
      state.mobilePreviewTicket = ticket.dataset.ticketKey || slide.dataset.ticketKey || null;
    }
  }

  function heroPool() {
    const base = state.events.filter(event => (isOngoing(event) || isUpcoming(event)) && event.image);
    const fallback = state.events.filter(event => isOngoing(event) || isUpcoming(event));
    const pool = selectFeatured(base.length >= 4 ? base : fallback.length ? fallback : state.events, Math.min(18, state.events.length));
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

  function scheduleHeroAutoAdvance() {
    window.clearTimeout(state.heroAutoAdvanceTimer);
    if (!state.heroPool.length || state.heroPool.length < 2) return;
    if (document.hidden || state.heroPaused || !state.heroInView) return;
    state.heroAutoAdvanceTimer = window.setTimeout(() => {
      if (document.hidden || state.heroAnimating || state.heroPaused || !state.heroInView) {
        scheduleHeroAutoAdvance();
        return;
      }
      changeHeroPair(1);
    }, 15000);
  }

  function scheduleHeroIntro(stack) {
    const token = ++state.heroIntroSequenceToken;
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    state.heroIntroComplete = false;
    stack.classList.add('is-intro-pending');
    stack.classList.remove('is-intro-playing', 'is-intro-complete', 'is-entering');

    const begin = async () => {
      if (!reducedMotion) await waitForHeroTypography();
      if (token !== state.heroIntroSequenceToken || !stack.isConnected) return;
      await nextFrame();
      await nextFrame();
      if (token !== state.heroIntroSequenceToken || !stack.isConnected) return;
      if (reducedMotion) {
        stack.classList.remove('is-intro-pending');
        stack.classList.add('is-intro-complete');
        state.heroIntroComplete = true;
        return;
      }
      // Attach transition rules while the tickets are still at their pending
      // right-side pose. Removing pending one painted frame later guarantees a
      // real start/end pair instead of skipping directly to the final layout.
      stack.classList.add('is-intro-playing');
      void stack.offsetWidth;
      await nextFrame();
      if (token !== state.heroIntroSequenceToken || !stack.isConnected) return;
      stack.classList.remove('is-intro-pending');
      state.heroIntroTimer = window.setTimeout(() => {
        if (token !== state.heroIntroSequenceToken || !stack.isConnected) return;
        stack.classList.remove('is-intro-playing');
        stack.classList.add('is-intro-complete');
        state.heroIntroComplete = true;
      }, 3150);
    };
    begin();
  }

  function renderHeroTickets({settle = false} = {}) {
    const stack = $('#heroTicketStack');
    if (!stack) return;
    window.clearTimeout(state.heroTransitionTimer);
    window.clearTimeout(state.heroAutoAdvanceTimer);
    window.clearTimeout(state.heroIntroTimer);
    state.heroIntroSequenceToken += 1;
    const pool = heroPool();
    if (!pool.length) return;
    const firstIndex = heroIndex();
    const secondIndex = heroIndex(1);
    const thirdIndex = heroIndex(2);
    const isIntro = !settle && !state.heroHasEntered;
    state.mobilePreviewTicket = null;
    stack.className = settle
      ? 'hero-ticket-stack is-resetting'
      : isIntro
        ? 'hero-ticket-stack is-intro-pending'
        : 'hero-ticket-stack is-intro-complete';
    stack.innerHTML = [
      heroTicketSlideMarkup(pool[firstIndex], 1, firstIndex + 1, '', heroPoseIndex(firstIndex)),
      heroTicketSlideMarkup(pool[secondIndex], 2, secondIndex + 1, '', heroPoseIndex(secondIndex)),
      heroTicketSlideMarkup(pool[thirdIndex], 3, thirdIndex + 1, '', heroPoseIndex(thirdIndex))
    ].join('');
    if (settle) {
      requestAnimationFrame(() => requestAnimationFrame(() => stack.classList.remove('is-resetting')));
    } else if (isIntro) {
      state.heroHasEntered = true;
      scheduleHeroIntro(stack);
    }
    updateHeroStatus();
    scheduleHeroAutoAdvance();
  }

  function changeHeroPair(direction) {
    const stack = $('#heroTicketStack');
    const pool = heroPool();
    if (!stack || pool.length < 4 || state.heroAnimating) return;

    window.clearTimeout(state.heroAutoAdvanceTimer);
    window.clearTimeout(state.heroTransitionTimer);
    window.clearTimeout(state.heroIntroTimer);
    state.heroIntroSequenceToken += 1;
    state.heroAnimating = true;
    clearHeroTicketInteraction();
    $('#heroNextButton')?.setAttribute('disabled', '');
    $('#heroPreviousButton')?.setAttribute('disabled', '');

    const finish = () => {
      state.heroAnimating = false;
      stack.classList.remove('is-r105-moving');
      $('#heroNextButton')?.removeAttribute('disabled');
      $('#heroPreviousButton')?.removeAttribute('disabled');
      updateHeroStatus();
      scheduleHeroAutoAdvance();
    };

    const first = stack.querySelector('.hero-ticket-slot-1');
    const second = stack.querySelector('.hero-ticket-slot-2');
    const third = stack.querySelector('.hero-ticket-slot-3');

    if (!first || !second || !third) {
      state.heroCursor = heroIndex(direction);
      renderHeroTickets({settle:true});
      finish();
      return;
    }

    const nextCursor = heroIndex(direction);
    const incomingIndex = direction > 0 ? heroIndex(3) : heroIndex(-1);
    const incomingSlot = direction > 0 ? 4 : 0;
    const template = document.createElement('template');
    template.innerHTML = heroTicketSlideMarkup(
      pool[incomingIndex],
      incomingSlot,
      incomingIndex + 1,
      '',
      heroPoseIndex(incomingIndex)
    ).trim();
    const incoming = template.content.firstElementChild;
    if (!incoming) {
      state.heroCursor = nextCursor;
      renderHeroTickets({settle:true});
      finish();
      return;
    }

    stack.classList.remove('is-entering', 'is-intro-pending', 'is-intro-playing', 'is-intro-complete', 'is-resetting', 'is-moving-next', 'is-moving-previous');
    try {
      stack.getAnimations({subtree:true}).forEach(animation => animation.cancel());
    } catch {}

    stack.appendChild(incoming);
    void stack.offsetWidth;
    stack.classList.add('is-r105-moving');

    const moveSlot = (node, from, to) => {
      node.classList.remove(`hero-ticket-slot-${from}`);
      node.classList.add(`hero-ticket-slot-${to}`);
    };

    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const duration = reducedMotion ? 40 : 940;
    const outgoing = direction > 0 ? first : third;

    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        if (direction > 0) {
          // Left button / next:
          // first exits left, second becomes first, third becomes second,
          // and one new ticket enters from the right as the third ticket.
          moveSlot(first, 1, 0);
          moveSlot(second, 2, 1);
          moveSlot(third, 3, 2);
          moveSlot(incoming, 4, 3);
        } else {
          // Right button / previous: exact reverse motion.
          moveSlot(third, 3, 4);
          moveSlot(second, 2, 3);
          moveSlot(first, 1, 2);
          moveSlot(incoming, 0, 1);
        }
      });
    });

    state.heroTransitionTimer = window.setTimeout(() => {
      outgoing.remove();
      state.heroCursor = nextCursor;
      finish();
    }, duration);
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


  function socialDiscussionEvent(row) {
    return state.events.find(item => String(item.id || item.uid || '') === String(row.matchedEventId || ''));
  }

  function socialDiscussionCardMarkup(row, {compact = false} = {}) {
    const event = socialDiscussionEvent(row);
    const source = String(row.source || '社群').toLowerCase();
    const label = source === 'ptt' ? 'PTT' : source === 'dcard' ? 'DCARD' : source === 'threads' ? 'THREADS' : source.toUpperCase();
    return `<article class="social-discussion-card${compact ? ' is-compact' : ''}" data-social-source="${escapeHtml(source)}">
      <div class="social-discussion-meta"><span>${escapeHtml(label)}</span><small>社群討論</small></div>
      ${row.publishedAt ? `<time datetime="${escapeHtml(row.publishedAt)}">${escapeHtml(String(row.publishedAt).slice(0,10))}</time>` : ''}
      <p>${escapeHtml(row.shortExcerpt || '')}</p>
      ${event ? `<a class="social-related-event" href="${eventHref(event)}"><small>相關展覽</small><strong>${escapeHtml(event.title)}</strong><span aria-hidden="true">→</span></a>` : ''}
      <a class="social-original-link" href="${escapeHtml(row.postUrl)}" target="_blank" rel="noopener noreferrer">前往公開原文 ↗</a>
    </article>`;
  }

  function socialNavigationEligible() {
    const rows = Array.isArray(state.socialDiscussions) ? state.socialDiscussions : [];
    return rows.length >= 6 && new Set(rows.map(row => String(row.matchedEventId || '')).filter(Boolean)).size >= 3;
  }

  function syncSocialNavigation() {
    const visible = socialNavigationEligible();
    $$('[data-social-nav]').forEach(link => link.hidden = !visible);
    const allLink = $('#socialDiscussionsAllLink');
    if (allLink) allLink.hidden = !visible;
  }

  function renderSocialDiscussions() {
    const section = $('#socialDiscussionsSection');
    const rail = $('#socialDiscussionsRail');
    if (!section || !rail) return;
    const rows = (Array.isArray(state.socialDiscussions) ? state.socialDiscussions : []).slice(0, 6);
    syncSocialNavigation();
    if (!rows.length) { section.hidden=true; rail.innerHTML = ''; return; }
    rail.innerHTML = rows.map(row => socialDiscussionCardMarkup(row, {compact:true})).join('');
    section.hidden = false;
  }

  function renderSocialView() {
    const rows = Array.isArray(state.socialDiscussions) ? [...state.socialDiscussions] : [];
    const filtered = rows.filter(row => state.socialPlatform === 'all' || String(row.source || '').toLowerCase() === state.socialPlatform);
    filtered.sort((a,b) => state.socialSort === 'latest'
      ? String(b.publishedAt || '').localeCompare(String(a.publishedAt || ''))
      : Number(b.popularityScore || 0) - Number(a.popularityScore || 0));
    const grid = $('#socialDiscussionGrid');
    const empty = $('#socialViewEmpty');
    const count = $('#socialViewCount');
    if (count) count.textContent = `共 ${filtered.length.toLocaleString('zh-TW')} 則經人工確認的公開討論`;
    if (grid) grid.innerHTML = filtered.map(row => socialDiscussionCardMarkup(row)).join('');
    if (empty) empty.hidden = filtered.length !== 0;
    $$('#socialPlatformFilters [data-social-platform]').forEach(button => button.classList.toggle('active', button.dataset.socialPlatform === state.socialPlatform));
    const sort = $('#socialSortSelect'); if (sort) sort.value = state.socialSort;
  }

  function discussionsForEvent(event) {
    const key = String(event.id || event.uid || '');
    return (Array.isArray(state.socialDiscussions) ? state.socialDiscussions : []).filter(row => String(row.matchedEventId || '') === key).slice(0, 3);
  }

  function renderHome() {
    const ongoing = state.events.filter(isOngoing);
    const featured = selectFeatured(ongoing.length ? ongoing : state.events, 9);
    const filteredPool = filterEvents(state.events, {includeDate:false});
    const homeFilterItems = state.date ? filteredPool.filter(event => eventOccursOn(event, state.date)) : filteredPool;
    const upcoming = state.events.filter(isUpcoming).sort((a,b) => (parseDate(a.startDate)?.getTime() || Infinity) - (parseDate(b.startDate)?.getTime() || Infinity)).slice(0, 4);
    const ending = state.events.filter(event => isEnding(event, 30)).sort((a,b) => (parseDate(a.endDate)?.getTime() || Infinity) - (parseDate(b.endDate)?.getTime() || Infinity)).slice(0, 4);

    cancelHomeHydrationTasks();
    $('#heroEventCount').textContent = state.events.length.toLocaleString('zh-TW');
    $('#heroVenueCount').textContent = sourceVenueCount(state.events).toLocaleString('zh-TW');
    const updated = parseDate(state.updatedAt);
    $('#heroUpdatedDate').textContent = updated
      ? `${updated.getFullYear()} 年 ${updated.getMonth()+1} 月 ${updated.getDate()} 日`
      : '等待首次更新';
    $('#heroUpdatedTime').textContent = updated
      ? `${String(updated.getHours()).padStart(2,'0')} 點 ${String(updated.getMinutes()).padStart(2,'0')} 分更新`
      : '資料更新時間';
    const paperDate = $('#heroPaperDate');
    if (paperDate) paperDate.textContent = updated
      ? `${updated.getFullYear()}.${String(updated.getMonth()+1).padStart(2,'0')}.${String(updated.getDate()).padStart(2,'0')}`
      : localDateKey(new Date()).replaceAll('-', '.');
    if (!$('#heroTicketStack').children.length) renderHeroTickets();

    renderCategoryStrip();
    renderHomeFilterResults(homeFilterItems);
    renderSocialDiscussions();
    syncHomeFilters();
    setupScrollReveal();

    const featuredRail = $('#featuredRail');
    const upcomingList = $('#upcomingList');
    const endingList = $('#endingList');
    const nearbyList = $('#nearbyHomeList');
    const venueGrid = $('#venueGrid');

    if (state.homeContentHydrated && featuredRail?.querySelector('.exhibition-card')) {
      renderHomeNearby();
      scheduleHomeVenueGrid({delayMs:180});
      return;
    }

    // Build the editorial card DOM on the first layout pass. Remote images
    // are still decoded one at a time, but the browser no longer shows an empty
    // section for one second and then inserts every card in a single frame.
    if (featuredRail) {
      featuredRail.innerHTML = featured.length
        ? featured.map((event,index) => cardMarkup(event,{curated:index < 3,motionIndex:index})).join('')
        : emptyInline('目前沒有符合篩選的展覽');
      featuredRail.removeAttribute('aria-busy');
      const featuredSection = featuredRail.closest('[data-motion-group]');
      featuredSection?.classList.remove('is-in-view');
      prepareSectionMedia(featuredRail, {limit:9, concurrency:1});
    }
    if (upcomingList) {
      upcomingList.innerHTML = upcoming.length ? upcoming.map(compactMarkup).join('') : emptyInline('目前沒有即將開展的活動');
      upcomingList.removeAttribute('aria-busy');
    }
    if (endingList) {
      endingList.innerHTML = ending.length ? ending.map(compactMarkup).join('') : emptyInline('目前沒有即將結束的活動');
      endingList.removeAttribute('aria-busy');
    }
    const timeMotion = upcomingList?.closest('[data-split-reveal]');
    timeMotion?.classList.remove('is-in-view');
    setupScrollReveal();

    nearbyList?.setAttribute('aria-busy', 'true');
    if (nearbyList && !nearbyList.children.length) nearbyList.innerHTML = '<div class="home-nearby-placeholder" aria-hidden="true"></div>';
    if (venueGrid && !venueGrid.children.length) venueGrid.innerHTML = '<div class="venue-grid-loading" role="status"><span></span><p>場館資料準備中</p></div>';

    scheduleCalmHomeTask(() => {
      renderHomeNearby();
      nearbyList?.removeAttribute('aria-busy');
      setupScrollReveal();
    }, {delayMs:800, timeoutMs:2000});

    scheduleHomeVenueGrid({delayMs:1050, onRendered:() => {
      state.homeContentHydrated = true;
    }});
  }

  function renderCategoryStrip() {
    const counts = countBy(state.events, event => eventCategories(event));
    const categories = CATEGORY_ORDER;
    $('#categoryStrip').innerHTML = categories.map(category => `
      <a class="category-chip reveal-item ${state.categories.has(category) ? 'active' : ''}" style="--reveal-index:${categories.indexOf(category)}" href="${categoryHref(category)}">
        <span class="category-icon">${CATEGORY_ICON[category] || '＋'}</span>
        <strong>${escapeHtml(category)}</strong><small>${(counts[category] || 0).toLocaleString('zh-TW')} 檔</small>
      </a>`).join('');
  }

  function scheduleHomeVenueGrid({delayMs = 0, onRendered = null} = {}) {
    const grid = $('#venueGrid');
    if (!grid || grid.dataset.rendered === 'true' || state.homeVenueRenderPending) {
      if (grid?.dataset.rendered === 'true' && typeof onRendered === 'function') onRendered();
      return;
    }
    if (!grid.children.length) {
      grid.innerHTML = '<div class="venue-grid-loading" role="status"><span></span><p>場館資料準備中</p></div>';
    }
    scheduleCalmHomeTask(() => {
      if (grid.dataset.rendered === 'true' || state.homeVenueRenderPending) return;
      state.homeVenueRenderPending = true;
      renderVenueGrid();
      state.homeVenueRenderPending = false;
      if (typeof onRendered === 'function') onRendered();
    }, {delayMs, timeoutMs:4600});
  }

  function renderVenueGrid() {
    // Compatibility marker: the former homepage rail used .slice(0, 36);
    // P2 deliberately caps the first paint at twelve venue cards.
    const grid = $('#venueGrid');
    if (!grid) return;
    const venues = venueCatalog()
      .filter(item => item.count > 0 && item.name && !/資料整理中|地點待確認/.test(item.name))
      .slice(0, 36);
    const eventsByVenue = state.homeVenueEventIndex;

    grid.innerHTML = venues.map((item, index) => {
      const venue = item.name;
      const venueImage = safeUrl(state.venueImages[venue] || '');
      const venueEvents = (eventsByVenue.get(venue) || [])
        .sort((a, b) => Number(isOngoing(b)) - Number(isOngoing(a)) || recommendationScore(b) - recommendationScore(a))
        .slice(0, 8);
      const eventImages = venueEvents
        .flatMap(event => event.images?.length ? event.images.slice(0, 1) : event.image ? [event.image] : [])
        .map(safeUrl)
        .filter((url, imageIndex, all) => isUsableImageUrl(url) && all.indexOf(url) === imageIndex)
        .slice(0, 3);
      const candidates = [
        ...(isUsableImageUrl(venueImage) ? [venueImage] : []),
        ...eventImages,
      ].filter((url, imageIndex, all) => all.indexOf(url) === imageIndex).slice(0, 4);
      const category = venueEvents.flatMap(event => event.categories || [event.category]).find(Boolean) || '美術';
      const fallback = fallbackPosition(category);
      const imageKind = isUsableImageUrl(venueImage) ? '場館影像' : eventImages.length ? '展覽主視覺' : '編輯選圖';
      const serialized = escapeHtml(JSON.stringify(candidates));
      return `<a class="venue-tile motion-card motion-from-right ${candidates.length ? 'has-image' : 'venue-placeholder'}" style="--motion-index:${Math.min(index, 7)}" href="${venueHref(venue)}" data-venue-route="${escapeHtml(venue)}">
        <span class="venue-fallback-art fallback-art" style="--fallback-x:${fallback.x};--fallback-y:${fallback.y}" aria-hidden="true"><span class="fallback-art-label">場館選集</span></span>
        ${candidates.length ? `<img src="${escapeHtml(candidates[0])}" data-venue-images="${serialized}" data-venue-image-index="0" alt="${escapeHtml(venue)}" loading="${index < 12 ? 'eager' : 'lazy'}" decoding="async" fetchpriority="${index < 12 ? 'auto' : 'low'}" referrerpolicy="no-referrer" onload="window.__validateVenueImage(this)" onerror="window.__venueImageFallback(this)">` : ''}
        <div class="venue-tile-content">
          <small>VENUE ${String(index+1).padStart(2,'0')}${imageKind ? ` · ${imageKind}` : ''}</small>
          <h3>${escapeHtml(venue)}</h3><p>${item.count} 檔展覽</p>
        </div>
      </a>`;
    }).join('') || emptyInline('目前沒有場館資料');
    grid.dataset.rendered = 'true';
    const section = grid.closest('.venue-section');
    section?.classList.remove('is-in-view');
    const mediaPromise = prepareSectionMedia(grid, {limit:12, concurrency:1});
    if (section) state.sectionMediaPromises.set(section, mediaPromise);
    requestAnimationFrame(() => setupScrollReveal());
  }

  window.__venueImageFallback = image => {
    image?.closest('.venue-tile')?.classList.add('is-media-ready');
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
    if (image.naturalWidth < 120 || image.naturalHeight < 80) {
      window.__venueImageFallback(image);
      return;
    }
    markDecodedMediaReady(image);
  };

  function renderHomeNearby() {
    const items = nearestVenues(3, state.userLocation ? NEARBY_RADIUS_KM : Infinity);
    const list = $('#nearbyHomeList');
    list.innerHTML = items.length ? items.map(venue => nearbyVenueMiniMarkup(venue, venue._distance ?? null)).join('') : emptyInline('目前沒有可定位的展場');
    const section = list.closest('.nearby-home');
    section?.classList.remove('is-in-view');
    const mediaPromise = prepareSectionMedia(list, {limit:3, concurrency:1});
    if (section) state.sectionMediaPromises.set(section, mediaPromise);
    $('#homeLocationButton').textContent = state.userLocation ? '已依目前位置排序' : '使用目前位置';
  }

  function syncHomeFilters() {
    $('#datePicker').value = state.date || '';
    $$('#statusPills button').forEach(button => button.classList.toggle('active', button.dataset.status === state.status));
    $('#clearFiltersButton').hidden = !(state.date || state.status !== 'all' || state.categories.size);
  }

  function listingResultSignature() {
    return [
      state.query.trim().toLowerCase(),
      [...state.categories].sort().join('|'),
      state.region || '',
      [...state.selectedVenues].sort().join('|'),
      state.status,
      state.admission,
      state.date || '',
      state.sort,
    ].join('::');
  }

  function ensureListingLoadMoreButton() {
    let button = $('#listingLoadMore');
    if (button) return button;
    const grid = $('#listingGrid');
    if (!grid) return null;
    button = document.createElement('button');
    button.id = 'listingLoadMore';
    button.className = 'listing-load-more';
    button.type = 'button';
    button.hidden = true;
    grid.insertAdjacentElement('afterend', button);
    return button;
  }

  function renderListing() {
    const items = sortEvents(filterEvents());
    const signature = listingResultSignature();
    if (signature !== state.listingResultSignature) {
      state.listingResultSignature = signature;
      state.listingRenderLimit = window.matchMedia('(max-width: 760px)').matches ? 12 : 24;
    }
    const visibleItems = items.slice(0, state.listingRenderLimit);
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
    $('#listingCount').textContent = visibleItems.length < items.length
      ? `找到 ${items.length.toLocaleString('zh-TW')} 檔展覽，目前顯示 ${visibleItems.length.toLocaleString('zh-TW')} 檔`
      : `找到 ${items.length.toLocaleString('zh-TW')} 檔展覽`;
    // Compatibility lineage: cardMarkup(event,{wholeCardLink:true})
    const listingGrid = $('#listingGrid');
    listingGrid.classList.remove('is-in-view');
    listingGrid.innerHTML = visibleItems.map((event, index) => cardMarkup(event,{wholeCardLink:true,motionIndex:Math.min(index, 7)})).join('');
    $('#listingEmpty').hidden = items.length !== 0;
    const loadMore = ensureListingLoadMoreButton();
    if (loadMore) {
      const remaining = Math.max(0, items.length - visibleItems.length);
      loadMore.hidden = remaining === 0;
      loadMore.textContent = remaining ? `顯示更多展覽（尚有 ${remaining.toLocaleString('zh-TW')} 檔）` : '';
    }
    $('#sortSelect').value = state.sort || 'recommended';
    renderSidebarOptions();
    renderListingCalendar();
    renderActiveFilters();
    setupScrollReveal();
  }

  function displayableVenueName(value = '') {
    const text = cleanPlaceText(value);
    if (!text || /^(?:地點待確認|其他地區|場館資料整理中)$/.test(text)) return '';
    if (/資料整理中|(?:^|｜)場館資料整理中/.test(text)) return '';
    if (/^(?:第?\s*[一二三四五六七八九十0-9]+(?:\s*[、,，~～-]\s*[一二三四五六七八九十0-9]+)*|第?\s*[一二三四五六七八九十0-9]+(?:樓|展覽廳|展覽室|展廳)|(?:一|二|三|四|五|六|七|八|九|十|[0-9]+)樓|展覽廳|展覽室|展廳|多功能室|會議室|大廳|中庭)$/.test(text)) return '';
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

    const categoryCounts = countBy(state.events, event => eventCategories(event));
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

    const catalog = venueCatalog();
    const regionGroups = REGION_ORDER.map(region => {
      const regionEvents = state.events.filter(event => eventRegions(event).includes(region));
      const venues = catalog
        .filter(item => item.region === region)
        .sort((a,b) => b.count - a.count || a.name.localeCompare(b.name, 'zh-Hant'));
      if (!regionEvents.length && !venues.length) return '';
      return `<details class="region-accordion ${state.region === region ? 'selected' : ''}" data-region-accordion="${escapeHtml(region)}" ${state.region === region ? 'open' : ''}>
        <summary><span class="region-name">${escapeHtml(region)}</span><small>${regionEvents.length.toLocaleString('zh-TW')} 檔</small><i aria-hidden="true">⌄</i></summary>
        <div class="region-venues">
          <button class="venue-filter-option ${state.region === region && !state.venue ? 'active' : ''}" type="button" data-region-filter="${escapeHtml(region)}" data-venue-filter=""><span>全部 ${escapeHtml(region)}</span><small>${regionEvents.length}</small></button>
          ${venues.length ? venues.map(venue => {
            const unavailable = venue.count === 0;
            return `<button class="venue-filter-option ${state.venue === venue.name ? 'active' : ''} ${unavailable ? 'is-unavailable' : ''}" type="button" data-region-filter="${escapeHtml(region)}" data-venue-filter="${escapeHtml(venue.name)}" ${unavailable ? 'disabled aria-disabled="true"' : ''}><span title="${escapeHtml(venue.name)}">${escapeHtml(venue.name)}</span><small>${unavailable ? '尚無展演' : venue.count}</small></button>`;
          }).join('') : '<p class="region-no-venue">目前沒有已登錄場館</p>'}
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

  function normalizedVenueLookupKey(value = '') {
    return cleanPlaceText(value).replace(/臺/g,'台').replace(/[\s　()（）\-_/／・·,，.。:：;；|｜]+/g,'').toLowerCase();
  }

  function venueRecordPriority(record) {
    if (record?.confirmed) return 30;
    if (record?.status === 'active') return 20;
    return 10;
  }

  function confirmedVenueRecordByName(name) {
    const normalized = normalizedVenueLookupKey(name);
    if (!normalized) return null;
    if (state.venueNameMatchCache.has(normalized)) {
      return state.venueNameMatchCache.get(normalized);
    }

    const exact = state.venueRegistryNormalizedIndex.get(normalized);
    if (exact?.confirmed) {
      state.venueNameMatchCache.set(normalized, exact);
      return exact;
    }

    let bestMatch = null;
    let bestScore = 0;
    state.venueRegistry.forEach(registry => {
      if (!registry?.confirmed) return;
      [
        registry.name,
        ...(registry.aliases || []),
        registry.venueComplexName,
      ].filter(Boolean).forEach(candidate => {
        const key = normalizedVenueLookupKey(candidate);
        const contained = key.length >= 4 && (
          normalized.includes(key)
          || (normalized.length >= 5 && key.includes(normalized))
        );
        if (!contained) return;
        const score = Math.min(key.length, normalized.length);
        if (score > bestScore) {
          bestScore = score;
          bestMatch = registry;
        }
      });
    });
    state.venueNameMatchCache.set(normalized, bestMatch);
    return bestMatch;
  }

  function venueRegistryRecord(name) {
    const cleanName = cleanPlaceText(name);
    const direct = state.venueRegistryIndex.get(cleanName);
    if (direct?.confirmed) return direct;

    const confirmed = confirmedVenueRecordByName(cleanName);
    if (confirmed) return confirmed;

    const rule = VENUE_ALIAS_RULES.find(
      ([pattern]) => pattern.test(cleanName)
    );
    if (!rule) return null;
    return confirmedVenueRecordByName(rule[1]);
  }

  function eventCanonicalVenueRecords(event) {
    if (event && state.eventVenueRecordCache.has(event)) {
      return state.eventVenueRecordCache.get(event);
    }
    const records = [];
    const seen = new Set();
    const addRecord = registry => {
      if (!registry?.confirmed) return;
      const key = registry.id || cleanPlaceText(registry.name);
      if (!key || seen.has(key)) return;
      seen.add(key);
      records.push(registry);
    };

    [
      event?.publicVenueId,
      event?.venueId,
      ...(event?.venueIds || []),
    ]
      .flatMap(value => stringList(value))
      .forEach(venueId => {
        const registry = state.venueRegistryById?.get(venueId);
        addRecord(registry);
      });

    eventVenueCandidateValues(event).forEach(name => {
      addRecord(venueRegistryRecord(name));
    });
    if (event) state.eventVenueRecordCache.set(event, records);
    return records;
  }

  function eventCanonicalVenueNames(event) {
    // Public venue filters are registry-led. P2 caches the resolved names so
    // repeated homepage, listing and sidebar renders do not rescan registries.
    if (event && state.eventVenueNameCache.has(event)) {
      return state.eventVenueNameCache.get(event);
    }
    const names = eventCanonicalVenueRecords(event)
      .map(record => cleanPlaceText(record.name))
      .filter(Boolean);
    if (event) state.eventVenueNameCache.set(event, names);
    return names;
  }

  function eventRegions(event) {
    if (event && state.eventRegionCache.has(event)) {
      return state.eventRegionCache.get(event);
    }
    const regions = eventCanonicalVenueRecords(event)
      .map(record => normalizeRegion(record.region || ''))
      .filter(region => region && region !== '其他地區');
    const unique = [...new Set(regions)];
    const result = unique.length ? unique : [normalizeRegion(event?.region || '其他地區')];
    if (event) state.eventRegionCache.set(event, result);
    return result;
  }

  const LEGACY_VENUE_TYPE_MAP = {
    museum:'museum_gallery', art_museum:'museum_gallery', gallery:'museum_gallery', exhibition_space:'museum_gallery',
    cultural_park:'cultural_park', cultural_center:'performing_arts', performing_arts_center:'performing_arts',
    concert_hall:'performing_arts', performance_space:'performing_arts', theater:'performing_arts',
    arena:'arena_stadium', stadium:'arena_stadium', sports_center:'arena_stadium',
    live_house:'live_house', cinema:'film_media', film_center:'film_media',
  };

  function inferredVenueType(name, registry = null) {
    const explicit = registry?.venueTypePrimary || registry?.venueTypes?.[0];
    const normalizedExplicit = LEGACY_VENUE_TYPE_MAP[explicit] || explicit;
    if (normalizedExplicit && VENUE_TYPE_LABELS[normalizedExplicit]) return normalizedExplicit;
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
    const registryNormalizedIndex = new Map();
    const registryById = new Map();
    const assignPreferred = (map, key, registry) => {
      if (!key) return;
      const existing = map.get(key);
      if (
        !existing
        || venueRecordPriority(registry)
          > venueRecordPriority(existing)
      ) {
        map.set(key, registry);
      }
    };

    state.venueRegistry.forEach(registry => {
      [
        registry.name,
        ...(registry.aliases || []),
        registry.venueComplexName,
      ].filter(Boolean).forEach(name => {
        assignPreferred(
          registryIndex,
          cleanPlaceText(name),
          registry,
        );
        assignPreferred(
          registryNormalizedIndex,
          normalizedVenueLookupKey(name),
          registry,
        );
      });
      assignPreferred(
        registryById,
        String(registry.id || '').trim(),
        registry,
      );
    });
    state.venueRegistryIndex = registryIndex;
    state.venueRegistryNormalizedIndex = registryNormalizedIndex;
    state.venueRegistryById = registryById;
    state.venueNameMatchCache = new Map();
    state.eventVenueRecordCache = new WeakMap();
    state.eventVenueNameCache = new WeakMap();
    state.eventRegionCache = new WeakMap();

    const coordinateBuckets = new Map();
    state.events.forEach(event => {
      if (!hasCoordinates(event)) return;
      const canonicalNames = eventCanonicalVenueRecords(event).flatMap(record => [
        record.name,
        ...(record.aliases || []),
        record.venueComplexName,
      ]);
      [...eventVenueCandidateValues(event), ...canonicalNames].forEach(value => {
        const key = normalizedVenueLookupKey(value);
        if (!key) return;
        if (!coordinateBuckets.has(key)) coordinateBuckets.set(key, []);
        coordinateBuckets.get(key).push([event.latitude, event.longitude]);
      });
    });
    state.venueRegistry.forEach(registry => {
      const directLatitude = Number(registry.latitude);
      const directLongitude = Number(registry.longitude);
      if (Number.isFinite(directLatitude) && Number.isFinite(directLongitude) && directLatitude !== 0 && directLongitude !== 0) {
        [registry.name, ...(registry.aliases || []), registry.venueComplexName].filter(Boolean).forEach(value => {
          const key = normalizedVenueLookupKey(value);
          if (!key || coordinateBuckets.has(key)) return;
          coordinateBuckets.set(key, [[directLatitude, directLongitude]]);
        });
      }
      const coordinate = cachedCoordinate([
        registry.address,
        `${registry.region || ''}${registry.district || ''}`,
        registry.district,
      ]);
      if (!coordinate) return;
      [registry.name, ...(registry.aliases || []), registry.venueComplexName].filter(Boolean).forEach(value => {
        const key = normalizedVenueLookupKey(value);
        if (!key || coordinateBuckets.has(key)) return;
        coordinateBuckets.set(key, [[coordinate.latitude, coordinate.longitude]]);
      });
    });
    state.venueCoordinateIndex = new Map([...coordinateBuckets].map(([key, coordinates]) => {
      const sortedLat = coordinates.map(item => item[0]).sort((a,b) => a-b);
      const sortedLng = coordinates.map(item => item[1]).sort((a,b) => a-b);
      const middle = Math.floor(coordinates.length / 2);
      return [key, {latitude:sortedLat[middle], longitude:sortedLng[middle]}];
    }));

    state.events.forEach(event => {
      const regions = eventRegions(event);
      if (
        regions.length === 1
        && regions[0] !== '其他地區'
      ) {
        event.region = regions[0];
      }
    });

    const records = new Map();
    const homeVenueEventIndex = new Map();
    state.venueRegistry
      .filter(registry => registry?.confirmed)
      .forEach(registry => {
        const name = displayableVenueName(registry.name);
        const key = cleanPlaceText(name);
        if (!key || records.has(key)) return;
        records.set(key, {
          id: registry.id || name,
          name,
          aliases: registry.aliases || [],
          region: normalizeRegion(
            registry.region || '其他地區'
          ),
          district: registry.district || '',
          venueType: inferredVenueType(name, registry),
          address: usableVenueAddress(registry.address || ''),
          count: 0,
          confirmed: true,
        });
      });

    let matchedEventCount = 0;
    let unmatchedEventCount = 0;
    const unmatchedSamples = [];

    state.events.forEach(event => {
      const canonicalRecords = eventCanonicalVenueRecords(event);
      if (canonicalRecords.length) {
        matchedEventCount += 1;
      } else {
        unmatchedEventCount += 1;
        if (unmatchedSamples.length < 20) {
          unmatchedSamples.push({
            id: event.id,
            title: event.title,
            venueValues: eventVenueCandidateValues(event),
          });
        }
      }

      const seen = new Set();
      canonicalRecords.forEach(registry => {
        if (!registry?.confirmed) return;
        const name = displayableVenueName(registry.name);
        const key = cleanPlaceText(name);
        if (!key || seen.has(key)) return;
        seen.add(key);
        const existing = records.get(key);
        if (!existing) return;
        existing.count += 1;
        if (!existing.address) {
          const eventAddress = usableVenueAddress(event.address || '');
          if (eventAddress) existing.address = eventAddress;
        }
        records.set(key, existing);
        if (!homeVenueEventIndex.has(name)) homeVenueEventIndex.set(name, []);
        homeVenueEventIndex.get(name).push(event);
      });
    });

    state.venueMatchDiagnostics = {
      eventCount: state.events.length,
      matchedEventCount,
      unmatchedEventCount,
      unmatchedSamples,
    };
    window.__venueMatchDiagnostics = state.venueMatchDiagnostics;

    state.homeVenueEventIndex = homeVenueEventIndex;
    state.venueCatalogCache = [...records.values()]
      .sort(
        (a, b) => (
          b.count - a.count
          || a.name.localeCompare(b.name, 'zh-Hant')
        )
      );
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
              const unavailable = item.count === 0;
              return `<button type="button" class="venue-selector-option ${checked ? 'active' : ''} ${unavailable ? 'is-unavailable' : ''}" data-venue-choice="${escapeHtml(item.name)}" aria-pressed="${checked}" ${unavailable ? 'disabled aria-disabled="true"' : ''}>
                <span><strong>${escapeHtml(item.name)}</strong><small>${escapeHtml(VENUE_TYPE_LABELS[item.venueType] || '展演場地')}</small></span>
                <em>${unavailable ? '尚無展演' : `${item.count} 檔`}</em>
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
    window.clearTimeout(state.venueDrawerTimer);
    $('#venueSelectorSearch').value = '';
    $('#venueSelectorBackdrop').hidden = false;
    $('#venueSelectorDrawer').setAttribute('aria-hidden','false');
    document.body.classList.add('venue-selector-open');
    requestAnimationFrame(() => $('#venueSelectorDrawer').classList.add('open'));
    lockViewport('venue-selector');
    renderVenueSelector();
    $('#venueSelectorList').scrollTop = 0;
    setTimeout(() => $('#venueSelectorSearch')?.focus(), 120);
  }

  function closeVenueSelector() {
    window.clearTimeout(state.venueDrawerTimer);
    $('#venueSelectorDrawer').classList.remove('open');
    $('#venueSelectorDrawer').setAttribute('aria-hidden','true');
    document.body.classList.remove('venue-selector-open');
    state.venueDrawerTimer = window.setTimeout(() => {
      if (!$('#venueSelectorDrawer').classList.contains('open')) {
        $('#venueSelectorBackdrop').hidden = true;
      }
    }, window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 20 : 380);
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
    const categoryCounts = countBy(state.events, event => eventCategories(event));
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

  function mobileDrawerTargetOffset(menu,target) {
    if(!menu||!target) return 0;
    const header=menu.querySelector('.mobile-menu-header,.mobile-drawer-header,.mobile-menu-top,header');
    const headerHeight=header?.getBoundingClientRect().height||96;
    const menuRect=menu.getBoundingClientRect();
    const targetRect=target.getBoundingClientRect();
    return Math.max(0,menu.scrollTop+targetRect.top-menuRect.top-headerHeight-20);
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
          top: mobileDrawerTargetOffset(menu, target),
          left: 0,
          behavior: 'auto',
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
    const eventDiscussions = discussionsForEvent(event);
    const detailCategories = eventCategories(event);
    const related = selectFeatured(state.events.filter(item => eventKey(item) !== eventKey(event) && (item.region === event.region || eventCategories(item).some(category => detailCategories.includes(category)))), 10);
    const mapUrl = googleMapsUrl(event);
    const externalUrl = event.sourceUrl || '';
    $('#detailContent').innerHTML = `
      <div class="detail-breadcrumb"><a href="./">首頁</a> / <a href="${categoryHref(detailCategories[0])}">${escapeHtml(detailCategories[0])}</a> / ${escapeHtml(event.title)}</div>
      <div class="detail-grid">
        <div class="detail-poster">${imageMarkup(event, 'detail-poster-placeholder')}</div>
        <article class="detail-info" data-content-type="${escapeHtml(event.contentType || '')}" data-editorial-status="${escapeHtml(event.editorialStatus || '')}" data-venue-coverage="${escapeHtml(event.venueCoverageStatus || '')}">
          <div class="detail-category detail-taxonomy">
            ${detailCategories.map(category => `<a href="${categoryHref(category)}">${escapeHtml(category)}</a>`).join('<span aria-hidden="true">·</span>')}
            <span aria-hidden="true">/</span>
            <a href="${regionHref(event.region)}">${escapeHtml(event.region)}</a>
          </div>
          <h1>${escapeHtml(event.title)}</h1>
          <div class="detail-meta">
            ${detailMeta('展期', dateRange(event))}${detailMeta('地點', event.venueDetail && eventVenueNames(event).length <= 1 ? `${eventVenueLabel(event)}｜${event.venueDetail}` : eventVenueLabel(event, '／'))}${detailMeta('地址', event.address || event.region)}${detailMeta('票價', compactPriceLabel(event.price))}${event.unit ? detailMeta('主辦單位', event.unit) : ''}${event.transitInfo ? detailMeta('交通', event.transitInfo) : ''}
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
      ${eventDiscussions.length ? `<section class="detail-social-discussions"><div class="detail-related-heading"><div><p class="eyebrow">SOCIAL DISCOVERY</p><h2>大家怎麼說</h2><p class="section-description">經人工確認、與這場展覽配對的公開討論。</p></div></div><div class="social-discussions-rail detail-social-rail">${eventDiscussions.map(row => socialDiscussionCardMarkup(row, {compact:true})).join('')}</div></section>` : ''}
      ${related.length ? `<section class="detail-related"><div class="detail-related-heading"><div><p class="eyebrow">YOU MAY ALSO LIKE</p><h2>附近或相似的展覽</h2></div><div class="section-controls" aria-label="切換附近或相似展覽"><button class="icon-button" type="button" data-scroll-target="detailRelatedRail" data-dir="-1" aria-label="向左瀏覽相似展覽">←</button><button class="icon-button" type="button" data-scroll-target="detailRelatedRail" data-dir="1" aria-label="向右瀏覽相似展覽">→</button></div></div><div class="featured-rail detail-related-rail" id="detailRelatedRail">${related.map(cardMarkup).join('')}</div></section>` : ''}`;
  }

  function detailMeta(label, value) { return `<div class="detail-meta-row"><small>${label}</small><strong>${escapeHtml(value || '—')}</strong></div>`; }
  function summaryText(text) { return text.length > 180 ? `${text.slice(0, 180).trim()}…` : text; }

  function hasCoordinates(event) { return Number.isFinite(event.latitude) && Number.isFinite(event.longitude) && event.latitude !== 0 && event.longitude !== 0; }
  function haversine(lat1, lon1, lat2, lon2) {
    const R = 6371, dLat = (lat2-lat1)*Math.PI/180, dLon = (lon2-lon1)*Math.PI/180;
    const a = Math.sin(dLat/2)**2 + Math.cos(lat1*Math.PI/180)*Math.cos(lat2*Math.PI/180)*Math.sin(dLon/2)**2;
    return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
  }
  function addressDistrictKey(value = '') {
    const text = cleanPlaceText(value).replaceAll('臺','台');
    const match = text.match(/((?:台北市|新北市|桃園市|台中市|台南市|高雄市|基隆市|新竹市|嘉義市)[^市縣]{1,5}(?:區|鄉|鎮|市))/);
    return match?.[1] || '';
  }

  function usableVenueAddress(value = '') {
    const text = cleanPlaceText(value);
    if (!text || /場館資料整理中|地點待確認|線上活動|待確認/.test(text)) return '';
    if (/(?:路|街|大道|巷|弄|號|村|里|園區)/.test(text) || /\d/.test(text) && text.length >= 8) return text;
    return '';
  }

  function cachedCoordinate(values = []) {
    for (const rawValue of values) {
      const key = cleanPlaceText(rawValue);
      if (!key) continue;
      const variants = [key, key.replaceAll('臺','台'), key.replaceAll('台','臺')];
      for (const variant of variants) {
        const coordinate = state.geocodeCache[variant];
        if (Array.isArray(coordinate) && coordinate.length >= 2
          && Number.isFinite(Number(coordinate[0])) && Number.isFinite(Number(coordinate[1]))) {
          return {latitude:Number(coordinate[0]), longitude:Number(coordinate[1])};
        }
      }
    }
    return null;
  }

  function eventCoordinates(event) {
    if (hasCoordinates(event)) return {latitude:event.latitude, longitude:event.longitude, precision:'event'};
    for (const value of eventVenueCandidateValues(event)) {
      const coordinate = state.venueCoordinateIndex.get(normalizedVenueLookupKey(value));
      if (coordinate) return {...coordinate, precision:'venue'};
    }
    const districtKey = addressDistrictKey(event.address);
    const coordinate = cachedCoordinate([
      event.address,
      districtKey,
      `${event.region || ''}${event.district || ''}`,
      event.region,
    ]);
    if (coordinate) return {...coordinate, precision:districtKey ? 'district' : 'address'};
    return null;
  }

  function nearestEvents(items, limit = 30, maxDistance = Infinity) {
    const located = items.map(event => {
      const coordinate = eventCoordinates(event);
      if (!coordinate) return null;
      const enriched = {...event, latitude:coordinate.latitude, longitude:coordinate.longitude, _coordinatePrecision:coordinate.precision};
      if (state.userLocation) enriched._distance = haversine(state.userLocation.lat,state.userLocation.lng,coordinate.latitude,coordinate.longitude);
      return enriched;
    }).filter(Boolean);
    if (!state.userLocation) return located.slice(0, limit);
    return located
      .filter(event => event._distance <= maxDistance)
      .sort((a,b) => a._distance-b._distance || recommendationScore(b)-recommendationScore(a))
      .slice(0,limit);
  }

  function venueAddressLabel(venue) {
    const direct = cleanPlaceText(venue?.address || '');
    if (direct && !/場館資料整理中|地點待確認|線上活動/.test(direct)) return direct;
    const district = [venue?.region, venue?.district].map(cleanPlaceText).filter(Boolean).join('');
    return district || '地址請見場館資訊';
  }

  function venueCoordinates(venue) {
    const latitude = Number(venue?.latitude);
    const longitude = Number(venue?.longitude);
    if (Number.isFinite(latitude) && Number.isFinite(longitude) && latitude !== 0 && longitude !== 0) {
      return {latitude, longitude, precision:'registry'};
    }
    const coordinate = state.venueCoordinateIndex.get(normalizedVenueLookupKey(venue?.name || ''));
    return coordinate ? {...coordinate, precision:'venue'} : null;
  }

  function nearestVenues(limit = 200, maxDistance = Infinity) {
    const located = venueCatalog().map(venue => {
      const coordinate = venueCoordinates(venue);
      if (!coordinate) return null;
      const enriched = {...venue, latitude:coordinate.latitude, longitude:coordinate.longitude, _coordinatePrecision:coordinate.precision};
      if (state.userLocation) enriched._distance = haversine(state.userLocation.lat, state.userLocation.lng, coordinate.latitude, coordinate.longitude);
      return enriched;
    }).filter(Boolean);
    if (!state.userLocation) return located.slice(0, limit);
    return located
      .filter(venue => venue._distance <= maxDistance)
      .sort((a,b) => a._distance-b._distance || b.count-a.count || a.name.localeCompare(b.name, 'zh-Hant'))
      .slice(0, limit);
  }

  function ensureLeafletAssets() {
    if (window.L) return Promise.resolve(window.L);
    if (state.leafletAssetsPromise) return state.leafletAssetsPromise;
    state.leafletAssetsPromise = new Promise((resolve, reject) => {
      if (!document.querySelector('link[data-leaflet-runtime]')) {
        const stylesheet = document.createElement('link');
        stylesheet.rel = 'stylesheet';
        stylesheet.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
        stylesheet.dataset.leafletRuntime = 'true';
        document.head.appendChild(stylesheet);
      }
      const existing = document.querySelector('script[data-leaflet-runtime]');
      if (existing) {
        existing.addEventListener('load', () => resolve(window.L), {once:true});
        existing.addEventListener('error', () => reject(new Error('Leaflet 載入失敗')), {once:true});
        return;
      }
      const script = document.createElement('script');
      script.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';
      script.async = true;
      script.dataset.leafletRuntime = 'true';
      script.onload = () => resolve(window.L);
      script.onerror = () => reject(new Error('Leaflet 載入失敗'));
      document.head.appendChild(script);
    });
    return state.leafletAssetsPromise;
  }

  function renderNearby() {
    const items = nearestVenues(200, state.userLocation ? NEARBY_RADIUS_KM : Infinity);
    $('#nearbyStatusText').textContent = state.userLocation
      ? `已定位目前位置，顯示 ${NEARBY_RADIUS_KM} 公里內展場並由近到遠排列。`
      : `正在請求定位權限；允許後會顯示 ${NEARBY_RADIUS_KM} 公里內展場。`;
    $('#nearbyCount').textContent = state.userLocation ? `${items.length} 處・${NEARBY_RADIUS_KM} KM 內` : `${items.length} 處待定位`;
    $('#nearbyResultList').innerHTML = items.map(venue => venueResultMarkup(venue, venue._distance)).join('')
      || emptyInline(state.userLocation ? `目前位置 ${NEARBY_RADIUS_KM} 公里內沒有可定位的展場` : '目前沒有提供座標的展場');
    const map = $('#nearbyMap');
    const token = ++state.nearbyMapRenderToken;
    if (!window.L) {
      map.classList.add('is-map-loading');
      map.innerHTML = '<div class="map-runtime-placeholder"><span>地圖載入中</span><small>展場清單可以先行瀏覽</small></div>';
    }
    ensureLeafletAssets().then(() => {
      if (token !== state.nearbyMapRenderToken || state.view !== 'nearby') return;
      map.classList.remove('is-map-loading');
      map.innerHTML = '';
      renderMap(items);
    }).catch(error => {
      console.warn('[Exhibition Hub] lazy map asset failed', error);
      if (token !== state.nearbyMapRenderToken) return;
      map.classList.remove('is-map-loading');
      map.innerHTML = '<div class="map-runtime-placeholder is-error"><span>地圖暫時無法載入</span><small>仍可使用右側展場清單與外部導航</small></div>';
    });
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
    items.slice(0, 100).forEach(venue => {
      const coordinate = venueCoordinates(venue);
      if (!coordinate) return;
      const marker = L.marker([coordinate.latitude, coordinate.longitude]).addTo(state.map);
      const directionsUrl = googleMapsDirectionsUrlForVenue(venue);
      marker.bindPopup(`<div class="map-popup"><h3>${escapeHtml(venue.name)}</h3><p>${escapeHtml(venueAddressLabel(venue))}</p><p>${Number.isFinite(venue._distance) ? `${venue._distance.toFixed(1)} KM` : ''}</p><div class="map-popup-actions"><a href="${venueHref(venue.name)}">查看場館展覽 →</a>${directionsUrl ? `<a href="${escapeHtml(directionsUrl)}" target="_blank" rel="noopener">外部地圖 ↗</a>` : ''}</div></div>`);
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
      showToast('已依目前位置重新整理附近展場');
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

  function googleMapsDirectionsUrlForVenue(venue) {
    const coordinate = venueCoordinates(venue);
    if (coordinate) {
      return `https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(`${coordinate.latitude},${coordinate.longitude}`)}&travelmode=transit`;
    }
    const query = [venueAddressLabel(venue), venue?.name].filter(Boolean).join(' ');
    return query ? `https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(query)}` : '';
  }

  function renderCurrentView() {
    const previousView = state.lastRenderedView;
    if (previousView === 'home' && state.view !== 'home') cancelHomeHydrationTasks();
    const views = {home:$('#homeView'),listing:$('#listingView'),nearby:$('#nearbyView'),social:$('#socialView'),detail:$('#detailView'),favorites:$('#favoritesView')};
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
    if (state.view === 'social') renderSocialView();
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
      : '尚未取得更新時間';
  }

  function navigateWithFeedback(target, options = {}) {
    if (state.routePending) return false;
    state.routePending = true;
    document.body.classList.add('is-route-pending');
    document.body.setAttribute('aria-busy', 'true');
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        try {
          navigateTo(target, options);
        } finally {
          requestAnimationFrame(() => {
            document.body.classList.remove('is-route-pending');
            document.body.removeAttribute('aria-busy');
            state.routePending = false;
          });
        }
      });
    });
    return true;
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

  // Legacy stagger cap marker: Math.min(index, 5). P2 extends the visible
  // sequence to seven items while keeping the delay bounded.
  function queueScrollReveal(target) {
    if (!target || target.classList.contains('is-in-view')) return;
    const previous = state.revealFrameTokens.get(target);
    if (previous) cancelAnimationFrame(previous);
    const first = requestAnimationFrame(() => {
      const second = requestAnimationFrame(() => {
        target.classList.add('is-in-view');
        state.revealFrameTokens.delete(target);
      });
      state.revealFrameTokens.set(target, second);
    });
    state.revealFrameTokens.set(target, first);
  }

  function queueScrollRevealWhenReady(target) {
    if (!target || target.dataset.revealWaiting === 'true') return;
    const mediaPromise = state.sectionMediaPromises.get(target);
    if (!mediaPromise) {
      queueScrollReveal(target);
      return;
    }
    target.dataset.revealWaiting = 'true';
    Promise.race([mediaPromise, delay(720)]).finally(() => {
      target.dataset.revealWaiting = 'false';
      queueScrollReveal(target);
    });
  }

  function setupScrollReveal() {
    const sequenceGroups = $$('[data-reveal-sequence]');
    sequenceGroups.forEach(group => {
      [...group.children].forEach((child, index) => {
        child.classList.add('reveal-item');
        child.style.setProperty('--reveal-index', Math.min(index, 7));
      });
    });
    const motionGroups = $$('[data-motion-group], .featured-block, .venue-section, #listingGrid');
    motionGroups.forEach(group => {
      const sectionMode = group.dataset.sectionMotion || '';
      const cap = sectionMode === 'nearby' ? 3 : sectionMode === 'venue' ? 7 : 7;
      $$('.motion-card', group).forEach((card, index) => {
        card.style.setProperty('--motion-index', Math.min(index, cap));
      });
    });
    const motionTargets = [...new Set([
      ...sequenceGroups,
      ...$$('[data-motion-group], [data-split-reveal], [data-fade-reveal], #listingGrid'),
    ])];
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      motionTargets.forEach(group => group.classList.add('is-in-view'));
      return;
    }
    if (!state.revealObserver) {
      state.revealObserver = new IntersectionObserver(entries => {
        entries.forEach(entry => {
          if (!entry.isIntersecting) return;
          state.revealObserver.unobserve(entry.target);
          queueScrollRevealWhenReady(entry.target);
        });
      }, {threshold:.08, rootMargin:'0px 0px -3% 0px'});
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
  }

  function replayHomeAnimations() {
    if (state.view !== 'home' || $('#homeView')?.hidden) return;
    requestAnimationFrame(() => setupScrollReveal());
  }

  function bindEvents() {
    let scrollControlFrame = 0;
    const updateScrollControls = () => {
      scrollControlFrame = 0;
      const currentY = window.scrollY || window.pageYOffset || 0;
      const headerScrolled = currentY > 12;
      const backToTopVisible = currentY > Math.max(520, innerHeight * .72);
      if (state.headerScrolledState !== headerScrolled) {
        state.headerScrolledState = headerScrolled;
        $('#siteHeader')?.classList.toggle('scrolled', headerScrolled);
      }
      if (state.backToTopState !== backToTopVisible) {
        state.backToTopState = backToTopVisible;
        $('#backToTopButton')?.classList.toggle('is-visible', backToTopVisible);
      }
    };
    window.addEventListener('scroll', () => {
      if (!scrollControlFrame) scrollControlFrame = requestAnimationFrame(updateScrollControls);
      if (!state.scrollClassActive) {
        state.scrollClassActive = true;
        document.body.classList.add('is-scrolling');
      }
      window.clearTimeout(state.scrollIdleTimer);
      state.scrollIdleTimer = window.setTimeout(() => {
        if (!state.scrollClassActive) return;
        state.scrollClassActive = false;
        document.body.classList.remove('is-scrolling');
      }, 150);
    }, {passive:true});
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
    const fineHeroPointer = () => window.matchMedia('(hover: hover) and (pointer: fine)').matches;
    heroCarousel?.addEventListener('pointerover', event => {
      if (!fineHeroPointer()) return;
      const slide = event.target.closest('.hero-ticket-slide');
      if (!slide || !heroCarousel.contains(slide)) return;
      if (event.relatedTarget && slide.contains(event.relatedTarget)) return;
      activateHeroTicketInteraction(slide);
    });
    heroCarousel?.addEventListener('pointerout', event => {
      if (!fineHeroPointer()) return;
      const slide = event.target.closest('.hero-ticket-slide');
      if (!slide || (event.relatedTarget && slide.contains(event.relatedTarget))) return;
      slide.classList.remove('is-ticket-active');
    });
    heroCarousel?.addEventListener('focusin', event => {
      const slide = event.target.closest('.hero-ticket-slide');
      if (slide) activateHeroTicketInteraction(slide);
    });
    heroCarousel?.addEventListener('focusout', event => {
      const slide = event.target.closest('.hero-ticket-slide');
      if (slide && (!event.relatedTarget || !slide.contains(event.relatedTarget))) {
        slide.classList.remove('is-ticket-active');
      }
    });
    const pauseHero = () => {
      state.heroPaused = true;
      window.clearTimeout(state.heroAutoAdvanceTimer);
    };
    const resumeHero = () => {
      state.heroPaused = false;
      scheduleHeroAutoAdvance();
    };
    heroCarousel?.addEventListener('mouseenter', pauseHero);
    heroCarousel?.addEventListener('mouseleave', resumeHero);
    heroCarousel?.addEventListener('focusin', pauseHero);
    heroCarousel?.addEventListener('focusout', event => {
      if (!heroCarousel.contains(event.relatedTarget)) resumeHero();
    });
    if ('IntersectionObserver' in window && heroCarousel) {
      state.heroVisibilityObserver?.disconnect();
      state.heroVisibilityObserver = new IntersectionObserver(entries => {
        state.heroInView = entries.some(entry => entry.isIntersecting && entry.intersectionRatio > .12);
        if (state.heroInView) scheduleHeroAutoAdvance();
        else window.clearTimeout(state.heroAutoAdvanceTimer);
      }, {threshold:[0,.12,.35]});
      state.heroVisibilityObserver.observe(heroCarousel);
    }
    const mobileHeroSwipeMode = () => window.matchMedia('(max-width: 760px) and (pointer: coarse)').matches;
    const resetHeroSwipe = () => {
      state.heroSwipeStartX = null;
      state.heroSwipeStartY = null;
      state.heroSwipePointerId = null;
      state.heroSwipeTouchId = null;
    };
    const finishHeroSwipe = (clientX, clientY) => {
      if (state.heroSwipeStartX == null || state.heroSwipeStartY == null) return;
      const deltaX = clientX - state.heroSwipeStartX;
      const deltaY = clientY - state.heroSwipeStartY;
      resetHeroSwipe();
      if (Math.abs(deltaX) < 42 || Math.abs(deltaX) < Math.abs(deltaY) * 1.2) return;
      state.heroSwipeBlockClickUntil = performance.now() + 520;
      clearHeroTicketInteraction();
      changeHeroPair(deltaX < 0 ? 1 : -1);
    };
    heroCarousel?.addEventListener('pointerdown', event => {
      if (!mobileHeroSwipeMode() || event.isPrimary === false) return;
      state.heroSwipePointerId = event.pointerId;
      state.heroSwipeStartX = event.clientX;
      state.heroSwipeStartY = event.clientY;
      try { heroCarousel.setPointerCapture(event.pointerId); } catch {}
    }, {passive:true});
    heroCarousel?.addEventListener('pointercancel', resetHeroSwipe);
    heroCarousel?.addEventListener('pointerup', event => {
      if (state.heroSwipePointerId !== null && event.pointerId !== state.heroSwipePointerId) return;
      finishHeroSwipe(event.clientX, event.clientY);
      try { heroCarousel.releasePointerCapture(event.pointerId); } catch {}
    }, {passive:true});
    // iOS/Safari fallback for environments where PointerEvent is incomplete.
    heroCarousel?.addEventListener('touchstart', event => {
      if (!mobileHeroSwipeMode() || window.PointerEvent || event.touches.length !== 1) return;
      const touch = event.touches[0];
      state.heroSwipeTouchId = touch.identifier;
      state.heroSwipeStartX = touch.clientX;
      state.heroSwipeStartY = touch.clientY;
    }, {passive:true});
    heroCarousel?.addEventListener('touchend', event => {
      if (window.PointerEvent || state.heroSwipeTouchId === null) return;
      const touch = [...event.changedTouches].find(item => item.identifier === state.heroSwipeTouchId);
      if (touch) finishHeroSwipe(touch.clientX, touch.clientY);
      else resetHeroSwipe();
    }, {passive:true});
    heroCarousel?.addEventListener('touchcancel', resetHeroSwipe, {passive:true});
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) {
        window.clearTimeout(state.heroAutoAdvanceTimer);
        return;
      }
      if ($('#heroTicketStack')?.children.length) scheduleHeroAutoAdvance();
    });

    $('#datePicker').addEventListener('change', event => {state.date = event.target.value || null; renderHome();});
    $('#filterResultsClear').addEventListener('click', () => {state.status='all';state.date=null;state.categories.clear();renderHome();$('#discover').scrollIntoView({behavior:'smooth',block:'start'});});
    $('#clearFiltersButton').addEventListener('click', () => {state.status='all';state.date=null;state.categories.clear();renderHome();});
    $('#socialSortSelect')?.addEventListener('change', event => {
      state.socialSort = event.target.value === 'latest' ? 'latest' : 'popular';
      renderSocialView();
    });

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
        // A stationary tap follows the link below immediately. Horizontal
        // swipes are still intercepted by heroSwipeBlockClickUntil above.
        clearHeroTicketInteraction();
      }
      const internalLink = event.target.closest('a[href]');
      if (internalLink && !event.defaultPrevented && event.button === 0 && !event.metaKey && !event.ctrlKey && !event.shiftKey && !event.altKey && !internalLink.target && !internalLink.hasAttribute('download')) {
        const url = new URL(internalLink.href, location.href);
        const isSameAppRoute = url.origin === location.origin && url.pathname === location.pathname && !url.hash;
        if (isSameAppRoute) {
          event.preventDefault();
          if (internalLink.closest('#mobileMenu')) closeMobileMenu();
          if (internalLink.matches('.venue-tile') || internalLink.hasAttribute('data-venue-route')) {
            navigateWithFeedback(url.href);
          } else {
            navigateTo(url.href);
          }
          return;
        }
      }
      const wholeCard = event.target.closest('.exhibition-card.is-whole-card-link');
      if (wholeCard && !event.target.closest('a,button,input,select,textarea')) {
        event.preventDefault();
        navigateTo(wholeCard.dataset.cardHref);
        return;
      }
      const socialPlatformButton = event.target.closest('[data-social-platform]');
      if (socialPlatformButton) {
        state.socialPlatform = socialPlatformButton.dataset.socialPlatform || 'all';
        renderSocialView();
        return;
      }
      const scrollButton = event.target.closest('[data-scroll-target]');
      if (scrollButton) {
        event.preventDefault();
        const target = document.getElementById(scrollButton.dataset.scrollTarget);
        if (target) {
          const direction = Number(scrollButton.dataset.dir) || 1;
          const stepRatio = Number(scrollButton.dataset.scrollStep) || .92;
          const distance = Math.max(target.clientWidth * stepRatio, 180);
          const maxLeft = Math.max(0, target.scrollWidth - target.clientWidth);
          const nextLeft = Math.max(0, Math.min(maxLeft, target.scrollLeft + direction * distance));
          target.scrollTo({left:nextLeft, behavior:'smooth'});
        }
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
    document.addEventListener('click', event => {
      if (!event.target.closest('#listingLoadMore')) return;
      state.listingRenderLimit += window.matchMedia('(max-width: 760px)').matches ? 12 : 24;
      renderListing();
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
      {url:'data/exhibitions.curated.json', local:true, enriched:true, curated:true},
      {url:'data/exhibitions.enriched.json', local:true, enriched:true, curated:false},
      {url:'data/exhibitions.json', local:true, enriched:false, curated:false},
      {url:'https://cloud.culture.tw/frontsite/trans/SearchShowAction.do?method=doFindTypeJ&category=all', local:false},
      {url:'https://cloud.culture.tw/frontsite/trans/SearchShowAction.do?method=doFindTypeJOpenApi&category=all', local:false},
    ];
    const failures = [];
    for (const source of sources) {
      try {
        const response = await fetch(source.url, {cache:'no-cache'});
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const payload = await response.json();
        const rawEvents = Array.isArray(payload) ? payload : payload.events || payload.data || payload.result || [];
        if (!Array.isArray(rawEvents) || !rawEvents.length) throw new Error('資料為空');
        return {payload, rawEvents, local:source.local, sourceUrl:source.url, enriched:Boolean(source.enriched), curated:Boolean(source.curated)};
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
      const [{payload, rawEvents, local, sourceUrl, enriched, curated}, venueRegistryResponse, northernMatrixResponse, taiwanMatrixResponse, geocodeCacheResponse, socialResponse] = await Promise.all([
        fetchEventPayload(),
        fetch('data/venues.json', {cache:'no-cache'}).then(response => response.ok ? response.json() : {venues:[]}).catch(() => ({venues:[]})),
        fetch('data/northern_venue_matrix.json', {cache:'no-cache'}).then(response => response.ok ? response.json() : {venues:[]}).catch(() => ({venues:[]})),
        fetch('data/taiwan_venue_matrix.json', {cache:'no-cache'}).then(response => response.ok ? response.json() : {venues:[]}).catch(() => ({venues:[]})),
        fetch('data/geocode-cache.json', {cache:'no-cache'}).then(response => response.ok ? response.json() : {}).catch(() => ({})),
        fetch('data/social_discussions.json', {cache:'no-cache'}).then(response => response.ok ? response.json() : {discussions:[]}).catch(() => ({discussions:[]})),
      ]);
      const stableVenues = Array.isArray(venueRegistryResponse?.venues) ? venueRegistryResponse.venues : [];
      const normalizeMatrixVenues = response => Array.isArray(response?.venues)
        ? response.venues.map(item => ({
            ...item,
            venueTypePrimary:item.venueType,
            venueTypes:[item.venueType],
          }))
        : [];
      const northernVenues = normalizeMatrixVenues(northernMatrixResponse);
      const confirmedTaiwanVenues = normalizeMatrixVenues(taiwanMatrixResponse);
      // Existing stable and northern records remain first so their curated aliases and active status win.
      // The confirmed nationwide matrix then extends coverage to west, south, east and missing northern venues.
      state.venueRegistry = [...stableVenues, ...northernVenues, ...confirmedTaiwanVenues];
      state.geocodeCache = geocodeCacheResponse && typeof geocodeCacheResponse === 'object' ? geocodeCacheResponse : {};
      state.socialDiscussions = Array.isArray(socialResponse?.discussions) ? socialResponse.discussions : [];
      syncSocialNavigation();
      state.updatedAt = payload.updatedAt || payload.updated_at || (!local ? new Date().toISOString() : null);
      state.stats = payload.stats || {};
      state.registryBuild = payload.registryBuild || null;
      state.dataSource = sourceUrl;
      document.documentElement.dataset.eventData = curated ? 'curated' : enriched ? 'enriched' : 'legacy';
      state.venueImages = Object.fromEntries(Object.entries(payload.venueImages || {}).map(([venue, image]) => [venue, safeUrl(image)]).filter(([, image]) => isUsableImageUrl(image)));
      state.events = rawEvents
        .map((event, index) => normalizeEvent(event, index, {trustCanonicalCategories:curated}))
        .filter(event => event.title && eventKey(event) && !isExcludedEvent(event));
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
