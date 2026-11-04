#!/usr/bin/env python3
"""로켓집수리 블로그 만들기.

- .github/blog/queue/*.md  : 아직 안 올라간 글 (이름 순서대로 하루에 하나씩 올라감)
- .github/blog/posts/*.md  : 이미 올라간 글 (date: 가 붙어 있음)

python3 .github/blog/publish.py            # 올라간 글로 /blog/ 페이지만 다시 만듦
python3 .github/blog/publish.py --publish  # 오늘 글이 없으면 대기열에서 하나 꺼내 올리고 다시 만듦

새로 생긴 주소는 .github/blog/new-urls.txt 에 적힘 (IndexNow 용).
"""
import datetime as dt
import html
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SRC = os.path.join(ROOT, '.github', 'blog')
QUEUE = os.path.join(SRC, 'queue')
POSTS = os.path.join(SRC, 'posts')
SITE = 'https://rocketzipsuri.com'
KST = dt.timezone(dt.timedelta(hours=9))
BRAND = '로켓집수리닷컴'
PHONE = '010-3051-8015'
TEMPLATE = os.path.join(ROOT, 'faq', 'index.html')
NAV_LINK = '<a href="/blog/">블로그</a>'

esc = html.escape


# ---------- 글 읽기 ----------
def read_post(path):
    raw = open(path, encoding='utf-8').read()
    m = re.match(r'---\n(.*?)\n---\n(.*)$', raw, re.S)
    if not m:
        raise SystemExit(f'{path}: 맨 위에 --- 로 감싼 정보가 없어요')
    meta = {}
    for line in m.group(1).splitlines():
        if ':' in line:
            k, v = line.split(':', 1)
            meta[k.strip()] = v.strip()
    for k in ('slug', 'title', 'description'):
        if not meta.get(k):
            raise SystemExit(f'{path}: {k} 가 비어 있어요')
    if not re.fullmatch(r'[a-z0-9-]+', meta['slug']):
        raise SystemExit(f'{path}: slug 는 영어 소문자·숫자·- 만 돼요')
    meta['body'] = m.group(2).strip()
    meta['path'] = path
    return meta


def write_post(meta, path):
    keys = [k for k in meta if k not in ('body', 'path')]
    head = '\n'.join(f'{k}: {meta[k]}' for k in keys)
    open(path, 'w', encoding='utf-8').write(f'---\n{head}\n---\n\n{meta["body"]}\n')


# ---------- 간단한 마크다운 ----------
def inline(t):
    t = esc(t, quote=False)
    t = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', t)
    t = re.sub(r'\[([^\]]+)\]\(([^)\s]+)\)', lambda m: f'<a href="{m.group(2)}">{m.group(1)}</a>', t)
    return t


