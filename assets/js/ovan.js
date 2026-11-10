// OVAN.log 공용: 데이터 정리, 아이콘, 픽셀 그림, 내비 말풍선, 페이지 전환
window.OVAN=(()=>{
const D=window.OVAN_DATA||{base:'',cats:[],posts:[]};
const B=D.base||'';
const ICON={
  'dev':'<path d="M8 6l-6 6 6 6M16 6l6 6-6 6"/>',
  'ctf-wargame':'<path d="M5 21V3M5 4h13l-3 4.5 3 4.5H5"/>',
  'bug-bounty':'<path d="M8 10h8v6a4 4 0 0 1-8 0zM9.5 10V8a2.5 2.5 0 0 1 5 0v2M12 10v10M3 14h5M16 14h5M4 8l4 3M20 8l-4 3M4 20l4-3M20 20l-4-3"/>',
  'tech-docs':'<path d="M4 20l1-5L16 4l4 4L9 19zM13.5 6.5l4 4"/>',
  'paper-conference':'<path d="M3 5h6a3 3 0 0 1 3 3v12a2.5 2.5 0 0 0-2.5-2.5H3zM21 5h-6a3 3 0 0 0-3 3v12a2.5 2.5 0 0 1 2.5-2.5H21z"/>',
  'contest-cert':'<circle cx="12" cy="9" r="6"/><path d="M8.5 14L7 22l5-3 5 3-1.5-8"/>',
  'about':'<circle cx="12" cy="8" r="4.5"/><path d="M3.5 21.5c1-4.5 4.4-7 8.5-7s7.5 2.5 8.5 7"/>',
  'archive':'<path d="M3 4h18v5H3zM5 9v11h14V9M9.5 13h5"/>'
};
const CATS={};D.cats.forEach(c=>CATS[c.k]=c);
const P=D.posts.map(([d,url,c,t,x])=>({d,url,c,t,x}));
const md=d=>d.slice(5).replace('-','.');
const byCat=c=>P.filter(p=>p.c===c);
// 미리 날짜를 잡아 둔 글(future: true)은 "최근 기록" 날짜에서 뺀다
const today=new Date(Date.now()+9*36e5).toISOString().slice(0,10);
const last=ps=>ps.find(p=>p.d<=today)||ps[0];
const catUrl=k=>`${B}/categories/${k}/`;
const LINKS={home:B+'/',about:B+'/about/',archive:B+'/archive/'};
const icon=(k,cls='ic')=>`<svg class="${cls}" viewBox="0 0 24 24" aria-hidden="true">${ICON[k]||ICON.archive}</svg>`;

/* 픽셀 그림. 캐릭터 그림을 옮기지 않고, 좋아하는 두 캐릭터를 떠올리게 하는 소품만 직접 찍었다.
   여우 가면(키리코), UFO(후타바). k=잉크 w=흰색 p=핑크 */
const PIX={
  fox:[
    '.k............k.',
    'kpk..........kpk',
    'kwpk........kpwk',
    'kwwpkkkkkkkkpwwk',
    'kwwwwwwwwwwwwwwk',
    'kwpwwwwwwwwwwpwk',
    'kwwkkkwwwwkkkwwk',
    'kwwwkkwwwwkkwwwk',
    '.kwwwwwwwwwwwwk.',
    '.kwppwwwwwwppwk.',
    '..kwwwwkkwwwwk..',
    '...kwwwkkwwwk...',
    '....kkwwwwkk....',
    '......kkkk......'],
  ufo:[
    '.....kkkkkk.....',
    '....kwwwwwwk....',
    '...kwwkwwwwwk...',
    '...kwwwwwwwwk...',
    '.kkkkkkkkkkkkkk.',
    'kwwpwwpwwpwwpwwk',
    'kwwwwwwwwwwwwwwk',
    '.kkkkkkkkkkkkkk.',
    '...kk..kk..kk...',
    '..p.....p....p..',
    '.p......p.....p.']
};
const pix=(name,cls='pix')=>{
  const g=PIX[name],W=g[0].length,H=g.length,by={k:'',w:'',p:''};
  g.forEach((row,y)=>[...row].forEach((c,x)=>{if(by[c]!==undefined)by[c]+=`M${x} ${y}h1v1h-1z`}));
  return `<svg class="${cls}" viewBox="0 0 ${W} ${H}" shape-rendering="crispEdges" aria-hidden="true">
    <path d="${by.w}" fill="#fff"/><path d="${by.p}" fill="#ff2e88"/><path d="${by.k}" fill="#0b0a0e"/></svg>`;
};

/* 내비: 한 글자씩 찍히는 말풍선. 커서는 두지 않는다. */
const reducedM=matchMedia('(prefers-reduced-motion: reduce)').matches;
const navi=(el,text)=>{
  clearInterval(el._t);
  if(reducedM){el.textContent=text;return}
  const ch=[...text];let n=0;el.textContent='';
  el._t=setInterval(()=>{el.textContent=ch.slice(0,++n).join('');if(n>=ch.length)clearInterval(el._t)},22);
};
return {CATS,P,PAPERS:D.papers||0,md,byCat,last,catUrl,LINKS,icon,pix,navi};
})();

