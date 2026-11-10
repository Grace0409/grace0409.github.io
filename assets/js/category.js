// 카테고리 페이지: 내비 한마디. 데이터에서 바로 계산한 사실만 말한다.
(()=>{
const {CATS,byCat,md,last,navi}=OVAN;
const say=document.getElementById('say');if(!say)return;
const K=say.dataset.cat,L=byCat(K);
const counts=Object.keys(CATS).map(k=>byCat(k).length),cMax=Math.max(...counts);
let line;
if(!L.length)line='아직 비어 있어. 곧 채워질 거야!';
else{
  const recent=md(last(L).d);
  // 제목 앞 [대괄호]가 가장 많이 붙은 출처를 센다 (예: [Dreamhack])
  const tagN={};L.forEach(p=>{const m=p.t.match(/^\[([^\]]+)\]/);if(m)tagN[m[1]]=(tagN[m[1]]||0)+1});
  const top=Object.entries(tagN).sort((a,b)=>b[1]-a[1])[0];
  if(top&&top[1]>=3)line=`${L.length}개 중 ${top[1]}개가 ${top[0]} 기록이야. 최근 건 ${recent}!`;
  else if(L.length===cMax)line=`${L.length}개, 제일 많이 쌓인 곳이야! 최근 건 ${recent}.`;
  else if(L.length<3)line=`아직 ${L.length}개. 이제 막 시작한 칸이야.`;
  else line=`${L.length}개 있어. 최근 건 ${recent}!`;
}
setTimeout(()=>navi(say,line),300);
})();
