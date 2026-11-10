// 홈을 뺀 페이지 공용: 여우 TOP 버튼, 읽기 막대, 코드 블록 터미널 바와 복사
(()=>{
const {pix}=OVAN;
const reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;

// 여우 버튼: 핑크 사선이 한 번 긋고 지나가는 사이 맨 위로 옮겨 간다
const fox=document.createElement('button');fox.type='button';fox.className='foxtop';fox.setAttribute('aria-label','맨 위로');
fox.innerHTML=pix('fox')+'<small>TOP</small>';
document.body.append(fox);
const blink=document.createElement('div');blink.className='blink';blink.setAttribute('aria-hidden','true');document.body.append(blink);
fox.addEventListener('click',()=>{
  if(reduced){scrollTo(0,0);return}
  blink.animate([
    {clipPath:'polygon(0 0,0 0,0 100%,0 100%)'},
    {clipPath:'polygon(0 0,120% 0,100% 100%,0 100%)',offset:.45},
    {clipPath:'polygon(120% 0,120% 0,100% 100%,100% 100%)'}],{duration:460,easing:'cubic-bezier(.6,0,.3,1)'});
  setTimeout(()=>scrollTo(0,0),200);
});

// 글 페이지에서만 읽은 만큼 차는 막대
const prog=document.getElementById('post')?Object.assign(document.createElement('div'),{className:'prog'}):null;
if(prog)document.body.append(prog);
const onScroll=()=>{
  fox.classList.toggle('show',scrollY>500);
  if(prog){const h=document.documentElement.scrollHeight-innerHeight;prog.style.transform=`scaleX(${h>0?Math.min(1,scrollY/h):0})`}
};
addEventListener('scroll',onScroll,{passive:true});onScroll();

// 넓은 표는 폰에서 화면 밖으로 밀리지 않게 가로 스크롤 상자로 감싼다
document.querySelectorAll('.prose table').forEach(t=>{
  if(t.parentElement.classList.contains('tbl'))return;
  const w=document.createElement('div');w.className='tbl';t.before(w);w.append(t);
});

// 코드 블록: 언어 이름과 COPY 버튼이 있는 터미널 바를 붙인다
document.querySelectorAll('.prose div.highlighter-rouge').forEach(box=>{
  const pre=box.querySelector('pre');if(!pre)return;
  const lang=([...box.classList].find(c=>c.startsWith('language-'))||'language-text').slice(9);
  const bar=document.createElement('div');bar.className='term-bar';
  bar.innerHTML=`<span>${lang==='plaintext'?'text':lang}</span>`;
  if(navigator.clipboard){
    const b=document.createElement('button');b.type='button';b.textContent='COPY';
    b.addEventListener('click',()=>navigator.clipboard.writeText(pre.innerText.replace(/\n$/,'')).then(()=>{b.textContent='COPIED';setTimeout(()=>b.textContent='COPY',1200)}));
    bar.append(b);
  }
  box.prepend(bar);
});
})();