def md(body):
    """## 제목, ### 소제목, - 목록, 1. 목록, | 표 |, ![설명](사진), > 강조 상자, 빈 줄로 문단."""
    out, lines, i = [], body.splitlines(), 0
    toc = []
    while i < len(lines):
        ln = lines[i].rstrip()
        if not ln.strip():
            i += 1
            continue
        if ln.startswith('## '):
            t = ln[3:].strip()
            hid = f's{len(toc) + 1}'
            toc.append((hid, t))
            out.append(f'<h2 id="{hid}">{inline(t)}</h2>')
            i += 1
        elif ln.startswith('### '):
            out.append(f'<h3>{inline(ln[4:].strip())}</h3>')
            i += 1
        elif re.match(r'!\[', ln):
            imgs = []
            while i < len(lines) and re.match(r'!\[', lines[i]):
                m = re.match(r'!\[([^\]]*)\]\(([^)\s]+)\)', lines[i])
                if m:
                    imgs.append(m.groups())
                i += 1
            cls = 'fig2' if len(imgs) > 1 else 'fig1'
            figs = ''.join(f'<figure><img src="{esc(s)}" alt="{esc(a)}" loading="lazy"><figcaption>{esc(a)}</figcaption></figure>' for a, s in imgs)
            out.append(f'<div class="{cls}">{figs}</div>')
        elif ln.startswith('|'):
            rows = []
            while i < len(lines) and lines[i].startswith('|'):
                cells = [c.strip() for c in lines[i].strip().strip('|').split('|')]
                if not all(re.fullmatch(r':?-+:?', c) for c in cells):
                    rows.append(cells)
                i += 1
            th = ''.join(f'<th>{inline(c)}</th>' for c in rows[0])
            tb = ''.join('<tr>' + ''.join(f'<td>{inline(c)}</td>' for c in r) + '</tr>' for r in rows[1:])
            out.append(f'<div class="tbl"><table><thead><tr>{th}</tr></thead><tbody>{tb}</tbody></table></div>')
        elif re.match(r'[-*] ', ln):
            items = []
            while i < len(lines) and re.match(r'[-*] ', lines[i]):
                items.append(f'<li>{inline(lines[i][2:].strip())}</li>')
                i += 1
            out.append('<ul>' + ''.join(items) + '</ul>')
        elif re.match(r'\d+\. ', ln):
            items = []
            while i < len(lines) and re.match(r'\d+\. ', lines[i]):
                txt = re.sub(r'^\d+\. ', '', lines[i]).strip()
                items.append(f'<li>{inline(txt)}</li>')
                i += 1
            out.append('<ol>' + ''.join(items) + '</ol>')
        elif ln.startswith('> '):
            parts = []
            while i < len(lines) and lines[i].startswith('> '):
                parts.append(inline(lines[i][2:].strip()))
                i += 1
            out.append('<aside class="note">' + '<br>'.join(parts) + '</aside>')
        else:
            parts = []
            while i < len(lines) and lines[i].strip() and not re.match(r'(#{2,3} |[-*] |\d+\. |\||> |!\[)', lines[i]):
                parts.append(inline(lines[i].strip()))
                i += 1
            out.append('<p>' + ' '.join(parts) + '</p>')
    return '\n'.join(out), toc


def split_faq(body):
    """'## 자주 묻는 질문' 아래 '### 질문' + 답 문단을 따로 꺼냄."""
    m = re.search(r'^## 자주 묻는 질문\s*$', body, re.M)
    if not m:
        return body, []
    rest = body[m.end():]
    nxt = re.search(r'^## ', rest, re.M)
    faq_txt = rest[:nxt.start()] if nxt else rest
    after = rest[nxt.start():] if nxt else ''
    faqs = []
    for q in re.split(r'^### ', faq_txt, flags=re.M)[1:]:
        q_line, _, a = q.partition('\n')
        a = ' '.join(x.strip() for x in a.strip().splitlines() if x.strip())
        if q_line.strip() and a:
            faqs.append((q_line.strip(), a))
    return (body[:m.start()] + after).strip(), faqs


def strip_md(t):
    t = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', t)
    return t.replace('**', '')