// data-pix 자리에 픽셀 그림을 채운다
document.querySelectorAll('[data-pix]').forEach(el=>{el.innerHTML=OVAN.pix(el.dataset.pix)});
// "최근 기록" 날짜는 미리 잡아 둔 글을 빼고 다시 적는다
document.querySelectorAll('.js-last').forEach(el=>{const p=OVAN.last(OVAN.P);if(p)el.textContent=OVAN.md(p.d)});

// 일시정지 버튼: 반복 움직임을 멈추고, 다음 방문에도 기억한다
(()=>{
  const root=document.documentElement;
  const sync=()=>{const p=root.classList.contains('paused');document.querySelectorAll('.pausebtn').forEach(b=>{b.setAttribute('aria-pressed',String(p));b.setAttribute('aria-label',p?'배경 움직임 다시 켜기':'배경 움직임 멈추기')})};
  document.querySelectorAll('.pausebtn').forEach(b=>b.addEventListener('click',()=>{
    const p=root.classList.toggle('paused');
    try{localStorage.setItem('ovan-motion',p?'off':'on')}catch(_){}
    sync();
  }));
  sync();
})();
OVAN.paused=()=>document.documentElement.classList.contains('paused');

// 페이지 이동 와이프. 핑크 판 앞머리를 픽셀 여우가 달려 나간다.
(()=>{
  const reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
  const w=document.createElement('div');w.className='wipe';w.setAttribute('aria-hidden','true');w.innerHTML='<i></i><i></i><b class="wfox">'+OVAN.pix('fox')+'</b>';
  document.body.appendChild(w);
  // 홈 카드 → 카테고리 머리: 브라우저가 페이지 전환(View Transitions)을 지원하면 카드가 그대로 날아가 붙는다.
  // 그 밖의 이동은 기존 와이프를 쓰고, 카드를 전환에서 빼서 와이프 화면이 새 페이지로 부드럽게 바뀌게 한다.
  const canMorph='onpageswap' in window&&!reduced;
  window.leave=(url,o={})=>{
    if(o.morph&&canMorph){location.href=url;return}
    document.querySelectorAll('.card').forEach(c=>c.style.viewTransitionName='none');
    if(reduced){location.href=url;return}
    w.classList.add('go');setTimeout(()=>{location.href=url},520);
  };
  document.addEventListener('click',e=>{
    const a=e.target.closest('a[data-go]');
    if(!a||e.defaultPrevented||e.button!==0||e.metaKey||e.ctrlKey||e.shiftKey||e.altKey||a.target==='_blank')return;
    if(a.origin!==location.origin)return;
    // 같은 페이지 안의 #앵커는 그냥 스크롤
    if(a.pathname===location.pathname&&a.hash)return;
    e.preventDefault();leave(a.href,{morph:a.hasAttribute('data-morph')});
  });
  addEventListener('pageshow',()=>{w.classList.remove('go');document.querySelectorAll('.card').forEach(c=>c.style.viewTransitionName='')});
})();
