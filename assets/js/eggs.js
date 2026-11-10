// 숨은 장치들. 화면에는 안내가 없고, 찾은 사람만 본다.
// 1) 콘솔 인사 + 깃발 문제  2) 아무 데서나 flag / sudo 타이핑  3) ↑↑↓↓←→←→BA
// 4) 홈 OV 배지 다섯 번  5) 내비 UFO 세 번
(()=>{
const {pix,navi}=OVAN;
const reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
const FLAG='OVAN{y0u_f0und_th3_f0x}';

const css=document.createElement('style');
css.textContent=`
.toast{position:fixed;left:20px;bottom:20px;z-index:80;max-width:min(420px,calc(100vw - 40px));background:#07060a;color:var(--paper);border:1px solid var(--rule);
  font:500 14px/1.65 "JetBrains Mono",ui-monospace,Consolas,monospace;padding:12px 16px 13px;transition:opacity .2s,translate .3s var(--out)}
.toast[hidden]{display:block;opacity:0;translate:0 12px;pointer-events:none}
.toast .tt{display:inline-block;margin-bottom:6px;font:800 italic 13px/1 var(--lat);letter-spacing:.18em;background:var(--pink);color:var(--ink);padding:4px 8px 3px;transform:skewX(-10deg)}
.toast p{margin:0;white-space:pre-wrap;word-break:keep-all}
.toast .k{color:var(--pink)}
.toast .m{color:var(--muted)}
.parade{position:fixed;left:0;right:0;bottom:12px;height:64px;z-index:79;pointer-events:none}
.parade b{position:absolute;bottom:0;left:0;width:56px}
.parade b:nth-child(even){bottom:20px}
.badge.fox{background:var(--paper);padding:7px}
.badge.fox svg{width:100%;height:auto}
@media (max-width:900px){.toast{bottom:64px}}`;
document.head.append(css);

// 토스트: 터미널 창처럼 생긴 짧은 알림
const toast=document.createElement('div');toast.className='toast';toast.hidden=true;toast.setAttribute('role','status');toast.setAttribute('aria-live','polite');
document.addEventListener('DOMContentLoaded',()=>document.body.append(toast));
let tT;
function say(title,html,ms=4200){
  toast.innerHTML=`<span class="tt">${title}</span><p>${html}</p>`;
  toast.hidden=false;clearTimeout(tT);tT=setTimeout(()=>toast.hidden=true,ms);
}

// 여우와 UFO가 화면 아래를 줄지어 지나간다
function parade(){
  if(reduced||OVAN.paused()||document.querySelector('.parade'))return;
  const p=document.createElement('div');p.className='parade';p.setAttribute('aria-hidden','true');
  const seq=['fox','ufo','fox','fox','ufo','fox'];
  p.innerHTML=seq.map(n=>`<b>${pix(n)}</b>`).join('');document.body.append(p);
  const W=innerWidth;let last;
  [...p.children].forEach((b,i)=>{
    last=b.animate([{transform:'translateX(-80px)'},{transform:`translateX(${W+40}px)`}],{duration:2600,delay:i*170,easing:'linear',fill:'both'});
    b.firstElementChild.animate([{transform:'translateY(0)'},{transform:'translateY(-6px)'},{transform:'translateY(0)'}],{duration:260,iterations:Infinity,easing:'steps(2)',delay:i*60});
  });
  last.finished.then(()=>p.remove());
}

// 1) 콘솔
console.log('%c OV %c OVAN.log ','background:#ff2e88;color:#0b0a0e;font:900 italic 22px sans-serif;padding:4px 8px','background:#0b0a0e;color:#fff;font:900 italic 22px sans-serif;padding:4px 8px');
console.log('%c개발자 도구까지 열어 보셨군요. 반갑습니다!\n이 사이트 어딘가에 여우 한 마리가 깃발을 숨겨 두었습니다.\n힌트: <html> 태그의 data 속성, 그리고 base64.\n찾으면 ovan.submit("OVAN{...}") 으로 제출해 보세요.','font:14px/1.6 sans-serif');
document.documentElement.dataset.fox=btoa(FLAG);
window.ovan={submit(f){
  if(String(f).trim()===FLAG){say('FLAG ACCEPTED','<span class="k">+100</span> 정답입니다! 여우가 축하 행진을 합니다 :)',5200);parade();return '정답!'}
  say('WRONG FLAG','<span class="m">다시 해 보세요. base64를 한 번 풀어야 합니다.</span>');return '오답'
}};

// 2), 3) 타이핑과 치트 코드
const KONAMI=['arrowup','arrowup','arrowdown','arrowdown','arrowleft','arrowright','arrowleft','arrowright','b','a'];
let keys=[],typed='';
document.addEventListener('keydown',e=>{
  if(e.ctrlKey||e.metaKey||e.altKey)return;
  const t=e.target;if(t.closest&&t.closest('input,textarea,select,[contenteditable]'))return;
  const k=e.key.toLowerCase();
  keys=[...keys,k].slice(-KONAMI.length);
  if(keys.join()===KONAMI.join()){keys=[];say('CHEAT CODE','치트 코드 확인. 무적 모드는 없지만 여우들이 인사하러 왔습니다!');parade();return}
  if(k.length!==1)return;
  typed=(typed+k).slice(-8);
  if(typed.endsWith('flag')){typed='';say('TERMINAL','<span class="k">$</span> cat flag.txt\ncat: flag.txt: Permission denied\n<span class="m"># 진짜 깃발은 콘솔 쪽에 있습니다.</span>')}
  else if(typed.endsWith('sudo')){typed='';say('TERMINAL','<span class="k">$</span> sudo su\n[sudo] password for guest:\nguest is not in the sudoers file.\n<span class="m"># 관리자 권한은 OVAN만 가지고 있어요 :)</span>')}
});

// 4) 홈 OV 배지: 다섯 번 누르면 잠깐 여우 가면으로 바뀐다 (홈에서는 배지가 자기 자신을 가리키는 링크라 막아도 손해가 없다)
document.addEventListener('DOMContentLoaded',()=>{
  const b=document.querySelector('.brand .badge');if(!b)return;
  let n=0,nT,on=false;
  b.addEventListener('click',e=>{
    e.preventDefault();e.stopPropagation();
    if(on)return;
    clearTimeout(nT);nT=setTimeout(()=>n=0,1600);
    if(++n<5){if(!reduced)b.animate([{rotate:'0deg'},{rotate:'-10deg'},{rotate:'0deg'}],{duration:180});return}
    n=0;on=true;b.classList.add('fox');b.innerHTML=pix('fox');
    if(!reduced)b.animate([{transform:'rotate(-6deg) scale(.4)'},{transform:'rotate(-6deg) scale(1.15)'},{transform:'rotate(-6deg) scale(1)'}],{duration:360,easing:'cubic-bezier(.2,1.35,.4,1)'});
    say('MASK ON','여우 가면 장착! 5초 동안만 유지됩니다.');
    setTimeout(()=>{b.classList.remove('fox');b.textContent='OV';on=false},5000);
  });
});

// 5) 내비 UFO: 세 번 누르면 위로 올라갔다가 돌아온다
const LINES=['앗, 간지러워!','그만 눌러, 스캔하는 중이란 말이야.','…좋아, 특별히 알려 줄게. 개발자 도구 콘솔을 열어 봐!'];
let uN=0,uT,uStep=0;
document.addEventListener('click',e=>{
  const u=e.target.closest('.navi .ufo');if(!u)return;
  clearTimeout(uT);uT=setTimeout(()=>uN=0,1200);
  if(++uN<3)return;
  uN=0;
  const sayEl=u.parentElement.querySelector('.say span:last-child');
  if(!reduced)u.animate([{transform:'none',opacity:1},{transform:'translateY(-90px)',opacity:0,offset:.45},{transform:'translateY(-90px)',opacity:0,offset:.55},{transform:'none',opacity:1}],{duration:1100,easing:'steps(8)'});
  if(sayEl)navi(sayEl,LINES[Math.min(uStep++,LINES.length-1)]);
});
})();
