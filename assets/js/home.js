// 홈: 타이틀 화면, 일시정지 메뉴, 영웅 선택 카드, 브리핑 창
(()=>{
const {CATS,P,PAPERS,md,byCat,last,icon,catUrl,LINKS,pix,navi}=OVAN,TOTAL=P.length;
const reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
const phone=matchMedia('(max-width:900px)');
// 메뉴 순서와 같다: 카테고리들, 그다음 About, Archive (_layouts/home.html)
const E=[
  ...Object.values(CATS).map(c=>({key:c.k,...c,url:catUrl(c.k),posts:byCat(c.k),kind:'cat'})),
  {key:'about',en:'About',ko:'플레이어 정보',type:'PROFILE',desc:'분산 시스템과 AI 에이전트 보안을 연구하는 김가영(OVAN)입니다.',url:LINKS.about,posts:byCat('paper-conference'),kind:'sys'},
  {key:'archive',en:'Archive',ko:'전체 기록',type:'ALL',desc:`지금까지 남긴 기록 ${TOTAL}개를 날짜순으로 모았습니다.`,url:LINKS.archive,posts:P,kind:'sys'}
];
// 내비 한마디: 데이터에서 바로 계산한 사실만
const counts=Object.keys(CATS).map(k=>byCat(k).length),cMax=Math.max(...counts),cMin=Math.min(...counts);
const line=e=>e.kind==='cat'
  ?(!e.posts.length?'아직 비어 있어. 곧 채워질 거야!'
   :e.posts.length===cMax?`${e.posts.length}개, 제일 많이 쌓인 곳이야!`
   :e.posts.length===cMin?`아직 ${e.posts.length}개. 이제 막 시작한 칸이야.`
   :`${e.posts.length}개 있어. 최근 건 ${md(last(e.posts).d)}!`)
  :e.key==='about'?'플레이어 정보! 연구 분야랑 활동 기록이 다 모여 있어.'
  :`전부 ${TOTAL}개. 첫 기록은 ${P[TOTAL-1].d.slice(0,7).replace('-','.')}!`;

const menu=document.getElementById('menu');
const items=[...menu.querySelectorAll('.mi')];
if(items.length!==E.length)return;
window.OVAN_HOME=true;
const stage=document.getElementById('stage'),slab=document.getElementById('slab'),stripe=document.getElementById('stripe');
const card=document.getElementById('card'),cardIn=document.getElementById('cardIn'),brief=document.getElementById('brief'),briefBox=brief.parentElement;
const slash=document.getElementById('slash'),slash2=document.getElementById('slash2');
let cur=-1;

// 선 아이콘을 24×24 캔버스에 찍어 픽셀로 바꾼다 (한 번 만들면 재사용)
const SPR={};
function sprite(k){
  if(SPR[k])return SPR[k];
  const N=24,c=document.createElement('canvas');c.width=c.height=N;
  const x=c.getContext('2d');x.lineWidth=2.2;x.lineCap='square';x.lineJoin='miter';
  const src=icon(k);
  for(const m of src.matchAll(/ d="([^"]+)"/g))x.stroke(new Path2D(m[1]));
  for(const m of src.matchAll(/<circle cx="([\d.]+)" cy="([\d.]+)" r="([\d.]+)"/g)){x.beginPath();x.arc(+m[1],+m[2],+m[3],0,Math.PI*2);x.stroke()}
  const a=x.getImageData(0,0,N,N).data;let sh='',ink='';
  for(let y=0;y<N;y++)for(let i=0;i<N;i++)if(a[(y*N+i)*4+3]>110){ink+=`M${i} ${y}h1v1h-1z`;sh+=`M${i+1} ${y+1}h1v1h-1z`}
  return SPR[k]=`<svg class="px" viewBox="-1 -1 26 26" aria-hidden="true"><path class="s" d="${sh}"/><path class="k" d="${ink}"/></svg>`;
}

const esc=s=>String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
function render(e){
  cardIn.innerHTML=`<div class="ghost" aria-hidden="true">${esc(e.en)}</div>
    <div class="head"><div class="type"><span>TYPE</span><b>${esc(e.type)}</b></div>
    <div class="name"><small>${esc(e.ko)}</small><b>${esc(e.en)}</b></div></div>
    <div class="portrait">${sprite(e.key)}</div>`;
  const lp=e.posts.length?last(e.posts):null;
  const chips=e.kind==='cat'
    ?[['POSTS',e.posts.length],['SHARE',Math.round(e.posts.length/TOTAL*100)+'%'],['LAST',lp?md(lp.d):'-']]
    :e.key==='about'?[['LOGS',TOTAL],['PAPERS',PAPERS],['SINCE','2026']]
    :[['LOGS',TOTAL],['FIRST',P[TOTAL-1].d.slice(0,7).replace('-','.')],['LAST',md(last(P).d)]];
  brief.innerHTML=`<div class="navi"><span class="ufo">${pix('ufo')}</span><p class="say"><span class="who">NAVI</span><span class="nsay"></span></p></div>
    <p class="lead">${esc(e.desc)}</p>
    <div class="chips">${chips.map(([k,v])=>`<div class="chip"><span>${k}</span><b>${v}</b></div>`).join('')}</div>
    <ul class="list">${e.posts.slice(0,3).map(p=>`<li><a href="${p.url}" data-go><time>${md(p.d)}</time><span>${esc(p.t)}</span></a></li>`).join('')}</ul>
    <a class="pick" href="${e.url}" data-go${e.kind==='cat'?' data-morph':''}><b>SELECT</b><span>${e.kind==='cat'?'카테고리 열기':esc(e.ko)+' 열기'}</span></a>`;
  navi(brief.querySelector('.nsay'),line(e));
}

// 핑크 판이 고른 메뉴 끝을 겨냥한다
function aim(){
  const st=stage.getBoundingClientRect(),W=st.width,H=st.height;
  if(phone.matches){
    const c=card.getBoundingClientRect(),y=c.top-st.top+c.height*.62;
    slab.style.clipPath=`polygon(0px 0px,${W}px 0px,${W}px ${y-60}px,0px ${y+60}px)`;
    stripe.style.clipPath=`polygon(0px ${y+74}px,${W}px ${y-46}px,${W}px ${y-38}px,0px ${y+82}px)`;
    return;
  }
  const r=items[cur].getBoundingClientRect(),s=.36;
  const px=r.right-st.left+64,py=r.top-st.top+r.height/2,tx=px-py*s,bx=px+(H-py)*s;
  slab.style.clipPath=`polygon(0px 0px,${tx}px 0px,${bx}px ${H}px,0px ${H}px)`;
  stripe.style.clipPath=`polygon(${tx+16}px 0px,${tx+25}px 0px,${bx+25}px ${H}px,${bx+16}px ${H}px)`;
}

function select(i,focus){
  i=(i+E.length)%E.length;
  if(focus)items[i].focus({preventScroll:true});
  if(i===cur)return;
  const first=cur<0;cur=i;
  items.forEach((a,k)=>{a.classList.toggle('on',k===i);a.setAttribute('aria-current',k===i?'true':'false')});
  aim();
  if(first||reduced){render(E[i]);return}
  // 핑크 사선과 그 뒤를 따르는 검은 선이 카드를 긋고, 그 사이에 내용이 바뀐다
  slash.animate([{transform:'translateX(-200%) skewX(-18deg)'},{transform:'translateX(420%) skewX(-18deg)'}],{duration:420,easing:'cubic-bezier(.6,0,.3,1)'});
  slash2.animate([{transform:'translateX(-200%) skewX(-18deg)'},{transform:'translateX(2400%) skewX(-18deg)'}],{duration:440,delay:50,easing:'cubic-bezier(.6,0,.3,1)'});
  // 맞은 것처럼 카드가 살짝 밀렸다 돌아오고, 브리핑 창은 한 번 기울어진다
  card.animate([{transform:'none'},{transform:'translateX(10px)'},{transform:'none'}],{duration:320,easing:'cubic-bezier(.2,.8,.2,1)'});
  const b0=phone.matches?0:-1.5;
  briefBox.animate([{rotate:b0+'deg'},{rotate:(b0-2)+'deg'},{rotate:b0+'deg'}],{duration:360,easing:'cubic-bezier(.2,1.4,.4,1)'});
  setTimeout(()=>{if(cur!==i)return;render(E[i]);
    cardIn.animate([{opacity:.2,transform:'translateX(-18px)'},{opacity:1,transform:'none'}],{duration:260,easing:'cubic-bezier(.2,.8,.2,1)'});
    // 스프라이트는 위에서부터 한 줄씩 찍혀 나온다
    cardIn.querySelector('.px').animate([{clipPath:'inset(0 0 100% 0)'},{clipPath:'inset(0 0 0 0)'}],{duration:380,delay:60,easing:'steps(12)',fill:'backwards'});
    brief.animate([{opacity:0,transform:'translateX(16px)'},{opacity:1,transform:'none'}],{duration:260,easing:'cubic-bezier(.2,.8,.2,1)'});
  },150);
}

// 마우스가 메뉴를 훑고 지나갈 때마다 카드가 긁히지 않게, 잠깐 머문 항목만 고른다
let hoverT;
items.forEach((a,i)=>{
  a.addEventListener('mouseenter',()=>{if(phone.matches)return;clearTimeout(hoverT);hoverT=setTimeout(()=>select(i),70)});
  a.addEventListener('mouseleave',()=>clearTimeout(hoverT));
  a.addEventListener('focus',()=>select(i));
  a.addEventListener('click',e=>{
    if(e.button!==0||e.metaKey||e.ctrlKey||e.shiftKey||e.altKey)return;
    e.preventDefault();
    if(phone.matches&&cur!==i){select(i);return}
    leave(E[i].url,{morph:E[i].kind==='cat'});
  });
});
document.addEventListener('keydown',e=>{
  if(e.altKey||e.ctrlKey||e.metaKey||phone.matches||scrollY>innerHeight*.5)return;
  const ae=document.activeElement;
  if(ae&&ae!==document.body&&!items.includes(ae))return;
  const k=e.key.toLowerCase();
  if(k==='arrowdown'||k==='s'||k==='arrowright'||k==='d'){e.preventDefault();select(cur+1,true)}
  else if(k==='arrowup'||k==='w'||k==='arrowleft'||k==='a'){e.preventDefault();select(cur-1,true)}
  else if(k==='enter'){e.preventDefault();leave(E[cur].url,{morph:E[cur].kind==='cat'})}
});

select(Math.min(1,E.length-1));
addEventListener('resize',()=>{slab.style.transition=stripe.style.transition='none';aim();requestAnimationFrame(()=>{slab.style.transition=stripe.style.transition=''})});
phone.addEventListener('change',aim);
document.fonts.ready.then(aim);

// 타이틀 화면: 이번 세션에 처음 왔거나 ?title=1 이면 띄운다. 닫힌 뒤에야 메뉴가 날아 들어온다.
const title=document.getElementById('title');
const startIntro=()=>setTimeout(()=>{document.body.classList.remove('intro');setTimeout(aim,700)},50);
if(!title||!document.documentElement.classList.contains('t-on')){startIntro();return}
const run=document.getElementById('tRun');
document.getElementById('tPress').focus({preventScroll:true});
// 15초 동안 그대로 두면 여우가 한 번씩 지나간다
const idle=setInterval(()=>{if(reduced||OVAN.paused())return;
  run.animate([{opacity:1,transform:'translateX(-80px)'},{opacity:1,transform:`translateX(${innerWidth+40}px)`}],{duration:2400,easing:'linear'});
  run.firstElementChild.animate([{transform:'none'},{transform:'translateY(-6px)'},{transform:'none'}],{duration:240,iterations:10,easing:'steps(2)'});
},15000);
let done=false;
const close=()=>{
  if(done)return;done=true;clearInterval(idle);
  try{sessionStorage.setItem('ovan-title','1')}catch(_){}
  removeEventListener('keydown',onKey,true);
  title.style.pointerEvents='none';
  let ended=false;
  const end=()=>{if(ended)return;ended=true;document.documentElement.classList.remove('t-on');if(!phone.matches)items[cur].focus({preventScroll:true})};
  startIntro();
  if(reduced){end();return}
  // 오른쪽 끝이 비스듬히 왼쪽으로 쓸려 나간다
  title.animate([{clipPath:'polygon(0 0,120% 0,100% 100%,0 100%)'},{clipPath:'polygon(0 0,0% 0,-20% 100%,0 100%)'}],{duration:480,easing:'cubic-bezier(.6,0,.3,1)',fill:'forwards'}).finished.then(end);
  setTimeout(end,700); // 탭이 가려져 애니메이션이 멈춰도 닫히게
};
// 아무 키: 이 키가 메뉴까지 움직이지 않게 캡처 단계에서 먹는다. 단축키와 F 키는 브라우저에 돌려준다.
const onKey=e=>{
  if(e.ctrlKey||e.metaKey||e.altKey||/^(Shift|Control|Alt|Meta|CapsLock|F\d+)$/.test(e.key))return;
  e.preventDefault();e.stopImmediatePropagation();close();
};
addEventListener('keydown',onKey,true);
title.addEventListener('click',close);
})();
