// 통계 모아 보기 (비밀번호: Cloudflare 변수 STATS_KEY)
const SCHEMA = 'CREATE TABLE IF NOT EXISTS hits (ts INTEGER, d TEXT, t TEXT, p TEXT, r TEXT, k TEXT, v TEXT, m INTEGER)';
const json = (o, s = 200) => new Response(JSON.stringify(o), { status: s, headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' } });
const kst = (ms) => new Date(ms + 9 * 3600e3).toISOString().slice(0, 10);

// 들어온 경로 이름 (referrer 주소 → 사람이 읽는 이름)
function src(r) {
  if (!r) return '직접 방문';
  if (r === 'blog.naver.com' || r === 'm.blog.naver.com') return '네이버 블로그';
  if (r.includes('naver')) return '네이버 검색';
  if (r.includes('google')) return '구글 검색';
  if (r.includes('daum')) return '다음 검색';
  if (r.includes('kakao')) return '카카오톡';
  if (r.includes('bing')) return '빙 검색';
  if (r.includes('daangn')) return '당근';
  if (r.includes('instagram')) return '인스타그램';
  if (r.includes('facebook')) return '페이스북';
  if (r.includes('youtube')) return '유튜브';
  return r;
}

export async function onRequestGet({ request, env }) {
  const u = new URL(request.url);
  if (!env.DB) return json({ error: 'nodb' }, 503);
  if (!env.STATS_KEY) return json({ error: 'nokey' }, 503);
  if (u.searchParams.get('k') !== env.STATS_KEY) return json({ error: 'auth' }, 401);
  const days = Math.min(365, Math.max(1, parseInt(u.searchParams.get('days')) || 7));
  const now = Date.now(), today = kst(now), from = kst(now - (days - 1) * 864e5);
  await env.DB.prepare(SCHEMA).run();
  const rows = (await env.DB.prepare('SELECT ts, d, t, p, r, k, v, m FROM hits WHERE d>=? ORDER BY ts LIMIT 200000').bind(from).all()).results;

  const C = { call: 'phone', sms: 'sms', lead: 'form' };
  const zero = () => ({ visitors: 0, views: 0, phone: 0, sms: 0, form: 0 });
  const tot = zero(), tod = zero(), dayMap = {}, vis = new Set(), tvis = new Set(), cvis = new Set();
  const first = {}, dvis = {}, pages = {}, cpages = {}, dev = { mobile: new Set(), pc: new Set() };
  for (let i = 0; i < days; i++) { const d = kst(now - (days - 1 - i) * 864e5); dayMap[d] = { day: d, ...zero(), _v: new Set() }; }
  for (const h of rows) {
    const day = dayMap[h.d]; const id = h.v || ('x' + h.ts);
    if (h.t === 'view') {
      tot.views++; vis.add(id); (h.m ? dev.mobile : dev.pc).add(id);
      if (day) { day.views++; day._v.add(id); }
      if (h.d === today) { tod.views++; tvis.add(id); }
      if (!first[id]) first[id] = { s: src(h.r), k: h.k || '', r: h.r || '' };
      const pg = pages[h.p] || (pages[h.p] = { path: h.p, views: 0, contacts: 0 }); pg.views++;
    } else if (C[h.t]) {
      const f = C[h.t]; tot[f]++; cvis.add(id);
      if (day) day[f]++;
      if (h.d === today) tod[f]++;
      (cpages[h.p] || (cpages[h.p] = { path: h.p, contacts: 0, phone: 0, sms: 0, form: 0 })).contacts++;
      cpages[h.p][f]++;
      if (pages[h.p]) pages[h.p].contacts++;
    }
  }
  tot.visitors = vis.size; tot.contact_visitors = [...cvis].filter(x => vis.has(x)).length || cvis.size; tod.visitors = tvis.size;
  const daily = Object.values(dayMap).map(d => { const { _v, ...o } = d; o.visitors = _v.size; return o; });

  const sm = {}, km = {};
  let kwSearch = 0, kwKnown = 0;
  for (const [id, f] of Object.entries(first)) {
    const s = sm[f.s] || (sm[f.s] = { name: f.s, visitors: 0, contacts: 0 }); s.visitors++; if (cvis.has(id)) s.contacts++;
    if (f.r && /naver|google|daum|bing/.test(f.r) && f.r !== 'blog.naver.com') { kwSearch++; if (f.k) kwKnown++; }
    if (f.k) { const key = f.k.trim().slice(0, 60); const k = km[key] || (km[key] = { kw: key, src: f.s, visitors: 0, contacts: 0 }); k.visitors++; if (cvis.has(id)) k.contacts++; }
  }
  const top = (o, key, n) => Object.values(o).sort((a, b) => b[key] - a[key]).slice(0, n);

  let photos = [];
  try {
    await env.DB.prepare('CREATE TABLE IF NOT EXISTS photos (g TEXT, n INTEGER, ts INTEGER, type TEXT, data BLOB, PRIMARY KEY (g, n))').run();
    await env.DB.prepare('CREATE TABLE IF NOT EXISTS photo_msg (g TEXT PRIMARY KEY, ts INTEGER, msg TEXT)').run();
    photos = (await env.DB.prepare('SELECT p.g, p.c, p.f, p.ts, m.msg FROM (SELECT g, COUNT(*) c, MIN(n) f, MAX(ts) ts FROM photos GROUP BY g ORDER BY ts DESC LIMIT 40) p LEFT JOIN photo_msg m ON m.g = p.g ORDER BY p.ts DESC').all()).results;
  } catch (e) {}

  return json({
    days, from, today, totals: tot, today_totals: tod, daily,
    sources: top(sm, 'visitors', 12), keywords: top(km, 'visitors', 30), kw_search: kwSearch, kw_known: kwKnown,
    contact_pages: top(cpages, 'contacts', 12), pages: top(pages, 'views', 20),
    devices: { mobile: dev.mobile.size, pc: dev.pc.size }, photos,
  });
}
