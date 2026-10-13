'use strict';
const $=s=>document.querySelector(s);
$('#menu')?.addEventListener('click',()=>{const open=$('#nav').classList.toggle('open');$('#menu').setAttribute('aria-expanded',String(open));});
const courseCategory=value=>({'舒乳':'舒乳顧問證書培訓','產康':'產後健康身型恢復課程'}[value]||value);
function filterCourses(){const filter=$('#course-filter');if(!filter)return;let visible=0;document.querySelectorAll('[data-category]').forEach(el=>{el.hidden=(filter.value!=='all'&&courseCategory(el.dataset.category)!==filter.value)||($('#format-filter')&&$('#format-filter').value!=='all'&&el.dataset.format!==$('#format-filter').value);if(!el.hidden)visible++;});if($('#course-empty'))$('#course-empty').hidden=visible>0;}
$('#course-filter')?.addEventListener('change',filterCourses);
$('#format-filter')?.addEventListener('change',filterCourses);
$('#consultant-search')?.addEventListener('submit',e=>{e.preventDefault();const d=new FormData(e.target);const match=d.has('demo')&&(!d.get('city')||d.get('city')==='臺北市')&&(!d.get('service')||d.get('service')==='舒乳')&&'示範顧問 A'.toLowerCase().includes(String(d.get('keyword')).trim().toLowerCase());const box=$('#consultant-results');box.replaceChildren();const p=document.createElement('p');p.textContent=match?'1 筆示範資料，0 筆正式顧問資料。':'沒有符合條件的資料。正式名冊尚未匯入，此結果不代表該地區沒有顧問。';box.append(p);if(match){const a=document.createElement('a');a.href='consultant-demo.html';a.className='button';a.textContent='示範顧問 A｜臺北市・舒乳（非真實人物） →';box.append(a);}});
$('#verify-form')?.addEventListener('submit',e=>{e.preventDefault();const n=String(new FormData(e.target).get('number')).trim();$('#verify-result').textContent=n==='DEMO-0001'?'示範紀錄 DEMO-0001：虛構資料，無認證效力，非正式證書。':'正式資料庫尚未接通，無法確認此編號。這不是「無效證書」判定。';});
const roles={admin:['帳號與角色管理','全站內容與資料審核','證書紀錄與撤銷管理','稽核紀錄'],officer:['課程與活動編輯','報名與合作案件處理','顧問資料送審'],instructor:['本人授課梯次','學員出席與評量草稿','教材維護'],consultant:['本人公開介紹送審','本人課程與證書紀錄','顧問資源閱讀']};
function showRole(){const box=$('#role-content');box.replaceChildren();const p=document.createElement('p');p.textContent='預留功能（僅展示，尚未啟用）';box.append(p);const ul=document.createElement('ul');roles[$('#role').value].forEach(t=>{const li=document.createElement('li');li.textContent=t;ul.append(li);});box.append(ul);}
if($('#role')){showRole();$('#role').addEventListener('change',showRole);}
let draft='';
if($('#contact-form')){const params=new URLSearchParams(location.search);for(const name of ['course','type']){const el=$('#contact-form').elements[name];const value=params.get(name);if([...el.options].some(o=>o.value===value))el.value=value;}
$('#contact-form').addEventListener('submit',e=>{e.preventDefault();const f=e.target;draft=['諮詢草稿（未送出，不代表報名成功）',...['type','course','name','email','organization','message'].map(n=>({type:'需求類型',course:'課程方向',name:'稱呼',email:'Email',organization:'機構名稱',message:'需求'}[n])+': '+(f.elements[n].tagName==='SELECT'?f.elements[n].selectedOptions[0].textContent:f.elements[n].value))].join('\n\n');$('#draft-content').textContent=draft;$('#draft').hidden=false;$('#draft').scrollIntoView({behavior:'auto'});});
$('#contact-form').addEventListener('reset',()=>{draft='';$('#draft').hidden=true;$('#draft-content').textContent='';});
$('#download-draft').addEventListener('click',()=>{const url=URL.createObjectURL(new Blob([draft],{type:'text/plain;charset=utf-8'}));const a=document.createElement('a');a.href=url;a.download='中華舒乳協會-諮詢草稿.txt';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);});}
// CMS content uses text nodes so editor content cannot inject markup.
(async()=>{try{const r=await fetch('/api/public');if(!r.ok)return;const entries=await r.json();if(!Array.isArray(entries))return;const file=location.pathname.split('/').pop();if(['courses.html','resources.html'].includes(file)){const kind=file==='courses.html'?'courses':'resources';const panel=document.createElement('section');const title=document.createElement('h2');title.textContent=kind==='courses'?'正式發布的課程':'協會文章與影片';panel.append(title);const grid=document.createElement('div');grid.className='grid';entries.filter(x=>x.kind===kind).forEach(x=>{const a=document.createElement('a');a.className='card';if(kind==='courses'){a.dataset.category=courseCategory(x.category);a.dataset.format=x.format||'pending';}a.href='content.html?id='+encodeURIComponent(x.id);const wrap=document.createElement('div');const h=document.createElement('h3');h.textContent=x.title;const p=document.createElement('p');p.textContent=kind==='courses'?[courseCategory(x.category),({online:'線上課程','in-person':'實體課程',hybrid:'線上＋實體'}[x.format]||'上課方式待公告'),x.date,x.location].filter(Boolean).join(' · '):x.youtube?'文章與 YouTube 影片':'協會文章';wrap.append(h,p);a.append(wrap);grid.append(a);});if(grid.childElementCount){panel.append(grid);document.querySelector('main').append(panel);}filterCourses();}
if(file==='content.html'){const x=entries.find(x=>x.id===new URLSearchParams(location.search).get('id'));const box=document.querySelector('#cms-content');if(!x){box.textContent='找不到已發布內容，資料可能已下架。';return;}document.querySelector('h1').textContent=x.title;document.title=x.title+'｜中華舒乳協會';const p=document.createElement('p');p.style.whiteSpace='pre-wrap';p.textContent=x.content;box.append(p);if(x.kind==='courses'){const info=document.createElement('p');info.textContent=[x.date,x.location,x.fee].filter(Boolean).join(' · ');info.textContent='上課方式：'+({online:'線上課程','in-person':'實體課程',hybrid:'線上＋實體'}[x.format]||'待公告')+' · '+info.textContent;box.prepend(info);const signup=document.createElement('a');signup.className='button';signup.href='https://line.me/R/ti/p/%40477dnljx';signup.textContent='LINE 詢問與報名 →';box.append(signup);}if(x.youtube){const a=document.createElement('a');a.href=x.youtube;a.rel='noopener noreferrer';a.className='button';a.textContent='在 YouTube 觀看影片 ↗';box.append(a);}}
}catch(e){/* Static deployment remains usable without CMS. */}})();
const verifyForm=document.querySelector('#verify-form');if(verifyForm){const clone=verifyForm.cloneNode(true);verifyForm.replaceWith(clone);clone.addEventListener('submit',async e=>{e.preventDefault();const number=String(new FormData(clone).get('number')).trim();const result=document.querySelector('#verify-result');if(number==='DEMO-0001'){result.textContent='示範紀錄 DEMO-0001：虛構資料，無認證效力。';return;}try{const r=await fetch('/api/verify',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({number})});if(!r.ok)throw Error();const d=await r.json();result.textContent=d.message||['證書編號：'+d.number,'課程：'+d.course,'核發日期：'+d.issued,'服務縣市：'+((d.cities||[]).join('、')||'未登錄'),'期限：'+(d.expires||'未登錄'),'狀態：'+({issued:'有效',revoked:'已撤銷',expired:'已到期'}[d.status])].join('；');}catch(e){result.textContent='證書查詢服務尚未接通，請透過 LINE 向協會確認。';}});}