# ---------- 페이지 틀 ----------
CSS = """<style>
.bl-hd{padding:56px 0 8px}.bl-hd .crumb{font-size:.9rem;color:var(--muted)}.bl-hd .crumb a{color:var(--muted)}
.bl-tag{display:inline-block;margin-top:18px;background:var(--pril);color:var(--pri2);font-weight:700;font-size:.85rem;padding:6px 13px;border-radius:999px}
.bl-hd h1{margin:14px 0 0;font-size:clamp(1.7rem,4vw,2.6rem);line-height:1.3;letter-spacing:-.045em;font-weight:800;max-width:860px}
.bl-meta{margin-top:14px;color:var(--muted);font-size:.95rem}
.bl-wrap{display:grid;grid-template-columns:minmax(0,760px) 260px;gap:56px;align-items:start;padding-top:28px;padding-bottom:72px}
.bl-cover{margin:0 0 30px;border-radius:20px;overflow:hidden;background:var(--bg2);aspect-ratio:16/9}.bl-cover img{width:100%;height:100%;object-fit:cover;display:block}
.bl{font-size:1.08rem;line-height:1.85;color:var(--ink)}
.bl h2{font-size:1.5rem;letter-spacing:-.035em;line-height:1.4;margin:52px 0 14px;scroll-margin-top:90px}
.bl h3{font-size:1.18rem;margin:30px 0 8px;letter-spacing:-.02em}
.bl p{margin:0 0 16px}.bl ul,.bl ol{margin:0 0 18px;padding-left:1.3em}.bl li{margin:6px 0}
.bl a{color:var(--pri2);text-decoration:underline;text-underline-offset:3px}
.bl strong{background:linear-gradient(transparent 62%,var(--pril) 62%)}
.bl .sum{background:var(--bg2);border-radius:18px;padding:22px 26px;margin:0 0 8px}
.bl .sum b{display:block;font-size:.95rem;color:var(--pri2);margin-bottom:6px}.bl .sum ul{margin:0}
.bl .note{border-left:4px solid var(--pri);background:var(--pril);padding:16px 20px;border-radius:0 14px 14px 0;margin:0 0 20px;color:var(--ink2);text-align:left;font-size:1rem;line-height:1.8}
.bl .tbl{overflow-x:auto;margin:6px 0 22px;border:1px solid var(--line);border-radius:14px}
.bl table{border-collapse:collapse;width:100%;font-size:.98rem;min-width:520px}
.bl th{background:var(--bg2);text-align:left;font-weight:700}.bl th,.bl td{padding:12px 14px;border-bottom:1px solid var(--line);vertical-align:top}
.bl tr:last-child td{border-bottom:0}
.bl .fig1,.bl .fig2{display:grid;gap:10px;margin:8px 0 24px}.bl .fig2{grid-template-columns:1fr 1fr}
.bl figure{margin:0}.bl figure img{width:100%;border-radius:14px;display:block;background:var(--bg2);aspect-ratio:4/3;object-fit:cover}
.bl figcaption{font-size:.88rem;color:var(--muted);margin-top:6px}
.bl .faq details{border:1px solid var(--line);border-radius:14px;padding:16px 20px;margin:0 0 10px}
.bl .faq summary{font-weight:700;cursor:pointer;list-style:none}.bl .faq summary::before{content:"Q. ";color:var(--pri)}
.bl .faq details p{margin:10px 0 0;color:var(--ink2)}
.bl .who{display:flex;gap:16px;align-items:center;border:1px solid var(--line);border-radius:18px;padding:20px 22px;margin-top:48px}
.bl .who img{width:52px;height:52px}.bl .who b{display:block}.bl .who span{color:var(--ink2);font-size:.95rem}
.bl-side{position:sticky;top:96px;display:grid;gap:16px}
.bl-side .box{border:1px solid var(--line);border-radius:18px;padding:18px 20px;font-size:.95rem}
.bl-side .box b{display:block;margin-bottom:8px}.bl-side ol{margin:0;padding-left:1.2em}.bl-side li{margin:5px 0}.bl-side a{color:var(--ink2)}
.bl-side .cta{background:var(--ink);color:#fff;border:0}.bl-side .cta a.btn{display:block;text-align:center;margin-top:10px}
.bl-more{padding:56px 0;background:var(--bg2)}.bl-more h2{font-size:1.5rem;letter-spacing:-.035em;margin:0 0 20px}
.bl-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:20px}
.bl-card{display:block;background:var(--card);border-radius:18px;overflow:hidden;border:1px solid var(--line);color:var(--ink);transition:transform .15s}
.bl-card:hover{transform:translateY(-3px)}
.bl-card .im{aspect-ratio:16/10;background:var(--bg2)}.bl-card .im img{width:100%;height:100%;object-fit:cover;display:block}
.bl-card .tx{padding:16px 18px 20px}.bl-card small{color:var(--pri2);font-weight:700}
.bl-card h3{margin:6px 0 8px;font-size:1.08rem;line-height:1.45;letter-spacing:-.025em}
.bl-card p{margin:0;color:var(--muted);font-size:.92rem;line-height:1.6;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.bl-first{display:grid;grid-template-columns:1.2fr 1fr;gap:0;margin-bottom:28px}.bl-first .im{aspect-ratio:16/10}.bl-first .tx{padding:32px}
.bl-first h3{font-size:1.5rem}
@media (max-width:960px){.bl-wrap{grid-template-columns:minmax(0,1fr);gap:24px}.bl-side{position:static}.bl-grid{grid-template-columns:1fr 1fr}.bl-first{grid-template-columns:1fr}.bl-first .tx{padding:20px}}
@media (max-width:600px){.bl-hd{padding:32px 0 0}.bl{font-size:1.02rem}.bl h2{font-size:1.32rem;margin-top:40px}.bl-grid{grid-template-columns:1fr}.bl .fig2{grid-template-columns:1fr}}
</style>"""


