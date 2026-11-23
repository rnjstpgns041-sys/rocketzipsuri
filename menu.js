/* 전체 메뉴: ☰ 버튼 → 오른쪽에서 나오는 카테고리 메뉴 (모든 페이지 공통) */
(function(){
if(document.getElementById('mz'))return;
var TEL='010-3051-8015';
var CATS=[
['🧺','건조기랙','세탁기 위로','/repair/dryer-rack/'],
['🍽️','식기세척기','빌트인·철거','/repair/dishwasher/'],
['🔥','쿡탑 교체','인덕션·가스레인지','/repair/induction-cut/'],
['💎','대리석·상판','구멍·깨짐 복원','/repair/countertop-repair/'],
['🚪','문·경첩','처짐·방향 변경','/repair/door-hinge/'],
['🗄️','붙박이장','롤러·상부장','/repair/closet-roller/'],
['🛁','욕실','욕조·팝업','/repair/bathtub-repair/'],
['🚰','수전·정수기','교체·구멍 복원','/repair/faucet/'],
['📺','TV 설치','벽걸이·거치대','/repair/tv-mount/'],
['🔨','철거·정리','붙박이장·식세기','/repair/closet-removal/']
];
var LINKS=[['홈으로','/'],['시공분야 전체','/repair/'],['시공사례','/cases/'],['고객 후기','/reviews/'],['현장 소식','/records/'],['자주 묻는 질문','/faq/'],['동네별 집수리','/k/'],['블로그','/blog/']];
var css='#mzb{flex:0 0 auto;width:42px;height:42px;margin-left:8px;border:0;border-radius:12px;background:#212575;color:#fff;display:inline-flex;align-items:center;justify-content:center;cursor:pointer;padding:0}'+
'#mzb svg{display:block}'+
'#mz{position:fixed;inset:0;z-index:9999;visibility:hidden}'+
'#mz.on{visibility:visible}'+
'#mz .mzd{position:absolute;inset:0;background:rgba(14,16,40,.5);opacity:0;transition:opacity .25s}'+
'#mz.on .mzd{opacity:1}'+
'#mz .mzp{position:absolute;top:0;right:0;bottom:0;width:min(88vw,420px);background:#F5F3F0;border-radius:24px 0 0 24px;overflow-y:auto;-webkit-overflow-scrolling:touch;transform:translateX(100%);transition:transform .3s cubic-bezier(.2,.8,.2,1);font-family:inherit;color:#191F28;letter-spacing:-.02em}'+
'#mz.on .mzp{transform:none}'+
'#mz .mzh{background:#212575;color:#fff;padding:22px 18px 18px;position:sticky;top:0;z-index:1}'+
'#mz .mzt{display:flex;align-items:center;gap:12px}'+
'#mz .mzt img{width:46px;height:46px;border-radius:12px;background:#fff;padding:6px;box-sizing:border-box}'+
'#mz .mzt b{display:block;font-size:1.15rem;font-weight:900}'+
'#mz .mzt small{display:block;font-size:.82rem;color:rgba(255,255,255,.75);margin-top:2px}'+
'#mz .mzx{margin-left:auto;width:40px;height:40px;border-radius:50%;border:0;background:rgba(255,255,255,.15);color:#fff;font-size:1.4rem;line-height:1;cursor:pointer}'+
'#mz .mzc{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:16px}'+
'#mz .mzc a{display:flex;align-items:center;justify-content:center;gap:6px;height:48px;border-radius:12px;font-weight:900;font-size:1rem;text-decoration:none}'+
'#mz .mzc .q{background:#FF6A26;color:#fff}#mz .mzc .c{background:#fff;color:#212575}'+
'#mz .mzs{padding:20px 16px 8px;font-size:.9rem;font-weight:800;color:#8B95A1}'+
'#mz .mzg{display:grid;grid-template-columns:1fr 1fr;gap:8px;padding:0 16px}'+
'#mz .mzg a{display:flex;align-items:center;gap:10px;background:#fff;border-radius:16px;padding:12px 10px;text-decoration:none;color:#191F28;box-shadow:0 0 0 1px rgba(33,37,117,.06);min-width:0}'+
'#mz .mzg i{flex:0 0 auto;width:38px;height:38px;border-radius:11px;background:#FFF1E8;display:flex;align-items:center;justify-content:center;font-style:normal;font-size:1.25rem}'+
'#mz .mzg b{display:block;font-size:.95rem;font-weight:900;line-height:1.25;word-break:keep-all}'+
'#mz .mzg span{display:block;font-size:.76rem;color:#8B95A1;margin-top:2px;line-height:1.3;word-break:keep-all}'+
'#mz .mzl{margin:0 16px 28px;background:#fff;border-radius:16px;overflow:hidden;box-shadow:0 0 0 1px rgba(33,37,117,.06)}'+
'#mz .mzl a{display:flex;justify-content:space-between;align-items:center;padding:16px 18px;font-weight:800;font-size:1rem;color:#191F28;text-decoration:none;border-top:1px solid #EEE}'+
'#mz .mzl a:first-child{border-top:0}#mz .mzl a.on{background:#FFF1E8;color:#E2561A}'+
'#mz .mzl a:after{content:"›";color:#B0B8C1;font-size:1.3rem}'+
'html.mzo,html.mzo body{overflow:hidden}'+
'.mzg2{display:flex;align-items:center;margin-left:auto;flex:0 0 auto}'+
'@media (max-width:520px){.mzg2 a.call{font-size:.82rem!important;padding:9px 12px!important;white-space:nowrap}.mzg2 #mzb{width:38px;height:38px;margin-left:6px}}';
var st=document.createElement('style');st.textContent=css;document.head.appendChild(st);
var here=location.pathname;
var q=document.getElementById('contact')?'#contact':'/#contact';
var h='<div class="mzd"></div><div class="mzp" role="dialog" aria-modal="true" aria-label="전체 메뉴"><div class="mzh"><div class="mzt"><img src="/favicon.svg" alt=""><div><b>로켓집수리닷컴</b><small>생활 집수리 · 서울·경기 출장</small></div><button type="button" class="mzx" aria-label="메뉴 닫기">✕</button></div>'+
'<div class="mzc"><a class="q" href="'+q+'">📷 사진 견적</a><a class="c" href="tel:'+TEL+'">📞 전화 상담</a></div></div>'+
'<div class="mzs">무엇을 고칠까요?</div><div class="mzg">';
CATS.forEach(function(c){h+='<a href="'+c[3]+'"><i>'+c[0]+'</i><div><b>'+c[1]+'</b><span>'+c[2]+'</span></div></a>'});
h+='</div><div class="mzs">둘러보기</div><div class="mzl">';
LINKS.forEach(function(l){h+='<a href="'+l[1]+'"'+(here==l[1]?' class="on"':'')+'>'+l[0]+'</a>'});
h+='</div></div>';
var m=document.createElement('div');m.id='mz';m.innerHTML=h;document.body.appendChild(m);
function op(){m.classList.add('on');document.documentElement.classList.add('mzo');if(window.track)try{track('menu_open',{})}catch(e){}}
function cl(){m.classList.remove('on');document.documentElement.classList.remove('mzo')}
m.querySelector('.mzd').onclick=cl;m.querySelector('.mzx').onclick=cl;
m.addEventListener('click',function(e){var a=e.target.closest('a');if(a)cl()});
document.addEventListener('keydown',function(e){if(e.key=='Escape')cl()});
var b=document.createElement('button');b.type='button';b.id='mzb';b.setAttribute('aria-label','전체 메뉴');
b.innerHTML='<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h16"/></svg>';
b.onclick=op;
var hd=document.querySelector('header');
var act=hd&&hd.querySelector('.act'),call=hd&&hd.querySelector('a.call');
if(act){act.style.display='flex';act.style.alignItems='center';act.appendChild(b)}
else if(call){var g=document.createElement('span');g.className='mzg2';call.parentNode.insertBefore(g,call);g.appendChild(call);g.appendChild(b)}else{b.style.cssText='position:fixed;top:12px;right:12px;z-index:9998';document.body.appendChild(b)}
})();
