// 사진 보기: /p/<번호>/ 는 사진 모음 화면, /p/<번호>/<1~3> 은 사진 파일
export async function onRequestGet({ params, env }) {
  const [g, n] = params.path || [];
  const nf = () => new Response('사진을 찾을 수 없어요. 보관 기간(90일)이 지났을 수 있어요.', { status: 404, headers: { 'Content-Type': 'text/plain; charset=utf-8' } });
  if (!env.DB || !/^[a-z0-9]{10,24}$/.test(g || '')) return nf();
  try {
    if (n) {
      const r = await env.DB.prepare('SELECT type, data FROM photos WHERE g=? AND n=?').bind(g, +n).first();
      if (!r) return nf();
      return new Response(new Uint8Array(r.data), { headers: { 'Content-Type': r.type, 'Cache-Control': 'private, max-age=86400', 'X-Robots-Tag': 'noindex' } });
    }
    const rs = (await env.DB.prepare('SELECT n, ts FROM photos WHERE g=? ORDER BY n').bind(g).all()).results;
    if (!rs.length) return nf();
    const d = new Date(rs[0].ts + 9 * 3600e3).toISOString().slice(0, 16).replace('T', ' ');
    const imgs = rs.map(r => `<a href="/p/${g}/${r.n}"><img src="/p/${g}/${r.n}" alt="견적 사진 ${r.n}"></a>`).join('');
    return new Response(`<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex"><title>견적 사진 ${rs.length}장</title>
<style>body{margin:0;background:#111;color:#eee;font-family:-apple-system,"Apple SD Gothic Neo","Malgun Gothic",sans-serif}p{margin:0;padding:14px 16px;font-size:14px;color:#aaa}img{display:block;width:100%;height:auto;margin:0 0 8px}</style></head>
<body><p>홈페이지 견적 사진 ${rs.length}장 · ${d} 접수 · 누르면 크게 보여요</p>${imgs}</body></html>`, { headers: { 'Content-Type': 'text/html; charset=utf-8', 'X-Robots-Tag': 'noindex', 'Cache-Control': 'private, no-store' } });
  } catch (e) { return nf(); }
}
