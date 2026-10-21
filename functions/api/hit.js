// 방문·전화·문자·견적 기록 (Cloudflare D1, 바인딩 이름 DB)
const SCHEMA = 'CREATE TABLE IF NOT EXISTS hits (ts INTEGER, d TEXT, t TEXT, p TEXT, r TEXT, k TEXT, v TEXT, m INTEGER)';
const clip = (s, n) => String(s || '').slice(0, n);
const TYPES = ['view', 'call', 'sms', 'lead'];

export async function onRequestPost({ request, env }) {
  if (!env.DB) return new Response(null, { status: 204 });
  const ua = request.headers.get('User-Agent') || '';
  if (/bot|crawl|spider|slurp|preview|headless|lighthouse/i.test(ua)) return new Response(null, { status: 204 });
  let x;
  try { x = JSON.parse(await request.text()); } catch (e) { return new Response(null, { status: 400 }); }
  if (!TYPES.includes(x.t)) return new Response(null, { status: 400 });
  const now = new Date(Date.now() + 9 * 3600e3); // 한국 시간
  await env.DB.prepare(SCHEMA).run();
  await env.DB.prepare('INSERT INTO hits VALUES (?,?,?,?,?,?,?,?)')
    .bind(Date.now(), now.toISOString().slice(0, 10), x.t, clip(x.p, 200), clip(x.r, 80), clip(x.k, 80), clip(x.v, 40), /Mobi|Android|iPhone/i.test(ua) ? 1 : 0).run();
  return new Response(null, { status: 204 });
}