def load_template():
    s = open(TEMPLATE, encoding='utf-8').read()
    a = s.index('<main id="main">')
    b = s.index('<section class="ct" id="contact">')
    head, tail = s[:a], s[b:]
    # 이 페이지 전용 정보 빼기
    head = re.sub(r'<script type="application/ld\+json">.*?</script>\s*', '', head, flags=re.S)
    head = head.replace(' class="on" href="/faq/"', ' href="/faq/"')
    head = add_nav(head, active=True)
    return head, tail


def add_nav(s, active=False):
    link = '<a class="on" href="/blog/">블로그</a>' if active else NAV_LINK
    if 'href="/blog/">블로그</a>' in s:
        return s
    return re.sub(r'(<nav class="nav">.*?)(</nav>)', lambda m: m.group(1) + link + m.group(2), s, count=1, flags=re.S)


def set_head(head, title, desc, url, image, og_type, ld):
    head = re.sub(r'<title>.*?</title>', f'<title>{esc(title)}</title>', head, count=1, flags=re.S)
    head = re.sub(r'(<meta name="description" content=")[^"]*', lambda m: m.group(1) + esc(desc), head, count=1)
    head = re.sub(r'(<link rel="canonical" href=")[^"]*', lambda m: m.group(1) + url, head, count=1)
    for prop, val in (('og:title', title), ('og:description', desc), ('og:url', url), ('og:type', og_type), ('og:image', image)):
        head = re.sub(rf'(<meta property="{prop}" content=")[^"]*', lambda m, v=val: m.group(1) + esc(v), head, count=1)
    head = re.sub(r'\s*<meta property="og:image:(width|height)"[^>]*>', '', head)
    lds = ''.join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>\n' for x in ld)
    rss = f'<link rel="alternate" type="application/rss+xml" title="{BRAND} 블로그" href="{SITE}/blog/feed.xml">\n'
    return head.replace('</head>', CSS + '\n' + rss + lds + '</head>', 1)


PER_SLOT = 2  # 한 번에 올리는 글 수
SLOTS = ('07:00', '22:00')  # 아침 7시, 밤 10시


def ptime(p):
    return p.get('time') or '07:00'


def iso(p):
    return f'{p["date"]}T{ptime(p)}:00+09:00'


def kdate(d):
    y, m, dd = d.split('-')
    return f'{y}년 {int(m)}월 {int(dd)}일'


def abs_url(u):
    return u if u.startswith('http') else SITE + u


def card(p, first=False):
    img = f'<div class="im"><img src="{esc(p["image"])}" alt="{esc(p["title"])}" loading="lazy"></div>' if p.get('image') else ''
    return (f'<a class="bl-card{" bl-first" if first else ""}" href="/blog/{p["slug"]}/">{img}<div class="tx">'
            f'<small>{esc(p.get("tag", "집수리 이야기"))} · {kdate(p["date"])}</small><h3>{esc(p["title"])}</h3>'
            f'<p>{esc(p["description"])}</p></div></a>')


