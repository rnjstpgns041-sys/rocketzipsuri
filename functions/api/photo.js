// 견적 사진 저장 → 문자에 넣을 "사진 보기" 주소용 (Cloudflare D1, 바인딩 이름 DB)
const SCHEMA = 'CREATE TABLE IF NOT EXISTS photos (g TEXT, n INTEGER, ts INTEGER, type TEXT, data BLOB, PRIMARY KEY (g, n))';
const KEEP = 90 * 864e5; // 90일 뒤 자동 삭제

export async function onRequestPost({ request, env }) {
  if (!env.DB) return new Response('nodb', { status: 503 });
  let fd;
  try { fd = await request.formData(); } catch (e) { return new Response('bad', { status: 400 }); }
  const g = String(fd.get('g') || '');
  if (!/^[a-z0-9]{10,24}$/.test(g)) return new Response('bad id', { status: 400 });
  await env.DB.prepare(SCHEMA).run();
  await env.DB.prepare('DELETE FROM photos WHERE ts < ?').bind(Date.now() - KEEP).run();
  let n = 0;
  for (let i = 1; i <= 3; i++) {
    const f = fd.get('photo' + i);
    if (!f || typeof f === 'string' || !f.size) continue;
    if (f.size > 1900000 || !/^image\//.test(f.type)) continue;
    const buf = await f.arrayBuffer();
    await env.DB.prepare('INSERT OR REPLACE INTO photos VALUES (?,?,?,?,?)').bind(g, i, Date.now(), f.type, buf).run();
    n++;
  }
  return new Response(JSON.stringify({ g, n }), { headers: { 'Content-Type': 'application/json' } });
}
