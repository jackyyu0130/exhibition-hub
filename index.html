<!DOCTYPE html>
<html lang="zh-Hant-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>台灣展覽誌｜全台藝文活動每日自動更新</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+TC:wght@700;900&family=Noto+Sans+TC:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
  :root{
    --brand: #4F46E5;
    --brand-dark: #3730A3;
    --ink: #1A1A2E;
    --ink-soft: #6B7280;
    --bg: #F7F8FB;
    --card: #FFFFFF;
    --line: #E7E7F0;
    --hot: #F43F5E;
    --closing: #F59E0B;
    --new: #6366F1;
    --radius: 14px;
  }

  *{ box-sizing:border-box; }
  body{
    margin:0;
    background: var(--bg);
    color: var(--ink);
    font-family: "Noto Sans TC", sans-serif;
    -webkit-font-smoothing:antialiased;
  }
  a{ color:inherit; text-decoration:none; }
  button{ font-family:inherit; cursor:pointer; }

  /* ---------- 導覽列 ---------- */
  .nav{
    position: sticky; top:0; z-index: 40;
    background: rgba(255,255,255,.92);
    backdrop-filter: blur(8px);
    border-bottom: 1px solid var(--line);
  }
  .nav-inner{
    max-width: 1180px; margin:0 auto;
    padding: .9rem 1.5rem;
    display:flex; align-items:center; gap: 1.8rem;
  }
  .brand{ display:flex; align-items:center; gap:.55rem; font-weight:700; font-size:1.05rem; flex-shrink:0; }
  .brand-mark{
    width:32px; height:32px; border-radius:9px;
    background: linear-gradient(135deg, var(--brand), #8B5CF6);
    display:flex; align-items:center; justify-content:center;
    color:#fff; font-size:1.05rem; transform: rotate(-6deg);
  }
  .brand-sub{ display:block; font-size:.68rem; font-weight:400; color:var(--ink-soft); margin-top:1px; }

  .nav-links{ display:flex; align-items:center; gap:1.4rem; font-size:.92rem; color:var(--ink-soft); position:relative; }
  .nav-links a, .nav-links button.nav-item{
    background:none; border:none; padding:.4rem 0; color:var(--ink-soft); font-size:.92rem;
  }
  .nav-links a:hover, .nav-links button.nav-item:hover{ color:var(--ink); }

  .nav-spacer{ flex:1; }
  .nav-count{
    font-size:.8rem; color:var(--ink-soft);
    background: var(--bg); border:1px solid var(--line);
    padding:.35rem .75rem; border-radius:999px;
    white-space:nowrap;
  }

  /* 下拉篩選面板（地區／分類共用樣式）*/
  .dropdown-wrap{ position:relative; }
  .dropdown-panel{
    position:absolute; top: calc(100% + 10px); left:0;
    background:#fff; border:1px solid var(--line); border-radius: 10px;
    box-shadow: 0 16px 40px rgba(20,20,40,.12);
    padding: .9rem; width: 240px;
    display:none; max-height: 340px; overflow-y:auto; z-index: 50;
  }
  .dropdown-panel.open{ display:block; }
  .dropdown-panel .opt{
    display:flex; align-items:center; gap:.55rem;
    font-size:.87rem; padding:.32rem 0; color:var(--ink);
  }
  .dropdown-panel .opt input{ accent-color:var(--brand); width:15px; height:15px; }
  .dropdown-panel .opt .c{ margin-left:auto; font-size:.72rem; color:var(--ink-soft); }
  .dropdown-clear{ font-size:.75rem; color:var(--brand); background:none; border:none; margin-bottom:.5rem; padding:0; }

  /* ---------- Hero ---------- */
  .hero{
    position:relative;
    padding: 4.2rem 1.5rem 2.6rem;
    text-align:center;
    overflow:hidden;
    background:
      radial-gradient(60% 90% at 15% -10%, rgba(139,92,246,.22), transparent),
      radial-gradient(50% 80% at 90% 10%, rgba(79,70,229,.18), transparent),
      linear-gradient(180deg, #EEF0FF 0%, var(--bg) 85%);
  }
  .hero h1{
    font-family:"Noto Serif TC", serif;
    font-weight:900;
    font-size: clamp(1.9rem, 4.4vw, 2.7rem);
    line-height:1.35;
    margin: 0 0 .7rem;
    position:relative;
  }
  .hero p.tagline{
    color:var(--ink-soft); font-size:1rem; margin:0 0 2rem; position:relative;
  }

  .search-bar{
    max-width: 640px; margin:0 auto; position:relative;
    background:#fff; border:1px solid var(--line); border-radius: 999px;
    padding: .5rem .5rem .5rem 1.2rem;
    display:flex; align-items:center; gap:.5rem;
    box-shadow: 0 14px 34px rgba(30,20,70,.08);
  }
  .search-bar svg{ flex-shrink:0; color: var(--ink-soft); }
  #searchInput{
    flex:1; border:none; outline:none; font-size:.95rem; font-family:inherit;
    background:transparent; padding:.5rem 0; color:var(--ink);
  }
  .locate-btn{
    display:flex; align-items:center; gap:.4rem;
    background: var(--ink); color:#fff; border:none;
    border-radius:999px; padding:.6rem 1.1rem; font-size:.85rem; font-weight:500;
    white-space:nowrap;
  }
  .locate-btn:hover{ background: var(--brand); }
  .locate-btn.active{ background: var(--brand); }

  /* 進行中／未來舉辦 狀態切換 */
  .status-toggle{ display:flex; gap:.5rem; flex-wrap:wrap; justify-content:center; }
  .status-btn{
    border:1px solid var(--line); background:#fff; color:var(--ink-soft);
    padding:.5rem 1.1rem; border-radius:999px; font-size:.85rem;
  }
  .status-btn.active{ background:var(--ink); color:#fff; border-color:var(--ink); }

  .hero .status-toggle{ margin-top: 1.4rem; }

  /* ---------- 分類圖示列 ---------- */
  .cat-row{
    max-width: 1180px; margin: 2rem auto 0; padding: 0 1.5rem;
    display:flex; gap: 1.6rem; flex-wrap:wrap; justify-content:center;
    position:relative;
  }
  .cat-chip{
    display:flex; flex-direction:column; align-items:center; gap:.5rem;
    background:none; border:none; color: var(--ink-soft); width: 76px;
  }
  .cat-chip .icon-circle{
    width:56px; height:56px; border-radius:50%;
    background:#fff; border:1px solid var(--line);
    display:flex; align-items:center; justify-content:center;
    color: var(--ink); transition: all .15s ease;
  }
  .cat-chip span.label{ font-size:.78rem; }
  .cat-chip:hover .icon-circle{ border-color: var(--brand); color:var(--brand); }
  .cat-chip.active .icon-circle{ background: var(--brand); border-color:var(--brand); color:#fff; }
  .cat-chip.active span.label{ color:var(--brand); font-weight:600; }

  /* ---------- 主內容 ---------- */
  main{ max-width:1180px; margin:0 auto; padding: 2.4rem 1.5rem 5rem; }

  /* 分類卡片列（首頁）*/
  .cat-section{ margin-bottom: 2.6rem; }
  .cat-section-head{
    display:flex; align-items:center; justify-content:space-between; margin-bottom:1rem;
  }
  .cat-section-head h2{
    font-size:1.15rem; margin:0; display:flex; align-items:center; gap:.6rem;
  }
  .cat-section-head .icon-sm{
    width:30px; height:30px; border-radius:50%; background:var(--bg);
    display:flex; align-items:center; justify-content:center; color:var(--brand); flex-shrink:0;
  }
  .cat-section-head .icon-sm svg{ width:16px; height:16px; }
  .row-controls{ display:flex; gap:.4rem; }
  .row-nav{
    width:32px; height:32px; border-radius:50%; border:1px solid var(--line);
    background:#fff; display:flex; align-items:center; justify-content:center; color:var(--ink-soft);
  }
  .row-nav:hover{ border-color:var(--brand); color:var(--brand); }

  .carousel{
    display:grid; grid-auto-flow:column; grid-auto-columns: calc((100% - 3*1.3rem)/4);
    gap:1.3rem; overflow-x:auto; scroll-snap-type:x proximity; padding-bottom:.5rem;
  }
  .carousel .card{ scroll-snap-align:start; }
  @media (max-width:1020px){ .carousel{ grid-auto-columns: calc((100% - 2*1.3rem)/3); } }
  @media (max-width:760px){ .carousel{ grid-auto-columns: calc((100% - 1.3rem)/2); } }
  @media (max-width:520px){ .carousel{ grid-auto-columns: 78%; } }

  .show-more-row{ text-align:center; margin-top:1.1rem; }
  .show-more-btn{
    display:inline-block; border:1px solid var(--brand); color:var(--brand); background:#fff;
    padding:.55rem 1.3rem; border-radius:999px; font-size:.85rem; font-weight:600;
  }
  .show-more-btn:hover{ background:var(--brand); color:#fff; }

  .back-link{ display:inline-block; margin-bottom:1.2rem; font-size:.85rem; color:var(--brand); font-weight:600; }

  .section-head{
    display:flex; align-items:center; justify-content:space-between; margin-bottom:1.2rem;
  }
  .section-head h2{ font-size:1.3rem; margin:0; }
  .section-head .hint{ font-size:.85rem; color:var(--ink-soft); }

  .grid{
    display:grid; grid-template-columns: repeat(4, 1fr); gap: 1.3rem;
  }
  @media (max-width: 1020px){ .grid{ grid-template-columns: repeat(3,1fr); } }
  @media (max-width: 760px){ .grid{ grid-template-columns: repeat(2,1fr); } }
  @media (max-width: 480px){ .grid{ grid-template-columns: 1fr; } }

  .card{
    background: var(--card); border:1px solid var(--line); border-radius: var(--radius);
    overflow:hidden; display:block; transition: transform .15s ease, box-shadow .15s ease;
  }
  a.card:hover{ transform: translateY(-3px); box-shadow: 0 16px 34px rgba(20,20,50,.1); }

  .card-media{
    aspect-ratio: 4 / 3; position:relative; overflow:hidden;
    display:flex; align-items:center; justify-content:center; color:#fff;
  }
  .card-media img{ position:absolute; inset:0; width:100%; height:100%; object-fit:cover; }
  .card-media .icon-wrap{ position:relative; z-index:0; }
  .card-badge{
    position:absolute; top:.6rem; left:.6rem;
    font-size:.68rem; font-weight:700; color:#fff;
    padding:.22rem .6rem; border-radius:999px;
  }
  .card-badge.closing{ background: var(--closing); }
  .card-badge.new{ background: var(--new); }

  .card-body{ padding: .9rem 1rem 1.05rem; }
  .card-cat{ font-size:.72rem; color:var(--brand); font-weight:600; margin-bottom:.3rem; }
  .card-title{
    font-size: .98rem; font-weight:700; line-height:1.4; margin:0 0 .45rem;
    display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden;
    min-height: 2.7em;
  }
  .card-meta{ font-size:.8rem; color:var(--ink-soft); line-height:1.6; }
  .card-meta .loc{ display:block; }
  .card-dist{ font-size:.78rem; color:var(--brand); font-weight:600; margin-top:.35rem; }

  .empty{
    text-align:center; padding: 3.5rem 1rem;
    color: var(--ink-soft); font-family:"Noto Serif TC", serif; font-size:1.05rem;
  }
  .grid .empty, .carousel .empty{ grid-column: 1 / -1; }

  .scroll-row{
    display:flex; gap: 1.1rem; overflow-x:auto; padding-bottom: .6rem;
    scroll-snap-type: x proximity;
  }
  .scroll-row .card{ flex: 0 0 220px; scroll-snap-align:start; }

  #mapContainer{
    height: 380px; border-radius: var(--radius);
    border:1px solid var(--line); overflow:hidden;
    background:#fff;
  }
  .map-popup{ font-family:"Noto Sans TC", sans-serif; }
  .map-popup h4{ margin:0 0 .3rem; font-size:.95rem; }
  .map-popup p{ margin:0 0 .3rem; font-size:.8rem; color:var(--ink-soft); }
  .map-popup a{ font-size:.8rem; color:var(--brand); font-weight:600; }

  .gmap-key-notice{
    height:100%; display:flex; flex-direction:column; align-items:center; justify-content:center;
    gap:.7rem; color:var(--ink-soft); text-align:center; padding:2rem;
  }
  .gmap-key-notice code{ background:var(--bg); padding:.2rem .5rem; border-radius:4px; font-size:.82rem; }

  footer{
    text-align:center; padding: 2.2rem 1.5rem 3rem;
    font-size:.8rem; color:var(--ink-soft);
    border-top:1px solid var(--line);
  }

  :focus-visible{ outline:2px solid var(--brand); outline-offset:2px; }
</style>
</head>
<body>

<header class="nav">
  <div class="nav-inner">
    <div class="brand">
      <span class="brand-mark">展</span>
      <span>台灣展覽誌<span class="brand-sub">全台藝文活動平台</span></span>
    </div>
    <nav class="nav-links">
      <a href="./">首頁</a>
      <div class="dropdown-wrap">
        <button class="nav-item" id="categoryNavBtn">分類 ▾</button>
        <div class="dropdown-panel" id="categoryPanel">
          <button class="dropdown-clear" data-clear="category">清除已選分類</button>
          <div id="categoryOptions"></div>
        </div>
      </div>
      <div class="dropdown-wrap">
        <button class="nav-item" id="regionNavBtn">地區 ▾</button>
        <div class="dropdown-panel" id="regionPanel">
          <button class="dropdown-clear" data-clear="region">清除已選地區</button>
          <div id="regionOptions"></div>
        </div>
      </div>
      <a href="#nearby">附近展覽</a>
    </nav>
    <div class="nav-spacer"></div>
    <span class="nav-count" id="navCount">載入中…</span>
  </div>
</header>

<section class="hero" id="top">
  <h1>探索全台精彩展覽<br>發現城市的文化與創意</h1>
  <p class="tagline">彙整文化部開放資料與各大展演場館資訊，每日自動更新</p>
  <div class="search-bar">
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
    <input type="text" id="searchInput" placeholder="搜尋展覽、地點、關鍵字…">
    <button class="locate-btn" id="locateBtn" type="button">
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3"/></svg>
      目前位置
    </button>
  </div>

  <div class="status-toggle" id="statusToggle">
    <button class="status-btn active" data-status="all" type="button">全部</button>
    <button class="status-btn" data-status="ongoing" type="button">目前舉辦</button>
    <button class="status-btn" data-status="upcoming" type="button">即將舉辦</button>
  </div>

  <div class="cat-row" id="catRow"></div>
</section>

<main>
  <div id="homepageRows"></div>

  <div id="detailView" style="display:none;">
    <a class="back-link" href="./">← 回首頁</a>
    <div class="section-head">
      <h2 id="detailTitle"></h2>
      <span class="hint" id="detailHint"></span>
    </div>
    <div class="grid" id="detailGrid"></div>
  </div>

  <section class="section" id="mapSection" style="margin-top:2.6rem;">
    <div class="section-head">
      <h2>地圖檢視</h2>
      <span class="hint">依目前的篩選條件顯示地點</span>
    </div>
    <div id="mapContainer"></div>
  </section>

  <section class="section" id="nearby" style="display:none; margin-top:2.6rem;">
    <div class="section-head">
      <h2>附近展覽</h2>
      <span class="hint">依你目前位置，由近到遠排序</span>
    </div>
    <div class="scroll-row" id="nearbyRow"></div>
  </section>
</main>

<footer>
  資料來源：文化部文化資料開放服務網（cloud.culture.tw）、華山1914文化創意產業園區 · 每日自動更新
</footer>

<script>
const state = {
  events: [],
  updatedAt: null,
  selectedRegions: new Set(),
  selectedCategories: new Set(),
  userLoc: null,
  statusFilter: 'all',
  detailCategory: null,
  lastPool: [],
  map: null,
  markers: [],
};

// 地區顯示順序：北到南，接著中部，再來東部與離島
const REGION_ORDER = [
  '台北市','新北市','基隆市','桃園市','新竹市','新竹縣',
  '台南市','高雄市','屏東縣',
  '台中市','彰化縣','南投縣','雲林縣','嘉義市','嘉義縣',
  '苗栗縣','宜蘭縣','花蓮縣','台東縣','澎湖縣','金門縣','連江縣',
  '其他地區',
];

const REGION_GROUPS = [
  ['台北市','臺北市'], ['新北市'], ['基隆市'], ['桃園市'],
  ['新竹市'], ['新竹縣'], ['苗栗縣'], ['台中市','臺中市'],
  ['彰化縣'], ['南投縣'], ['雲林縣'], ['嘉義市'], ['嘉義縣'],
  ['台南市','臺南市'], ['高雄市'], ['屏東縣'], ['宜蘭縣'],
  ['花蓮縣'], ['台東縣','臺東縣'], ['澎湖縣'], ['金門縣'], ['連江縣'],
];

// 首頁分類區塊的顯示順序
const CATEGORY_ORDER = ['音樂','美術','動漫','表演','舞蹈','攝影','設計','講座','市集','其他'];

const CATEGORY_ICON_MAP = {
  '音樂': 'music', '美術': 'palette', '動漫': 'anime', '表演': 'masks',
  '舞蹈': 'dance', '攝影': 'camera', '設計': 'design', '講座': 'mic',
  '市集': 'bag', '其他': 'ticket',
};

const ICONS = {
  palette: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M12 2a10 10 0 1 0 0 20c1.5 0 2-1 2-2s-.5-1.5-.5-2 1-1.5 2-1.5H17a4 4 0 0 0 4-4c0-5.5-4.5-10-9-10Z"/><circle cx="7.5" cy="10.5" r="1"/><circle cx="10.5" cy="7" r="1"/><circle cx="15" cy="7.5" r="1"/></svg>',
  music: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/></svg>',
  masks: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M17 3a2 2 0 0 1 2 2c0 7-2.5 8-2.5 12a2.5 2.5 0 0 1-5 0"/><path d="M7 3a2 2 0 0 0-2 2c0 7 2.5 8 2.5 12a2.5 2.5 0 0 0 5 0"/></svg>',
  camera: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 8h3l2-2h6l2 2h3v11H4z"/><circle cx="12" cy="13" r="3.5"/></svg>',
  mic: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="9" y="2" width="6" height="11" rx="3"/><path d="M5 11a7 7 0 0 0 14 0M12 18v4M9 22h6"/></svg>',
  bag: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M6 8h12l1 12H5z"/><path d="M9 8V6a3 3 0 0 1 6 0v2"/></svg>',
  ticket: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M3 8a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v2a2 2 0 0 0 0 4v2a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-2a2 2 0 0 0 0-4z"/></svg>',
  anime: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M12 2l1.6 4.9L18.5 8l-4.1 3 1.5 4.9-4-2.9-4 2.9 1.5-4.9L5.5 8l4.9-1.1z"/><path d="M19 15l.7 2 2 .7-2 .7-.7 2-.7-2-2-.7 2-.7z"/></svg>',
  dance: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="4.5" r="1.8"/><path d="M12 7v6M12 8l-5-2M12 8l5-2M12 13l-4 7M12 13l4 7"/></svg>',
  design: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z"/></svg>',
};

const PLACEHOLDER_GRADIENTS = {
  palette: 'linear-gradient(135deg,#F472B6,#8B5CF6)',
  music:   'linear-gradient(135deg,#60A5FA,#6366F1)',
  masks:   'linear-gradient(135deg,#FB923C,#F43F5E)',
  camera:  'linear-gradient(135deg,#34D399,#0EA5E9)',
  mic:     'linear-gradient(135deg,#A78BFA,#6366F1)',
  bag:     'linear-gradient(135deg,#FBBF24,#F97316)',
  anime:   'linear-gradient(135deg,#FDE68A,#F59E0B)',
  dance:   'linear-gradient(135deg,#5EEAD4,#0D9488)',
  design:  'linear-gradient(135deg,#C4B5FD,#7C3AED)',
  ticket:  'linear-gradient(135deg,#94A3B8,#475569)',
};

function iconKeyFor(category){ return CATEGORY_ICON_MAP[category] || 'ticket'; }

function detectRegion(ev){
  const text = `${ev.locationName || ''} ${ev.location || ''}`;
  for(const group of REGION_GROUPS){
    if(group.some(kw => text.includes(kw))) return group[0];
  }
  return '其他地區';
}

function sortByRegionOrder(regions){
  return regions.slice().sort((a,b) => {
    const ai = REGION_ORDER.indexOf(a); const bi = REGION_ORDER.indexOf(b);
    return (ai === -1 ? 999 : ai) - (bi === -1 ? 999 : bi);
  });
}

function sortByCategoryOrder(cats){
  return cats.slice().sort((a,b) => {
    const ai = CATEGORY_ORDER.indexOf(a); const bi = CATEGORY_ORDER.indexOf(b);
    return (ai === -1 ? 999 : ai) - (bi === -1 ? 999 : bi);
  });
}

// ---------- 讀取網址參數（從「顯示更多展覽」連結進來時使用）----------
function readUrlParams(){
  const params = new URLSearchParams(location.search);
  const category = params.get('category');
  const status = params.get('status');
  if(category) state.detailCategory = category;
  if(status && ['all','ongoing','upcoming'].includes(status)) state.statusFilter = status;
}

async function loadData(){
  readUrlParams();
  try{
    const res = await fetch('data/exhibitions.json', { cache: 'no-store' });
    const data = await res.json();
    state.events = (data.events || []).map(ev => ({ ...ev, region: detectRegion(ev) }));
    state.updatedAt = data.updatedAt;
    buildCategoryRow();
    buildCategoryPanel();
    buildRegionPanel();
    syncStatusButtons();
    render();
    updateNavCount();
  }catch(err){
    document.getElementById('homepageRows').innerHTML =
      '<div class="empty">資料載入失敗，請確認 data/exhibitions.json 是否存在。</div>';
    console.error(err);
  }
}

function updateNavCount(){
  document.getElementById('navCount').textContent = `收錄 ${state.events.length} 檔活動`;
}

function countBy(list, key){
  const counts = {};
  list.forEach(ev => {
    const v = ev[key];
    if(!v) return;
    counts[v] = (counts[v] || 0) + 1;
  });
  return counts;
}

function buildCategoryRow(){
  const counts = countBy(state.events, 'category');
  const cats = sortByCategoryOrder(Object.keys(counts));
  const row = document.getElementById('catRow');
  row.innerHTML = cats.map(cat => `
    <button class="cat-chip" data-cat="${escapeAttr(cat)}">
      <span class="icon-circle">${ICONS[iconKeyFor(cat)]}</span>
      <span class="label">${escapeHtml(cat)}</span>
    </button>
  `).join('');
  row.querySelectorAll('.cat-chip').forEach(btn => {
    btn.addEventListener('click', () => {
      const cat = btn.dataset.cat;
      toggleCategory(cat);
    });
  });
  syncCategoryChips();
}

function buildCategoryPanel(){
  const counts = countBy(state.events, 'category');
  const cats = sortByCategoryOrder(Object.keys(counts));
  const el = document.getElementById('categoryOptions');
  el.innerHTML = cats.map(cat => `
    <label class="opt">
      <input type="checkbox" data-category="${escapeAttr(cat)}">
      ${escapeHtml(cat)}
      <span class="c">${counts[cat]}</span>
    </label>
  `).join('');
  el.querySelectorAll('input[data-category]').forEach(cb => {
    cb.addEventListener('change', () => {
      toggleCategory(cb.dataset.category, cb.checked);
    });
  });
  syncCategoryPanelChecks();
}

function toggleCategory(cat, forceState){
  const on = forceState !== undefined ? forceState : !state.selectedCategories.has(cat);
  if(on) state.selectedCategories.add(cat); else state.selectedCategories.delete(cat);
  syncCategoryChips();
  syncCategoryPanelChecks();
  render();
}

function syncCategoryChips(){
  document.querySelectorAll('.cat-chip').forEach(btn => {
    btn.classList.toggle('active', state.selectedCategories.has(btn.dataset.cat));
  });
}
function syncCategoryPanelChecks(){
  document.querySelectorAll('input[data-category]').forEach(cb => {
    cb.checked = state.selectedCategories.has(cb.dataset.category);
  });
}

function buildRegionPanel(){
  const counts = countBy(state.events, 'region');
  const regions = sortByRegionOrder(Object.keys(counts));
  const el = document.getElementById('regionOptions');
  el.innerHTML = regions.map(region => `
    <label class="opt">
      <input type="checkbox" data-region="${escapeAttr(region)}">
      ${escapeHtml(region)}
      <span class="c">${counts[region]}</span>
    </label>
  `).join('');
  el.querySelectorAll('input[data-region]').forEach(cb => {
    cb.addEventListener('change', () => {
      const r = cb.dataset.region;
      if(cb.checked) state.selectedRegions.add(r); else state.selectedRegions.delete(r);
      render();
    });
  });
}

function syncStatusButtons(){
  document.querySelectorAll('.status-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.status === state.statusFilter);
  });
}

// ---------- 日期／狀態判斷 ----------
function parseDate(str){
  if(!str) return null;
  const parts = str.split(/[\/\-]/).map(Number);
  if(parts.length < 3 || parts.some(isNaN)) return null;
  return new Date(parts[0], parts[1]-1, parts[2]);
}

function isOngoing(ev){
  const now = new Date();
  const start = parseDate(ev.startDate);
  const end = parseDate(ev.endDate);
  if(start && start > now) return false;
  if(end && end < now) return false;
  return true;
}
function isUpcoming(ev){
  const start = parseDate(ev.startDate);
  return start ? start > new Date() : false;
}

// 進行中的展覽優先顯示，其次依日期排序（進行中→依結束日期排序；未開展→依開始日期排序）
function compareEvents(a, b){
  const aOngoing = isOngoing(a), bOngoing = isOngoing(b);
  if(aOngoing !== bOngoing) return aOngoing ? -1 : 1;
  if(aOngoing){
    const aVal = parseDate(a.endDate)?.getTime() ?? Infinity;
    const bVal = parseDate(b.endDate)?.getTime() ?? Infinity;
    return aVal - bVal;
  }
  const aVal = parseDate(a.startDate)?.getTime() ?? Infinity;
  const bVal = parseDate(b.startDate)?.getTime() ?? Infinity;
  return aVal - bVal;
}

function computeBadge(ev){
  const now = new Date();
  const end = parseDate(ev.endDate);
  const start = parseDate(ev.startDate);
  if(end){
    const daysLeft = (end - now) / 86400000;
    if(daysLeft >= 0 && daysLeft <= 7) return { label:'即將截止', cls:'closing' };
  }
  if(start){
    const daysSinceStart = (now - start) / 86400000;
    if(daysSinceStart >= 0 && daysSinceStart <= 10) return { label:'新開展', cls:'new' };
  }
  return null;
}

function dateRangeText(ev){
  if(ev.startDate && ev.endDate && ev.startDate !== ev.endDate) return `${ev.startDate} – ${ev.endDate}`;
  return ev.startDate || ev.endDate || '日期未提供';
}

// ---------- 篩選 ----------
function getFilteredPool(){
  const q = document.getElementById('searchInput').value.trim().toLowerCase();
  let pool = state.events.filter(ev => {
    if(state.selectedRegions.size && !state.selectedRegions.has(ev.region)) return false;
    if(state.statusFilter === 'ongoing' && !isOngoing(ev)) return false;
    if(state.statusFilter === 'upcoming' && !isUpcoming(ev)) return false;
    if(q){
      const haystack = `${ev.title} ${ev.locationName} ${ev.location} ${ev.unit}`.toLowerCase();
      if(!haystack.includes(q)) return false;
    }
    return true;
  });
  pool.sort(compareEvents);
  return pool;
}

// ---------- 卡片 ----------
function cardMarkup(ev, { showDistance } = {}){
  const iconKey = iconKeyFor(ev.category);
  const badge = computeBadge(ev);
  const tag = ev.sourceUrl ? 'a' : 'div';
  const href = ev.sourceUrl ? `href="${escapeAttr(ev.sourceUrl)}" target="_blank" rel="noopener"` : '';
  const gradient = PLACEHOLDER_GRADIENTS[iconKey];
  // 圖片一律先放 icon 佔位圖在底層，真的圖片載入成功才蓋在上面；
  // 如果圖片網址失效載入失敗，onerror 會把圖片移除，讓底下的佔位圖自然顯示出來
  const media = `
    <div class="icon-wrap">${ICONS[iconKey]}</div>
    ${ev.image ? `<img src="${escapeAttr(ev.image)}" alt="" loading="lazy" onerror="this.remove()">` : ''}
  `;

  return `
    <${tag} class="card" ${href}>
      <div class="card-media" style="background:${gradient}">
        ${media}
        ${badge ? `<span class="card-badge ${badge.cls}">${badge.label}</span>` : ''}
      </div>
      <div class="card-body">
        <div class="card-cat">${escapeHtml(ev.category || '活動')}</div>
        <h3 class="card-title">${escapeHtml(ev.title)}</h3>
        <div class="card-meta">
          <span class="loc">${escapeHtml(ev.locationName || ev.location || '地點未提供')}</span>
          <span>${escapeHtml(dateRangeText(ev))}</span>
        </div>
        ${showDistance && ev._distance != null ? `<div class="card-dist">距離約 ${ev._distance.toFixed(1)} 公里</div>` : ''}
      </div>
    </${tag}>
  `;
}

// ---------- 首頁：依分類分區顯示 ----------
const ROW_PAGE_SIZE = 4;
const ROW_MAX_ITEMS = ROW_PAGE_SIZE * 3; // 最多顯示 3 頁

function buildShowMoreUrl(category){
  const params = new URLSearchParams();
  params.set('category', category);
  if(state.statusFilter !== 'all') params.set('status', state.statusFilter);
  return `?${params.toString()}`;
}

function renderHomepage(pool){
  const wrap = document.getElementById('homepageRows');
  const byCategory = {};
  pool.forEach(ev => { (byCategory[ev.category] = byCategory[ev.category] || []).push(ev); });

  let cats = sortByCategoryOrder(Object.keys(byCategory));
  if(state.selectedCategories.size){
    cats = cats.filter(c => state.selectedCategories.has(c));
  }

  if(cats.length === 0){
    wrap.innerHTML = '<div class="empty">沒有符合條件的活動，換個關鍵字或篩選條件看看？</div>';
    return;
  }

  wrap.innerHTML = cats.map(cat => {
    const items = byCategory[cat];
    const shown = items.slice(0, ROW_MAX_ITEMS);
    const hasMore = items.length > ROW_MAX_ITEMS;
    return `
      <section class="cat-section">
        <div class="cat-section-head">
          <h2><span class="icon-sm">${ICONS[iconKeyFor(cat)]}</span>${escapeHtml(cat)}<span class="hint">（${items.length} 檔）</span></h2>
          <div class="row-controls">
            <button class="row-nav prev" data-row="${escapeAttr(cat)}" aria-label="向左">‹</button>
            <button class="row-nav next" data-row="${escapeAttr(cat)}" aria-label="向右">›</button>
          </div>
        </div>
        <div class="carousel" id="row-${cssId(cat)}">
          ${shown.map(ev => cardMarkup(ev)).join('')}
        </div>
        ${hasMore ? `
          <div class="show-more-row">
            <a class="show-more-btn" href="${buildShowMoreUrl(cat)}" target="_blank" rel="noopener">顯示更多展覽 →</a>
          </div>` : ''}
      </section>
    `;
  }).join('');

  wrap.querySelectorAll('.row-nav').forEach(btn => {
    btn.addEventListener('click', () => {
      const el = document.getElementById(`row-${cssId(btn.dataset.row)}`);
      if(!el) return;
      const dir = btn.classList.contains('next') ? 1 : -1;
      el.scrollBy({ left: dir * el.clientWidth, behavior: 'smooth' });
    });
  });
}

function cssId(str){
  return str.replace(/[^a-zA-Z0-9\u4e00-\u9fff]/g, '_');
}

function renderDetail(pool){
  const category = state.detailCategory;
  const items = pool.filter(ev => ev.category === category);
  document.getElementById('detailTitle').textContent = category;
  document.getElementById('detailHint').textContent = `共 ${items.length} 檔`;
  const grid = document.getElementById('detailGrid');
  grid.innerHTML = items.length
    ? items.map(ev => cardMarkup(ev)).join('')
    : '<div class="empty">目前這個分類沒有符合條件的活動。</div>';
}

// ---------- 主渲染流程 ----------
function render(){
  const pool = getFilteredPool();
  state.lastPool = pool;

  const isDetail = Boolean(state.detailCategory);
  document.getElementById('homepageRows').style.display = isDetail ? 'none' : 'block';
  document.getElementById('detailView').style.display = isDetail ? 'block' : 'none';

  if(isDetail){
    renderDetail(pool);
  }else{
    renderHomepage(pool);
  }

  renderNearby();
  const mapPool = isDetail ? pool.filter(ev => ev.category === state.detailCategory) : pool;
  renderMapView(mapPool);
}

// ---------- 附近展覽（地理位置）----------
function haversine(lat1, lon1, lat2, lon2){
  const R = 6371;
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a = Math.sin(dLat/2)**2 + Math.cos(lat1*Math.PI/180) * Math.cos(lat2*Math.PI/180) * Math.sin(dLon/2)**2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
}

function renderNearby(){
  const section = document.getElementById('nearby');
  if(!state.userLoc){ section.style.display = 'none'; return; }

  const withCoords = state.events
    .map(ev => {
      const lat = parseFloat(ev.latitude);
      const lng = parseFloat(ev.longitude);
      if(isNaN(lat) || isNaN(lng)) return null;
      return { ...ev, _distance: haversine(state.userLoc.lat, state.userLoc.lng, lat, lng) };
    })
    .filter(Boolean)
    .sort((a,b) => a._distance - b._distance)
    .slice(0, 10);

  const row = document.getElementById('nearbyRow');
  section.style.display = 'block';
  row.innerHTML = withCoords.length
    ? withCoords.map(ev => cardMarkup(ev, { showDistance: true })).join('')
    : '<div class="empty">目前沒有活動提供座標資訊，暫時無法計算距離。</div>';
}

// ---------- 地圖檢視（OpenStreetMap / Leaflet，免金鑰）----------
function initMapIfNeeded(){
  if(state.map) return;
  state.map = L.map('mapContainer').setView([23.7, 121.0], 7);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap 貢獻者',
    maxZoom: 18,
  }).addTo(state.map);
  state.markerLayer = L.layerGroup().addTo(state.map);
}