def render_post(p, posts, head, tail):
    url = f'{SITE}/blog/{p["slug"]}/'
    body, faqs = split_faq(p['body'])
    # '## 한 줄로 정리하면' 은 요약 상자로
    summ = ''
    m = re.match(r'## 한 줄로 정리하면\s*\n(.*?)(?=^## |\Z)', body, re.S | re.M)
    if m:
        inner, _ = md(m.group(1))
        summ = f'<div class="sum"><b>한 줄로 정리하면</b>{inner}</div>'
        body = body[m.end():].strip()
    content, toc = md(body)
    faq_html = ''
    if faqs:
        faq_html = '<h2 id="faq">자주 묻는 질문</h2><div class="faq">' + ''.join(
            f'<details><summary>{inline(q)}</summary><p>{inline(a)}</p></details>' for q, a in faqs) + '</div>'
        toc.append(('faq', '자주 묻는 질문'))
    image = abs_url(p.get('image') or '/img/share-v7.jpg')
    published = iso(p)
    ld = [{
        '@context': 'https://schema.org', '@type': 'BlogPosting', 'headline': p['title'],
        'description': p['description'], 'image': image, 'datePublished': published, 'dateModified': published,
        'mainEntityOfPage': url, 'inLanguage': 'ko-KR',
        'author': {'@type': 'Organization', 'name': BRAND, 'url': SITE + '/'},
        'publisher': {'@type': 'Organization', 'name': BRAND, 'url': SITE + '/', 'logo': {'@type': 'ImageObject', 'url': SITE + '/favicon.svg'}},
        'about': p.get('tag', '집수리'),
    }, {
        '@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': 1, 'name': '홈', 'item': SITE + '/'},
            {'@type': 'ListItem', 'position': 2, 'name': '블로그', 'item': SITE + '/blog/'},
            {'@type': 'ListItem', 'position': 3, 'name': p['title'], 'item': url}]}]
    if faqs:
        ld.append({'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': [
            {'@type': 'Question', 'name': strip_md(q), 'acceptedAnswer': {'@type': 'Answer', 'text': strip_md(a)}} for q, a in faqs]})
    h = set_head(head, f'{p["title"]} | {BRAND}', p['description'], url, image, 'article', ld)
    cover = f'<figure class="bl-cover"><img src="{esc(p["image"])}" alt="{esc(p.get("image_alt") or p["title"])}"></figure>' if p.get('image') else ''
    toc_html = ''.join(f'<li><a href="#{i}">{esc(strip_md(t))}</a></li>' for i, t in toc)
    repair = ''
    if p.get('repair') and os.path.isdir(os.path.join(ROOT, 'repair', p['repair'])):
        repair = f'<a class="btn" href="/repair/{p["repair"]}/" style="margin-top:8px;display:block;text-align:center">이 작업 자세히 보기</a>'
    others = [x for x in posts if x['slug'] != p['slug']]
    same = [x for x in others if x.get('tag') == p.get('tag')]
    more = (same + [x for x in others if x not in same])[:3]
    more_html = ''
    if more:
        more_html = f'<section class="bl-more"><div class="w"><h2>다른 글도 읽어 보세요</h2><div class="bl-grid">{"".join(card(x) for x in more)}</div><p style="margin:24px 0 0"><a href="/blog/">블로그 전체 글 보기 →</a></p></div></section>'
    main = f'''<main id="main">
<section class="bl-hd"><div class="w"><nav class="crumb"><a href="/">홈</a> › <a href="/blog/">블로그</a> › {esc(p.get("crumb") or p["title"])}</nav>
<span class="bl-tag">{esc(p.get("tag", "집수리 이야기"))}</span><h1>{esc(p["title"])}</h1>
<p class="bl-meta">{BRAND} · <time datetime="{published}">{kdate(p["date"])}</time></p></div></section>
<div class="w bl-wrap"><article class="bl">{cover}{summ}
{content}
{faq_html}
<div class="who"><img src="/favicon.svg" alt=""><div><b>{BRAND}</b><span>서울·경기 전 지역과 전국으로 출장 가는 생활 집수리. 블로그에 작업일지 889편을 직접 남겨 왔어요. 상담 <a href="tel:{PHONE}">{PHONE}</a></span></div></div>
</article>
<aside class="bl-side"><div class="box"><b>이 글의 순서</b><ol>{toc_html}</ol></div>
<div class="box cta"><b>사진 한 장이면 돼요</b>고칠 곳 사진과 동네를 보내 주시면 예상 금액을 먼저 알려드려요.<a class="btn p" href="#contact">사진으로 견적 받기</a><a class="btn" href="tel:{PHONE}" style="background:#fff;color:var(--ink)">전화 {PHONE}</a>{repair}</div></aside></div>
{more_html}
'''
    return h + main + tail