$('#mom-filter')?.addEventListener('change',e=>document.querySelectorAll('[data-mom-group]').forEach(el=>el.hidden=e.target.value!=='all'&&el.dataset.momGroup!==e.target.value));
// Gentle motion is limited to the homepage and respects reduced-motion preferences.
if(document.querySelector('.hero-note')){
 const blocks=[...document.querySelectorAll('main>.hero,main>.destination,main>section>.destination,body>.cta')];
 const motion=window.matchMedia('(prefers-reduced-motion: reduce)');
 const pointer=window.matchMedia('(hover: hover) and (pointer: fine)');
 blocks.forEach(block=>{
  block.classList.add('home-motion');
  block.addEventListener('pointerenter',()=>{
   if(!motion.matches&&pointer.matches&&!block.classList.contains('home-arriving'))block.classList.add('home-sway');
  });
  block.addEventListener('animationend',event=>{
   if(event.target!==block)return;
   block.classList.remove('home-sway','home-arriving');
  });
 });
 if('IntersectionObserver' in window&&!motion.matches){
  const observer=new IntersectionObserver(entries=>entries.forEach(entry=>{
   if(entry.isIntersecting){
    if(!motion.matches)entry.target.classList.add('home-arriving');
    observer.unobserve(entry.target);
   }
  }),{threshold:0.12});
  blocks.forEach(block=>observer.observe(block));
  motion.addEventListener('change',()=>{
   if(motion.matches){observer.disconnect();blocks.forEach(block=>block.classList.remove('home-arriving','home-sway'));}
  });
 }
}