function renderMapView(pool){
  initMapIfNeeded();
  state.markerLayer.clearLayers();

  const withCoords = pool.filter(ev => !isNaN(parseFloat(ev.latitude)) && !isNaN(parseFloat(ev.longitude)));

  withCoords.forEach(ev => {
    const lat = parseFloat(ev.latitude);
    const lng = parseFloat(ev.longitude);
    const marker = L.marker([lat, lng]);
    const linkHtml = ev.sourceUrl
      ? `<a href="${escapeAttr(ev.sourceUrl)}" target="_blank" rel="noopener">前往官方頁面 →</a>`
      : '';
    marker.bindPopup(`
      <div class="map-popup">
        <h4>${escapeHtml(ev.title)}</h4>
        <p>${escapeHtml(ev.locationName || ev.location || '')}<br>${escapeHtml(dateRangeText(ev))}</p>
        ${linkHtml}
      </div>
    `);
    state.markerLayer.addLayer(marker);
  });

  if(withCoords.length > 0){
    const bounds = L.latLngBounds(withCoords.map(ev => [parseFloat(ev.latitude), parseFloat(ev.longitude)]));
    state.map.fitBounds(bounds, { padding: [30,30], maxZoom: 13 });
  }
}

function escapeHtml(str){
  if(!str) return '';
  return String(str).replace(/[&<>"']/g, s => ({
    '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'
  }[s]));
}
function escapeAttr(str){ return escapeHtml(str); }