def render_index(posts, head, tail):
    url = SITE + '/blog/'
    title = f'집수리 블로그 · 고치기 전에 읽는 이야기 | {BRAND}'
    desc = '서울·경기 출장 집수리 현장에서 직접 겪은 일로 쓰는 글. 건조기랙, 식기세척기, 상판 복원, 문 수리까지 고치기 전에 알아 두면 좋은 내용을 매일 아침·저녁 올려요.'
    ld = [{'@context': 'https://schema.org', '@type': 'Blog', 'name': f'{BRAND} 블로그', 'url': url, 'description': desc, 'inLanguage': 'ko-KR',
           'publisher': {'@type': 'Organization', 'name': BRAND, 'url': SITE + '/'},
           'blogPost': [{'@type': 'BlogPosting', 'headline': p['title'], 'url': f'{SITE}/blog/{p["slug"]}/', 'datePublished': iso(p)} for p in posts[:30]]}]
    h = set_head(head, title, desc, url, SITE + '/img/share-v7.jpg', 'website', ld)
    if posts:
        cards = card(posts[0], first=True) + '<div class="bl-grid">' + ''.join(card(p) for p in posts[1:]) + '</div>'
    else:
        cards = '<p>첫 글을 준비하고 있어요.</p>'
    main = f'''<main id="main">
<section class="ph"><div class="w"><nav class="crumb"><a href="/">홈</a> › 블로그</nav><span class="eb">매일 아침 7시·밤 10시 새 글</span>
<h1>고치기 전에 읽는<br><em>집수리 이야기</em></h1>
<p class="lead">현장에서 직접 겪은 일로 써요. 어떤 고장인지, 고칠지 바꿀지, 무엇을 준비하면 되는지 정리했어요.</p></div></section>
<section class="sec" style="padding-top:0"><div class="w">{cards}</div></section>
'''
    return h + main + tail


def rss(posts):
    items = ''.join(
        f'<item><title>{esc(p["title"])}</title><link>{SITE}/blog/{p["slug"]}/</link><guid>{SITE}/blog/{p["slug"]}/</guid>'
        f'<pubDate>{dt.datetime.fromisoformat(iso(p)).strftime("%a, %d %b %Y %H:%M:%S +0900")}</pubDate>'
        f'<description>{esc(p["description"])}</description></item>' for p in posts[:50])
    return (f'<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel><title>{BRAND} 블로그</title><link>{SITE}/blog/</link>'
            f'<description>서울·경기 출장 생활 집수리 이야기</description><language>ko</language>{items}</channel></rss>\n')


def update_sitemap(posts):
    path = os.path.join(ROOT, 'sitemap.xml')
    s = open(path, encoding='utf-8').read()
    s = re.sub(r'\s*<url><loc>https://rocketzipsuri\.com/blog/[^<]*</loc>.*?</url>', '', s, flags=re.S)
    newest = posts[0]['date'] if posts else dt.datetime.now(KST).date().isoformat()
    add = f'\n  <url><loc>{SITE}/blog/</loc><lastmod>{newest}</lastmod></url>' + ''.join(
        f'\n  <url><loc>{SITE}/blog/{p["slug"]}/</loc><lastmod>{p["date"]}</lastmod></url>' for p in posts)
    s = s.replace('</urlset>', add + '\n</urlset>', 1)
    open(path, 'w', encoding='utf-8').write(s)


def update_robots():
    path = os.path.join(ROOT, 'robots.txt')
    s = open(path, encoding='utf-8').read()
    if 'Disallow: /.github/' not in s:
        s = s.replace('Disallow: /p/', 'Disallow: /p/\nDisallow: /.github/', 1)
    if '/blog/feed.xml' not in s:
        s = s.rstrip('\n') + f'\nSitemap: {SITE}/blog/feed.xml\n'
    open(path, 'w', encoding='utf-8').write(s)


