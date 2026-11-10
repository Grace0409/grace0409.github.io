// 글 페이지: 목차와 내비가 지금 읽는 구간을 따라간다
(()=>{
const {navi}=OVAN;
const art=document.getElementById('post');if(!art)return;
const H=[...art.querySelectorAll('h2[id]')];
const toc=document.getElementById('toc'),say=document.getElementById('say'),pct=document.getElementById('pct');
const min=art.dataset.min||'1';
toc.innerHTML=H.map((h,k)=>`<li><a href="#${h.id}"><i>${String(k+1).padStart(2,'0')}</i>${h.textContent}</a></li>`).join('');
const links=[...toc.querySelectorAll('a')];
let sec=-2;
function track(){
  let k=-1;H.forEach((h,j)=>{if(h.getBoundingClientRect().top<innerHeight*.35)k=j});
  const r=art.getBoundingClientRect(),p=Math.max(0,Math.min(1,(innerHeight*.5-r.top)/r.height));
  pct.textContent=Math.round(p*100)+'%';
  if(k===sec)return;sec=k;
  links.forEach((a,j)=>a.classList.toggle('on',j===k));
  navi(say,k<0?(H.length?`읽는 데 ${min}분쯤 걸려. 구간은 ${H.length}개!`:`읽는 데 ${min}분쯤 걸려!`)
    :k===H.length-1?'마지막 구간이야. 거의 다 왔어!'
    :`지금 「${H[k].textContent}」 구간. ${k+1}/${H.length}`);
}
addEventListener('scroll',track,{passive:true});track();
})();