// ---------- 事件綁定 ----------
document.getElementById('searchInput').addEventListener('input', render);

document.querySelectorAll('.status-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    state.statusFilter = btn.dataset.status;
    syncStatusButtons();
    render();
  });
});
});

document.getElementById('locateBtn').addEventListener('click', () => {
  const btn = document.getElementById('locateBtn');
  if(!navigator.geolocation){
    alert('你的瀏覽器不支援定位功能');
    return;
  }
  btn.textContent = '定位中…';
  navigator.geolocation.getCurrentPosition(
    pos => {
      state.userLoc = { lat: pos.coords.latitude, lng: pos.coords.longitude };
      btn.innerHTML = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3"/></svg> 已定位';
      btn.classList.add('active');
      renderNearby();
      document.getElementById('nearby').scrollIntoView({ behavior:'smooth', block:'start' });
    },
    () => { btn.textContent = '定位失敗，重試'; }
  );
});

function setupDropdown(navBtnId, panelId){
  const navBtn = document.getElementById(navBtnId);
  const panel = document.getElementById(panelId);
  navBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    document.querySelectorAll('.dropdown-panel').forEach(p => { if(p !== panel) p.classList.remove('open'); });
    panel.classList.toggle('open');
  });
  document.addEventListener('click', (e) => {
    if(!panel.contains(e.target) && e.target !== navBtn) panel.classList.remove('open');
  });
}
setupDropdown('regionNavBtn', 'regionPanel');
setupDropdown('categoryNavBtn', 'categoryPanel');

document.querySelector('[data-clear="region"]').addEventListener('click', () => {
  state.selectedRegions.clear();
  document.querySelectorAll('input[data-region]').forEach(cb => cb.checked = false);
  render();
});
document.querySelector('[data-clear="category"]').addEventListener('click', () => {
  state.selectedCategories.clear();
  syncCategoryChips();
  syncCategoryPanelChecks();
  render();
});

loadData();
</script>

</body>
</html>
