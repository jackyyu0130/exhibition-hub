(() => {
  'use strict';

  const CATEGORY_ORDER = ['快閃','美術','攝影','設計','動漫','音樂','表演','舞蹈','講座','市集','商展','電影','親子','其他'];
  const CATEGORY_ICON = {
    '快閃':'✦','美術':'◐','攝影':'□','設計':'◇','動漫':'★','音樂':'♪','表演':'◎','舞蹈':'↝','講座':'⌁','市集':'◌','商展':'▣','電影':'▷','親子':'☀','其他':'＋'
  };
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
    category: null,
    region: null,
    venue: null,
    date: null,
    query: '',
    sort: 'recommended',
    userLocation: null,
    map: null,
    markers: null,
  };

  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];

  function escapeHtml(value = '') {
    return String(value).replace(/[&<>'"]/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[char]));
  }

  function safeUrl(value = '') {
    try {
      const url = new URL(value, location.href);
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
    let categories = Array.isArray(raw) ? raw : raw ? [raw] : [];
    categories = categories.map(String).map(item => item.trim()).filter(Boolean);
    const text = `${title} ${description}`;
    const keywordRules = [
      ['快閃', /快閃|期間限定|popup|pop-up/i], ['攝影', /攝影|影像|photo/i], ['動漫', /動漫|動畫|漫畫|卡通|anime|公仔|角色/i],
      ['設計', /設計|建築|工藝|時尚|design/i], ['舞蹈', /舞蹈|舞作|芭蕾/i], ['音樂', /音樂|演唱會|樂團|concert/i],
      ['表演', /戲劇|劇場|表演|歌劇|馬戲|音樂劇/i], ['講座', /講座|論壇|工作坊|分享會/i], ['市集', /市集|祭典|嘉年華|文創攤位/i],
      ['商展', /展售|博覽會|商展|產業展/i], ['電影', /電影|影展|放映/i], ['親子', /親子|兒童|家庭/i], ['美術', /美術|藝術|繪畫|雕塑|裝置|當代|典藏/i]
    ];
    keywordRules.forEach(([cat, regex]) => { if (regex.test(text) && !categories.includes(cat)) categories.push(cat); });
    if (!categories.length) categories = ['其他'];
    return categories.filter((cat, index, arr) => arr.indexOf(cat) === index).slice(0, 3);
  }

  function normalizeImage(raw) {
    const candidates = [];
    if (Array.isArray(raw)) candidates.push(...raw);
    else if (raw && typeof raw === 'object') candidates.push(raw.url, raw.src, raw.image);
    else candidates.push(raw);
    return candidates.map(item => typeof item === 'string' ? item : '').map(safeUrl).find(Boolean) || '';
  }

  function normalizeEvent(raw, index) {
    const show = Array.isArray(raw.showinfo) ? raw.showinfo[0] || {} : {};
    const title = firstValue(raw.title, raw.titile, raw.name, '未命名展覽');
    const description = firstValue(raw.description, raw.descriptionFilterHtml, raw.comment);
    const address = firstValue(raw.address, raw.location, show.location);
    const venue = firstValue(raw.locationName, raw.venue, show.locationName, address);
    const sourceUrl = firstValue(raw.sourceUrl, raw.sourceWebPromote, raw.webSales, raw.sourceWebSite, raw.url);
    const id = String(firstValue(raw.id, raw.UID, raw.uid, sourceUrl, `${title}-${index}`));
    const rawCategories = firstValue(raw.categories, raw.categoryName, raw.category);
    const image = normalizeImage(firstValue(raw.image, raw.images, raw.imageURL, raw.imageUrl));
    const latitude = Number(firstValue(raw.latitude, raw.lat, show.latitude));
    const longitude = Number(firstValue(raw.longitude, raw.lng, show.longitude));
    const region = normalizeRegion(firstValue(raw.region, address, venue));
    const price = firstValue(raw.price, raw.Price, show.price, raw.discountInfo, raw.onSales === 'N' ? '免費' : '');
    return {
      id, title: String(title).trim(), description: stripHtml(description),
      sourceUrl: safeUrl(sourceUrl), image,
      images: Array.isArray(raw.images) ? raw.images.map(normalizeImage).filter(Boolean) : image ? [image] : [],
      categories: normalizeCategories(rawCategories, title, description),
      category: normalizeCategories(rawCategories, title, description)[0],
      startDate: firstValue(raw.startDate, raw.start, show.time),
      endDate: firstValue(raw.endDate, raw.end, raw.endTime, show.endTime, raw.startDate),
      locationName: String(venue || '地點待確認').trim(),
      location: String(venue || '地點待確認').trim(), address: String(address || '').trim(), region,
      latitude: Number.isFinite(latitude) && Math.abs(latitude) <= 90 ? latitude : null,
      longitude: Number.isFinite(longitude) && Math.abs(longitude) <= 180 ? longitude : null,
      price: String(price || '票價請見活動頁面').trim(),
      unit: Array.isArray(raw.masterUnit) ? raw.masterUnit.join('、') : firstValue(raw.unit, raw.organizer, raw.showUnit, raw.masterUnit),
      transitInfo: firstValue(raw.transitInfo, raw.transit),
      hitRate: Number(raw.hitRate || 0),
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
    if (!event.image) return `<div class="${className || 'card-placeholder'}">${escapeHtml(CATEGORY_ICON[event.category] || '展')}</div>`;
    return `<img src="${escapeHtml(event.image)}" alt="${escapeHtml(event.title)}" loading="lazy" onerror="this.replaceWith(Object.assign(document.createElement('div'),{className:'${className || 'card-placeholder'}',textContent:'${escapeHtml(CATEGORY_ICON[event.category] || '展')}'}))">`;
  }

  function cardBadge(event) {
    if (isEnding(event)) return '即將結束';
    if (isUpcoming(event)) return '即將開展';
    if (isFree(event)) return '免費入場';
    return '本週精選';
  }

  function cardMarkup(event) {
    return `
      <article class="exhibition-card">
        <a class="card-image" href="${eventHref(event)}">
          ${imageMarkup(event)}
          <span class="card-badge">${cardBadge(event)}</span>
        </a>
        <button class="favorite-button ${isFavorite(event) ? 'active' : ''}" type="button" data-favorite="${escapeHtml(eventKey(event))}" aria-label="${isFavorite(event) ? '取消收藏' : '加入收藏'}">${isFavorite(event) ? '♥' : '♡'}</button>
        <div class="card-body">
          <div class="card-kicker"><span>${escapeHtml(event.categories[0] || '展覽')}</span><span>${escapeHtml(event.region)}</span></div>
          <a href="${eventHref(event)}"><h3 class="card-title">${escapeHtml(event.title)}</h3></a>
          <div class="card-meta"><span>${escapeHtml(dateRange(event))}</span><span>${escapeHtml(event.locationName)}</span></div>
          <div class="card-price ${isFree(event) ? 'free' : ''}">${escapeHtml(event.price)}</div>
        </div>
      </article>`;
  }

  function compactMarkup(event) {
    const date = compactDate(event);
    return `<a class="compact-item" href="${eventHref(event)}">
      <div class="compact-date"><strong>${date.day}</strong><span>${date.month}</span></div>
      <div class="compact-info"><h4>${escapeHtml(event.title)}</h4><p>${escapeHtml(event.locationName)} · ${escapeHtml(event.region)}</p></div>
      <span class="compact-arrow">↗</span>
    </a>`;
  }

  function nearbyMiniMarkup(event, distance = null) {
    return `<a class="nearby-mini-card" href="${eventHref(event)}">
      ${imageMarkup(event, 'nearby-mini-media')}
      <div class="nearby-mini-body"><small>${distance === null ? escapeHtml(event.region) : `${distance.toFixed(1)} KM`}</small><h3>${escapeHtml(event.title)}</h3><p>${escapeHtml(event.locationName)}</p></div>
    </a>`;
  }

  function resultMarkup(event, distance) {
    return `<a class="nearby-result-card" href="${eventHref(event)}">
      ${imageMarkup(event, 'nearby-result-media')}
      <div><small>${Number.isFinite(distance) ? `${distance.toFixed(1)} KM` : escapeHtml(event.region)}</small><h3>${escapeHtml(event.title)}</h3><p>${escapeHtml(dateRange(event))}</p><p>${escapeHtml(event.locationName)}</p></div>
    </a>`;
  }

  function readParams() {
    const params = state.params;
    state.query = params.get('q') || '';
    state.category = params.get('category') || null;
    state.region = params.get('region') || null;
    state.venue = params.get('venue') || null;
    state.status = params.get('status') || 'all';
    state.date = params.get('date') || null;
    if (params.has('event')) state.view = 'detail';
    else if (params.get('view') === 'nearby') state.view = 'nearby';
    else if (params.get('view') === 'favorites') state.view = 'favorites';
    else if (params.get('view') === 'all' || state.query || state.category || state.region || state.venue || params.has('status')) state.view = 'listing';
    else state.view = 'home';
  }

  function filterEvents(items = state.events) {
    const query = state.query.trim().toLowerCase();
    return items.filter(event => {
      if (query) {
        const haystack = [event.title,event.description,event.locationName,event.address,event.region,event.categories.join(' '),event.price].join(' ').toLowerCase();
        if (!haystack.includes(query)) return false;
      }
      if (state.category && !event.categories.includes(state.category)) return false;
      if (state.region && event.region !== state.region) return false;
      if (state.venue && event.locationName !== state.venue) return false;
      if (state.status === 'ongoing' && !isOngoing(event)) return false;
      if (state.status === 'upcoming' && !isUpcoming(event)) return false;
      if (state.status === 'ending' && !isEnding(event, 30)) return false;
      if (state.status === 'free' && !isFree(event)) return false;
      if (state.date) {
        const selected = dateOnly(new Date(`${state.date}T00:00:00`));
        const start = parseDate(event.startDate);
        const end = parseDate(event.endDate);
        if (start && selected < dateOnly(start)) return false;
        if (end && selected > dateOnly(end)) return false;
      }
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

  function renderHome() {
    const pool = filterEvents();
    const ongoing = state.events.filter(isOngoing);
    const featured = selectFeatured(pool.length ? pool : ongoing, 9);
    const upcoming = state.events.filter(isUpcoming).sort((a,b) => (parseDate(a.startDate) || Infinity) - (parseDate(b.startDate) || Infinity)).slice(0, 4);
    const ending = state.events.filter(event => isEnding(event, 30)).sort((a,b) => (parseDate(a.endDate) || Infinity) - (parseDate(b.endDate) || Infinity)).slice(0, 4);

    $('#heroEventCount').textContent = state.events.length.toLocaleString('zh-TW');
    $('#heroVenueCount').textContent = new Set(state.events.map(event => event.locationName).filter(Boolean)).size.toLocaleString('zh-TW');

    const heroPick = featured[0] || state.events[0];
    if (heroPick) {
      $('#heroTicketTitle').textContent = heroPick.title;
      $('#heroTicketMeta').textContent = `${dateRange(heroPick)} · ${heroPick.locationName}`;
      $('#heroTicket').onclick = () => location.href = eventHref(heroPick);
    }

    renderCategoryStrip();
    $('#featuredRail').innerHTML = featured.length ? featured.map(cardMarkup).join('') : emptyInline('目前沒有符合篩選的展覽');
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
      <a class="category-chip ${state.category === category ? 'active' : ''}" href="${categoryHref(category)}">
        <span class="category-icon">${CATEGORY_ICON[category] || '＋'}</span>
        <strong>${escapeHtml(category)}</strong><small>${counts[category]} 檔</small>
      </a>`).join('');
  }

  function renderVenueGrid() {
    const counts = countBy(state.events, event => event.locationName);
    const venues = Object.keys(counts).filter(Boolean).sort((a,b) => counts[b] - counts[a]).slice(0, 7);
    $('#venueGrid').innerHTML = venues.map((venue, index) => {
      const image = state.venueImages[venue] || state.events.find(event => event.locationName === venue && event.image)?.image || '';
      return `<a class="venue-tile" href="${venueHref(venue)}">
        ${image ? `<img src="${escapeHtml(image)}" alt="${escapeHtml(venue)}" loading="lazy">` : ''}
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
    let items = sortEvents(filterEvents());
    const titleParts = [];
    if (state.query) titleParts.push(`「${state.query}」`);
    if (state.category) titleParts.push(state.category);
    if (state.region) titleParts.push(state.region);
    if (state.venue) titleParts.push(state.venue);
    $('#listingTitle').textContent = titleParts.length ? titleParts.join(' · ') : '探索全台展覽';
    $('#listingEyebrow').textContent = state.query ? 'SEARCH RESULTS' : 'EXPLORE EXHIBITIONS';
    $('#listingDescription').textContent = state.query ? '以下是符合搜尋關鍵字與篩選條件的結果。' : '依分類、地區、日期與舉辦狀態，找到適合你的展覽。';
    $('#listingCount').textContent = `找到 ${items.length.toLocaleString('zh-TW')} 檔展覽`;
    $('#listingGrid').innerHTML = items.map(cardMarkup).join('');
    $('#listingEmpty').hidden = items.length !== 0;
    $('#listingDatePicker').value = state.date || '';
    $('#sortSelect').value = state.sort;
    renderSidebarOptions();
    renderActiveFilters();
  }

  function renderSidebarOptions() {
    const statusOptions = [['all','全部展覽'],['ongoing','目前舉辦'],['upcoming','即將舉辦'],['ending','即將結束'],['free','免費展覽']];
    $('#listingStatusOptions').innerHTML = statusOptions.map(([value,label]) => `<button class="vertical-option ${state.status === value ? 'active' : ''}" data-set-filter="status" data-value="${value}"><span>${label}</span><span></span></button>`).join('');
    const categoryCounts = countBy(state.events, event => event.categories);
    $('#listingCategoryOptions').innerHTML = Object.keys(categoryCounts).sort((a,b) => (CATEGORY_ORDER.indexOf(a)+1 || 99) - (CATEGORY_ORDER.indexOf(b)+1 || 99)).map(category => `<button class="vertical-option ${state.category === category ? 'active' : ''}" data-set-filter="category" data-value="${escapeHtml(category)}"><span>${escapeHtml(category)}</span><span>${categoryCounts[category]}</span></button>`).join('');
    const regionCounts = countBy(state.events, event => event.region);
    $('#listingRegionOptions').innerHTML = REGION_ORDER.filter(region => regionCounts[region]).map(region => `<button class="vertical-option ${state.region === region ? 'active' : ''}" data-set-filter="region" data-value="${escapeHtml(region)}"><span>${escapeHtml(region)}</span><span>${regionCounts[region]}</span></button>`).join('');
  }

  function renderActiveFilters() {
    const filters = [];
    if (state.query) filters.push(['q', `搜尋：${state.query}`]);
    if (state.category) filters.push(['category', state.category]);
    if (state.region) filters.push(['region', state.region]);
    if (state.venue) filters.push(['venue', state.venue]);
    if (state.status !== 'all') filters.push(['status', {ongoing:'目前舉辦',upcoming:'即將舉辦',ending:'即將結束',free:'免費展覽'}[state.status] || state.status]);
    if (state.date) filters.push(['date', state.date]);
    $('#activeFilters').innerHTML = filters.map(([key,label]) => `<span class="active-filter">${escapeHtml(label)}<button type="button" data-clear-filter="${key}" aria-label="移除篩選">×</button></span>`).join('');
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
        <div class="detail-poster">${event.image ? `<img src="${escapeHtml(event.image)}" alt="${escapeHtml(event.title)}">` : `<div class="detail-poster-placeholder">${CATEGORY_ICON[event.category] || '展'}</div>`}</div>
        <article class="detail-info">
          <div class="detail-category">${escapeHtml(event.categories.join(' · '))} / ${escapeHtml(event.region)}</div>
          <h1>${escapeHtml(event.title)}</h1>
          <p class="detail-summary">${escapeHtml(summaryText(event.description) || `${event.locationName}舉辦中的展覽，詳細資訊請見活動官方頁面。`)}</p>
          <div class="detail-meta">
            ${detailMeta('展期', dateRange(event))}${detailMeta('地點', event.locationName)}${detailMeta('地址', event.address || event.region)}${detailMeta('票價', event.price)}${event.unit ? detailMeta('主辦單位', event.unit) : ''}${event.transitInfo ? detailMeta('交通', event.transitInfo) : ''}
          </div>
          <div class="detail-actions">
            <a class="primary" href="${escapeHtml(externalUrl)}" target="_blank" rel="noopener">查看官方資訊 ↗</a>
            <a href="${escapeHtml(googleMapsUrl(event))}" target="_blank" rel="noopener">地圖導航</a>
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
      marker.bindPopup(`<div class="map-popup"><h3>${escapeHtml(event.title)}</h3><p>${escapeHtml(event.locationName)}</p><p>${escapeHtml(dateRange(event))}</p><a href="${eventHref(event)}">查看展覽 →</a></div>`);
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
      if (value === null || value === '' || value === 'all') params.delete(key); else params.set(key,value);
    });
    params.delete('event');
    location.href = `?${params.toString()}`;
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

    $('#datePicker').addEventListener('change', event => {state.date = event.target.value || null; renderHome();});
    $('#clearFiltersButton').addEventListener('click', () => {state.status='all';state.date=null;state.category=null;renderHome();});
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
      const filterButton = event.target.closest('[data-set-filter]');
      if (filterButton) updateUrl({[filterButton.dataset.setFilter]:filterButton.dataset.value});
      const clearButton = event.target.closest('[data-clear-filter]');
      if (clearButton) updateUrl({[clearButton.dataset.clearFilter]:null});
    });

    $('#listingDatePicker').addEventListener('change', event => updateUrl({date:event.target.value || null}));
    $('#sidebarClearDate').addEventListener('click', () => updateUrl({date:null}));
    $('#sortSelect').addEventListener('change', event => {state.sort=event.target.value;renderListing();});
    $('#filterDrawerButton').addEventListener('click', () => $('#filterSidebar').classList.toggle('open'));
    $('#homeLocationButton').addEventListener('click', requestLocation);
    $('#nearbyLocationButton').addEventListener('click', requestLocation);
  }

  async function shareEvent(event) {
    const data = {title:event.title,text:`${event.title}｜${dateRange(event)}｜${event.locationName}`,url:new URL(eventHref(event),location.href).href};
    try {
      if (navigator.share) await navigator.share(data);
      else { await navigator.clipboard.writeText(data.url); showToast('連結已複製'); }
    } catch (error) { if (error.name !== 'AbortError') showToast('暫時無法分享'); }
  }

  async function loadData() {
    readParams();
    bindEvents();
    try {
      const response = await fetch('data/exhibitions.json', {cache:'no-store'});
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const payload = await response.json();
      state.updatedAt = payload.updatedAt || payload.updated_at || null;
      state.venueImages = payload.venueImages || {};
      const rawEvents = Array.isArray(payload) ? payload : payload.events || [];
      state.events = rawEvents.map(normalizeEvent).filter(event => event.title && eventKey(event));
      renderCurrentView();
    } catch (error) {
      console.error(error);
      $('#loadingView').hidden = true;
      $('#errorView').hidden = false;
    }
  }

  loadData();
})();
