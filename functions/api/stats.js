// 통계 모아 보기 (비밀번호: Cloudflare 변수 STATS_KEY)
const SCHEMA = 'CREATE TABLE IF NOT EXISTS hits (ts INTEGER, d TEXT, t TEXT, p TEXT, r TEXT, k TEXT, v TEXT, m INTEGER)';
const json = (o, s = 200) => new Response(JSON.stringify(o), { status: s, headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' } });

export async function onRequestGet({ request, env }) {
  const u = new URL(request.url);
  if (!env.DB) return json({ error: 'nodb' }, 503);
  if (!env.STATS_KEY) return json({ error: 'nokey' }, 503);
  if (u.searchParams.get('k') !== env.STATS_KEY) return json({ error: 'auth' }, 401);
  const days = Math.min(365, Math.max(1, parseInt(u.searchParams.get('days')) || 30));
  const from = new Date(Date.now() + 9 * 3600e3 - (days - 1) * 864e5).toISOString().slice(0, 10);
  await env.DB.prepare(SCHEMA).run();
  const q = (sql) => env.DB.prepare(sql).bind(from).all().then(r => r.results);
  const [daily, pages, refs, kws, lp, dev] = await Promise.all([
    q(`SELECT d, SUM(t='view') views, COUNT(DISTINCT CASE WHEN t='view' THEN v END) visitors, SUM(t='call') calls, SUM(t='sms') sms, SUM(t='lead') leads FROM hits WHERE d>=? GROUP BY d ORDER BY d`),
    q(`SELECT p, COUNT(*) n FROM hits WHERE d>=? AND t='view' GROUP BY p ORDER BY n DESC LIMIT 15`),
    q(`SELECT CASE WHEN r='' THEN '직접 방문' ELSE r END r, COUNT(*) n FROM hits WHERE d>=? AND t='view' GROUP BY 1 ORDER BY n DESC LIMIT 10`),
    q(`SELECT k, COUNT(*) n FROM hits WHERE d>=? AND t='view' AND k<>'' GROUP BY k ORDER BY n DESC LIMIT 15`),
    q(`SELECT p, SUM(t='call') calls, SUM(t='sms') sms, SUM(t='lead') leads FROM hits WHERE d>=? AND t<>'view' GROUP BY p ORDER BY COUNT(*) DESC LIMIT 10`),
    q(`SELECT m, COUNT(*) n FROM hits WHERE d>=? AND t='view' GROUP BY m`),
  ]);
  return json({ from, days, daily, pages, refs, kws, lp, dev });
}