def add_nav_everywhere():
    n = 0
    for dp, dn, fn in os.walk(ROOT):
        dn[:] = [d for d in dn if not d.startswith('.') and d not in ('functions', 'img', 'video')]
        for f in fn:
            if f.endswith('.html'):
                p = os.path.join(dp, f)
                s = open(p, encoding='utf-8').read()
                t = add_nav(s)
                # 바닥글 '블로그' 는 네이버 블로그로 가던 것 → 이름만 구분
                t = t.replace('target="_blank" rel="noopener">블로그</a>', 'target="_blank" rel="noopener">네이버 블로그</a>')
                if '<a href="/blog/">' not in t.split('<footer', 1)[-1] and '<footer' in t:
                    t = t.replace(' · <a href="/k/">많이 찾는 집수리</a>', ' · <a href="/blog/">블로그</a> · <a href="/k/">많이 찾는 집수리</a>', 1)
                if t != s:
                    open(p, 'w', encoding='utf-8').write(t)
                    n += 1
    return n


def main():
    today = dt.datetime.now(KST).date().isoformat()
    os.makedirs(POSTS, exist_ok=True)
    os.makedirs(QUEUE, exist_ok=True)
    published_new = []
    now = dt.datetime.now(KST)
    slot = SLOTS[0] if now.hour < 15 else SLOTS[1]
    if '--publish' in sys.argv:
        posts = [read_post(os.path.join(POSTS, f)) for f in sorted(os.listdir(POSTS)) if f.endswith('.md')]
        slugs = {p['slug'] for p in posts}
        need = PER_SLOT - sum(1 for p in posts if p.get('date') == today and ptime(p) == slot)
        if need <= 0:
            print(f'오늘 {slot} 글은 이미 올라가 있어요')
        queue = sorted(f for f in os.listdir(QUEUE) if f.endswith('.md'))
        for f in queue:
            if need <= 0:
                break
            p = read_post(os.path.join(QUEUE, f))
            if p['slug'] in slugs:
                print(f'{f}: 같은 주소 글이 이미 있어서 건너뜀')
                continue
            p['date'] = today
            p['time'] = slot
            write_post(p, os.path.join(POSTS, f'{today}-{slot.replace(":", "")}-{p["slug"]}.md'))
            os.remove(os.path.join(QUEUE, f))
            slugs.add(p['slug'])
            published_new.append(p['slug'])
            need -= 1
            print(f'새 글 올림 ({slot}): {p["title"]}')
        if need > 0:
            print(f'대기열에 글이 모자라요 ({need}편 부족)')
    posts = [read_post(os.path.join(POSTS, f)) for f in sorted(os.listdir(POSTS)) if f.endswith('.md')]
    posts = [p for p in posts if p.get('date') and p['date'] <= today]
    posts.sort(key=lambda p: (p['date'], ptime(p), p['path']), reverse=True)
    head, tail = load_template()
    out = os.path.join(ROOT, 'blog')
    keep = {p['slug'] for p in posts}
    if os.path.isdir(out):
        for d in os.listdir(out):
            if os.path.isdir(os.path.join(out, d)) and d not in keep:
                import shutil
                shutil.rmtree(os.path.join(out, d))
    for p in posts:
        os.makedirs(os.path.join(out, p['slug']), exist_ok=True)
        open(os.path.join(out, p['slug'], 'index.html'), 'w', encoding='utf-8').write(render_post(p, posts, head, tail))
    os.makedirs(out, exist_ok=True)
    open(os.path.join(out, 'index.html'), 'w', encoding='utf-8').write(render_index(posts, head, tail))
    open(os.path.join(out, 'feed.xml'), 'w', encoding='utf-8').write(rss(posts))
    update_sitemap(posts)
    update_robots()
    n = add_nav_everywhere()
    urls = [f'{SITE}/blog/{s}/' for s in published_new] + ([f'{SITE}/blog/'] if published_new else [])
    open(os.path.join(SRC, 'new-urls.txt'), 'w').write('\n'.join(urls) + ('\n' if urls else ''))
    left = len([f for f in os.listdir(QUEUE) if f.endswith('.md')])
    print(f'블로그 글 {len(posts)}개, 대기열 {left}개, 메뉴 고친 페이지 {n}개')


if __name__ == '__main__':
    main()
